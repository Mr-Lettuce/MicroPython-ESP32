# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import os
import sys

sys.path.reverse()

# WIFI conection parameters
os.environ['SSID']         ='wifi_id'
os.environ['SSIDPW']       ='wifi_password'

# Adafruit IO parameters, these are the configuration for 2 groups and 4 feeds:
# In the "esp-actions" group the commands will be processed with feed "cmd", and the "summary" feed will be for reporting stuffs from system-to-human
# In the "reports" group all the measurement data of this entire control system will be stored.
# os.environ['AIO_SUB_FEED'] = [ feeds from where you will receive data ]
# os.environ['AIO_REP_FEED'] = [ feeds where the data will be sent ]

# __MQTT_SERVER_
os.environ['AIO_USERNAME'] = 'adafruit_user'
os.environ['AIO_KEY']      = 'adafruit_key'
os.environ['AIO_CID']      = bytes('ESP32_'+ machine.unique_id(), 'utf-8')
os.environ['AIO_SUB_FEED'] = [ 'esp-actions.cmd' ]
os.environ['AIO_REP_FEED'] = [ 'reports.humidity', 'reports.temperature', 'esp-actions.summary']

# __HARDWARE_ASSIGNMENT__
os.environ['DHT_PIN']           = 11 #39 x
os.environ['WATER_PROBE_PIN']   = 36 #34 -*
os.environ['SINK_PROBE_PIN']    = 39 #35 -*

os.environ['LIGHT_PIN']         = 32 #   -
os.environ['COOLER_PIN']        = 33 #35 #25 - Pins 34-39 are input only, and also do not have internal pull-up resistors
os.environ['VENTILATION_PIN']   = 25 #32 #26 -
os.environ['PELT_PIN']          = 26 #33 #32 -
os.environ['HEAT_PIN']          = 27 #25 #33 -
os.environ['HUMID_PIN']         = 14 #26 #   x
os.environ['R_LED_PIN']         = 6  #27 Pins 6, 7, 8, 11, 16, and 17 are used for connecting the embedded flash, and are not recommended for other uses
os.environ['G_LED_PIN']         = 7  #14 
os.environ['B_LED_PIN']         = 8  #12 

'''
Pines PWM

13
14
15
16
17
18
19

21
22
23

25
26
27

32
33
'''
