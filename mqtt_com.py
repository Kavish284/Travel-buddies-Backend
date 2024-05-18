import time
from paho.mqtt import client as mqtt_client

class TripHandler:
    def __init__(self, client_id, client_name, destination_loc, broker='broker.hivemq.com'):
        self.client_id = client_id
        self.client_name = client_name
        self.destination_loc = destination_loc
        self.broker = broker
        self.source_loc = None  # This will be set dynamically based on user's live location
        self.topic = f'travel-buddy/{self.source_loc.lower().replace(" ", "-")}/{self.destination_loc.lower().replace(" ", "-")}'

    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print(f"Failed to connect, return code {rc}")

        client = mqtt_client.Client(self.client_id)
        client.on_connect = on_connect
        client.connect(self.broker)
        return client

    def publish(self, client):
        msg = f"Created By: {self.client_name}\nFrom: {self.source_loc}\nTo: {self.destination_loc}\ncount: 1\n"
        result = client.publish(self.topic, msg, retain=True)
        status = result[0]
        if status == 0:
            print(msg)
            return True
        else:
            print('Trip not published!')
            return False

    def run(self):
        self.source_loc = get_curr_location().split(',')[-2].strip()  # Set the source dynamically
        self.topic = f'travel-buddy/{self.source_loc.lower().replace(" ", "-")}/{self.destination_loc.lower().replace(" ", "-")}'
        client = self.connect_mqtt()
        time.sleep(1)
        client.loop_start()
        success = self.publish(client)
        client.loop_stop()
        client.disconnect()
        return success

class TripSearcher:
    def __init__(self, source, broker='broker.hivemq.com'):
        self.source_loc = source
        self.broker = broker
        self.topic = f'travel-buddy/{self.source_loc.lower().replace(" ", "-")}/+'
        self.client_id = 'id'
        self.client_name = 'name'
        self.trips_queue = []

    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print(f"Failed to connect, return code {rc}")

        client = mqtt_client.Client(self.client_id)
        client.on_connect = on_connect
        client.connect(self.broker)
        return client

    def subscribe(self, client):
        def on_message(client, userdata, msg):
            print(msg.payload.decode())
            actual_msg = msg.payload.decode().split('\n')
            if len(actual_msg) >= 5:
                cname = src = dest = cnt = None
                for item in actual_msg:
                    if item.startswith("Created By:"):
                        cname = item.split(':')[1].strip()
                    elif item.startswith("From:"):
                        src = item.split(':')[1].strip()
                    elif item.startswith("To:"):
                        dest = item.split(':')[1].strip()
                    elif item.startswith("count:"):
                        try:
                            cnt = int(item.split(':')[1].strip())
                        except ValueError:
                            print("Invalid count format:", item.split(':')[1].strip())
                if cname and src and dest and cnt is not None:
                    self.trips_queue.append((cname, src, dest, cnt))
                else:
                    print("Incomplete message format:", msg.payload.decode())
            else:
                print("Invalid message format:", msg.payload.decode())

        client.subscribe(self.topic)
        client.on_message = on_message

    def run(self):
        client = self.connect_mqtt()
        client.loop_start()
        self.subscribe(client)
        time.sleep(3)
        client.unsubscribe(self.topic)
        client.loop_stop()
        client.disconnect()
        return self.trips_queue

class TripClearer:
    def __init__(self, source, destination, broker='broker.hivemq.com'):
        self.source_loc = source
        self.destination_loc = destination
        self.topic = f'travel-buddy/{self.source_loc.lower().replace(" ", "-")}/{self.destination_loc.lower().replace(" ", "-")}'
        self.client_id = 'tourist_1'
        self.client_name = 'Tourist 1'
        self.broker = broker

    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print(f"Failed to connect, return code {rc}")

        client = mqtt_client.Client(self.client_id)
        client.on_connect = on_connect
        client.connect(self.broker)
        return client

    def publish(self, client):
        result = client.publish(self.topic, '', retain=True)
        status = result[0]
        if status == 0:
            print('Timeout! Trip Cleared Successfully!')
            return True
        else:
            print('Trip not published!')
            return False

    def run(self):
        client = self.connect_mqtt()
        time.sleep(1)
        client.loop_start()
        success = self.publish(client)
        client.loop_stop()
        client.disconnect()
        return success

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

if __name__ == '__main__':
    # Usage Example:

    # Add Trip
    trip_adder = TripHandler(client_id='1234', client_name='Alice', destination_loc='Chicago Downtown')
    trip_adder.run()

    # Search Trip
    trip_searcher = TripSearcher(source='IU Sample Gates')
    trip_results = trip_searcher.run()
    print(trip_results)

    # Clear Trip
    trip_clearer = TripClearer(source='IU Sample Gates', destination='Chicago Downtown')
    trip_clearer.run()
