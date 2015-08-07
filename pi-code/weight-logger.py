#!/usr/bin/python

#based on https://gist.github.com/jacksenechal/5862530#file-readscale-py

import os, time
import usb.core
import usb.util
from sys import exit
import math
import time

from coffeeMachine import CoffeeMachine

# DYMO M25
VENDOR_ID = 0x0922
PRODUCT_ID = 0x8004

# USPS 75lb scale (doesn't work yet...)
#VENDOR_ID = 0x04d9
#PRODUCT_ID = 0x8010

# find the USB device
dev = usb.core.find(idVendor=VENDOR_ID,
                       idProduct=PRODUCT_ID)

doReconnect = False

coffeeMech = CoffeeMachine()

def main():
    try:
        # was it found?
        if dev is None:
            print "device not found"
            globals()['doReconnect'] = True
        else:
            devmanufacturer = usb.util.get_string(dev, 256, 1)
            devname = usb.util.get_string(dev, 256, 2)
            print "device found: " + devmanufacturer + " " + devname

            interface = 0
            if dev.is_kernel_driver_active(interface) is True:
                #print "but we need to detach kernel driver"
                dev.detach_kernel_driver(interface)

                # use the first/default configuration
                dev.set_configuration()
                #print "claiming device"
                usb.util.claim_interface(dev, interface)

                # XXX would be good to release it when we're done:
                #
                # print "release claimed interface"
                # usb.util.release_interface(dev, interface)
                # print "now attaching the kernel driver again"
                # dev.attach_kernel_driver(interface)
                # print "all done"
        listen()

    except KeyboardInterrupt as e: 
        print "\nquitting"
        exit();

def reconnect():
    interface = 0
    globals()['doReconnect'] = False
    print "trying to reconnect"
    try:
        globals()['dev'] = usb.core.find(idVendor=VENDOR_ID,
                           idProduct=PRODUCT_ID)
        
        if dev != None and dev.is_kernel_driver_active(interface) is True:
            #print "but we need to detach kernel driver"
            dev.detach_kernel_driver(interface)

            # use the first/default configuration
            dev.set_configuration()
            #print "claiming device"
            usb.util.claim_interface(dev, interface)
        else:
            globals()['doReconnect'] = True    
    except usb.core.USBError as e:
        print "USBError: " + str(e.args)
        globals()['doReconnect'] = True

def grab():
    try:
        # first endpoint
        if dev == None:
            return None
        endpoint = dev[0][(0,0)][0]

        # read a data packet
        attempts = 10
        data = None
        while data is None and attempts > 0:
            try:
                data = dev.read(endpoint.bEndpointAddress,
                                   endpoint.wMaxPacketSize)
            except usb.core.USBError as e:
                data = None
                attempts -= 1
                if e.args == ('Operation timed out',):
                    print "timed out... trying again"
                    continue

        return data
    except usb.core.USBError as e:
        print "USBError: " + str(e.args)
        globals()['doReconnect'] = True
        return None
    except IndexError as e:
        print "IndexError: " + str(e.args)


def listen():
    DATA_MODE_GRAMS = 2
    DATA_MODE_OUNCES = 11

    last_raw_weight = 0
    last_raw_weight_stable = 4

    print "listening for weight..."

    while True:
        time.sleep(.1)

        weight = 0

        if globals()['doReconnect'] == True:
            reconnect()

        data = grab()
        if data != None:
            raw_weight = data[4] + data[5] * 256

            grams = 0
            if data[2] == DATA_MODE_OUNCES:
                ounces = raw_weight * 0.1
                grams = ounces / 0.035274
        	
            elif data[2] == DATA_MODE_GRAMS:
                grams = raw_weight
            grams = int(math.ceil(grams))

            # print "weight: %s" % grams
            coffeeMech.updateMass(grams)
            # with open("w.log", "a") as myfile:
            #     myfile.write("%d:%d\n" % (long(math.floor(time.time()*1000)),grams))


def probe():
    for cfg in dev:
        print "cfg: " + str(cfg.bConfigurationValue)
        print "descriptor: " + str(usb.util.find_descriptor(cfg, find_all=True, bInterfaceNumber=1))
        for intf in cfg:
            print "interfacenumber, alternatesetting: " + str(intf.bInterfaceNumber) + ',' + str(intf.bAlternateSetting)
            for ep in intf:
                print "endpointaddress: " + str(ep.bEndpointAddress)


#probe()
main()
