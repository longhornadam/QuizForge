# QuizForge Feature Spec: Per-Choice Rationales
**Schema Change + Renderer Template + Base Doc Update**
**Handoff Document for Development Conversation — March 2026**

---

## 1. Context and Motivation

QuizForge currently generates one rationale per scored item, explaining only why the correct answer is correct. This spec was sufficient for basic answer-key generation but does not support a high-demand use case: student-facing correction documents where every answer choice receives its own explanation.

A teacher using QuizForge for 8th-grade CS classes generated a validation document with per-choice rationales in a table format. When shared with students after an assessment, the response was strongly positive. Students reported that:

- Seeing why each wrong answer was wrong helped them understand the misconception, not just the right answer
- The table format made it easy to scan and find their specific wrong choice
- The rationale length (1–2 sentences per choice) was enough to explain without overwhelming

This feature request has two components: (1) extending the QuizForge JSON schema to carry per-choice rationale data, and (2) building a renderer that produces the student-facing table format.

---

## 2. Target Output — What Students See

The following shows the exact format that received positive student feedback. This is the target rendering for the correction document output.

**Q5: In a flowchart, a labeled line connects a decision shape to the next step and is marked "Yes." What does this line represent?**

| | Choice Text | ✓ / ✗ | Rationale |
|---|---|:---:|---|
| **A** | The value stored in a variable | ✗ | *Variables store data values; they are not related to arrows. Arrows represent the direction of program flow.* |
| **B** | **The path the program takes when the answer is Yes** | ✓ | Arrows show program flow between steps. A labeled arrow marked "Yes" indicates the path followed when the decision evaluates to true. |
| **C** | The number of times a loop will repeat | ✗ | *Loop counts are not shown by individual arrows. Arrows simply show which step comes next based on the decision outcome.* |
| **D** | The data type of the decision result | ✗ | *Data types describe the kind of data a variable holds. An arrow label like "Yes" shows program direction, not data types.* |

**Key visual features in the rendered (DOCX/HTML) version:**
- Correct row (B) has light green background shading (#E6F3E6)
- Correct choice text is **bold**
- ✓ is green (#006600), ✗ is red (#CC0000), both bold and centered
- Incorrect rationale text is *italic*
- Correct rationale text is normal weight (not italic)

---

## 3. Visual Formatting Spec

| Element | Specification |
|---|---|
| **Question header** | Bold, dark blue (#1F3864), outside the table. Format: "Q[n]: [full stem]" |
| **Table columns** | 4 columns: Letter \| Choice Text \| ✓/✗ \| Rationale |
| **Header row** | Dark blue background (#1F3864), white bold text |
| **Correct row shading** | Light green background (#E6F3E6) on all four cells of the correct answer row |
| **Correct choice text** | Bold. All other choice text is normal weight. |
| **✓ / ✗ column** | Centered. ✓ in green (#006600) for correct. ✗ in red (#CC0000) for incorrect. Bold. |
| **Correct rationale** | Normal weight (not italic). Explains why this answer IS correct. |
| **Incorrect rationale** | Italic. Explains what this choice actually describes and why it does not apply. |
| **Rationale length** | 1–2 sentences, approximately 15–30 words. Never generic; always specific to the choice content. |
| **Incorrect rows** | White/default background. No special shading. |

---

## 4. Schema Change — Current vs. Proposed

### 4a. Current Schema (Section 11 of QuizForge Base)

The current rationales array has one entry per scored item with a single rationale string that explains only the correct answer:

```json
"rationales": [
  {
    "item_id": "exam_05",
    "rationale": "Arrows show program flow; a labeled arrow marked Yes indicates the path followed when the decision is true."
  }
]
```

### 4b. Proposed Schema (Per-Choice Rationales)

The rationales array expands to include a `choices` sub-array. Each choice gets its own rationale:

```json
"rationales": [
  {
    "item_id": "exam_05",
    "choices": [
      {
        "id": "A",
        "correct": false,
        "rationale": "Variables store data values; they are not related to arrows. Arrows represent the direction of program flow."
      },
      {
        "id": "B",
        "correct": true,
        "rationale": "Arrows show program flow between steps. A labeled arrow marked \"Yes\" indicates the path followed when the decision evaluates to true."
      },
      {
        "id": "C",
        "correct": false,
        "rationale": "Loop counts are not shown by individual arrows. Arrows simply show which step comes next based on the decision outcome."
      },
      {
        "id": "D",
        "correct": false,
        "rationale": "Data types describe the kind of data a variable holds. An arrow label like \"Yes\" shows program direction, not data types."
      }
    ]
  }
]
```

### 4c. Format requirement

All rationale entries for MC and MA items must use the per-choice `choices` array format. Entries that lack a `choices` key are silently skipped by the parser and will not appear in any output.

---

## 5. Rationale Writing Guidelines (for Base Doc Section 11)

These guidelines govern how LLMs should write per-choice rationales. This text should replace or supplement the current Section 11 in QuizForge_Base_DRAFT.md.

### 5a. Correct Choice Rationale

- 1–2 sentences explaining WHY this answer is correct
- Connect the concept to the answer — don't just restate the choice
- Normal weight (not italic) in rendered output
- Example: "Arrows show program flow between steps. A labeled arrow marked 'Yes' indicates the path followed when the decision evaluates to true."

### 5b. Incorrect Choice Rationale

- 1–2 sentences explaining WHY this specific choice is wrong
- Name the misconception: what does this choice actually describe, and why doesn't that apply here?
- Common pattern: *"[What this choice actually describes]; [why that doesn't apply here]."*
- Never generic ("This is incorrect"). Always specific to the distractor's content.
- Italic in rendered output
- Example: "Loop counts are not shown by individual arrows. Arrows simply show which step comes next based on the decision outcome."

### 5c. Length and Tone

- Target: 15–30 words per rationale
- Direct teaching voice — not condescending, not overly formal
- Must stand alone without deferring to a teacher ("ask your teacher" is never acceptable)
- Always use per-choice rationales for MC and MA items regardless of subject. The renderer can hide distractor rationales from students if needed; it cannot create them if they were never written.

---

## 6. Implementation Checklist

There are three separate work streams. They can be done in parallel.

| # | Work Stream | What Changes | Owner / Tool |
|---|---|---|---|
| 1 | **QuizForge Base Doc** | Rewrite Section 11 (Rationales) to require per-choice format for MC/MA. Update Section 13 (Preflight) to add check: every MC/MA choice must have a rationale. Per-choice rationales are uniform across all subjects — no CS/ELA distinction, no legacy format. | LLM conversation (prompt engineering). Edit QuizForge_Base_DRAFT.md directly. |
| 2 | **QuizForge Application (Schema + Parser)** | Update JSON schema and parser to require the per-choice choices array format. Entries without a choices array are silently skipped. No legacy single-string format. | VSCode agent / developer. Requires access to the QuizForge codebase. |
| 3 | **Renderer / Export Template** | Build a "Correction Document" export format that produces the table layout from Section 2. Must support DOCX output (for printing) and HTML output (for Canvas). Formatting rules are in Section 3 of this document. | VSCode agent / developer. New rendering template in the export pipeline. |

---

## 7. Proposed Section 11 Replacement Text

The following is the exact text that should replace the current Section 11 in QuizForge_Base_DRAFT.md. It is written in the same voice and format as the rest of the base document.

> ## 11. RATIONALES (JSON)
>
> All MC and MA items must use per-choice rationales. Each answer option — correct and incorrect — gets its own rationale.
>
> **Required format:**
> ```json
> "rationales": [
>   {
>     "item_id": "mc_example",
>     "choices": [
>       { "id": "A", "correct": true,  "rationale": "Why A is correct." },
>       { "id": "B", "correct": false, "rationale": "Why B is wrong." },
>       { "id": "C", "correct": false, "rationale": "Why C is wrong." },
>       { "id": "D", "correct": false, "rationale": "Why D is wrong." }
>     ]
>   }
> ]
> ```
>
> **Rationale Writing Rules:**
> - One entry per scored item (skip STIMULUS / STIMULUS_END).
> - Correct-choice rationale: 1–2 sentences explaining why this answer IS correct. Connect the concept to the answer. Normal weight in rendered output.
> - Incorrect-choice rationale: 1–2 sentences explaining what this choice actually describes and why it does not apply. Name the specific misconception. Italic in rendered output.
> - Target length: 15–30 words per rationale. Direct teaching voice.
> - Never generic ("This is incorrect"). Always specific to the choice content.
> - Never tell students to "ask/see your teacher" — rationales must stand alone.
>
> **Subject-Level Guidance:**
> - Always use per-choice rationales for MC and MA items regardless of subject. The renderer can always hide distractor rationales; it cannot create them if they are missing.

---

## 8. Proposed Section 13 (Preflight) Addition

Add the following check to the existing preflight checklist in Section 13:

> ☐ **Per-choice rationale check (MC/MA):** If using per-choice format, verify every choice ID in the item's choices array has a corresponding entry in the rationale's choices array. No choice should be missing a rationale. Each rationale must be specific to that choice's content, not a generic filler.

---

## 9. Full Example — Complete Item + Rationale in New Format

This shows one complete MC item and its matching per-choice rationale entry, exactly as they would appear in a QuizForge JSON payload.

**Inside the `items` array:**
```json
{
  "id": "exam_05",
  "type": "MC",
  "prompt": "In a flowchart, a labeled line connects a decision shape to the next step and is marked \"Yes.\" What does this line represent?",
  "choices": [
    { "text": "The path the program takes when the answer is Yes", "correct": true, "id": "A" },
    { "text": "The value stored in a variable", "correct": false, "id": "B" },
    { "text": "The number of times a loop will repeat", "correct": false, "id": "C" },
    { "text": "The data type of the decision result", "correct": false, "id": "D" }
  ]
}
```

**Inside the `rationales` array:**
```json
{
  "item_id": "exam_05",
  "choices": [
    {
      "id": "A",
      "correct": true,
      "rationale": "Arrows show program flow between steps. A labeled arrow marked \"Yes\" indicates the path followed when the decision evaluates to true."
    },
    {
      "id": "B",
      "correct": false,
      "rationale": "Variables store data values; they are not related to arrows. Arrows represent the direction of program flow."
    },
    {
      "id": "C",
      "correct": false,
      "rationale": "Loop counts are not shown by individual arrows. Arrows simply show which step comes next based on the decision outcome."
    },
    {
      "id": "D",
      "correct": false,
      "rationale": "Data types describe the kind of data a variable holds. An arrow label like \"Yes\" shows program direction, not data types."
    }
  ]
}
```

---

## 10. Non-MC Question Types

Per-choice rationales apply to MC and MA items only. For other question types, continue using the existing single-rationale format:

| Question Type | Rationale Format |
|---|---|
| **MC / MA** | Per-choice (required) |
| **TF** | Single rationale explaining the correct boolean value |
| **FITB** | Single rationale explaining the accepted answer(s) |
| **MATCHING** | Single rationale summarizing the correct pairings |
| **ORDERING** | Single rationale explaining the correct sequence |
| **NUMERICAL** | Single rationale explaining how to arrive at the answer |
| **ESSAY / FILEUPLOAD** | No rationale (human-graded items) |

---

## 11. Open Questions for Development

The following decisions should be resolved during development:

1. **HTML export:** Should the correction table be embedded in the Canvas quiz as a post-submission view, or generated as a standalone HTML file the teacher downloads and shares?

2. **Toggle mechanism:** How does the teacher indicate whether distractor rationales should be visible to students? A metadata flag? A renderer config option? Both?

3. **TF expansion:** Should True/False items also get per-choice rationales (one for True, one for False), or is the single rationale sufficient for binary items?

4. **Matching/Ordering:** Is there a future need for per-pair or per-step rationales in MATCHING and ORDERING items, or is single-rationale always sufficient?
