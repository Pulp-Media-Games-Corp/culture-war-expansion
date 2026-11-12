"""Build index.html for the CULTURE WAR Expansion Files site.

Usage (from the repo root):
    pip install openpyxl pillow
    python src/build.py

Reads src/data/card-ideas.xlsx (the "Copy of Copy of CARD IDEAS" tab by
default), src/template.html, src/assets and src/fonts, and writes a single
self-contained index.html at the repo root.
"""
import base64, datetime, io, json, re, sys
from pathlib import Path

import openpyxl
from PIL import Image
import numpy as np

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
sys.path.insert(0, str(SRC))
from casing import case_block  # noqa: E402

SHEET = 'Copy of Copy of CARD IDEAS'
FACTION_CODE = {'anarchy': 'ana', 'community': 'com', 'technocracy': 'tek',
                'conservative': 'con', 'libertarian': 'lib', 'shadow': 'sha'}
# Sample card art: (card name, faction code) -> asset key
ART = {('CATFISH', 'tek'): 'art_catfish', ('MATCHA LATTE', 'com'): 'art_matcha',
       ('A.I. SLOP', 'tek'): 'art_aislop'}
# SHADOW mark recolour for black backgrounds (darkened 10% on request)
NIHIL_TONES = [round(v * 0.9) for v in (78, 170, 255)]


def clean(s):
    if s is None:
        return ''
    if isinstance(s, float) and s.is_integer():
        s = int(s)
    return re.sub(r'\s+', ' ', str(s).replace(' ', ' ')).strip()


def load_cards():
    wb = openpyxl.load_workbook(SRC / 'data' / 'card-ideas.xlsx', data_only=True)
    ws = wb[SHEET] if SHEET in wb.sheetnames else wb.worksheets[0]
    col = {h: i for i, h in enumerate(c.value for c in ws[1]) if h}
    cards = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not any(v not in (None, '') for v in r[:14]):
            continue
        raw = r[col['Card Name']]
        if isinstance(raw, datetime.datetime):  # Excel turned "6-7" into a date
            name = f'{raw.month}-{raw.day}'
        else:
            name = clean(raw)
        # Brand rule: HEROES by card name only, never the real person parodied
        name = re.sub(r'\s*\([^)]*\)\s*$', '', name).upper()
        faction = clean(r[col['Faction']]).lower()
        code = FACTION_CODE[faction]
        ctype = clean(r[col['Card Type']]).upper()
        unit_type = clean(r[col['Unit Type']]).upper()
        unit_class = clean(r[col['Unit Class']]).upper().replace('/', ' / ')
        event_type = clean(r[col['Event Type']]).upper()
        note = clean(r[col['NOTES']])
        text = clean(r[col['Event Effect']]) or clean(r[col['Unit Abilities']])
        text = case_block(text.replace('p0ut', 'put')) if text else ''
        sub = {'UNIT': unit_type, 'EVENT': event_type,
               'REAL ESTATE': 'SPECIAL' if 'special' in note.lower() else ''}.get(ctype, '')
        cards.append({'name': name, 'faction': code, 'type': ctype, 'sub': sub,
                      'cls': unit_class if ctype == 'UNIT' else '', 'fx': text,
                      'art': ART.get((name, code), '')})
    # unique, hash-safe ids; label same-name variants within a faction
    seen = {}
    for c in cards:
        slug = re.sub(r'[^a-z0-9]+', '-', c['name'].lower()).strip('-') or 'card'
        base = f"card-{slug}-{c['faction']}"
        seen[base] = seen.get(base, 0) + 1
        c['_base'], c['_n'] = base, seen[base]
        c['id'] = base if seen[base] == 1 else f'{base}-{seen[base]}'
    for c in cards:
        if seen[c['_base']] > 1:
            c['ver'] = f"VERSION {c['_n']} OF {seen[c['_base']]}"
        del c['_base'], c['_n']
    return [{k: v for k, v in c.items() if v != ''} for c in cards]


def data_uri(im, size=None, fmt='WEBP', q=88):
    if size:
        im = im.copy()
        im.thumbnail((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, fmt, quality=q, method=6)
    return f'data:image/{fmt.lower()};base64,' + base64.b64encode(buf.getvalue()).decode()


def img(name):
    im = Image.open(SRC / 'assets' / name).convert('RGBA')
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def nihil_dark():
    a = np.asarray(Image.open(SRC / 'assets' / 'nihil_original.png').convert('RGBA')).astype(float)
    tone = np.interp(a[..., 0], [12, 131, 255], NIHIL_TONES)
    out = np.zeros(a.shape, dtype=np.uint8)
    out[..., 0] = out[..., 1] = out[..., 2] = tone.astype(np.uint8)
    out[..., 3] = (np.clip(a[..., 3] / 66.0, 0, 1) * 255).astype(np.uint8)
    o = Image.fromarray(out, 'RGBA')
    return o.crop(o.getbbox())


def load_assets():
    out = {}
    for f in ['ana', 'com', 'tek', 'con', 'lib']:
        out[f'{f}_emblem'] = data_uri(img(f'{f}_main.png'), 560)
        out[f'{f}_icon'] = data_uri(img(f'{f}_icon.png'), 96)
    n = nihil_dark()
    out['sha_emblem'] = data_uri(n, 640)
    out['sha_icon'] = data_uri(n, 112)
    out['globe'] = data_uri(img('globe.png'), 900, q=80)
    out['wordmark'] = data_uri(img('wordmark.png'), 1130)
    out['panther'] = data_uri(img('panther.png'), 360)
    out['g_unit'] = data_uri(img('g_unit.png'), 96)
    out['g_event'] = data_uri(img('g_event.png'), 96)
    out['g_re'] = data_uri(img('g_re.png'), 96)
    for k in ['catfish', 'matcha', 'aislop']:
        im = Image.open(SRC / 'assets' / f'art_{k}.jpg').convert('RGB')
        im.thumbnail((760, 1100), Image.LANCZOS)
        out[f'art_{k}'] = data_uri(im, None, q=84)
    return out


def main():
    cards = load_cards()
    assets = load_assets()
    fav = img('globe.png')
    fav.thumbnail((64, 64))
    buf = io.BytesIO(); fav.save(buf, 'PNG')
    font = lambda f: 'data:font/woff2;base64,' + base64.b64encode((SRC / 'fonts' / f).read_bytes()).decode()
    html = ((SRC / 'template.html').read_text()
            .replace('{{FONT_DISPLAY}}', font('archivo.woff2'))
            .replace('{{FONT_BODY}}', font('courier-prime-bold.woff2'))
            .replace('{{GLOBE_ICON}}', 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode())
            .replace('{{ASSETS}}', json.dumps(assets))
            .replace('{{CARDS}}', json.dumps(cards, ensure_ascii=False)))
    assert '{{' not in html, 'unfilled placeholder in template'
    assert '—' not in html, 'em dash found (brand rule)'
    (ROOT / 'index.html').write_text(html)
    print(f'{len(cards)} cards, {sum(1 for c in cards if c.get("fx"))} with effects, '
          f'{len(html) // 1024} KB -> index.html')


if __name__ == '__main__':
    main()
