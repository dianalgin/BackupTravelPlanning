
import pandas as pd

def import_data():
    # @diana and denis, change to your directory
    gtfs_dir = '/Users/paulinaheine/Codes/BackupTravelPlanning/gtfs_dummy_data/'

    # load data
    agency_df = pd.read_csv(gtfs_dir + 'agency.txt')
    stops_df = pd.read_csv(gtfs_dir + 'stops.txt')
    routes_df = pd.read_csv(gtfs_dir + 'routes.txt')
    trips_df = pd.read_csv(gtfs_dir + 'trips.txt')
    stop_times_df = pd.read_csv(gtfs_dir + 'stop_times.txt')
    calendar_df = pd.read_csv(gtfs_dir + 'calendar.txt')

    return agency_df, stops_df, routes_df, trips_df, stop_times_df, calendar_df

agency_df, stops_df, routes_df, trips_df, stop_times_df, calendar_df = import_data()

# Beispielanzeige der Daten
print("Stops Data:")
print(stops_df.head())

print("\nStop Times Data:")
print(stop_times_df.head())

