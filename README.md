# CULTURE WAR Expansion Files

Card concept browser for the upcoming CULTURE WAR expansion, served at https://expansion.culturewarthegame.com via GitHub Pages.

- `index.html`: the whole site in one file (fonts, logos, card art and data built in)
- `CNAME`: tells GitHub Pages which custom domain to serve

To update: replace `index.html` with the new version and commit. The site refreshes within a few minutes.

CULTURE WAR™ is published by PM Games. © 2025 PM Games. All rights reserved.

## Rebuilding the page

The live page is built from the files in `src/`:

- `src/data/card-ideas.xlsx`: card data (the "Copy of Copy of CARD IDEAS" tab)
- `src/template.html`: layout, styles and browser logic
- `src/assets/`: faction emblems, logos, game icons, SHADOW mark, sample card art
- `src/fonts/`: Archivo and Courier Prime (brand fallback fonts, SIL Open Font License)
- `src/casing.py`: applies the brand casing rules to effect text

To rebuild: `pip install openpyxl pillow numpy`, then `python src/build.py` from the repo root. It writes `index.html`.
