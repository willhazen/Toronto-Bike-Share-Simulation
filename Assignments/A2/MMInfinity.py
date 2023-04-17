# -*- coding: utf-8 -*-
"""
Converted from VBASim by
Yujing Lin, Linda Pei & Barry L Nelson
Last update 8/15/2018
"""


import SimClasses
import SimFunctions
import SimRNG
import math
import pandas
import numpy as np
 
SimClasses.Clock = 0
MeanParkingTime = 2.0
QueueLength = SimClasses.CTStat()
N = 0
MaxQueue = 0
RepNum = 300

ZSimRNG = SimRNG.InitializeRNSeed()
Calendar = SimClasses.EventCalendar()

TheCTStats = []
TheDTStats = []
TheQueues = []
TheResources = []

TheCTStats.append(QueueLength)

AllQueueLength = []
AllMaxQueue = []
AllN = []

print("Average Number in Queue", "Maximum Number in Queue")
 
def NSPP(Stream):
    PossibleArrival = SimClasses.Clock + SimRNG.Expon(1.0/110, Stream)
    while SimRNG.Uniform(0, 1, Stream) >= (100 + 10 * math.sin(3.141593 * PossibleArrival / 12)) / 110.0:
        PossibleArrival = PossibleArrival + SimRNG.Expon(1.0/110, Stream)
    nspp = PossibleArrival - SimClasses.Clock
    return nspp

def Arrival():
    global MaxQueue
    global N
    interarrival = NSPP(1)
    SimFunctions.Schedule(Calendar,"Arrival", interarrival)
    N = N + 1
    QueueLength.Record(N)
    if N > MaxQueue:
        MaxQueue = N   
    SimFunctions.Schedule(Calendar,"Departure",SimRNG.Expon(MeanParkingTime, 2))

def Departure():
    global N
    N = N - 1
    QueueLength.Record(N)
    
for Reps in range(0,RepNum,1):
    N = 0
    MaxQueue = 0
    SimFunctions.SimFunctionsInit(Calendar,TheQueues,TheCTStats,TheDTStats,TheResources)
    interarrival = NSPP(1)
    SimFunctions.Schedule(Calendar,"Arrival",interarrival)
    SimFunctions.Schedule(Calendar,"EndSimulation", 24)
    
    NextEvent = Calendar.Remove()
    SimClasses.Clock = NextEvent.EventTime
    if NextEvent.EventType == "Arrival":
        Arrival()
    elif NextEvent.EventType == "Departure":
        Departure()
    
    while NextEvent.EventType != "EndSimulation":
        NextEvent = Calendar.Remove()
        SimClasses.Clock = NextEvent.EventTime
        if NextEvent.EventType == "Arrival":
            Arrival()
        elif NextEvent.EventType == "Departure":
            Departure()
    
    AllQueueLength.append(QueueLength.Mean())
    AllMaxQueue.append(MaxQueue)
    AllN.append(N) 
    
    print(Reps+1, QueueLength.Mean(), MaxQueue, N)

# estimating the 0.99th quantile
quantile_index = int(np.ceil(RepNum*0.99)-1)
print("Estimated required capacity is:",np.sort(AllMaxQueue)[quantile_index])
print("Estimated Expected Average # of cars:", np.mean(AllQueueLength))
print("Estimated Expected Max # of cars:", np.mean(AllMaxQueue))