import time

class DatabaseWakeupChecker:
    def __init__(self, spark, jdbc_url: str, connection_properties: dict, max_attempts: int = 5, sleep_seconds: int = 1):
        self.spark = spark
        self.jdbc_url = jdbc_url
        self.conn_props = connection_properties
        self.max_attempts = max_attempts
        self.sleep_seconds = sleep_seconds

    def run(self):
        success = False
        for attempt in range(1, self.max_attempts + 1):
            print(f"Attempt {attempt}: Trying to wake up the database...")
            try:
                dummy_df = self.spark.read.jdbc(
                    url=self.jdbc_url,
                    table="(SELECT 1 AS check_value) AS dummy_table",
                    properties=self.conn_props
                )
                if dummy_df.count() > 0:
                    print("Database is awake and ready.")
                    success = True
                    break
            except Exception as e:
                print(f"Attempt {attempt} failed: {e}")
            time.sleep(self.sleep_seconds)

        if not success:
            raise Exception(
                f"Failed to wake up the database after {self.max_attempts} attempts."
            )

jdbc_url = dbutils.secrets.get(scope="Capstone", key="DatabasejdbcUrl")
connection_properties = {
    "user": dbutils.secrets.get(scope="Capstone", key="DatabaseUsername"),
    "password": dbutils.secrets.get(scope="Capstone", key="DatabasePassword"),
    "driver": dbutils.secrets.get(scope="Capstone", key="DatabaseDriver"),
}

checker = DatabaseWakeupChecker(spark, jdbc_url, connection_properties, max_attempts=5, sleep_seconds=1)
checker.run()