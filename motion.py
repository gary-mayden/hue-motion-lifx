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
PIR_URL = 'http://' + secrets.HUE_BRIDGE + '/api/' + secrets.USER_ID + '/sensors/13'

lastPrint = lastAction = dt.datetime.now()
state = -1

def togglelifx(on):
  if on:
    logger.info("LIFX ON")
  else:
    logger.info("LIFX OFF")

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