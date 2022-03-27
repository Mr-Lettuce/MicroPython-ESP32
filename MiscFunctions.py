import os
import gc
from time import sleep
from machine import Pin
import btree


def init_routine():
    ''' __INIT_ROUTINE__
        Just a phisical indication of the main script running with onboard Led
    '''
    led = Pin(2, Pin.OUT)
    led.value(1)
    sleep(0.5)
    led.value(0)
    gc.collect()

class Routine:
    def __init__(
        self,
        temperature      =   '24',
        humidity         =   '60',
        ventilation      =   '4:4',
        start_light      =   '08:00',
        end_light        =   '18:00',
        start_date       =   '24:03:2022',
        end_date         =   '24:03:2032',
    ):
        self.temperature =   temperature
        self.humidity    =   humidity
        self.ventilation =   ventilation
        self.start_light =   start_light
        self.end_light   =   end_light
        self.start_date  =   start_date
        self.end_date    =   end_date
        
    def change_value(self, key, value):
        setattr(self, key, value)
        
        
def save_to_db(key, value):
    try:
        f = open("routine_db", "r+b")
    except OSError:
        f = open("routine_db", "w+b")
    db = btree.open(f)
    db[key] = value
    db.flush()
    print(f'Saved in database params: {key} = {db[key]}')
    db.close()
    f.close()
    
def read_db(key):
    try:
        f = open("routine_db", "r+b")
    except OSError:
        f = open("routine_db", "w+b")
    db = btree.open(f)
    print(f'Value stored in routine database for {key} is {db[key]}')
    for k in db:
        print(k)
    db.close()
    f.close()
