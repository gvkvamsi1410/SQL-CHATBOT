import mysql.connector
from mysql.connector import Error

def populate_database():
    try:
        # Connect to MySQL server without specifying a database to create it first
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Admin1234'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create Database if it doesn't exist (relates to their resume: Metro Vehicle and Crew Scheduling)
            cursor.execute("CREATE DATABASE IF NOT EXISTS metro_scheduling")
            print("Database 'metro_scheduling' is ready.")
            
            # Switch to the new database
            cursor.execute("USE metro_scheduling")
            
            # Create Vehicles table safely without deleting anything
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Vehicles (
                    VehicleID INT PRIMARY KEY AUTO_INCREMENT,
                    Type VARCHAR(50),
                    Capacity INT,
                    Status VARCHAR(50)
                )
            """)
            
            # Create Crew table safely
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Crew (
                    CrewID INT PRIMARY KEY AUTO_INCREMENT,
                    Name VARCHAR(100),
                    Role VARCHAR(50),
                    Status VARCHAR(50)
                )
            """)
            
            # Create Schedules table safely
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Schedules (
                    ScheduleID INT PRIMARY KEY AUTO_INCREMENT,
                    VehicleID INT,
                    CrewID INT,
                    Route VARCHAR(100),
                    StartTime DATETIME,
                    EndTime DATETIME,
                    FOREIGN KEY (VehicleID) REFERENCES Vehicles(VehicleID),
                    FOREIGN KEY (CrewID) REFERENCES Crew(CrewID)
                )
            """)
            
            print("Tables are ready.")
            
            # Insert dummy data only if the tables are empty
            cursor.execute("SELECT COUNT(*) FROM Vehicles")
            if cursor.fetchone()[0] == 0:
                print("Inserting dummy Vehicles...")
                vehicles_data = [
                    ('Metro Train Type A', 500, 'Active'),
                    ('Metro Train Type B', 600, 'Maintenance'),
                    ('Metro Train Type C', 550, 'Active')
                ]
                cursor.executemany("INSERT INTO Vehicles (Type, Capacity, Status) VALUES (%s, %s, %s)", vehicles_data)
                
            cursor.execute("SELECT COUNT(*) FROM Crew")
            if cursor.fetchone()[0] == 0:
                print("Inserting dummy Crew...")
                crew_data = [
                    ('John Doe', 'Driver', 'Available'),
                    ('Jane Smith', 'Driver', 'On Leave'),
                    ('Mike Johnson', 'Conductor', 'Available')
                ]
                cursor.executemany("INSERT INTO Crew (Name, Role, Status) VALUES (%s, %s, %s)", crew_data)
                
            cursor.execute("SELECT COUNT(*) FROM Schedules")
            if cursor.fetchone()[0] == 0:
                print("Inserting dummy Schedules...")
                schedule_data = [
                    (1, 1, 'Line 1 Northbound', '2026-07-01 08:00:00', '2026-07-01 16:00:00'),
                    (3, 3, 'Line 2 Eastbound', '2026-07-01 09:00:00', '2026-07-01 17:00:00')
                ]
                cursor.executemany("INSERT INTO Schedules (VehicleID, CrewID, Route, StartTime, EndTime) VALUES (%s, %s, %s, %s, %s)", schedule_data)
                
            # Commit the changes
            connection.commit()
            print("Dummy data successfully pushed!")

    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

if __name__ == '__main__':
    populate_database()
