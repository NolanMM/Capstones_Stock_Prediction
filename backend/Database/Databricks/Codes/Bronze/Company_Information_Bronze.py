import pandas as pd
import requests
import time

class CompanyInfoUpdater:
    def __init__(self,
                 spark,
                 sp500_url: str,
                 jdbc_url: str,
                 connection_props: dict,
                 api_key: str,
                 bronze_csv_path: str = '/dbfs/FileStore/Bronze/Company_Information_Bronze.csv',
                 bronze_table_name: str = 'Bronze.Company_Information',
                 batch_size: int = 10000,
                 num_partitions: int = 8,
                 rate_limit: float = 0.2):

        self.spark = spark
        self.sp500_url = sp500_url
        self.jdbc_url = jdbc_url
        self.connection_props = connection_props
        self.api_key = api_key
        self.bronze_csv_path = bronze_csv_path
        self.bronze_table_name = bronze_table_name
        self.batch_size = batch_size
        self.num_partitions = num_partitions
        self.rate_limit = rate_limit

    def get_sp500_symbols(self) -> list:
        tables = pd.read_html(self.sp500_url)
        symbols = tables[0]['Symbol'].tolist()
        return symbols

    def fetch_profile_data(self, symbols: list) -> pd.DataFrame:
        all_data = []
        for symbol in symbols:
            url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={self.api_key}"
            try:
                resp = requests.get(url)
                resp.raise_for_status()
                data = resp.json()
                if data and isinstance(data, list):
                    df = pd.DataFrame(data)
                    all_data.append(df)
                    print(f"Retrieved data for {symbol}")
                else:
                    print(f"No profile data for {symbol}")
            except Exception as e:
                print(f"Error retrieving data for {symbol}: {e}")
            time.sleep(self.rate_limit)

        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            print("Profile data combined successfully.")
            return combined
        else:
            print("No data retrieved.")
            return pd.DataFrame()

    def save_to_csv(self, df: pd.DataFrame):
        df.to_csv(self.bronze_csv_path, index=False)
        print(f"Saved combined data to {self.bronze_csv_path}")

    def read_old_data(self):
        return self.spark.read.jdbc(
            url=self.jdbc_url,
            table=self.bronze_table_name,
            properties=self.connection_props
        )

    def read_new_data(self):
        return self.spark.read.csv(
            self.bronze_csv_path,
            header=True,
            inferSchema=True
        )

    def filter_new_records(self, new_df, old_df, key: str = 'symbol'):
        return new_df.join(old_df.select(key), on=key, how='left_anti')

    def combine_and_write(self):
        old_df = self.read_old_data()
        new_df = self.read_new_data()
        filtered_new = self.filter_new_records(new_df, old_df)
        combined_df = filtered_new.unionByName(old_df)
        combined_df.write \
            .format("jdbc") \
            .option("url", self.jdbc_url) \
            .option("dbtable", self.bronze_table_name) \
            .option("user", self.connection_props["user"]) \
            .option("password", self.connection_props["password"]) \
            .option("driver", self.connection_props["driver"]) \
            .mode("overwrite") \
            .option("batchsize", self.batch_size) \
            .option("numPartitions", self.num_partitions) \
            .save()
        print("Data successfully written to Azure SQL Database.")

    def run(self):
        symbols = self.get_sp500_symbols()
        profile_df = self.fetch_profile_data(symbols)
        if not profile_df.empty:
            self.save_to_csv(profile_df)
            self.combine_and_write()
        else:
            print("Skipping database update due to no profile data.")

sp500_url = dbutils.secrets.get(scope="Capstone", key="sandp500url")
jdbc_url = dbutils.secrets.get(scope="Capstone", key="DatabasejdbcUrlBackup")
connection_props = {
    "user": dbutils.secrets.get(scope="Capstone", key="DatabaseUsername"),
    "password": dbutils.secrets.get(scope="Capstone", key="DatabasePassword"),
    "driver": dbutils.secrets.get(scope="Capstone", key="DatabaseDriver")
}
api_key = dbutils.secrets.get(scope="Capstone", key="ModelingPrepAPIKey")

updater = CompanyInfoUpdater(
    spark=spark,
    sp500_url=sp500_url,
    jdbc_url=jdbc_url,
    connection_props=connection_props,
    api_key=api_key
)
updater.run()
