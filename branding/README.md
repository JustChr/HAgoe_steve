# Branding

Logo / icon concepts for the integration. Source is SVG; PNGs are rendered from it.

## Options

| File | Concept |
|------|---------|
| `icon-option-1` | Solid teal→green tile, white bolt. Punchy, highest contrast at small sizes. |
| `icon-option-2` | Dark tile, three "phase" bars + accent bolt. Says *3-phase smart charging*. |
| `icon-option-3` | **✅ Chosen.** Duotone gradient tile, deep-slate bolt. Minimal, confident. |
| `icon-option-4` | Monoline bolt + phase ticks on transparent. Airy, lightest weight. |
| `logo-lockup`   | Horizontal mark + "go-e + SteVe / SMART CHARGING" wordmark. |

## Rendering

`sharp` and native renderers fight OneDrive file locks in this folder, so render in a temp dir:

```bash
WORK="$TEMP/goebrand"; mkdir -p "$WORK"
cp *.svg render.mjs "$WORK/"; cd "$WORK"
npm init -y && npm install @resvg/resvg-js @resvg/resvg-js-win32-x64-msvc
node render.mjs && cp *.png "<repo>/branding/"
```

## Using it in HACS

HACS shows the icon/logo from the [home-assistant/brands](https://github.com/home-assistant/brands)
repo, keyed by the integration domain (`goe_steve`). The brands-ready files for the chosen
**Option 3** are rendered (trimmed, per brands CI rules) to:

```
hacs/custom_integrations/goe_steve/
  icon.png      256×256  (full-bleed tile)
  icon@2x.png   512×512
  logo.png      512×194  (wordmark lockup, trimmed)
  logo@2x.png   1024×388
```

To submit: fork [home-assistant/brands](https://github.com/home-assistant/brands), copy this
`custom_integrations/goe_steve/` folder into the repo root, and open a PR. The brand sources are
`icon-brands.svg` (full-bleed icon) and `logo-lockup.svg` (lockup) — edit those and re-render.
