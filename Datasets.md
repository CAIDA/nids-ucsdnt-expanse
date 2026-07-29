[README](README.md) | [Introduction](Introduction.md) | Datasets ⮕ | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)

# Datasets

## UCSD Network Telescope FlowTuple Records

The notebooks read **FlowTuple v4** records from the UCSD Network Telescope, stored as **Avro** files on a CAIDA S3-compatible endpoint.

- **Endpoint**: `https://hermes.caida.org`
- **Bucket**: `telescope-ucsdnt-avro-flowtuple-v4-2026`
- **Layout**: `datasource=ucsd-nt/year=YYYY/month=MM/day=DD/*.flowtuple-v4.avro` - one prefix per UTC day, with one Avro file per 5-minute collection window (~288 files/day).

### Credentials

Access requires `UCSD_NT_S3_ACCESS_KEY` / `UCSD_NT_S3_SECRET_KEY`, shared through the project directory on Expanse. These should already be preloaded in your shell via `.bashrc` + `.ucsdnts3.env` on Expanse - see your course's SDSC Expanse access instructions if you have not set this up yet.

### FlowTuple Fields Used in This Module

| Field             | Example       | Description                                                                 |
| ----------------- | ------------- | ---------------------------------------------------------------------------|
| **time**          | 1771027200    | Start of the record's collection window (Unix time, converted to UTC)      |
| **src_ip**        | 3229923820    | Source IP address, packed as a 32-bit integer                              |
| **packet_cnt**    | 4              | Number of packets observed for this record                                 |
| **prefix2asn**    | 1756           | Origin ASN of the prefix covering `src_ip`                                 |
| **netacq_country**| IR             | Source country per the Neustar/NetAcuity geolocation database              |


<br/>

## Output Parquet Files (produced by this module's own tasks)

Task 1-2 (prototype, test window) and Task 3 (batch job, full period) both write the same three per-day Parquet files, plus two extras produced only by the prototype notebook:

These files should be stored into appropriate location on Expanse Lustre, rather than the home directory. E.g., `/expanse/lustre/projects/<projid>/<userid>/output`

| File                                        | Produced by  | Columns                                              |
| -------------------------------------------- | ------------ | ----------------------------------------------------- |
| `ir_daily_summary_<date>.parquet`            | Tasks 1 & 3  | `date`, `total_packet_cnt`, `unique_src_ips`, `unique_asns` |
| `ir_src_asn_<date>.parquet`                  | Tasks 1 & 3  | `date`, `src_ip`, `prefix2asn` (distinct pairs)        |
| `ir_asn_daily_packets_<date>.parquet`        | Tasks 1 & 3  | `date`, `prefix2asn`, `total_packet_cnt`               |
| `ir_hourly_packets_test.parquet`             | Task 1 only  | `hour`, `total_packet_cnt`, `unique_asns`              |
| `ir_disappeared_subnet24_test.parquet`       | Task 2 only  | `prev_date`, `next_date`, `subnet_24`, `prefix2asn`    |

Task 4 (`analysis.ipynb`) reads the per-day files that Task 3's batch job wrote and combines them into full-period versions (`ir_daily_summary_full.parquet`, `ir_src_asn_full.parquet`, `ir_asn_daily_packets_full.parquet`) covering all of 2026-02-10 to 2026-03-05.

## Background: 2026 Internet Blackout in Iran

Task 4 asks you to correlate any traffic drop you detect against a real, independently-reported event: the **[2026 Internet blackout in Iran](https://en.wikipedia.org/wiki/2026_Internet_blackout_in_Iran)** Wikipedia article. Read it before attempting Task 4's last question - you will need its reported dates and description of the blackout's severity/scope to judge whether your measured drop is consistent with it.

[ [CAIDA UCSD Network Telescope](https://www.caida.org/projects/network_telescope/) | [CAIDA telescope datasets](https://catalog.caida.org/search?query=telescope) ]

[README](README.md) | [Introduction](Introduction.md) | Datasets ⮕ | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)
