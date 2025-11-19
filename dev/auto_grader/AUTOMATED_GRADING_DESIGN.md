# Automated Canvas Grading Workflow Design

## Core Purpose
**Grade written student work using LLMs, then push scores/feedback to Canvas.**

Focus: Short answer responses, essays, extended constructed responses (ECRs) - the stuff that actually needs grading. Canvas already auto-grades multiple choice, matching, etc.

---

## Input Sources & Parsing Rules

### 1. Standard Assignments (online_text_entry)
**Status**: ✅ Fully functional via API

- **Pull Method**: Canvas REST API v1
- **Endpoint**: `GET /api/v1/courses/{course_id}/assignments/{assignment_id}/submissions`
- **What to Extract**: All `online_text_entry` submission bodies
- **Tested**: "If You Kill Me" SCR - 10 submissions pulled successfully

**Rule**: Extract submission HTML, strip tags, output clean text with student names.

---

### 2. Classic Quizzes - CSV via API
**Status**: ✅ API-driven CSV generation + parsing

**Detection**: Assignment has `quiz_id` field (not null)

**API Workflow**:
```python
# 1. Request report generation
POST /api/v1/courses/{course_id}/quizzes/{quiz_id}/reports
Body: {"quiz_report": {"report_type": "student_analysis"}}

# 2. Poll progress_url until workflow_state == "completed"
GET {progress_url}

# 3. Download CSV from file.url in the QuizReport object
GET {file_url}
```

---

### 3. New Quizzes CSV Export (MANUAL ONLY)
**Status**: ⚠️ No API access

**Detection**: Assignment has `submission_types: ["external_tool"]` and `quiz_id: null`

**Why Manual**: New Quizzes are LTI tools, not traditional Canvas quizzes. They don't expose CSV generation endpoints. Must use Canvas UI "Download Responses" button.

**Tested**: Assignment 3279698 confirmed to have no `quiz_id`, making Quiz Reports API inaccessible.

#### **CSV Parsing Rules for New Quizzes**

**IGNORE These Column Types** (Canvas already graded them):
- Multiple choice (`choice`)
- True/False 
- Matching (`matching`)
- Numerical answers
- Fill-in-the-blank with exact match
- Any auto-scored question type

**EXTRACT These Column Types**:
- **Essay questions** - Identified by:
  - Column header length > 300 characters
  - Contains "Extended Constructed Response" OR "ECR"
  - Contains multi-paragraph prompts with rubric requirements
  
- **Short answer (text entry)** - Identified by:
  - Column header is a question but NOT a choice question
  - Student responses are sentences/paragraphs (not single words)
  - Typical length: 50-300 words

**Extraction Format**:
```
STUDENT: [Name]
WORD COUNT: [N]
─────────────────────────
[Clean text response]
```

---

## Grading Workflow (3 Phases)

### Phase 1: Extract → Single Clean Text File

**Input**: Canvas CSV export OR API JSON
**Output**: One `.txt` file formatted for LLM grading

```
PROMPT: [Assignment question/ECR prompt]
RUBRIC: [Scoring criteria if available]

═══════════════════════════════════════════════════════

STUDENT 1: Grace Nelson
WORD COUNT: 363
───────────────────────────────────────────────────────
[Full essay text here, HTML stripped]

═══════════════════════════════════════════════════════

STUDENT 2: Marcus Johnson  
WORD COUNT: 402
───────────────────────────────────────────────────────
[Full essay text here, HTML stripped]
```

**File naming**: `[AssignmentName]_READY_FOR_GRADING.txt`

---

### Phase 2: LLM Grading → Structured Output

**Input**: Single text file from Phase 1
**Process**: LLM reads all submissions, applies rubric, generates scores/feedback
**Output**: JSON file with grading results

```json
{
  "assignment": "Caitlyn Clark ECR",
  "max_points": 30,
  "rubric": {...},
  "grades": [
    {
      "student_name": "Grace Nelson",
      "score": 27,
      "feedback": "Strong thesis with clear evidence from both texts...",
      "strengths": ["Clear organization", "Effective quotes"],
      "improvements": ["Spelling: 'coefficient' not 'coefficent'"]
    }
  ]
}
```

**File naming**: `[AssignmentName]_GRADED.json`

---

### Phase 3: Push to Canvas

**Status**: ✅ **TESTED AND WORKING**

**Endpoint**: `PUT /api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}`

**Confirmed Capabilities**:
- Post numerical grades
- Add text feedback comments
- Post comments without changing grades
- Changes reflect immediately in Canvas UI

**Request Body**:
```json
{
  "submission": {
    "posted_grade": 85
  },
  "comment": {
    "text_comment": "Great analysis! Strong evidence..."
  }
}
```

**Test Results**: Successfully posted grade 99.5 + feedback to Assignment 3286605, then restored original score 85.0. Both operations returned 200 OK.

---

## File Organization

```
/dev/auto_grader/
├── parse_canvas_csv.py          # Extract text from New.Quiz CSV
├── parse_api_submissions.py     # Extract from standard assignments
├── grade_submissions.py         # LLM grading engine
├── push_to_canvas.py           # Upload scores/feedback
│
├── [Course]/[Assignment]/
│   ├── raw_export.csv          # Original Canvas export
│   ├── READY_FOR_GRADING.txt   # Phase 1 output
│   ├── GRADED.json             # Phase 2 output
│   └── canvas_upload_log.txt   # Phase 3 confirmation
```

---

## Script Specifications

### `parse_new_quiz_csv.py`

**Purpose**: Extract ONLY written responses from New.Quiz CSV exports

**Detection Logic**:
```python
def is_written_response_column(header, responses):
    """
    Determine if a column needs grading.
    Returns True ONLY for essay/short answer questions.
    """
    # Explicit exclusions (auto-graded by Canvas)
    if any(keyword in header.lower() for keyword in [
        'multiple choice', 'true/false', 'matching', 
        'fill in the blank', 'numerical'
    ]):
        return False
    
    # Essay indicators
    if 'extended constructed response' in header.lower():
        return True
    if 'ecr' in header.lower():
        return True
    if len(header) > 300:  # Long prompts = essays
        return True
    
    # Short answer indicators: check actual responses
    avg_word_count = sum(len(r.split()) for r in responses if r) / len(responses)
    if avg_word_count > 20:  # More than 20 words average = needs grading
        return True
    
    return False
```

**Output Format**:
- One text file: `[assignment_name]_READY_FOR_GRADING.txt`
- No JSON, no multiple files, no metadata dumps
- Just: student name + word count + clean text response

---

### `parse_api_submissions.py`

**Purpose**: Extract written responses from standard Canvas assignments

**Input**: Course ID + Assignment ID
**API Call**: `GET /api/v1/courses/{course_id}/assignments/{assignment_id}/submissions`
**Filter**: Only `online_text_entry` submissions
**Output**: Same format as CSV parser above

---

### `grade_with_llm.py` (TO BUILD)

**Purpose**: Read the `_READY_FOR_GRADING.txt` file, grade all responses, output JSON

**Key Requirements**:
- Use prompt caching (system message with rubric)
- Process all students in one file
- Output: `[assignment_name]_GRADED.json` with scores + feedback
- No interaction required - runs headless

---

## Cost Estimates

**Per 30-student assignment (avg 300 words/response)**:
- With prompt caching: ~$0.015
- Without caching: ~$1.50
- **Time saved**: ~75 minutes vs manual grading

---

## Current Status

✅ **Phase 1 Complete**: Text extraction from both CSV and API
⏳ **Phase 2 Next**: Build LLM grading engine
⏳ **Phase 3 Future**: Canvas grade upload automation
