"""
Converted from VBASim by
Yujing Lin, Linda Pei & Barry L Nelson
Last update 8/15/2018
"""

import SimFunctions
import SimRNG 
import SimClasses
import numpy as np
import pandas


ZSimRNG = SimRNG.InitializeRNSeed()

Queue = SimClasses.FIFOQueue()
Wait = SimClasses.DTStat()
Server = SimClasses.Resource()
Calendar = SimClasses.EventCalendar()

TheCTStats = []
TheDTStats = []
TheQueues = []
TheResources = []

TheDTStats.append(Wait)
TheQueues.append(Queue)
TheResources.append(Server)

Server.SetUnits (1) 
MeanTBA = 1.0
MeanST = 0.8
Phases = 3
RunLength = 55000.0
WarmUp = 5000.0

AllWaitMean = []
AllQueueMean = []
AllQueueNum = []
AllServerMean = []
print ("Rep", "Average Wait", "Average Number in Queue", "Number Remaining in Queue", "Server Utilization")

def Arrival():
    SimFunctions.Schedule(Calendar,"Arrival",SimRNG.Expon(MeanTBA, 1))
    Customer = SimClasses.Entity()
    Queue.Add(Customer)
    
    if Server.Busy == 0:
        Server.Seize(1)
        SimFunctions.Schedule(Calendar,"EndOfService",SimRNG.Erlang(Phases,MeanST,2))

def EndOfService():
    DepartingCustomer = Queue.Remove()
    Wait.Record(SimClasses.Clock - DepartingCustomer.CreateTime)
    if Queue.NumQueue() > 0:
        SimFunctions.Schedule(Calendar,"EndOfService",SimRNG.Erlang(Phases,MeanST,2))
    else:
        Server.Free(1)

for reps in range(0,10,1):

    SimFunctions.SimFunctionsInit(Calendar,TheQueues,TheCTStats,TheDTStats,TheResources)
    SimFunctions.Schedule(Calendar,"Arrival",SimRNG.Expon(MeanTBA, 1))
    SimFunctions.Schedule(Calendar,"EndSimulation",RunLength)
    SimFunctions.Schedule(Calendar,"ClearIt",WarmUp)
    
    NextEvent = Calendar.Remove()
    SimClasses.Clock = NextEvent.EventTime
    if NextEvent.EventType == "Arrival":
        Arrival()
    elif NextEvent.EventType == "EndOfService":
        EndOfService() 
    elif NextEvent.EventType == "ClearIt":
        SimFunctions.ClearStats(TheCTStats,TheDTStats)
    
    while NextEvent.EventType != "EndSimulation":
        NextEvent = Calendar.Remove()
        SimClasses.Clock = NextEvent.EventTime
        if NextEvent.EventType == "Arrival":
            Arrival()
        elif NextEvent.EventType == "EndOfService":
            EndOfService()
        elif NextEvent.EventType == "ClearIt":
            SimFunctions.ClearStats(TheCTStats,TheDTStats)
    
    AllWaitMean.append(Wait.Mean())
    AllQueueMean.append(Queue.Mean())
    AllQueueNum.append(Queue.NumQueue())
    AllServerMean.append(Server.Mean())
    print (reps+1, Wait.Mean(), Queue.Mean(), Queue.NumQueue(), Server.Mean())

# output results

print("Estimated Expected Average wait:",np.mean(AllWaitMean))
print("Estimated Expected Average queue-length:", np.mean(AllQueueMean))
print("Estimated Expected Average utilization:",np.mean(AllServerMean))

# convert the output to a dataframe and write to a .csv file
output = {"AllWaitMean" : AllWaitMean, "AllQueueMean": AllQueueMean, "AllQueueNum" : AllQueueNum, "AllServerMean": AllServerMean}
output = pandas.DataFrame(output)
output.to_csv("MG1_output.csv", sep=",")


