# Canvas Outcomes System - Deep Dive Research

**Research Date:** November 13, 2025  
**Purpose:** Understand Canvas outcomes architecture to inform QuizForge integration strategy, particularly regarding formative vs summative assessment differentiation.

---

## Canvas Outcomes Core Concepts

### 1. **Outcome Definition**

An **Outcome** in Canvas represents a learning objective/standard:

```json
{
  "id": 1,
  "title": "CS.6.A [S] - Define and Use Primitive Data Types",
  "display_name": "Data Types Mastery",
  "description": "Student can identify and use primitive data types",
  "vendor_guid": "CS.6.A",
  "calculation_method": "decaying_average",
  "calculation_int": 65,
  "mastery_points": 3,
  "points_possible": 5,
  "ratings": [
    { "description": "Exceeds", "points": 5 },
    { "description": "Mastery", "points": 3 },
    { "description": "Approaching", "points": 2 },
    { "description": "Beginning", "points": 1 }
  ]
}
```

**Key Fields:**
- `vendor_guid`: Custom identifier (e.g., TEKS code `CS.6.A`)
- `calculation_method`: How multiple scores are combined
- `mastery_points`: Threshold for "mastery" status
- `ratings`: Rubric-style scoring levels

---

### 2. **Outcome Alignments**

**Alignments** connect outcomes to assessable items (quizzes, assignments):

```json
{
  "id": 1,
  "assignment_id": 3287991,
  "assessment_id": null,
  "submission_types": "online_quiz",
  "url": "/courses/123/quizzes/3287991",
  "title": "Python Fundamentals Quiz"
}
```

**Canvas API for Alignments:**
- `POST /api/v1/courses/:course_id/outcome_alignments`
  - **Payload:** `{ "asset_string": "quizzes:3287991_73b480a05d4a36da910553b295811051", "learning_outcome_id": 42 }`
  - `asset_string` format: `{asset_type}:{quiz_id}_{question_id}`
  - Aligns a SINGLE question to a SINGLE outcome
  
- `GET /api/v1/courses/:course_id/outcome_alignments?student_id=456`
  - Returns all aligned assignments/quizzes for a student

**Critical Finding:** Alignments are **question-level**, not quiz-level. Each question can be aligned to one or more outcomes.

---

### 3. **Outcome Results**

When a student takes an aligned quiz, Canvas generates **OutcomeResults**:

```json
{
  "id": 42,
  "score": 4,
  "percent": 0.8,
  "submitted_or_assessed_at": "2025-11-13T10:30:00Z",
  "links": {
    "user": "3",
    "learning_outcome": "97",
    "alignment": "53"
  }
}
```

**Result Flow:**
1. Student submits quiz
2. Canvas auto-grades questions
3. For each aligned question:
   - Score mapped to outcome rating scale
   - OutcomeResult created
   - Result contributes to outcome rollup

---

### 4. **Outcome Rollups (Mastery Calculation)**

Canvas calculates a **rollup score** per outcome per student across ALL aligned assessments.

**Calculation Methods:**

| Method | Description | Use Case |
|--------|-------------|----------|
| **decaying_average** | Recent scores weighted more heavily | **DEFAULT** - Reflects growth over time |
| **weighted_average** | Older name for previous decaying_average (pre-FF) | Legacy |
| **n_mastery** | Mastery achieved after N consecutive mastery scores | Requires consistency |
| **highest** | Only highest score counts | Gives credit for peak performance |
| **latest** | Only most recent score counts | Focuses on current ability |
| **average** | Simple mean of all scores | Treats all attempts equally |

**Example Decaying Average (calc_int = 65%):**
- Scores: `[2, 3, 4, 5]` (oldest → newest)
- Formula: `newest * 0.65 + older_average * 0.35`
- Calculation: `5 * 0.65 + 3.5 * 0.35 = 4.475`

**Rollup API:**
- `GET /api/v1/courses/:course_id/outcome_rollups?user_ids[]=456&include[]=outcomes`
  - Returns current mastery status per outcome
  - Shows contributing scores if `contributing_scores=true`

---

## Formative vs Summative Assessment Problem

### **Your Concern (VALID):**

> "Easy low-level practices on a TEKS standard might show mastery, but actual TEST-weight questions are harder and the kid isn't at Master level."

### **Canvas Behavior:**

**ALL aligned questions contribute to rollup calculation.** Canvas does NOT natively distinguish between:
- Formative (practice, low-stakes)
- Summative (tests, high-stakes)

**Result:** A student could achieve "mastery" by doing well on easy practice questions, then fail the summative test—but Canvas still shows mastery.

---

## Solutions for Formative/Summative Differentiation

### **Option 1: Don't Align Formative Assessments** ⭐ RECOMMENDED

**Strategy:** Only align summative assessments (unit tests, semester exams).

**Pros:**
- ✅ Rollup scores reflect ONLY meaningful assessments
- ✅ Students can practice without polluting mastery data
- ✅ Simple to implement in QuizForge (metadata flag)
- ✅ Aligns with educational best practices

**Cons:**
- ❌ No Learning Mastery tracking for formative work
- ❌ Teachers can't see practice progress via outcomes dashboard

**Implementation:**
```python
# QuizForge text format
Quiz_Type: summative  # or "formative"
Outcomes: CS.6.A, CS.7.B  # Only applies if summative

# Packager logic
if quiz.type == "summative":
    generate_alignment_manifest()
else:
    skip_outcome_processing()
```

---

### **Option 2: Use Calculation Method = "highest"**

**Strategy:** Align ALL assessments, but configure outcomes to only count highest score.

**Pros:**
- ✅ Formative AND summative tracked
- ✅ Final mastery reflects peak performance
- ✅ Students can practice without penalty

**Cons:**
- ❌ Requires outcome configuration at Canvas level (not per-quiz)
- ❌ Teachers must manually change calculation method for each outcome
- ❌ "Highest" doesn't show growth trajectory

---

### **Option 3: Separate Outcome Sets**

**Strategy:** Create TWO outcome groups:
- **"CS TEKS - Formative"** (practice outcomes)
- **"CS TEKS - Summative"** (test outcomes)

Align formative quizzes to formative outcomes, summative to summative outcomes.

**Pros:**
- ✅ Complete separation of data
- ✅ Teachers can view both practice and test mastery
- ✅ Supports different calculation methods per group

**Cons:**
- ❌ Doubles outcome management overhead
- ❌ Confusing for teachers (which outcome to view?)
- ❌ QuizForge would need to manage two outcome registries

---

### **Option 4: Canvas "Assignment Groups" Weighting** (NOT NATIVE TO OUTCOMES)

Canvas has **Assignment Groups** (e.g., "Tests 60%, Homework 40%"), but this is for **final grades**, not outcome mastery.

**Verdict:** ❌ Not applicable to outcomes system.

---

### **Option 5: External Post-Processing** (ADVANCED)

**Strategy:** Use Canvas API to:
1. Retrieve all outcome results
2. Filter by alignment metadata (formative vs summative)
3. Recalculate rollups with custom weights
4. Display custom dashboard

**Pros:**
- ✅ Complete control over calculation
- ✅ Can implement sophisticated weighting

**Cons:**
- ❌ Requires building separate reporting system
- ❌ Canvas Learning Mastery Gradebook shows "wrong" data
- ❌ High development cost

---

## Recommended QuizForge Strategy

### **Phase 1: Add Assessment Type Metadata**

Extend QuizForge text format:

```
Title: Python Variables and Operators
Assessment_Type: summative  # or "formative"
Outcomes: CS.6.A, CS.6.B, CS.7.A

Type: multiple_choice
Points: 5
Outcomes: CS.6.A  # Question-level override possible
Prompt: ...
```

**Behavior:**
- `Assessment_Type: summative` → Generate alignment manifest
- `Assessment_Type: formative` → Skip alignment, include note in README
- If omitted → Prompt user or default to summative

---

### **Phase 2: Canvas API Enhancement**

When creating alignments via API, include custom metadata (if Canvas supports):

```python
# Check if Canvas accepts custom fields in alignment POST
alignment_payload = {
    "asset_string": "quizzes:3287991_73b480a05d4a36da910553b295811051",
    "learning_outcome_id": 42,
    "assessment_type": "summative"  # Custom field (TBD if Canvas stores this)
}
```

**NOTE:** Canvas API docs don't explicitly show custom fields for alignments. May need to test if these are stored/retrievable.

---

### **Phase 3: Documentation for Teachers**

Include guidance in QuizForge docs:

```markdown
## Outcome Alignment Best Practices

**Formative Assessments (Practice):**
- Low-stakes quizzes for skill building
- RECOMMENDATION: Do NOT align to outcomes
- Rationale: Prevents "false mastery" from easy practice questions

**Summative Assessments (Tests):**
- High-stakes, comprehensive evaluations
- RECOMMENDATION: Always align to outcomes
- These scores determine true mastery status

**To mark a quiz as formative:**
Add `Assessment_Type: formative` in quiz header.
QuizForge will skip outcome alignment for this quiz.
```

---

## Other API Capabilities Worth Exploring

### **1. Bulk Alignment Creation**

**Scenario:** Import 50 quizzes with 500 aligned questions.

**Current Plan:** Loop through questions, POST one-by-one.

**Better Approach:** Check if Canvas supports batch alignment API.

**Research Needed:** Canvas API docs don't show explicit batch endpoint for alignments. May need to test:
- Can we POST multiple alignments in single request?
- Is there a bulk import format (CSV/JSON)?

---

### **2. Quiz Metadata Syncing**

**Scenario:** User updates quiz in Canvas, wants to re-export to QuizForge text format.

**API Endpoints Needed:**
- `GET /api/v1/courses/:course_id/quizzes/:quiz_id/questions` → Retrieve questions
- `GET /api/v1/courses/:course_id/outcome_alignments` → Retrieve alignments
- Map alignments to questions via `assessment_question_identifierref`

**QuizForge Tool:** `canvas_to_text.py` (reverse packager)
- Downloads quiz from Canvas
- Converts to QuizForge text format
- Includes `Outcomes:` fields from alignments
- Enables round-trip editing workflow

---

### **3. Outcome Result Retrieval (Student Progress)**

**Scenario:** Teacher wants to see which outcomes students are struggling with.

**API Endpoint:**
```
GET /api/v1/courses/:course_id/outcome_results?user_ids[]=123&include[]=outcomes
```

**QuizForge Dashboard Idea:**
- Fetch outcome results after quiz submissions
- Generate report: "Question 3 (CS.7.A) - 60% correct rate"
- Suggest remediation resources for low-mastery outcomes

---

### **4. Outcome Import/Export**

**Scenario:** Share TEKS outcome sets between teachers.

**Canvas Supports:**
- **Outcome CSV Import:** `POST /api/v1/accounts/:account_id/outcome_imports`
- **CSV Format:**
  ```csv
  vendor_guid,title,description,display_name,calculation_method,calculation_int,mastery_points,ratings
  CS.6.A,"Data Types","Define primitive types","Data Types",decaying_average,65,3,"Exceeds:5,Mastery:3,Approaching:2,Beginning:1"
  ```

**QuizForge Tool:** `outcome_exporter.py`
- Reads `CS_Outcomes.txt` → Converts to Canvas CSV format
- Includes calculation method recommendations
- Teachers upload to Canvas via API or UI

---

### **5. Quiz Settings Configuration**

**Scenario:** Set quiz as "practice mode" with unlimited attempts, no grade recording.

**Current QuizForge:** Only generates QTI questions + manifest.

**Enhancement:** Include Canvas-specific metadata in QTI `assessment_meta.xml`:
```xml
<quiz_type>practice_quiz</quiz_type>  <!-- vs "assignment" -->
<allowed_attempts>-1</allowed_attempts>  <!-- unlimited -->
<show_correct_answers>true</show_correct_answers>
<hide_results/>  <!-- don't show in gradebook -->
```

**Benefit:** Formative quizzes auto-configured as practice mode.

---

### **6. Learning Mastery Gradebook Export**

**Scenario:** Teacher wants Excel report of outcome mastery per student.

**Canvas API:**
```
GET /api/v1/courses/:course_id/outcome_rollups?include[]=outcomes&include[]=users
```

**QuizForge Tool:** `mastery_report.py`
- Fetches rollup data
- Generates CSV: `Student, Outcome, Score, Mastery Status, Contributing Assessments`
- Enables data analysis in Excel/Python

---

## Unified Canvas API Strategy for QuizForge

### **Proposed Module: `quizforge.integrations.canvas_api`**

**Core Functions:**

1. **`align_quiz_outcomes(quiz_id, alignment_manifest)`**
   - Input: Quiz ID (from Canvas), JSON with question-outcome mappings
   - POST alignments to Canvas
   - Returns: Alignment IDs for tracking

2. **`fetch_quiz_structure(quiz_id)`**
   - GET quiz questions from Canvas
   - Extract question IDs, titles, types
   - Returns: Quiz object compatible with QuizForge domain model

3. **`sync_outcome_registry(outcome_csv_path)`**
   - POST outcomes to Canvas via CSV import
   - Returns: Canvas-assigned outcome IDs

4. **`export_quiz_to_text(quiz_id, output_path)`**
   - Reverse packager: Canvas → QuizForge text
   - Includes outcome alignments in `Outcomes:` fields

5. **`fetch_mastery_report(outcome_ids, student_ids)`**
   - GET outcome rollups for specified students/outcomes
   - Returns: DataFrame with mastery data

6. **`configure_quiz_settings(quiz_id, settings_dict)`**
   - Update quiz metadata (attempts, show_answers, etc.)
   - Supports formative/summative presets

---

## Decision Matrix: Assessment Type Handling

| Approach | Complexity | Teacher Control | Data Accuracy | QuizForge Effort |
|----------|------------|-----------------|---------------|------------------|
| **Option 1: No Formative Alignment** | Low | High | ⭐⭐⭐⭐⭐ Excellent | ✅ Minimal |
| Option 2: Highest Calc Method | Medium | Low | ⭐⭐⭐ Good | Moderate |
| Option 3: Separate Outcome Sets | High | Medium | ⭐⭐⭐⭐ Very Good | High |
| Option 4: Assignment Groups | N/A | N/A | ❌ Not Applicable | N/A |
| Option 5: Custom Dashboard | Very High | Medium | ⭐⭐⭐⭐⭐ Excellent | Very High |

---

## Recommended Implementation Roadmap

### **Immediate (Next Steps):**

1. ✅ Add `Assessment_Type:` field to QuizForge text format
2. ✅ Update text parser to recognize formative/summative flag
3. ✅ Packager skips alignment manifest for formative quizzes
4. ✅ Document best practices for teachers

### **Phase 2 (After Basic Alignment Works):**

5. ⚠️ Build `canvas_to_text.py` reverse packager
6. ⚠️ Test Canvas API for custom alignment metadata support
7. ⚠️ Create outcome CSV export tool

### **Phase 3 (Advanced Features):**

8. ⚠️ Mastery report generator
9. ⚠️ Batch alignment API research/implementation
10. ⚠️ Integration with Canvas quiz settings (practice mode)

---

## Key Takeaways for QuizForge

1. **Canvas does NOT export outcome alignments in QTI** → API-based alignment is mandatory
2. **All aligned questions contribute to mastery** → Formative/summative differentiation required
3. **Calculation methods are outcome-level, not quiz-level** → "Highest" strategy requires outcome reconfiguration
4. **Question-level alignments** → Each question can have multiple outcomes
5. **Asset string format:** `quizzes:{quiz_id}_{question_id}` → Need Canvas-assigned IDs post-import

---

## Open Questions

1. ❓ Does Canvas API support custom metadata fields in alignment POSTs?
2. ❓ Is there a batch alignment endpoint we're missing?
3. ❓ Can QTI import set `quiz_type` to `practice_quiz` (formative mode)?
4. ❓ Do Canvas outcome reports allow filtering by alignment source (formative vs summative)?
5. ❓ What's the Canvas API rate limit for bulk alignment operations (500+ questions)?

---

**Status:** Research complete. Ready for architectural decision on formative/summative handling.

**Recommendation:** **Option 1 (No Formative Alignment)** as default, with `Assessment_Type:` field to give teachers control.
