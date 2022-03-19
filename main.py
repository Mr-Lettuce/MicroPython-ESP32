from machine import Pin
from time import sleep
import os
import gc
from WifiConnect import ConnectWifi


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
    
        
if __name__ == "__main__":
    init_routine()
    main()
