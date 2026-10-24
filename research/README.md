# Education training datasets

These are the education dataset files supplied by the repository owner and used in the project's earlier training work. They are published at the owner's explicit request. They are not answers submitted through the deployed self-check. No model was retrained, converted or re-saved during publication.

| File | Rows | Source / use |
|---|---:|---|
| `dataset/student_performance_dataset.csv` | 708 | Original CSV from `archive.zip`; exact source for the primary frozen model before deduplication |
| `imported/original.csv` | 708 | CSV imported from the same archive for the dataset-specific comparison pipeline; values match the original file, serialization differs |
| `imported/exam.csv` | 100,000 | `student_exam_performance.csv` from owner-supplied `archive (2).zip` |
| `imported/academic.csv` | 3,000 | `student_performance_dataset777.csv` from owner-supplied `archive (1).zip` |
| `imported/entrance.csv` | 666 | CSV conversion of `CEE_DATA.arff` from the owner-supplied UCI entrance-examination archive |
| `imported/uci_math.csv` | 395 | CSV import of `student-mat.csv` from the nested UCI `student.zip` |
| `imported/uci_portuguese.csv` | 649 | CSV import of `student-por.csv` from the nested UCI `student.zip` |
| `imported/uci_dictionary.txt` | — | Original field dictionary accompanying the UCI subject datasets |

The files above are byte-identical to the existing local training inputs. [manifest.json](manifest.json) records their SHA-256 hashes, sizes, row counts and column names. CSV serialization from the earlier import step may differ from an archive's original CSV; no additional transformation was performed for publication. Duplicate rows are retained in these source files; earlier training loaders removed them before splitting.

## Sources and attribution

- **Original study-habits dataset:** Amr Maree, [Student Performance Prediction](https://www.kaggle.com/datasets/amrmaree/student-performance-prediction), supplied version 2. Kaggle metadata listed CC BY 4.0. Collection provenance was not independently verified.
- **Mathematics and Portuguese:** [UCI Student Performance](https://archive.ics.uci.edu/dataset/320/student+performance), associated with P. Cortez and A. M. G. Silva, *Using data mining to predict secondary school student performance* (2008). [Dataset DOI](https://doi.org/10.24432/C5TG7T). UCI lists CC BY 4.0. These are secondary-school records from two Portuguese schools; they are not college records.
- **Entrance examination:** [UCI Student Performance on an Entrance Examination](https://archive.ics.uci.edu/dataset/582/student+performance+on+an+entrance+examination), collected by Prof. Jiten Hazarika; UCI donation 2018. [Dataset DOI](https://doi.org/10.24432/C58D0H). UCI lists CC BY 4.0.
- **100,000-row exam and 3,000-row academic-habits datasets:** supplied directly by the owner in the archives named above. The original publisher, collection process and redistribution license were not established from those files. No new license or claim that they are genuine college records is assigned by this repository.

## Interpretation

Some source columns describe demographic, family or wellbeing attributes. Preserving the source dataset does not mean the deployed model uses those columns. The deployed self-check asks only for its five declared academic/context features. No names, email addresses, phone numbers or roll numbers were found in the published column schema; the study-habits and larger exam datasets contain source student identifiers. Public availability does not establish that a dataset is appropriate for decisions about individual students.

The frozen primary model uses the original study-habits dataset only. Other files supported separate earlier experiments; their labels and grading scales must not be pooled into one target. UCI G1/G2 are earlier grades and G3 is the final grade on a 0–20 scale. The deployed model does not automatically train or change when these CSVs are updated.

Training scripts, the AlphaGenome checkpoint, bundled notebooks, presentations, credentials and student chat transcripts are not part of this dataset upload.
