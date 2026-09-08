"""Explicit, private commercial scenarios. Never changes a Package or approval."""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from pathlib import Path
import re
import sys

from .hashes import canonical_sha256
from .repository import ProjectPackageRevisionRepository


def _fields(value, required, path):
    if not isinstance(value, dict) or set(value) != set(required):
        raise ValueError(f"{path}: expected exactly {', '.join(required)}")


def _text(value, path):
    if not isinstance(value, str) or not value.strip() or len(value) > 160:
        raise ValueError(f"{path}: non-empty text, at most 160 characters, is required")
    return value.strip()


def _number(value, path, maximum=Decimal('1000000000'), positive=False):
    if isinstance(value, bool) or value is None or not isinstance(value, (str, int, float)):
        raise ValueError(f"{path}: an explicit decimal number is required")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{path}: invalid decimal number") from exc
    if not result.is_finite() or result < 0 or result > maximum or (positive and result == 0):
        raise ValueError(f"{path}: number outside the permitted range")
    if result.as_tuple().exponent < -6:
        raise ValueError(f"{path}: at most six decimal places are supported")
    return result


def _money(value):
    return format(value.quantize(Decimal('.01'), rounding=ROUND_HALF_UP), '.2f')


def _quantity(value):
    return format(value.quantize(Decimal('.0001'), rounding=ROUND_HALF_UP), '.4f')


def calculate_estimate(scenario: dict) -> dict:
    """All work is parallel within one horizon; this is a capacity lower bound, not a scheduler."""
    _fields(scenario, ['currency', 'planning_workdays', 'contingency_percent', 'people', 'assignments'], 'scenario')
    currency = scenario['currency']
    if not isinstance(currency, str) or not re.fullmatch(r'[A-Z]{3}', currency):
        raise ValueError('currency: use a three-letter uppercase currency code')
    horizon = _number(scenario['planning_workdays'], 'planning_workdays', Decimal('10000'), positive=True)
    contingency = _number(scenario['contingency_percent'], 'contingency_percent', Decimal('100'))
    factor = 1 + contingency / 100
    if not isinstance(scenario['people'], list) or not 1 <= len(scenario['people']) <= 200:
        raise ValueError('people: supply between 1 and 200 people')
    if not isinstance(scenario['assignments'], list) or not 1 <= len(scenario['assignments']) <= 1000:
        raise ValueError('assignments: supply between 1 and 1000 work assignments')
    people = {}
    for person in scenario['people']:
        _fields(person, ['id', 'name', 'hours_per_day', 'availability_percent'], 'person')
        ident = _text(person['id'], 'person.id')
        if ident in people:
            raise ValueError(f'Duplicate person id: {ident}')
        name = _text(person['name'], 'person.name')
        hours = _number(person['hours_per_day'], 'hours_per_day', Decimal('24'), positive=True)
        available = _number(person['availability_percent'], 'availability_percent', Decimal('100'))
        people[ident] = dict(id=ident, name=name, daily_capacity=hours * available / 100,
                             effort=Decimal(0), cost=Decimal(0), revenue=Decimal(0))
    rows = []
    ids = set()
    roles = {}
    for item in scenario['assignments']:
        _fields(item, ['id', 'person_id', 'role', 'effort_hours', 'cost_per_hour', 'sell_per_hour', 'currency'], 'assignment')
        ident = _text(item['id'], 'assignment.id')
        if ident in ids:
            raise ValueError(f'Duplicate assignment id: {ident}')
        ids.add(ident)
        person_id = _text(item['person_id'], 'assignment.person_id')
        if person_id not in people:
            raise ValueError(f'Unknown person: {person_id}')
        if item['currency'] != currency:
            raise ValueError('Mixed currencies are not supported; supply approved converted rates explicitly')
        role = _text(item['role'], 'role')
        hours = _number(item['effort_hours'], 'effort_hours')
        cost_rate = _number(item['cost_per_hour'], 'cost_per_hour')
        sell_rate = _number(item['sell_per_hour'], 'sell_per_hour')
        buffered = hours * factor
        cost = Decimal(_money(buffered * cost_rate))
        revenue = Decimal(_money(buffered * sell_rate))
        for target in (people[person_id], roles.setdefault(role, dict(role=role, effort=Decimal(0), cost=Decimal(0), revenue=Decimal(0)))):
            target['effort'] += buffered
            target['cost'] += cost
            target['revenue'] += revenue
        rows.append(dict(id=ident, person_id=person_id, role=role, base_hours=_quantity(hours),
                         buffered_hours=_quantity(buffered), cost=_money(cost), revenue=_money(revenue)))
    resources = []
    warnings = []
    duration = Decimal(0)
    infeasible = False
    for person in people.values():
        daily = person['daily_capacity']
        capacity = daily * horizon
        days = person['effort'] / daily if daily else (Decimal(0) if not person['effort'] else None)
        if days is None:
            infeasible = True
        else:
            duration = max(duration, days)
        overloaded = person['effort'] > capacity
        if overloaded:
            warnings.append(f"{person['name']}: assigned effort exceeds available hours in the planning horizon")
        resources.append(dict(id=person['id'], name=person['name'], buffered_hours=_quantity(person['effort']),
            capacity_hours=_quantity(capacity), minimum_workdays=None if days is None else _quantity(days),
            overallocated=overloaded, cost=_money(person['cost']), revenue=_money(person['revenue'])))
    cost = sum((p['cost'] for p in people.values()), Decimal(0))
    revenue = sum((p['revenue'] for p in people.values()), Decimal(0))
    return dict(schema_version='1.0.0', status='scenario_only', currency=currency,
        scenario_sha256=canonical_sha256(scenario), inputs=scenario, assignments=rows, people=resources,
        roles=[dict(role=r['role'], buffered_hours=_quantity(r['effort']), cost=_money(r['cost']), revenue=_money(r['revenue'])) for r in roles.values()],
        totals=dict(cost=_money(cost), revenue=_money(revenue), contribution=_money(revenue-cost),
                    margin_percent=_quantity((revenue-cost)/revenue*100) if revenue else None,
                    buffered_hours=_quantity(sum((p['effort'] for p in people.values()), Decimal(0))),
                    minimum_workdays=None if infeasible else _quantity(duration)),
        warnings=warnings, limitations=['Private, unsaved scenario; not an approved offer or staffing commitment.',
            'Contingency increases effort, cost and rate-based revenue equally; it does not set a fixed customer price.',
            'Duration is a resource-capacity lower bound. Dependencies, calendars, leave and task sequencing are not scheduled.',
            'Amounts exclude taxes, travel, third-party charges and currency conversion. Line amounts round half-up to two decimals.'])


def preview_estimate(repository, project_ref, revision, scenario):
    record = repository.get(revision)
    if record.project_ref != project_ref:
        raise ValueError('Project revision belongs to another project')
    result = calculate_estimate(scenario)
    return dict(result, project_ref=project_ref, revision_hash=record.revision_hash)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--schemas', type=Path, required=True)
    parser.add_argument('--project-ref', required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    try:
        value = preview_estimate(ProjectPackageRevisionRepository(args.repository, args.schemas), args.project_ref, args.revision, json.load(sys.stdin))
        print(json.dumps(dict(ok=True, value=value)))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps(dict(ok=False, status=422, error=str(error))))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
