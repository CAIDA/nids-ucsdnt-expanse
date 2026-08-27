# Review checkpoint — nids-ucsdnt-expanse (agent-facing)

Resume state for a content + URL review of this module, cross-checked against the executed
instructor key. Read this instead of re-deriving. Human-facing decisions live in
[review-summary.md](review-summary.md).

## 1. State

- **Review complete. No student source file has been modified.** Only this file and
  [review-summary.md](review-summary.md) exist as new artifacts.
- Branch `q6-change-date` in both repos; the key branch is identical to its `main`.
- 14 tracked student files reviewed in full, plus the entire key repo.
- **Q6 is being fixed in the key first** (§3). Student-side Q6 changes are deferred until the
  key is re-run and final, so its settled wording and cell structure get copied rather than
  guessed at.

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

Established facts — **not defects**:

| Claim | Status |
|---|---|
| 111 relative links | 0 broken, incl. every nav bar and `slides/ETP-Week-07-expanse.pptx` |
| 9 external URLs | all HTTP 200 |
| `2026_Internet_blackout_in_Iran` | real standard article, not a redirect |
| `hermes.caida.org` root → 404 | **expected** for an S3 API endpoint; a config value, not a hyperlink |
| 2026-02-10 → 2026-03-05 | 24 days inclusive; `+23d` lands exactly on 03-05; matches `--array=0-23`. 2026 is not a leap year |
| `time` example `1771027200` | = 2026-02-14 00:00 UTC, matches first test day — correct |
| Q5's "Iran's local time (UTC+3:30)" | correct; Iran abolished DST in 2022 |

**Wikipedia article contents** (fetched via the API — do not re-fetch): blackout imposed
**8 Jan 2026**; relaxed 28 Jan with severe restrictions remaining; traffic down **50% as of
16 Feb**; renewed "near total" blackout **28 Feb** at **4%** of normal; **~1% by 6 March**;
partially restored 25 May.

**Key repo as ground truth** (executed against real Expanse/S3 data — do not re-derive):

- Key prototype cell 15 uses **exactly** `spark_df, ir_df, src_asn_rows, asn_rows, hourly_rows`.
- Key prototype cell 22 mutates `ir_src_asn_df` in place, cell 29 writes it → the key's
  `ir_src_asn_test.parquet` genuinely has **4** columns.
- Key batch script writes `date, src_ip, prefix2asn` (3 cols, `date` inserted at position 0).
- Key analysis writes `ir_*_full.parquet` to **CWD**, same as the student copy.
- Key prototype cell 3 has **no `%dotenv`** — the key ran as `kmok`, who had the vars in-shell.
- Key batch sampling `normalize()` → `+55min`; key Task 1 uses `hours=23, minutes=55`.
- Key's full 24-day summary table is committed as saved output; the baseline arithmetic in §3
  was recomputed from it and matches the key's written answer to the digit.

## 3. Q6 — fixed in the key, student side deferred

**The defect:** Q6 asked whether flagged drop days "fall within the blackout dates it reports."
The article reports 8 Jan – 25 May 2026; the whole study period sits inside it, so the answer is
trivially yes for all 24 days — including three `pct_change()` false positives. The key's own
answer called the comparison "close to meaningless here."

**Settled decisions:** baseline is **article-derived** (days before 28 Feb); the baseline
computation ships as **provided working code**, not a fourth student exercise; the key gets a
**full-pipeline re-run**.

**Applied to the key** (`../nids-ucsdnt-expanse-key/`, branch `q6-change-date`):

1. `analysis.ipynb` cell 25 — Q6 reworded onto the 28 Feb renewal, asking for a magnitude
   comparison against the article's 4% / 1%, which flagged days are real vs. spike rebounds,
   and how to state a result whose baseline is itself measured during a blackout.
2. `analysis.ipynb` cell 22 (new) — `pct_of_baseline_df`, expressing `unique_src_ips` /
   `unique_asns` as a percentage of the pre-28-February average.
3. `analysis.ipynb` cell 24 — per-ASN cell fixed. It ended in `.head(10)` on a frame sorted by
   `['date', 'total_packet_cnt']`, so it only ever returned the earliest flagged date
   (2026-02-14, a false positive) and **never a real drop day**. Now `.groupby('date').head(5)`.
4. `analysis.ipynb` cell 26 — Q6 answer rewritten, carrying a **VERIFY AFTER RE-RUN** banner.
5. `joblogs/.gitkeep` added; `README.md` and `todo.md` updated.

**Figures staged in the key's Q6 answer** (derived from job `52586699`'s committed output;
must be re-verified post-run): baseline **1,194.3** src IPs / **101.1** ASNs over 02-10 → 02-27;
03-01 at **2.8%** of baseline src IPs falling to **2.1%** by 03-05; ASN share 10.9% → 6.9%.
Article says 4% at renewal → ~1% by 6 Mar, so the measured value sits between the two.

**Deferred to the student repo, once the key is final** — copy, do not re-derive:
[Tasks.md:48](Tasks.md#L48), [Task-4-full-period-analysis.md:62](Task-4-full-period-analysis.md#L62),
`analysis.ipynb` cell 22 (Q6 text), cell 21 (the same `.head(10)` bug), the new baseline cell,
plus the premise text in [Introduction.md](Introduction.md) "Detecting the Drop" and
[Datasets.md:48](Datasets.md#L48).

## 4. Remaining findings

### Blocking — a student hits these

| # | Location | Defect | Fix |
|---|---|---|---|
| **B1** | [run_ir_traffic.slurm:12](run_ir_traffic.slurm#L12) | `#SBATCH --output="joblogs/slurm-%A_%a.out"` but `joblogs/` is untracked and absent from a fresh clone. Slurm opens the output file at task start, **before** the script body runs, so `mkdir -p joblogs` at line 30 is too late. All 24 tasks fail with no log saying why. **Now also a prerequisite blocking the key re-run** — already fixed in the key. | Add tracked `joblogs/.gitkeep`; add explicit `mkdir -p joblogs` pre-`sbatch` step to [Tasks.md:30](Tasks.md#L30). |
| **B2** | prototype cell 3, `analysis.ipynb` cell 3 | `%dotenv /expanse/lustre/projects/sdp178/kmok/.ucsdnts3.env` — a path into another user's directory. | Repoint to `/expanse/lustre/projects/{PROJECT}/{USER}/.ucsdnts3.env`. See K3 — keeping `%dotenv` is correct. `analysis.ipynb` never touches S3, so its dotenv cell can go entirely. |
| **B3** | [run_ir_traffic.slurm:4](run_ir_traffic.slurm#L4), [:21](run_ir_traffic.slurm#L21) | `#SBATCH --account=sdp178` hardcoded while lines 22-23 use `${ETP26_ACCOUNT}`. `REPO_DIR=/home/${USER}/nids-ucsdnt-expanse` assumes clone location. [Tasks.md:30](Tasks.md#L30) and [Task-3-batch-job.md:57](Task-3-batch-job.md#L57) claim the mail line is *the only* edit — false. | `#SBATCH` cannot expand shell vars (see §5). Document `sbatch --account=$ETP26_ACCOUNT` as the zero-edit override; `REPO_DIR=${SLURM_SUBMIT_DIR}`; correct the "only line" claim in both docs. |

### Docs contradict code

| # | Location | Defect | Fix |
|---|---|---|---|
| **F4** | [Datasets.md](Datasets.md) output table | Lists the three `<date>`-suffixed files as "Produced by Tasks 1 & 3". The prototype writes five `*_test.parquet` files; only the batch script writes `*_<date>.parquet`. Confirmed against the key. | Split into a prototype block (5 files) and a batch block (3 files). |
| **F5** | — | **FLIPPED.** The key produces the 4-column `ir_src_asn_test.parquet` too. Changing the student notebook would diverge from the key. | **Fix `Datasets.md` to document 4 columns** for the prototype file. Leave both notebooks alone. |
| **F6** | [Datasets.md:44](Datasets.md#L44), [Introduction.md](Introduction.md) | Batch job samples only the 00:00 UTC hour, but Datasets.md says the combined files cover "all of 2026-02-10 to 2026-03-05" and Introduction.md never mentions sampling. | Fix the wording; add the caveat to "From Prototype to Batch Job". |
| **F7** | `analysis.ipynb` Part B plots | Titled "Daily inbound telescope traffic" with no sampling caveat. | Note that Part B is a 00:00 UTC hourly sample. |
| **F8** | pedagogical | 00:00 UTC = **03:30 IRST**, the diurnal trough. Q5 has students find the diurnal pattern; Q6 has them detect a blackout from a sample at that trough. | State it near Q6. Partly addressed by the reworded Q6. |
| **F9** | prototype cell 15 | `del spark_df, ir_df, src_asn_rows, asn_rows, hourly_rows` sits **outside** `# YOUR CODE HERE` and `NameError`s unless the student picks those exact five names. **CONFIRMED against key** — the names come straight from it. | Name all five in cell 15's TODO steps and the Task 1 guide. No divergence risk. Unblocked. |
| **F10** | — | **FLIPPED.** The key also writes `ir_*_full.parquet` to CWD. | Leave both notebooks writing to CWD; fix [Datasets.md:34](Datasets.md#L34), whose "Lustre, rather than the home directory" claim is what the code contradicts. Add `.gitignore` — README step 9 has students commit and push. |

### Key cross-check findings

| # | Detail |
|---|---|
| **K2** | The test window is **not a clean baseline**. 2026-02-14/15 sit in the relaxed-but-restricted phase (article: traffic down 50% as of 16 Feb), and **02-14 is itself one of the five flagged drop days**. Q1 asks about "baseline background telescope traffic" stability; the key's answer caveats it as "a degraded baseline, not pre-blackout normal traffic." Add one sentence to `Introduction.md` and near Q1. |
| **K3** | **CORRECTED.** The `%dotenv` divergence is *intentional*, not a regression — the key ran as `kmok`, who had the credentials in-shell; students do not. Keep `%dotenv`; only the path is wrong (B2). |
| **K7** | `prefix2asn = 0` appears in real data (key Q1 notes it) and will show up in students' top-N rankings. Undocumented in the `Datasets.md` field table. |
| **K8** | Key Q5 cites "extending the aggregation loop's `groupBy` to also group by `prefix2asn` (**as the Task 4 guide suggests**)". [Task-4-full-period-analysis.md](Task-4-full-period-analysis.md) suggests no such thing. Add it to the guide, or the key answer is stale. |
| **K9** | Q1–Q5 are verbatim-identical across `Tasks.md`, the guides, and both notebooks. **Only Q6 drifted** — `Tasks.md` carried a shorter version than the notebooks. The Q6 rewrite is the moment to reconcile it. |
| **K10** | **RETIRED.** [Task-3-batch-job.md:20](Task-3-batch-job.md#L20)'s reference to "Task 1's `pd.Timedelta(hours=23, minutes=55)`" is accurate — the key confirms. Not an issue. |
| **K11** | Real Iranian ASNs now available from key Q4 output for the `Datasets.md` example: **197207, 58224, 44244** (top by distinct `/24`), **48551, 49556, 208137** (top by packets). |

### Polish

| # | Location | Fix |
|---|---|---|
| P11 | [Tasks.md:11](Tasks.md#L11) | Promises `ETP26_ACCOUNT` is documented in `Datasets.md`. It is not — add it. |
| P12 | [README.md:53](README.md#L53) | Backscatter mislabeled: the parenthetical defines *all* unsolicited traffic as "backscatter", then the next sentence correctly lists it as one of four categories. Drop the parenthetical. |
| P13 | [Introduction.md:22](Introduction.md#L22), [:43](Introduction.md#L43) | "backout" → "blackout"; "disappearence" → "disappearance". |
| P14 | [PySpark-Parquet.md:19](PySpark-Parquet.md#L19) | Imprecision, not an error: describes the module as running `local[*]`, but the prototype pins `local[{n_cores}]` and the Slurm script always passes `--cores`. The `local[*]`-vs-cluster point stands. Reword to "local mode". Lowest priority. |
| P15 | [README.md:57](README.md#L57) | Glossary titled `netacq_country` but describes two fields — name `maxmind_country`, matching [Introduction.md:41](Introduction.md#L41) and [ir_traffic_batch.py:111](ir_traffic_batch.py#L111). |
| P16 | [Datasets.md](Datasets.md) field table | `src_ip 3229923820` = `192.132.185.236`, `prefix2asn 1756` — neither Iranian, in a row whose `netacq_country` is `IR`. Replace using K11. |
| P17 | [Tasks.md:34](Tasks.md#L34), [Task-3-batch-job.md:61](Task-3-batch-job.md#L61), prototype cell 29 | Q3 grammar, **duplicated verbatim in 3 places**: "It used array of jobs (one per day)" → "It uses a job array (one task per day)". |
| P18 | [README.md:34-49](README.md#L34-L49) | Tree lists `joblogs/` but omits `slides/`. Add `slides/`; mark `joblogs/` as created at submit time. |

### Needs an Expanse run

**T19** — `spark-avro_2.13:4.2.0` pinned against `hadoop-aws:3.5.0`
([ir_traffic_batch.py:179](ir_traffic_batch.py#L179), prototype cell 9); `hadoop-aws` must match
the Hadoop version in the container's Spark build or S3A fails with `NoSuchMethodError`. Also
`--mem-per-cpu=4000 × 4 = ~15.6 GiB` cgroup vs. `--memory 12g` heap leaves ~3.6 GiB for JVM
metaspace/off-heap plus container. **The key's pending re-run will settle both.**

## 5. Sequencing and coupling

- **P17 is a 3-way duplicate.** Fix `Tasks.md`, `Task-3-batch-job.md`, and prototype cell 29 in
  one pass. Every question edit must be checked against all copies (see K9).
- **F4 before F5.** Split the `Datasets.md` output table first; documenting the 4th column only
  makes sense once prototype `_test` files are distinguished from batch `_<date>` files.
- **`#SBATCH` lines do not expand shell variables.** Parsed by Slurm before the shell runs, so
  `--account=${ETP26_ACCOUNT}` silently cannot work. Hence B3 needs a literal placeholder or the
  `sbatch --account=` override.
- **B1 and F10 both feed `.gitignore`.** With a tracked `joblogs/.gitkeep`, the ignore rule must
  be `joblogs/*` + `!joblogs/.gitkeep`, not `joblogs/`.
- **F9 touches a cell adjacent to student code.** Edit only the TODO comment block.
- **Student Q6 work waits on the key.** Do not re-derive its wording or cell code — copy it.

## 6. Verification

1. **Fresh clone** — `joblogs/` present; `grep -rn 'sdp178\|kmok' .` returns nothing.
2. **Slurm launch** — `sbatch --account=$ETP26_ACCOUNT run_ir_traffic.slurm` from repo root;
   all 24 tasks produce `joblogs/slurm-<A>_<a>.out` and none fail at launch.
3. **Re-run both link checks** from §2.
4. **Prototype end to end** — the five `*_test.parquet` files and their columns match the
   corrected `Datasets.md` table; then `analysis.ipynb` Part A against them.
5. **`git status` after a full student run** — no Parquet, `joblogs/`, or `.ipynb_checkpoints/`
   untracked-and-committable.
6. **Q6 parity** — once the key is final, its Q6 text and the two cells match the student copies
   verbatim.

## 7. Open — needs a human

Parked in [review-summary.md](review-summary.md): the account-line mechanism, `.gitignore`, the
`Datasets.md` example values (P16), whether naming the five `del` variables (F9) narrows student
freedom, and K8. **Do not apply B3, P16, F9, or K8 before those are answered.** Everything else
in §4 is unblocked but should land *after* the key's re-run, so the student repo is updated once.
