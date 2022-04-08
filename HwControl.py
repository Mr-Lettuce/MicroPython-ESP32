#Latest commit fed52db

import os
import machine
import network
import time
import dht
import math
import gc
import _thread
from MiscFunctions import save_to_db
from MiscFunctions import read_db
from machine import Pin, PWM, ADC
from WifiConnect import ConnectWifi
from AioFunctions import send_mqtt
from AioFunctions import summary_msg
from MiscFunctions import Routine



DHT_PIN         =   os.environ.get('DHT_PIN')
WATER_PROBE_PIN =   os.environ.get('WATER_PROBE_PIN')
SINK_PROBE_PIN  =   os.environ.get('SINK_PROBE_PIN')
PELT_PIN        =   os.environ.get('PELT_PIN')
HEAT_PIN        =   os.environ.get('HEAT_PIN')
COOLER_PIN      =   os.environ.get('COOLER_PIN')
VENTILATION_PIN =   os.environ.get('VENTILATION_PIN')
R_LED_PIN       =   os.environ.get('R_LED_PIN')
G_LED_PIN       =   os.environ.get('G_LED_PIN')
B_LED_PIN       =   os.environ.get('B_LED_PIN')


#Sensors

#dht = dht.DHT22(machine.Pin(DHT_PIN))
water_p= ADC(Pin(WATER_PROBE_PIN))
sink_p = ADC(Pin(SINK_PROBE_PIN))

#Actuators
pelt        = machine.PWM(Pin(PELT_PIN), freq=500, duty=0)
heat        = machine.PWM(Pin(HEAT_PIN), freq=10, duty=0)
cooler      = machine.PWM(Pin(COOLER_PIN), freq=4800, duty=0)
ventilation = machine.PWM(Pin(VENTILATION_PIN), freq=500, duty=0)

#Indicators
#rPin = Pin(R_LED_PIN, Pin.OUT)
#gPin = Pin(G_LED_PIN, Pin.OUT)
#bPin = Pin(B_LED_PIN, Pin.OUT)


routine0 = Routine()                        # Initialization for routine 0 



def control_monitoring():
  '''
  This function sense the temperature and humidity of all sensors and control the sink temperature trough PWM and a cooler.
  Also control the temperature needs comparing to the routine.
  
  Its designed to work in a thread
  '''
  start = time.ticks_ms()
  
  
  global temp_w
  global temp_s
  temp_w = 0.0
  temp_s = 0.0
  global val_w
  global val_s
  val_w = 0
  val_s = 0
    
  rs = 68000                                          # Resistor in the circuit board, same for water and sink probe
  vcc = 3.3                                           # Operating voltage
  loopcount1 = 0                                      # Count for ADC sensing
  loopcount2 = 0                                      # Count for cooler response
  loopcount3 = 0                                      # Count for reports to MQTT and adjust for new settings
  while True:
    delta = time.ticks_diff(time.ticks_ms(), start)
    loopcount2 += 1
    loopcount3 += 1
    #dht.measure()                                    # sense DHT
    
    if delta % 2 == 0:                                # Sense the probes every 2 miliseconds
        val_w += water_p.read_uv()
        val_s += sink_p.read_uv()
        loopcount1 += 1
    if loopcount1 >= 1000:                            # Average value from 1000 samples
        val_w = val_w / loopcount1;
        val_s = val_s / loopcount1;
      
        v_ntc_w = val_w * 0.000001                    # temp_ntc():
        v_ntc_s = val_s * 0.000001
        r_ntc_w = (rs * v_ntc_w) / (vcc - v_ntc_w)
        r_ntc_s = (rs * v_ntc_s) / (vcc - v_ntc_s)
        r_ntc_w = math.log(r_ntc_w)
        r_ntc_s = math.log(r_ntc_s)
        temp_w = 1 / (0.001129148 + (0.000234125 + (0.0000000876741 * r_ntc_w * r_ntc_w ))* r_ntc_w )
        temp_w = temp_w - 273.15
        temp_s = 1 / (0.001129148 + (0.000234125 + (0.0000000876741 * r_ntc_s * r_ntc_s ))* r_ntc_s )
        temp_s = temp_s - 273.15
      
        loopcount1 = 0
        delta = 0    
    
    if loopcount2 >= 15000:
      if 30 < temp_s <= 55:
        cooler_set( 60 +((temp_s - 30) * 1.66 ))
      elif temp_s > 55:
        cooler_set(100)
      else:
        cooler.duty(0)
      loopcount2 = 0
    
    if loopcount3 >= 5000:
        send_mqtt('reports.temperature', temp_w)#d.temperature )
        send_mqtt('reports.humidity', temp_s)#d.humidity )
        #print(f'DHT = Temperature: {d.temperature}, Humidity: {d.humidity}')
        #summary_msg(f'Water temperature:        {temp_w}')
        #summary_msg(f'Sink temperature:         {temp_s}')
        loopcount3 = 0
        sync_db()
        reach_temp(routine0.temperature)        
        #print(f'routine0.temperature = {routine0.temperature}')
        summary_msg(f'routine0.temperature = {routine0.temperature}')
        
        if network.WLAN(network.STA_IF).isconnected() != True:
                ConnectWifi()
            
    
    gc.collect()
    
    
def peltier_set(percentage: float):
    summary_msg(f'__DEBUG_PELTIER_SET__ {percentage}')
    pelt.duty_u16(round((percentage*65535)/100))       # Set duty to desired percentage
    
def heater_set(percentage: float):
    summary_msg(f'__DEBUG_HEATER_SET__ {percentage}')  
    heat.duty_u16(round((percentage*65535)/100))       # Set duty to desired percentage
    
def cooler_set(percentage: float):
    #summary_msg(f'__DEBUG_COOLER_SET__ {percentage}')    
    cooler.duty_u16(round((percentage*65535)/100))     # Set duty to desired percentage
    #cooler.duty_u16(65535)
    
def ventilation_set():   #(percentage: float):
    summary_msg('__DEBUG__VENTILATION__ON__')
    cooler.duty_u16(round((50*65535)/100))             # Set duty to desired percentage
    
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
  global temp_w  
  heater_min_percentage = 0                                       # Adjust hardware parameters
  heater_max_percentage = 50
  peltier_min_percentage = 40
  peltier_max_percentage = 80

  peltier_levels = float((peltier_max_percentage - peltier_min_percentage) / 5)
  heater_levels = float((heater_max_percentage - heater_min_percentage) / 8)
  
  #dht.measure()
  delta_temp = abs(float(temp - temp_w))#dht.temperature))
  
  if temp < temp_w:        #d.temperature:                                        # Cooling call
      if 0.2 < delta_temp <= 5:
          peltier_set(peltier_min_percentage + (delta_temp * peltier_levels))
          heat.duty(0)
      elif delta_temp > 5:
          peltier_set(peltier_max_percentage)
          heat.duty(0)
      else:
          pelt.duty(0)
          heat.duty(0)

  if temp > temp_w:       #d.temperature:                                          # Heating call
      if 0.1 < delta_temp <= 5:
          heater_set(heater_min_percentage + (delta_temp * heater_levels))
          pelt.duty(0)
      elif delta_temp > 5:
          heater_set(heater_max_percentage)
          pelt.duty(0)
      else:
          heat.duty(0)
          pelt.duty(0)


#def adapt_light():
  '''
  check the time cicle set and adjust the PWM output to be adaptative in the closeness to the starting/finishing time
  '''

#def ventilation_routine():
  '''
  control the coller trough PWM
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


def sync_db(r_num: int): 
    if r_num # use exec('expr as str')
    routine0.temperature = read_db('r0.temperature')

if __name__=='__main__':
    #control_monitoring(22)
    print('done')
