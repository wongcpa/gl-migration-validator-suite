"""
tests/test_erp_mapping_validator.py
Run: pytest tests/ -v
"""
import sys, os, csv, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from erp_mapping_validator import (
    build_lookup, load_mapping, validate, MIGRATION_PATHS
)

F = os.path.join(os.path.dirname(__file__), 'fixtures')

# Use NetSuite → SAP as primary test path
NS_SAP_CFG = MIGRATION_PATHS["1"]

class TestBuildLookup:
    def test_returns_dict(self):
        lu = build_lookup(NS_SAP_CFG['src_coa'], NS_SAP_CFG['src_cols'])
        assert isinstance(lu, dict)
    def test_has_account_entries(self):
        lu = build_lookup(NS_SAP_CFG['src_coa'], NS_SAP_CFG['src_cols'])
        assert len(lu) > 10
    def test_entries_have_required_keys(self):
        lu = build_lookup(NS_SAP_CFG['src_coa'], NS_SAP_CFG['src_cols'])
        for code, entry in lu.items():
            assert {'num','name','type','active'}.issubset(entry.keys())
    def test_active_flag_is_boolean(self):
        lu = build_lookup(NS_SAP_CFG['src_coa'], NS_SAP_CFG['src_cols'])
        for entry in lu.values():
            assert isinstance(entry['active'], bool)
    def test_duplicate_codes_first_wins(self):
        coa = [('1000','Name A','TypeA',True),('1000','Name B','TypeB',True)]
        lu = build_lookup(coa, 4)
        assert lu['1000']['name'] == 'Name A'

class TestLoadMapping:
    def test_loads_netsuite_to_sap(self):
        mapping = load_mapping(f'{F}/mapping_netsuite_to_sap.csv',
                               'netsuite_acct_num','sap_gl_acct')
        assert len(mapping) > 10
    def test_returns_tuples(self):
        mapping = load_mapping(f'{F}/mapping_netsuite_to_sap.csv',
                               'netsuite_acct_num','sap_gl_acct')
        assert all(isinstance(m, tuple) and len(m) == 3 for m in mapping)
    def test_loads_xero_to_netsuite(self):
        mapping = load_mapping(f'{F}/mapping_xero_to_netsuite.csv',
                               'xero_code','netsuite_acct_num')
        assert len(mapping) > 10
    def test_loads_sap_to_oracle(self):
        mapping = load_mapping(f'{F}/mapping_sap_to_oracle.csv',
                               'sap_gl_acct','oracle_acct')
        assert len(mapping) > 10
    def test_loads_workday_to_netsuite(self):
        mapping = load_mapping(f'{F}/mapping_workday_to_netsuite.csv',
                               'workday_worktag_id','netsuite_acct_num')
        assert len(mapping) > 5
    def test_loads_qbo_to_netsuite(self):
        mapping = load_mapping(f'{F}/mapping_qbo_to_netsuite.csv',
                               'qbo_acct_num','netsuite_acct_num')
        assert len(mapping) > 10

class TestValidate:
    @pytest.fixture
    def ns_sap_setup(self):
        src = build_lookup(NS_SAP_CFG['src_coa'], NS_SAP_CFG['src_cols'])
        tgt = build_lookup(NS_SAP_CFG['tgt_coa'], NS_SAP_CFG['tgt_cols'])
        mapping = load_mapping(f'{F}/mapping_netsuite_to_sap.csv',
                               'netsuite_acct_num','sap_gl_acct')
        return src, tgt, mapping

    def test_returns_four_lists(self, ns_sap_setup):
        src, tgt, mapping = ns_sap_setup
        result = validate(mapping, src, tgt, NS_SAP_CFG['type_map'], 'NetSuite','SAP')
        assert len(result) == 4  # errors, warnings, unmapped, clean

    def test_clean_mappings_exist(self, ns_sap_setup):
        src, tgt, mapping = ns_sap_setup
        errors, warnings, unmapped, clean = validate(
            mapping, src, tgt, NS_SAP_CFG['type_map'], 'NetSuite','SAP')
        assert len(clean) > 5

    def test_type_mismatch_detected(self, ns_sap_setup):
        """Fixture contains intentional type mismatches; each must be reported."""
        src, tgt, mapping = ns_sap_setup
        errors, warnings, unmapped, clean = validate(
            mapping, src, tgt, NS_SAP_CFG['type_map'], 'NetSuite','SAP')
        assert any('TYPE_MISMATCH' in e for e in errors)

    def test_type_mismatch_not_counted_as_clean(self):
        src = {'1000':{'name':'Cash','type':'Bank','active':True}}
        tgt = {'500000':{'name':'Revenue','type':'P','active':True}}
        mapping = [('1000','500000','Wrong side of the ledger')]
        errors, warnings, unmapped, clean = validate(mapping, src, tgt, {'Bank':'X'}, 'NS','SAP')
        assert any('TYPE_MISMATCH' in e for e in errors)
        assert clean == []

    def test_inactive_account_flagged(self, ns_sap_setup):
        src, tgt, mapping = ns_sap_setup
        errors, warnings, unmapped, clean = validate(
            mapping, src, tgt, NS_SAP_CFG['type_map'], 'NetSuite','SAP')
        inactive_warnings = [w for w in warnings if 'INACTIVE' in w]
        assert len(inactive_warnings) >= 1

    def test_duplicate_target_flagged(self, ns_sap_setup):
        src, tgt, mapping = ns_sap_setup
        errors, warnings, unmapped, clean = validate(
            mapping, src, tgt, NS_SAP_CFG['type_map'], 'NetSuite','SAP')
        dup_warnings = [w for w in warnings if 'DUPLICATE' in w]
        assert len(dup_warnings) >= 1

    def test_clean_entries_have_required_fields(self, ns_sap_setup):
        src, tgt, mapping = ns_sap_setup
        errors, warnings, unmapped, clean = validate(
            mapping, src, tgt, NS_SAP_CFG['type_map'], 'NetSuite','SAP')
        for entry in clean:
            assert len(entry) == 5  # src_code, src_name, tgt_code, tgt_name, notes

    def test_contra_revenue_to_gross_flagged(self):
        src = {'4100':{'name':'Revenue Deductions','type':'Income','active':True}}
        tgt = {'400000':{'name':'Content Licensing Revenue','type':'P','active':True},
               '400900':{'name':'Contra Revenue','type':'P','active':True}}
        errors, _, _, clean = validate([('4100','400000','')], src, tgt, {}, 'NS','SAP')
        assert any('CONTRA_TO_GROSS' in e for e in errors)
        assert clean == []
        errors, _, _, clean = validate([('4100','400900','')], src, tgt, {}, 'NS','SAP')
        assert errors == [] and len(clean) == 1

    def test_opening_balance_equity_flagged(self):
        src = {'3000':{'name':'Opening Balance Equity','type':'Equity','active':True}}
        tgt = {'3000':{'name':'Common Stock','type':'Equity','active':True}}
        _, warnings, _, _ = validate([('3000','3000','')], src, tgt, {}, 'QBO','NS')
        assert any('OBE_RECLASS' in w for w in warnings)

    def test_missing_source_produces_error(self):
        src = {'1000':{'name':'Cash','type':'Bank','active':True}}
        tgt = {'100000':{'name':'Bank','type':'X','active':True}}
        mapping = [('9999','100000','Missing source')]
        errors, warnings, unmapped, clean = validate(mapping, src, tgt, {}, 'NS','SAP')
        assert any('MISSING_SOURCE' in e for e in errors)

    def test_empty_target_produces_warning(self):
        src = {'1000':{'name':'Cash','type':'Bank','active':True}}
        tgt = {}
        mapping = [('1000','','No target')]
        errors, warnings, unmapped, clean = validate(mapping, src, tgt, {}, 'NS','SAP')
        assert any('UNMAPPED_INLINE' in w for w in warnings)

class TestAllMigrationPaths:
    @pytest.mark.parametrize("path_name", list(MIGRATION_PATHS.keys()))
    def test_path_config_has_required_keys(self, path_name):
        cfg = MIGRATION_PATHS[path_name]
        required = {'name','src_label','tgt_label','fixture','src_coa','tgt_coa','type_map',
                    'src_cols','tgt_cols','map_cols','expected_mapping_cols','output'}
        assert required.issubset(cfg.keys())

    @pytest.mark.parametrize("path_name,fixture,src_col,tgt_col", [
        ("1", "mapping_netsuite_to_sap.csv",     "netsuite_acct_num",  "sap_gl_acct"),
        ("2", "mapping_xero_to_netsuite.csv",    "xero_code",          "netsuite_acct_num"),
        ("3", "mapping_sap_to_oracle.csv",       "sap_gl_acct",        "oracle_acct"),
        ("4", "mapping_workday_to_netsuite.csv", "workday_worktag_id", "netsuite_acct_num"),
        ("5", "mapping_qbo_to_netsuite.csv",     "qbo_acct_num",       "netsuite_acct_num"),
    ])
    def test_full_validation_pipeline(self, path_name, fixture, src_col, tgt_col):
        cfg = MIGRATION_PATHS[path_name]
        src = build_lookup(cfg['src_coa'], cfg['src_cols'])
        tgt = build_lookup(cfg['tgt_coa'], cfg['tgt_cols'])
        mapping = load_mapping(f'{F}/{fixture}', src_col, tgt_col)
        errors, warnings, unmapped, clean = validate(
            mapping, src, tgt, cfg['type_map'], cfg['src_label'], cfg['tgt_label'])
        # All paths should complete without exception
        assert isinstance(errors, list)
        assert isinstance(warnings, list)
        assert isinstance(unmapped, list)
        assert isinstance(clean, list)
        assert len(clean) > 0  # Every fixture has some clean mappings

class TestIntegration:
    def test_export_produces_csv(self, tmp_path):
        from erp_mapping_validator import export_csv
        src = build_lookup(NS_SAP_CFG['src_coa'], NS_SAP_CFG['src_cols'])
        tgt = build_lookup(NS_SAP_CFG['tgt_coa'], NS_SAP_CFG['tgt_cols'])
        mapping = load_mapping(f'{F}/mapping_netsuite_to_sap.csv','netsuite_acct_num','sap_gl_acct')
        errors, warnings, unmapped, clean = validate(
            mapping, src, tgt, NS_SAP_CFG['type_map'], 'NetSuite','SAP')
        out = str(tmp_path / 'result.csv')
        export_csv(clean, errors, warnings, out)
        assert os.path.exists(out)
        with open(out, newline='', encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))
        assert len(rows) > 0
