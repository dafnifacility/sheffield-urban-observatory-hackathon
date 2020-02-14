import json
import datetime

def check_for_multiple_lines(text):
    """
    Checks to see if multiple sensor records are inluded in the API response
    """

    break_list = []
    count = 0
    for i in range(0, len(text)):
        line = text[i]

        if line[0:5] == '# End':
            break_list.append(i)

    return break_list

def read_request_response(sensor_text):
    """
    Take a .csv response from the Sheffield UO and convert to .geojson format
    """
    data = []
    data_dict = {}
    column_descriptors = {}

    for line in sensor_text:
        if line == '<pre>' or len(line) == 0:
            pass

        elif line[0] != '#':  # this is the actual data for the sensor

            column_descriptors_keys = []
            for key in column_descriptors.keys():
                column_descriptors_keys.append(key)

            if len(data_dict) == 0:
                for i in range(2,len(column_descriptors.keys())):
                   data_dict[column_descriptors[column_descriptors_keys[i]]['name']] = []

            line_data = line.split(',')
            seconds = line_data[0]
            sensor = line_data[1]
            data_values = line_data[2:]
            data_values = [float(item.strip()) for item in data_values]

            #value =datetime.datetime.fromtimestamp(int(seconds))
            #date_time = value.strftime('%Y-%m--%d %H:%M:%S')

            for i in range(2, len(column_descriptors)):
                data_dict[column_descriptors[column_descriptors_keys[i]]['name']].append(
                    {
                        "Variable": column_descriptors[column_descriptors_keys[i]]['name'],
                        "Units": column_descriptors[column_descriptors_keys[i]]['units'],
                        "Sensor Name": sensor,
                        "Timestamp": int(seconds) * 1000, #convert to milliseconds to match Newcastle
                        "Value": data_values[i-2],
                        "Flagged as Suspect Reading": '',
                    }
                )

        else:
            if 'sensor.family:' in line:
                family = line.split(':')[1].strip()
            elif 'site.id:' in line:
                site_name = line.split(':')[1].strip()
            elif 'From:' in line:
                from_ = line.split(': ')[1].strip()
            elif 'To:' in line:
                to_ = line.split(': ')[1].strip()
            elif 'site.longitude' in line:
                longitude = line.split(': ')[1].replace(' [deg]', '')
            elif 'site.latitude' in line:
                latitude = line.split(': ')[1].replace(' [deg]', '')
            elif 'site.heightAboveSeaLevel' in line:
                hasl = line.split(':')[1].replace(' [m]', '')
            elif 'sensor.heightAboveGround' in line:
                hag = line.split(':')[1].replace(' [m]', '')
            elif 'sensor.detectors' in line:
                detectors = line.split(': ')[1]
                detectors = [item.strip() for item in detectors.split(',')]
            elif 'ColDescription' in line:
                col = line.split(': ')[1]
                descriptor_keys = col.split(' / ')
            elif 'Column_' in line[2:9]:
                line = line.split('/ ')

                column_dtls = {}

                for i in range(1, len(line)):
                    column_dtls[descriptor_keys[i - 1]] = line[i].strip()
                column_descriptors[line[0][2:].strip()] = column_dtls

    geom = {"0": "POINT (%s %s)" % (longitude, latitude)}

    json_ = {
        'Sensor Name': {"0": '%s' % site_name},
        'Location (WKT)': geom,
        "Sensor Height Above Ground": {"0": '%s' % hag},
        "Raw ID": {"0": "%s" % site_name},
        'data': data_dict,
        "Sensor Centroid Longitude": {"0": "%s" % longitude},
        "Sensor Centroid Latitude": {"0": "%s" % latitude},
        'family': family,
        'from': from_,
        'to': to_,
        'detectors': detectors,
        'column_metatdata': column_descriptors,
    }

    return json_

def convert_csv_to_json(text):
    """
    Converts a text string from a successful API call to the Sheffield Urban Observatories into json matching the format of the json returned from the Newcastle Urban Observatory API.
    """
    response_text = text.splitlines()
    break_points = check_for_multiple_lines(response_text)

    output_ = []
    bp = 0
    for break_point in break_points:
        json_ = read_request_response(response_text[bp:break_point])
        bp = break_point
        output_.append(json_)
    output = {'sensors': output_}

    return json.dumps(output)

def convert_api_json_to_geojson(json_):
    """Convert json to geojson
    """

    json_ = json.loads(json_)
    json_ = json_['sensors']

    # setup dict for data

    geojson = {}

    # add required keys

    geojson["type"] = "FeatureCollection"

    geojson["name"] = ''

    # to be populated

    # this is temp for all data currently in database - need to automate generation of the crs dict

    # geojson["crs"] = {"type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::4326" }}

    # to be populated

    geojson["features"] = []
    for feat in json_:
        #print('FEAT:', feat)
        x, y = feat["Location (WKT)"]['0'].replace('(', '').replace(')', '').split(' ')[1:]

        geometry = {
            "type": "Point",
            "coordinates": [float(x.strip()), float(y.strip())]
        }

        # populate the features key
        # loop through the data
        #for item in json_:

        # create dict to store feature
        feature = {}

        # the data type
        feature["type"] = "Feature"

        # the feature attributes
        feature["properties"] = {}

        # add geom to the data dict
        feature["geometry"] = geometry

        # add all other attributes to data dict
        for attribute in feat.keys():
            #print(feature["properties"])
            try:
                feature["properties"][attribute] = feat[attribute]['0']
            except:
                feature['properties'][attribute] = feat[attribute]

        # add feature dict to geojson features list
        geojson["features"].append(feature)

    return json.dumps(geojson)
