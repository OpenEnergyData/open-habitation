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

app = application = falcon.App()


json_handler = media.JSONHandler(
    dumps=functools.partial(json.dumps, indent=4, sort_keys=True),
)


result_cache = []


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
        address = obj.get('address').strip()
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
        # get_production_info_string(address)


prod_res = ProductionResource()
app.add_route("/api/production/yearly", prod_res)


spec = APISpec(
    title="EcoHabitasOpen APP",
    version="0.0.1",
    openapi_version='3.0',
    plugins=[FalconPlugin(app)],
)

spec.path(resource=prod_res)

# BUG! https://github.com/PWZER/swagger-ui-py/issues/29
# falcon_api_doc(app, config=spec.to_dict(), url_prefix='/api/doc', title='API doc')


class IndexResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        with open(Path('./public/index.html').resolve(), 'r') as f:
            resp.text = f.read()


app.add_route('/', IndexResource())
app.add_static_route('/public', Path('./public/').resolve())


if __name__ == '__main__':
    with make_server('', 8000, application) as httpd:
        print('Serving on http://localhost:8000')
        httpd.serve_forever()
