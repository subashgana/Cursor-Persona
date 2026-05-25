# Adobe Express Bird Logo Persona Prompt Generation

This repository now includes a dependency-free generator for creating persona-isolated
test prompts for a shared Adobe Express task: **create a Bird logo**.

## Important input note

The requested source file path was:

```text
C:\Users\subash.b\OneDrive - Qualitest Group\Desktop\persona_background_test_cases.json
```

That Windows Desktop path is not available inside the Linux Cursor Cloud
workspace. To generate the final HTML, Word, and JSON prompt deliverables, copy
`persona_background_test_cases.json` into the repository root or pass its path
with `--input`.

## Adobe Express feature source

The feature catalogue in `data/adobe_express_features.json` was created from:

```text
https://www.adobe.com/in/express/feature
```

The generator maps each persona's behavior to named Adobe Express features such
as:

- Design with AI
- Make content that always stands out
- Add design elements
- Play with text
- Apply your brand
- Work better together
- Edit images, videos and PDFs in just a few clicks
- Remix it
- Add amazing effects to any project
- Create videos made for social
- Take command of social content

## Run the generator

From the repository root:

```bash
python3 tools/generate_bird_logo_prompts.py \
  --input persona_background_test_cases.json \
  --output-dir generated
```

If the persona JSON is placed in the repository root with the exact file name
`persona_background_test_cases.json`, the `--input` argument can be omitted:

```bash
python3 tools/generate_bird_logo_prompts.py
```

## Generated deliverables

The command writes:

- `generated/Persona_Test_Cases_Bird_Logo_Demo.html`
  - Colorful interactive HTML showcase
  - Searchable persona cards
  - Copy buttons for each unique prompt
  - Persona summary, mapped features, background recommendation, and prompt
- `generated/Persona Test Cases Bird Logo.docx`
  - Formal Word test case document
  - SI.No summary table
  - Detailed persona test case sections
- `generated/bird_logo_persona_prompts.json`
  - Machine-readable prompt and feature mapping output

## Supported persona JSON shapes

The generator accepts common structures, including:

```json
[
  {
    "persona_id": "P001",
    "persona_name": "Example Persona",
    "occupation": "Marketing manager",
    "technical_skill": "Intermediate",
    "prompt_style": "Concise bullet points",
    "ai_trust_level": "Cautious",
    "accessibility": "High contrast preferred",
    "locale": "en-IN",
    "privacy_posture": "Enterprise data cautious",
    "acceptance_criteria": "Logo must be readable at small sizes",
    "avoid_list": "No copyrighted brand references"
  }
]
```

or nested containers:

```json
{
  "personas": [
    { "name": "Persona A" },
    { "name": "Persona B" }
  ]
}
```

The parser recognizes many field aliases, such as `persona`, `name`,
`role`, `job_title`, `tech_skill`, `communication_style`, `ai_trust`,
`accessibility_needs`, `privacy`, `success_criteria`, and `constraints`.

## Mapping logic

Every prompt is grounded in the shared Bird logo task and then adjusted by
persona behavior:

- Low technical skill adds guided template and Quick Action workflows.
- Advanced technical skill adds effects and more detailed design controls.
- Low AI trust adds verification checkpoints and manual review wording.
- High AI trust allows faster Firefly ideation.
- Accessibility needs add high-contrast, readable type, and export checks.
- Privacy or enterprise signals add brand controls and collaborative review.
- Social or marketing contexts add social resizing, scheduling, and optional
  animation guidance.
- Locale values influence typography and language-readiness instructions.

Each output prompt includes persona isolation language so preferences from one
persona are not reused for another.
