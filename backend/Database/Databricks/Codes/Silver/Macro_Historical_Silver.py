from pyspark.sql.functions import last, sequence, to_date
from pyspark.sql.window import Window
from datetime import datetime
from fredapi import Fred
import pandas as pd


class MacroHistoricalETL:
    def __init__(
        self,
        spark: SparkSession,
        jdbc_url: str,
        connection_properties: dict,
        api_key: str,
        indicators: dict,
        start: str = "2010-01-01",
        end: str = None,
    ):
        self.spark = spark
        self.jdbc_url = jdbc_url
        self.conn_props = connection_properties
        self.fred = Fred(api_key=api_key)
        self.indicators = indicators
        self.start = start
        self.end = end or datetime.today().strftime("%Y-%m-%d")

    def fetch_indicator(self, name: str, series_id: str):
        data = self.fred.get_series(
            series_id,
            observation_start=self.start,
            observation_end=self.end,
        )
        pdf = pd.DataFrame({
            "date": data.index,
            f"{name}_value": data.values,
        })
        return self.spark.createDataFrame(pdf)

    def fetch_all(self):
        return {name: self.fetch_indicator(name, sid) for name, sid in self.indicators.items()}

    def fill_and_align(self, dfs: dict):
        ranges = [df.selectExpr("min(date)", "max(date)").first() for df in dfs.values()]
        min_date = min(r[0] for r in ranges)
        max_date = max(r[1] for r in ranges)

        date_df = self.spark.sql(
            f"SELECT explode(sequence(to_date('{min_date}'), to_date('{max_date}'), interval 1 day)) AS date"
        )

        aligned = {}
        for name, df in dfs.items():
            tmp = date_df.join(df, "date", "left")
            win = Window.orderBy("date").rowsBetween(Window.unboundedPreceding, 0)
            for c in tmp.columns:
                if c != "date":
                    tmp = tmp.withColumn(c, last(c, True).over(win))
            aligned[name] = tmp
        return aligned

    def join_and_write(self, aligned: dict):
        iterator = iter(aligned.values())
        joined = next(iterator)
        for df in iterator:
            joined = joined.join(df, ["date"], "inner")

        joined.write \
            .format("jdbc") \
            .option("url", self.jdbc_url) \
            .option("dbtable", "Silver.Macro_Historical") \
            .option("user", self.conn_props["user"]) \
            .option("password", self.conn_props["password"]) \
            .option("driver", self.conn_props["driver"]) \
            .mode("overwrite") \
            .option("batchsize", 10000) \
            .option("numPartitions", 8) \
            .save()
        print("Data successfully written to Azure SQL Database.")

    def run(self):
        dfs = self.fetch_all()
        aligned = self.fill_and_align(dfs)
        self.join_and_write(aligned)

jdbc_url = dbutils.secrets.get(scope="Capstone", key="DatabasejdbcUrl")
connection_properties = {
    "user": dbutils.secrets.get(scope="Capstone", key="DatabaseUsername"),
    "password": dbutils.secrets.get(scope="Capstone", key="DatabasePassword"),
    "driver": dbutils.secrets.get(scope="Capstone", key="DatabaseDriver"),
}
api_key = dbutils.secrets.get(scope="Capstone", key="FredAPIKey")


macro_indicators = {
    "gdp": "GDP",
    "real_gdp": "GDPC1",
    "ferfed_funds_effective_rate": "FEDFUNDS",
    "labor_force_participant_rate": "CIVPART",
    "cpi": "CPIAUCSL",
    "unemployment": "UNRATE",
    "interest_rate": "FEDFUNDS",
    "job_openning_non_farm" : "JTSJOL",
    "hires_total_non_farm" : "JTSHIL",
    "quit_total_non_farm" : "JTSQUR",
    "layoff_discharge_non_farm" : "JTSLDL",
    "layoffs_and_discharges_professional_and_business_services" : "JTU540099LDL",
    "layoffs_and_discharges_manufacturing" : "JTU3000LDL",
    "layoffs_and_discharges_fiance_and_insurance" : "JTU5200LDL",
    "layoffs_and_discharges_construction" : "JTU2300LDL",
    "layoffs_and_discharges_total_private" : "JTS1000LDL",
    "layoffs_and_discharges_retail_trade" : "JTU4400LDL",
    "layoffs_and_discharges_real_estate_and_rental_and_leasing" :"JTU5300LDL",
    "layoffs_and_discharges_accommodation_and_food_services" : "JTU7200LDL",
    "real_estate_loans_all_commercial_bank" : "CREACBM027NBOG",
    "commercial_real_estate_prices_for_US_rate" : "COMREPUSQ159N"
}

etl = MacroHistoricalETL(
    spark, jdbc_url, connection_properties, api_key, macro_indicators, start="2010-01-01"
)
etl.run()



