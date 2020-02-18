import requests
import pandas as pd

class GetData:

    @staticmethod
    def sheffield(start, end):
        """

        :param start:
        :param end:
        :return:
        """

        sh_resp = requests.get(f"http://localhost:8080/data/sheffield/?starttime={start.isoformat()}&endtime={end.isoformat()}&sensor_type=Vehicle+Count")

        # Remove empty data entries
        sh_cleaned = [sensor for sensor in sh_resp.json()['sensors'] if sensor['data']]

        # Convert to pandas dataframe
        dataf = pd.json_normalize(sh_cleaned, ['data', "data~flow"],
                                ['Sensor Centroid Latitude', 'Sensor Centroid Longitude'])

        # make conversions
        dataf['Timestamp'] = pd.to_datetime(dataf['Timestamp'], unit='s')
        dataf['Value'] = dataf['Value'].astype(float)
        dataf['latitude'] = [float(lat['0']) for lat in dataf['Sensor Centroid Latitude'].values.tolist()]
        dataf['longitude'] = [float(lon['0']) for lon in dataf['Sensor Centroid Longitude'].values.tolist()]

        return dataf


    @staticmethod
    def newcastle(start, end):
        """

        :param start:
        :param end:
        :return:
        """

        nc_resp = requests.get(f"http://localhost:8080/data/newcastle/?starttime={start.isoformat()}&endtime={end.isoformat()}&sensor_type=Vehicle+Count")

        # Remove empty data entries
        nc_cleaned = [sensor for sensor in nc_resp.json()['sensors'] if sensor['data']]

        # Convert to pandas dataframe
        dataf = pd.json_normalize(nc_cleaned, ['data', 'Vehicle Count'],
                                ['Sensor Centroid Latitude', 'Sensor Centroid Longitude'])

        # make conversions
        dataf['Timestamp'] = pd.to_datetime(dataf['Timestamp'], unit='ms')
        dataf['latitude'] = [lat['0'] for lat in dataf['Sensor Centroid Latitude'].values.tolist()]
        dataf['longitude'] = [lat['0'] for lat in dataf['Sensor Centroid Longitude'].values.tolist()]

        return dataf