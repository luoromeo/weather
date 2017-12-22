# coding=utf-8

import requests
import json

# api_url
temperature_url = "http://api.yeelink.net/v1.1/device/354653/sensor/400827/datapoints"

# api_headers
api_headers = {'U-ApiKey': 'ca139804ec402cab4174bf15ec1c9e9f', 'content-type': 'application/json'}


def pos_temperature(v):
    value = {"value": v}
    r = requests.post(temperature_url, headers=api_headers, data=json.dumps(value))
    return r
