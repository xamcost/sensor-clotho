# Sensor-clotho

A simple containerized app to read data from an [Adafruit SHTC3](https://learn.adafruit.com/adafruit-sensirion-shtc3-temperature-humidity-sensor/overview)
sensor on a Raspberry Pi, and publish them to an MQTT broker. If you only
use this sensor, you should be able to use this app without any modification
of its code, just by setting environment variables.

Feel free to fork the repo to extend this app to read other sensors plugged on your
Raspberry Pi.

## How to use

There is three ways to run this app:
1. executing directly the `main.py` script
2. using the Docker image
3. deploying it on a Kubernetes cluster

### Prerequisites

#### Enabling i2c on the Raspberry Pi

Make sure i2c and SPI are enabled on your Raspberry Pi. For this, you can use
`raspi-config`:

```bash
sudo raspi-config
```

and then navigate to *interfaces* and enable i2c and SPI. You can check it using:

```bash
ls /dev/i2c* /dev/spi*
```

This should print the list of i2c/spi devices.

#### Logging

By default, this app logs both in the console and in a file (the size of the
latter is limited to 500 Mb). The reason behind this is to enable checking old
log messages. Because of the file logging, executing directly
the python script locally may throw an error: you can avoid this by either
commenting/removing this logging handler, or by adjusting the file path to
an existing directory on your machine.

The file logging is also the reason why a persistent volume is required for
the Docker container (and therefore a volume claim in the kubernetes manifests).
Feel free to delete this file handler from the code and get rid of this volume.

### Executing the main script

First, install the relevant dependencies:
```bash
sudo apt-get install -y i2c-tools libgpiod-dev gcc
```

Set a Python environment (this app has been tested with Python 3.10.6):
```bash
python -m venv <path/to/your/env>
source <path/to/your/env>/bin/activate
```

Install Python dependencies:
```bash
pip install --no-cache-dir --upgrade -r /code/requirements.txt
```

Then, set the relevent environment variables:
- `BROKER_HOST`: the MQTT broker host name
- `BROKER_PORT`: the MQTT broker port
- `BROKER_USER`: the MQTT broker user
- `BROKER_PWD`: the MQTT broker password
- `BROKER_TOPIC`: the topic to publish the messages to

Before running the script, you can comment the instantiation of the
`RotatingFileHandler` for logs, or modify where it writes the log file,
to avoid an error. Then:

```bash
python -m main
```

### Using the Docker image

The app image is built on the [python 3.10.6-slim-buster for Linux arm64 v8](https://hub.docker.com/layers/library/python/3.10.6-slim-buster/images/sha256-71afed5910cdec96814776079578269e194088a06a64952daebf0d745c1f105d?context=explore).
Build the image yourself, or pull it from the registry:

```bash
docker pull ghcr.io/xamcost/sensor-clotho:latest
```

Create a directory to store logs:

```bash
mkdir ./logs
```

Then, run it **passing your i2c/spi devices** and the environment variables:

```bash
docker run --device /dev/i2c-0 --device /dev/i2c-1 \
-v ./logs:/logs \
-e BROKER_HOST=<mqtt_host> \
-e BROKER_PORT=<mqtt_port> \
-e BROKER_USER=<mqtt_user> \
-e BROKER_PWD=<mqtt_pwd> \
-e BROKER_TOPIC=<mqtt_topic> \
--name sensor-clotho ghcr.io/xamcost/sensor-clotho:latest
```

You can check the logs to see if it's working as expected:

```bash
docker logs --follow sensor-clotho
```

### Deploying on a Kubernetes cluster

That's what I am doing, on a cluster of Raspberry Pi 4 managed by k3s.
You can find the manifests in the `kubernetes_manifests` directory.
The latter not only covers this app, but also deploy a
[Smarter device manager](https://github.com/smarter-project/smarter-device-manager/tree/main),
since as of now, Kubernetes does not allow access to host devices without
enabling privileges. A big thanks to the fellows of [Arm research](https://getsmarter.io/)
for this open-source work. Two small things to note about the device manager
in the present case:
- it is deployed solely for one node. If you want it to automatically expose devices
on other nodes of your cluster, use a `nodeSelector` instead, as shown
[here](https://github.com/smarter-project/smarter-device-manager/blob/6ebcbefa2592f83baab3bac903c2500fe649c799/smarter-device-manager-ds-k3s.yaml#L29-L30)
- the configmap here exposes all devices of the Raspberry Pi. You may want to
narrow this down to your needs only.

Prior to deployment, first set a few environment variables in your shell:

```bash
export MQTT_BROKER_USER=<user>
export MQTT_BROKER_PWD=<password>
export MQTT_BROKER_PWD=<host>
export MQTT_BROKER_PORT=<port>
export SENSOR_CLOTHO_SHTC3_TOPIC=<topic to publish data>
export SENSOR_CLOTHO_NODE=<name of node to deploy app on>
export SENSOR_CLOTHO_STORAGECLASS=<name of the storage class to use for persistent volume claim>
```

Then, deploy:
```bash
cat ./kubernetes_manifests/*.yaml | envsubst | kubectl apply -f -
```
