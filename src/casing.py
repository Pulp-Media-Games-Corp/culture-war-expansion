"""Brand Standards section 3a casing for effect / ability text.

Each effect text is treated as one block:
- UNIT(S), EVENT(S), CAPITAL, REAL ESTATE and UNIT classes: full caps on first
  use in the block, Title Case after that.
- CYBER, HERO, BASE, COMMON, MOD(S), FLASH, HAPPENING, OPERATION(S), LIFE,
  COUNTER-ATTACK: always caps.
- "Modded" is left as written (matches printed First Edition cards).
- Sheet shorthand "Cyber Unit Unit(s)" / "Cyber Unit unit" means a CYBER UNIT.
"""
import re

FIRST_USE = {
    'real estate': ('REAL ESTATE', 'Real Estate'),
    'units': ('UNITS', 'Units'), 'unit': ('UNIT', 'Unit'),
    'events': ('EVENTS', 'Events'), 'event': ('EVENT', 'Event'),
    'capital': ('CAPITAL', 'Capital'),
}
CLASSES = ['artist', 'academic', 'criminal', 'business', 'citizen', 'police',
           'media', 'political', 'technocrat', 'outcast', 'athlete', 'military']
ALWAYS = {'cyber': 'CYBER', 'hero': 'HERO', 'heroes': 'HEROES', 'base': 'BASE',
          'common': 'COMMON', 'mod': 'MOD', 'mods': 'MODS', 'flash': 'FLASH',
          'happening': 'HAPPENING', 'operation': 'OPERATION',
          'operations': 'OPERATIONS', 'life': 'LIFE',
          'counter-attack': 'COUNTER-ATTACK'}
FACTIONS = ['anarchy', 'community', 'technocracy', 'conservative', 'libertarian']

def key_of(word):
    w = word.lower()
    if w in ('unit', 'units'):
        return 'unit'
    if w in ('event', 'events'):
        return 'event'
    return w

terms = sorted(list(FIRST_USE) + CLASSES + list(ALWAYS) + FACTIONS, key=len, reverse=True)
PAT = re.compile(r'(?<![A-Za-z])(' + '|'.join(re.escape(t).replace(r'\ ', r'\s+') for t in terms) + r')(?![A-Za-z])', re.I)

def case_block(text):
    # sheet shorthand: "Cyber Unit Units" / "Cyber Unit unit" -> CYBER + Unit(s)
    text = re.sub(r'\bCyber Unit (?=units?\b)', 'Cyber ', text, flags=re.I)
    text = re.sub(r'\bUNITs\b', 'UNITS', text)
    text = re.sub(r'\bEVENTs\b', 'EVENTS', text)
    seen = set()

    def rep(m):
        raw = m.group(1)
        w = re.sub(r'\s+', ' ', raw.lower())
        if w in ALWAYS:
            return ALWAYS[w]
        if w in FACTIONS:
            return w.title()
        k = key_of(w)
        if w in FIRST_USE:
            up, title = FIRST_USE[w]
        else:  # UNIT class
            up, title = w.upper(), w.title()
        if k in seen:
            # later use: Title Case, but keep caps the author already set (both are allowed)
            return raw if raw.isupper() else title
        seen.add(k)
        return up
    text = PAT.sub(rep, text)
    # sentence starts that were typed lowercase
    text = re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
    return text

if __name__ == '__main__':
    import json, sys
    cards = json.load(open(sys.argv[1]))
    for c in cards:
        if c.get('fx'):
            new = case_block(c['fx'])
            print(f"{c['name']} [{c['faction']}]\n  OLD: {c['fx']}\n  NEW: {new}\n")
