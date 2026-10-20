# Design resources — sample-bakery
This folder is the design hub: originals, decisions and briefs. Applications consume versioned runtime exports copied into their own repositories, never this whole folder.

## Layout
| Folder / file | Purpose |
|---|---|
| `BRAND.md` | Identity, palette, typography and usage rules; status pending until approved values exist |
| `DECISIONS.md` | Design decisions `D-NNN` with date, source and status |
| `catalog.json` | Every asset with id, path, kind, status (unreviewed / proposed / approved / deprecated), source, usage rights, surfaces |
| `tokens/` | Primitive and semantic design tokens (Design Tokens Format Module JSON) with a revision |
| `briefs/<surface>.md` | One brief per surface from templates/DESIGN-BRIEF.md |
| `inbox/` | Unclassified deliveries; `inbox/RESOURCE-LIST.md` records what arrived, when and what was approved |
| `source/` | Editable masters, palette and typography specifications, licences, manuals |
| `assets/` | Logos, icons, fonts, patterns, photos in their final formats |
| `references/` | Inspiration and references (never copied into products) |
| `exports/<revision>/` | Selected runtime derivatives with a manifest of hashes |

## Intake rules
1. Keep the designer's original delivery intact; register every file in `catalog.json` with provenance and rights. Receipt is not approval.
2. The latest explicit owner instruction wins; references and inspiration are not approval.
3. When official values arrive, update BRAND.md, the catalog, the tokens and DECISIONS.md together and replace provisional references in active tasks without deleting history.
4. Large editable masters need an explicit storage decision (Git-ignored or external) before committing.

## Prompts
Intake: "Read design/BRAND.md, design/DECISIONS.md, design/catalog.json and the relevant brief. Treat unapproved values as provisional; do not invent fonts, colours or logos; record UI decisions as proposals; check contrast; capture real screens."

Final delivery: "Review design/inbox/RESOURCE-LIST.md and the new resources. Preserve originals, register every file in catalog.json with status and provenance, apply the explicit approvals I supplied, update BRAND.md and tokens with official values, record differences in DECISIONS.md and list outstanding items. Update only affected exports and tasks."
