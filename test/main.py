# ----------------------------------------------------------------------------
# Simple testprogram for the Tesserae-API library.
#
# This program focusses on API tests, it does not display anything.
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/circuitpython-tesserae
# ----------------------------------------------------------------------------

INTERVAL = 15

import time

import adafruit_requests
from tesserae_api import Tesserae_ID, Tesserae_API

# Get hostname and wifi details from a settings.py file
try:
  from settings import secrets
except ImportError:
  print("WiFi secrets are kept in settings.py, please add them there!")
  raise

# Get application settings from settings.py
try:
  from settings import app_config
except ImportError:
  print("application configuration is in settings.py, please add them there!")
  raise

# --- connect-helper   -------------------------------------------------------

def connect():
  """ try to connect """
  for _ in range(3):
    try:
      print("connecting to AP...")
      wifi.radio.connect(secrets.ssid, secrets.password)
      print("... connected")
      break
    except Exception as e:
      print("Failed:\n", e)
      time.sleep(1)
      continue

# --- output helper   ---------------------------------------------------------

def pp_dict(d):
  """ pretty-print dict """
  print("{")
  for key, value in d.items():
    print(f"  {key}: {value}")
  print("}")

# --- discovery helper   ------------------------------------------------------

def discover():
  """ use discovery """
  while not app_config.token:
    code, resp = api.discover()
    if code != 200:
      # bail out
      raise RuntimeError(f"Tesserae-Server HTTP-Code: {code}, content: {resp}")
    if resp.get("registered",False):
      print(f"registered with token: {api.token}")
      app_config.token = api.token
      return
    wait_time = resp.get("retry_after_s",30)
    print(f"not registered yet, retrying in {wait_time}s")
    time.sleep(wait_time)

# --- register helper   -------------------------------------------------------

def register(pairing_code):
  """ use fallback registration """

  code, resp = api.register(pairing_code)
  if code != 201:
    # bail out
    raise RuntimeError(f"Tesserae-Server HTTP-Code: {code}, content: {resp}")
  print(f"registered with token: {api.token} (reused: {resp.reused_existing}")
  app_config.token = api.token

# --- main program   ----------------------------------------------------------

try:
  import wifi
  import socketpool
  connect()
  pool = socketpool.SocketPool(wifi.radio)
except:
  # CPython
  import socket as pool

req_factory = adafruit_requests.Session(pool)

panel = Tesserae_ID("test_id", 400, 300, app_config.mac)
api = Tesserae_API(panel.id, app_config.url, req_factory, token=app_config.token,
                   debug=app_config.debug)

# skip discovery/registration if we have a token
if not app_config.token:
  if hasattr(app_config, "pairing_code"):
    register(app_config.pairing_code)
  else:
    discover()

# query current frame url and print it
while True:
  code, resp = api.frame()
  print(f"api.frame(): HTTP-code: {code}")
  if code == 200:
    pp_dict(resp)
  elif code == 304:
    print("not modified")

  # send status (fake battery)
  code, resp = api.status({"battery_mv": 3850})
  print(f"api.status(): HTTP-code: {code}")
  if code == 200:
    pp_dict(resp)
  else:
    raise RuntimeError(f"unexpected HTTP return code {code}")

  # sleep as requested
  wait_time = resp.get("next_poll_s",30)
  print(f"Polling again in {wait_time}s")
  time.sleep(wait_time)
