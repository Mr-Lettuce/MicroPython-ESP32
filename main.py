from machine import Pin
from time import sleep

# __INIT_ROUTINE__
led = Pin(2, Pin.OUT)
led.value(1)
sleep(0.5)
led.value(0)
    
# __WIFI_CONNECTION__    
''' 
  define a function to connect wifi
  call the func if the connection is unsuccesfull
  try 5 times and then continue
'''

import network
sta_if = network.WLAN(network.STA_IF); sta_if.active(True)
sta_if.connect(os.environ.get('SSID'), os.environ.get('SSIDPW'))
if sta_if.isconnected():
  for i in range (3):
    Pin(2, Pin.OUT).value(1)
    sleep(0.2)
    Pin(2, Pin.OUT).value(0)
    sleep(0.2)
    
while True:
    Pin(2, Pin.OUT).value(1)
    sleep(1)
    Pin(2, Pin.OUT).value(0)
    sleep(1)
