import network
import os
import gc
from machine import Pin
from time import sleep


def ConnectWifi():
  ''' To set up the SSID and SSID Password 'os' module must be reinstalled to get the option " os.environ['SSID'] = 'YourSSID' "
  Those environment variables can be set in the ' boot.py ' file
  '''
  print('Running WifiConnect.py, updated with commit a9f7c16')
  led = Pin(2, Pin.OUT)
  sta_if = network.WLAN(network.STA_IF); sta_if.active(True)
  if not sta_if.isconnected():
    sta_if.connect(os.environ.get('SSID'), os.environ.get('SSIDPW'))
    print('Connecting to the wifi Network: ' + os.environ.get('SSID'))
    while not sta_if.isconnected():
      time.sleep(1)
    for i in range (3):
      Pin(2, Pin.OUT).value(1)
      sleep(0.2)
      Pin(2, Pin.OUT).value(0)
      sleep(0.2)
  gc.collect()
  print(sta_if.ifconfig())

      
if __name__ == "__main__":
    ConnectWifi()
