import dash
from dash.dependencies import Input, Output, State

import dash_html_components as html
import dash_core_components as dcc

import datetime as dt
import plotly.graph_objs as go
import numpy as np

from plot_builder import Plotter

plotter = Plotter()

app = dash.Dash(__name__)

app.layout = html.Div(id='data_background', children=[

                 html.Div(className='middle_container', children=[
                    dcc.DatePickerSingle(
                        id='date-picker-single',
                        initial_visible_month=dt.datetime(2020, 1, 1),
                        date=dt.date(2020, 1, 1),

                    ),

                 ])
                 ,
                 html.Div(style={'clear': 'left'})

                    ,


                 html.Div(className='middle_container', children=[

                    html.Div(id='core_vis_container',
                             className='map_container', children=[

                        html.H2('Sheffield', id='core_data_title'),

                        html.Div(id='data_container',children=[
                            dcc.Graph(id='core-map')
                            ]),
                    ])
                    ,
                    html.Div(id='unc_vis_container', className='map_container',
                             children=[

                        html.H2('Newcastle', id='unc_data_title'),

                        html.Div(id='unc_container', children=[
                            dcc.Graph(id='unc-map')
                            ]),


                    ]),
                    html.Div(style={'clear': 'left'})
                    ]),

                 html.Div(id="times_container", className='middle_container',
                          children=[
                     html.Div(id='timeseries_container',children=
                        [dcc.Graph(id='pixel_timeseries')
                        ]),
                ])
             ])


@staticmethod
@app.callback(Output(component_id='core-map', component_property='figure'),
              [Input('date-picker-single', 'date')])
def update_sheffield_map(date):
    """
    Update the map in response to click on the slider or the timeseries
    """
    return plotter.create_sheffield_map(date)

@staticmethod
@app.callback(Output(component_id='unc-map', component_property='figure'),
              [Input('date-picker-single', 'date')])
def update_newcastle_map(date):
    """
    Update the map in response to click on the slider or the timeseries

    """
    return plotter.create_newcastle_map(date)

@staticmethod
@app.callback(Output(component_id='pixel_timeseries', component_property='figure'),
              [Input(component_id='core-map', component_property='clickData'),
               Input(component_id='unc-map', component_property='clickData')])
def update_timeseries(sh_point, nc_point):
    """
    """

    # Isolate the input which has triggered this callback
    trigger = dash.callback_context.triggered[0]

    if trigger['value']:

        # Update latitude and longitude from map click
        latitude = trigger['value']['points'][0]['lat']
        longitude = trigger['value']['points'][0]['lon']

        # Create the timeseries plot
        timeseries_plot = plotter.update_timeseries(latitude, longitude)

        return timeseries_plot

    else:

        layout = go.Layout(
            xaxis={'ticks': '', 'showticklabels': False,
                   'zeroline': False, 'showgrid':False},
            yaxis={'ticks': '', 'showticklabels': False,
                   'zeroline': False, 'showgrid':False},
            #width=1265,
            #height=271,
            autosize=True,#False,
            margin=go.layout.Margin(
                l=80,
                r=0,
                b=80,
                t=30,
                pad=4)
        )

        dummy_data = [go.Scatter(
            x=np.arange(5),
            y=np.arange(5)*np.nan
        )]

        return {'data': dummy_data, 'layout': layout}


if __name__ == '__main__':
    app.run_server(debug=True)