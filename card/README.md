# go-e + SteVe Smart Charging — Lovelace cards

Source for the **two** dashboard cards bundled with the integration. The build output is
committed to `../custom_components/goe_steve/www/goe-steve-card.js` (one bundle serves both
cards), which the integration serves and auto-registers on setup — end users never touch
this folder.

## Build

```bash
npm install
npm run build      # → ../custom_components/goe_steve/www/goe-steve-card.js
npm run watch      # rebuild on change
npx tsc --noEmit   # type-check only
```

CI (`.github/workflows/validate.yml`) rebuilds the bundle and fails if the committed output is
stale, so **always commit the rebuilt `goe-steve-card.js` alongside source changes**.

## Layout

- `src/goe-steve-card.ts` — the main *answer strip* card: live charging figure with ring +
  solar/battery/grid source bar, balance line, the brain's reason, state chips (battery-hold
  shield, price verdict, dwell countdowns, phases), plan strip with draggable price target,
  and inline controls (mode, Auto/Hold/Free, reserve line, tunables).
- `src/goe-steve-card-editor.ts` — its visual config editor (`ha-form` + device selector).
- `src/goe-steve-price-card.ts` — the price-forecast chart card with the draggable "cheap"
  threshold (writes the *Cheap price* number).
- `src/goe-steve-price-card-editor.ts` — its visual config editor.
- `src/entities.ts` — discovers the integration's entities for one device (by registry
  `translation_key`, entity_id-suffix fallback).
- `src/localize.ts` — card i18n (EN/DE).

Built with [Lit](https://lit.dev) and bundled with [esbuild](https://esbuild.github.io).
