from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, TimestampType
)
from pyspark.sql.functions import (
    col, to_timestamp,
    from_utc_timestamp, date_format
)

class HistoricalStockNewsPipeline:
    def __init__(
        self,
        spark: SparkSession,
        jdbc_url: str,
        connection_properties: dict,
        bronze_table: str = "Bronze.Historical_Stock_News",
        silver_csv_path: str = "/dbfs/FileStore/Silver/Historical_Stock_News_Silver.csv",
        silver_table: str = "Silver.Historical_Stock_News",
        target_timezone: str = "America/New_York"
    ):
        self.spark = spark
        self.jdbc_url = jdbc_url
        self.conn_props = connection_properties
        self.bronze_table = bronze_table
        self.silver_csv_path = silver_csv_path
        self.silver_table = silver_table
        self.timezone = target_timezone

        self.expected_schema = StructType([
            StructField("id", IntegerType(), True),
            StructField("category", StringType(), True),
            StructField("datetime", TimestampType(), True),
            StructField("headline", StringType(), True),
            StructField("image", StringType(), True),
            StructField("related", StringType(), True),
            StructField("source", StringType(), True),
            StructField("summary", StringType(), True),
            StructField("url", StringType(), True),
            StructField("symbol", StringType(), True)
        ])

    def run(self):
        df = self.spark.read.jdbc(
            url=self.jdbc_url,
            table=self.bronze_table,
            properties=self.conn_props
        )

        missing = [f.name for f in self.expected_schema if f.name not in df.columns]
        if missing:
            raise ValueError(f"Missing columns in Bronze data: {missing}")

        for field in self.expected_schema:
            if isinstance(field.dataType, TimestampType):
                df = df.withColumn(field.name, to_timestamp(col(field.name)))
            else:
                df = df.withColumn(field.name, col(field.name).cast(field.dataType))
        df = (
            df
            .withColumn("datetime", from_utc_timestamp("datetime", self.timezone))
            .withColumn("datetime", date_format("datetime", "yyyy-MM-dd HH:mm:ss"))
        )

        df = df.fillna(
            subset=[f.name for f in self.expected_schema if isinstance(f.dataType, StringType)],
            value="None"
        )

        count = df.count()
        start_id = count + 1
        pdf = df.toPandas()
        pdf["id"] = range(start_id, start_id + count)
        pdf.to_csv(self.silver_csv_path, index=False)

        desired_order = [f.name for f in self.expected_schema]
        silver_df = (
            self.spark.read
                .option("header", True)
                .option("inferSchema", True)
                .option("multiLine", True)
                .option("escape", "\"")
                .csv(self.silver_csv_path.replace("/dbfs", ""))
                .select(desired_order)
        )

        (
            silver_df.write
                .format("jdbc")
                .option("url", self.jdbc_url)
                .option("dbtable", self.silver_table)
                .option("user", self.conn_props["user"])
                .option("password", self.conn_props["password"])
                .option("driver", self.conn_props["driver"])
                .mode("overwrite")
                .option("batchsize", 10000)
                .option("numPartitions", 8)
                .save()
        )

        print("Data successfully written to Silver table.")

jdbc_url = dbutils.secrets.get(scope="Capstone", key="DatabasejdbcUrl")
conn_props = {
    "user": dbutils.secrets.get(scope="Capstone", key="DatabaseUsername"),
    "password": dbutils.secrets.get(scope="Capstone", key="DatabasePassword"),
    "driver": dbutils.secrets.get(scope="Capstone", key="DatabaseDriver")
}

pipeline = HistoricalStockNewsPipeline(spark, jdbc_url, conn_props)
pipeline.run()
