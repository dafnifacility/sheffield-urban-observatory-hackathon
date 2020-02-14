import cherrypy
from converter import Converter
import requests
from csv_response_parser import convert_csv_to_json, convert_api_json_to_geojson
import json

class SheffieldConverter(Converter):
    def convert_type_name(type_name):
        type_name_conversion = {
            'Vehicle Count':'SCC_flow',
            'allpollu':'AMfixed',
        }
        return type_name_conversion[type_name]


    url = 'https://sheffield-portal.urbanflows.ac.uk/uflobin/ufdex'
    conversion_dict = {
        'starttime':('Tfrom', None),
        'endtime':('Tto', None),
        'sensor_type':('byFamily', convert_type_name),
        'sensor_name':('bySensor', None)
    }

sheffield_converter = SheffieldConverter()

class SheffieldIngest(object):
    @cherrypy.expose
    def index(self, **params):
        request_url = sheffield_converter.url
        if params:
            request_url = sheffield_converter.convert_parameters(params)
        
        geo_json = False

        if 'geo_json' in params:
            if params['geo_json'] in ['true', 'TRUE', 'True', 't']:
                geo_json = True
            del params['geo_json']
        
        request_url += '&freqInMin=5&tok=generic&aktion=CSV_show'

        response = requests.get(request_url)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        
        response = convert_csv_to_json(response.text)

        if geo_json:
            response = convert_api_json_to_geojson(response)

        return response.encode('utf8')