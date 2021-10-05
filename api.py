from typing import Literal
from api_prototype import *
import falcon
import json
import functools

from pathlib import Path
from falcon import media
from falcon_apispec import FalconPlugin
from wsgiref.simple_server import make_server
from pandas_datapackage_reader import read_datapackage
from apispec import APISpec
from swagger_ui import falcon_api_doc

import psycopg2 as pg
from psycopg2 import sql

host = "0.0.0.0"
port = "5434"
database="geo_admin"
username = "testuser"
password = "test123"

connection = pg.connect(database=database, user=username, password=password, host=host, port=port)

app = application = falcon.App()


json_handler = media.JSONHandler(
    dumps=functools.partial(json.dumps, indent=4, sort_keys=True),
)


result_cache = []


class ElectricityProduction():
    def on_get(self, req, res):
        """Response to GET request for the building's electricity production 

        Parameters
        ----------
        req : [type]
            [description]
        res : [type]
            [description]
        """

class AddressSearch():

    def on_get(self, req, resp):

        #print("received get request on /addresssearch")
        #print(req.params["term"])
        pattern = req.params["term"]+"%%"
        cursor = connection.cursor()
        cursor.execute("select \"CompleteAddress\" from electricity_production where \"CompleteAddress\" ilike %(ilike)s order by \"Address\" limit 10" , {"ilike":pattern})
        suggestions = cursor.fetchall()
        suggestions = [i[0] for i in suggestions]
        #print(suggestions)
        #print(json.dumps(availableTags))
        resp.media = suggestions
        resp.media_handler = json_handler



street_search = AddressSearch()
app.add_route("/addresssearch", street_search)



class ProductionResource:
    def on_get(self, req, resp):
        """Handles GET requests
        ---
        description: Gets building data
        responses:
            200:
                description: JSON blob
        """
        resp.media = result_cache
        resp.media_handler = json_handler

    def on_post(self, req, resp):
        """Handles POST requests
        ---
        description: Gets building data for a search address
        requestBody:
            required: true
            content:
                application/x-www-form-urlencoded:
                    schema:
                        type: object
                        properties:
                            address:
                                type: string
                                description: Building in Switzerland
        responses:
            200:
                description: JSON blob
        """
        obj = req.get_media()
        print("Address POSTED!!")
        print(req)
        print(type(req))
        print(obj)
        print(type(obj))
        address = obj.get('address').strip()
        print(obj["address"])
        print(obj.get("address"))
        print(type(obj.get("address")))
        print(address)
        print(type(address))
        data = None
        for r in result_cache:
            if r['address'] == address:
                data = r
        if data is None:
            data = calculate_results(address)
            if data is not None:
                data['id'] = len(result_cache) + 1
                result_cache.append(data)
            else:
                # TODO: throw 404 error
                pass
        resp.media = result_cache
        resp.media_handler = json_handler
        get_production_info_string(address)


prod_res = ProductionResource()
app.add_route("/api/production/yearly", prod_res)



spec = APISpec(
    title="Open Habitation API",
    version="0.1.0",
    openapi_version='3.0',
    plugins=[FalconPlugin(app)],
)

spec.path(resource=prod_res)

# BUG! https://github.com/PWZER/swagger-ui-py/issues/29
falcon_api_doc(app, config=spec.to_dict(), url_prefix='/api/doc/', title='API doc')
#print(spec.to_yaml())

class IndexResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        with open(Path('./public/index.html').resolve(), 'r') as f:
            resp.text = f.read()


app.add_route('/', IndexResource())
app.add_route('/js/script.js', Path('./js/script.js').resolve())
app.add_static_route('/public', Path('./public/').resolve())


if __name__ == '__main__':
    with make_server('', 8000, application) as httpd:
        print('Serving on http://localhost:8000')
        httpd.serve_forever()
