# Domain Leader Study — aifor-science-protocol (AI-for-science agent protocol)

OUROBOROS phase-3, cohort-01 tranche-2. PROPOSE-ONLY study card: documentation only, no production change in this PR.

## Domain leaders studied
| Leader | What they have | Key sources |
| --- | --- | --- |
| ScienceAgentBench (OSU NLP, ICLR'25) | 102 tasks from 80 papers for tool-augmented scientific data analysis; separates tool-augmented vs autonomous settings; execution-based grading with program support and verdict rubric | arXiv:2410.05080; github.com/OSU-NLP-Group/ScienceAgentBench |

## What the leader does better
- Execution-based evaluation: an agent answer only counts when the produced notebook/code actually runs and reproduces the target metric — the same receipts-first honesty our protocol encodes.
- Explicit setting separation (tool-augmented vs autonomous) prevents grading an agent on capabilities its setting does not allow — avoids manufactured-green by construction.
- Task provenance is grounded in real published papers, so the benchmark cannot drift into self-referential fantasy tasks.

## Absorb actions (proposed, NOT implemented in this PR)
- [ ] Align the protocol's task schema with ScienceAgentBench fields (source paper, gold program, evaluation metric, required tools).
- [ ] Adopt execution-based grading: a protocol run is only GREEN when the emitted artifact executes against the recorded checker, else INCIDENT/FAIL with receipt.
- [ ] Add an explicit per-run setting tag (tool-augmented | autonomous) to run metadata, mirroring the leader's setting taxonomy.
- [ ] Add a verdict rubric (execution vs semantic match) instead of binary pass/fail to preserve honest partial signal.

## Sources
- ScienceAgentBench paper: https://arxiv.org/abs/2410.05080
- Code/data: https://github.com/OSU-NLP-Group/ScienceAgentBench
