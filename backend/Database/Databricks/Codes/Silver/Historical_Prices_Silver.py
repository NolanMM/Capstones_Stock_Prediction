from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, DoubleType, IntegerType,
    StringType, TimestampType, DateType, LongType
)
from pyspark.sql.functions import (
    col, to_timestamp, from_utc_timestamp, date_format,
    round, lag, when, avg, lit, abs
)
from pyspark.sql import Window

class HistoricalPricesTAPipeline:
    def __init__(
        self,
        spark: SparkSession,
        jdbc_url: str,
        connection_properties: dict,
        bronze_table: str = "Bronze.Historical_Prices",
        silver_parquet: str = "/dbfs/FileStore/Silver/Historical_Prices_Silver.parquet",
        silver_table: str = "Silver.Historical_Prices",
        ta_table: str = "Silver.Historical_Prices_TA",
        timezone: str = "America/New_York",
        periods: range = range(2, 30),
        batchsize: int = 10000,
        num_partitions: int = 8
    ):
        self.spark = spark
        self.jdbc_url = jdbc_url
        self.conn_props = connection_properties
        self.bronze_table = bronze_table
        self.silver_parquet = silver_parquet
        self.silver_table = silver_table
        self.ta_table = ta_table
        self.timezone = timezone
        self.periods = periods
        self.batchsize = batchsize
        self.num_partitions = num_partitions

        self.expected_schema = StructType([
            StructField("Open", DoubleType(),   True),
            StructField("High", DoubleType(),   True),
            StructField("Low", DoubleType(),   True),
            StructField("Close", DoubleType(),   True),
            StructField("Volume", IntegerType(),  True),
            StructField("Dividends", DoubleType(),   True),
            StructField("Stock_Symbol", StringType(),   True),
            StructField("Stock_Splits", DoubleType(),   True),
            StructField("Date", TimestampType(),True),
        ])

        self.double_cols = ["Open", "High", "Low", "Close"]

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
            dt = field.dataType
            if isinstance(dt, TimestampType):
                df = df.withColumn(field.name, to_timestamp(col(field.name)))
            else:
                df = df.withColumn(field.name, col(field.name).cast(dt))

        for c in self.double_cols:
            df = df.withColumn(c, round(col(c), 2).cast(DoubleType()))

        df = (
            df.withColumn("Date", to_timestamp("Date"))
              .withColumn("Date", from_utc_timestamp("Date", self.timezone))
              .withColumn("Date", date_format("Date", "yyyy-MM-dd HH:mm:ss"))
        )

        df = df.dropDuplicates().dropna(
            subset=["Date", "Open", "High", "Low", "Close", "Volume", "Stock_Symbol"]
        )

        df.write.mode("overwrite").parquet(self.silver_parquet)

        df_silver = (
            self.spark.read
                .option("header", True)
                .option("inferSchema", True)
                .parquet(self.silver_parquet)
        )
        (
            df_silver.write
                .format("jdbc")
                .option("url", self.jdbc_url)
                .option("dbtable", self.silver_table)
                .option("user", self.conn_props["user"])
                .option("password", self.conn_props["password"])
                .option("driver", self.conn_props["driver"])
                .mode("overwrite")
                .option("batchsize", self.batchsize)
                .option("numPartitions", self.num_partitions)
                .save()
        )

        print("✅ Silver prices written to", self.silver_table)

        # 8. Compute Technical Analysis (RSI & MARD)
        df_ta = (
            df_silver
            .orderBy("Stock_Symbol", "Date")
            .select("Stock_Symbol", "Date", "Close")
        )

        for p in self.periods:
            win = Window.partitionBy("Stock_Symbol").orderBy("Date")
            df_ta = df_ta   \
                        .withColumn(f"delta_{p}", col("Close") - lag("Close", 1).over(win))
                        .withColumn(f"gain_{p}", when(col(f"delta_{p}") > 0, col(f"delta_{p}")).otherwise(0))
                        .withColumn(f"loss_{p}", when(col(f"delta_{p}") < 0, -col(f"delta_{p}")).otherwise(0))
            
            win_avg = win.rowsBetween(-p + 1, 0)
            df_ta = df_ta \
                        .withColumn(f"avg_gain_{p}", avg(col(f"gain_{p}")).over(win_avg))
                        .withColumn(f"avg_loss_{p}", avg(col(f"loss_{p}")).over(win_avg))
                        .withColumn(f"RS_{p}",
                            when(col(f"avg_loss_{p}") == 0, lit(None))
                            .otherwise(col(f"avg_gain_{p}") / col(f"avg_loss_{p}"))
                        )
                        .withColumn(f"RSI_{p}",
                            when(col(f"RS_{p}").isNotNull(),
                                100 - (100 / (1 + col(f"RS_{p}"])))
                        ))
            win_ma = win_avg
            df_ta = df_ta   \
                    .withColumn(f"rolling_avg_{p}", avg(col("Close")).over(win_ma))
                    .withColumn(f"abs_diff_{p}", abs(col("Close") - col(f"rolling_avg_{p}")))
                    .withColumn(f"rel_diff_{p}",
                        when(col("Close") != 0, col(f"abs_diff_{p}") / col("Close")).otherwise(lit(None))
                    )
                    .withColumn(f"MARD_{p}", round(avg(col(f"rel_diff_{p}")).over(win_ma), 4))
                    .drop(f"rolling_avg_{p}", f"abs_diff_{p}", f"rel_diff_{p}")
            

        select_cols = ["Stock_Symbol", "Date"] + \
                      [f"RSI_{p}" for p in self.periods] + \
                      [f"gain_{p}" for p in self.periods] + \
                      [f"loss_{p}" for p in self.periods] + \
                      [f"MARD_{p}" for p in self.periods]

        df_result = df_ta.select(*select_cols).fillna(-99999)


        df_result.write
            .format("jdbc")
            .option("url", self.jdbc_url)
            .option("dbtable", self.ta_table)
            .option("user", self.conn_props["user"])
            .option("password", self.conn_props["password"])
            .option("driver", self.conn_props["driver"])
            .mode("overwrite")
            .option("batchsize", self.batchsize)
            .option("numPartitions", self.num_partitions)
            .save()


        print("Technical analysis written to", self.ta_table)

jdbc_url = dbutils.secrets.get(scope="Capstone", key="DatabasejdbcUrl")
conn_props = {
    "user": dbutils.secrets.get(scope="Capstone", key="DatabaseUsername"),
    "password": dbutils.secrets.get(scope="Capstone", key="DatabasePassword"),
    "driver": dbutils.secrets.get(scope="Capstone", key="DatabaseDriver")
}

pipeline = HistoricalPricesTAPipeline(spark, jdbc_url, conn_props)
pipeline.run()
