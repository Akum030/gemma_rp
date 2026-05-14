# Priority Benchmark Report

## Source Files
- v7: `c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/v7_eval_summary.json`
- hybrid serving: `c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/hybrid_v7_qmeans_eval_summary.json`
- v8: `c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/v8_eval_summary.json`
- v9: `c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/v9_eval_summary.json`
- v10: `c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/v10_eval_summary.json`
- v11: `c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/v11_eval_summary.json`

## Summary Table

| Model | Status | N | Key P | Key R | Key F1 | Key+Value P | Key+Value R | Key+Value F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qmeans | completed | 1000 | 0.9595 | 0.2982 | 0.455 | 0.1266 | 0.0393 | 0.06 |
| v7 | completed | 1000 | 0.6049 | 0.1915 | 0.2909 | 0.3228 | 0.1022 | 0.1552 |
| hybrid_v7_plus_qmeans_fallback | completed | 1000 | 0.756 | 0.4246 | 0.5438 | 0.2394 | 0.1344 | 0.1722 |
| v8 | completed | 1000 | 0.6112 | 0.0912 | 0.1588 | 0.4125 | 0.0616 | 0.1072 |
| v9 | completed | 1000 | 0.7755 | 0.0245 | 0.0475 | 0.4388 | 0.0139 | 0.0269 |
| v10 | completed | 1000 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| v11 | completed | 1000 | 0.7947 | 0.3182 | 0.4544 | 0.3543 | 0.1418 | 0.2026 |

## Notes
- Best current key F1: hybrid_v7_plus_qmeans_fallback (0.5438)
- Best current key+value F1: v11 (0.2026)
- Best standalone priority model: v11 (key+value F1 0.2026)
- The hybrid row is a serving-time combination, not a new standalone finetuned model.
- This report is purely a metric rollup. It does not replace structural error analysis.
