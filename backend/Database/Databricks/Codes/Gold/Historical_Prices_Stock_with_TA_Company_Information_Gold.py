from pyspark.sql import SparkSession
from pyspark.sql.functions import col, substring, to_date


class HistoricalPricesETL:
    def __init__(self, spark: SparkSession, jdbc_url: str, connection_properties: dict):
        self.spark = spark
        self.jdbc_url = jdbc_url
        self.connection_properties = connection_properties

    def run(self):
        prices_df = self.spark.read.jdbc(
            url=self.jdbc_url,
            table="Silver.Historical_Prices",
            properties=self.connection_properties
        )
        ta_df = self.spark.read.jdbc(
            url=self.jdbc_url,
            table="Silver.Historical_Prices_TA",
            properties=self.connection_properties
        )
        info_df = self.spark.read.jdbc(
            url=self.jdbc_url,
            table="Silver.Company_Information",
            properties=self.connection_properties
        )

        prices_df = prices_df.withColumn(
            "Date",
            to_date(substring(col("Date"), 1, 10))
        )

        joined_df = prices_df.join(
            ta_df,
            on=["Stock_Symbol", "Date", "Close"],
            how="inner"
        )

        info_df = info_df.withColumnRenamed(
            "symbol", "Stock_Symbol"
        )

        enriched_df = joined_df.join(
            info_df,
            on=["Stock_Symbol"],
            how="left"
        )

        enriched_df.write \
            .format("jdbc") \
            .option("url", self.jdbc_url) \
            .option("dbtable", "Gold.Historical_Prices_Stock_with_TA_Company_Information") \
            .option("user", self.connection_properties["user"]) \
            .option("password", self.connection_properties["password"]) \
            .option("driver", self.connection_properties["driver"]) \
            .mode("overwrite") \
            .option("batchsize", 10000) \
            .option("numPartitions", 8) \
            .save()

        print("Data successfully written to Azure SQL Database.")

jdbc_url = dbutils.secrets.get(scope="Capstone", key="DatabasejdbcUrl")
connection_properties = {
    "user": dbutils.secrets.get(scope="Capstone", key="DatabaseUsername"),
    "password": dbutils.secrets.get(scope="Capstone", key="DatabasePassword"),
    "driver": dbutils.secrets.get(scope="Capstone", key="DatabaseDriver")
}

etl = HistoricalPricesETL(spark, jdbc_url, connection_properties)
etl.run()