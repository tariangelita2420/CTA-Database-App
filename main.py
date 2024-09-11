#
# Name: Taria Reese
# Project 1: CTA Database App
# Overview: Program that uses python and SQL to
# output data from the CTA daily ridership data
# depending on the commands input by the user
# there are 9 commands that allow for a variety
# of data displayed with some including plotting
#
import math
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

##################################################################
#
# print_stats
#
# Given a connection to the CTA database, executes various
# SQL queries to retrieve and output basic stats.
#
def print_stats(dbConn):
    dbCursor = dbConn.cursor()
    
    print("General Statistics:")
    
    dbCursor.execute("Select count(*) From Stations;")
    row = dbCursor.fetchone();
    print("  # of stations:", f"{row[0]:,}")

    dbCursor.execute("Select count(*) From Stops;")
    row = dbCursor.fetchone();
    print("  # of stops:", f"{row[0]:,}")

    dbCursor.execute("Select count(*) From Ridership;")
    row = dbCursor.fetchone();
    print("  # of ride entries:", f"{row[0]:,}")

    dbCursor.execute("Select strftime('%Y-%m-%d', MIN(Ride_Date)), strftime('%Y-%m-%d',MAX(Ride_Date)) From Ridership;")
    row = dbCursor.fetchone();
    print("  date range:", row[0], "-", row[1])

    dbCursor.execute("Select SUM(Num_Riders) From Ridership;")
    row = dbCursor.fetchone();
    print("  Total ridership:", f"{row[0]:,}")

##################################################################
# Function to allow user to find stations names entered by the user
# allows user to enter partial names as input
def command_1(dbConn):
    dbCursor = dbConn.cursor()
    nameInput = input("\nEnter partial station name (wildcards _ and %): ")
    dbCursor.execute(
        "SELECT Station_ID, Station_Name FROM Stations WHERE Station_Name LIKE ? ORDER BY Station_Name ASC",
        (f"{nameInput}",))
    names = dbCursor.fetchall()
    if names:
        for row in names:
            print(f"{row[0]} : {row[1]}")
    else:
        print("**No stations found...")

##################################################################
# Function to allow user to enter a station name and finds
# the percentages of rider on weekdays, weekends, and holiday's
def command_2(dbConn):
    cursor = dbConn.cursor()
    query = "SELECT SUM(Num_Riders) FROM Ridership WHERE Station_ID = (SELECT Station_ID FROM Stations WHERE Station_Name = ?)"
    stationName = input("\nEnter the name of the station you would like to analyze: ")

    # Total ridership
    cursor.execute(query, (stationName,))
    total_riders = cursor.fetchone()[0]
    if total_riders is None:
        print("**No data found...\n")
        return None, None, None

    # Weekday ridership
    cursor.execute(query + " AND Type_of_Day = 'W'", (stationName,))
    weekday_riders = cursor.fetchone()[0]

    # Saturday ridership
    cursor.execute(query + " AND Type_of_Day = 'A'", (stationName,))
    saturday_riders = cursor.fetchone()[0]

    # Sunday/holiday ridership
    cursor.execute(query + " AND Type_of_Day = 'U'", (stationName,))
    sunday_riders = cursor.fetchone()[0]

    #calculates the percentages and outputs results
    if total_riders > 0:
        weekday_pct = (weekday_riders / total_riders) * 100
        saturday_pct = (saturday_riders / total_riders) * 100
        sunday_pct = (sunday_riders / total_riders) * 100
        print(f"Percentage of ridership for the {stationName} station:")
        print("  Weekday ridership:", f"{weekday_riders:,}", f"({weekday_pct:.2f}%)")
        print("  Saturday ridership:", f"{saturday_riders:,}", f"({saturday_pct:.2f}%)")
        print("  Sunday/holiday ridership:", f"{sunday_riders:,}", f"({sunday_pct:.2f}%)")
        print("  Total ridership:", f"{total_riders:,}")
    else:
        print("**No data found...\n")

##################################################################
# Function to output ridership on weekdays for all
# the stations in the database with percentages
def command_3(dbConn):
    cursor = dbConn.cursor()

    #executes the query
    query = """
    SELECT s.Station_Name, SUM(r.Num_Riders) AS Weekday_Total
    FROM Ridership r
    INNER JOIN Stations s ON r.Station_ID = s.Station_ID
    WHERE r.Type_of_Day = 'W'
    GROUP BY s.Station_Name
    ORDER BY Weekday_Total DESC;
    """
    cursor.execute(query)
    query_results = cursor.fetchall()

    # Sum total ridership for weekdays across all stations
    overall_weekday_ridership = sum(ridership for _, ridership in query_results)

    # Outputs the results
    print("Ridership on Weekdays for Each Station")
    for station, ridership in query_results:
        ridership_percentage = (ridership / overall_weekday_ridership) * 100
        print(f"{station} : {ridership:,} ({ridership_percentage:.2f}%)")

##################################################################
# Function that allows the user to enter a line color and direction
# to output all stops in that line/color
def command_4(dbConn):
    cursor = dbConn.cursor()
    line_color = input("\nEnter a line color (e.g. Red or Yellow): ").upper()

    # SQL query for stops by line color
    color_based_query = """
        SELECT Stop_Name, ADA 
        FROM Stops 
        JOIN StopDetails ON Stops.Stop_ID = StopDetails.Stop_ID 
        JOIN Lines ON StopDetails.Line_ID = Lines.Line_ID 
        WHERE UPPER(Lines.Color) = ? 
        GROUP BY Stop_Name 
        ORDER BY Stop_Name ASC;
        """
    cursor.execute(color_based_query, (line_color,))
    color_based_stops = cursor.fetchall()

    if color_based_stops:
        travel_direction = input("Enter a direction (N/S/W/E): ").upper()

        # SQL query for stops by line color and direction
        direction_based_query = """
            SELECT Stop_Name, ADA 
            FROM Stops 
            JOIN StopDetails ON Stops.Stop_ID = StopDetails.Stop_ID 
            JOIN Lines ON StopDetails.Line_ID = Lines.Line_ID 
            WHERE UPPER(Lines.Color) = ? AND UPPER(Stops.Direction) = ? 
            GROUP BY Stop_Name 
            ORDER BY Stop_Name ASC;
            """
        cursor.execute(direction_based_query, (line_color, travel_direction))
        direction_based_stops = cursor.fetchall()

        if direction_based_stops:
            for row in direction_based_stops:
                if (row[1] == 1):
                    print(row[0], ": direction = ", travel_direction, "(handicap accessible)")
                else:
                    print(row[0], ": direction = ", travel_direction, "(not handicap accessible)")
        else:
            print("**That line does not run in the direction chosen...")
    else:
        print("**No such line...")

##################################################################
# Function that outputs the number of stops for each line/color and
# direction with percentages included
def command_5(dbConn):
    cursor = dbConn.cursor()

    # Query for counting stops depending on line/color
    cursor.execute(""" SELECT Lines.Color, Stops.Direction, COUNT(DISTINCT Stops.Stop_ID) AS Num_Stops
    FROM Stops
    INNER JOIN StopDetails ON Stops.Stop_ID = StopDetails.Stop_ID
    JOIN Lines ON StopDetails.Line_ID = Lines.Line_ID
    GROUP BY Lines.Color, Stops.Direction
    ORDER BY Lines.Color ASC, Stops.Direction ASC;""")

    stops = cursor.fetchall()
    stops_count = """
        SELECT COUNT() FROM Stops;
        """
    cursor.execute(stops_count)
    total_stops = cursor.fetchone()[0]

    # output results
    print("Number of Stops For Each Color By Direction")
    for color, direction, num_stops in stops:
        percentage = (num_stops / total_stops) * 100
        print(f"{color} going {direction} : {num_stops} ({percentage:.2f}%)")

##################################################################
# Function that allows user to enter station name and output
# total ridership for each year in the chosen station
def command_6(dbConn):
    input_station_name = input("\nEnter a station name (wildcards _ and %): ")
    query_cursor = dbConn.cursor()

    # get user station name
    station_query = """
       SELECT Station_Name FROM Stations
       WHERE Station_Name LIKE ?
       GROUP BY Station_Name;
       """
    query_cursor.execute(station_query, (input_station_name,))
    found_stations = query_cursor.fetchall()

    if len(found_stations) > 1:
        print("**Multiple stations found...")
        return
    elif not found_stations:
        print("**No station found...")
        return

    # gets total ridership for each year
    exact_station_name = found_stations[0][0]
    ridership_query = """
       SELECT STRFTIME('%Y', Ride_Date) AS Year, SUM(Num_Riders) AS Total
       FROM Ridership JOIN Stations ON Ridership.Station_ID = Stations.Station_ID
       WHERE Station_Name = ?
       GROUP BY Year
       ORDER BY Year ASC;
       """
    query_cursor.execute(ridership_query, (exact_station_name,))

    # print results and plot
    yearly_ridership = query_cursor.fetchall()
    if yearly_ridership:
        print(f"Yearly Ridership at {exact_station_name}")
        for each_year, total_riders in yearly_ridership:
            print(f"{each_year} : {total_riders:,}")

        plot_query = input("Plot? (y/n) \n")
        if plot_query.lower() == 'y':
            plot_years = [int(data[0]) for data in yearly_ridership]
            plot_totals = [data[1] for data in yearly_ridership]
            plt.figure(figsize=(10, 6))
            plt.plot(plot_years, plot_totals, marker='o')
            plt.title(f"Yearly Ridership at {exact_station_name}")
            plt.xlabel("Year")
            plt.ylabel("Number of Riders")
            plt.xticks(plot_years, rotation=45)
            plt.tight_layout()
            plt.show()

##################################################################
# Function that allows user to input station name&year and output the
# total ridership for each month in that year and can be plotted
def command_7(dbConn):
    pattern_station_name = input("\nEnter a station name (wildcards _ and %): ")

    cursor = dbConn.cursor()

    # Query to find stations matching the pattern
    cursor.execute("SELECT Station_ID, Station_Name FROM Stations WHERE Station_Name LIKE ?", (pattern_station_name,))
    found_stations = cursor.fetchall()

    if not found_stations:
        print("**No station found...")
        return
    elif len(found_stations) > 1:
        print("**Multiple stations found...")
        return
    input_year = input("Enter a year: ")

    # Query to get monthly ridership data
    selected_station_id = found_stations[0][0]
    monthly_ridership_query = """
        SELECT STRFTIME('%m/%Y', Ride_Date) AS Month, SUM(Num_Riders)
        FROM Ridership
        WHERE Station_ID = ? AND STRFTIME('%Y', Ride_Date) = ?
        GROUP BY Month
        ORDER BY Ride_Date
        """
    cursor.execute(monthly_ridership_query, (selected_station_id, input_year))
    monthly_data = cursor.fetchall()

    # Display the monthly ridership data
    print(f"Monthly Ridership at {found_stations[0][1]} for {input_year}")
    for month_period, total in monthly_data:
        print(f"{month_period} : {total:,}")

    # plot data if user wants
    decision_to_plot = input("Plot? (y/n) \n")
    if decision_to_plot.lower() == 'y':
        plot_months = [int(month.split('/')[0]) for month, _ in monthly_data]
        plot_totals = [total for _, total in monthly_data]

        plt.figure(figsize=(10, 6))
        plt.plot(plot_months, plot_totals, marker='o')
        plt.title(f"Monthly Ridership at {found_stations[0][1]} for {input_year}")
        plt.xlabel("Month")
        plt.ylabel("Number of Riders")
        plt.xticks(range(1, 13))
        plt.grid(True)
        plt.tight_layout()
        plt.show()

##################################################################
# Function that allows user to input two station name&year and output the
# total ridership for each day in that year and can be plotted
def command_8(dbConn):
    print()
    comparison_year = input("Year to compare against? ")

    cursor = dbConn.cursor()

    def get_station_data(station_query):
        cursor.execute("SELECT Station_ID, Station_Name FROM Stations WHERE Station_Name LIKE ?", (station_query,))
        found_stations = cursor.fetchall()
        if len(found_stations) == 0:
            print("**No station found...")
            return None, None
        elif len(found_stations) > 1:
            print("**Multiple stations found...")
            return None, None
        return found_stations[0]

    print()
    first_station_query = input("Enter station 1 (wildcards _ and %): ")

    first_station_id, first_station_name = get_station_data(first_station_query)
    if first_station_id is None:
        return
    print()
    second_station_query = input("Enter station 2 (wildcards _ and %): ")
    second_station_id, second_station_name = get_station_data(second_station_query)
    if second_station_id is None:
        return

    # Retrieves the full year's data for each station for plotting
    first_station_data = gather_ridership(cursor, first_station_id, comparison_year)
    second_station_data = gather_ridership(cursor, second_station_id, comparison_year)

    # Displays only the first 5 and last 5 days of ridership data
    print(f"Station 1: {first_station_id} {first_station_name}")
    show_ridership(first_station_data)

    print(f"Station 2: {second_station_id} {second_station_name}")
    show_ridership(second_station_data)
    print()

    # Asks user if they want to plot the data
    plot_decision = input("Plot? (y/n) \n")
    if plot_decision.lower() == 'y':
        plot_ridership(first_station_data, second_station_data, first_station_name, second_station_name, comparison_year)

#
# helper function to get rider ship data
def gather_ridership(cursor, station_id, year):
    cursor.execute("""
        SELECT DATE(Ride_Date) as RideDate, Num_Riders 
        FROM Ridership 
        WHERE Station_ID = ? AND STRFTIME('%Y', Ride_Date) = ? 
        ORDER BY RideDate
        """, (station_id, year))
    return cursor.fetchall()

#
# helper function to display ridership info
def show_ridership(ridership_info):
    for ride_date, num_riders in ridership_info[:5] + ridership_info[-5:]:
        print(f"{ride_date} {num_riders}")

#
# helper function to plot ridership data
def plot_ridership(ridership_1, ridership_2, station_1, station_2, year):
    # Prepares the data for plotting
    days_station_1 = [index for index in range(len(ridership_1))]
    riders_station_1 = [riders for _, riders in ridership_1]

    days_station_2 = [index for index in range(len(ridership_2))]
    riders_station_2 = [riders for _, riders in ridership_2]

    plt.figure(figsize=(10, 6))
    plt.plot(days_station_1, riders_station_1, label=station_1)
    plt.plot(days_station_2, riders_station_2, label=station_2)
    plt.title(f"Ridership Each Day of {year}")
    plt.xlabel("Day")
    plt.ylabel("Number of Riders")
    plt.legend()
    plt.show()

##################################################################
# Function that allows user to enter a longitude and latitude and
# find stations within a square mile radius and can be plotted with a map
def command_9(dbConn):
    try:
        input_latitude = float(input("\nEnter a latitude: "))
        if not 40 <= input_latitude <= 43:
            print("**Latitude entered is out of bounds...")
            return

        input_longitude = float(input("Enter a longitude: "))
        if not -88 <= input_longitude <= -87:
            print("**Longitude entered is out of bounds...")
            return

        # calculates milage
        degrees_per_mile_lat = 1 / 69
        degrees_per_mile_long = 1 / 51

        upper_latitude = round(input_latitude + degrees_per_mile_lat, 3)
        lower_latitude = round(input_latitude - degrees_per_mile_lat, 3)
        upper_longitude = round(input_longitude + degrees_per_mile_long, 3)
        lower_longitude = round(input_longitude - degrees_per_mile_long, 3)

        station_query = """
        SELECT DISTINCT Stations.Station_Name, Stops.Latitude, Stops.Longitude 
        FROM Stations
        JOIN Stops ON Stations.Station_ID = Stops.Station_ID
        WHERE Stops.Latitude BETWEEN ? AND ? AND Stops.Longitude BETWEEN ? AND ?
        ORDER BY Stations.Station_Name;
        """
        query_cursor = dbConn.cursor()
        query_cursor.execute(station_query, (lower_latitude, upper_latitude, lower_longitude, upper_longitude))
        nearby_stations = query_cursor.fetchall()

        if not nearby_stations:
            print("**No stations found...")
            return

        print("\nList of Stations Within a Mile")
        for station, lat, lon in nearby_stations:
            print(f"{station} : ({lat}, {lon})")

        map_plot_decision = input("Plot? (y/n) \n")
        if map_plot_decision.lower() == 'y':
            display_stations_map(nearby_stations)

    except ValueError:
        print("**Invalid input. Please enter a valid number.")


# displays the map with a chicago picture with plots of the stations
def display_stations_map(station_list):
    map_image = plt.imread("chicago.png")
    longitudes = [longitude for _, _, longitude in station_list]
    latitudes = [latitude for _, latitude, _ in station_list]
    station_names = [name for name, _, _ in station_list]

    map_bounds = [-87.9277, -87.5569, 41.7012, 42.0868]
    plt.imshow(map_image, extent = map_bounds)
    plt.scatter(longitudes, latitudes, color='blue')
    for index, station in enumerate(station_names):
        plt.annotate(station, (longitudes[index], latitudes[index]))
    plt.xlim([-87.9277, -87.5569])
    plt.ylim([41.7012, 42.0868])
    plt.title("Stations Near You")
    plt.show()

##################################################################
#
# main
#
print('** Welcome to CTA L analysis app **')
print()

dbConn = sqlite3.connect('CTA2_L_daily_ridership.db')

print_stats(dbConn)

# Command Loop
while True:
    command = input("Please enter a command (1-9, x to exit): ")

    if command == '1':
        command_1(dbConn)
    elif command == '2':
        command_2(dbConn)
    elif command == '3':
        command_3(dbConn)
    elif command == '4':
        command_4(dbConn)
    elif command == '5':
        command_5(dbConn)
    elif command == '6':
        command_6(dbConn)
    elif command == '7':
        command_7(dbConn)
    elif command == '8':
        command_8(dbConn)
    elif command == '9':
        command_9(dbConn)
    elif command.lower() == 'x':
        break
    else:
        print(" **Error, unknown command, try again...")

#
# done
#
