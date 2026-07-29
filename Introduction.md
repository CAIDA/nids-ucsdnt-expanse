[README](README.md) | Introduction ⮕ | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)

# Introduction and Background

### Reading

- [Network telescope (Wikipedia)](https://en.wikipedia.org/wiki/Network_telescope) - background on darknets as a passive Internet-measurement technique
- [2026 Internet blackout in Iran (Wikipedia)](https://en.wikipedia.org/wiki/2026_Internet_blackout_in_Iran) - background for Task 4
- [CAIDA data catalog: telescope datasets](https://catalog.caida.org/search?query=telescope) - CAIDA's collection of network-telescope-derived datasets
- [CAIDA FlowTuple Documentation](https://www.caida.org/projects/network_telescope/docs/data/flowtuple/)

### Prerequisite NIDS Modules

- [How the Internet assigns and uses Autonomous Systems (ASes)](https://github.com/CAIDA/nids-asn-introduction)
- [nids-dns-ecosystem](https://github.com/CAIDA/nids-dns-ecosystem) - PySpark fundamentals this module builds on
- [nids-telescope-traffic](https://github.com/CAIDA/nids-telescope-traffic) - network telescope / flow concepts this module builds on

## Introduction

In _nids-asn-introduction_ you explored how ASes are organized and identified. This module uses that same ASN concept, but the traffic itself comes from a very different vantage point: instead of watching what networks *announce* they route (BGP), we watch what unsolicited traffic actually *arrives* at address space that nobody uses.

In _nids-telescope-traffic_ you experienced how to process a small sample of raw network telescope traffic and learn the concept of network flows. In this assignment, you will analyze the full network telescope data to study countrywide Internet backout events.

### FlowTuple Records

The UCSD Network Telescope's raw packet captures are pre-aggregated into **FlowTuple** records: each record summarizes traffic sharing a common tuple of fields (source/destination address, ports, protocol, etc.) over a short collection window, along with a packet count. FlowTuple files are stored in Apache **Avro** format. Each file contains 5 minutes of flow records, yielding 288 five-minute files per day.

Avro has no column or predicate pushdown the way Parquet does - the *entire* content of a file must be decoded before a filter (like "keep only rows geolocated to Iran") can drop the rows that don't match. A full day's ~288 files is too much data to comfortably load and filter with plain pandas, which is why this module uses **PySpark** running locally on an Expanse compute node: Spark can read, decode, and filter all of a day's files without ever materializing the unfiltered data as a single in-memory pandas object.

### From Prototype to Batch Job

Running Spark interactively against a whole ~24-day period, one day at a time, inside a single Jupyter kernel would tie up a shared interactive allocation for a very long time. This module follows a two-stage pattern that is common when scaling up an HPC analysis:

1. **Prototype**: in `ir_traffic_prototype.ipynb`, work out and sanity-check the per-day aggregation logic interactively against just **two test days**.
2. **Scale up**: once the logic is right, the same per-day logic runs unattended, once per day, as a **Slurm job array** - one array task per day, all 24 tasks queued (and several running concurrently) without holding an interactive session open.

You will do both: implement the per-day logic yourself in the prototype notebook (Tasks 1-2), then port that same logic into a standalone script and submit it as a Slurm job array to cover the full period (Task 3).

### Attribution: Geolocation and ASN

Each FlowTuple record carries two independent commercial geolocation fields, `netacq_country` and `maxmind_country`, either of which can map a source IP to a country - this module uses `netacq_country`. Each record also carries `prefix2asn`, the origin ASN of the prefix covering that source IP - the same origin-AS concept from _nids-asn-introduction_, just attached directly to telescope traffic instead of derived from a BGP RIB.

Beyond per-ASN traffic volume, this module also looks at address-space churn at **`/24` granularity** (256-address blocks). The IPs of users sending unsolicited traffic could be dynamically (re)assigned by the ISP. We group the source IPs by `/24` to acquire a more stable picture of the disappearence of users.


### Detecting the Drop

Once the full 24-day period is aggregated, Task 4 asks you to build a **simple anomaly-detection heuristic**: compare each day's total attributed traffic to a recent baseline (e.g. the previous day) and flag days where it falls sharply. This is deliberately simple - no statistical modeling - because the goal is not a general-purpose change-point detector, but a first-pass filter you can then check by hand against a real, independently-reported event. A drop that lines up with the reported dates of a national blackout is much more convincing evidence than the drop alone.

#### Optional Reading

- [UCSD Network Telescope (CAIDA)](https://www.caida.org/projects/network_telescope/) - background on the telescope infrastructure itself


[README](README.md) | Introduction ⮕ | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)
