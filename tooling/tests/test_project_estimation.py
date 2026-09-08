from copy import deepcopy
from types import SimpleNamespace

import pytest

from tooling.superversion.project_package.estimation import calculate_estimate, preview_estimate


@pytest.fixture
def scenario():
    return dict(currency='EUR', planning_workdays='10', contingency_percent='20',
                people=[dict(id='p1', name='Consultant', hours_per_day='8', availability_percent='50')],
                assignments=[dict(id='a1', person_id='p1', role='Engineer', effort_hours='40',
                                  cost_per_hour='50.25', sell_per_hour='100.10', currency='EUR')])


def test_decimal_math_and_capacity(scenario):
    result = calculate_estimate(scenario)
    assert result['totals'] == dict(cost='2412.00', revenue='4804.80', contribution='2392.80',
                                   margin_percent='49.8002', buffered_hours='48.0000', minimum_workdays='12.0000')
    assert result['people'][0]['overallocated'] is True
    assert result['roles'][0]['cost'] == '2412.00'
    assert result['status'] == 'scenario_only'


def test_zero_effort_rates_and_revenue_are_not_missing(scenario):
    scenario['assignments'][0].update(effort_hours='0', cost_per_hour='0', sell_per_hour='0')
    scenario['people'][0]['availability_percent'] = '0'
    result = calculate_estimate(scenario)
    assert result['totals']['margin_percent'] is None
    assert result['totals']['minimum_workdays'] == '0.0000'
    assert not result['warnings']


def test_zero_capacity_is_infeasible(scenario):
    scenario['people'][0]['availability_percent'] = '0'
    assert calculate_estimate(scenario)['totals']['minimum_workdays'] is None


@pytest.mark.parametrize('value', ['', None, True, 'NaN', 'Infinity', '-1', '0.0000001'])
def test_missing_or_invalid_rate_rejected(scenario, value):
    scenario['assignments'][0]['cost_per_hour'] = value
    with pytest.raises(ValueError):
        calculate_estimate(scenario)


def test_mixed_currency_rejected(scenario):
    scenario['assignments'][0]['currency'] = 'USD'
    with pytest.raises(ValueError, match='Mixed currencies'):
        calculate_estimate(scenario)


def test_unknown_or_duplicate_people_rejected(scenario):
    scenario['assignments'][0]['person_id'] = 'missing'
    with pytest.raises(ValueError, match='Unknown person'):
        calculate_estimate(scenario)
    scenario['people'].append(deepcopy(scenario['people'][0]))
    with pytest.raises(ValueError, match='Duplicate person'):
        calculate_estimate(scenario)


def test_line_rounding_and_sum_agree(scenario):
    scenario['contingency_percent'] = '0'
    scenario['assignments'][0].update(effort_hours='0.1', cost_per_hour='0.05')
    scenario['assignments'].append(dict(scenario['assignments'][0], id='a2'))
    result = calculate_estimate(scenario)
    assert result['totals']['cost'] == '0.02'
    assert result['people'][0]['cost'] == '0.02'
    assert result['roles'][0]['cost'] == '0.02'
    assert result['assignments'][0]['cost'] == '0.01'


def test_input_immutable_and_deterministic(scenario):
    before = deepcopy(scenario)
    assert calculate_estimate(scenario) == calculate_estimate(scenario)
    assert scenario == before


def test_project_binding_checked_before_calculation(scenario):
    repo = SimpleNamespace(get=lambda revision: SimpleNamespace(project_ref='other', revision_hash=revision))
    with pytest.raises(ValueError, match='another project'):
        preview_estimate(repo, 'selected', 'a'*64, scenario)


def test_revision_bound_without_approval_or_repository_write(scenario):
    repo = SimpleNamespace(get=lambda revision: SimpleNamespace(project_ref='selected', revision_hash=revision))
    result = preview_estimate(repo, 'selected', 'a'*64, scenario)
    assert result['revision_hash'] == 'a'*64
    assert result['project_ref'] == 'selected'
