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
  measure the % and define pwm duty acoording to the diff
  
  It will never use the heater neither peltier al full power to prevent unmanageable situations, so the percentage will be used in a defined range, easy to adjust above
  '''
  heater_min_percentage = 0
  heater_max_percentage = 50
  peltier_min_percentage = 40
  peltier_max_percentage = 80
  dht.measure()
  
  delta_temp = abs(float(temp - dht.temperature))
  peltier_levels = float((peltier_max_percentage - peltier_min_percentage) / 10)
  heater_levels = float((heater_max_percentage - heater_min_percentage) / 10)
  '''
  temp-set        dht             delta          p/h %
  
  25              14              11             50
  25              15              10             50
  25              16              9              45
  25              17              8              40
  25              18              7              35
  25              19              6              30
  25              20              5              25
  25              21              4              20
  25              22              3              15
  25              23              2              10
  25              24              1              5
  25              25              0              0
  25              26              1              44
  25              27              2              48
  25              28              3              52
  25              29              4              56
  25              30              5              60
  25              31              6              64
  25              32              7              68
  25              33              8              72
  25              34              9              76
  25              35              10             80
  25              40              15             80
  
  '''
  if temp > d.temperature:                                        # Cooling function
    print('cool_that_shit')
    if delta_temp <= 10:
      peltier_set(peltier_min_percentage + (delta_temp * peltier_levels))
      adapt_cooler(20 + (delta_temp * 8))     # Use PWM between 20 and 100 %
    else:
      peltier_set(peltier_max_percentage)
      adapt_cooler(100)
  if temp < d.temperature:                                        # Heating function
    print('heat_that_shit')
    if delta_temp <= 10:
      heater_set(heater_min_percentage + (delta_temp * heater_levels))
      adapt_cooler(20 + (delta_temp * 8))
    else:
      heater_set(heater_max_percentage)
      adapt_cooler(100)
      
# __DEBUG__
print(f'd.temperature = {d.temperature},
      delta_temp = {delta_temp},
      d.humidity = {d.humidity},
      peltier_set(peltier_min_percentage + (delta_temp * peltier_levels)) = {peltier_set(peltier_min_percentage + (delta_temp * peltier_levels))},
      heater_set(heater_min_percentage + (delta_temp * heater_levels)) = {heater_set(heater_min_percentage + (delta_temp * heater_levels))},
      adapt_cooler(20 + (delta_temp * 8)) = {adapt_cooler(20 + (delta_temp * 8))}')
      
      
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
