import React from 'react'
import ReactDOM from 'react-dom'
import mapboxgl from 'mapbox-gl'
import Grid from '@material-ui/core/Grid';
import SplitPane from 'react-split-pane'
import DateTimePicker from 'react-datetime-picker';
import DatetimeRangePicker from 'react-datetime-range-picker';
import axios from 'axios';
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts';

mapboxgl.accessToken = 'pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4M29iazA2Z2gycXA4N2pmbDZmangifQ.-g_vE53SD2WrJ6tFX7QHmA';

class Application extends React.Component {
  constructor(props: Props) {
    super(props);
    this.state = {
      sheffieldState: {
        slng: -1.4688,
        slat: 53.3811,
        szoom: 13.00
      },
      newcastleState: {
        lng: -1.5929,
        lat: 54.9776,
        zoom: 11.14
      },
      startDate: new Date(),
      endDate: new Date(),
      mapChange: false,
      sheffieldSensors: [],
      newcastleSensors: [],
      sheffieldData: [{ x: 10, y: 30 }, { x: 30, y: 200 }, { x: 45, y: 100 }, { x: 50, y: 400 }, { x: 70, y: 150 }, { x: 100, y: 250 }],
      newcastleData: [{ x: 30, y: 20 }, { x: 50, y: 180 }, { x: 75, y: 240 }, { x: 100, y: 100 }, { x: 120, y: 190 }]
    }

    this.updateMap = this.updateMap.bind(this)
    this.onPopupClick = this.onPopupClick.bind(this)
  }

  async getDataAxios(sheffieldURL, newcastleURL) {
    const sheffieldResponse =
      await axios.get(sheffieldURL)
    const newcastleResponse =
      await axios.get(newcastleURL)

    console.log(sheffieldResponse.data)
    console.log(newcastleResponse.data)

    this.setState({
      mapChange: true,
      sheffieldSensors: sheffieldResponse.data,
      newcastleSensors: newcastleResponse.data
    })
  }

  handleClick = () => {
    var sheffieldURL = "http://localhost:8080/data/sheffield/?starttime=2020-01-01T07:00:00&endtime=2020-01-02T07:00:00&sensor_type=Vehicle+Count&geo_json=true"
    var newcastleURL = "http://localhost:8080/data/newcastle/?starttime=2020-01-01T07:00:00&endtime=2020-01-02T07:10:00&sensor_type=Vehicle+Count&geo_json=true"
    this.getDataAxios(sheffieldURL, newcastleURL)
  }

  onDateChange = (startDate, endDate) => {
    this.setState({
      startDate: startDate,
      endDate: endDate
    })
  }

  onPopupClick = (e, map, newcastle) => {
    var coordinates = e.features[0].geometry.coordinates.slice();

    // Ensure that if the map is zoomed out such that multiple
    // copies of the feature are visible, the popup appears
    // over the copy being pointed to.
    while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
      coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
    }

    var propertiesObject = JSON.parse(e.features[0].properties.data)

    if (newcastle) {
      propertiesObject = propertiesObject['Vehicle Count']
    }
    else {
      propertiesObject = propertiesObject['data~flow']
    }

    var data = []
    for (var i = 0; i < propertiesObject.length; i++) {
      var value = propertiesObject[i]['Value']
      data.push({
        x: (propertiesObject[i]['Timestamp'] - 1577862000000) / 1000 / 60,
        y: value
      })
    }

    if (newcastle) {
      this.setState({
        newcastleData: data
      })
    }
    else {
      this.setState({
        sheffieldData: data
      })
    }


    new mapboxgl.Popup()
      .setLngLat(coordinates)
      .setHTML("Added to plot!")
      .addTo(map);
  }

  updateMap = (that) => {
    console.log("Calling update map!")

    const { lng, lat, zoom } = this.state.newcastleState;
    const newcastleMap = new mapboxgl.Map({
      container: this.newcastleMapContainer,
      style: 'mapbox://styles/mapbox/streets-v9',
      center: [lng, lat],
      zoom
    });


    const { slng, slat, szoom } = this.state.sheffieldState;
    const sheffieldMap = new mapboxgl.Map({
      container: this.sheffieldMapContainer,
      style: 'mapbox://styles/mapbox/streets-v9',
      center: [-1.4688, 53.3811],
      zoom
    });

    if (this.state.sheffieldSensors.length != 0) {
      var imageAddress = "https://cdn.onlinewebfonts.com/svg/img_553938.png"
      sheffieldMap.on('load', () => {
        sheffieldMap.loadImage(imageAddress, (error, image) => {
          if (error) throw error;
          console.log("Adding image")
          sheffieldMap.addImage('car', image);
        });

        sheffieldMap.addSource('sensors', {
          type: 'geojson',
          data: this.state.sheffieldSensors
        });

        sheffieldMap.addLayer({
          "id": "sensors",
          "type": "symbol",
          "source": "sensors",
          "layout": {
            "icon-image": "car",
            'icon-size': 0.02,
            'icon-allow-overlap': true
          }
        })

        sheffieldMap.on('click', 'sensors', function (e) {
          that.onPopupClick(e, sheffieldMap, false)
        });

        // Change the cursor to a pointer when the mouse is over the places layer.
        sheffieldMap.on('mouseenter', 'sensors', function () {
          sheffieldMap.getCanvas().style.cursor = 'pointer';
        });

        // Change it back to a pointer when it leaves.
        sheffieldMap.on('mouseleave', 'sensors', function () {
          sheffieldMap.getCanvas().style.cursor = '';
        });
      });
    }

    if (this.state.newcastleSensors.length != 0) {
      var imageAddress = "https://cdn.onlinewebfonts.com/svg/img_553938.png"
      newcastleMap.on('load', () => {
        newcastleMap.loadImage(imageAddress, (error, image) => {
          if (error) throw error;
          console.log("Adding image")
          newcastleMap.addImage('car', image);
        });

        newcastleMap.addSource('sensors', {
          type: 'geojson',
          data: this.state.newcastleSensors
        });

        newcastleMap.addLayer({
          "id": "sensors",
          "type": "symbol",
          "source": "sensors",
          "layout": {
            "icon-image": "car",
            'icon-size': 0.02,
            'icon-allow-overlap': true
          }
        })

        newcastleMap.on('click', 'sensors', function (e) {
          that.onPopupClick(e, newcastleMap, true)
        });

        // Change the cursor to a pointer when the mouse is over the places layer.
        newcastleMap.on('mouseenter', 'sensors', function () {
          newcastleMap.getCanvas().style.cursor = 'pointer';
        });

        // Change it back to a pointer when it leaves.
        newcastleMap.on('mouseleave', 'sensors', function () {
          newcastleMap.getCanvas().style.cursor = '';
        });
      });
    }


  }

  componentDidUpdate() {
    if (this.state.mapChange) {
      var that = this;
      this.updateMap(that)
      this.setState({
        mapChange: false
      })
    }

  }

  componentDidMount() {
    this.updateMap()
  }

  render() {
    console.log("Logging states!")
    console.log(this.state.sheffieldData)
    console.log(this.state.newcastleData)
    return (
      <SplitPane split="horizontal" defaultSize={600}>
        <SplitPane split="vertical" primary="first" defaultSize={960}>
          <div ref={el => this.newcastleMapContainer = el} className="absolute top right left bottom" />
          <div ref={el => this.sheffieldMapContainer = el} className="absolute top right left bottom" />
        </SplitPane>
        <SplitPane split="vertical" primary="first" defaultSize={960}>
          <div style={{ justifyContent: 'center', alignItems: 'center', padding: '50px' }}>
            <h1>Choose your date range:</h1>
            <br />
            <DatetimeRangePicker
              onChange={this.onDateChange}
              value={this.state.startDate}
            />
            <br />
            <a href="#" onClick={this.handleClick}>
              Click me
            </a>
          </div>
          <ScatterChart
            width={900}
            height={375}
            margin={{
              top: 30, right: 20, bottom: 20, left: 20,
            }}
          >
            <CartesianGrid />
            <XAxis type="number" dataKey="x" name="Timestamp" unit="Minutes" />
            <YAxis type="number" dataKey="y" name="Count" unit="cars/min" />
            <ZAxis type="number" range={[100]} />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Legend />
            <Scatter name="Newcastle" data={this.state.newcastleData} fill="#82ca9d" line shape="diamond" />
            <Scatter name="Sheffield" data={this.state.sheffieldData} fill="#8884d8" line shape="cross" />
          </ScatterChart>
        </SplitPane>
      </SplitPane>

    );
  }
}

ReactDOM.render(<Application />, document.getElementById('app'));
