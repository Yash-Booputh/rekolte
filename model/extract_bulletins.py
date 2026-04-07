"""
Harvest Bulletin PDF Extraction Script
Rékolte - CST3990 Final Year Project

Extracts season-end TCH (Tonnes Cane per Hectare) and related metrics from:
- Old format (2008-2019): MSIRI/MCIA tabular format with NORD/EST/SUD/OUEST/CENTRE columns
- New format (2020-2025): Chamber of Agriculture format with estate-level data + sector subtotals

Strategy: Extract the LAST bulletin of each season (cumulative "à ce jour" figures = season total).

Output: season_end_data.csv with columns:
  season, region, tch, surface_harvested, cane_production, sugar_production,
  extraction_rate, tsh, source_file, format
"""

import os
import re
import warnings
import pandas as pd
import pdfplumber

warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_DIR, '..', '..', 'Sugarcane Data')
OLD_DIR = os.path.join(DATA_ROOT, '2008 - 2019')
NEW_DIR = os.path.join(DATA_ROOT, '2020 - 2026')
OUTPUT_CSV = os.path.join(BASE_DIR, 'season_end_data.csv')

REGIONS = ['NORD', 'EST', 'SUD', 'OUEST', 'CENTRE']
# Old format column order in the MSIRI table
OLD_FORMAT_COL_ORDER = ['NORD', 'EST', 'SUD', 'OUEST', 'CENTRE', 'ILE']


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def clean_num(s):
    """Clean a PDF-extracted number string into a float. Returns None if unparseable."""
    if s is None:
        return None
    s = str(s).strip()
    if s in ('-', '', 'nan', 'NaN', 'None'):
        return None
    # Remove thousands separators and stray spaces inside numbers
    s = re.sub(r'(\d)\s+(\d)', r'\1\2', s)   # "1 234" -> "1234"
    s = re.sub(r'(\d)\s*,\s*(\d)', r'\1\2', s)  # "1,234" -> "1234"
    s = s.replace(',', '').strip()
    try:
        return float(s)
    except ValueError:
        return None


def parse_pair(cell_text):
    """
    Parse a cell containing "semaine_val ytd_val" (space-separated pair).
    Returns (semaine, ytd). Each can be None.

    Values in TCH/TSH/extraction-rate cells are clean (e.g. "91.3 72.1").
    Surface and cane cells have space artifacts but we handle those separately.
    """
    if not cell_text:
        return None, None
    text = cell_text.strip().replace('\n', ' ')
    # Extract all float tokens (do NOT collapse digit-space-digit; that corrupts pairs)
    tokens = re.findall(r'-?\d+(?:[.,]\d+)?', text)
    # Normalise each token (remove thousands commas, French decimal comma)
    cleaned = []
    for t in tokens:
        t = re.sub(r'(\d),(\d{3})', r'\1\2', t)   # "1,234" → "1234"
        t = re.sub(r'\b(\d{1,3}),(\d{1,2})\b', r'\1.\2', t)  # "64,8" → "64.8"
        t = t.replace(',', '')
        try:
            cleaned.append(float(t))
        except ValueError:
            pass
    if not cleaned:
        return None, None
    if len(cleaned) == 1:
        return None, cleaned[0]
    # First token = semaine, last token = ytd
    return cleaned[0], cleaned[-1]


# ---------------------------------------------------------------------------
# OLD FORMAT PARSER (2008-2019, MSIRI/MCIA)
# ---------------------------------------------------------------------------
def _extract_row_values(line, min_val=0, max_val=200):
    """
    Extract float numbers from a text line within [min_val, max_val].
    Handles:
    - French decimal commas: '64,8' → 64.8
    - Thousands commas: '1,234' → 1234
    - PDF apostrophe artifacts: "8'1.4" → 81.4
    - Stray spaces in numbers are NOT collapsed (would corrupt adjacent values)
    """
    # Fix "'," artifact: "8',1.4" → "81.4" (apostrophe-comma inside number)
    line = re.sub(r"(\d)'[,](\d)", r'\1\2', line)
    # Fix "'." artifact: "1'.t476" → ignore non-digit after apostrophe
    line = re.sub(r"(\d)'[^0-9]", r'\1', line)
    # Remove simple apostrophe artifacts: "8'1" → "81"
    line = re.sub(r"(\d)'(\d)", r'\1\2', line)
    # Replace French decimal commas: digit,digit where x<=3 digits and y is 1-2 digits
    line = re.sub(r'\b(\d{1,3}),(\d{1,2})\b', r'\1.\2', line)
    # Remove thousands separators (digit,comma,3digits pattern)
    line = re.sub(r'(\d),(\d{3})', r'\1\2', line)
    # Extract all float-like tokens
    nums = re.findall(r'-?\d+(?:\.\d+)?', line)
    vals = []
    for n in nums:
        try:
            v = float(n)
            if min_val <= v <= max_val:
                vals.append(v)
        except ValueError:
            pass
    return vals


def parse_old_format(pdf_path):
    """
    Parse MSIRI-format bulletin using pdfplumber text extraction.
    Robust to PDF layout variations across 2008-2019.

    Column order in old format: NORD, EST, SUD, OUEST, CENTRE, ILE
    Returns dict keyed by region with sub-dict of metrics, or None on failure.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text() or ''
    except Exception as e:
        print(f"  [pdfplumber error] {os.path.basename(pdf_path)}: {e}")
        return None

    lines = text.split('\n')

    def find_ytd_values(pattern, min_val=0, max_val=200):
        """
        Find the line matching pattern and return numeric values on that line.
        If no values on that line, check the line immediately before (current year
        data in the two-row layout) and the line after (also current year sometimes).
        Always returns the first occurrence with >= 5 valid values.
        """
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.IGNORECASE):
                # Case 1: values on same line as label
                vals = _extract_row_values(line, min_val, max_val)
                if len(vals) >= 5:
                    return vals[:6]
                # Case 2: current year data is the line BEFORE the label
                if i > 0:
                    prev_vals = _extract_row_values(lines[i - 1], min_val, max_val)
                    if len(prev_vals) >= 5:
                        return prev_vals[:6]
                # Case 3: values on the next line
                if i + 1 < len(lines):
                    next_vals = _extract_row_values(lines[i + 1], min_val, max_val)
                    if len(next_vals) >= 5:
                        return next_vals[:6]
        return None

    # TCH range 40-130 t/ha; 'jour' OCR often corrupts to 'jouQ'/'jouo' etc.
    tch_vals  = find_ytd_values(r'TCH.*ce.jou|Productivit.*ce.jou', min_val=40, max_val=130)
    # Surface in hectares: regional values 100-20000 ha
    surf_vals = find_ytd_values(r'Superficie.*r.colt.e.*(ce.jou|a ce jour)', min_val=100, max_val=20000)
    # Cane production: wide range
    cane_vals = find_ytd_values(r'Tonnes cannes.*(r.colt.es|recoltees).*(ce.jou|a ce jour)', min_val=1000, max_val=2000000)

    if tch_vals is None:
        print(f"  [TCH not found] {os.path.basename(pdf_path)}")
        return None

    result = {}
    for i, region in enumerate(OLD_FORMAT_COL_ORDER[:5]):  # Skip ILE
        result[region] = {
            'tch': tch_vals[i] if i < len(tch_vals) else None,
            'surface_harvested': surf_vals[i] if surf_vals and i < len(surf_vals) else None,
            'cane_production': cane_vals[i] if cane_vals and i < len(cane_vals) else None,
            'sugar_production': None,
            'extraction_rate': None,
            'tsh': None,
        }

    return result


# ---------------------------------------------------------------------------
# NEW FORMAT PARSER (2020-2025, Chamber of Agriculture)
# ---------------------------------------------------------------------------
def parse_new_format(pdf_path):
    """
    Parse Chamber of Agriculture format using pdfplumber.
    Table on page 1 has all estate data; sector subtotals (NORD/SUD/EST/OUEST/CENTRE)
    are identifiable by walking the entity label list.

    Returns dict keyed by region with sub-dict of metrics, or None on failure.
    """
    REGION_SET = set(REGIONS + ['ILE'])

    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            tables = page.extract_tables()
    except Exception as e:
        print(f"  [pdfplumber error] {os.path.basename(pdf_path)}: {e}")
        return None

    if not tables:
        print(f"  [no tables] {os.path.basename(pdf_path)}")
        return None

    # Find the champs table (has "Champs" or "NORD" in the first cell)
    main_table = None
    for t in tables:
        if t and t[0] and t[0][0]:
            cell0 = str(t[0][0])
            if 'NORD' in cell0 or 'Champs' in cell0 or 'Terra' in cell0:
                main_table = t
                break
    if main_table is None:
        main_table = tables[0]

    if len(main_table) < 4:
        print(f"  [table too small] {os.path.basename(pdf_path)}")
        return None

    # Row 0 col 0: all entity labels joined by \n
    labels_text = main_table[0][0] or ''
    labels = [l.strip() for l in labels_text.split('\n') if l.strip()]

    if not labels:
        print(f"  [no labels] {os.path.basename(pdf_path)}")
        return None

    # Dynamically find column indices from Row 1 headers
    # Row 1: [None, 'Surface récoltée\n(Hectares)', 'Production de canne\n(Tonnes)', ..., 'Tonnes Cannes/Ha\n(TCH)', ...]
    header_row = main_table[1] if len(main_table) > 1 else []
    COL_SURF, COL_CANE, COL_SUGAR, COL_EXTR, COL_TCH, COL_TSH = 1, 2, 3, 4, 5, 6  # defaults

    for ci, cell in enumerate(header_row):
        if not cell:
            continue
        cell_upper = cell.upper()
        if 'SURFACE' in cell_upper or 'HECTARE' in cell_upper:
            COL_SURF = ci
        elif 'PRODUCTION DE CANNE' in cell_upper or 'CANNE\n(TONNES)' in cell_upper:
            COL_CANE = ci
        elif 'PRODUCTION DE SUCRE' in cell_upper:
            COL_SUGAR = ci
        elif "TAUX D'EXTRACTION" in cell_upper or 'EXTRACTION' in cell_upper:
            COL_EXTR = ci
        elif 'TCH' in cell_upper or 'TONNES CANNES/HA' in cell_upper:
            COL_TCH = ci
        elif 'TSH' in cell_upper or 'TONNES SUCRE/HA' in cell_upper:
            COL_TSH = ci

    result = {}
    label_idx = 0

    # Data rows start at index 3 (skip header rows 0,1,2)
    for row in main_table[3:]:
        # Determine how many entities this row covers
        # Use col 1 (surface) as reference; each \n-separated value = one entity
        ref_cell = None
        for ci in [COL_SURF, COL_CANE, COL_TCH]:
            if ci < len(row) and row[ci] and str(row[ci]).strip():
                ref_cell = str(row[ci])
                break

        if ref_cell is None:
            # Completely empty row – skip without advancing label counter
            continue

        entity_values = [v.strip() for v in ref_cell.split('\n') if v.strip()]
        n_entities = len(entity_values)

        for entity_idx in range(n_entities):
            if label_idx >= len(labels):
                break

            label = labels[label_idx]

            if label in REGION_SET and label != 'ILE':
                def get_ytd(col):
                    if col >= len(row) or not row[col]:
                        return None
                    cell_lines = [v.strip() for v in str(row[col]).split('\n') if v.strip()]
                    line = cell_lines[entity_idx] if entity_idx < len(cell_lines) else (cell_lines[-1] if cell_lines else '')
                    _, ytd = parse_pair(line)
                    return ytd

                result[label] = {
                    'tch': get_ytd(COL_TCH),
                    'surface_harvested': get_ytd(COL_SURF),
                    'cane_production': get_ytd(COL_CANE),
                    'sugar_production': get_ytd(COL_SUGAR),
                    'extraction_rate': get_ytd(COL_EXTR),
                    'tsh': get_ytd(COL_TSH),
                }

            label_idx += 1

    return result if result else None


# ---------------------------------------------------------------------------
# Season detection helpers
# ---------------------------------------------------------------------------
def get_bulletin_number_old(filename):
    """Extract bulletin number from old format filename like 'bul14crop19.pdf'."""
    m = re.search(r'bul(\d+)crop', filename, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def get_bulletin_number_new(filename):
    """Extract bulletin number from new format filename like 'BH-24-23-decembre-2023.pdf'."""
    m = re.search(r'BH-(\d+)-', filename, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def find_last_bulletin(folder, fmt):
    """Return (filename, bulletin_number) of the last bulletin in a season folder."""
    try:
        files = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')]
    except FileNotFoundError:
        return None, 0

    if not files:
        return None, 0

    if fmt == 'old':
        numbered = [(f, get_bulletin_number_old(f)) for f in files]
    else:
        numbered = [(f, get_bulletin_number_new(f)) for f in files]

    numbered = [(f, n) for f, n in numbered if n > 0]
    if not numbered:
        return None, 0

    best = max(numbered, key=lambda x: x[1])
    return best


# ---------------------------------------------------------------------------
# Main extraction loop
# ---------------------------------------------------------------------------
def extract_all_seasons():
    rows = []

    # --- OLD FORMAT (2008-2019) ---
    print("=== OLD FORMAT (2008-2019) ===")
    for year in range(2008, 2020):
        folder = os.path.join(OLD_DIR, str(year))
        filename, bul_num = find_last_bulletin(folder, 'old')
        if not filename:
            print(f"  Season {year}: no bulletins found")
            continue

        pdf_path = os.path.join(folder, filename)
        print(f"  Season {year}: parsing {filename} (bulletin {bul_num})...", end=' ')
        data = parse_old_format(pdf_path)

        if not data:
            print("FAILED")
            continue

        print("OK")
        for region in REGIONS:
            if region in data:
                d = data[region]
                rows.append({
                    'season': year,
                    'region': region,
                    'tch': d['tch'],
                    'surface_harvested': d['surface_harvested'],
                    'cane_production': d['cane_production'],
                    'sugar_production': d.get('sugar_production'),
                    'extraction_rate': d.get('extraction_rate'),
                    'tsh': d.get('tsh'),
                    'bulletin_number': bul_num,
                    'source_file': filename,
                    'format': 'old',
                })

    # --- NEW FORMAT (2020-2025) ---
    print("\n=== NEW FORMAT (2020-2025) ===")
    for year in range(2020, 2026):
        folder = os.path.join(NEW_DIR, str(year))
        filename, bul_num = find_last_bulletin(folder, 'new')
        if not filename:
            print(f"  Season {year}: no bulletins found")
            continue

        pdf_path = os.path.join(folder, filename)
        print(f"  Season {year}: parsing {filename} (bulletin {bul_num})...", end=' ')
        data = parse_new_format(pdf_path)

        if not data:
            print("FAILED")
            continue

        print("OK")
        for region in REGIONS:
            if region in data:
                d = data[region]
                rows.append({
                    'season': year,
                    'region': region,
                    'tch': d['tch'],
                    'surface_harvested': d['surface_harvested'],
                    'cane_production': d['cane_production'],
                    'sugar_production': d.get('sugar_production'),
                    'extraction_rate': d.get('extraction_rate'),
                    'tsh': d.get('tsh'),
                    'bulletin_number': bul_num,
                    'source_file': filename,
                    'format': 'new',
                })

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved {len(df)} rows to: {OUTPUT_CSV}")
    return df


if __name__ == '__main__':
    df = extract_all_seasons()

    print("\n=== EXTRACTION SUMMARY ===")
    print(f"Total rows: {len(df)}")
    print(f"Seasons: {sorted(df['season'].unique())}")
    print(f"Regions: {df['region'].unique().tolist()}")
    print(f"\nTCH null count by season:")
    print(df.groupby('season')['tch'].apply(lambda x: x.isna().sum()).to_string())

    print("\n=== SEASON-END TCH per REGION ===")
    pivot = df.pivot(index='season', columns='region', values='tch')
    print(pivot.round(1).to_string())
