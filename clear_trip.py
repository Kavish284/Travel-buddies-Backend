import time
from paho.mqtt import client as mqtt_client

class MqttClear:
    """Class for clearing MQTT trip data."""

    def __init__(self):
        self.broker = 'broker.hivemq.com' 
        self.topic = 'travel-buddy/any/any'
        self.client_id = 'tourist_1'  # From app
        self.client_name = 'Tourist 1'  # From app

    def connect_mqtt(self):
        """Connect to the MQTT broker."""
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
        """Publish an empty message to clear trip data."""
        result = client.publish(self.topic, '', retain=True)
        status = result[0]
        if status == 0:
            print('Timeout! Trip Cleared Successfully!')
            return True
        else:
            print('Trip not published!')
            return False

    def run(self):
        """Run the process to clear trip data."""
        client = self.connect_mqtt()
        time.sleep(1)
        client.loop_start()
        success = self.publish(client)
        client.loop_stop()
        client.disconnect()
        return success
