import { build, context } from "esbuild";

const options = {
  entryPoints: ["src/goe-steve-card.ts"],
  bundle: true,
  minify: true,
  format: "esm",
  target: "es2021",
  // Bundle straight into the integration's www folder so it ships with the
  // component and gets auto-registered on setup.
  outfile: "../custom_components/goe_steve/www/goe-steve-card.js",
  banner: {
    js: "/* go-e + SteVe Smart Charging card — bundled, do not edit by hand. Source in /card. */",
  },
};

if (process.argv.includes("--watch")) {
  const ctx = await context(options);
  await ctx.watch();
  console.log("watching…");
} else {
  await build(options);
  console.log("built goe-steve-card.js");
}
