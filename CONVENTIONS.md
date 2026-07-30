# Project Archiving and Naming Conventions

> This document is the single source of truth for file placement and naming in this repository.
> If you are unsure where a file belongs or how it should be named, follow this document.
> If the repository disagrees with this document, update the repository layout instead of weakening the rule.

Last updated: 2026-07-30

---

## 1. Repository Structure

```
Car-and-Robotic-Arm/
├── README.md              Project entry point
├── CONVENTIONS.md         This file
├── CLAUDE.md              AI agent working rules
├── pyproject.toml         Python project definition (managed with uv)
│
├── docs/                  First-party project documentation
│   ├── hardware/          Hardware specs, protocol notes, wiring
│   ├── setup/             Bring-up and environment setup guides
│   ├── progress/          Verified progress logs from real hardware work
│   └── adr/               Architecture decision records
│
├── src/carbot/            Importable Python package
├── tests/                 Automated tests
├── examples/              Runnable example and verification scripts
├── scripts/               One-off tools and validators
│
├── assets/                Binary assets
│   ├── inventory/         Inventory photos (numbered sequence)
│   ├── assembly/          Assembly photos (numbered sequence)
│   ├── reference/         Diagrams, screenshots, spec images
│   └── assembly-guide/    Extracted assembly manual pages and text
│
├── site/                  Astro website source
│   ├── src/data/          Shared website data files
│   ├── src/pages/         Routes (default locale at root, English under `/en/`)
│   ├── src/components/    Components
│   ├── src/layouts/       Layouts
│   ├── src/styles/        Shared tokens and page styles
│   └── public/            Static files copied as-is
│
├── astro.config.mjs       Build configuration (`_site/` output is not committed)
├── package.json
│
└── vendor/                Vendor material, kept read-only
    ├── yourfun-nezha/
    ├── keyes-37in1-sensor-kit/
    └── raspberry-pi/
```

## 2. Decide Placement by Asking One Question

**Who created this file?**

| Source | Where it goes | Editable |
|---|---|---|
| First-party documentation | `docs/` | Yes |
| First-party code | `src/`, `tests/`, `examples/`, `scripts/` | Yes |
| Photos we captured | `assets/` | Append only |
| Website frontend | `site/` | Yes |
| Vendor-provided material | `vendor/` | No |
| Generated scratch output | `scratch/` | Not committed |

`vendor/` is a hard boundary. If vendor code needs adaptation, copy it into `src/` or `scripts/`
and keep the original files untouched for reference.

## 3. Naming Rules

### 3.1 Code and Documents: `lower-kebab-case`

```
docs/hardware/nezha-i2c-protocol.md
scripts/build-assembly-html.py
site/inventory/index.html
```

The only exception is Python modules, which use `snake_case` because they must be imported, for
example `src/carbot/nezha.py`.

### 3.2 Document Language and Filenames

Filenames never carry a language suffix. Use plain `name.md`:

```
good: raspberry-pi-5-pinout.md
good: mac-to-raspberry-pi-access.md
bad:  deskflow-macos-raspberrypi.en.md
```

This rule costs nothing, because the website does not resolve language through filenames either.
Localization is handled in three places, none of which is a filename:

| Layer | Mechanism |
|---|---|
| Routes | Directory prefix — `site/src/pages/en/`, configured in `astro.config.mjs` (`defaultLocale: 'zh'`, `prefixDefaultLocale: false`) |
| UI strings | `zh` / `en` keys in `site/src/i18n/ui.ts` |
| Page data | `i18n.zh` / `i18n.en` fields inside `site/src/data/*.json` |

Adding a `.en` or `.zh` suffix to a file therefore signals nothing to any build step, and only
creates a second naming style to remember.

**Language inside a document:** technical reference material — protocol notes, pinouts, ADRs,
bring-up procedures — is written in English so that the terminology matches the code and vendor
sources. Guides aimed at repository visitors rather than at contributors may be bilingual in a
single file, English first and Traditional Chinese second within each section. Do not split a
bilingual guide into two files.

| Document | Language |
|---|---|
| `docs/hardware/`, `docs/adr/`, `docs/progress/` | English |
| `docs/setup/mac-to-raspberry-pi-access.md` | Bilingual (visitor-facing) |
| Other `docs/setup/` procedures | English |

### 3.3 Asset Photos: `NNN_Title_Case_Description.ext`

```
assets/inventory/027_Waveshare_PanTilt_HAT_Front.jpg
assets/assembly/003_Car_Chassis_Bottom_Wiring.jpg
```

- `NNN` is a three-digit inventory number.
- Once assigned, a number is never reused, reordered, or recycled.
- The numbering sequence is global across `assets/inventory/` and `assets/assembly/`.
- The current highest number is `091`. Number `048` is intentionally unused. The next photo starts at `092`.

Title case is intentional here. The number is part of the identity, and these filenames are easier
to browse visually than kebab case. This is the only repository-wide exception to the standard naming style.

### 3.4 Reference Images: `lower-kebab-case`

Use an ISO date prefix when the image is tied to a dated observation.

```
assets/reference/raspberry-pi-5/gpio-pinout-diagram.png
assets/reference/nezha/2026-07-30-stm32-car-wiring-diagram.png
```

`assets/reference/` stores unnumbered diagrams, screenshots, and spec sheets grouped by source.

### 3.5 Hard Prohibitions

Rename these before adding them to the repository:

```
bad: Screenshot 2026-07-30 at 3.30.58 AM.png
bad: IMG_0325.JPG
bad: G SDA SCL 5V.JPG
bad: untitled.pdf

good: assets/reference/nezha/2026-07-30-i2c-header-g-sda-scl-5v.jpg
good: assets/inventory/091_HXS_18650_Battery_Pack_Label.jpg
```

- No spaces
- No non-English first-party filenames
- File extensions must be lowercase
- Dates must use ISO `YYYY-MM-DD`

The only exception is `vendor/`, where original filenames are preserved for traceability.

## 4. `vendor/` Import Rules

Every `vendor/<supplier>/` directory must contain a `README.md` that records:

1. Supplier name and official link
2. Download date and version
3. Location of the original archive or media
4. What was excluded during import

Always remove generated build artifacts such as `.o`, `.crf`, `.d`, `.lst`, `.dep`, `.map`,
`.axf`, and `.uvoptx`. The full ignore list lives in `.gitignore`. These files can be rebuilt and
consume most of the unnecessary space in imported SDKs.

## 4.5 Website Data

Keep page content in data files instead of hardcoding it inside HTML or component markup.

The website uses a single shared dataset with localized fields under `i18n.zh` and `i18n.en`:

```js
{
  id, number, name, category, tags, images,
  i18n: {
    zh: { title, desc, specs, ... },
    en: { title, desc, specs, ... }
  }
}
```

`images` stores paths relative to the repository root, such as
`assets/inventory/001_Example_Module.jpg`.

Current data files:

| File | Purpose |
|---|---|
| `site/src/data/modules.json` | Inventory catalog |
| `site/src/data/assembly-guide.json` | Assembly guide content |
| `site/src/data/categories.ts` | Inventory category labels |

After changing website data, run:

```bash
uv run python scripts/check_inventory_data.py
```

The validator checks that assets exist, IDs are unique, bilingual fields are present, and asset
filenames follow the `NNN_` rule from §3.3.

### Local Preview

```bash
npm run dev
```

The site is served at <http://localhost:4321/Car-and-Robotic-Arm/> so the local path matches the
GitHub Pages base path.

## 5. Git

### Commit Messages

Use Conventional Commits, with the top-level folder as the scope when helpful:

```text
docs: add NeZha register mapping notes
src: add Python driver for the NeZha board
assets: add binocular camera photos 092-093
vendor: import 37-in-1 sensor kit vendor files
site: fix inventory image paths
chore: add gitignore
```

Prefer commit bodies that explain **why** the change exists rather than repeating the diff.

### Size Guardrails

This repository contains many binary assets. Keep these limits in mind:

| Item | Current state | Limit |
|---|---|---|
| Working tree | ~195MB | n/a |
| `.git` history | ~83MB | GitHub recommends under 1GB |
| Largest file | ~2.4MB | GitHub hard limit is 100MB |
| `assets/` | ~45MB | GitHub Pages publish limit is 1GB |

Rules:

- Compress single photos below **1MB** before committing them.
- PDF and document-like files should stay below **10MB** unless discussed first.
- Videos, firmware images, and archives do not belong in this repository.

`git rm` does not shrink history by itself. The repository history was rewritten once on
2026-07-30 with `git filter-repo` to reduce size. That kind of operation is destructive and must
always be discussed before repeating it.

## 6. Scratch Files

Experimental output and temporary files belong in `scratch/`, which is already ignored. Do not
scatter files such as `test.py`, `tmp.json`, or generic placeholders in the repository root.

## 7. Checklist Before Adding a File

1. Who created it? Choose the top-level directory from §2.
2. Does the filename contain spaces, non-English text, or uppercase extensions?
3. Is it a photo? Assign the next number and never reuse an old one.
4. Is it larger than 1MB? Compress it first.
5. Is it vendor material? Remove build artifacts and add a `README.md`.
