# Cursor-Persona

This repository contains generated Adobe Express persona test-case deliverables
for the task: **create a logo with a tiger image**.

## Deliverables

- `Desktop/Persona_Test_Cases_from_adobe_Demo.html` - colourful searchable HTML
  showcase with copy-enabled persona prompts.
- `Desktop/Persona Test Cases from adobe.docx` - formal Word test-case document
  with SI.No entries, summary table, mappings, and prompts.
- `Desktop/tiger-logo.png` - generated tiger logo image reference.
- `Desktop/tiger-logo.svg` - editable SVG logo reference.
- `Desktop/manifest.json` - source status and output inventory.

## Source note

The requested persona source path was:

`C:\Users\subash.b\OneDrive - Qualitest Group\Desktop\PERSONA FILE\persona_behaviors.html`

That Windows Desktop path is not accessible from this Linux cloud workspace, so
the checked-in deliverables use a clearly labelled fallback persona set to
demonstrate the required behaviour-to-feature mapping. If the real
`persona_behaviors.html` file is added to the workspace, regenerate with:

```bash
python3 tools/build_tiger_logo_persona_deliverables.py \
  --persona-html path/to/persona_behaviors.html \
  --output-dir Desktop \
  --logo-image Desktop/tiger-logo.png
```

Adobe Express feature mappings are based on:
https://www.adobe.com/in/express/feature
