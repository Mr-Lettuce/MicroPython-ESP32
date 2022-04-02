import os
import gc
from AioFunctions import mqtt_connect_and_subscribe
from HwControl import control_monitoring
from WifiConnect import ConnectWifi
from MiscFunctions import init_routine
from MiscFunctions import Routine
import MiscFunctions
import _thread



def main():
    '''
    _TODO_
    monitoring of wifi network connection & to reconnect
    monitoring of MQTT connection & reconnect
    make routine persistant trough saving settings into a db
    '''
    ConnectWifi()
    routine0 = Routine()
    _thread.start_new_thread(mqtt_connect_and_subscribe, ())
    control_monitoring()
    
    
if __name__ == "__main__":
    init_routine()
    main()
