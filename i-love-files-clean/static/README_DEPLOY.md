# I LOVE FILES — "Dispatch" Broadsheet Re-skin (v2, refined)

A full visual redesign of your file-conversion SaaS in the warm-parchment
broadsheet style (matching musthaque.netlify.app), tuned for clean contrast and
comfortable daily use — WITHOUT changing any app logic, IDs, or API calls.

## What v2 fixes (from the first version)
- Cleaner light mode: page and cards now separate crisply (warm-white cards on a
  parchment page) instead of the muddy same-tone tan.
- Calmer dark mode: card surface is a cleaner warm-charcoal, and the tool format
  badges (W, X, P, DWG...) are toned down so they read as ink stamps, not loud blocks.
- Balanced filter pills: all pills share one style; the active pill is ember-red.
- Lighter paper grain so nothing looks dull.
- New CRISP logo: sharp vector recreation of your heart + pipe/valve/CAD emblem
  (logo-icon.png, favicon.png, favicon.ico included) - no blur at any size.

## Kept exactly as-is (as requested)
- Every file-conversion tool icon/badge stays in its original colour and text.
- Your original logo and favicon are untouched.

## New speed feature for returning users
- A "Recent Dispatches - One-Click Repeat" strip above the tool grid remembers your
  last 6 tools (stored locally in the browser) and re-launches any in one click.
  Chip icons are pulled live from your real tool cards, so they always match.

## Files in this folder
- index.html         -> Replace your current index.html (two lines added only).
- broadsheet-skin.css -> New. Put in your /static/ folder.
- broadsheet-speed.js -> New. Put in your /static/ folder.
- logo-icon.png      -> New crisp logo. Overwrite /static/logo-icon.png.
- favicon.png        -> New crisp favicon. Overwrite /static/favicon.png.
- favicon.ico        -> New crisp favicon. Overwrite /static/favicon.ico.

Your existing styles.css and app.js are UNCHANGED.
The skin loads AFTER styles.css, so it only overrides appearance.

## Install (matches your current /static/ setup)
1. Copy broadsheet-skin.css and broadsheet-speed.js into your static/ directory.
2. Replace index.html with the one in this folder.
3. Hard-refresh (Ctrl/Cmd+Shift+R) to clear the old CSS cache.

All API endpoints (/api/convert, /api/cad/batch-plot, auth, billing, quota) and
every onclick handler work exactly as before.

## Reverting
Remove these two lines from index.html:
  <link rel="stylesheet" href="/static/broadsheet-skin.css">
  <script src="/static/broadsheet-speed.js"></script>
The app returns to its previous look instantly. Nothing else was touched.
