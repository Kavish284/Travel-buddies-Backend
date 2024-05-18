from flask import Flask, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
import datetime
import requests
from mqtt_com import TripHandler, TripSearcher, TripClearer
import pymysql

pymysql.install_as_MySQLdb()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///students.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
app.app_context().push()
ma = Marshmallow(app)

# Database model
class Trips(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(200))
    lastname = db.Column(db.String(200))
    source = db.Column(db.String(200))
    destination = db.Column(db.String(200))
    datecreated = db.Column(db.DateTime, default=datetime.datetime.now())

    def __init__(self, firstname, lastname, source, destination):
        self.firstname = firstname
        self.lastname = lastname
        self.source = source
        self.destination = destination

# Marshmallow schema
class TripSchema(ma.Schema):
    class Meta:
        fields = ('id', 'firstname', 'lastname', 'source', 'destination', 'datecreated')

trip_schema = TripSchema()
trips_schema = TripSchema(many=True)

# Routes for CRUD operations
@app.route('/get', methods=['GET'])
def get_trips():
    all_trips = Trips.query.all()
    results = trips_schema.dump(all_trips)
    return jsonify(results)

# Other CRUD routes (get_trip, add_trip, update_trip, delete_trip) can be added here...

# MQTT search and clear routes
@app.route('/mqttsearch', methods=['GET'])
def mqtt_search_trips():
    mqtt_trips = TripSearcher(source='YourSourceHere')  # Provide the appropriate source
    res = mqtt_trips.run()
    return jsonify(res)

@app.route('/mqttclear', methods=['GET'])
def mqtt_clear():
    clear_trips = TripClearer(source='YourSourceHere', destination='YourDestinationHere')  # Provide the appropriate source and destination
    res = clear_trips.run()
    return jsonify({'Action': 'Trips Cleared Successfully'}) if res else jsonify({'Action': 'Could not clear Trips'})

# Helper function to get current location
def get_curr_location():
    response = requests.get('https://ipinfo.io/json')
    data = response.json()
    lat, lon = data['loc'].split(',')
    api_key = 'c6e3c9905f104ecf8514cf640a9cfe32'
    url = f'https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={api_key}&language=en'
    response = requests.get(url)
    data = response.json()
    location_name = data['results'][0]['formatted']
    return location_name

# Route to get current location
@app.route('/curr_location', methods=['GET'])
def curr_location():
    res = get_curr_location()
    loc = res.split(',')[-2].strip()
    return jsonify({'curr': loc})

# Routes for getting trips based on location
@app.route('/location', methods=['POST'])
def get_location():
    if request.method == 'POST':
        location = request.json['location']
        return redirect(url_for('location_trips', location=location))
    
@app.route('/location_trips', methods=['GET'])
def location_trips():
    loc = get_curr_location()
    loc = loc.split(',')[-2].strip()
    result = db.session.query(Trips).filter(Trips.source == loc).all()
    data = [{'firstname': res.firstname, 
             'lastname': res.lastname, 
             'source':res.source, 
             'destination':res.destination, 
             'datecreated': res.datecreated,
             'id': res.id} for res in result]
    mq_search = TripSearcher(loc)  # Assuming you want to search based on location
    res = mq_search.run()
    print(res)
    return jsonify(data)

# Route for guide trips
@app.route('/guide', methods=['GET'])
def get_gtrips():
    loc = get_curr_location()
    loc = loc.split(',')[-2].strip()
    result = db.session.query(Trips).filter(Trips.destination == loc).all()
    data = [{'firstname': res.firstname, 
             'lastname': res.lastname,
             'source':res.source, 
             'destination':res.destination, 
             'datecreated': res.datecreated,
             'id': res.id} for res in result]
    mq_search = TripSearcher(loc)  # Assuming you want to search based on location
    res = mq_search.run()
    print(res)
    return jsonify(data)

if __name__ == '__main__':
    app.run()
