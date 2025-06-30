from pyspark.sql.functions import to_timestamp, from_utc_timestamp, date_format
from pyspark.sql.types import StructType, StructField, FloatType, IntegerType
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pyspark.sql import SparkSession, DataFrame
import scipy.special
import pandas as pd
import torch

class HistoricalNewsSentimentUpdater:
    def __init__(self, spark: SparkSession, dbutils,
                 silver_table: str = "Silver.Historical_Stock_News",
                 gold_table: str = "Gold.Historical_Stock_News_Sentiment_Score",
                 timezone: str = "America/New_York"):
        self.spark = spark
        self.dbutils = dbutils
        self.silver_table = silver_table
        self.gold_table = gold_table
        self.timezone = timezone

        self.jdbc_url = dbutils.secrets.get(scope="Capstone", key="DatabasejdbcUrl")
        self.connection_props = {
            "user": dbutils.secrets.get(scope="Capstone", key="DatabaseUsername"),
            "password": dbutils.secrets.get(scope="Capstone", key="DatabasePassword"),
            "driver": dbutils.secrets.get(scope="Capstone", key="DatabaseDriver")
        }

        self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        self.tokenizer_kwargs = {"padding": True, "truncation": True, "max_length": 512}

    def read_table(self, table: str) -> DataFrame:
        return (
            self.spark.read
                .jdbc(url=self.jdbc_url, table=table, properties=self.connection_props)
                .orderBy("id")
        )

    def get_diff(self) -> DataFrame:
        old_df = self.read_table(self.gold_table)
        new_df = self.read_table(self.silver_table)
        diff = new_df.join(old_df, on="id", how="left_anti")
        # convert and normalize timestamp
        diff = (diff
                .withColumn("datetime", to_timestamp("datetime"))
                .withColumn("datetime", from_utc_timestamp("datetime", self.timezone))
                .withColumn("datetime", date_format("datetime", "yyyy-MM-dd HH:mm:ss")))
        return diff

    def score_sentiment(self, diff_df: DataFrame) -> DataFrame:
        pdf = diff_df.select("id", "headline").toPandas()
        ids = pdf["id"].tolist()
        texts = pdf["headline"].tolist()

        preds = []
        for idx, text in zip(ids, texts):
            with torch.no_grad():
                inputs = self.tokenizer(text, return_tensors="pt", **self.tokenizer_kwargs)
                logits = self.model(**inputs).logits
                scores = scipy.special.softmax(logits.cpu().numpy().squeeze())
                preds.append((float(scores[0]), float(scores[1]), float(scores[2]), int(idx)))

        schema = StructType([
            StructField("positive_value", FloatType(), True),
            StructField("negative_value", FloatType(), True),
            StructField("neutral_value",  FloatType(), True),
            StructField("id",            IntegerType(), True),
        ])
        return self.spark.createDataFrame(preds, schema)

    def write_back(self, scored_df: DataFrame):
        scored_df \
            .write \
            .format("jdbc") \
            .option("url", self.jdbc_url) \
            .option("dbtable", self.gold_table) \
            .option("user", self.connection_props["user"]) \
            .option("password", self.connection_props["password"]) \
            .option("driver", self.connection_props["driver"]) \
            .mode("append") \
            .option("batchsize", 10000) \
            .option("numPartitions", 8) \
            .save()

    def run(self):
        diff_df = self.get_diff()
        if diff_df.rdd.isEmpty():
            print("No new records to score.")
            return

        sentiment_df = self.score_sentiment(diff_df)
        to_append = diff_df.join(sentiment_df, on="id", how="inner").orderBy("id")
        self.write_back(to_append)
        print(f"Appended {sentiment_df.count()} sentiment-scored records to {self.gold_table}.")


updater = HistoricalNewsSentimentUpdater(spark, dbutils)
updater.run()
