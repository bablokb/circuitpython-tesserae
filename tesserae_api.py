# ----------------------------------------------------------------------------
# CircuitPython Library for the Tesserae REST-API.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-tesserae
# ----------------------------------------------------------------------------

""" class Tesserae_API - public visible interface class """

import json
import time

class Tesserae_ID:
  """ ID structure for Tesserae Clients """

  KIND = "circuitpython_generic"
  FW_VERSION = "0.1.0"

  # --- constructor   --------------------------------------------------------

  def __init__(self,device_id, width, height, mac):
    """ constructor """

    self.id = {
      "device_id": device_id,
      "kind": Tesserae_ID.KIND,
      "panel_w": width,
      "panel_h": height,
      "fw_version": Tesserae_ID.FW_VERSION,
      "mac": mac,
      }

# --- API wrapper   ----------------------------------------------------------

class Tesserae_API:
  """ interface class for the Tesserae REST-API """

  TIMEOUT = 2
  API_ROOT = "api/v1/device"

  # --- constructor   --------------------------------------------------------

  def __init__(self, id, url, req_factory, token=None, debug=False):
    """ constructor
    id: ID of this device
    url: ip or hostname of Tesserae server (including port)
    req_factory: object adafruit_requests.Session
    mac: MAC address
    token: auth-token
    """

    self._id = id
    self._api_url   = f"{url}/{Tesserae_API.API_ROOT}"
    self._req   = req_factory
    self._debug = debug

    self.token  = token

  # --- print debug message   ------------------------------------------------

  def debug(self,msg):
    """ print debug message """
    if self._debug:
      print(f"Tesserae: {msg}")

  # --- build header   -------------------------------------------------------

  def _headers(self, extra_headers={}, with_auth=True):
    """ build request header """
    headers = {
      "Accept": "application/json",
      "Content-Type":"application/json",
      }
    headers.update(extra_headers)
    if with_auth and self.token:
      headers["X-Tesserae-Token"] = self.token
    elif with_auth:
      raise RuntimeError("no Auth-Token")
    return headers

  # --- post data   ----------------------------------------------------------

  def _post(self, api, content, extra_headers={}, with_auth=True):
    """ post the given (json) content """

    endpoint = f"{self._api_url}/{api}"
    self.debug(f"posting to {endpoint}: {content}")
    try:
      response = self._req.post(
        endpoint,
        headers=self._headers(extra_headers,with_auth),
        timeout=Tesserae_API.TIMEOUT,
        json=content)
      code, resp = response.status_code, response.json()
      self.debug(f"api-response: {code}: {resp}")
      response.close()
      return code, resp
    except Exception as ex:
      self.debug(f"failed to post data to {endpoint} with exception: {ex}")
      raise

  # --- get data   ----------------------------------------------------------

  def _get(self, api, with_auth=True):
    """ query data from Tesserae server """

    endpoint = f"{self._api_url}/{api}"
    self.debug(f"requesting from {endpoint}")
    try:
      response = self._req.get(
        endpoint,
        headers=self._headers({},with_auth),
        timeout=Tesserae.TIMEOUT)
      code, resp = response.status_code, response.json()
      self.debug(f"api-response: {code}: {resp}")
      response.close()
      return code, resp
    except Exception as ex:
      self.debug(f"failed to query data from {endpoint} with exception: {ex}")
      raise

  # --- discover   ----------------------------------------------------------

  def discover(self):
    """ post identity for discovery
    id: dictionary with identity attributes (see docs)
    """
    code, resp = self._post("discover", self._id, {}, False)
    if code == 200 and "device_token" in resp:
      self.token = resp["device_token"]
    return code, resp

  # --- register   ----------------------------------------------------------

  def register(self, pairing_code):
    """ post identity for registration
    id: dictionary with identity attributes (see docs)
    """
    code, resp = self._post("register", self._id,
                            {"X-Pairing-Code": f"{pairing_code}"},
                            False)
    if code == 201 and "device_token" in resp:
      self.token = resp["device_token"]
    return code, resp

  # --- query frame information   --------------------------------------------

  def frame(self):
    """ query frame information """

    endpoint = f"self._id['device_id']/frame"
    return self._get(endpoint)

  # --- post status   --------------------------------------------------------

  def status(self, info={}):
    """ post status information """

    return self._post("status", info)
