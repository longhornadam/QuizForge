# Canvas QTI Export Analysis - Outcome Alignment Storage

**Test Date:** November 13, 2025  
**Export File:** `c9a901d11fb26d25e4f938028adca8ae67d20a30c14f26fca617813ecdb1a22e.zip`  
**Test Condition:** First 2 questions manually aligned in Canvas UI, remaining 10 questions unaligned

---

## Key Finding: Canvas Does NOT Export Outcome Alignments to QTI

### Files in Canvas Export:
```
canvas_export/
├── imsmanifest.xml
└── ge803f0183b7483a1be5f014503c653ea/
    ├── assessment_meta.xml
    └── ge803f0183b7483a1be5f014503c653ea.xml (QTI questions)
```

### Analysis Results:

#### 1. **QTI Question XML** (`ge803f0183b7483a1be5f014503c653ea.xml`)
- ✅ Contains all 12 questions with full structure
- ✅ Question metadata preserved (points, type, calculator settings)
- ❌ **NO outcome alignment metadata present**
- ❌ No `qtimetadatafield` for outcome codes/IDs
- ❌ No custom Canvas-specific outcome references
- Only contains standard QTI `<outcomes>` elements for scoring (not Learning Outcomes)

#### 2. **Assessment Metadata XML** (`assessment_meta.xml`)
- ✅ Contains quiz-level settings (title, points, attempts, display settings)
- ✅ Contains assignment configuration
- ❌ **NO outcome alignment data**
- ❌ No outcome references or identifiers
- No sections for question-to-outcome mappings

#### 3. **Manifest XML** (`imsmanifest.xml`)
- Standard IMS Common Cartridge structure
- No outcome-related extensions or metadata

---

## Critical Discovery: Outcome Alignments are Database-Only

**Canvas stores outcome alignments in its internal database, NOT in exportable QTI files.**

### Implications:

1. **QTI Import/Export Cannot Transfer Alignments**
   - Importing QTI → alignments must be done via Canvas UI or API
   - Exporting QTI → alignments are lost/not included
   - Round-trip workflow (export → modify → re-import) loses all alignments

2. **Manual UI Alignment Was Successful** (confirmed by user)
   - User manually aligned 2 questions via Canvas UI
   - Alignments visible in Canvas Learning Mastery Gradebook
   - BUT alignments do NOT appear in exported QTI

3. **QuizForge Integration Requirements Confirmed**
   - ✅ Phase 1: Text format with `Outcomes:` field (REQUIRED)
   - ✅ Phase 2: Generate clean QTI without outcome metadata (CORRECT approach)
   - ✅ **Phase 3: Canvas API for alignment is THE ONLY PATH** (MANDATORY)

---

## Canvas API Alignment Workflow (Required Implementation)

### Step-by-Step Process:

1. **QuizForge generates clean QTI** (already working)
   - Text → QTI conversion with `Outcomes:` field preserved internally
   - QTI ZIP contains NO outcome metadata (Canvas ignores it anyway)

2. **User imports QTI to Canvas**
   - Canvas creates quiz with auto-generated question IDs
   - Questions have no alignments yet

3. **QuizForge API Tool retrieves question IDs**
   - `GET /api/v1/courses/:course_id/quizzes/:quiz_id/questions`
   - Maps question titles to Canvas-assigned IDs
   - Example: `Q01_DataTypes` → `assessment_question_id: 73b480a05d4a36da910553b295811051`

4. **QuizForge API Tool creates alignments**
   - For each question with `Outcomes:` field:
     - Match outcome code (e.g., `CS.6.A`) to Canvas outcome ID (from course outcomes)
     - POST to `/api/v1/courses/:course_id/outcome_alignments`
     - Payload: `{ "asset_string": "quizzes:3287991_73b480a05d4a36da910553b295811051", "learning_outcome_id": <canvas_outcome_id> }`

5. **Verification**
   - Canvas Learning Mastery Gradebook shows alignments
   - Quiz edit screen shows "Align to Outcomes(N)" counts
   - Student submissions trigger mastery score calculations

---

## Technical Details from Export

### Canvas Question ID Format (from export XML):
```xml
<qtimetadatafield>
  <fieldlabel>assessment_question_identifierref</fieldlabel>
  <fieldentry>73b480a05d4a36da910553b295811051</fieldentry>
</qtimetadatafield>
```

### Asset String Construction:
- Format: `quizzes:{quiz_id}_{question_id}`
- Example: `quizzes:3287991_73b480a05d4a36da910553b295811051`
- Quiz ID from: `<assessment external_assignment_id="3287991">`
- Question ID from: `assessment_question_identifierref` metadata field

### Canvas Adds to QTI on Export:
- `external_assignment_id` (quiz ID)
- `assessment_question_identifierref` (question ID in Canvas DB)
- `original_answer_ids` (UUIDs for answer choices)
- `calculator_type` metadata

---

## Comparison: Our Import vs Canvas Export

| Element | Our Generated QTI | Canvas Export |
|---------|-------------------|---------------|
| Item idents | `item_abc123` (UUID-based) | Canvas UUIDs (different) |
| Question IDs | Not present | `assessment_question_identifierref` added |
| Quiz ID | Not present | `external_assignment_id` added |
| Outcome metadata | Custom `qtimetadatafield` (ignored) | **Not present** (even for aligned Qs) |
| Answer IDs | Simple (`a`, `b`, `c`, `d`) | UUIDs (`b09665c1-1955-41aa-956d-e832d3bd2bb1`) |

---

## Next Steps for QuizForge Integration

### Phase 3 Implementation (MANDATORY):

1. **Create `canvas_api_aligner.py`** in `dev/outcomes/`
   - Read quiz alignment data (JSON format with question titles + outcome codes)
   - Authenticate to Canvas API (requires API token from user)
   - GET quiz questions to map titles → Canvas IDs
   - GET course outcomes to map codes → Canvas outcome IDs
   - POST alignment for each question-outcome pair

2. **User Workflow:**
   ```
   1. Author quiz in text format with Outcomes: field
   2. Run QuizForge packager → generates clean QTI ZIP
   3. Import QTI to Canvas (manual step)
   4. Run alignment tool: python canvas_api_aligner.py --quiz-id 3287991 --alignment-file alignments.json
   5. Tool creates alignments via API
   6. Verify in Canvas Learning Mastery Gradebook
   ```

3. **Production Integration:**
   - Add `outcome_codes` field to Question domain model
   - Text parser extracts `Outcomes:` field → stores as list
   - Packager generates:
     - Clean QTI ZIP (no outcome metadata)
     - Separate `alignments.json` file (title + outcome codes mapping)
   - User runs post-import alignment tool separately

---

## Conclusion

**Canvas does NOT preserve outcome alignments in QTI exports.**  
**API-based alignment after QTI import is the ONLY viable approach.**

Manual UI alignment works perfectly (confirmed by user testing), but is not scalable.  
QuizForge must implement Canvas API integration to automate the alignment process.

---

**Status:** Analysis complete. Ready for Phase 3 API tool development.
