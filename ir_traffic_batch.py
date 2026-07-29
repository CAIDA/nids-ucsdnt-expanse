"""Batch job version of ir_traffic_prototype.ipynb (Task 3).

For a single day, lists UCSD Network Telescope FlowTuple Avro files on S3, loads
the 00:00 UTC hour (12 five-minute files, sampled rather than the full day) into
Spark, filters to source IPs geolocated to a target country (Iran, IR, by
default), and writes three Parquet files for that day:

  - ir_daily_summary_<date>.parquet     - one row: date, total packets, unique
    source IPs, unique source ASNs seen from that country on that day.
  - ir_src_asn_<date>.parquet           - the distinct (source IP, source ASN)
    pairs geolocated to that country on that day.
  - ir_asn_daily_packets_<date>.parquet - the total packets contributed by each
    ASN geolocated to that country on that day.

Intended to be run once per day via the Slurm job array in run_ir_traffic.slurm,
so that the full 2026-02-10 to 2026-03-05 period can be covered without holding
an interactive notebook session open for hours.

This is the same per-day logic as Task 1 in ir_traffic_prototype.ipynb - port
your working solution from there into the `# YOUR CODE HERE` section below.
"""

import argparse
import os
import socket
import struct

import boto3
from botocore.config import Config
import pandas as pd

import findspark
findspark.init()

import pyspark
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import pyspark.sql.types as pst


# --- Handy IP helper functions ---

def long2ip(long):
    """Convert an integer IPv4 value back to dotted-quad string."""
    return socket.inet_ntoa(struct.pack('!L', long))


# --- Functions to facilitate the loading of FlowTuple files ---

def load_ft_pyspark(spark, avro_files):
    df = spark.read.format('avro').load(avro_files)
    df = df.withColumn('time', F.to_utc_timestamp((df.time).cast(dataType=pst.TimestampType()), 'UTC'))
    return df


def time_to_avro_list(s3_objects_df, s3_bucket, start_time, end_time):
    """Returns a list of S3 paths to Avro files that fall within the specified time range."""
    start_time = pd.Timestamp(start_time)
    end_time = pd.Timestamp(end_time)

    if start_time.tzinfo is None:
        start_time = start_time.tz_localize("UTC")
    if end_time.tzinfo is None:
        end_time = end_time.tz_localize("UTC")

    mask = (s3_objects_df["datetime"] >= start_time) & (s3_objects_df["datetime"] <= end_time)
    keys = s3_objects_df.loc[mask, "Key"].tolist()
    return [f"s3a://{s3_bucket}/{key}" for key in keys]


def list_avro_objects(s3_endpoint_url, s3_bucket, prefix, access_key, secret_key):
    """List available FlowTuple files for a given year/month/day prefix."""
    s3 = boto3.client(
        "s3",
        endpoint_url=s3_endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )

    paginator = s3.get_paginator("list_objects")
    objects = []
    for page in paginator.paginate(Bucket=s3_bucket, Prefix=prefix):
        objects.extend(page.get("Contents", []))

    s3_objects_df = pd.DataFrame(objects, columns=["Key", "Size"])
    s3_objects_df["unix_time"] = s3_objects_df["Key"].str.extract(r"\.(\d+)\.flowtuple-v4\.avro$")[0].astype("int64")
    s3_objects_df["datetime"] = pd.to_datetime(s3_objects_df["unix_time"], unit="s", utc=True)
    return s3_objects_df


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate the 00:00 UTC hour (sampled per day) of UCSD NT FlowTuple traffic "
            "geolocated to a target country."
        )
    )
    parser.add_argument(
        "--date", required=True,
        help="Day to process, in YYYY-MM-DD format (UTC day, e.g. 2026-02-10).",
    )
    parser.add_argument(
        "--output-dir", "-o", default="./output",
        help=(
            "Directory to write ir_daily_summary_<date>.parquet, ir_src_asn_<date>.parquet, "
            "and ir_asn_daily_packets_<date>.parquet to (default: ./output)"
        ),
    )
    parser.add_argument(
        "--geo-field", default="netacq_country", choices=["netacq_country", "maxmind_country"],
        help="Which geolocation field to filter source IPs on (default: netacq_country).",
    )
    parser.add_argument(
        "--country", default="IR",
        help="ISO country code to filter source IPs on (default: IR, Iran).",
    )
    parser.add_argument(
        "--cores", type=int, default=None,
        help="Number of local Spark cores to use (spark.master=local[N]). Defaults to all "
             "available cores (local[*]) - match this to your Slurm --cpus-per-task.",
    )
    parser.add_argument(
        "--memory", default="12g",
        help="Spark driver memory, e.g. '12g' (default: 12g). local[*] mode runs the driver "
             "and all executors in one JVM, so keep this comfortably below your Slurm "
             "--mem-per-cpu * --cpus-per-task allocation, with headroom for the container/OS.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    day = pd.to_datetime(args.date)

    # S3 credentials, same environment variables used in the interactive notebook.
    ucsd_nt_s3_access_key = os.environ["UCSD_NT_S3_ACCESS_KEY"]
    ucsd_nt_s3_secret_key = os.environ["UCSD_NT_S3_SECRET_KEY"]

    s3_endpoint_url = "https://hermes.caida.org"
    s3_bucket = "telescope-ucsdnt-avro-flowtuple-v4-2026"

    # The FlowTuple dataset partitions objects by year/month/day, so one day = one prefix.
    prefix = f"datasource=ucsd-nt/year={day.year:04d}/month={day.month:02d}/day={day.day:02d}/"

    s3_objects_df = list_avro_objects(s3_endpoint_url, s3_bucket, prefix, ucsd_nt_s3_access_key, ucsd_nt_s3_secret_key)
    print(f"[{args.date}] found {len(s3_objects_df)} FlowTuple files under {prefix}")

    if len(s3_objects_df) == 0:
        # No data for this day (e.g. gap in collection) - write empty-but-valid outputs
        # so downstream concatenation doesn't have to special-case missing days.
        pd.DataFrame([{
            "date": args.date, "total_packet_cnt": 0, "unique_src_ips": 0, "unique_asns": 0,
        }]).to_parquet(os.path.join(args.output_dir, f"ir_daily_summary_{args.date}.parquet"), index=False)
        pd.DataFrame(columns=["date", "src_ip", "prefix2asn"]).to_parquet(
            os.path.join(args.output_dir, f"ir_src_asn_{args.date}.parquet"), index=False
        )
        pd.DataFrame(columns=["date", "prefix2asn", "total_packet_cnt"]).to_parquet(
            os.path.join(args.output_dir, f"ir_asn_daily_packets_{args.date}.parquet"), index=False
        )
        return

    # PySpark setup, identical to the interactive prototype notebook.
    #
    # local[*] mode runs the driver and all "executors" in ONE JVM, and left unset
    # spark.driver.memory defaults to ~1g - far below what run_ir_traffic.slurm actually
    # requests (--cpus-per-task=4 --mem-per-cpu=4000 => ~16g). Avro has no column/predicate
    # pushdown, so the sampled hour's ~12 files must be fully decoded before the country
    # filter drops non-matching rows, which is memory-heavy regardless of filter selectivity.
    # Without this, the JVM gets OOM-killed mid-job (surfaces as "SparkContext was shut down" /
    # "Connection refused"), not a normal catchable Spark error. Keep this comfortably below
    # the sbatch --mem-per-cpu * --cpus-per-task total, with headroom for the container/OS.
    spark_master = f'local[{args.cores}]' if args.cores else 'local[*]'
    conf = pyspark.SparkConf().setAll([
        ('spark.master', spark_master),
        ('spark.app.name', 'IR Traffic Daily Aggregation'),
        ('spark.jars.packages', 'org.apache.spark:spark-avro_2.13:4.2.0,org.apache.hadoop:hadoop-aws:3.5.0'),
        ('spark.hadoop.fs.s3a.endpoint', s3_endpoint_url),
        ('spark.hadoop.fs.s3a.path.style.access', 'true'),
        ('spark.hadoop.fs.s3a.endpoint.region', 'us-east-1'),
        ('spark.hadoop.fs.s3a.access.key', ucsd_nt_s3_access_key),
        ('spark.hadoop.fs.s3a.secret.key', ucsd_nt_s3_secret_key),
        ('spark.hadoop.fs.s3a.aws.credentials.provider', 'org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider'),
        # hadoop-aws 3.5.0 turns on the new S3 Analytics Accelerator reader by default; its
        # background prefetch threads can throw "SocketException: Socket closed" ERROR-level
        # noise when spark.stop() tears down the S3 connection pool out from under them at the
        # end of each task. Harmless (fires after outputs are already written), but disable it
        # to avoid the noise and this still-experimental component's other rough edges.
        ('spark.hadoop.fs.s3a.analytics.accelerator.enabled', 'false'),
        ('spark.sql.execution.arrow.pyspark.enabled', 'false'),
        ('spark.driver.memory', args.memory),    # <-- keep below the sbatch mem request, see above
        ('spark.driver.maxResultSize', '4g'),
        ('spark.sql.shuffle.partitions', '32'),  # default 200 is excessive overhead for 4 local cores
    ])
    spark = SparkSession.builder.config(conf=conf).getOrCreate()

    # Port your Task 1 solution here:
    # 1. Sample just the 00:00 UTC hour of `day` (12 five-minute files) rather than the
    #    full day, using time_to_avro_list + load_ft_pyspark, to keep the full 24-day
    #    batch run's total data volume manageable.
    # 2. Filter to rows where args.geo_field matches args.country.
    # 3. Compute the daily summary (total packet count, unique source IPs, unique ASNs)
    #    and write it to ir_daily_summary_<date>.parquet under args.output_dir.
    # 4. Compute the distinct (src_ip, prefix2asn) pairs (converting src_ip with long2ip)
    #    and write them to ir_src_asn_<date>.parquet.
    # 5. Compute total packets per ASN and write them to ir_asn_daily_packets_<date>.parquet.
    #
    # Each Parquet file's rows should include a `date` column set to args.date, and each
    # DataFrame should come from a pandas conversion of a Spark aggregation (.toPandas()),
    # not a raw .collect() - see the three ir_*.to_parquet(...) calls in Task 1 for the
    # exact schemas expected by analysis.ipynb.

    # YOUR CODE HERE

    spark.stop()


if __name__ == "__main__":
    main()
