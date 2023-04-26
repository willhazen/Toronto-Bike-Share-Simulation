class Station:
    def __init__(self, station_id, level, capacity):
        self.id = station_id
        self.level = level
        self.capacity = capacity
        self.bikes = {}
        self.bike_list = []
        for i in range(level):
            bike_id = f"{station_id}-{i+1}"  # create unique bike ID
            self.bikes[bike_id] = True  # mark bike as available
            self.bike_list.append(bike_id)

    def rent_bike(self):
        # Request a bike from the station
        if self.level > 0:
            if self.bike_list:
                random_index = np.random.randint(0, len(self.bike_list))
                bike_id = self.bike_list.pop(random_index)
                self.level -= 1
                return bike_id
        return None

    def return_bike(self, bike_id):
        # # Return a bike to the station
        if self.level < self.capacity:
            self.bike_list.append(bike_id)
            self.level += 1

    def Get_Bike_List(self):
        return self.bike_list


class Customer:
    def __init__(self, customer_id, start_s_id, bike=None):
        self.customer_id = customer_id
        self.start_s_id = start_s_id
        self.end_s_id = 0
        self.station_level = 0
        self.bike = bike
        self.T = 0
        self.time = 0
        self.Min = None
        self.Trip_Time = 0

    def rent_bike(self):
        station = StationDict[self.start_s_id]
        print(f"   Customer Arrives at S{station.id} with Level: {station.level}")

        if station.level > 0:
            self.bike = station.rent_bike()
            self.station_level = station.level
            #print(f"    [Customer Rent Bikes] Customer ID: {self.customer_id} | Bike ID {self.bike} || Start Time: {self.T}:{self.Min} || From: S{self.start_s_id} -> Remaining Level: {self.station_level}")
            self.Departure()
        else:
            print(f"    -   (EMPTY) -- Customer {self.customer_id} CANNOT RENT BIKE -- EMPTY STATION {self.start_s_id} w/ level {self.station_level} -- (EMPTY)")

    # def return_bike(self, end_station, bike):
    #     destination_station = StationDict[end_station]
    #     destination_station.return_bike(bike)
    #     self.station_level = destination_station.level
        
    def return_bike(self, end_station, bike):
        destination_station = StationDict[end_station]

        if destination_station.level >= destination_station.capacity:
            print(f"    -   (FULL) Customer {self.customer_id} CANNOT RETURN BIKE -- FULL STATION {destination_station.id} w/ level {destination_station.level} -- (FULL)")

        else:
            destination_station.return_bike(bike)
            self.station_level = destination_station.level
    
    def Departure(self):
        self.end_s_id = int(self.Destination())
        end_station = StationDict[self.end_s_id]
        
        trip_time = self.TripDuration()
        self.Trip_Time = trip_time
        
        print(f"        [Customer Rents Bike and Departs]: Customer ID: {self.customer_id} | Bike ID: {self.bike}")
        print(f"            - Start Time:{self.time}:{self.Min}")
        print(f"            - From: S{self.start_s_id} -> Level {self.station_level} | To: S{end_station.id} -> Level {end_station.level}")
        print(f"            - Expected Trip Time: {self.Trip_Time} min")
        
        SimFunctions.Schedule(Calendar, "Bike_Arrival", trip_time)
        return self.end_s_id
    

######
#HELPER FUNCTIONS
######
    def Destination(self):
        end_s_id = None
        while end_s_id is None:
            end_s_id = self.ChoosingRoute(prob_df, start_s_id=self.start_s_id, start_time=self.T)
        return end_s_id
    
    def ChoosingRoute(self, prob_df, start_s_id, start_time):
        retry = None
        try:
            #np.random.seed(2)
            start_row = prob_df.loc[(start_s_id, start_time)]
            probs = start_row.values
            end_s_id = np.random.choice(start_row.index, p=probs)
            return end_s_id
        except KeyError:
            print(f"NO DATA found for start station: '{start_s_id}' and start T: '{start_time}'")
            retry = None
            return retry

    def TripDuration(self):
        try:
            duration_data = avg_trip_duration[(avg_trip_duration["Start Time (per 30min)"] == self.T) &
                                            (avg_trip_duration["Start Station Id"] == self.start_s_id) &
                                            (avg_trip_duration["End Station Id"] == self.end_s_id)]["Avg_Trip_Duration"].values[0]
        except IndexError:
            avg_start_id = avg_trip_duration[(avg_trip_duration["Start Time (per 30min)"] == self.T) & (avg_trip_duration["Start Station Id"] == self.start_s_id)]["Avg_Trip_Duration"]
            avg_start = avg_trip_duration[(avg_trip_duration["Start Station Id"] == self.start_s_id)]["Avg_Trip_Duration"].mean()
            avg_end = avg_trip_duration[(avg_trip_duration["Start Station Id"] == self.end_s_id)]["Avg_Trip_Duration"].mean()
            avg_dur = (avg_start_id + avg_start + avg_end)/3
            duration_data = avg_dur.values[0]

        trip_time = duration_data * SimRNG_Modified.Lognormal(ZSimRNG, E_x, SD_x**2, 4)
        trip_time = np.round(trip_time)
        #trip_time = max(2, trip_time)
        return trip_time

def Start():
    SimFunctions.Schedule(Calendar, "Customer_Arrival", SimRNG_Modified.Expon(ZSimRNG, 0, 1))
    
def NextCustomerID():
    if not hasattr(NextCustomerID, "counter"):
        NextCustomerID.counter = 0
    NextCustomerID.counter += 1
    return NextCustomerID.counter


def Customer_Arrival_Rate(T):
    #np.random.seed(1)
    temp_df = arrival_df[arrival_df["Start Time (per 30min)"] == T]
    arrival_rates = temp_df["ArrivalRate (per min)"].values
    possible_station_ids = temp_df["Start Station Id"].values
    selected_station_id = np.random.choice(possible_station_ids, p=(arrival_rates / arrival_rates.sum()))
    arrival_rate = arrival_df[(arrival_df["Start Time (per 30min)"] == T) & (arrival_df["Start Station Id"] == selected_station_id)]["ArrivalRate (per min)"].values[0]
    return arrival_rate, selected_station_id

def Customer_Arrival(empty_error, CustomerList, T, minute):
    arrival_rate, station_id = Customer_Arrival_Rate(T)
    mu = 1/arrival_rate
    SimFunctions.Schedule(Calendar, "Customer_Arrival", np.round(SimRNG_Modified.Expon(ZSimRNG, mu, 1)))
    
    station = StationDict[station_id]
    customer_id = NextCustomerID()
    customer = Customer(customer_id, station_id)
    customer.start_s_id = station_id
    customer.station_level = station.level
    customer.T = T
    customer.time = T//2
    customer.Min = minute
################################################################
# STATION EMPTY
################################################################
    if customer.station_level == 0:
        print(f"    (EMPTY) -- Customer {customer.customer_id} CANNOT RENT BIKE | S{customer.start_s_id} -> level {customer.station_level} -- (EMPTY)")
        empty_error += 1
    else:
        CustomerList.append(customer)
        customer.rent_bike()
        
    return empty_error, customer


def Bike_Arrival(Full_Error, CustomerList, temp_customer, T, minute):
    end_s_id = temp_customer.end_s_id
    if end_s_id != 0:
        end_station = StationDict[end_s_id] 
        
        if end_station.level < end_station.capacity:
            for customer in CustomerList:
                end_time_minutes = (T//2) * 60 + minute
                start_time_minutes = customer.time * 60 + customer.Min
                total_trip_time = end_time_minutes - start_time_minutes
                if customer.end_s_id == end_station.id and customer.bike is not None and total_trip_time >= customer.Trip_Time:
                    customer.return_bike(customer.end_s_id, customer.bike)
                    print(f"                [BIKE RETURNED] Customer ID: {customer.customer_id} | Bike ID: {customer.bike}")
                    print(f"                    - Start Time:{customer.time}:{customer.Min} - End Time:{T//2}:{minute}")
                    print(f"                    - Expected Trip Time: {customer.Trip_Time} min")
                    print(f"                    - Total Trip Time: {total_trip_time} min")
                    print(f"                    - From: S{customer.start_s_id} | To: S{end_station.id} -> Level {end_station.level}")
                    CustomerList.remove(customer)
                    return Full_Error

    ################################################################
    #STATION FULL
    ################################################################
        else:
            for customer in CustomerList:
                customer_end_station = StationDict[customer.start_s_id]
                end_time_minutes = (T//2) * 60 + minute
                start_time_minutes = customer.time * 60 + customer.Min
                total_trip_time = end_time_minutes - start_time_minutes
                if customer.end_s_id == customer_end_station.id and customer_end_station.level >= customer_end_station.capacity and total_trip_time >= customer.Trip_Time:
                    temp_customer = customer
                    print(f"     (FULL) -- Start Time:{customer.time}:{customer.Min} - End Time:{T//2}:{minute} || Customer ID: {customer.customer_id} || To: S{end_station.id} -> Level {end_station.level} | Capacity {end_station.capacity} || From: S{customer.start_s_id} -- (FULL)")
                    Full_Error += 1
                    Retrial(temp_customer=temp_customer, T=T, minute=minute)
                    return Full_Error
                else:
                    pass
    else:
        pass
    
    return Full_Error


def Retrial(temp_customer, T, minute):
    customer = temp_customer
    customer.T = T
    customer.time = T//2
    customer.Min = minute
    customer.end_s_id = customer.Destination()
    print(f"    [TRAVELS TO NEW STATION] Start Time:{customer.time}:{customer.Min} || Customer ID: {customer.customer_id} travels to S{customer.end_s_id}")
    trip_time = customer.TripDuration()
    SimFunctions.Schedule(Calendar, "Bike_Arrival", min(30, trip_time))

