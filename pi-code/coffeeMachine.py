
#all wights in grams
#all wights can shift several grams so use ranges
MACHINE_BASE = 2365
CRAFT_BASE = 430

SCOOP_OF_GROUNDS = 5
USUAL_SCOOPS = 6

USUAL_DRY_GOUNDS = SCOOP_OF_GROUNDS * USUAL_SCOOPS

GROUNDS_PER_CUP = 2.5

MAX_WATER = 1745

#guesses at ranges
GROND_RETENTION_MIN = 110
GROND_RETENTION_MAX = 190

WATER_FULL_POT = 2080

CUP = 173

SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

if SLACK_WEBHOOK_URL == None:
  print "ERROR: SLACK_WEBHOOK_URL not set"
  exit()

import time
import math
from collections import deque
import json
import urllib2

def messageSlack(msg):
    data = {
            'text': msg
    }
    req = urllib2.Request(SLACK_WEBHOOK_URL)
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, json.dumps(data))

class CoffeeMachine:

    #states
    UNKNOWN = 0
    PREPARING = 1
    BREWING = 2
    HAS_COFFEE = 3
    EMPTY = 4


    def __init__(self):
        self.state = CoffeeMachine.UNKNOWN
        self.runningMassSamples = deque([0] * 6) #how many samples it takes to stablize
        self.runingCurrentMass = 0
        self.startLastMassChange = 0
        self.massChaning = False
        self.massStableCount = 0
        self.currentMass = 0;
        self.startOfBrewing = 0
        self.brewTime = 1000000
        self.fullMass = 0
        self.wetGroudnsMass = 0
        self.coffeMass = 0
        self.feedbackCount = 0

    
    def updateMass(self, mass):
        self.runningMassSamples.popleft()
        self.runningMassSamples.append(mass)
        new_mass = reduce(lambda x, y: x + y, self.runningMassSamples) / len(self.runningMassSamples)
        # print new_mass
        stable_epsilon = 10
        #have we diverged from the mean enought to say a change has happened 
        #TODO smooth this so one random reading doesn't through things
        if abs(self.runingCurrentMass - mass) > stable_epsilon:
            if not self.massChaning:
                self.startLastMassChange = time.time()
            self.massStableCount = 3
            self.massChaning = True

        if self.massStableCount > 0 and abs(self.runingCurrentMass - mass) < stable_epsilon:
            self.massStableCount -= 1
            if self.massStableCount == 0:
                self.massChaning = False
                time_d = time.time() - self.startLastMassChange
                print ("stablized at %d grams over %f sec " % (new_mass, time_d) )
                self.massChange( (new_mass, time_d) )


        self.runingCurrentMass  = new_mass
        self.update()

    def update(self):
        self.feedbackCount += 1
        self.feedbackCount = self.feedbackCount % 10

        if self.feedbackCount == 0:
                print "STATE %f" % self.state

        if self.state in [CoffeeMachine.PREPARING, CoffeeMachine.BREWING]:
            t = time.time()

            if self.feedbackCount == 0:
                print "%f seconds left in brew" % (t - (self.startOfBrewing + self.brewTime))

            if self.state != CoffeeMachine.BREWING and (t - (self.startOfBrewing + 40)) > 0:
                self.state = CoffeeMachine.BREWING
                print "Brewing"
                messageSlack("Coffee Brewing")
            elif (t - (self.startOfBrewing + self.brewTime)) > 0:
                self.state = CoffeeMachine.HAS_COFFEE
                self.fullMass = self.currentMass
                print "COFFEE!!!"
                messageSlack("Coffee is ready")
        return None

    def massChange(self, mass_change):
        mass_delta = mass_change[0] - self.currentMass

        #only react to +100g changes
        if abs(mass_delta) > 100:
            # increase in mass
            if mass_delta > 0:
                
                long_time_change = 8.0
                # if the change took a longish time it was probably adding watter and starting a brew
                # an increase after starting a brew or during a brew restarts the start of a brew
                if mass_change[1] > long_time_change or self.state in [CoffeeMachine.PREPARING, CoffeeMachine.BREWING]:
                    self.state = CoffeeMachine.PREPARING
                    self.startOfBrewing = time.time()
                    #brew time is 45 sec per cup + 30
                    self.brewTime = float(mass_change[0] - (MACHINE_BASE + CRAFT_BASE)) / float(CUP + GROUNDS_PER_CUP) * 45 + 30
                    self.wetGroudnsMass = -1
                    print "starting brew"
                # for quick mass changes when in the HAS_COFFEE state we update how much coffee is left
                elif mass_change[1] < long_time_change and self.state == CoffeeMachine.HAS_COFFEE:
                    if abs((mass_change[0] - (MACHINE_BASE + CRAFT_BASE) - self.wetGroudnsMass)) < 30:
                        self.state = CoffeeMachine.EMPTY
                        print "NO MORE COFFEE!"
                        messageSlack("Out of coffee people. Maybe make some more?")
                    else:
                        msg = "%d cups of coffee left" % int((mass_change[0] - (MACHINE_BASE + CRAFT_BASE) - self.wetGroudnsMass) / CUP)
                        print msg
                        messageSlack(msg)
                else:
                    print "unhandeled increase %f %f" % mass_change
            # decrease in mass
            else:
                if self.state == CoffeeMachine.HAS_COFFEE and self.wetGroudnsMass == -1:
                    self.wetGroudnsMass = mass_change[0] - MACHINE_BASE
                    print "first removal after brew. wet ground mass is %fg" % self.wetGroudnsMass

                if self.state == CoffeeMachine.BREWING and (time.time() - (self.startOfBrewing + self.brewTime)) < self.brewTime * 0.5:
                    print "OMG WHAT ARE YOU DOING COFFEE IS GOIND EVERYWHERE!!"
                    # I guess were done now
                    self.state = CoffeeMachine.HAS_COFFEE
                    messageSlack("Coffee is ready")

        self.currentMass = mass_change[0]

# if mass is above MACHINE_BASE + CRAFT_BASE + USUAL_DRY_GOUNDS + (CUP * 2) we have probabbly started brewing


# aprox 45 sec brew time per cup + cups grounds

# mass above constant 


# listen for change in mass 
#     is mass D +> 2 cups materials and Dt > instant threshold
#         start of brew after stablized
#     is mass D - before > .5 of brew 
#         WTFBBQ!
#     is mass D - after .5 of brew 
#         brew finsihed
#             sub machine base from total this is wet grounds mass
#     if mass D +> and Dt < instant threshold
#         coffee was porred 
#             if new weight == wet grounds and craft and base 
#                 is empty