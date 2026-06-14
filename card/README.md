# go-e + SteVe Smart Charging — Lovelace card

Source for the dashboard card bundled with the integration. The build output is committed to
`../custom_components/goe_steve/www/goe-steve-card.js`, which the integration serves and
auto-registers on setup — end users never touch this folder.

## Build

```bash
npm install
npm run build      # → ../custom_components/goe_steve/www/goe-steve-card.js
npm run watch      # rebuild on change
npx tsc --noEmit   # type-check only
```

CI (`.github/workflows/validate.yml`) rebuilds the bundle and fails if the committed output is
stale, so always commit the rebuilt `goe-steve-card.js` alongside source changes.

## Layout

- `src/goe-steve-card.ts` — the card: header/reason, energy-flow SVG, controls, sessions.
- `src/goe-steve-card-editor.ts` — the visual config editor (`ha-form` + device selector).
- `src/entities.ts` — discovers the integration's entities from one device.

Built with [Lit](https://lit.dev) and bundled with [esbuild](https://esbuild.github.io).
