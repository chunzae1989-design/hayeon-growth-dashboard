#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parent
CHART = ROOT / 'growth_chart_kr.json'
OUT = ROOT / 'percentile_curves.json'
PCTS = [3, 10, 25, 50, 75, 90, 97]
KINDS = ['height', 'weight', 'bmi']
SEX = 'female'
START_MONTH = 24
END_MONTH = 60


def value_from_lms(L: float, M: float, S: float, pct: float) -> float:
    z = NormalDist().inv_cdf(pct / 100)
    if abs(L) < 1e-9:
        return M * math.exp(S * z)
    return M * ((1 + L * S * z) ** (1 / L))


def main() -> int:
    chart = json.loads(CHART.read_text(encoding='utf-8'))
    samples = chart['samples'][SEX]
    out = {
        'source': chart['_meta']['source'],
        'sourceUrl': chart['_meta']['source_url'],
        'method': 'KDCA 2017 LMS percentile curves, female, monthly samples',
        'ageRangeMonths': [START_MONTH, END_MONTH],
        'percentiles': PCTS,
        'series': {},
    }
    for kind in KINDS:
        rows = {int(float(r['age_months'])): r for r in samples[kind]}
        series = []
        for age in range(START_MONTH, END_MONTH + 1):
            r = rows[age]
            L, M, S = float(r['L']), float(r['M']), float(r['S'])
            item: dict[str, float | int] = {'ageMonths': age}
            for p in PCTS:
                item[f'p{p}'] = round(value_from_lms(L, M, S, p), 2)
            series.append(item)
        out['series'][kind] = series
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(OUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
