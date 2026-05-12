# Gemma3 vs Gemma4 — Research Artifact Repository

**Paper:** Attribute Extraction with Fine-tuned Gemma Models — A Comparison Study  
**Domain:** Industrial Product Search (Electric Motors)  
**Dataset:** 1,000 product search queries  
**Ground Truth:** Claude Opus (Claude Sonnet 4)  
**Generated:** 2026-05-12T14:08:46

---

## Repository Layout

```
artifacts/
  gemma3/raw/     — Gemma3 (Gemma 2 9B based) training, inference, results
  gemma4/raw/     — Gemma4 (Gemma V4) training, inference, results
  common/raw/     — Shared datasets, GT, comparisons, docs
docs/
  provenance.md          — Source locations, copy rules, exclusions
  missing_items.md       — Files still needed for full paper
  research_artifact_index.md — Human-readable index by category
manifests/
  file_manifest.csv      — Full file manifest (path, sha256, size, family)
  file_manifest.json     — Same as JSON
checks/
  integrity_report.md    — Counts, duplicates, anchor status, checklist
```

## Quick Stats
| Family | Files | Size |
|--------|-------|------|
| Gemma3 | 15 | 1.57 MB |
| Gemma4 | 4 | 3.61 MB |
| Common | 204 | 91.79 MB |

## Benchmark Results (Key Finding)
| Model | vs Ground Truth Key Match |
|-------|--------------------------|
| Gemini (zero-shot) | 85.4% |
| Gemma V4 (fine-tuned) | 59.9% |
| QMeans (production) | 52.8% |

## See Also
- `docs/missing_items.md` — files still needed from GPU server
- `checks/integrity_report.md` — anchor file status
