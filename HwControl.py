import os
import machine
from machine import Pin, PWM, ADC
from time import sleep
import dht
import math
import gc
import _thread

os.environ['DHT_PIN'] = 12
os.environ['WATER_PROBE_PIN'] = 13
os.environ['SINK_PROBE_PIN'] = 14
os.environ['PELT_PIN'] = 15
os.environ['HEAT_PIN'] = 16
os.environ['COOLER_PIN'] = 17
os.environ['R_LED_PIN'] = 18
os.environ['G_LED_PIN'] = 19
os.environ['B_LED_PIN'] = 20


DHT_PIN         =   os.environ.get('DHT_PIN')
WATER_PROBE_PIN =   os.environ.get('WATER_PROBE_PIN')
SINK_PROBE_PIN  =   os.environ.get('SINK_PROBE_PIN')
PELT_PIN        =   os.environ.get('PELT_PIN')
HEAT_PIN        =   os.environ.get('HEAT_PIN')
COOLER_PIN      =   os.environ.get('COOLER_PIN')
R_LED_PIN       =   os.environ.get('R_LED_PIN')
G_LED_PIN       =   os.environ.get('G_LED_PIN')
B_LED_PIN       =   os.environ.get('B_LED_PIN')


#Sensors

dht = dht.DHT22(machine.Pin(DHT_PIN))
water_p= ADC(Pin(WATER_PROBE_PIN))
sink_p = ADC(Pin(SINK_PROBE_PIN))

#Actuators
pelt = machine.PWM(Pin(PELT_PIN), freq=500, duty=612)
heat = machine.PWM(Pin(HEAT_PIN), freq=500, duty=612)
cooler = machine.PWM(Pin(COOLER_PIN), freq=500, duty=612)

#Indicators
#rPin = Pin(R_LED_PIN, Pin.OUT)
#gPin = Pin(G_LED_PIN, Pin.OUT)
#bPin = Pin(B_LED_PIN, Pin.OUT)


def threaded_monitoring():
  '''
  This function sense the temperature and humidity of all sensors and control the sink temperature trough PWM and a cooler.
  Also control the temperature needs comparing to the routine.
  
  Its designed to work in a thread
  '''
  start = time.ticks_ms()
  global temp_w
  global temp_s
  rs = 100000  #150000                            # Resistor in the circuit board, same for water and sink probe
  vcc = 3.3                                       # Operating voltage
  while True:
    delta = time.ticks_diff(time.ticks_ms(), start)
    dht.measure()                                     # sense DHT
    val_w = 0                                         # smoothadc():
    val_s = 0
    loopcount1 = 0
    loopcount2 = 0
    if delta - start // 2 == 0:                       # Sense the probes every 2 miliseconds
        val_w += water_p.read_uv()
        val_s += sink_p.read_uv()
        loopcount1+= 1
    if loopcount1 >= 1000:                            # Average value from 1000 samples
      val_w = val_w / loopcount;
      val_s = val_s / loopcount;
      
      v_ntc_w = val_w() * 0.000001                    # temp_ntc():
      v_ntc_s = val_s() * 0.000001
      r_ntc_w = (rs * v_ntc_w) / (vcc - v_ntc_w)
      r_ntc_s = (rs * v_ntc_s) / (vcc - v_ntc_s)
      r_ntc_w = math.log(r_ntc_w)
      r_ntc_s = math.log(r_ntc_s)
      temp_w = 1 / (0.001129148 + (0.000234125 + (0.0000000876741 * r_ntc_w * r_ntc_w ))* r_ntc_w )
      temp_w = temp_w - 273.15
      temp_s = 1 / (0.001129148 + (0.000234125 + (0.0000000876741 * r_ntc_s * r_ntc_s ))* r_ntc_s )
      temp_s = temp_s - 273.15
      
      loopcount1 = 0
    
      print(f'DHT = Temperature: {d.temperature}, Humidity: {d.humidity}')
      print(f'Water temperature: {temp_w}')
      print(f'Sink temperature: {temp_s}')
    
    if loopcount2 >= 3000:
      if 30 < temp_s <= 55:
        cooler_set( 40 +((temp_s - 30) * 2.5 ))
      elif temp_s > 55:
        cooler_set(100)
      else:
        cooler_set(0)
    gc.collect()
    
    
def peltier_set(percentage: float):
    pelt.duty_u16(round((percentage*65535)/100))       # Set duty to desired percentage
    
    
def cooler_set(percentage: float):
    cooler.duty_u16(round((percentage*65535)/100))     # Set duty to desired percentage
    
    
def reach_temp(temp: float):
  '''
  activate the heater/peltier to reach the temp in a adaptative way
  measure the % and define pwm duty acoording to the diff
  
  It will never use the heater neither peltier al full power to prevent unmanageable situations, so the percentage will be used in a defined range, easy to adjust above
  
  With:
    heater_min_percentage = 0
    heater_max_percentage = 50
    peltier_min_percentage = 40
    peltier_max_percentage = 80
  temp-set        dht             delta          p/h %
  
  24              19              5              80
  24              19.5            4.5            76
  24              20              4              72
  24              20.5            3.5            68
  24              21              3              64
  24              21.5            2.5            60
  24              22              2              56
  24              22.5            1.5            52
  24              23              1              48
  24              23.5            0.5            44
  24     ---      24              0              0
  24              24.5            0.5            2.5
  24              25              1              5
  24              25.5            1.5            7.8
  24              26              2              10
  24              26.5            2.5            12.5
  24              27              3              15
  24              27.5            3.5            17.5
  24              28              4              20
  24              28.5            4.5            22.5
  24              29              5              25
  '''
  
  heater_min_percentage = 0                                       # Adjust hardware parameters
  heater_max_percentage = 50
  peltier_min_percentage = 40
  peltier_max_percentage = 80

  peltier_levels = float((peltier_max_percentage - peltier_min_percentage) / 5)
  heater_levels = float((heater_max_percentage - heater_min_percentage) / 10)
  
  dht.measure()
  delta_temp = abs(float(temp - dht.temperature))
  
  if temp < d.temperature:                                        # Cooling call
      print('Cool_that_shit!')
      if 0.2 < delta_temp <= 5:
          print((peltier_min_percentage + (delta_temp * peltier_levels)))
          peltier_set((peltier_min_percentage + (delta_temp * peltier_levels)))
      elif delta_temp > 5:
          print((peltier_max_percentage))
          peltier_set((peltier_max_percentage))
      else:
          print(f'peltier_set(0)')
          peltier_set(0)

  if temp > d.temperature:                                          # Heating call
      print('Heat_that_shit!')
      if 0.2 < delta_temp <= 5:
          print((heater_min_percentage + (delta_temp * heater_levels)))
          heater_set((heater_min_percentage + (delta_temp * heater_levels)))
      elif delta_temp > 5:
          print(heater_max_percentage)
          heater_set(heater_max_percentage)
      else:
          print(f'heater_set(0)')
          heater-set(0)


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


if __name__=='__main__':
    _thread.start_new_thread(threaded_monitoring, ())
