# Review checkpoint — nids-ucsdnt-expanse (agent-facing)

Resume state for a content + URL review of this module. Read this instead of re-deriving.
Human-facing decisions live in [review-summary.md](review-summary.md).

## 1. State

- **Review complete. Zero fixes applied.** No file in this repo was modified.
- Working tree clean at `e9c0637` ("added slides"), branch `main`.
- 14 tracked files reviewed in full: 9 `.md`, 2 `.ipynb`, `ir_traffic_batch.py`,
  `run_ir_traffic.slurm`, `slides/ETP-Week-07-expanse.pptx`.
- 18 findings below. 3 are blocking, 1 needs an Expanse run to settle.

## 2. Already verified — do not redo

**All links are clean.** Both checks were run and passed:

```bash
# 111 relative [..](..) targets across 9 .md + 2 .ipynb — 0 broken
python3 -c "
import re,os,json,glob
t=set()
def scan(n,x):
    for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)',x):
        l=m.group(2)
        if not l.startswith(('http','#','mailto')): t.add((n,l))
for f in glob.glob('*.md'): scan(f,open(f).read())
for f in ['ir_traffic_prototype.ipynb','analysis.ipynb']:
    scan(f,'\n'.join(''.join(c['source']) for c in json.load(open(f))['cells']))
print([x for x in sorted(t) if not os.path.exists(x[1].split('#')[0])] or 'none')"

# 9 external URLs — all 200
grep -roE 'https?://[^ )\"'\''\`>,;]+' --include='*.md' --include='*.py' \
  --include='*.ipynb' --include='*.slurm' . | sed 's/[.,]*$//' | sort -u
```

Established facts, all confirmed correct — **these are not defects**:

| Claim | Status |
|---|---|
| 111 relative links | 0 broken, incl. every nav bar and `slides/ETP-Week-07-expanse.pptx` |
| 9 external URLs | all HTTP 200 |
| `en.wikipedia.org/wiki/2026_Internet_blackout_in_Iran` | real standard article, not a redirect (checked via REST summary API) |
| `github.com/CAIDA/nids-expanse-2026/tree/main/3_running_batch_job` | 200, tree path exists |
| `https://hermes.caida.org` root → 404 | **expected** for an S3 API endpoint with no bucket/key; it is a config value, not a hyperlink |
| 2026-02-10 → 2026-03-05 | 24 days inclusive; `+23d` lands exactly on 2026-03-05; matches `--array=0-23`. 2026 is not a leap year |
| `time` example `1771027200` | = 2026-02-14 00:00 UTC, matches first test day — correct |
| Task 3 window `normalize()` → `+55min` | 12 five-minute files, matches "12 files" in the docs |
| Q5's "Iran's local time (UTC+3:30)" | correct; Iran abolished DST in 2022, IRST is UTC+3:30 year-round |

## 3. Settled decisions — do not re-litigate

1. **`.ucsdnts3.env` → per-student path.** `/expanse/lustre/projects/{PROJECT}/{USER}/.ucsdnts3.env`,
   matching [run_ir_traffic.slurm:40](run_ir_traffic.slurm#L40). Datasets.md documents how the
   copy is placed there.
2. **Scope = docs + notebooks + slurm.** Notebook edits stay minimal and touch no
   `# YOUR CODE HERE` block.
3. **00:00 UTC sampling stays.** No behavior change; it gets documented instead (F8, F9).

## 4. Findings

### Blocking — a student hits these

| # | Location | Defect | Fix |
|---|---|---|---|
| **B1** | [run_ir_traffic.slurm:12](run_ir_traffic.slurm#L12) | `#SBATCH --output="joblogs/slurm-%A_%a.out"` but `joblogs/` is untracked (`git ls-files` confirms) and absent from a fresh clone. Slurm opens the output file at task start, **before** the script body runs, so the `mkdir -p joblogs` at line 30 is too late. All 24 tasks fail with no log saying why. | Add tracked `joblogs/.gitkeep`; add explicit `mkdir -p joblogs` pre-`sbatch` step to [Tasks.md:30](Tasks.md#L30); leave line 30 as belt-and-braces. |
| **B2** | `ir_traffic_prototype.ipynb` cell 3, `analysis.ipynb` cell 3 | Both hardcode `%dotenv /expanse/lustre/projects/sdp178/kmok/.ucsdnts3.env` — a path into another user's directory. Three competing locations exist repo-wide: this, [run_ir_traffic.slurm:40](run_ir_traffic.slurm#L40) `${USERPROJ_DIR}/.ucsdnts3.env`, and [Datasets.md:15](Datasets.md#L15) "preloaded via `.bashrc`". | Both → `%dotenv /expanse/lustre/projects/{PROJECT}/{USER}/.ucsdnts3.env` using the existing cell vars. `analysis.ipynb` never touches S3 — drop its `%load_ext dotenv` + `%dotenv` entirely, keep `USER`/`PROJECT`. |
| **B3** | [run_ir_traffic.slurm:4](run_ir_traffic.slurm#L4), [:21](run_ir_traffic.slurm#L21) | `#SBATCH --account=sdp178` hardcoded while lines 22-23 use `${ETP26_ACCOUNT}`. `REPO_DIR=/home/${USER}/nids-ucsdnt-expanse` assumes clone location. [Tasks.md:30](Tasks.md#L30) and [Task-3-batch-job.md:57](Task-3-batch-job.md#L57) both claim the mail line is *the only* edit needed — false. | Line 4 → `YOUR_ACCOUNT_HERE` + document `sbatch --account=$ETP26_ACCOUNT` override (see §5). Line 21 → `REPO_DIR=${SLURM_SUBMIT_DIR}`. Correct the "only line" claim in both docs. |

### Docs contradict code

| # | Location | Defect | Fix |
|---|---|---|---|
| **F4** | [Datasets.md](Datasets.md) output table | Lists `ir_daily_summary_<date>.parquet` / `ir_src_asn_<date>.parquet` / `ir_asn_daily_packets_<date>.parquet` as "Produced by Tasks 1 & 3". The prototype writes five `*_test.parquet` files (cells 17, 23, 25, 27); only the batch script writes `*_<date>.parquet`. `analysis.ipynb` Part A reads the `_test` names, confirming. | Split into a prototype block (5 `*_test.parquet`) and a batch block (3 `*_<date>.parquet`), each with correct columns. |
| **F5** | prototype cells 21 → 27 | Cell 21 mutates in place (`ir_src_asn_df['subnet_24'] = ...`); cell 27 writes afterwards, so `ir_src_asn_test.parquet` ships 4 columns, not the 3 Datasets.md documents. | Cell 27 → `ir_src_asn_df[['date','src_ip','prefix2asn']].to_parquet(...)`. Safe: Part A re-derives `subnet_24` from `src_ip`. |
| **F6** | [Datasets.md:44](Datasets.md#L44), [Introduction.md](Introduction.md) | Batch job samples only the 00:00 UTC hour, but Datasets.md says combined files cover "all of 2026-02-10 to 2026-03-05" and Introduction.md never mentions sampling. Only Tasks.md and Task-3 guide do. Students compare full-day test numbers to 1-hour full-period numbers and see an unexplained order-of-magnitude gap. | Fix the Datasets.md wording; add the caveat to Introduction.md's "From Prototype to Batch Job". |
| **F7** | `analysis.ipynb` cells 17, 20 | Plot titled "Daily inbound telescope traffic" with no sampling caveat. | Note in titles/markdown that Part B is a 00:00 UTC hourly sample. |
| **F8** | pedagogical, spans Q5/Q6 | 00:00 UTC = **03:30 IRST**, the diurnal trough. Q5 has students find the diurnal pattern; Q6 has them detect a blackout from a sample taken at that trough every day. Defensible but never stated. | State it explicitly near Q6. Human decision — see [review-summary.md](review-summary.md). |
| **F9** | prototype cell 15 | Loop ends with `del spark_df, ir_df, src_asn_rows, asn_rows, hourly_rows` — **outside** `# YOUR CODE HERE`, so it `NameError`s unless the student picks those exact five names. The 9 inline TODO steps never name them; [Task-1-aggregate-daily-traffic.md](Task-1-aggregate-daily-traffic.md) shows only `spark_df` and `ir_df`. | Name all five in cell 15's TODO steps and the Task 1 guide. Naming hint, not a solution. |
| **F10** | `analysis.ipynb` cell 15 | Three `to_parquet('ir_*_full.parquet')` calls use bare relative paths → notebook CWD → the clone. Contradicts [Datasets.md:34](Datasets.md#L34) ("Lustre, rather than the home directory"). No `.gitignore` exists; README step 9 tells students to commit and push. | Add `FULL_OUTPUT_DIR = f'/expanse/lustre/projects/{PROJECT}/{USER}/output/full'` + `os.makedirs`. Add `.gitignore`: `*.parquet`, `joblogs/`, `.ipynb_checkpoints/`. |

### Polish

| # | Location | Fix |
|---|---|---|
| P11 | [Tasks.md:11](Tasks.md#L11) | Promises `ETP26_ACCOUNT` is documented in Datasets.md. It is not — Credentials covers only the two S3 keys. Add it. |
| P12 | [README.md:53](README.md#L53) | Backscatter mislabeled: the parenthetical defines *all* unsolicited traffic as "backscatter", then the next sentence correctly lists it as one of four categories alongside scanning, misconfiguration, spoofed-source attacks. Drop the parenthetical. |
| P13 | [Introduction.md:22](Introduction.md#L22), [:43](Introduction.md#L43) | "backout" → "blackout"; "disappearence" → "disappearance". |
| P14 | [PySpark-Parquet.md:19](PySpark-Parquet.md#L19) | Imprecision, not a flat error: the passage describes this module as running `local[*]`, but the prototype pins `local[{n_cores}]` from `SLURM_CPUS_PER_TASK` (cell 9) and the batch script defaults to `local[*]` only when `--cores` is absent ([ir_traffic_batch.py:175](ir_traffic_batch.py#L175)) — the Slurm script always passes it. The `local[*]`-vs-cluster point being made is still correct. Reword to "local mode" or note the pinned core count. Lowest priority item here. |
| P15 | [README.md:57](README.md#L57) | Glossary entry titled `netacq_country` (singular) but describes two fields. Name `maxmind_country`, matching [Introduction.md:41](Introduction.md#L41) and `--geo-field` choices in [ir_traffic_batch.py:111](ir_traffic_batch.py#L111). |
| P16 | [Datasets.md](Datasets.md) field table | `src_ip 3229923820` decodes to `192.132.185.236`; `prefix2asn 1756` — neither Iranian, in a row whose `netacq_country` is `IR`. Human decision — see summary. |
| P17 | [Tasks.md:34](Tasks.md#L34), [Task-3-batch-job.md:61](Task-3-batch-job.md#L61), prototype cell 29 | Q3 grammar, **duplicated verbatim in 3 places**: "It used array of jobs (one per day)" → "It uses a job array (one task per day)". |
| P18 | [README.md:34-49](README.md#L34-L49) | Tree lists `joblogs/` but omits `slides/`, linked two sections earlier. Add `slides/`; mark `joblogs/` as created at submit time. |

### Needs an Expanse run

**T19** — Cannot be settled from here. `spark-avro_2.13:4.2.0` is pinned against
`hadoop-aws:3.5.0` ([ir_traffic_batch.py:179](ir_traffic_batch.py#L179), prototype cell 9);
`hadoop-aws` must match the Hadoop version bundled in the container's Spark build or S3A fails
with `NoSuchMethodError`. Separately, `--mem-per-cpu=4000 × 4 = ~15.6 GiB` cgroup vs.
`--memory 12g` heap leaves ~3.6 GiB for JVM metaspace/off-heap plus container — tight.

## 5. Sequencing and coupling

- **P17 is a 3-way duplicate.** The same Q3 sentence appears in Tasks.md, Task-3-batch-job.md,
  and prototype cell 29. Fix all three in one pass or they drift. Q1/Q2/Q4/Q5/Q6 are likewise
  duplicated across Tasks.md, the task guides, and the notebooks — check every question edit
  against all copies.
- **F4 before F5.** Split the Datasets.md output table first; the `subnet_24` column fix only
  makes sense once the table distinguishes prototype `_test` files from batch `_<date>` files.
- **`#SBATCH` lines do not expand shell variables.** They are parsed by Slurm before the shell
  runs, so `--account=${ETP26_ACCOUNT}` silently cannot work. This is why B3 needs either a
  literal placeholder or the `sbatch --account=$ETP26_ACCOUNT` command-line override.
- **B1 and F10 both feed `.gitignore`.** Adding `joblogs/.gitkeep` while gitignoring `joblogs/`
  requires the negation to be right — `joblogs/*` + `!joblogs/.gitkeep`, not `joblogs/`.
- **F9 touches a cell adjacent to student code.** Edit only the TODO comment block; the `del`
  line and everything after it stays as-is.

## 6. Verification

1. **Fresh clone** — `joblogs/` present; `grep -rn 'sdp178\|kmok' .` returns nothing.
2. **Slurm launch** (the silently-broken one) — `sbatch --account=$ETP26_ACCOUNT run_ir_traffic.slurm`
   from repo root on a login node; confirm `joblogs/slurm-<A>_<a>.out` appears for all 24 tasks
   and none fail at launch.
3. **Re-run both link checks** from §2 — all relative targets resolve, all external URLs 200.
4. **Prototype end to end** with a reference solution — the five `*_test.parquet` files and
   their columns match the corrected Datasets.md table, specifically `ir_src_asn_test.parquet`
   having exactly 3 columns. Then run `analysis.ipynb` Part A against them.
5. **`git status` after a full student run** — no Parquet, `joblogs/`, or `.ipynb_checkpoints/`
   showing as untracked-and-committable.

## 7. Open — needs a human

Five decisions are parked in [review-summary.md](review-summary.md) §4: the account line
mechanism, the 03:30 IRST sampling question, combined-Parquet destination + `.gitignore`,
the Datasets.md example values (P16), and whether naming the five `del` variables (F9) narrows
student freedom too much. **Do not apply B3, F8, F10, P16, or F9 before those are answered.**
Everything else in §4 is unblocked.
