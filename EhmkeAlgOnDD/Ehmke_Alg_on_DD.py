from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import math


def import_data():
    #  change to your directory
    gtfs_dir = 'C:/Users/Diana Lutska/DAP/gtfs_dummy_data/'

    # load data
    agency_df = pd.read_csv(gtfs_dir + 'agency.txt')
    stops_df = pd.read_csv(gtfs_dir + 'stops.txt')
    routes_df = pd.read_csv(gtfs_dir + 'routes.txt')
    trips_df = pd.read_csv(gtfs_dir + 'trips.txt')
    stop_times_df = pd.read_csv(gtfs_dir + 'stop_times.txt')
    calendar_df = pd.read_csv(gtfs_dir + 'calendar.txt')

    return agency_df, stops_df, routes_df, trips_df, stop_times_df, calendar_df

agency_df, stops_df, routes_df, trips_df, stop_times_df, calendar_df = import_data()

# Sort by trip_id and stop_sequence to ensure legs are in order
legcreation_df = stop_times_df.sort_values(['trip_id', 'stop_sequence']).reset_index(drop=True)

#Shift the columns to get the arrival stop and time for each departure stop and time
legcreation_df['arrival_stop_id'] = legcreation_df['stop_id'].shift(-1)
legcreation_df['arrival_time'] = legcreation_df['arrival_time'].shift(-1)
#print(legcreation_df)

# Filter out the last stop of each trip, as it has no next stop
legs_df = legcreation_df[legcreation_df['trip_id'] == legcreation_df['trip_id'].shift(-1)].copy()
legs_df['arrival_stop_id']=legs_df['arrival_stop_id'].astype(int)
#print(legs_df.head())

legs_df = legs_df.merge(trips_df, on='trip_id', how='left')
#print(legs_df)

legs_df['leg'] = list(zip(
    zip(legs_df['stop_id'], legs_df['departure_time']),
    zip(legs_df['arrival_stop_id'], legs_df['arrival_time']),
    legs_df['route_id']
))

legs_df = legs_df[['trip_id', 'leg']]
#print(legs_df)


# Reliability function

# Function to calculate probability of successful transfer between two subsequent legs
def calculate_transfer_probability(prev_leg: pd.Series, next_leg: pd.Series) -> float:

    #If line = next line , then probability = 1 since the traveler remains on the same line
    if prev_leg[1][2] == next_leg[1][2]:
        return 1  
    else:
        #check if departure time is larger than arrival
        if prev_leg[1][1][1] > next_leg[1][0][1]:
            return 0
        else :
        # created random probability, just for the test, later we can either do it the same for all, or take into account the time between the transfer.
        #in Ehmke he includes walking legs, but maybe we can have some distribution function, the more time for the transfer, the highrer the chance.
            return 0.5
            
# i hope it is cumulative distribution
def calculate_cumulative_probability(itinerary) -> list[float]:
    cumulative_probabilities = [1] 
    for i in range(len(itinerary) - 1):
        prev_leg = itinerary[i]
        next_leg = itinerary[i+1]

        transfer_prob = calculate_transfer_probability(prev_leg, next_leg)
        cumulative_probabilities.append(cumulative_probabilities[-1] * transfer_prob)
    return cumulative_probabilities
  


# if there is a chance to have all succesful transfers, is the arrival time in time budget
def calculate_arrival_probability(itinerary, start_time, time_budget) -> int:
    # Check if all previous transfers were successful
    if math.prod(calculate_cumulative_probability(itinerary)) > 0:  # Only proceed if all transfers are successful( naka can be possibly made)
        # Calculate the actual arrival time at the final leg
        destination_leg = itinerary[-1]
        destination_arrival_time = destination_leg[1][1][1]
        
        start_time = datetime.strptime(start_time, "%H:%M:%S")
        destination_arrival_time = datetime.strptime(destination_arrival_time, "%H:%M:%S")

        total_travel_time = destination_arrival_time - start_time

        # Check if total travel time is within the budget
        if total_travel_time <= time_budget:
            return 1  # Probability of 1 if arrival is within the time budget
        else:
            return 0  # Probability of 0 if arrival is beyond the time budget
    else:
        return 0  # Probability of 0 if any prior transfer was unsuccessful
    
    
            
def primary_itinerary_reliability(itinerary, start_time, time_budget) -> float:
    
    cumulative_probabilities = calculate_cumulative_probability(itinerary)
    product_of_probabilities= math.prod(cumulative_probabilities)
    arrival_probability = calculate_arrival_probability(itinerary,start_time,time_budget)

    reliability = arrival_probability * product_of_probabilities
    return reliability

def backup_itinerary_reliability(itinerary, backup_itinerary:list[pd.Series], start_time, time_budget) -> float:

    arrival_probability = calculate_arrival_probability(backup_itinerary, start_time, time_budget)
    cumulative_probabilities = calculate_cumulative_probability(itinerary)
    product_of_probabilities= math.prod(cumulative_probabilities)
    
    transfer_point = backup_itinerary[0][1][0][0]
    initial_transfer_prob = 1 # Default value in case no missed transfer is identified

    for idx, leg in enumerate(itinerary[:-1]):  # Exclude last item since we're accessing i+1
        if leg[1][1][0] == transfer_point:
            prev_leg = itinerary[idx]
            missed_leg = itinerary[idx + 1]
            initial_transfer_prob = calculate_transfer_probability(prev_leg,missed_leg)
            break

    backup_reliability = arrival_probability * product_of_probabilities * (1 - initial_transfer_prob)
    
    return backup_reliability

def itinerary_reliability(itinerary : list[pd.Series],Backups : list[tuple], start_time:str, time_budget: timedelta) -> float:
    primary_reliability = primary_itinerary_reliability(itinerary,start_time,time_budget)
    added_reliability = 0
    for b in Backups:
        #this will be fucked up, as we dont know yet how to make backups ( like on what format)
        # i used Set for all backups, but set dont allow df nor lists, so backup_sequence is turple)
        backup_itinerary = b[1]
        # Convert indices back to full rows using legs_df
        backup_reliability = backup_itinerary_reliability(itinerary,backup_itinerary,start_time,time_budget)
        added_reliability += backup_reliability
    

    complete_reliability = primary_reliability + added_reliability
    return complete_reliability

itinerary = [legs_df.iloc[4],legs_df.iloc[6]]
start_time = "06:00:00"
time_budget = timedelta(hours=0, minutes=12)

# backup itineary= (leg of the prim it where is transfer, [sequence of legs of backup starting from the next after transfer], reliability, arrival time)
# idk whats happening at this point actually

transfer_leg = itinerary[0]

backup_itinerary = [legs_df.iloc[7]]


backup1 = (transfer_leg,backup_itinerary)
#creating backups list for trying out (too much hasstle with set)
Backups = [backup1]

a = itinerary_reliability(itinerary,Backups,start_time,time_budget)
print(a)



def search_adjecent_legs(node_id):
    filtered_legs = []
    for index, row in legs_df.iterrows():
        if row[1][0][0] == node_id:  
            filtered_legs.append(row)
    return filtered_legs


def travel_time(itinerary, start_time):
    destination_leg = itinerary[-1]
    destination_arrival_time = destination_leg[1][1][1]
        
    start_time = datetime.strptime(start_time, "%H:%M:%S")
    destination_arrival_time = datetime.strptime(destination_arrival_time, "%H:%M:%S")

    total_travel_time = destination_arrival_time - start_time
    return total_travel_time

def is_transfer(itinerary) -> bool:
    prev_leg = itinerary[-2]
    next_leg = itinerary[-1]
    if prev_leg[1][2] == next_leg[1][2]:
        return False
    else:
        return True
    



def find_path(origin_node: int,destination_node: int, start_time : str, time_budget: timedelta):
    
    MRIB_reliability = 0
    MRIB = None
    LIST = []

    adjecent_legs = search_adjecent_legs(origin_node)

    for leg in adjecent_legs:
        itinerary  = [leg]
        reliability = 1
        duration = travel_time(itinerary,start_time)
        expected_arrival_time = leg[1][1][1]
        Backups = []
        LIST.append([itinerary,reliability,duration,expected_arrival_time,Backups])
    
        
    while len(LIST) > 0:
        print("New iteration")
        # Find the shortest itinerary
        #Here was too many problems with search of shortest path.... so thats why it looks so bad
        min_index = 0
        min_value =  LIST[0][2]

        for i in range(1, len(LIST)):
            current_value = LIST[i][2]
            if current_value < min_value:
                min_value = current_value
                min_index = i
        
        shortest_path = LIST.pop(min_index)

        #print(len(LIST))
        #going further into the network
        #print(shortest_path)
        tail = shortest_path[0][-1]
        if tail[1][1][0] == destination_node:
            print("end station")
            Backups = shortest_path[4]
            rel = itinerary_reliability(shortest_path[0],Backups,start_time,time_budget)
            #print(rel)
            if rel > MRIB_reliability:
                print("new most reliable path")
                MRIB_reliability = rel
                MRIB = shortest_path
        else:
            print("search for the next connection")
            #here will be all possible path from the second node
            LIST1 = []
            #set of all legs adjacent to tail leg m
            next_legs = search_adjecent_legs(tail[1][1][0])
            #print(next_legs)
            for leg in next_legs:
                itinerary = shortest_path[0] + [leg]
                #print(itinerary)
                Backups = shortest_path[4]
                reliability = itinerary_reliability(itinerary,Backups,start_time,time_budget)
                #print(reliability)
                duration = travel_time(itinerary,start_time)
                #print(duration)
                expected_arrival_time = leg[1][1][1]
                #print(expected_arrival_time)
                backup = []
                if reliability > 0: # check initially so we dont waste time later
                    LIST1.append([itinerary,reliability,duration,expected_arrival_time,backup])
                else:
                    print("Reliability 0")
                # If leg l j in set of transfer legs T i 
            #print(LIST1)
            if len(LIST1) > 0:
                min_index = 0
                min_value =  LIST1[0][2]
                for i in range(1, len(LIST1)):
                        current_value = LIST1[i][2]
                        if current_value < min_value:
                            min_value = current_value
                            min_index = i
                #remove transfer so only backups are left
                shortest_next_itinerary = LIST1.pop(min_index)
                
                if is_transfer(shortest_next_itinerary[0]) is False:
                    print("direct connection")
                    LIST.append(shortest_next_itinerary)
                else :
                    print('Not transfer, search for backup')
                    if len(LIST1) > 0:
                        shortest_backup_path = min(LIST1, key=lambda x: x[2])
                        #print(shortest_backup_path)
                        shortest_backup = shortest_backup_path[0][-2:]
                        #print(shortest_backup)
                        tail = shortest_backup[-1]
                        #print(tail)
                        if tail[1][1][0] == destination_node:
                            #print("destination")
                            backup = (shortest_backup[0],[shortest_backup[1]])
                            #print(backup)
                            shortest_next_itinerary[4].append(backup)
                            #print(shortest_next_itinerary)
                            LIST.append(shortest_next_itinerary)
                        else:
                            print("well i need to think about that")
                            #Like here we deffinitely need Dijiksra from the last stop of backup to the destination, as the algorithm above just looks at all the adj legs.
                            #maybe djicstra is needed at 280 line, so the shortest backup will be searched.
                    else:
                        print("no backups")
            else:
                print("no further feasible connections")
                
    return MRIB_reliability, MRIB
        

        
origin_node = 1 # for now the departure node is 1
destination_node = 4
start_time = "06:00:00"
time_budget = timedelta(hours=0, minutes=0)

MRIB_reliability, MRIB = find_path(origin_node,destination_node,start_time,time_budget)
print(MRIB_reliability, MRIB)

primary_itinerary_MRIB = MRIB[0]
backup_itineraryies_MRIB = MRIB[4] # aka there can be multiples

# dont ask me about the indeces, i now it iss bad
print("Primary path: take trip#" ,primary_itinerary_MRIB[0][0], "then take trip#" ,primary_itinerary_MRIB[1][0])
print("In case of missed transfer, on stattion ",backup_itineraryies_MRIB[0][0][1][1][0], "take trip# ", backup_itineraryies_MRIB[0][1][0][0])