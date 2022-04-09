#Latest commit 4aafa8b

from umqtt.robust import MQTTClient
from MiscFunctions import save_to_db
from MiscFunctions import read_db
from time import sleep
import os
import sys
import gc
import utime
import machine
import _thread


'''
Feeds to report:

Temperature         PX      incu_esp1.temperature
Humdity             PX      incu_esp1.humidity

Feeds to cmd:
Settings(Input)             esp-actions.cmd
Summary(Output)             esp-actions.summary

Pins to control:
Light               PX      esp-actions.summary
Peltier             PX      esp-actions.summary
Calefactor          PX      esp-actions.summary
Ventilation         PX      esp-actions.summary
Humidifier          PX      esp-actions.summary
'''


mqtt_client_id      = os.environ.get('AIO_CID')
ADAFRUIT_IO_URL     = 'io.adafruit.com' 
ADAFRUIT_USERNAME   = os.environ.get('AIO_USERNAME')
ADAFRUIT_IO_KEY     = os.environ.get('AIO_KEY')
SUBSCRIBE_FEEDS     = os.environ.get('AIO_SUB_FEED')
REPORT_FEEDS        = os.environ.get('AIO_REP_FEED')


client = MQTTClient(client_id = mqtt_client_id,
                    server    = ADAFRUIT_IO_URL, 
                    user      = ADAFRUIT_USERNAME, 
                    password  = ADAFRUIT_IO_KEY,
                    keepalive = False,
                    ssl       = False)

client.DEBUG = True                                                     # Print diagnostic messages when retries/reconnects happens


def mqtt_connect_and_subscribe():                                       # __WORKING__
    '''
    This loop is intended for being called in a separate thread in order to wait for incoming messages
    Included the connect, subscribe and check mqtt msg functions 
    '''
    try:                                                                # mqtt_connect() function
        client.connect()
        print('Connected succesfully to MQTT server')
        gc.collect()
    except Exception as e:
        print('Could not connect to MQTT server {}{}'.format(type(e).__name__, e))
        gc.collect()
        sys.exit()

    client.set_callback(callback)                                       # subscribe_to_feeds() function
    for i in range(len(SUBSCRIBE_FEEDS)):
        current_feed = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, SUBSCRIBE_FEEDS[i]), 'utf-8')
        client.subscribe(current_feed)                                  # __TODO_ADJUST__ self, topic, qos=0
        print(f'Subscribed to feed {current_feed}')
    gc.collect()
    start = time.ticks_ms()
    while True:
        delta = time.ticks_diff(time.ticks_ms(), start)
        try:                                                            # check_mqtt() function
            if delta >= 100:
                client.wait_msg()
                gc.collect()
        except OSError as error:
            print(error)
            print('MQTT Connection failed, trying to reconnect...')
            client.disconnect()
            gc.collect()
            mqtt_connect_and_subscribe()
            continue


def send_mqtt(topic, msg):                                              # to_feed = b'Daddy_mdr/feeds/esp-actions.summary' , msg = holaa
    '''
    Send msg to adafruit topic
    '''
    #to_feed = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, b'topic'), 'utf-8')
    to_feed = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, topic), 'utf-8')
    #print(f'__DEBUG__ to_feed = {to_feed} , msg = {msg} ')
    client.publish(to_feed, bytes(str(msg), 'utf-8'))                   # __TODO_ADJUST__ self, topic, msg, retain=False, qos=0


def callback(topic, msg):
    '''
    Get the topic and message, if it need to be analize in search for a setting pass it to the corresponding function as a string
    '''
    print('__DEBUG__ Received Data:  Topic = {}, Msg = {}'.format(topic, msg))
    
    received_topic = str(topic,'utf-8').split('/')[-1]                  # Isolate topic for remote cmd instructions
    if received_topic == 'esp-actions.cmd':                             # Take actions acording to topic(groups), esp-actions or reports
        remote_cmd(str(msg,'utf-8'))                                    # Convert msg to str and pass it to the cmd analize function
    if received_topic == 'reports':
        print('ESP reported: ' + str(msg,'utf-8'))
    #gc.collect()


def remote_cmd(received_cmd):
    '''
    Get the string message received and search for setting formatted as:

        set.humidity=xx                                                 # Set target humidity
        set.temperature=xx                                              # Set target temperature
        
        set.ventilation=xx:xx                                           # Set ventilation like: _times_per_day_ : _minutes_per_time_
        
        do.reset                                                        # Reset ESP32
        
        exec.something                                                  # Execute something directly
        
        TODO:
        set.date=DD:MM:YYYY                                             # Set Date to DS3231
        set.routine=x:                                                  # Set routine like: _routine_number_ and it will wait for following parameters:
            DD:MM:YYYY                                                  _starting_date_
            xx:xx                                                       _init_light_hour_
            xx:xx                                                       _end_light_hour_
            xx                                                          _temperature_
            xx                                                          _humidity_
#       set.time=xx:xx                                                  # Set actual time in HH:MM
#       set.init-light=xx:xx                                            # Set initial hour for light cicle in HH:MM
#       set.end-light=xx:xx                                             # Set ending hour for light cicle in HH:MM

        do.reportnow                                                    # Report general status inmediately
    '''
    if received_cmd.count('.') >= 1:
        category     = received_cmd.split('.')[0]
        cmd          = received_cmd.split('.')[1]
        if category == 'set':
            set_value(cmd)                                              # Call function for set new values
        if category == 'do':
            machine_cmd(cmd)                                            # Call funcion for execute cmd for ESP control
        if category == 'exec':
            exec(str(cmd))                                              # Pass the msg directly to exec function
        gc.collect()
    else:
        print('Not cmd format found in message')
        send_mqtt('esp-actions.summary', 'No "cmd" format found in message')



def machine_cmd(received_cmd):
    '''
    Analysis and execution of the cmds received to command the ESP32 as a system
    '''
    if received_cmd == 'reset':
        send_mqtt('esp-actions.summary', 'Received soft reset cmd, resetting ESP')
        machine.reset()


def set_value(attr_value):                                              # Analize input for settings adjustments
    if attr_value.count('=') >= 1:
        key          = attr_value.split('=')[0]
        value        = attr_value.split('=')[1]
        send_mqtt('esp-actions.summary', f'Set new parameter: {key} = {value}')
        #routine0.change_value(key, value)
        save_to_db(f'r0_{key}', str(value))
    else:
        print('No "cmd" format found in message')
        send_mqtt('esp-actions.summary', 'Not set format found in message')
    gc.collect()
    
    
def summary_msg(msg: str):
    send_mqtt('esp-actions.summary', msg)
    print(msg)


def threaded_mqtt():
    _thread.start_new_thread(mqtt_connect_and_subscribe, ())
    gc.collect()


if __name__=='__main__':
    #from MiscFunctions import Routine
    #routine0 = Routine()
    #threaded_mqtt()
    print('done_aioF')
