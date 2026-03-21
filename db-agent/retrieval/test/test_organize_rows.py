import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from organize_rows import clean_rows, organize_rows


class TestCleanRows:
    def test_filters_none_and_empty(self):
        rows = [{'a': 1, 'b': None, 'c': ''}]
        assert clean_rows(rows) == [{'a': 1}]

    def test_filters_underscore_prefix(self):
        rows = [{'a': 1, '_internal': 42}]
        assert clean_rows(rows) == [{'a': 1}]

    def test_keeps_valid_values(self):
        rows = [{'a': 1, 'b': 'hello', 'c': 0}]
        assert clean_rows(rows) == [{'a': 1, 'b': 'hello', 'c': 0}]


class TestOrganizeRowsSingleRow:
    def test_single_row_returns_dict(self):
        assert organize_rows([{'a': 1, 'b': 2}]) == {'a': 1, 'b': 2}

    def test_empty_returns_empty_list(self):
        assert organize_rows([]) == []


class TestOrganizeRowsCommonColumns:
    def test_all_equal_returns_common_dict(self):
        rows = [{'a': 1, 'b': 2}, {'a': 1, 'b': 2}]
        assert organize_rows(rows) == {'a': 1, 'b': 2}

    def test_extracts_common_with_items(self):
        rows = [{'a': 1, 'b': 10}, {'a': 1, 'b': 20}]
        result = organize_rows(rows)
        assert isinstance(result, dict)
        assert result['a'] == 1
        assert 'items' in result

    def test_single_remaining_merges_flat(self):
        rows = [{'a': 1, 'b': 2}, {'a': 1}]
        result = organize_rows(rows)
        assert result == {'a': 1, 'b': 2}


class TestOrganizeRowsGrouping:
    def test_splits_by_least_variance(self):
        rows = [
            {'city': 'X', 'street': 'A', 'order': 1},
            {'city': 'X', 'street': 'A', 'order': 2},
            {'city': 'X', 'street': 'B', 'order': 3},
        ]
        result = organize_rows(rows)
        assert isinstance(result, dict)
        assert result['city'] == 'X'
        assert 'items' in result
        items = result['items']
        assert isinstance(items, list)
        assert len(items) == 2

    def test_prefers_keys_present_in_all_rows(self):
        rows = [
            {'color': 'red', 'size': 'L'},
            {'color': 'red', 'size': 'M', 'extra': 'note'},
        ]
        result = organize_rows(rows)
        assert isinstance(result, dict)
        assert result['color'] == 'red'

    def test_no_common_no_useful_split_returns_list(self):
        rows = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
        result = organize_rows(rows)
        assert isinstance(result, list)
        assert len(result) == 2


class TestOrganizeRowsRecursive:
    def test_nested_grouping(self):
        rows = [
            {'car': 'A', 'year': 2020, 'trip': 1},
            {'car': 'A', 'year': 2020, 'trip': 2},
            {'car': 'B', 'year': 2021, 'trip': 3},
        ]
        result = organize_rows(rows)
        assert isinstance(result, list)
        assert len(result) == 2
        group_a = next(r for r in result if isinstance(r, dict) and r.get('car') == 'A')
        assert group_a['year'] == 2020
        assert 'items' in group_a

    def test_subset_row_merges_extras(self):
        rows = [
            {'car': 'X', 'model': 'M1', 'year': 2020},
            {'car': 'X', 'model': 'M1', 'year': 2020, 'color': 'red', 'vin': '123'},
        ]
        result = organize_rows(rows)
        assert isinstance(result, dict)
        assert result['car'] == 'X'
        assert result['model'] == 'M1'
        assert result['year'] == 2020
        assert result['color'] == 'red'
        assert result['vin'] == '123'
        assert 'items' not in result


class TestSeparate:
    def test_single_value_becomes_scalar(self):
        records = [
            {'device': 'android', 'order': 1},
            {'device': 'android', 'order': 2},
        ]
        result = organize_rows(records, separate_cols={'device'})
        assert isinstance(result, dict)
        assert result['device'] == 'android'

    def test_multiple_values_become_list(self):
        records = [
            {'device': 'android', 'order': 1},
            {'device': 'ios', 'order': 2},
        ]
        result = organize_rows(records, separate_cols={'device'})
        assert isinstance(result, dict)
        assert result['device'] == ['android', 'ios']

    def test_separated_keys_at_end(self):
        records = [
            {'device': 'android', 'name': 'A', 'order': 1},
            {'device': 'ios', 'name': 'A', 'order': 2},
        ]
        result = organize_rows(records, separate_cols={'device'})
        assert isinstance(result, dict)
        keys = list(result.keys())
        assert keys[-1] == 'device'

    def test_single_record_merges_flat(self):
        records = [{'device': 'android', 'name': 'A', 'order': 1}]
        result = organize_rows(records, separate_cols={'device'})
        assert result == {'name': 'A', 'order': 1, 'device': 'android'}
        assert 'items' not in result

    def test_no_remaining_returns_separated_only(self):
        records = [{'device': 'android'}, {'device': 'ios'}]
        result = organize_rows(records, separate_cols={'device'})
        assert result == {'device': ['android', 'ios']}


class TestOrganizeRowsPrefix:
    def test_strips_prefix_from_keys(self):
        rows = [{'tbl_id': 1, 'tbl_name': 'Alice'}]
        assert organize_rows(rows, prefix='tbl_') == {'id': 1, 'name': 'Alice'}

    def test_prefix_with_compression(self):
        rows = [{'tbl_id': 1, 'tbl_val': 10}, {'tbl_id': 1, 'tbl_val': 20}]
        result = organize_rows(rows, prefix='tbl_')
        assert isinstance(result, dict)
        assert result['id'] == 1
        assert 'items' in result

    def test_prefix_with_separate_cols(self):
        rows = [{'tbl_device': 'android', 'tbl_order': 1}, {'tbl_device': 'ios', 'tbl_order': 2}]
        result = organize_rows(rows, separate_cols={'device'}, prefix='tbl_')
        assert isinstance(result, dict)
        assert result['device'] == ['android', 'ios']


class TestOrganizeRowsOrganizeCols:
    def test_organizes_list_of_dicts_value(self):
        trips = [{'city': 'NYC', 'year': 2020}, {'city': 'NYC', 'year': 2021}]
        rows = [{'name': 'Alice', 'trips': trips}]
        result = organize_rows(rows, organize_cols={'trips'})
        assert result == {
            'name': 'Alice',
            'trips': {'city': 'NYC', 'items': [{'year': 2020}, {'year': 2021}]},
        }

    def test_key_not_in_organize_cols_left_unchanged(self):
        rows = [{'name': 'Alice', 'tags': ['a', 'b']}]
        result = organize_rows(rows, organize_cols={'other'})
        assert result == {'name': 'Alice', 'tags': ['a', 'b']}

    def test_organize_col_with_varying_rows(self):
        trips = [{'city': 'NYC'}, {'city': 'LA'}]
        rows = [{'name': 'Alice', 'trips': trips}]
        result = organize_rows(rows, organize_cols={'trips'})
        assert isinstance(result, dict)
        assert result['trips'] == [{'city': 'NYC'}, {'city': 'LA'}]

    def test_organize_col_non_list_of_dicts_raises(self):
        rows = [{'name': 'Alice', 'tags': [1, 2, 3]}]
        with pytest.raises(ValueError):
            organize_rows(rows, organize_cols={'tags'})


class TestOrganizeRowsValidation:
    def test_raises_for_non_list(self):
        with pytest.raises(ValueError):
            organize_rows({'a': 1})  # type: ignore

    def test_raises_for_list_of_non_dicts(self):
        with pytest.raises(ValueError):
            organize_rows([1, 2, 3])  # type: ignore
