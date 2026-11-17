"""Pull daily candles from Coinbase's free public API and save them to S3 as Parquet."""
import datetime as dt, io, os, time
import boto3, pandas as pd, requests

BUCKET = os.environ["BUCKET"]                     # e.g. ashlee-mkt-data-7k2p
PRODUCTS = ["BTC-USD", "ETH-USD", "SOL-USD"]
DAYS = 730                                        # ~2 years
URL = "https://api.exchange.coinbase.com/products/{}/candles"

def fetch(product):
    end = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    cur, rows = end - dt.timedelta(days=DAYS), []
    while cur < end:                              # API returns max 300 candles per call
        nxt = min(cur + dt.timedelta(days=299), end)
        r = requests.get(URL.format(product), timeout=30,
                         params={"granularity": 86400, "start": cur.isoformat(), "end": nxt.isoformat()},
                         headers={"User-Agent": "market-data-agent"})
        r.raise_for_status()
        rows += r.json()
        cur = nxt
        time.sleep(0.4)                           # stay under rate limits
    df = pd.DataFrame(rows, columns=["ts", "low", "high", "open", "close", "volume"])
    df = df.drop_duplicates("ts").sort_values("ts")
    df["date"] = pd.to_datetime(df["ts"], unit="s").dt.date
    df["product"] = product
    return df[["date", "product", "open", "high", "low", "close", "volume"]]

if __name__ == "__main__":
    s3 = boto3.Session(profile_name="mkt").client("s3")
    for p in PRODUCTS:
        df = fetch(p)
        buf = io.BytesIO(); df.to_parquet(buf, index=False)
        key = f"raw/coinbase/candles_1d/{p}.parquet"
        s3.put_object(Bucket=BUCKET, Key=key, Body=buf.getvalue())
        print(f"{p}: {len(df)} rows -> s3://{BUCKET}/{key}")
