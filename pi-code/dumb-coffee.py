#!/usr/bin/python

#based on https://gist.github.com/jacksenechal/5862530#file-readscale-py

import os, time
import usb.core
import usb.util
from sys import exit
import time
import math
from collections import deque
import json
import urllib2
import datetime

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

#known masses in g
CUP = 173
CRAFT_BASE = 430

SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

if SLACK_WEBHOOK_URL == None:
  print "ERROR: SLACK_WEBHOOK_URL not set"
  exit()


def messageSlack(msg):
    data = {
            'text': msg
    }
    req = urllib2.Request(SLACK_WEBHOOK_URL)
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, json.dumps(data))

def doRecord(msg):
    lines = deque([])
    wlines = []
    with open("log/w.log", "r") as f:
        for line in f:
            lines.append(line)
    with open("log/w.log", "w") as f:
        wlines = list(lines)[-199:]
        wlines.append("%s,%s\n" % (datetime.datetime.today(), msg))
        for l in wlines:
            f.write(l)
        f.close()

class CoffeeMachine:

    def __init__(self):
        self.runningMassSamples = deque([0] * 6) #how many samples it takes to stablize
        self.runingCurrentMass = 0
        self.startLastMassChange = 0
        self.massChanging = False
        self.massStableCount = 0
        self.currentMass = 0;
        self.coffeMass = 0
        self.feedbackCount = 0
        self.lastMass = 0

    
    def updateMass(self, mass):
        self.runningMassSamples.popleft()
        self.runningMassSamples.append(mass)
        new_mass = reduce(lambda x, y: x + y, self.runningMassSamples) / len(self.runningMassSamples)
        # print new_mass
        stable_epsilon = 10
        #have we diverged from the mean enought to say a change has happened 
        #TODO smooth this so one random reading doesn't through things
        if abs(self.runingCurrentMass - mass) > stable_epsilon:
            if not self.massChanging:
                self.startLastMassChange = time.time()
            self.massStableCount = 3
            self.massChanging = True

        if self.massStableCount > 0 and abs(self.runingCurrentMass - mass) < stable_epsilon:
            self.massStableCount -= 1
            if self.massStableCount == 0:
                self.massChanging = False
                time_d = time.time() - self.startLastMassChange
                print ("%s || stablized at %d grams over %f sec " % (datetime.datetime.today(), new_mass, time_d) )
                self.massChange( (new_mass, time_d) )


        self.runingCurrentMass  = new_mass


    def massChange(self, mass_change):
        mass_delta = mass_change[0] - self.currentMass
        print "%s || new mass d %f, c %f" % (datetime.datetime.today(), mass_delta, self.currentMass)
        #only react to +50g changes
        if abs(mass_delta) > 50:
            # increase in mass
            if mass_delta > 0:
                print "%s || increase %f, %f, C %f " % (datetime.datetime.today(), mass_change[0] - CRAFT_BASE, abs(mass_change[0] - self.lastMass), self.lastMass)
                if mass_change[0] - CRAFT_BASE > 30 and abs(mass_change[0] - self.lastMass) > 30 :
                    cups = (mass_change[0] - CRAFT_BASE) / float(CUP)
                    msg = "%.2f cups of coffee available" % cups
                    messageSlack(msg)
                    doRecord("cups,%.4f" % cups)
                    print "%s || %s" % (datetime.datetime.today(),msg)
                elif abs(mass_change[0] - self.lastMass) > 30 :
                    msg = "No more coffee :("
                    messageSlack(msg)
                    doRecord("empty,")
                    print "%s || %s" % (datetime.datetime.today(),msg)

                self.lastMass = mass_change[0]
            # decrease in mass
            else:
                #message api that craft is off the scale
                if False: print "what?!"
        self.currentMass = mass_change[0]



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
