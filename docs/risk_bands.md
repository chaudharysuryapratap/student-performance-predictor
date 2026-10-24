# Demonstration risk bands

The owner selected the source dataset's passing mark, 60/100. All 500 deduplicated source records follow this label rule. The frozen model, source data and training scripts remain byte-identical.

The original 100-record calibration partition gives an absolute-residual split-conformal radius of 6.260760806936638 points at nominal coverage 0.9. It was recomputed using the frozen model and matched the saved report. Train, calibration and test membership are disjoint. The source hash matches that report and the recomputed test predictions match the saved predictions.

For score s, lower = max(0, s − radius) and upper = min(100, s + radius). High means upper < 60. Medium means lower < 60 <= upper. Low means lower >= 60. Boundaries use full precision: approximately 53.73924 and 66.26076. Rounded display values never determine the band.

| Demo band | Test records | Recorded score below 60 |
|---|---:|---:|
| High | 40 | 38 |
| Medium | 58 | 37 |
| Low | 2 | 0 |

The interval covered 89 of 100 test outcomes. This is marginal score-interval coverage, not an individual passing probability or a calibrated probability for each band. The Low sample is far too small to establish dependable low-risk performance. All results remain uncertain, and Low never guarantees a pass. The test split has now been inspected; it cannot be described as a fresh future evaluation. Independent college data is required for external validation. No names, contacts, transcripts, or new student submissions were used.

Reproduce the audit locally with `python scripts/evaluate_bands.py` in the complete original workspace. It reads the locked model and original report, recomputes predictions and the existing calibration quantile, and writes only aggregate `models/band_evidence.json`. It does not fit, train, modify or save a model. The original private report and split identifiers are not published. Deployment needs only the aggregate evidence; its checksum is recorded in `core/bands.yaml` and its model hash must match the locked artifact. Different evidence requires explicit checksum review; arbitrary YAML thresholds remain rejected.

After deployment, verify a synthetic confirmed result shows a band, interval, passing mark and evaluation counts without a scoring exception. If band rendering or hash checks fail, restore the preceding app commit; never bypass the model lock. No institution-specific accuracy or pass probability is claimed.
