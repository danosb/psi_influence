# Used to pull data from the Emotiv Epoch EEG. 
# Requires node-red server and mosquitto

import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("bands_alpha")
    client.subscribe("bands_beta-high")
    client.subscribe("bands_beta_low")
    client.subscribe("bands_gamma")
    client.subscribe("bands_theta")
    client.subscribe("metrics_excitement")
    client.subscribe("metrics_focus")
    client.subscribe("metrics_interest")
    client.subscribe("metrics_engagement")
    client.subscribe("metrics_stress")
    client.subscribe("metrics_relaxation")
    client.subscribe("metrics_longtermexcitement")
    client.subscribe("metrics_mn8-attention")
    client.subscribe("metrics_mn8-cognitivestress")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("Topic: " + msg.topic + "\nMessage: " + str(msg.payload.decode()))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
