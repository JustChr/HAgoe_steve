# Branding

Logo / icon concepts for the integration. Source is SVG; PNGs are rendered from it.

## Options

| File | Concept |
|------|---------|
| `icon-option-1` | Solid teal→green tile, white bolt. Punchy, highest contrast at small sizes. |
| `icon-option-2` | Dark tile, three "phase" bars + accent bolt. Says *3-phase smart charging*. |
| `icon-option-3` | **✅ Chosen.** Duotone gradient tile, deep-slate bolt. Minimal, confident. |
| `icon-option-4` | Monoline bolt + phase ticks on transparent. Airy, lightest weight. |
| `logo-lockup`   | Horizontal mark + "go-e + SteVe / SMART CHARGING" wordmark (transparent — for the brands `logo.png`). |
| `logo-banner`   | The lockup on a deep-slate panel. Self-contained, reads on light **and** dark backgrounds — used at the top of `README.md` / `info.md`. |

## Rendering

`sharp` and native renderers fight OneDrive file locks in this folder, so render in a temp dir:

```bash
WORK="$TEMP/goebrand"; mkdir -p "$WORK"
cp *.svg render.mjs "$WORK/"; cd "$WORK"
npm init -y && npm install @resvg/resvg-js @resvg/resvg-js-win32-x64-msvc
node render.mjs && cp *.png "<repo>/branding/"
```

## Brand images in Home Assistant and the Marketplace

Since Home Assistant 2026.3 a custom integration ships its own brand images in a `brand/`
folder; HA serves them locally (they win over the brands CDN) and the Marketplace reads them
from the integration's latest release. No submission to home-assistant/brands is needed. The
rendered **Option 3** files live in `custom_components/goe_steve/brand/`:

```
icon.png          256×256   full-bleed tile (bright enough for light and dark themes)
icon@2x.png       512×512
logo.png          512×194   wordmark lockup, trimmed, dark text for light backgrounds
logo@2x.png       1024×388
dark_logo.png     512×194   same lockup, light text for dark backgrounds
dark_logo@2x.png  1024×388
```

Rules (brands spec): PNG, transparent, trimmed to no padding; icon square 256/512; logo
landscape with shortest side 128–256 (256–512 for @2x). Sources: `icon-brands.svg`,
`logo-lockup.svg`, `logo-lockup-dark.svg` — edit those and re-render (the script writes to a
`brand/` folder in the temp dir; copy it into `custom_components/goe_steve/`).

The files only become visible to Marketplace users once they are part of a **release**.
