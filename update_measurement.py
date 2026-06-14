#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from growth_calc import annotate_measurement

SEOUL = ZoneInfo('Asia/Seoul')
ROOT = Path('/Users/na/HermesProjects/hayeon-growth-dashboard')
DATA = ROOT / 'data.json'
PRIVATE = ROOT / '.private_child.json'


def parse_number(pattern: str, text: str) -> float | None:
    m = re.search(pattern, text, re.I)
    return float(m.group(1)) if m else None


def load_birth_date() -> str:
    if PRIVATE.exists():
        data = json.loads(PRIVATE.read_text(encoding='utf-8'))
        if data.get('birthDate'):
            return data['birthDate']
    public = json.loads(DATA.read_text(encoding='utf-8'))
    if public.get('child', {}).get('birthDatePrivateHint'):
        return public['child']['birthDatePrivateHint']
    raise SystemExit('birthDate missing')


def main() -> int:
    ap = argparse.ArgumentParser(description='Add Hayeon growth measurement')
    ap.add_argument('--text', help='Raw text like: 하연 키 90cm 몸무게 14kg')
    ap.add_argument('--date', default=datetime.now(SEOUL).strftime('%Y-%m-%d'))
    ap.add_argument('--height-cm', type=float)
    ap.add_argument('--weight-kg', type=float)
    ap.add_argument('--note', default='Telegram 입력')
    args = ap.parse_args()

    height = args.height_cm
    weight = args.weight_kg
    if args.text:
        height = height or parse_number(r'키\s*([0-9]+(?:\.[0-9]+)?)\s*cm?', args.text)
        weight = weight or parse_number(r'(?:몸무게|체중)\s*([0-9]+(?:\.[0-9]+)?)\s*kg?', args.text)
    if height is None or weight is None:
        raise SystemExit('height/weight required')

    data = json.loads(DATA.read_text(encoding='utf-8'))
    birth_date = load_birth_date()
    row = {
        'date': args.date,
        'heightCm': round(height, 1),
        'weightKg': round(weight, 1),
        'source': 'Telegram',
        'note': args.note,
    }
    row = annotate_measurement(row, birth_date, 'female')
    rows = data.setdefault('measurements', [])
    rows[:] = [r for r in rows if r.get('date') != args.date]
    rows.append(row)
    rows.sort(key=lambda r: r.get('date', ''))
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'updated', 'item': row}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
