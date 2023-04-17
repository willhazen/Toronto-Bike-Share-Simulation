## Note: 
## Need to define a new attribute (ClassNum) in the SimClasses file for the Entity object 


import SimFunctions
import SimRNG 
import SimClasses
import numpy as np

ZSimRNG = SimRNG.InitializeRNSeed()

Queue1 = SimClasses.FIFOQueue()
Queue2 = SimClasses.FIFOQueue()
Server1 = SimClasses.Resource()
Server2 = SimClasses.Resource()
TotalTime1 = SimClasses.DTStat()
TotalTime2 = SimClasses.DTStat()
Calendar = SimClasses.EventCalendar()

TheCTStats = []
TheDTStats = []
TheQueues = []
TheResources = []

TheDTStats.append(TotalTime1)
TheDTStats.append(TotalTime2)
TheQueues.append(Queue1)
TheQueues.append(Queue2)
TheResources.append(Server1)
TheResources.append(Server2)

# lists to collect across replication outputs
AllQueue1 = []
AllQueue2 = []
AllTotalTime1 = []
AllTotalTime2 = []
AllUtil1 = []
AllUtil2 = []

Server1.SetUnits (1) 
Server2.SetUnits (1) 

MeanTBA1 = 1/(1.3*0.9)
MeanTBA2 = 1/(0.4*0.9)
MeanPT1_1 = 1.0
MeanPT1_2 = 2.0
MeanPT2 = 1.0
WarmUp = 5000.0
RunLength = 80000.0

def Arrival1():
    SimFunctions.Schedule(Calendar,"Arrival1",SimRNG.Expon(MeanTBA1, 1))
    Class1Customer = SimClasses.Entity()
    Class1Customer.ClassNum = 1
    
    if Server1.Busy == 0:
        Server1.Seize(1)
        SimFunctions.SchedulePlus(Calendar,"EndOfService1",SimRNG.Expon(MeanPT1_1,3), Class1Customer)
    elif Server2.Busy == 0:
        Server2.Seize(1)
        SimFunctions.SchedulePlus(Calendar,"EndOfService2",SimRNG.Expon(MeanPT1_2,4), Class1Customer)
    else:
        Queue1.Add(Class1Customer)

def Arrival2():
    SimFunctions.Schedule(Calendar,"Arrival2",SimRNG.Expon(MeanTBA2, 2))
    Class2Customer = SimClasses.Entity()
    Class2Customer.ClassNum = 2

    if Server2.Busy == 0:
        Server2.Seize(1)
        SimFunctions.SchedulePlus(Calendar,"EndOfService2",SimRNG.Expon(MeanPT2,5), Class2Customer)
    else:
        Queue2.Add(Class2Customer)

def EndOfService1(DepartingCustomer): # class 1 job departing server 1
    TotalTime1.Record(SimClasses.Clock - DepartingCustomer.CreateTime)
    if Queue1.NumQueue() > 0:
        NextCustomer = Queue1.Remove()
        SimFunctions.SchedulePlus(Calendar, "EndOfService1", SimRNG.Expon(MeanPT1_1,3), NextCustomer)
    else:
        Server1.Free(1)

def EndOfService2(DepartingCustomer): # class 1 or 2 job departing server 2; give priority to class 1
    if DepartingCustomer.ClassNum == 1: # class 1 customer departing
        TotalTime1.Record(SimClasses.Clock - DepartingCustomer.CreateTime)
    else: # class 2 customer departing
        TotalTime2.Record(SimClasses.Clock - DepartingCustomer.CreateTime)

    if Queue1.NumQueue() > 0: # priority to class 1
        NextCustomer = Queue1.Remove()
        SimFunctions.SchedulePlus(Calendar,"EndOfService2", SimRNG.Expon(MeanPT1_2,4), NextCustomer)
    elif Queue2.NumQueue() > 0: 
        NextCustomer = Queue2.Remove()
        SimFunctions.SchedulePlus(Calendar,"EndOfService2", SimRNG.Expon(MeanPT2,5), NextCustomer)
    else:
        Server2.Free(1)

# replication loop
for reps in range(0,10,1):
    print reps+1
    SimFunctions.SimFunctionsInit(Calendar,TheQueues,TheCTStats,TheDTStats,TheResources)

    SimFunctions.Schedule(Calendar,"Arrival1",SimRNG.Expon(MeanTBA1, 1))
    SimFunctions.Schedule(Calendar,"Arrival2",SimRNG.Expon(MeanTBA2, 2))
    SimFunctions.Schedule(Calendar,"EndSimulation",RunLength)
    SimFunctions.Schedule(Calendar,"ClearIt",WarmUp)
    
    NextEvent = Calendar.Remove()
    SimClasses.Clock = NextEvent.EventTime
    if NextEvent.EventType == "Arrival1":
        Arrival1()
    elif NextEvent.EventType == "Arrival2":
        Arrival2() 
    
    # main simulation loop
    while NextEvent.EventType != "EndSimulation":
        NextEvent = Calendar.Remove()
        SimClasses.Clock = NextEvent.EventTime
        if NextEvent.EventType == "Arrival1":
            Arrival1()
        elif NextEvent.EventType == "Arrival2":
            Arrival2()
        elif NextEvent.EventType == "EndOfService1":
            EndOfService1(NextEvent.WhichObject) 
        elif NextEvent.EventType == "EndOfService2":
            EndOfService2(NextEvent.WhichObject)
        elif NextEvent.EventType == "ClearIt":
            SimFunctions.ClearStats(TheCTStats,TheDTStats)

    # save the output for each replication
    AllQueue1.append(Queue1.Mean())
    AllQueue2.append(Queue2.Mean())
    AllTotalTime1.append(TotalTime1.Mean())
    AllTotalTime2.append(TotalTime2.Mean()) 
    AllUtil1.append(Server1.Mean())
    AllUtil2.append(Server2.Mean())

# print the estimates
print ("Estimated Total Time 1 = ",np.mean(AllTotalTime1))
print ("Estimated Total Time 2 = ",np.mean(AllTotalTime2))
print ("Estimated Queue 1 length = ", np.mean(AllQueue1))
print ("Estimated Queue 2 length = " , np.mean(AllQueue2))
print ("Estimated Server 1 Util. = ", np.mean(AllUtil1))
print ("Estimated Server 2 Util. = " , np.mean(AllUtil2))
