# TD 1 report, 21/10/2026

_To be written at the end of the session._

## References

Each member computes the references of their questions in `reference-<role>.csv`, then another member cross-checks them independently (A-B, C-D, E-A, see the README). Each member then fills their own rows of `reference-td1.csv`; C checks the consolidated file.

| Role | Questions | File | Own check | Cross-checked by | Cross-check result |
|---|---|---|---|---|---|
| A | C01, C04, C05, C06 | `reference-A.csv` | | B | match |
| B | C07, C12, C13, C20 | `reference-B-temp.csv` | `check_reference_B.py` | A | match |
| C | C02, C08, C09, C11 | `reference-C.csv`, queries in `refs/` | Python recomputation from `data/*.csv` with a hand-written completed-age function; boundary customers (C001-C007, born one day apart) checked | D | match (same four values) |
| D | C03, C10, C14, C18 | `reference-D.csv` | `validate_role_d.py` | C | match (same four values): C recomputed them blind, with a different SQL age formula (date shifts instead of year/month-day arithmetic) and in Python from `data/*.csv` |
| E | C15, C16, C17, C19 | `reference_E.csv` | `check_reference_E.py` | A | match |
