"""
erp_gl_mapping_validator.py
============================
ERP GL Account Mapping Validator Suite — 5 Migration Paths

Usage:
  python erp_gl_mapping_validator.py

You will be prompted to select a migration path, then provide:
  - A mapping CSV file

Test fixtures (one per migration path):
  mapping_netsuite_to_sap.csv
  mapping_xero_to_netsuite.csv
  mapping_sap_to_oracle.csv
  mapping_workday_to_netsuite.csv
  mapping_qbo_to_netsuite.csv

Migration path CSV columns vary — see EXPECTED_COLUMNS below.

Author: Jimmy Wong, CPA
DATA PRIVACY: All data is processed locally. No data leaves your machine.
"""

import csv
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# SECTION 1: CHART OF ACCOUNTS — ALL SYSTEMS
# ---------------------------------------------------------------------------

# NetSuite
NS_COA: List[Tuple] = [
    ("1000","Cash - Operating","Bank",True),("1001","Cash - Payroll","Bank",True),
    ("1100","Accounts Receivable","Accounts Receivable",True),
    ("1110","Prepaid Expenses","Other Current Asset",True),
    ("1120","Deferred Revenue - Current","Other Current Liability",True),
    ("1200","Fixed Assets","Fixed Asset",True),("1210","Accumulated Depreciation","Fixed Asset",True),
    ("1300","Intercompany Receivable","Other Current Asset",True),
    ("1400","Content Assets","Other Asset",True),("1410","Accum Amort - Content","Other Asset",True),
    ("2000","Accounts Payable","Accounts Payable",True),
    ("2010","Accrued Liabilities","Other Current Liability",True),
    ("2020","Deferred Revenue","Other Current Liability",True),
    ("2030","Intercompany Payable","Other Current Liability",True),
    ("2100","Long-Term Debt","Long Term Liability",True),
    ("2110","Credit Card Liability","Other Current Liability",True),
    ("3000","Common Stock","Equity",True),("3100","Retained Earnings","Equity",True),
    ("3200","APIC","Equity",True),
    ("4000","Content Licensing Revenue","Income",True),("4010","Streaming Revenue","Income",True),
    ("4020","Advertising Revenue","Income",True),("4030","Intercompany Revenue","Income",True),
    ("4100","Revenue Deductions","Income",True),
    ("5000","Content Amortization","Cost of Goods Sold",True),
    ("5010","Royalty Expense","Cost of Goods Sold",True),
    ("5020","Distribution Costs","Cost of Goods Sold",True),
    ("5100","Materials","Cost of Goods Sold",True),
    ("6000","Salaries & Wages","Expense",True),("6010","Benefits","Expense",True),
    ("6020","Rent Expense","Expense",True),("6030","Software & IT","Expense",True),
    ("6040","Marketing","Expense",True),("6050","Depreciation Expense","Expense",True),
    ("6100","Occupancy","Expense",True),("6200","IT and Technology","Expense",True),
    ("6300","Professional Services","Expense",True),("6400","Depreciation","Expense",True),
    ("7000","Interest Income","Other Income",True),("7100","Other Income","Other Income",True),
    ("8000","Interest Expense","Other Expense",True),("8100","Other Expenses","Other Expense",True),
    ("9999","Suspense - Legacy","Other Current Asset",False),
]

# SAP S/4HANA
SAP_COA: List[Tuple] = [
    ("100000","Bank Operating","X"),("100010","Bank Payroll","X"),
    ("110000","Trade Receivables","X"),("110010","Allowance - Bad Debt","X"),
    ("110020","Unbilled Receivables","X"),("120000","Prepaid Expenses","X"),
    ("130000","Inventory","X"),("131000","Intercompany Receivables","X"),
    ("150000","Plant and Equipment","X"),("151000","Accumulated Depreciation","X"),
    ("160000","Intangible Assets - Content","X"),("161000","Accumulated Amortization","X"),
    ("170000","Other Long-Term Assets","X"),
    ("200000","Trade Payables","X"),("210000","Accrued Liabilities","X"),
    ("220000","Deferred Revenue","X"),("221000","Intercompany Payables","X"),
    ("230000","Tax Payables","X"),("250000","Long-Term Borrowings","X"),
    ("300000","Share Capital","X"),("310000","Retained Earnings","X"),("320000","APIC","X"),
    ("400000","Content Licensing Revenue","P"),("400100","Streaming Revenue","P"),
    ("400200","Advertising Revenue","P"),("400300","Intercompany Revenue","P"),
    ("400900","Revenue Deductions","P"),
    ("500000","Content Amortization","P"),("500100","Royalties","P"),("500200","Distribution","P"),
    ("600000","Personnel Costs","P"),("600100","Employee Benefits","P"),
    ("600200","Rent and Occupancy","P"),("600300","IT and Software","P"),
    ("600400","Marketing","P"),("600500","Travel and Entertainment","P"),
    ("600600","Depreciation and Amortization","P"),("600700","Professional Services","P"),
    ("600800","Insurance","P"),
    ("700000","Interest Income","P"),("700100","FX Gains","P"),
    ("800000","Interest Expense","P"),("800100","FX Losses","P"),
]

# Xero
XERO_COA: List[Tuple] = [
    ("090","Business Checking","BANK",True),("091","Savings Account","BANK",True),
    ("200","Accounts Receivable","CURRENT",True),("201","Prepayments","CURRENT",True),
    ("610","Accounts Payable","CURRLIAB",True),("620","GST/HST Collected","CURRLIAB",True),
    ("630","Wages Payable","CURRLIAB",True),
    ("710","Common Shares","EQUITY",True),("720","Retained Earnings","EQUITY",True),
    ("400","Sales Revenue","REVENUE",True),("401","Consulting Revenue","REVENUE",True),
    ("402","Subscription Revenue","REVENUE",True),("410","Other Income","OTHERINCOME",True),
    ("500","Direct Labour","DIRECTCOSTS",True),("501","Hosting Costs","DIRECTCOSTS",True),
    ("600","Salaries","OVERHEADS",True),("601","Rent","OVERHEADS",True),
    ("602","Software Subscriptions","OVERHEADS",True),("603","Marketing","OVERHEADS",True),
    ("604","Professional Fees","OVERHEADS",True),
    ("800","Fixed Assets","FIXED",True),("801","Accumulated Depreciation","DEPRECIATN",True),
    ("820","Depreciation Expense","OVERHEADS",True),
    ("900","OLD Clearing Account","CURRENT",False),
]

# Oracle Fusion
ORACLE_COA: List[Tuple] = [
    ("01-1000-000","Cash and Cash Equivalents","Balance Sheet"),
    ("01-1100-000","Accounts Receivable - Trade","Balance Sheet"),
    ("01-1101-000","Allowance for Doubtful Accts","Balance Sheet"),
    ("01-1200-000","Raw Material Inventory","Balance Sheet"),
    ("01-1201-000","WIP Inventory","Balance Sheet"),
    ("01-1202-000","Finished Goods Inventory","Balance Sheet"),
    ("01-1300-000","Prepaid Assets","Balance Sheet"),
    ("01-1500-000","Property Plant Equipment","Balance Sheet"),
    ("01-1501-000","Accumulated Depreciation","Balance Sheet"),
    ("01-1600-000","Intangible Assets","Balance Sheet"),
    ("01-2000-000","Accounts Payable","Balance Sheet"),
    ("01-2100-000","Accrued Liabilities","Balance Sheet"),
    ("01-2200-000","Deferred Revenue","Balance Sheet"),
    ("01-2300-000","Income Taxes Payable","Balance Sheet"),
    ("01-2500-000","Notes Payable Long-Term","Balance Sheet"),
    ("01-3000-000","Common Stock","Balance Sheet"),
    ("01-3100-000","Retained Earnings","Balance Sheet"),
    ("01-4000-000","Product Revenue","Income Statement"),
    ("01-4001-000","Service Revenue","Income Statement"),
    ("01-4900-000","Contra Revenue","Income Statement"),
    ("01-5000-000","Cost of Revenue","Income Statement"),
    ("01-5100-000","Manufacturing Overhead","Income Statement"),
    ("01-6000-000","Research and Development","Income Statement"),
    ("01-6100-000","Sales and Marketing","Income Statement"),
    ("01-6200-000","General and Administrative","Income Statement"),
    ("01-6300-000","Stock-Based Compensation","Income Statement"),
    ("01-7000-000","Interest and Other Income","Income Statement"),
    ("01-8000-000","Interest Expense","Income Statement"),
    ("01-8100-000","Income Tax Expense","Income Statement"),
]

# Workday
WORKDAY_COA: List[Tuple] = [
    ("WD-1000","Cash","Assets",True),("WD-1100","Accounts Receivable","Assets",True),
    ("WD-1200","Prepaid Expenses","Assets",True),("WD-1300","PP&E Net","Assets",True),
    ("WD-2000","Accounts Payable","Liabilities",True),
    ("WD-2100","Accrued Salaries","Liabilities",True),
    ("WD-2200","Deferred Revenue","Liabilities",True),
    ("WD-3000","Common Stock","Equity",True),("WD-3100","Retained Earnings","Equity",True),
    ("WD-4000","Service Revenue","Revenue",True),("WD-4100","Product Revenue","Revenue",True),
    ("WD-5000","Personnel Costs","Expenses",True),("WD-5100","Occupancy","Expenses",True),
    ("WD-5200","Technology","Expenses",True),("WD-5300","Professional Services","Expenses",True),
    ("WD-5400","Depreciation","Expenses",True),
    ("WD-ARCH","Archived Suspense","Assets",False),
]

# QBO
QBO_COA: List[Tuple] = [
    ("1000","Checking","Bank",True),
    ("1100","Accounts Receivable (A/R)","Accounts Receivable (A/R)",True),
    ("1200","Prepaid Expenses","Other Current Assets",True),
    ("1500","Equipment","Fixed Assets",True),("1510","Accumulated Depreciation","Fixed Assets",True),
    ("2000","Accounts Payable (A/P)","Accounts Payable (A/P)",True),
    ("2100","Accrued Liabilities","Other Current Liabilities",True),
    ("2200","Credit Card Payable","Credit Card",True),
    ("2300","Deferred Revenue","Other Current Liabilities",True),
    ("3000","Opening Balance Equity","Equity",True),
    ("3100","Retained Earnings","Equity",True),
    ("4000","Services","Income",True),("4100","Product Sales","Income",True),
    ("5000","Cost of Labour","Cost of Goods Sold",True),
    ("5100","Cost of Materials","Cost of Goods Sold",True),
    ("6000","Payroll Expenses","Expenses",True),("6100","Rent or Lease","Expenses",True),
    ("6200","Computer and Internet Exp","Expenses",True),
    ("6300","Professional Fees","Expenses",True),("6400","Depreciation","Expenses",True),
    ("7000","Other Income","Other Income",True),
    ("8000","Other Expenses","Other Expense",True),
    ("9999","Uncategorized Expense","Expenses",False),
]

# ---------------------------------------------------------------------------
# SECTION 2: TYPE COMPATIBILITY MAPS
# ---------------------------------------------------------------------------

NS_TO_SAP_TYPE = {
    "Bank":"X","Accounts Receivable":"X","Other Current Asset":"X",
    "Fixed Asset":"X","Other Asset":"X","Accounts Payable":"X",
    "Other Current Liability":"X","Long Term Liability":"X","Equity":"X",
    "Income":"P","Cost of Goods Sold":"P","Expense":"P",
    "Other Income":"P","Other Expense":"P",
}
XERO_TO_NS_TYPE = {
    "BANK":"Bank","CURRENT":"Other Current Asset","CURRLIAB":"Other Current Liability",
    "DEPRECIATN":"Fixed Asset","DIRECTCOSTS":"Cost of Goods Sold","EQUITY":"Equity",
    "EXPENSE":"Expense","FIXED":"Fixed Asset","LIABILITY":"Long Term Liability",
    "OTHERINCOME":"Other Income","OVERHEADS":"Expense","PREPAYMENT":"Other Current Asset",
    "REVENUE":"Income","SALES":"Income","TERMLIAB":"Long Term Liability",
}
SAP_TO_ORACLE_TYPE = {"X":"Balance Sheet","P":"Income Statement"}
WORKDAY_TO_NS_TYPE = {
    "Assets":"Other Current Asset","Liabilities":"Other Current Liability",
    "Equity":"Equity","Revenue":"Income","Expenses":"Expense",
}
QBO_TO_NS_TYPE = {
    "Bank":"Bank","Accounts Receivable (A/R)":"Accounts Receivable",
    "Other Current Assets":"Other Current Asset","Fixed Assets":"Fixed Asset",
    "Other Assets":"Other Asset","Accounts Payable (A/P)":"Accounts Payable",
    "Credit Card":"Other Current Liability","Other Current Liabilities":"Other Current Liability",
    "Long Term Liabilities":"Long Term Liability","Equity":"Equity",
    "Income":"Income","Cost of Goods Sold":"Cost of Goods Sold",
    "Expenses":"Expense","Other Income":"Other Income","Other Expense":"Other Expense",
}

# ---------------------------------------------------------------------------
# SECTION 3: MIGRATION PATH CONFIGS
# ---------------------------------------------------------------------------

MIGRATION_PATHS = {
    "1": {
        "name":       "NetSuite → SAP S/4HANA",
        "fixture":    "mapping_netsuite_to_sap.csv",
        "src_label":  "NetSuite",
        "tgt_label":  "SAP S/4HANA",
        "src_coa":    NS_COA,
        "tgt_coa":    SAP_COA,
        "type_map":   NS_TO_SAP_TYPE,
        "src_cols":   4,   # has active flag
        "tgt_cols":   3,
        "map_cols":   ("netsuite_acct_num", "sap_gl_acct"),
        "expected_mapping_cols": {"netsuite_acct_num", "sap_gl_acct", "mapping_notes"},
        "output":     "mapping_result_netsuite_to_sap.csv",
    },
    "2": {
        "name":       "Xero → NetSuite",
        "fixture":    "mapping_xero_to_netsuite.csv",
        "src_label":  "Xero",
        "tgt_label":  "NetSuite",
        "src_coa":    XERO_COA,
        "tgt_coa":    NS_COA,
        "type_map":   XERO_TO_NS_TYPE,
        "src_cols":   4,
        "tgt_cols":   4,
        "map_cols":   ("xero_code", "netsuite_acct_num"),
        "expected_mapping_cols": {"xero_code", "netsuite_acct_num", "mapping_notes"},
        "output":     "mapping_result_xero_to_netsuite.csv",
    },
    "3": {
        "name":       "SAP S/4HANA → Oracle Fusion",
        "fixture":    "mapping_sap_to_oracle.csv",
        "src_label":  "SAP S/4HANA",
        "tgt_label":  "Oracle Fusion",
        "src_coa":    SAP_COA,
        "tgt_coa":    ORACLE_COA,
        "type_map":   SAP_TO_ORACLE_TYPE,
        "src_cols":   3,
        "tgt_cols":   3,
        "map_cols":   ("sap_gl_acct", "oracle_acct"),
        "expected_mapping_cols": {"sap_gl_acct", "oracle_acct", "mapping_notes"},
        "output":     "mapping_result_sap_to_oracle.csv",
    },
    "4": {
        "name":       "Workday → NetSuite",
        "fixture":    "mapping_workday_to_netsuite.csv",
        "src_label":  "Workday",
        "tgt_label":  "NetSuite",
        "src_coa":    WORKDAY_COA,
        "tgt_coa":    NS_COA,
        "type_map":   WORKDAY_TO_NS_TYPE,
        "src_cols":   4,
        "tgt_cols":   4,
        "map_cols":   ("workday_worktag_id", "netsuite_acct_num"),
        "expected_mapping_cols": {"workday_worktag_id", "netsuite_acct_num", "mapping_notes"},
        "output":     "mapping_result_workday_to_netsuite.csv",
    },
    "5": {
        "name":       "QBO → NetSuite",
        "fixture":    "mapping_qbo_to_netsuite.csv",
        "src_label":  "QuickBooks Online",
        "tgt_label":  "NetSuite",
        "src_coa":    QBO_COA,
        "tgt_coa":    NS_COA,
        "type_map":   QBO_TO_NS_TYPE,
        "src_cols":   4,
        "tgt_cols":   4,
        "map_cols":   ("qbo_acct_num", "netsuite_acct_num"),
        "expected_mapping_cols": {"qbo_acct_num", "netsuite_acct_num", "mapping_notes"},
        "output":     "mapping_result_qbo_to_netsuite.csv",
    },
}

# ---------------------------------------------------------------------------
# SECTION 4: FILE INPUT WITH RETRY LOGIC
# ---------------------------------------------------------------------------

def select_migration_path() -> Dict:
    """Present migration path menu and return selected config."""
    print("\n" + "=" * 64)
    print("  ERP GL MAPPING VALIDATOR")
    print("=" * 64)
    print("\nSelect migration path:")
    for key, cfg in MIGRATION_PATHS.items():
        print(f"  [{key}] {cfg['name']}  (fixture: {cfg['fixture']})")

    for attempt in range(1, 4):
        choice = input("\nEnter number (1-5): ").strip()
        if choice in MIGRATION_PATHS:
            return MIGRATION_PATHS[choice]
        print(f"  Invalid choice '{choice}'. Enter 1, 2, 3, 4, or 5.")
        if attempt < 3:
            print(f"  Attempt {attempt}/3.")

    print("\n  FATAL: Maximum attempts reached. Exiting.")
    sys.exit(1)


def prompt_for_file(cfg: Dict, max_attempts: int = 3) -> str:
    """
    Prompt for the mapping CSV file.
    Re-prompts up to max_attempts times on failure.
    """
    src_col, tgt_col = cfg["map_cols"]
    expected = cfg["expected_mapping_cols"]

    print(f"\nTest fixture: {cfg['fixture']}")
    print(f"Expected columns: {', '.join(sorted(expected))}")

    for attempt in range(1, max_attempts + 1):
        raw  = input(f"\nMapping CSV for {cfg['name']}: ").strip()
        path = Path(raw)

        if not path.exists():
            print(f"  ERROR: File not found: '{raw}'")
        elif path.suffix.lower() != ".csv":
            print(f"  ERROR: Expected .csv, got '{path.suffix}'")
        else:
            try:
                with open(path, newline="", encoding="utf-8-sig") as f:
                    headers = set(csv.DictReader(f).fieldnames or [])
                    missing = {src_col, tgt_col} - headers
                    if missing:
                        print(f"  ERROR: Missing required columns: "
                              f"{', '.join(sorted(missing))}")
                        print(f"  Expected: {', '.join(sorted(expected))}")
                    else:
                        return str(path)
            except Exception as e:
                print(f"  ERROR: Could not read file: {e}")

        if attempt < max_attempts:
            print(f"  Attempt {attempt}/{max_attempts}. Please try again.")

    print(f"\n  FATAL: Maximum attempts ({max_attempts}) reached. Exiting.")
    sys.exit(1)


def prompt_for_output(default: str) -> str:
    raw = input(f"\nOutput CSV filename [{default}]: ").strip()
    return raw if raw else default


# ---------------------------------------------------------------------------
# SECTION 5: VALIDATION ENGINE
# ---------------------------------------------------------------------------

def build_lookup(coa: List[Tuple], n_cols: int) -> Dict[str, Dict]:
    """Build account number → details dict from a COA list."""
    lookup = {}
    for row in coa:
        code = row[0]
        name = row[1]
        acct_type = row[2]
        active = row[3] if n_cols >= 4 else True
        if code not in lookup:
            lookup[code] = {"num": code, "name": name,
                            "type": acct_type, "active": active}
    return lookup


def load_mapping(filepath: str, src_col: str,
                 tgt_col: str) -> List[Tuple[str, str, str]]:
    """Load mapping CSV into (source, target, notes) tuples."""
    rows = []
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            src   = row[src_col].strip()
            tgt   = row.get(tgt_col, "").strip()
            notes = row.get("mapping_notes", "").strip()
            rows.append((src, tgt, notes))
    return rows


# Contra revenue accounts (deductions from gross) must not land in gross revenue.
CONTRA_RE = re.compile(r"deduction|contra|return|rebate|discount|price protection", re.I)
GROSS_RE  = re.compile(r"revenue|sales", re.I)


def validate(mapping: List[Tuple], src_lookup: Dict, tgt_lookup: Dict,
             type_map: Dict, src_name: str, tgt_name: str):
    """
    Validate mapping and return (errors, warnings, unmapped, clean).
    """
    errors, warnings, clean = [], [], []
    mapped_src   = {m[0] for m in mapping}
    tgt_usage: Dict[str, List] = {}

    for src_code, tgt_code, notes in mapping:
        s = src_lookup.get(src_code)
        t = tgt_lookup.get(tgt_code) if tgt_code else None

        if not s:
            errors.append(f"[MISSING_SOURCE] {src_name} account '{src_code}' not in COA.")
            continue
        if not tgt_code:
            warnings.append(
                f"[UNMAPPED_INLINE] {src_name} {src_code} "
                f"({s['name']}) has no target account.")
            continue
        if not t:
            errors.append(
                f"[MISSING_TARGET] {tgt_name} account '{tgt_code}' not in COA.")
            continue

        if not s.get("active", True):
            warnings.append(
                f"[INACTIVE] {src_name} {src_code} ({s['name']}) is inactive. "
                f"Confirm migration intent.")

        expected = type_map.get(s["type"])
        mismatch = bool(expected) and t["type"] != expected
        if mismatch:
            errors.append(
                f"[TYPE_MISMATCH] {src_code} ({s['type']}) → {tgt_code} ({t['type']}). "
                f"Expected target type: {expected}.")

        contra_to_gross = (bool(CONTRA_RE.search(s["name"])) and bool(GROSS_RE.search(t["name"]))
                           and not CONTRA_RE.search(t["name"]))
        if contra_to_gross:
            errors.append(
                f"[CONTRA_TO_GROSS] {src_code} ({s['name']}) → {tgt_code} ({t['name']}). "
                f"Contra revenue mapped to gross revenue; net revenue would be overstated.")

        if "opening balance equity" in s["name"].lower():
            warnings.append(
                f"[OBE_RECLASS] {src_code} ({s['name']}) → {tgt_code}. Reclassify Opening "
                f"Balance Equity (usually to Retained Earnings) and clear it at cutover.")

        tgt_usage.setdefault(tgt_code, []).append(src_code)
        if not (mismatch or contra_to_gross):
            clean.append((src_code, s["name"], tgt_code, t["name"], notes))

    for tgt_code, srcs in tgt_usage.items():
        if len(srcs) > 1:
            tgt_name_str = tgt_lookup.get(tgt_code, {}).get("name", tgt_code)
            warnings.append(
                f"[DUPLICATE_TARGET] {tgt_code} ({tgt_name_str}) targeted by "
                f"{len(srcs)} source accounts: {', '.join(srcs)}.")

    unmapped = [
        s for code, s in src_lookup.items()
        if code not in mapped_src and s.get("active", True)
    ]

    return errors, warnings, unmapped, clean


# ---------------------------------------------------------------------------
# SECTION 6: REPORTING
# ---------------------------------------------------------------------------

def print_report(errors, warnings, unmapped, clean,
                 src_name, tgt_name) -> None:
    """Print validation report."""
    div = "=" * 76
    print(f"\n{div}")
    print(f"  GL MAPPING VALIDATION: {src_name} → {tgt_name}")
    print(f"  Date: {date.today()}")
    print(f"  Errors: {len(errors)}  |  Warnings: {len(warnings)}  "
          f"|  Unmapped Active: {len(unmapped)}  |  Clean: {len(clean)}")
    print(div)

    if errors:
        print(f"\n  🔴 ERRORS — Must Resolve Before Migration ({len(errors)})")
        print("  " + "-" * 68)
        for e in errors:
            print(f"  {e}")

    if warnings:
        print(f"\n  🟡 WARNINGS — Review Required ({len(warnings)})")
        print("  " + "-" * 68)
        for w in warnings:
            print(f"  {w}")

    if unmapped:
        print(f"\n  ⚪ UNMAPPED ACTIVE ACCOUNTS ({len(unmapped)})")
        print("  " + "-" * 68)
        print(f"  {'Account':<14} {'Name':<36} {'Type'}")
        for a in unmapped:
            print(f"  {a['num']:<14} {a['name'][:35]:<36} {a['type']}")

    print(f"\n  ✔ CLEAN MAPPINGS ({len(clean)})")
    print("  " + "-" * 68)
    print(f"  {'Source':<14} {'Source Name':<28} {'Target':<16} {'Target Name'}")
    for sc, sn, tc, tn, _ in clean:
        print(f"  {sc:<14} {sn[:27]:<28} {tc:<16} {tn[:27]}")

    print(f"\n{div}")
    print("  NOTE: Resolve all ERRORS before migration cutover.")
    print("  WARNINGS should be reviewed with both functional consultants.")
    print(div)


def export_csv(clean, errors, warnings, filepath: str) -> None:
    """Export results to CSV."""
    rows = []
    for sc, sn, tc, tn, notes in clean:
        rows.append({"source": sc, "source_name": sn, "target": tc,
                     "target_name": tn, "notes": notes, "status": "CLEAN",
                     "issue": ""})
    for e in errors:
        rows.append({"source": "", "source_name": "", "target": "",
                     "target_name": "", "notes": "", "status": "ERROR",
                     "issue": e})
    for w in warnings:
        rows.append({"source": "", "source_name": "", "target": "",
                     "target_name": "", "notes": "", "status": "WARNING",
                     "issue": w})
    if not rows:
        return
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n  ✔ Results exported to: {filepath}")


# ---------------------------------------------------------------------------
# SECTION 7: MAIN
# ---------------------------------------------------------------------------

def main():
    cfg = select_migration_path()

    input_path  = prompt_for_file(cfg)
    output_path = prompt_for_output(cfg["output"])

    src_col, tgt_col = cfg["map_cols"]

    print(f"\nBuilding COA lookups...")
    src_lookup = build_lookup(cfg["src_coa"], cfg["src_cols"])
    tgt_lookup = build_lookup(cfg["tgt_coa"], cfg["tgt_cols"])

    print(f"Loading mapping from: {input_path}")
    mapping = load_mapping(input_path, src_col, tgt_col)

    print("Validating...")
    errors, warnings, unmapped, clean = validate(
        mapping, src_lookup, tgt_lookup,
        cfg["type_map"], cfg["src_label"], cfg["tgt_label"]
    )

    print_report(errors, warnings, unmapped, clean,
                 cfg["src_label"], cfg["tgt_label"])
    export_csv(clean, errors, warnings, output_path)


if __name__ == "__main__":
    # Report symbols (✔, →) must print even when output is redirected on Windows.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
