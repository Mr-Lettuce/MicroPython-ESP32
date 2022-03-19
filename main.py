from machine import Pin
from time import sleep
import os
import gc
import WifiConnect


def init_routine():
    ''' __INIT_ROUTINE__
        Just a phisical indication of the main script running with onboard Led
    '''
    led = Pin(2, Pin.OUT)
    led.value(1)
    sleep(0.5)
    led.value(0)
    
def main():
    ConnectWifi()
    while True:
        Pin(2, Pin.OUT).value(1)
        sleep(1)
        Pin(2, Pin.OUT).value(0)
        sleep(1)
        
if __name__ == "__main__":
    init_routine_routine()
    main()
