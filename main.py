"""
This script reads data from an Adafruit SHTC3 sensor and publishes it to a MQTT
broker.
"""

import datetime
import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler

import adafruit_shtc3
import board
import paho.mqtt.client as mqttc

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s: %(message)s"
)
_logger = logging.getLogger(__name__)
logging.getLogger("").handlers = []
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.DEBUG)
_logger.addHandler(console_handler)

file_handler = RotatingFileHandler(
    f"/logs/{__name__}.log", maxBytes=500000000, backupCount=1
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
_logger.addHandler(file_handler)

# MQTT Broker parameters
BROKER_HOST = os.getenv("BROKER_HOST")
BROKER_PORT = int(os.getenv("BROKER_PORT"))
BROKER_USER = os.getenv("BROKER_USER")
BROKER_PWD = os.getenv("BROKER_PWD")
# MQTT topic to publish to
HS_SHTC3_TOPIC = os.getenv("BROKER_TOPIC")


def on_connect(client, userdata, flags, rc):
    """
    Callback for when the client receives a CONNACK response from the broker.
    Subscribes to all topics defined in the TOPICS list.

    Parameters
    ----------
    client : mqttc.Client
        The client instance for this callback.
    userdata : any
        The user data as passed to the Client() constructor or user_data_set().
    flags : dict
        Response flags sent by the broker.
    rc : int
        The connection result.
    """
    if rc == 0:
        _logger.info(f"MQTT client connected to host {BROKER_HOST}:{BROKER_PORT}")
    else:
        _logger.debug(
            f"Could not connect to {BROKER_HOST}:{BROKER_PORT}: error code {rc}"
        )


def on_disconnect(client, userdata, rc):
    """
    Callback for when the client disconnects from the broker.

    Parameters
    ----------
    client : mqttc.Client
        The client instance for this callback.
    userdata : any
        The user data as passed to the Client() constructor or user_data_set().
    rc : int
        The disconnection result.
    """
    _logger.info(f"MQTT client disconnected from host {BROKER_HOST}:{BROKER_PORT}")


def connect_mqtt():
    """
    Connects to the MQTT broker and returns the client instance.

    Returns
    -------
    mqttc.Client
        The client instance for this callback.
    """
    client = mqttc.Client(client_id=None, clean_session=True)
    client.enable_logger(logger=_logger)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    client.username_pw_set(username=BROKER_USER, password=BROKER_PWD)
    client.connect(host=BROKER_HOST, port=BROKER_PORT)

    return client


def publish_shtc3_data(client, topic, shct3):
    """
    Publish data to a MQTT topic.

    Parameters
    ----------
    client : mqttc.Client
        The client instance for this callback.
    topic : str
        The topic to publish to.
    data : dict
        The data to publish.
    """
    data = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": shtc3.temperature,
        "humidity": shtc3.relative_humidity,
    }
    client.publish(topic=HS_SHTC3_TOPIC, payload=json.dumps(data), qos=1, retain=True)
    _logger.info(f"Publishing data to topic {topic}: {data}")
    time.sleep(15 * 60)


if __name__ == "__main__":
    i2c = board.I2C()
    shtc3 = adafruit_shtc3.SHTC3(i2c)

    try:
        while True:
            try:
                client = connect_mqtt()
                publish_shtc3_data(client, HS_SHTC3_TOPIC, shtc3)
            except Exception:
                _logger.exception("Error publishing data")
                continue
    except KeyboardInterrupt:
        _logger.info("Stopping script")
