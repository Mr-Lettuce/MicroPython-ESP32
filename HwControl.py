import machine
from machine import Pin, PWM
from time import sleep
import dht

#Sensors
dht = dht.DHT22(machine.Pin(12))                      #os.environ.get('DHT_PIN')          # BOOT os.environ['DHT_PIN'] = 12
#water_p= dht.DHT22(machine.Pin(XX))                  #os.environ.get('WATER_PROBE_PIN')  # BOOT os.environ['WATER_PROBE_PIN'] = xx
#sink_p = dht.DHT22(machine.Pin(XX))                  #os.environ.get('SINK_PROBE_PIN')   # BOOT os.environ['SINK_PROBE_PIN'] = xx

#Actuators
pelt = machine.PWM(Pin(13), freq=500, duty=612)       #os.environ.get('PELT_PIN')         # BOOT os.environ['PELT_PIN'] = 12
#heat = machine.PWM(Pin(XX), freq=500, duty=612)      #os.environ.get('HEAT_PIN')         # BOOT os.environ['HEAT_PIN'] = xx
#cooler = machine.PWM(Pin(XX), freq=500, duty=612)    #os.environ.get('COOLER_PIN')       # BOOT os.environ['COOLER_PIN'] = xx

#Indicators
#rPin = Pin(xx, Pin.OUT)                              #os.environ.get('R_LED_PIN')        # BOOT os.environ['R_LED_PIN'] = xx
#gPin = Pin(xx, Pin.OUT)                              #os.environ.get('G_LED_PIN')        # BOOT os.environ['G_LED_PIN'] = xx
#bPin = Pin(xx, Pin.OUT)                              #os.environ.get('B_LED_PIN')        # BOOT os.environ['B_LED_PIN'] = xx


def sense(delay):
  while True:
    dht.measure()
    print('Temperature: {d.temperature}, Humidity: {d.humidity}')
    sleep(delay)
    
def peltier_set(float:percentage):
    pelt.duty_u16(round((percentage*65535)/100))       # set duty to desired percentage
    
def reach_temp(float:temp):
  '''
  activate the heater/peltier to reach the temp in a adaptative way
  measure the % and define pwm duty acoordingly to the diff
  d.temperature             temp needed           %           % to peltier        % to heater
  5                         25                    20          -                   80
  15                        25                    60          -                   40
  25                        25                    100         -                   -
  35                        25                    140         40                  -
  45                        25                    180         80                  -
  
  It will never use the heater neither peltier al full power to prevent unmanageable situations, so the percentage will be used in a defined range, easy to adjust above
  '''
  heater_min_percentage = 0
  heater_max_percentage = 60
  peltier_min_percentage = 40
  peltier_max_percentage = 90
  dht.measure()
  #adj_peltier_percentage = float((((dht.temperature * 100) / temp) * 100) / (peltier_max_percentage + 100 - peltier_min_percentage)) # no va
  
  delta = (temp - dht.temperature)
  delta   virtual     real
  0       0%
  1       40%         1%
  5.5     65%         50% 
  10      90%         100%
  
  if temp > d.temperature:
    print('cool_that_shit')
    peltier_set(
    
  if temp < d.temperature:
    print('heat_that_shit')
    
def adapt_cooler():
  ''' 
  for internal control of the cooler to be as quiet as possible
  measure the % close to temp max set for the peltier sink
  '''
  
#def adapt_light():
  '''
  check the time cicle set and adjust the PWM output to be adaptative in the closeness to the starting/finishing time
  '''
#def rgb_indicator(state):
  '''
  receive the desired state of the rgb and adjust the color for coolness project
  check color generation with PWM usage or use signal, not PIN:  
  
  rPin = Pin(xx, Pin.OUT)             #define output pin above
  
  rlight = Signal(rPin, invert=False) #set signal pin
  rlight.value(1)                     #activate signal pin method 1
  rlight.on(1)                        #activate signal pin method 2
  '''
  
    
if __name__='__main__':
  sense()
