# ----------------------------------------------------------------------------
# CircuitPython Library for the Tesserae REST-API.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-tesserae
# ----------------------------------------------------------------------------

""" class Tesserae_API - public visible interface class """

import io
import json
import time

class Tesserae_ID:
  """ ID structure for Tesserae Clients """

  KIND = "circuitpython_generic"
  FW_VERSION = "0.1.0"

  # --- constructor   --------------------------------------------------------

  def __init__(self,name, device_id, width, height, format, gamut, mac):
    """ constructor """

    self.id = {
      "device_id": device_id,
      "kind": Tesserae_ID.KIND,
      "panel_w": width,
      "panel_h": height,
      "format": format,
      "gamut": gamut,
      "name": name,
      "fw_version": Tesserae_ID.FW_VERSION,
      "mac": mac,
      }

# --- API wrapper   ----------------------------------------------------------

class Tesserae_API:
  """ interface class for the Tesserae REST-API """

  TIMEOUT = 2
  API_ROOT = "api/v1/device"
  CHUNK_SIZE = 4096

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
    self._etag  = None

  # --- print debug message   ------------------------------------------------

  def debug(self,msg):
    """ print debug message """
    if self._debug:
      if isinstance(msg,dict):
        print("Tesserae: {")
        for key, value in msg.items():
          print(f"Tesserae:   {key}: {value}")
        print("Tesserae: }")
      else:
        print(f"Tesserae: {msg}")

  # --- build header   -------------------------------------------------------

  def _headers(self, extra_headers={}, with_auth=True):
    """ build request header """
    headers = {
      "Accept": "application/json",
      "Content-Type":"application/json",
      "Host": self._api_url.split("//", 1)[1].split("/", 1)[0], # workaround
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
    self.debug(f"posting to {endpoint}")
    self.debug(content)
    try:
      response = self._req.post(
        endpoint,
        headers=self._headers(extra_headers,with_auth),
        timeout=Tesserae_API.TIMEOUT,
        json=content)
      code = response.status_code
      self.debug(f"api-response: {code=}")
      self.debug("headers:")
      self.debug(response.headers)
      resp = response.content
      if len(resp):
        if response.headers.get("content-type") == "application/json":
          resp = json.loads(resp)
          self.debug(resp)
      response.close()
      return code, resp
    except Exception as ex:
      self.debug(f"failed to post data to {endpoint} with exception: {ex}")
      raise

  # --- get data   ----------------------------------------------------------

  def _get(self, api_or_url, extra_headers={}, with_auth=True):
    """ query data from Tesserae server.
    If the argument is an url, the caller has to process the
    response (and close it). Otherwise, the response is processed here.
    """

    if api_or_url[:4] == "http":
      endpoint = api_or_url
      is_api = False
    else:
      endpoint = f"{self._api_url}/{api_or_url}"
      is_api = True
    self.debug(f"requesting from {endpoint}")
    try:
      response = self._req.get(
        endpoint,
        headers=self._headers(extra_headers,with_auth),
        timeout=Tesserae_API.TIMEOUT)
      code = response.status_code
      headers = response.headers
      self.debug(f"api-response: {code=}")
      self.debug("headers:")
      self.debug(headers)
      if is_api:
        resp = response.content
        if len(resp):
          if response.headers.get("content-type") == "application/json":
            resp = json.loads(resp)
            self.debug(resp)
        response.close()
        return code, headers, resp
      else:
        return code, headers, response
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
    if self._etag:
      extra_headers = {"If-None-Match": self._etag}
    else:
      extra_headers = {}
    code, headers, resp = self._get(f"{self._id['device_id']}/frame",
                                    extra_headers)
    self._etag = headers.get("etag", None)
    self._url  = headers.get("content-location", None)
    if code == 304:
      # 304 does not return a response, so emulate it for the client
      resp = {"url": self._url}
    return code, resp

  # --- post status   --------------------------------------------------------

  def status(self, info={}):
    """ post status information """
    return self._post(f"{self._id['device_id']}/status", info)

  # --- post log   -----------------------------------------------------------

  def log(self, level, msg):
    """ post status information """
    return self._post(f"{self._id['device_id']}/log",
                      {"level": level, "msg": msg})

  # --- content of url returned by /frame   ----------------------------------

  def url_content(self):
    """ content (binary) of url returned by /frame """

    if not self._url:
      raise RuntimeError("no cached url")
    code, headers, response = self._get(self._url,{},False)
    if code != 200:
      raise RuntimeError(f"could not fetch data. HTTP-code: {code}")
    content_length = int(headers.get("content-length"))
    self.debug(f"url_content(): content-length: {content_length}")
    try:
      buffer = io.BytesIO(content_length)
    except:
      # CPython
      buffer = io.BytesIO(bytearray(content_length))
    offset = 0
    for chunk in response.iter_content(Tesserae_API.CHUNK_SIZE):
      l = len(chunk)
      buffer.write(chunk)
      offset += l
    if offset != content_length:
      raise RuntimeError(
        f"content length {offset} does not match 'Content-Lengh' header {content_length}")
    buffer.seek(0)
    response.close()
    return buffer
