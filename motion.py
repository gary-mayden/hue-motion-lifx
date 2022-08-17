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


logger = logging.getLogger()
logger.setLevel(logging.INFO)
dirName = os.path.dirname(os.path.realpath(__file__))
handler = RotatingFileHandler(os.path.join(dirName, 'pir.log'), maxBytes=20 * 1024 * 1024)
formatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


COOL_DOWN = (60 * 10)
PIR_URL = 'http://' + secrets.HUE_BRIDGE + '/api/' + secrets.USER_ID + '/sensors/23'
LIFX_STATE = 'https://api.lifx.com/v1/lights/' + secrets.LIFX_ID + '/state'
LIFX_HEADERS = {
  "Authorization": "Bearer %s" % secrets.LIFX_TOKEN,
}

lastPrint = lastAction = dt.datetime.now()
state = -1

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
      logger.info(json_data['results'])
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
  elif pir is False and (now - lastAction).total_seconds() > COOL_DOWN:
    lastAction = now
    state = 0
    togglelifx(False)

  time.sleep(2.0)