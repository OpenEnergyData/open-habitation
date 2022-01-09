import apispec
import api_helpers as ah
import falcon
import json
import functools
import os

from pathlib import Path
from falcon import media
from falcon_apispec import FalconPlugin
from wsgiref.simple_server import make_server
from pandas_datapackage_reader import read_datapackage
from apispec import APISpec
from swagger_ui import falcon_api_doc

import psycopg2 as pg
from psycopg2 import sql
import dotenv

dotenv.load_dotenv()


# create database connection
# -----------------------------------------------------------------------------------------------------
if True: # make code collapsable
    local_database = os.getenv("LOCAL_DATABASE")

    if local_database=="true":
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        username = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        database = "openhabitation"

        connection = pg.connect(database=database, user=username, password=password, host=host, port=port)
    else:
        # database connection taylored for heroku deployment:
        DATABASE_URL = os.environ['DATABASE_URL']
        connection = pg.connect(DATABASE_URL, sslmode='require')
# -----------------------------------------------------------------------------------------------------


app = application = falcon.App()


json_handler = media.JSONHandler(
    dumps=functools.partial(json.dumps, indent=4, sort_keys=True),
)


result_cache = []



class AddressSearch():
    """
    Providing address suggestions based on pattern matching
    """

    def on_get(self, req, resp):

        print("request received")
        #print("received get request on /addresssearch")
        #print(req.params["term"])
        pattern = req.params["term"]+"%%"
        cursor = connection.cursor()
        cursor.execute("select \"CompleteAddress\" from gwr where \"CompleteAddress\" ilike %(ilike)s order by \"CompleteAddress\" limit 15" , {"ilike":pattern})
        suggestions = cursor.fetchall()
        suggestions = [i[0] for i in suggestions]
        #print(suggestions)
        #print(json.dumps(availableTags))
        resp.media = suggestions
        resp.media_handler = json_handler


SearchAddress = AddressSearch()
app.add_route("/api/addresssearch", SearchAddress)


class HouseInfoResource():
    def __init__(self) -> None:
        pass

    def on_get(self, req, resp):
        """
        Handles GET requests
        ---
        description: Gets building information
        responses:
            200:
                description: JSON blob
        """
        print(req)
        print(req.params)

        address = req.params["address"]
        angle = req.params["angle"]
        aspect = req.params["aspect"]
        # mountingplace = req.params["mountingplace"]

        if angle=="undefined":
            angle = None
        if aspect=="undefined":
            aspect = None

        output = ah.get_house_info(address, angle, aspect)

        if output==None:
            resp.status = falcon.HTTP_404
            resp.text = "No data found for that address."
        else:
            resp.media = output
            resp.media_handler = json_handler

        # dummy values:
        # output = {}
        # output['address'] = address
        # output['category'] = "unknown"
        # output['total_power'] = 50
        # output['angle'] = angle
        # output['aspect'] = aspect
        # output['mountingplace'] = mountingplace
        # output['yearly_production'] = "unknown"
        # output["space_heating"] = "gas"
        # output["hot_water"] = "gas"
        # output['eco_rating'] = "Z"



HouseInfoRes = HouseInfoResource()
app.add_route("/api/houseinfo", HouseInfoRes)


class ProductionResource():
    """
    Getting information of electricity production for a specific address
    """

    def __init__(self) -> None:
        pass

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
        query = req.get_media()
        print(query.keys())
        # query = {}
        # query["address"] = obj.get('address').strip()
        # query["angle"] = obj.get('angle')
        # query["aspect"] = obj.get('aspect')
        # query["mountingplace"] = obj.get('mountingplace')

        data = None
        global result_cache
        for r in result_cache:
            if r['address']==query['address'] and r['angle']==query['angle'] and r['aspect']==query['aspect'] and r['mountingplace']==query['mountingplace']:
                data = r
        if data is None:
            data = ah.calculate_results(query)
            if data is not None:
                #data['id'] = len(result_cache) + 1
                result_cache.append(data)
            else:
                # TODO: throw 404 error
                resp.status = falcon.HTTP_404
                resp.text = "No data found for that address."

        if len(result_cache) > 20:
            result_cache = result_cache[-20:]

        resp.media = result_cache
        resp.media_handler = json_handler


# ProdRes = ProductionResource()
# app.add_route("/api/production/yearly", ProdRes)



class HeatingResource():
    def __init__(self) -> None:
        pass


# HeatRes = HeatingResource()
# app.add_route("/api/heating", HeatRes)



# spec = APISpec(
#     title="Open Habitation API",
#     version="0.1.0",
#     openapi_version='3.0',
#     plugins=[FalconPlugin(app)],
# )

# spec.path(resource=ProdRes)

# BUG! https://github.com/PWZER/swagger-ui-py/issues/29
# falcon_api_doc(app, config=spec.to_dict(), url_prefix='/api/doc/', title='API doc')
#print(spec.to_yaml())

class IndexResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        with open(Path('./public/index.html').resolve(), 'r') as f:
            resp.text = f.read()


app.add_route('/', IndexResource())
app.add_static_route('/public/app.js', Path('./public/app.js').resolve())
app.add_static_route('/public', Path('./public/').resolve())


if __name__ == '__main__':
    with make_server('', 8000, application) as httpd:
        print('Serving on http://localhost:8000')
        httpd.serve_forever()




