# ----------------------------------------------------------------------------
# settings_template.py: secrets and app_config - copy to settings.py and
#                       adapt.
#
# Author: Bernhard Bablok
# License: MIT
#
# Website: https://github.com/bablokb/circuitpython-tesserae
# ----------------------------------------------------------------------------

class Settings:
  pass

# network configuration   ----------------------------------------------------

secrets = Settings()
secrets.ssid      = 'my_ssid'
secrets.password  = 'my_password'

# app configuration   --------------------------------------------------------

# generic
app_config = Settings()
app_config.debug = True

# application specific
app_config.url = "http://tesserae-dev:8765"
app_config.mac   = "DE:AD:BE:EF"
app_config.token = None
#app_config.pairing_code = 123456
