import time

minutes = 5

jdbc_url = "jdbc:sqlserver://capstone-database-server.database.windows.net:1433;database=writedatabasesilverlayer"
connection_properties = {
    "user": "capstonedioxieteam",
    "password": "Connhenbeo1@",
    "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver"
}

success = False

for i in range(minutes):
    print(f"Attempt {i+1}: Trying to wake up the database...")
    try:
        dummy_df = spark.read.jdbc(
            url=jdbc_url,
            table="(SELECT 1 AS check_value) AS dummy_table",
            properties=connection_properties
        )

        if dummy_df.count() > 0:
            print("Database is awake and ready.")
            success = True
            break
    except Exception as e:
        print(f"Attempt {i+1} failed: {e}")
    time.sleep(1)

if not success:
    raise Exception("Failed to wake up the database after multiple attempts.")
