README ⮕ | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)

### Network Infrastructure Data Science (NIDS) Module

---

# Measuring Internet Disruptions with the UCSD Network Telescope

## Learning Objectives

The goal of this assignment is to understand how a **network telescope (darknet)** passively observes unsolicited Internet traffic, how to use **PySpark** to filter and aggregate large-scale FlowTuple flow records read directly from S3-hosted Avro files on an HPC cluster, how to attribute that traffic to a source country and origin AS, how to scale an interactive prototype into a **Slurm batch job array** to cover a much longer time period, and how to detect and interpret a real anomaly — a national Internet blackout — in the resulting time series. This assignment builds on the ASN concepts introduced in _nids-asn-introduction_, the PySpark fundamentals from _nids-dns-ecosystem_, and the network-flow concepts from _nids-telescope-traffic_.

## Slides

- [ETP week 07 UCSD Telescope](slides/ETP-Week-07-expanse.pptx)

## Overview

Start by reading **Introduction** to get the background needed to understand the assignment. **Datasets** explains each dataset and how to access it.

- step 1 [read the introduction](Introduction.md)
- step 2 [read dataset overviews](Datasets.md)
- step 3 [review the tasks](Tasks.md)
- step 4 get access to SDSC Expanse and launch an interactive Jupyter session (see [Datasets](Datasets.md) for credentials)
- step 5 complete `ir_traffic_prototype.ipynb` (Tasks 1 and 2)
  - complete each task by replacing the `# YOUR CODE HERE` sections
- step 6 complete `ir_traffic_batch.py` and submit `run_ir_traffic.slurm` covering 2026-02-10 to 2026-03-05 (Task 3)
- step 7 once the batch job finishes, complete `analysis.ipynb` (Task 4)
- step 8 answer all six questions across the two notebooks' markdown cells
- step 9 download your completed notebooks and scripts, commit, and push to GitHub ⬅ deliverables

### Directory Structure

```
nids-ucsdnt-expanse
├- Introduction.md                          # Introduction and background
├- Datasets.md                              # Dataset overview and access instructions
├- PySpark-Parquet.md                       # PySpark/Parquet delta guide (assumes nids-dns-ecosystem's Spark.md)
├- Tasks.md                                 # Task checklist and instructions
├- Task-1-aggregate-daily-traffic.md        # Guidance for Task 1's Spark aggregation loop
├- Task-2-daily-churn.md                    # Guidance for Task 2's /24 churn set-difference logic
├- Task-3-batch-job.md                      # Guidance for Task 3's prototype-to-batch port
├- Task-4-full-period-analysis.md           # Guidance for Task 4's pandas analysis
├- ir_traffic_prototype.ipynb           ⬅  # Complete Tasks 1 & 2 / Commit / Push
├- ir_traffic_batch.py                  ⬅  # Complete Task 3 / Commit / Push
├- run_ir_traffic.slurm                     # Provided Slurm job array for Task 3 - edit the mail-notification line, see Tasks.md
├- joblogs/                                 # Slurm job array logs land here
└- analysis.ipynb                       ⬅  # Complete Task 4 / Commit / Push
```

### Glossary

- **Network Telescope (Darknet)**: A block of globally routed but otherwise unused IP address space, monitored for unsolicited incoming traffic ("backscatter"). Because no legitimate service listens there, essentially all traffic arriving is a byproduct of scanning, misconfiguration, spoofed-source attacks, or backscatter from elsewhere on the Internet - making it a useful passive sensor for Internet-wide events.
- **FlowTuple**: The UCSD Network Telescope's flow-level record format. Each record summarizes traffic sharing a common tuple of fields (e.g. source/destination address, ports, protocol) over a short collection interval.
- **Avro**: A compact, row-oriented binary file format used to store FlowTuple records. Unlike Parquet, Avro has no column or predicate pushdown, so a whole file must be decoded before any filter (like a country match) can drop non-matching rows.
- **PySpark / Spark**: The distributed data-processing engine used in this module (in `local[*]` mode) to filter and aggregate a day's ~288 FlowTuple Avro files without loading them all into pandas memory at once.
- **Geolocation (`netacq_country`)**: Commercial IP geolocation databases, each mapping a source IP to a country. Used here to attribute observed traffic to Iran (IR); kept as two fields so one can be cross-checked against the other.
- **`prefix2asn`**: The origin ASN attributed to the prefix that covers a given source IP, same concept as in _nids-asn-introduction_.
- **`/24` subnet**: Shorthand for a block of 256 consecutive IPv4 addresses (`a.b.c.0/24`). Used in this module as a coarser unit than a single IP address to measure address-space churn without over-counting dynamically reassigned individual addresses.
- **Slurm job array**: A single batch-job submission that runs many near-identical tasks - here, one per day - in parallel/queued fashion on an HPC cluster, each task indexed by `SLURM_ARRAY_TASK_ID`.
- **Expanse**: SDSC's HPC cluster, used here to run both the interactive Jupyter session (for the prototype notebook) and the Slurm batch job array (for the full period).
- **Drop day**: A day whose observed traffic falls sharply relative to a recent baseline (e.g. the previous day) - used in Task 4 as a simple anomaly-detection heuristic, then checked against a real-world event.

README ⮕ | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [PySpark & Parquet](PySpark-Parquet.md) | [Tasks](Tasks.md) | [Task 1](Task-1-aggregate-daily-traffic.md) | [Task 2](Task-2-daily-churn.md) | [Task 3](Task-3-batch-job.md) | [Task 4](Task-4-full-period-analysis.md) | [Prototype Notebook](ir_traffic_prototype.ipynb) | [Analysis Notebook](analysis.ipynb)
