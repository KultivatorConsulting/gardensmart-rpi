import json
import logging
import ssl
import os
import signal
import sys
import time

from paho.mqtt import client as mqtt_client

from state_store import StateStore
from relay_driver import *

exe_dir = os.path.dirname(__file__)

config_path = exe_dir + '/etc/gardensmart.config.json'
loggin_path = exe_dir + '/log/gardensmart_irrigator.log'

client = None
config = None
state_store = None

logging.basicConfig(
    filename=loggin_path,
    format='%(asctime)s %(name)-15s %(levelname)-8s %(processName)-10s %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger('gardensmart_irrigatorService')
logger.info('Started GardenSmart Irrigator Service Logger')

def signal_handler(signal, frame):
    logger.info('GardenSmart service is stopping')
    client.disconnect()
    client.loop_stop(force=False)
    logger.info('GardenSmart service has stopped')
    sys.exit(os.EX_OK)

def load_config_json():
    if os.path.isfile(config_path):
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
            config_file.close()
            return config

config = load_config_json()

broker = config.get('broker')
client_id = broker.get('clientId')
username = broker.get('username')
password = broker.get('password')
ca_certs = broker.get('caCerts')
cert_file = broker.get('certFile')
key_file = broker.get('keyFile')
host = broker.get('host')
port = broker.get('port')

topic_commands = config.get('topicCommands')
topic_irrigators = config.get('topicIrrigators')
topic_zones = config.get('topicZones')

def connect() -> mqtt_client:
    client = mqtt_client.Client(client_id)
    client.enable_logger(logger)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.tls_set(
      ca_certs,
      cert_file,
      key_file,
      cert_reqs=ssl.CERT_REQUIRED,
      tls_version=ssl.PROTOCOL_TLS,
      ciphers=None
    )
    client.tls_insecure_set(True)
    client.connect(host, port)
    return client

def subscribe(client: mqtt_client):
    client.subscribe(topic_commands)
    client.subscribe(topic_irrigators)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())

    if (msg.topic == topic_commands):
        if (payload['command'] == 'getZones'):
            publish_zones()

    if (msg.topic == topic_irrigators):
        if (payload['operation'] == 'valveOnDuration' and payload['relayId'] is not None):
            relay_on(payload['relayId'])
            state_store.set_zone_valve_on(payload['relayId'], payload['parameters']['duration'])

        if (payload['operation'] == 'valveOff' and payload['relayId'] is not None):
            relay_off(payload['relayId'])
            state_store.clear_zone_valve(payload['relayId'])

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info('Connected to MQTT Broker!')
        subscribe(client)
    else:
        logger.error('Failed to connect, return code %d\n', rc)

def on_subscribe(client, userdata, mid, granted_qos):
    logger.info('Subscribed to MQTT Broker!')

def publish_zones():
    zones = config.get('irrigatorService')
    for zone in zones['zones']:
        time_remaining = state_store.get_zone_valve_time_remaining(zone['relayId'])

        zone['isValveOpen'] = relay_get_port_status(zone['relayId'])
        zone['remainingTime'] = time_remaining
        zone['flowRate'] = 0

    payload = json.dumps(zones['zones'])
    client.publish(topic_zones, payload)

def if_irrigators_active():
    active = False
    zones = config.get('irrigatorService')
    for zone in zones['zones']:
        if (relay_get_port_status(zone['relayId']) == True):
            active = True

    return active

def check_timers():
    zones = config.get('irrigatorService')
    for zone in zones['zones']:
        time_remaining = state_store.get_zone_valve_time_remaining(zone['relayId'])
        if (time_remaining is not None and time_remaining < 0):
            relay_off(zone['relayId'])
            state_store.clear_zone_valve(zone['relayId'])

signal.signal(signal.SIGHUP, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

state_store = StateStore(logger)

client = connect()
client.loop_start()

while True:
    time.sleep(1)
    if (if_irrigators_active()):
        check_timers()
        publish_zones()
    pass
