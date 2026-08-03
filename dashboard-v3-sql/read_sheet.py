#!/usr/bin/env python3
"""
read_sheet.py — Dashboard V3 STEP 1.
Parses the manager's Google-Sheet export ("New Containers to UK - 2026 .xlsx")
with the standard library only (an .xlsx is a zip of XML), and emits the
authoritative Container -> Component SKU mapping that V3 is built from.

The SHEET is the source of truth for which SKUs belong to which container.
Everything else (images, combos, listings, sales) is fetched from the database
using these SKUs -- see build_v3.py.
"""
import json, zipfile, re
from pathlib import Path
from xml.etree import ElementTree as ET

BASE = Path(__file__).resolve().parent
PROJ = BASE.parent
XLSX = PROJ / "dashboard-v3-data" / "New Containers to UK - 2026 .xlsx"
NS   = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RNS  = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

z = zipfile.ZipFile(XLSX)

# shared strings table
shared = []
if "xl/sharedStrings.xml" in z.namelist():
    for si in ET.fromstring(z.read("xl/sharedStrings.xml")):
        shared.append("".join(t.text or "" for t in si.iter(NS+'t')))

# sheet name -> worksheet part
wb   = ET.fromstring(z.read("xl/workbook.xml"))
rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
rid2target = {r.get('Id'): r.get('Target') for r in rels}
sheets = []
for s in wb.iter(NS+'sheet'):
    tgt = rid2target[s.get(RNS+'id')].lstrip('/')
    if not tgt.startswith('xl/'): tgt = 'xl/' + tgt
    sheets.append((s.get('name'), tgt))

def col_of(ref):                       # "BC12" -> "BC"
    return re.match(r'([A-Z]+)', ref).group(1)

def read_sheet(part):
    """-> list of row dicts keyed by column letter"""
    ws = ET.fromstring(z.read(part))
    rows = []
    for row in ws.iter(NS+'row'):
        d = {}
        for c in row.iter(NS+'c'):
            ref, t = c.get('r'), c.get('t')
            v = c.find(NS+'v'); isel = c.find(NS+'is')
            if t == 's' and v is not None:
                val = shared[int(v.text)]
            elif t == 'inlineStr' and isel is not None:
                val = "".join(x.text or "" for x in isel.iter(NS+'t'))
            elif v is not None:
                val = v.text
            else:
                continue
            if val is not None and str(val).strip() != '':
                d[col_of(ref)] = str(val).strip()
        if d: rows.append(d)
    return rows

SKU_RE = re.compile(r'^[A-Z0-9][A-Z0-9+._/-]{2,}$', re.I)

out, report = {}, []
for name, part in sheets:
    if not name.lower().startswith('container'):
        report.append((name, 'skipped (not a container tab)', 0)); continue
    rows = read_sheet(part)
    if not rows:
        report.append((name, 'empty', 0)); continue

    # locate the header row and the SKU / image columns by NAME, not position
    hdr_i, cmap = None, {}
    for i, r in enumerate(rows[:8]):
        low = {k: v.lower() for k, v in r.items()}
        if any(v == 'sku' for v in low.values()):
            hdr_i = i
            for k, v in low.items():
                if v == 'sku':                       cmap['sku'] = k
                elif 'image link' in v:              cmap['img'] = k
                elif v == 'asin':                    cmap['asin'] = k
                elif 'ebay id' in v:                 cmap['ebay'] = k
                elif v == 'amazon':                  cmap['amazon'] = k
                elif v == 'ebay':                    cmap['f_ebay'] = k
                elif v == 'shopify':                 cmap['shopify'] = k
                elif 'varmen' in v:                  cmap['confirm'] = k
                elif 'adams' in v:                   cmap['adams'] = k
            break
    if hdr_i is None or 'sku' not in cmap:
        report.append((name, 'NO SKU COLUMN FOUND', 0)); continue

    seen, items = set(), []
    for r in rows[hdr_i+1:]:
        sku = (r.get(cmap['sku']) or '').strip()
        if not sku or not SKU_RE.match(sku): continue
        key = sku.upper()
        if key in seen: continue          # de-dupe inside a container tab
        seen.add(key)
        flag = lambda k: (r.get(cmap.get(k, ''), '') or '').strip().upper() == 'TRUE'
        # spreadsheet error values (#N/A, #REF!, …) are NOT data -- drop them
        raw_img = (r.get(cmap.get('img', ''), '') or '').strip()
        if raw_img.startswith('#') or not raw_img.lower().startswith(('http://','https://')):
            raw_img = ''
        items.append({
            "sku": sku,
            "sheet_image": raw_img,
            "asins": [a for a in re.split(r'[\s,]+', r.get(cmap.get('asin',''), '') or '') if a],
            "ebay_ids": [a for a in re.split(r'[\s,]+', r.get(cmap.get('ebay',''), '') or '') if a],
            "sheet_amazon": flag('amazon'), "sheet_ebay": flag('f_ebay'),
            "sheet_shopify": flag('shopify'), "confirmed": flag('confirm'),
        })
    out[name] = items
    report.append((name, 'ok', len(items)))

print(f"{'CONTAINER':<16} {'STATUS':<28} SKUs")
for n, s, c in report: print(f"{n:<16} {s:<28} {c}")

allsk = [i['sku'] for v in out.values() for i in v]
print(f"\ncontainers with SKUs : {len(out)}")
print(f"total SKU rows       : {len(allsk)}")
print(f"distinct SKUs        : {len(set(s.upper() for s in allsk))}")
dupes = {}
for c, v in out.items():
    for i in v: dupes.setdefault(i['sku'].upper(), []).append(c)
multi = {k: v for k, v in dupes.items() if len(v) > 1}
print(f"SKUs in >1 container : {len(multi)}")
for k, v in list(multi.items())[:8]: print(f"   {k} -> {v}")

(BASE / "sheet_containers.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(f"\nwrote {BASE/'sheet_containers.json'}")
