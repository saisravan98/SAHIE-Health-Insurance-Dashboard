"""Prepare Census SAHIE Excel exports without loading entire workbooks into memory."""
import argparse
import csv
import json
import re
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
FIELDS = ['year', 'statefips', 'countyfips', 'geocat', 'agecat', 'racecat',
          'sexcat', 'iprcat', 'NIPR', 'NUI', 'PCTUI', 'pctui_moe',
          'state_name', 'county_name', 'source_file']
KEY = FIELDS[:8]


def excel_rows(path):
    """Stream the first worksheet, preserving sparse columns and shared strings."""
    with ZipFile(path) as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            root = etree.fromstring(archive.read('xl/sharedStrings.xml'))
            strings = [''.join(n.itertext()) for n in root]
        wb = etree.fromstring(archive.read('xl/workbook.xml'))
        sheet = wb.find(NS + 'sheets')[0]
        rid = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        rels = etree.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        target = next(n.get('Target') for n in rels if n.get('Id') == rid)
        target = target.lstrip('/') if target.startswith('/') else 'xl/' + target
        with archive.open(target) as stream:
            for _, row in etree.iterparse(stream, events=('end',), tag=NS + 'row'):
                values = []
                for cell in row:
                    letters = re.match(r'[A-Z]+', cell.get('r')).group()
                    index = 0
                    for letter in letters:
                        index = index * 26 + ord(letter) - 64
                    while len(values) < index:
                        values.append('')
                    value = cell.find(NS + 'v')
                    text = value.text if value is not None else ''
                    if cell.get('t') == 's':
                        text = strings[int(text)]
                    elif cell.get('t') == 'inlineStr':
                        text = ''.join(cell.find(NS + 'is').itertext())
                    values[index - 1] = (text or '').strip()
                yield values
                row.clear()
                while row.getprevious() is not None:
                    del row.getparent()[0]


def prepare(raw_dir, output):
    paths = sorted(Path(raw_dir).glob('sahie_*.xlsx'))
    if not paths:
        raise ValueError('Place sahie_2018.xlsx through sahie_2022.xlsx in the input folder.')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.tmp')
    report = {'sources': [], 'rows_written': 0, 'excluded_missing_estimates': 0}
    seen = set()
    try:
        with temporary.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            for path in paths:
                header = None
                written = excluded = 0
                print(f'Reading {path.name}...', flush=True)
                for row in excel_rows(path):
                    if header is None:
                        if row and row[0] == 'year' and 'NIPR' in row:
                            header = row
                            missing = set(FIELDS[:-1]) - set(header)
                            if missing:
                                raise ValueError(f'{path.name}: missing columns {sorted(missing)}')
                        continue
                    if not row or not row[0]:
                        continue
                    record = dict(zip(header, row))
                    if not str(record.get('year', '')).isdigit():
                        raise ValueError(f'{path.name}: unexpected non-data row after header')
                    year = int(record['year'])
                    if not 2018 <= year <= 2022:
                        raise ValueError(f'Unexpected year {year}')
                    for column in KEY:
                        record[column] = int(record[column])
                    # Census explicitly marks Kalawao County estimates unavailable.
                    if (record['statefips'], record['countyfips'], record['geocat']) == (15, 5, 50):
                        excluded += 1
                        continue
                    if any(record.get(c, '') in ('', '.', 'N/A')
                           for c in ['NIPR', 'NUI', 'PCTUI', 'pctui_moe']):
                        excluded += 1
                        continue
                    try:
                        for column in ['NIPR', 'NUI', 'PCTUI', 'pctui_moe']:
                            record[column] = float(record[column])
                    except (ValueError, KeyError) as error:
                        raise ValueError(f'{path.name}: malformed estimate {record}') from error
                    if record['NIPR'] == 0 and record['NUI'] == 0:
                        excluded += 1
                        continue
                    if not (record['NIPR'] > 0 and 0 <= record['NUI'] <= record['NIPR']
                            and 0 <= record['PCTUI'] <= 100 and record['pctui_moe'] >= 0):
                        raise ValueError(f'{path.name}: invalid estimate {record}')
                    expected = 100 * record['NUI'] / record['NIPR']
                    if abs(expected - record['PCTUI']) > 0.11:
                        raise ValueError(f'{path.name}: rate/count mismatch {record}')
                    key = tuple(record[c] for c in KEY)
                    if key in seen:
                        raise ValueError(f'Duplicate demographic/geographic key: {key}')
                    seen.add(key)
                    record['statefips'] = f"{record['statefips']:02d}"
                    record['countyfips'] = f"{record['countyfips']:03d}"
                    record['source_file'] = path.name
                    writer.writerow({c: record[c] for c in FIELDS})
                    written += 1
                if header is None or written == 0:
                    raise ValueError(f'{path.name}: no usable SAHIE records')
                report['sources'].append({'file': path.name, 'rows': written, 'excluded': excluded})
                report['rows_written'] += written
                report['excluded_missing_estimates'] += excluded
                print(f'{path.name}: {written:,} rows; {excluded:,} unavailable rows excluded', flush=True)
        temporary.replace(output)
        output.with_suffix('.quality.json').write_text(json.dumps(report, indent=2))
        return report
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', default='raw_data')
    parser.add_argument('--output', default='processed_sahie.csv')
    args = parser.parse_args()
    print(json.dumps(prepare(args.input_dir, args.output), indent=2))
