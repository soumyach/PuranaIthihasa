# Resume this continuation

Use the current graph tables, chapter_coverage.json, source_coverage.json and extraction_queue.json as the authoritative state. The frozen track patches record this continuation against its original baseline; do not replay them against the already integrated graph. Historical arc checkpoint files are append-only snapshots, not newer replacements for the current tables.

Preserve existing IDs. Add distinct evidence-backed records and document corrections with before/after values. Resume exact unread or unextracted passage bounds in the queue. COMPLETE chapters require whole-body reading and all six checks; a finished bounded story spine does not promote an incomplete chapter.

Next source order: resolve Upāsanā 3, 11, 13, 23 and 24, then extract 36 onward; extract Krīḍā 12 onward and the read material at 150, then continue 151–155; resolve Mudgala 1.27, 1.31 and 1.32, then resume 1.48 onward and khaṇḍas 2–9. Preserve the embedded Gītā 138–148 work and its separate standalone-witness gaps. Devī Bhāgavata priority sections remain only partly extracted.

For independent review, consult continuation_independent_review.json, VERIFICATION_REPORT.md and claims_needing_review.json. Unreviewed author-supported claims remain candidates for further independent checking.

Offline checks from the research folder:

```sh
python3 validate_graph.py
python3 -m unittest discover -s . -p test_integrity.py -v
```
