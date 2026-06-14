#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHART = ROOT / 'growth_chart_kr.json'
DAYS_PER_MONTH = 365.25 / 12


def age_months(birth: str, measured: str) -> float:
    b = date.fromisoformat(birth)
    m = date.fromisoformat(measured)
    return round((m - b).days / DAYS_PER_MONTH, 2)


def _interp(samples: list[dict], age: float) -> dict:
    rows = sorted(samples, key=lambda r: float(r['age_months']))
    lo = max((r for r in rows if float(r['age_months']) <= age), key=lambda r: float(r['age_months']))
    hi = min((r for r in rows if float(r['age_months']) >= age), key=lambda r: float(r['age_months']))
    if float(lo['age_months']) == float(hi['age_months']):
        return {k: float(lo[k]) for k in ['age_months', 'L', 'M', 'S']}
    t = (age - float(lo['age_months'])) / (float(hi['age_months']) - float(lo['age_months']))
    return {k: float(lo[k]) + (float(hi[k]) - float(lo[k])) * t for k in ['age_months', 'L', 'M', 'S']}


def percentile(sex: str, kind: str, age: float, value: float) -> dict:
    chart = json.loads(CHART.read_text(encoding='utf-8'))
    lms = _interp(chart['samples'][sex][kind], age)
    L, M, S = lms['L'], lms['M'], lms['S']
    z = math.log(value / M) / S if abs(L) < 1e-9 else ((value / M) ** L - 1) / (L * S)
    pct = 0.5 * (1 + math.erf(z / math.sqrt(2))) * 100
    return {
        'value': round(value, 2),
        'median': round(M, 2),
        'z': round(z, 2),
        'percentile': round(pct, 1),
        'band': band(pct),
    }


def band(p: float) -> str:
    if p < 3:
        return '3백분위 미만'
    if p <= 10:
        return '3~10백분위'
    if p <= 25:
        return '10~25백분위'
    if p <= 75:
        return '25~75백분위'
    if p <= 90:
        return '75~90백분위'
    if p <= 97:
        return '90~97백분위'
    return '97백분위 초과'


def annotate_measurement(row: dict, birth_date: str, sex: str = 'female') -> dict:
    age = age_months(birth_date, row['date'])
    height = float(row['heightCm'])
    weight = float(row['weightKg'])
    bmi = weight / ((height / 100) ** 2)
    row['ageMonths'] = age
    row['benchmarks'] = {
        'source': 'KDCA 2017 Growth Chart / Severance percentile guide',
        'sourceUrl': 'https://www.kdca.go.kr/kdca/5458/subview.do',
        'method': 'LMS interpolated by age in months',
        'height': percentile(sex, 'height', age, height),
        'weight': percentile(sex, 'weight', age, weight),
        'bmi': percentile(sex, 'bmi', age, bmi),
    }
    return row
