# Latest commit 8d3aaaf

'''
This script manages data of routines and hardware outputs of the ESP32.
Here we have the process of data stored in the database, synced in local variables to get the parameters needed for operation.
All routines are stored in DB and then are selected as current 'schedule' based on dates defined in each one.
'''
import os
import machine
import network
import time
import dht
import math
import gc
import _thread
from machine import RTC
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


schedule = Routine()                                  # Initialization for routine 0 
rtc = RTC()


def control_monitoring():
  '''
   This is the core function of the incubator, in charge of sensing real world, adjust water/sink temperature (maybe humidity too), lights,
  status RGB LED
  Also control the temperature needs comparing to the routine.
  '''
  # General variables initialization
  start = time.ticks_ms()
  global schedule
  vent_on = False
    
  # Variables for thermocouple sensing
  global temp_w                                       # Water temperature immediate value
  global temp_s                                       # Sink temperature immediate value
  temp_w = 0.0                                        #
  temp_s = 0.0                                        #
  global val_w                                        # Value for smooth ADC sensing (water)
  global val_s                                        # Value for smooth ADC sensing (sink)
  val_w = 0                                           #
  val_s = 0                                           #
  rs = 68000                                          # Resistor in the circuit board, same for water and sink probe
  vcc = 3.3                                           # Operating voltage
  loopcount1 = 0                                      # Count for ADC sensing
  loopcount2 = 0                                      # Count for cooler response
  loopcount3 = 0                                      # Count for reports to MQTT and adjust for new settings
  loopcount4 = 0                                      # Count for ventilation and general report

  while True:
    #dht.measure()                                    # sense DHT
    delta = time.ticks_diff(time.ticks_ms(), start)
    loopcount2 += 1
    loopcount3 += 1
    loopcount4 += 1
    
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


    if loopcount2 >= 30000:
        if 30 < temp_s <= 55:
            cooler_set( 60 +((temp_s - 30) * 1.66 ))
        elif temp_s > 55:
            cooler_set(100)
        else:
            cooler.duty(0)
        #ventilation_set(schedule.ventilation)                # __TODO__ FIX_NOT_WORKING: MemoryError: memory allocation failed, allocating 327676 bytes
      
        if network.WLAN(network.STA_IF).isconnected() != True:
            try:
                ConnectWifi()
            except Exception as e:
                print('Wifi not connected, trying to reconect in next loop.{}{}'.format(type(e).__name__, e))
                print(rtc.datetime())
                network.WLAN(network.STA_IF).active(False)
        loopcount2 = 0

    
    if loopcount3 >= 5000:
        #sel_r = read_db('sel_r')                              # OLD 
        #sync_db('r0')                                         # OLD
        sync_db(read_db('sel_r'))                              # Apply the selected routine, saved in db, to actual schedule params
        
        reach_temp(schedule.temperature)
        send_mqtt('reports.temperature', temp_w)#d.temperature )
        send_mqtt('reports.humidity', temp_s)#d.humidity )
        loopcount3 = 0

        summary_msg(f'  Selected routine = {read_db('sel_r')} \n  Target temperature = {schedule.temperature} \n  Ventilation intensity = {schedule.ventilation} \n  Light start/end time = {schedule.start_light} / {schedule.end_light}')


    if loopcount4 >= 900000:
        if vent_on == True:
            ventilation_set(0)
        else:
            ventilation_set(schedule.ventilation)
        #summary_msg(f'Selected routine = {sel_r} \n Target temperature = {schedule.temperature} \n Ventilation intensity = {schedule.ventilation} \n Light start/end time = {schedule.start_light} / {schedule.end_light}')
        loopcount4 = 0
        
        
    gc.collect()


def peltier_set(percentage: float):
    pelt.duty_u16(round((percentage*65535)/100))       # Set duty to desired percentage
    summary_msg(f'__DEBUG_PELTIER_SET__ {percentage}')
    
def heater_set(percentage: float):
    heat.duty_u16(round((percentage*65535)/100))       # Set duty to desired percentage
    summary_msg(f'__DEBUG_HEATER_SET__ {percentage}')  
    
def cooler_set(percentage: float):
    cooler.duty_u16(round((percentage*65535)/100))     # Set duty to desired percentage
    
def ventilation_set(percentage: float):
    ventilation.duty_u16(round((percentage*65535)/100))     # Set duty to desired percentage
    
    
def reach_temp(temp: float):
  '''
  activate the heater/peltier to reach the temp in a adaptative way
  measure the % and define pwm duty acoording to the diff
  
  It will never use the heater neither peltier al full power to prevent unmanageable situations, so the percentage will be used in a defined range, easy to adjust above
  '''
  global temp_w  
  heater_min_percentage = 0                                                       # Adjust hardware parameters
  heater_max_percentage = 50
  peltier_min_percentage = 30
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


#def rgb_indicator(state):
  '''
  receive the desired state of the rgb and adjust the color for coolness project
  check color generation with PWM usage or use signal, not PIN:  

  rPin = Pin(xx, Pin.OUT)             #define output pin above

  rlight = Signal(rPin, invert=False) #set signal pin
  rlight.value(1)                     #activate signal pin method 1
  rlight.on(1)                        #activate signal pin method 2
  
  GOOD                                # Green
  GOOD NOT CONNECTED                  # Green flashing
  GOOD, NO MQTT                       # Green and red flashing
  ADJUSTING                           # Blue
  ALERT/ERROR                         # Red
  '''


def sync_db(r_num: str):                              # Accepts argument as "r0", "r1", etc
    global schedule
    params = ( 'temperature', 'humidity', 'ventilation', 'start_light', 'end_light', 'start_date', 'end_date' )
    for i in params:
        exec( f'schedule.{i} = read_db("{r_num}_{i}")')


if __name__=='__main__':
    print('done HwControl')
