# 淡墨浓秋 · Ink Autumn — Theme Design Spec

Theme id: `ink-autumn`
Names: 淡墨浓秋 / Ink Autumn

A Leo AI Studio theme, sitting beside `deep-sea-molten-orange` and
`amethyst-teal` in `theme/themes.json`. Nothing about it is special-cased in
application code: the shell resolves it, upstream components consume tokens, and
`theme/leo.css` is the only place that knows what those tokens contain.

---

## Theme Freeze

| Field | Frozen result |
|---|---|
| Theme | 淡墨浓秋 / Ink Autumn (`ink-autumn`) |
| Version | v1 |
| Status | ACCEPTED & FROZEN |
| Freeze date | 2026-09-05 |
| Theme acceptance | PASS |
| Runtime integration | PASS |
| Default-theme integration | PASS — first-run default is `ink-autumn` |
| Settings selection and persistence | PASS — registry-driven selection, save, fresh store instance and page reload |
| Desktop/mobile acceptance | PASS — existing 1440×900 and 390×844 acceptance matrix |
| Light/dark acceptance | PASS — Home, Workspace, Chat and Settings in both modes |
| Package/deploy integration | PASS — clean committed build and installed application checked |
| Release verifier | PASS — 11 PASS / 0 FAIL / 0 NOT TESTED for the isolated freeze baseline described below |

### Frozen boundary

No further palette changes, background-art changes, visual polishing, spacing /
opacity / decoration adjustments for appearance, or new theme-owned visual
features are permitted. Ordinary changes in aesthetic preference do not reopen
Ink Autumn v1. Changes are allowed only for:

1. A confirmed visual bug.
2. A readability or accessibility regression.
3. A runtime compatibility bug.
4. A packaging or deployment regression.
5. A Leo AI global design-system migration.

### Integration evidence and correction

This freeze found one real integration defect that the earlier handcrafted
preview pages did not exercise: `SettingsStore.state_for_shell()` and the
`ShellApi` sanitizer omitted the registry catalog, so the workbench Settings
consumer received no themes; the launcher shell also retained two static theme
cards. The separate integration fix exposes allowlisted registry metadata and
uses the existing shell card classes/styles to render the catalog. It does not
change theme colors, artwork, CSS or layout styling.

The focused suite passes **290 tests**, covering runtime, settings store/API,
readability, build reproducibility, UI/API contracts, startup and four Chromium
Settings DOM cases (shell/workbench × zh/en). The DOM cases use the production
Settings code and real API/store with temporary user data: select each theme,
save `ink-autumn`, recreate the store, reload the page and check the persisted
appearance. Existing user settings and credentials are not changed.

The deployed executable's 14 `leo_shell` modules were checked against committed
source and loaded directly from its embedded archive for the same four DOM
cases. Runtime injection and shell rendering resolve assets from the actual
installed `theme/` directory, in both locales. The package contract passes for
315 launcher files, 21 critical files and 24 archive modules. These checks are
Chromium DOM / real API-store integration evidence, not a claim of a new full
native WebView2 navigation or visual-acceptance run. The existing 16 desktop /
mobile, light / dark preview images are retained as the visual evidence.

### Release baseline and evidence boundary

The freeze release is on `codex/ink-autumn-v1-freeze`, based on `d58dffe` plus
the integration-only commit `df65d04` and this documentation. Its counterpart
on shared `master` is integration commit `c524c83`. During this task, independent
research-SOP commits landed on shared `master`; they are preserved there and
are deliberately not included or deployed by this theme freeze. No deployed
skills were overwritten to obtain a passing result.

The strict PASS belongs to the isolated, clean freeze checkout and its measured
installed artifact, **not** to the concurrently advancing, governance-dirty
shared `master`. `manifests/build-current.json` records the exact freeze build
commit and installed hashes. Evidence is retained under
`docs/manual-acceptance-evidence/theme-ink-autumn/freeze-v1/`, including the
pre-integration manifest, intermediate failures, build/deploy logs, the focused
test log and final verification logs. When verifying from a worktree, explicitly
set `LEO_APP_ROOT` as well as `--app-root`: the nested skills verifier obtains
its installation target from the environment. An intermediate check without
that environment override targeted the worktree's nonexistent sibling install;
its failure log is retained, not counted as deployed drift.

Ink Autumn's own newly added theme-asset provenance is closed. Leo AI's global
**F-008 remains PARTIAL**: the 10 historical runtime assets listed in section 10
remain independent provenance-governance work, not Ink Autumn v1 acceptance
blockers. The existing portability governance test remains a non-theme failure
(1 failed / 8 passed, historical Windows home paths in the compliance audit).
Neither item reopens Ink Autumn v1, and verifier PASS does not claim that these
global governance obligations are complete. No existing governance files were
modified or staged. The repository has no established theme-tag convention;
documentation and commits define this freeze, without inventing a tag scheme.

---

## 1. Intent

> 中国传统纸墨美学 × 现代 AI / 科研工作台

A research workbench that happens to be printed on 宣纸, not a 古风 website.
Traditional material is the *ground*: paper, ink wash, one cinnabar pigment,
generous 留白. Everything on top of it is a modern tool — dense, legible, quiet.

Three ordered tie-breakers, applied whenever the design had to choose:

1. Readability beats visual invention.
2. 留白 beats added elements.
3. Modern tool-feel beats traditional decoration.

Explicitly not in this theme: 灯笼, 祥云, 龙凤, scroll frames, calligraphy
banners, stacked seals, brush cursors, blue/violet "tech" gradients, neon,
pure-white SaaS cards, pure-black panels.

---

## 2. The three masters

Delivered as three 1672×941 (16:9) images. They are the visual母版, not
wallpaper: the palette below is measured from them, not invented next to them.

| Master | Ships as | Scene |
|---|---|---|
| `ink-autumn-branch.src.png` | `ink-autumn-branch.webp` | **Home / Welcome** — the rising branch |
| `ink-autumn-tree.src.png` | `ink-autumn-tree.webp` | **Knowledge / Memory** — the rooted tree (reserved for Leo Tree) |
| `ink-autumn-branch-warm.src.png` | `ink-autumn-branch-warm.webp` | **Workspace / Research** — the warm branch variant |

**Non-destructive contract.** Masters are stored byte-identical under
`assets/backgrounds/` and are never edited. `tools/build_backgrounds.py` renders
each to WebP at the *same* dimensions, crop and colours; the only transformation
is compression, and both `build` and `verify` re-decode the output and fail if
the artwork was tinted (`MAX_TINT_DRIFT = 0.5/255`) or the paper grain scrubbed
(`MAX_GRAIN_DRIFT = 4.0/255`). Measured tint drift is 0.24–0.37/255.

Presentation may only use `cover` / `position` / `opacity` / crop — no recolour,
no filter, no blur of the artwork itself.

### Measured source values

Sampled across all three masters:

- paper ground: `#E8D8C0`–`#E8DCC4`, H 36–38°, S 15–18%, V 89–91%
- paper highlight: `#F2E3CC`–`#F5E9D1`
- deep paper: `#D7C7A8`–`#DBD0BC`
- darkest ink present: `#68594A`, H 30°, S 29%, V 41%
- mid ink: `#887B6B`, `#B4A794`
- full hue range of the artwork: **H 24–41° only** — one warm family, nothing else

The UI ink extends this family darker (the masters are washes; body text needs
more density), and the cinnabar accent is designed *into* the same family rather
than imported from outside it.

---

## 3. Token architecture

Two layers, and business components only ever see the second.

```
theme/leo.css
  layer 1  semantic  --leo-*         authored here, the theme's own vocabulary
  layer 2  contract  --bg, --ink…    upstream OpenAI4S token names, mapped from layer 1
```

Layer 1 is the vocabulary requested in the brief; layer 2 is what
`upstream/OpenAI4S/.../style.css` already consumes. Mapping one onto the other
means the theme is authored once, in paper-and-ink terms, and no upstream
component is edited to understand it. Leo Tree can later bind straight to
layer 1.

| Semantic (layer 1) | Role | Maps to (layer 2) |
|---|---|---|
| `--leo-background` | app ground, the 装裱 mount | `--bg`, `--bg-100` |
| `--leo-background-muted` | recessed ground, gutters | `--bg-300` |
| `--leo-paper` | reading surface, cards | `--bg-000`, `--card`, `--panel` |
| `--leo-paper-elevated` | modals, popovers | `--panel` (dialog scope) |
| `--leo-panel-background` | sidebar / dock chrome | `#sidebar`, `#rightdock` |
| `--leo-input-background` | fields, composer | `--bg-000` in input scope |
| `--leo-code-background` | code blocks, `pre` | `--bg-200` |
| `--leo-ink` | body text | `--ink`, `--text-000` |
| `--leo-ink-secondary` | secondary text | `--text-200` |
| `--leo-ink-muted` | meta, placeholder | `--text-400`, `--muted`, `--faint` |
| `--leo-border` | structural hairlines | `--border-card`, `--line2` |
| `--leo-border-subtle` | in-surface separators | `--border`, `--line` |
| `--leo-accent` | 朱砂 — links, focus, active | `--accent`, `--accent-fill` |
| `--leo-accent-hover` | pressed / hover cinnabar | `--clay-em` |
| `--leo-accent-muted` | cinnabar wash for fills | `--accent-line` |
| `--leo-selection` | text selection ground | `::selection` |

### Light palette (verified contrast)

| Token | Value | on paper | on background |
|---|---|---|---|
| `--leo-background` | `#E7DAC4` | — | — |
| `--leo-background-muted` | `#DFD0B6` | — | — |
| `--leo-paper` | `#F2E9DA` | — | — |
| `--leo-paper-elevated` | `#F8F1E6` | — | — |
| `--leo-code-background` | `#EBE0CD` | — | — |
| `--leo-input-background` | `#F7F0E3` | — | — |
| `--leo-ink` | `#2B2420` | **12.68** | 11.06 |
| `--leo-ink-secondary` | `#544A40` | **7.18** | 6.26 |
| `--leo-ink-muted` | `#635647` | **5.91** | 5.16 |
| `--leo-accent` | `#903525` | **6.41** | 5.60 |
| `--leo-accent-hover` | `#832F20` | 7.29 | 6.36 |
| clay (secondary pigment) | `#A8593B` | 4.20 | 3.66 |
| clay-em (clay as text) | `#8C4227` | 5.97 | 5.21 |
| success | `#4A6B36` | 5.06 | 4.42 |
| danger | `#973229` | 6.22 | 5.43 |
| warning | `#7E5A1C` | 5.18 | 4.52 |

Body text is AAA on every ground. Secondary is AAA. Muted, accent and every
status colour clear AA (4.5) on every ground they are used on. `clay` is a fill
colour; `clay-em` is its text form.

Both the cinnabar and the muted ink are one step deeper than the first pass.
They have to clear AA not only on a flat swatch but against the darkest stroke
of the artwork showing through the scene (§6), and
`tests/test_theme_readability.py` failed them until they did.

### Dark palette — 「夜纸」

Warm near-black, never `#000`. Ink and paper swap roles; the pigment family does
not change.

| Token | Value | on `--leo-paper` |
|---|---|---|
| `--leo-background` | `#17130F` | — |
| `--leo-background-muted` | `#120F0C` | — |
| `--leo-paper` | `#1F1A15` | — |
| `--leo-paper-elevated` | `#272119` | — |
| `--leo-ink` | `#EDE3D0` | 13.56 |
| `--leo-ink-secondary` | `#C6B7A0` | 8.78 |
| `--leo-ink-muted` | `#9A8C79` | 5.26 |
| `--leo-code-background` | `#1B1712` | — |
| `--leo-accent` | `#D2705A` | 5.10 |
| `--leo-accent-hover` | `#E08B75` | 6.67 |

### Tool hues (`--k-*`)

Upstream ships 14 saturated hues (magenta, cobalt, violet…) for tool cards.
They are remapped onto traditional pigments at low saturation — 墨, 赭石, 花青,
苔绿, 朱砂 — so the activity stream still colour-codes but reads as ink washes.
Every remapped hue holds ≥ 4.0 contrast on paper, background and code ground in
light, and ≥ 5.1 in dark.

### Syntax colours

Upstream hardcodes `#a626a4` magenta and `#3d6fe0` blue for `.tok-*`. Both are
overridden in this theme:

| Token | Light | Dark | Pigment |
|---|---|---|---|
| `.tok-kw` | `#9A3B2A` | `#D2705A` | 朱砂 — keyword as 朱批 |
| `.tok-str` | `#4A6B36` | `#8DAE74` | 苔绿 |
| `.tok-com` | `#756857` | `#8A7E6E` | 淡墨, italic |
| `.tok-num` | `#835C21` | `#C9A45E` | 赭石 |
| `.tok-fn` | `#3F5A72` | `#8FA5BA` | 花青 |

---

## 4. Typography

Unchanged. `Leo Inter` + `Leo Noto Sans SC` for UI, `Leo Space Grotesk` for the
wordmark and display headings, `Leo JetBrains Mono` for code — the same four
faces every Leo theme uses, at the same sizes and the same tracking.

This is deliberate. A theme that also swaps the type is not a theme, it is a
second design system: switching away would change line breaks, wrap points and
the vertical rhythm of every document in the app. Ink Autumn changes colour,
surface, border and radius, and nothing that moves a glyph.

---

## 5. Geometry, border, shadow

Paper does not float.

| | Value | Rationale |
|---|---|---|
| `--radius` | `5px` | tighter than upstream's 6 — a sheet, not a pill |
| `--radius-card` | `9px` | down from 12 |
| `--radius-lg` | `13px` | down from 16 |
| `--shadow-card` | hairline ring + `0 1px 2px` at 3% | a sheet resting on a sheet |
| `--shadow-soft` | hairline ring only | most surfaces need no shadow at all |
| `--shadow-pop` | `0 12px 34px` at 12% | dialogs only |

**Border carries the structure, shadow only whispers.** Every card is a
hairline-bordered paper block on paper. Hover never glows: it shifts the ground
by one paper step, or draws a 1px cinnabar rule on the leading edge.

---

## 6. Background scenes

`body` carries a fixed, `cover`-positioned master plus a paper-coloured scrim
layer stacked above it in the same `background` shorthand. The scrim is how
opacity is applied without touching the artwork.

| Scene | Master | Presence on the bare ground | Behind running text |
|---|---|---|---|
| Home (`#dashboard` visible) | `ink-autumn-branch` | 14% light / 8% dark | n/a — dashboard text lives in cards |
| Workspace (`#workspace` visible) | `ink-autumn-branch-warm` | 14% (sidebar 2%, dock 3%) | 4.8%, via `#main`'s own paper scrim |
| Workspace, empty session | `ink-autumn-branch-warm` | 14% | 6.7% — the scrim opens up when there is no running text |
| Knowledge (settings content pane) | `ink-autumn-tree` | 11% light / 5% dark | n/a — a masked corner layer, not a ground |

Those numbers are not documentation: `tests/test_theme_readability.py` composites
each of them against the masters' darkest stroke (and, at night, their brightest
paper) and fails the build if any ink drops below its floor.

The knowledge scene is a masked layer rather than a background with a scrim over
it. A scrim dilutes an image but cannot stop it being a rectangle, and on night
paper a pale master at any opacity reads as a lit block with four corners; a
radial mask dissolves them.

Scene selection is by `body:has(#dashboard:not(.hidden))` etc. — no JS, no class
plumbing, no upstream edit.

**Readability protection.** The reading surfaces are lighter than the ground and
translucent, not transparent: the message column, cards and composer sit on
`--leo-paper` at 88–94% alpha, so the botanical shows through as texture and
never as a competing edge. The artwork's own mass sits bottom-right, where the
layout keeps gutters.

---

## 7. Decorative language

Ceiling: **at most two decorative marks per screen.** 宁可没有，也不要堆。

Everything new is inline SVG in `leo.css` (a few hundred bytes each), authored in
the masters' language — one weight, one pigment, no fills.

| Asset | Where | Notes |
|---|---|---|
| 淡墨分割线 `--leo-rule-ink` | `.md hr`, settings group separators | a wash that thins at both ends, not a 1px line |
| 朱砂小印 | after the wordmark, on the baseline | 5px cinnabar square — a seal follows a signature; it is not a badge above it |
| cinnabar edge rule | active tab / session / theme card | `inset 2px 0 0` instead of a filled pill |
| 研究痕迹 `--leo-trace` | empty session only | decaying sine + gaussian + logistic, 5% light / 7% dark. Not on the dashboard: a screen that already carries a whole branch is allowed one mark, and the branch is it |
| 水墨节点 `--leo-node-mark` | file tree / artifact empty states | three dots and two edges |
| thinking pulse | existing spinner | ink-drop breathing, `prefers-reduced-motion` respected |

### Research traces

PDE curves, gaussians, node graphs and matrix rules are allowed — this is Leo AI,
not a heritage product — but only at the weight the masters use for their own
faint marks: **淡, 弱, 若隐若现**, like a note left on the paper. They are never
chart-like, never labelled, never above 6% opacity.

---

## 8. Leo Tree reservation

Leo Tree will need `TreeNode`, `Section`, `Edge`, `Progress`, `Review`,
`KnowledgeCard`. This theme exports the vocabulary those will bind to, already
defined and already themed:

```
--leo-tree-node, --leo-tree-node-active, --leo-tree-edge,
--leo-tree-canvas, --leo-tree-progress, --leo-tree-progress-track,
--leo-tree-review, --leo-tree-card, --leo-tree-card-border
```

They are defined in both light and dark, derived from the same paper/ink/cinnabar
values, and `ink-autumn-tree.webp` is already registered as the knowledge ground.
Nothing consumes them yet — the point is that Leo Tree will not need a second
palette, and the 树 metaphor (植物 / 知识结构 / 长期成长) already has its artwork.

---

## 9. Switching

- Registered in `theme/themes.json` alongside the existing two, `builtin: true`.
- `default_theme` is now `ink-autumn`, so a fresh install opens on it.
- `settings_store._default_theme_id()` reads that field instead of a hardcoded
  id, so the shipped default is a theme-layer decision.
- An existing `user/appearance.json` still wins: nobody is moved off the theme
  they chose.
- Settings → 外观 lists all three; switching away restores the previous theme
  exactly, because every Ink Autumn rule is scoped under
  `html[data-leo-theme="ink-autumn"]`.

---

## 10. Asset provenance — Grok F-008

F-008 (UNVERSIONED PRODUCT ASSET) asks whether a shipped asset can be traced to
a committed source. `tools/theme_asset_provenance.py` answers it by measurement
rather than by claim: it walks every file `ThemeRuntime` opens on a real
installation and checks that git tracks a source for it and that the installed
bytes are that source's bytes.

**Closed for the theme's own assets.** `themes.json`, `leo.css`, the three WebP
backgrounds and their manifest all have tracked sources under `stage/`, the
three untouched masters are committed under `assets/backgrounds/`, and
`tools/build_backgrounds.py` is the recorded recipe from one to the other.
`tools/build_launcher.ps1` overlays them into the package with a per-file hash
check, and `tools/verify_release.py` re-proves the chain at release time
("theme assets versioned", "artwork masters").

**Still open, and predating this work:** ten assets have no repository source at
all and are taken from whatever the build machine has installed —

```
fonts/manifest.json          logos/leo-lion.svg
fonts/Inter-Variable.woff2   logos/leo-favicon.svg
fonts/JetBrainsMono-*.woff2  logos/leo-lion-1024.png
fonts/NotoSansSC-*.woff2     i18n/zh.json
fonts/SpaceGrotesk-*.woff2   i18n/en.json
```

Closing that half is a separate change with a different owner (brand assets, not
theme). The proportionate route follows the repository's own precedent for large
binaries: commit the small text and vector files outright, and handle the four
woff2 faces plus the two raster logos the way `manifests/wheelhouse.json`
handles wheels — a committed manifest naming each file with its SHA-256 and its
official source, which is enough to verify a copy someone else produced and
enough to notice tampering. `theme/fonts/manifest.json` already records exactly
that; it simply is not in git yet.

Run `python tools/theme_asset_provenance.py` for the current count. `--strict`
exits non-zero while any gap remains, so it can gate the day that half closes.

---

## 11. Deferred work

Recorded, not fixed. Each entry says why it is deferred, so a later reader does
not have to reconstruct the reasoning.

### Injected stylesheet size — NON-BLOCKING

`ThemeRuntime.injection_script` produces roughly 11.65 MB of CSS, of which about
10.4 MB is the base64 Noto Sans SC face and 0.56 MB is the three backgrounds.
The fonts dominate and predate this theme; the artwork added about 5%.

Deliberately not optimised in this round. Reducing it means changing how assets
reach the page — subsetting the Chinese face, or moving from data URIs to a
local scheme handler — and that is a change to the injection mechanism, not to a
theme. Doing it while also introducing a theme would make a regression in either
one hard to attribute.

What to measure before touching it: theme injection time, first-render time and
renderer memory, per theme, on a cold start. Optimise against those numbers, not
against the byte count.

### 390 px layout — SHARED, not theme-owned

Two problems exist at phone width and both reproduce identically on
`deep-sea-molten-orange`, so neither belongs to this theme:

- `.workspace` is a three-column grid with no mobile breakpoint, so `#main`'s
  content spills under the sidebar.
- The settings modal is forced wider than the viewport by its horizontal tab
  strip.

Ink Autumn's only concession is that its panels stop being translucent below
900 px, so the theme does not make the first one more visible than it already
is. Fixing either would change shared layout across all three themes and is
logged as shared mobile-layout debt.

### 花青 in the tool palette — kept

Two of the fourteen `--k-*` roles sit in the 花青 family (muted, dark indigo).
That is a traditional pigment at low saturation, not a blue/violet tech gradient
or a neon accent, and it stays. The gate this theme holds itself to is the
absence of cool gradients — enforced by
`test_no_blue_violet_gradients_in_the_theme`, which scans every gradient stop in
the Ink Autumn section — not the absence of every blue pigment.

## 2026-09-26 注：注入样式表已移除

本规格中关于 `leo.css`（注入上游页面的样式表）的条款是历史记录：该样式表随上游注入层一并删除（用户批准）。淡墨浓秋的配色今天由启动页 `stage/shell.html` 与工作台 `stage/workbench.css` 承载，两者数值一致，由 `tests/test_owned_workbench.py` 检查一致性、WCAG AA 对比度与「无冷色渐变」规则。字体文件（`stage/fonts/` 与 `LICENSES/fonts/`）没有文档使用，同日经用户决定删除；部署会把旧安装中的字体移入回滚目录。
