import time
import datetime as dt
import os
import sys
import json
import requests
import logging
from logging.handlers import RotatingFileHandler
import traceback
import secrets
import hashlib
import hmac
import uuid
import secrets

logger = logging.getLogger()
logger.setLevel(logging.INFO)
dirName = os.path.dirname(os.path.realpath(__file__))
handler = RotatingFileHandler(os.path.join(dirName, 'pir.log'), maxBytes=20 * 1024 * 1024)
formatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


COOL_DOWN = (6 * 10)
PIR_URL = 'http://' + secrets.HUE_BRIDGE + '/api/' + secrets.USER_ID + '/sensors/2'
LIFX_STATE = 'https://api.lifx.com/v1/lights/' + secrets.LIFX_ID + '/state'
LIFX_HEADERS = {
  "Authorization": "Bearer %s" % secrets.LIFX_TOKEN,
}
TUYA_STATE = 'https://openapi.tuyaus.com/v1.0/iot-03/devices/' + secrets.TUYA_DEVICE_ID + '/commands'
TUYA_HEADERS = {
    "sign_method": "HMAC-SHA256",
    "client_id": secrets.TUYA_CLIENT_ID,
    "t": str(int(time.time() * 1000)),
    "mode": "cors",
    "Content-Type": "application/json",
    "sign": "",
    "access_token": secrets.TUYA_CLIENT_SECRET,
}

lastPrint = lastAction = dt.datetime.now()
state = -1

def toggleTuya(on):
  if on:
    payload = {
      "commands": [{"code": "switch_led", "value": True}]
    }
    putTUYAState(payload)
    logger.info("TUYA ON")
  else:
    payload = {
      "commands": [{"code": "switch_led", "value": False}]
    }
    putTUYAState(payload)
    logger.info("TUYA OFF")

def putTUYAState(payload):
    try:
        nonce = str(uuid.uuid4())

        t = str(int(time.time() * 1000))

        stringToSign = "POST\n\n{}\n{}\n{}".format(
            hashlib.sha256(json.dumps(payload).encode('utf-8')).hexdigest(),
            nonce,
            TUYA_STATE
        )

        str_to_sign = "{}{}{}{}{}".format(
            secrets.TUYA_CLIENT_ID,
            secrets.TUYA_CLIENT_SECRET,
            t,
            nonce,
            stringToSign
        )

        signature = hmac.new(
            secrets.TUYA_CLIENT_SECRET.encode('utf-8'),
            str_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()

        TUYA_HEADERS["sign"] = signature

        response = requests.post(TUYA_STATE, data=json.dumps(payload), headers=TUYA_HEADERS)
        json_data = json.loads(response.text)
        logger.info(json_data)
        return json_data['success'] is True
    except:
        logger.exception("exception occurred")
        return True

def togglelifx(on):
  if on:
    payload = {
      "power": "on",
    }
    putLIFXState(payload)
    logger.info("LIFX ON")
  else:
    payload = {
      "power": "off",
    }
    putLIFXState(payload)
    logger.info("LIFX OFF")    

def putLIFXState(payload):
    try:
      response = requests.put(LIFX_STATE, data=payload, headers=LIFX_HEADERS)
      json_data = json.loads(response.text)
      logger.info(json_data['results'])
      return json_data['results'] is True
    except:
      logger.exception("LIFX exception occurred")
      return True  

def getPirState():
  try:
    response = requests.get(PIR_URL)
    json_data = json.loads(response.text)
    return json_data['state']['presence'] is True
  except:
    logger.exception("exception occurred")
    return True


logger.info("*** START ***")
logger.info("PIR URL: " + PIR_URL)
while True:
  now = dt.datetime.now()
  pir = getPirState()

  if (now - lastPrint).total_seconds() > 30:
    logger.info("state - current: " + str(pir) + ", master: " + str(state))
    lastPrint = now

  if pir is True:
    lastAction = now
    if state != 1:
      state = 1
      togglelifx(True)
      toggleTuya(True)
  elif pir is False and (now - lastAction).total_seconds() > COOL_DOWN:
    lastAction = now
    state = 0
    togglelifx(False)
    toggleTuya(False)

  time.sleep(.5)