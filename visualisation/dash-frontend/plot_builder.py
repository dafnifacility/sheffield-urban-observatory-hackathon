import plotly.express as px
from get_data import GetData
import datetime as dt
import pandas as pd
import plotly.graph_objects as go
import numpy as np

class Plotter:

    def __init__(self):

        self.access_token = 'pk.eyJ1IjoiYmV0aGFubWFyeSIsImEiOiJjazZqaGNuNjUwYXkyM2VtZWV6NG9hOWduIn0.0Mo4fVxPTQdMbJxuMzb2WA'

        self.timeseries_data = pd.DataFrame()

        pass

    def create_sheffield_map(self, date):
        """
        Build the map
        """
        date = dt.datetime.strptime(date, "%Y-%m-%d")

        start = dt.datetime(date.year, date.month, date.day, 0, 0)
        end = dt.datetime(date.year, date.month, date.day, 23, 59)

        px.set_mapbox_access_token(self.access_token)

        self.sh_dframe = GetData.sheffield(start, end)

        figure = px.scatter_mapbox(self.sh_dframe , lat="latitude", lon="longitude", color="Value",
                          color_continuous_scale=px.colors.cyclical.IceFire, size_max=15, zoom=10)

        return figure

    def create_newcastle_map(self, date):
        """
        Build the map
        """
        date = dt.datetime.strptime(date, "%Y-%m-%d")

        start = dt.datetime(date.year, date.month, date.day, 0, 0)
        end = dt.datetime(date.year, date.month, date.day, 23, 59)

        px.set_mapbox_access_token(self.access_token)

        self.nc_dframe = GetData.newcastle(start, end)

        figure = px.scatter_mapbox(self.nc_dframe , lat="latitude", lon="longitude", color="Value",
                          color_continuous_scale=px.colors.cyclical.IceFire, size_max=15, zoom=10)

        return figure

    def update_timeseries(self, lat, lon):
        """
        :param df:
        :return:
        """

        column_name = f"{lat}, {lon}"

        # Check the two datasets for this latitude and longitude
        sh_sensors_here = self.sh_dframe[(self.sh_dframe.latitude.eq(lat)) & (self.sh_dframe.longitude.eq(lon))]
        nc_sensors_here = self.nc_dframe[(self.nc_dframe.latitude.eq(lat)) & (self.nc_dframe.longitude.eq(lon))]

        # concatenate (one should be empty)
        sensors_here = pd.concat([sh_sensors_here, nc_sensors_here])

        # Switch the index to be time
        sensors_here = sensors_here.set_index(sensors_here['Timestamp'])

        # Add in the right column name
        sensors_here.rename(columns={'Value': column_name}, inplace=True)

        # Add this to the timeseries dataframe
        self.timeseries_data = pd.concat([self.timeseries_data, sensors_here[column_name]], axis=1)


        fig = go.Figure()
        for column in self.timeseries_data.columns:
            fig.add_trace(go.Scatter(x=self.timeseries_data.index, y=self.timeseries_data[column],
                                     mode='markers', name=column))

        return fig

    def clear_timeseries(self):

        self.timeseries_data = pd.DataFrame()

        layout = go.Layout(
            xaxis={'ticks': '', 'showticklabels': False,
                   'zeroline': False, 'showgrid': False},
            yaxis={'ticks': '', 'showticklabels': False,
                   'zeroline': False, 'showgrid': False},
            autosize=True,  # False,
            margin=go.layout.Margin(
                l=80,
                r=0,
                b=80,
                t=30,
                pad=4)
        )

        dummy_data = [go.Scatter(
            x=np.arange(5),
            y=np.arange(5) * np.nan
        )]

        return {'data': dummy_data, 'layout': layout}
