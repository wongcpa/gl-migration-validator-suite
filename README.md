# gl-migration-validator-suite

**Chart of accounts mapping validator for five ERP migration paths — NetSuite→SAP, Xero→NetSuite, SAP→Oracle, Workday→NetSuite, QBO→NetSuite.**

Built to reflect ERP implementation and migration work across Fortune 500, SaaS startup, and Amazon subsidiary environments. Validates proposed GL account mappings for type mismatches, duplicate targets, inactive source accounts, and unmapped active accounts — catching go-live blockers before cutover.

[![License: MIT](https://img.shields.io/badge/License-MIT-teal.svg)](LICENSE) [![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org) [![Tests: pytest](https://img.shields.io/badge/Tests-pytest-green.svg)](tests/) [![100% Local](https://img.shields.io/badge/Data%20Privacy-100%25%20Local-brightgreen.svg)](#data-privacy)

---

## Live Demo
Open `src/index.html` → select a migration path → drop the matching fixture CSV from `fixtures/`.

---

## Migration Paths Supported

| Path | Fixture | Use Case |
|---|---|---|
| NetSuite → SAP S/4HANA | `mapping_netsuite_to_sap.csv` | Amazon subsidiary scale-up |
| Xero → NetSuite | `mapping_xero_to_netsuite.csv` | SaaS startup growth migration |
| SAP S/4HANA → Oracle Fusion | `mapping_sap_to_oracle.csv` | Fortune 500 semiconductor |
| Workday → NetSuite | `mapping_workday_to_netsuite.csv` | Enterprise HR-to-ERP |
| QuickBooks Online → NetSuite | `mapping_qbo_to_netsuite.csv` | SMB growth migration |

---

## Features

| Feature | Detail |
|---|---|
| Type compatibility check | B/S accounts cannot map to P&L and vice versa |
| Duplicate target detection | Flags many-to-one mappings requiring review |
| Inactive account flagging | Warns when retired accounts are included in scope |
| Missing account detection | Catches accounts in mapping not found in either COA |
| Unmapped active accounts | Lists source accounts missing from the mapping file |
| Filter by B/S vs P&L | Web app filter for Balance Sheet vs. Income Statement mappings |
| CSV export | Migration-ready validation report |
| All 5 paths in one tool | Single web app, single CLI, no switching between files |

---

## Repository Structure

```
gl-migration-validator-suite/
├── src/
│   ├── index.html                      # Browser web app — all 5 paths
│   └── validators/
│       ├── erp_mapping_validator.py    # Python CLI — all 5 paths via menu
│       ├── netsuite_to_sap.py          # Standalone: NetSuite → SAP
│       ├── xero_to_netsuite.py         # Standalone: Xero → NetSuite
│       └── sap_oracle_wd_qbo.py        # Standalone: SAP→Oracle, WD→NS, QBO→NS
├── tests/
│   └── test_erp_mapping.py             # pytest suite — all 5 paths
├── fixtures/
│   ├── mapping_netsuite_to_sap.csv
│   ├── mapping_xero_to_netsuite.csv
│   ├── mapping_sap_to_oracle.csv
│   ├── mapping_workday_to_netsuite.csv
│   └── mapping_qbo_to_netsuite.csv
├── requirements.txt
├── .gitignore
└── LICENSE
```

---

## Quick Start

**Web app:** `open src/index.html` → select path → drop matching CSV from `fixtures/`.

**CLI:**
```bash
git clone https://github.com/wongcpa/gl-migration-validator-suite.git
cd gl-migration-validator-suite
python src/validators/erp_mapping_validator.py
# Select migration path (1–5), then enter fixture CSV path
```

**Tests:** `pip install pytest && pytest tests/ -v`

---

## Mapping CSV Format

Each migration path requires a CSV with source account, target account, and notes columns. See the fixture files in `fixtures/` for exact column names per path.

| Error Code | Meaning | Action |
|---|---|---|
| `MISSING_SOURCE` | Account in mapping not in source COA | Verify account number |
| `MISSING_TARGET` | Account in mapping not in target COA | Confirm target COA is current |
| `TYPE_MISMATCH` | B/S mapped to P&L or vice versa | Review mapping logic |
| `INACTIVE` | Inactive source account in scope | Confirm migration intent |
| `DUPLICATE_TARGET` | Multiple sources → same target | Confirm intentional consolidation |

---

## ERP-Specific Notes

- **SAP**: Account types `X` (Balance Sheet) and `P` (P&L) are strictly enforced — mismatches cause posting blocks at go-live
- **Oracle Fusion**: Segment-qualified accounts (e.g. `01-4000-000`) require full segment mapping
- **NetSuite**: Subsidiary and department dimensions are separate from COA — map independently
- **Xero**: Duplicate account codes across tracking categories will be flagged
- **QBO**: Opening Balance Equity should be reclassified to Common Stock post-migration

---

## Data Privacy
All processing is local. No COA or mapping data is uploaded to any server.

---

## Author

**Jimmy Wong, CPA (WA), CPA (Canada)**
[www.wong.cpa](https://www.wong.cpa) · [LinkedIn](https://www.linkedin.com/in/wongjimmy/) · [GitHub @wongcpa](https://github.com/wongcpa)

*Resolve all ERRORS before migration cutover. Review WARNINGS with both functional consultants.*
