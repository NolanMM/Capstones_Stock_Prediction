from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import lit
from datetime import datetime
import pandas as pd

class CompanyInfoSilverUpdater:
    def __init__(self, spark: SparkSession, dbutils, bronze_table: str, silver_table: str,
                 silver_csv_path: str):
        self.spark = spark
        self.dbutils = dbutils
        self.bronze_table = bronze_table
        self.silver_table = silver_table
        self.silver_csv_path = silver_csv_path

        self.jdbc_url = dbutils.secrets.get(scope="Capstone", key="DatabasejdbcUrl")
        self.connection_props = {
            "user": dbutils.secrets.get(scope="Capstone", key="DatabaseUsername"),
            "password": dbutils.secrets.get(scope="Capstone", key="DatabasePassword"),
            "driver": dbutils.secrets.get(scope="Capstone", key="DatabaseDriver")
        }

    def read_bronze(self) -> DataFrame:
        return (
            self.spark.read
            .jdbc(url=self.jdbc_url, table=self.bronze_table, properties=self.connection_props)
        )

    def clean(self, df: DataFrame) -> DataFrame:
        today = datetime.today().date()
        return (
            df.dropDuplicates()
              .fillna(0)
              .withColumn("updated_date", lit(today))
        )

    def to_csv(self, df: DataFrame):
        pdf = df.toPandas()
        pdf.to_csv(self.silver_csv_path, index=False)

    def read_csv(self) -> DataFrame:
        return (
            self.spark.read
            .option("header", True)
            .option("inferSchema", True)
            .csv(self.silver_csv_path)
        )

    def write_silver(self, df: DataFrame):
        (
            df.write
              .format("jdbc")
              .option("url", self.jdbc_url)
              .option("dbtable", self.silver_table)
              .option("user", self.connection_props["user"])
              .option("password", self.connection_props["password"])
              .option("driver", self.connection_props["driver"])
              .mode("overwrite")
              .option("batchsize", 10000)
              .option("numPartitions", 8)
              .save()
        )

    def run(self):
        bronze_df = self.read_bronze()
        clean_df = self.clean(bronze_df)
        self.to_csv(clean_df)
        silver_df = self.read_csv()
        self.write_silver(silver_df)
        print("Data successfully written to Azure SQL Database.")

updater = CompanyInfoSilverUpdater(
    spark=spark,
    dbutils=dbutils,
    bronze_table="Bronze.Company_Information",
    silver_table="Silver.Company_Information",
    silver_csv_path="/dbfs/FileStore/Silver/Company_Information_Silver.csv"
)
updater.run()
