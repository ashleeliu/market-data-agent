"""Download Parquet files from S3 and load them into a local DuckDB file."""
import os, pathlib
import boto3, duckdb

BUCKET = os.environ["BUCKET"]
PREFIX = "raw/coinbase/candles_1d/"
s3 = boto3.Session(profile_name="mkt").client("s3")
pathlib.Path("data").mkdir(exist_ok=True)

for obj in s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX).get("Contents", []):
    dest = "data/" + obj["Key"].split("/")[-1]
    s3.download_file(BUCKET, obj["Key"], dest)
    print("downloaded", dest)

con = duckdb.connect("market.duckdb")
con.execute("""
    CREATE OR REPLACE TABLE candles_1d AS
    SELECT CAST(date AS DATE) AS date, product, open, high, low, close,
           volume AS volume_base, volume * close AS volume_usd
    FROM read_parquet('data/*.parquet')
""")
print(con.execute("SELECT product, COUNT(*), MIN(date), MAX(date) FROM candles_1d GROUP BY 1").fetchall())
con.close()
