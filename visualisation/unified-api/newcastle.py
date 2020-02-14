import cherrypy
from converter import Converter
import requests
from csv_response_parser import convert_api_json_to_geojson

class NewcastleConverter(Converter):
    def convert_datetime(datetime):
        return datetime.replace(':', '').replace('-', '').replace('T', '')
    
    url = 'http://uoweb3.ncl.ac.uk/api/v1.1/sensors/data/json/'
    conversion_dict = {
        'starttime':('starttime', convert_datetime),
        'endtime':('endtime', convert_datetime)
    }

newcastle_converter = NewcastleConverter()

class NewcastleIngest(object):
    @cherrypy.expose
    def index(self, **params):
        request_url = newcastle_converter.url

        geo_json = False

        # When getting a specific sensor from Newcastle, the URL is different
        if 'sensor_name' in params:
            sensor_name = params['sensor_name']
            newcastle_converter.url = f'http://uoweb3.ncl.ac.uk/api/v1.1/sensors/{sensor_name}/data/json/'
            del params['sensor_name']

        if 'geo_json' in params:
            if params['geo_json'] in ['true', 'TRUE', 'True', 't']:
                geo_json = True
            del params['geo_json']

        if params:
            request_url = newcastle_converter.convert_parameters(params)

        response = requests.get(request_url)
        response = response.text

        if geo_json:
            response = convert_api_json_to_geojson(response)

        cherrypy.response.headers['Content-Type'] = 'application/json'
        return response.encode('utf8')