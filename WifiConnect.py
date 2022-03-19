import network
import time
from machine import Pin

def main():
  print('Running WifiConnect.py')
  
def WifiConnect():
  ''' To set up the SSID and SSID Password 'os' module must be reinstalled to get the option " os.environ['SSID'] = 'YourSSID' "
  Those environment variables can be set in the ' boot.py ' file
  '''
  
  led = Pin(2, Pin.OUT)
  sta_if = network.WLAN(network.STA_IF); sta_if.active(True)
  if not sta_if.isconnected():
    sta_if.connect(os.environ.get('SSID'), os.environ.get('SSIDPW'))
    print('Connecting to the wifi Network: ' + os.environ.get('SSID'))
    while not sta_if.isconnected():
      time.sleep(1)
    print(sta_if.ifconfig())
    for i in range (3):
      Pin(2, Pin.OUT).value(1)
      sleep(0.2)
      Pin(2, Pin.OUT).value(0)
      sleep(0.2)
      
if __name__ == "__main__":
    main()
