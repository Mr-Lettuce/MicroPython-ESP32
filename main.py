import os
import gc
import AioFunctions
from WifiConnect import ConnectWifi
from MiscFunctions import init_routine
from MiscFunctions import Routine
import MiscFunctions


def main():
    ConnectWifi()
    gc.collect()
    routine0 = Routine()                # TODO: Make persistant trough saving setting into a file
    #mqtt_connect()
    #subscribe_to_feeds()
   
if __name__ == "__main__":
    init_routine()
    main()
