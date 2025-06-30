from pyspark.sql import SparkSession
from pyspark.sql import DataFrame
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    LongType, DateType
)
from pyspark.sql.functions import lit
import yfinance as yf
import pandas as pd
from datetime import date, datetime
import time

class HistoricalPricesPipeline:
    def __init__(
        self,
        spark: SparkSession,
        sandp500_url: str,
        jdbc_url: str,
        connection_properties: dict,
        bronze_table: str = "Bronze.Historical_Prices",
        parquet_path: str = "/dbfs/FileStore/Bronze/Historical_Prices_Bronze.parquet",
        batchsize: int = 10000,
        num_partitions: int = 8,
        pause_seconds: int = 1
    ):
        self.spark = spark
        self.sandp500_url = sandp500_url
        self.jdbc_url = jdbc_url
        self.conn_props = connection_properties
        self.bronze_table = bronze_table
        self.parquet_path = parquet_path
        self.batchsize = batchsize
        self.num_partitions = num_partitions
        self.pause_seconds = pause_seconds

        self.schema = StructType([
            StructField('Open', DoubleType(), True),
            StructField('High', DoubleType(), True),
            StructField('Low', DoubleType(), True),
            StructField('Close', DoubleType(), True),
            StructField('Volume', LongType(),   True),
            StructField('Dividends', DoubleType(), True),
            StructField('Date', DateType(),   True),
            StructField('Stock_Symbol', StringType(), True),
            StructField('Stock_Splits', DoubleType(), True),
        ])

    def run(self):
        tables = pd.read_html(self.sandp500_url)
        symbols = tables[0]['Symbol'].tolist()

        old_df = self.spark.read.jdbc(
            url=self.jdbc_url,
            table=self.bronze_table,
            properties=self.conn_props
        )
        max_date = old_df.agg({'Date': 'max'}).collect()[0][0]
        start_date = max_date if isinstance(max_date, date) else max_date.date()
        end_date = date.today()

        rdd_empty = self.spark.sparkContext.emptyRDD()
        df_union = self.spark.createDataFrame(rdd_empty, schema=self.schema)

        for sym in symbols:
            try:
                hist = yf.Ticker(sym).history(start=start_date, end=end_date)
                pdf = hist.reset_index()[[
                    'Open','High','Low','Close','Volume','Dividends','Date','Stock Splits'
                ]].rename(columns={'Stock Splits':'Stock_Splits'})
                sdf = self.spark.createDataFrame(pdf)
                sdf = sdf.withColumn('Stock_Symbol', lit(sym))
                df_union = df_union.union(sdf.select(self.schema.fieldNames()))
                time.sleep(self.pause_seconds)
            except Exception as e:
                print(f"⚠️  Skipping {sym}: {e}")
                continue

        df_union.write.mode("overwrite").parquet(self.parquet_path)

        df_final = (
            self.spark.read
                .option("header", True)
                .option("inferSchema", True)
                .parquet(self.parquet_path)
        )
        (
            df_final.write
                .format("jdbc")
                .option("url", self.jdbc_url)
                .option("dbtable", self.bronze_table)
                .option("user", self.conn_props["user"])
                .option("password", self.conn_props["password"])
                .option("driver", self.conn_props["driver"])
                .mode("append")
                .option("batchsize", self.batchsize)
                .option("numPartitions", self.num_partitions)
                .save()
        )

        print("Historical prices successfully appended to Bronze.Historical_Prices")

sandp500_url = dbutils.secrets.get(scope="Capstone", key="sandp500url")
jdbc_url      = dbutils.secrets.get(scope="Capstone", key="DatabasejdbcUrl")
conn_props = {
    "user": dbutils.secrets.get(scope="Capstone", key="DatabaseUsername"),
    "password": dbutils.secrets.get(scope="Capstone", key="DatabasePassword"),
    "driver": dbutils.secrets.get(scope="Capstone", key="DatabaseDriver")
}

pipeline = HistoricalPricesPipeline(
    spark,
    sandp500_url,
    jdbc_url,
    conn_props
)
pipeline.run()
