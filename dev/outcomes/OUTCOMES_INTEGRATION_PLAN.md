# QuizForge Outcomes Integration Plan
**Version 1.0 | Created: 2025-11-13**

---

## Executive Summary

**Goal:** Enable QuizForge to attach TEKS/Outcomes to individual quiz questions for Canvas Learning Mastery tracking.

**Strategy:** Three-phase implementation combining text format extension, domain model updates, and post-import API alignment.

**Timeline:** 
- Phase 1 (Foundation): 1-2 weeks
- Phase 2 (QTI Metadata): 1 week  
- Phase 3 (API Alignment): 2-3 weeks

---

## Background

### Current State
- QuizForge generates Canvas-compatible QTI packages
- Questions can be created from LLM prompts or text specs
- No outcome/standard alignment capability
- Data tracking limited to grade-level metrics

### Desired State
- Every question can be tagged with 1+ outcome codes (e.g., `CS.6.A`, `ELA.7.5.B`)
- Outcomes appear in Canvas Learning Mastery Gradebook
- Teachers can run outcome-level reports across students/courses
- Supports both manual tagging and LLM-suggested alignment

### Canvas Reality Check
✅ **API Approach:** Full support via Outcome Alignments API  
⚠️ **QTI Metadata:** Limited/unreliable import support  
📊 **Hybrid Strategy:** Embed metadata in QTI + API fallback for guaranteed alignment

---

## Phase 1: Foundation & Data Model

### 1.1 Extend Question Domain Models

**File:** `Packager_Canvas/quizforge/domain/questions.py`

Add outcome tracking to base `Question` class:

```python
@dataclass
class Question:
    qtype: str
    prompt: str
    points: float = 10.0
    points_set: bool = False
    parent_stimulus_ident: Optional[str] = None
    parent_stimulus_title: Optional[str] = None
    forced_ident: Optional[str] = None
    # NEW: Outcome alignment
    outcome_ids: List[str] = field(default_factory=list)
    outcome_tags: Optional[str] = None  # Raw comma-separated from text input
```

**Rationale:**
- `outcome_ids`: Parsed list of standard codes (e.g., `["CS.6.A", "CS.7.B"]`)
- `outcome_tags`: Preserves original text input for validation/debugging
- Inherited by all question types (MC, Essay, TF, etc.)

### 1.2 Extend Text Format Specification

**Files to Update:**
- `LLM_Modules/QF_BASE.md` (Section 5: Field Definitions)
- `User_Docs/guides/NUMERIC_MODULE_CHOOSER.md` (if applicable)

**New Field:**
```
Outcomes: CS.6.A, CS.7.B, CS.8.C
```

**Format Rules:**
- Optional field for all question types
- Comma-separated list of outcome codes
- Whitespace trimmed automatically
- Case-insensitive matching against known outcomes
- Empty/missing = no alignment

**Example Question Block:**
```
Type: MC
Points: 10
Outcomes: CS.6.A, CS.7.B
Prompt:
Which Python keyword declares a function?
Choices:
- [ ] func
- [x] def
- [ ] function
- [ ] define
---
```

### 1.3 Create Outcome Registry/Loader

**New File:** `Packager_Canvas/quizforge/domain/outcomes.py`

```python
"""Outcome/standard registry and validation."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class Outcome:
    """Represents a course outcome/standard."""
    code: str  # e.g., "CS.6.A"
    name: str
    description: str
    friendly_name: Optional[str] = None
    friendly_description: Optional[str] = None
    category: Optional[str] = None  # "S" (Supporting) or "R" (Readiness)


class OutcomeRegistry:
    """Load and validate outcome codes from text files."""
    
    def __init__(self):
        self.outcomes: Dict[str, Outcome] = {}
    
    def load_from_file(self, path: Path) -> None:
        """Parse outcomes from dev/outcomes/*.txt format."""
        # Implementation: Parse Name:/Description: blocks
        pass
    
    def load_from_directory(self, dir_path: Path) -> None:
        """Load all *.txt files from directory."""
        pass
    
    def validate_code(self, code: str) -> bool:
        """Check if outcome code exists."""
        return code.upper() in self.outcomes
    
    def get_outcome(self, code: str) -> Optional[Outcome]:
        """Retrieve outcome by code."""
        return self.outcomes.get(code.upper())
    
    def suggest_matches(self, partial: str) -> List[Outcome]:
        """Fuzzy match for user typos."""
        pass
```

**Registry Location:**
- Load from `dev/outcomes/*.txt` at package time
- Or from `LLM_Modules/Course Outcomes TEKS/` (consolidated location)
- Support multiple subject areas (CS, ELA, Math, Science)

### 1.4 Update Text Parser

**File:** `Packager_Canvas/quizforge/io/parsers/text_parser.py` (or equivalent)

Add outcome parsing logic:

```python
def parse_question_block(lines: List[str]) -> Question:
    # ... existing parsing ...
    
    # NEW: Parse Outcomes field
    if "Outcomes:" in block_text:
        outcome_line = extract_field("Outcomes:", block_text)
        outcome_tags = outcome_line.strip()
        outcome_ids = [code.strip() for code in outcome_tags.split(",")]
        question.outcome_tags = outcome_tags
        question.outcome_ids = outcome_ids
    
    return question
```

**Validation:**
- Warn if outcome code not in registry (don't block export)
- Log unrecognized codes for teacher review
- Suggest corrections for typos (e.g., "CS.6.a" → "CS.6.A")

---

## Phase 2: QTI Metadata Embedding

### 2.1 Extend QTI Renderer

**File:** `Packager_Canvas/quizforge/renderers/qti/assessment.py`

Add outcome metadata to `<itemmetadata>` block:

```python
def render_item_metadata(question: Question) -> ET.Element:
    itemmetadata = ET.SubElement(item, "itemmetadata")
    qtimetadata = ET.SubElement(itemmetadata, "qtimetadata")
    
    # Existing fields: question_type, points_possible, etc.
    # ...
    
    # NEW: Outcome alignment metadata
    if question.outcome_ids:
        for outcome_code in question.outcome_ids:
            field = ET.SubElement(qtimetadata, "qtimetadatafield")
            ET.SubElement(field, "fieldlabel").text = "outcome_alignment"
            ET.SubElement(field, "fieldentry").text = outcome_code
    
    return itemmetadata
```

**QTI Output Example:**
```xml
<item ident="item_q1_abc123" title="Q01_Functions">
  <itemmetadata>
    <qtimetadata>
      <qtimetadatafield>
        <fieldlabel>question_type</fieldlabel>
        <fieldentry>multiple_choice_question</fieldentry>
      </qtimetadatafield>
      <qtimetadatafield>
        <fieldlabel>points_possible</fieldlabel>
        <fieldentry>10.0</fieldentry>
      </qtimetadatafield>
      <qtimetadatafield>
        <fieldlabel>outcome_alignment</fieldlabel>
        <fieldentry>CS.6.A</fieldentry>
      </qtimetadatafield>
      <qtimetadatafield>
        <fieldlabel>outcome_alignment</fieldlabel>
        <fieldentry>CS.7.B</fieldentry>
      </qtimetadatafield>
    </qtimetadata>
  </itemmetadata>
  <!-- question content -->
</item>
```

### 2.2 Generate Alignment Manifest

**New File:** `Packager_Canvas/quizforge/renderers/qti/outcome_manifest.py`

Create JSON sidecar for API alignment fallback:

```python
def generate_outcome_manifest(quiz: Quiz) -> dict:
    """Create JSON mapping questions to outcomes."""
    manifest = {
        "quiz_title": quiz.title,
        "generated_at": datetime.now().isoformat(),
        "alignments": []
    }
    
    for idx, question in enumerate(quiz.questions, 1):
        if question.outcome_ids:
            manifest["alignments"].append({
                "question_number": idx,
                "question_ident": get_item_ident(question, idx),
                "outcome_codes": question.outcome_ids,
                "question_prompt_preview": question.prompt[:100]
            })
    
    return manifest
```

**Output:** `outcome_alignments.json` included in QTI ZIP

**Purpose:**
- If Canvas ignores QTI metadata → API tool reads JSON to align programmatically
- Provides audit trail of intended alignments
- Human-readable for teacher verification

---

## Phase 3: API-Based Alignment Tool

### 3.1 Post-Import Alignment Script

**New File:** `Packager_Canvas/quizforge/services/outcome_aligner.py`

```python
"""Align outcomes via Canvas API after QTI import."""

import requests
from typing import List, Dict


class OutcomeAligner:
    def __init__(self, canvas_url: str, api_token: str):
        self.base_url = canvas_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_token}"}
    
    def get_course_outcomes(self, course_id: int) -> List[Dict]:
        """Fetch all outcomes available in course."""
        url = f"{self.base_url}/api/v1/courses/{course_id}/outcome_groups"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def find_outcome_by_code(self, course_id: int, code: str) -> Optional[int]:
        """Map outcome code (e.g., CS.6.A) to Canvas outcome ID."""
        outcomes = self.get_course_outcomes(course_id)
        for group in outcomes:
            for outcome in group.get("outcomes", []):
                if code in outcome.get("title", "") or code in outcome.get("short_description", ""):
                    return outcome["id"]
        return None
    
    def get_quiz_questions(self, course_id: int, quiz_id: int) -> List[Dict]:
        """Retrieve all questions from imported quiz."""
        url = f"{self.base_url}/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def align_outcome_to_question(
        self,
        course_id: int,
        quiz_id: int,
        question_id: int,
        outcome_id: int
    ) -> bool:
        """Create outcome alignment for specific question."""
        url = f"{self.base_url}/api/v1/courses/{course_id}/outcome_alignments"
        payload = {
            "asset_type": "quizzes.quiz",
            "asset_id": quiz_id,
            "learning_outcome_id": outcome_id,
            "artifact_type": "quizzes.quiz.question",
            "artifact_id": question_id
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.status_code == 201
    
    def process_manifest(
        self,
        course_id: int,
        quiz_id: int,
        manifest_path: Path
    ) -> Dict[str, int]:
        """Read outcome_alignments.json and apply via API."""
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        stats = {"success": 0, "failed": 0, "skipped": 0}
        questions = self.get_quiz_questions(course_id, quiz_id)
        
        for alignment in manifest["alignments"]:
            q_num = alignment["question_number"]
            outcome_codes = alignment["outcome_codes"]
            
            # Match by position (Canvas preserves order from QTI)
            if q_num > len(questions):
                stats["skipped"] += 1
                continue
            
            canvas_question_id = questions[q_num - 1]["id"]
            
            for code in outcome_codes:
                outcome_id = self.find_outcome_by_code(course_id, code)
                if not outcome_id:
                    print(f"Warning: Outcome {code} not found in course")
                    stats["skipped"] += 1
                    continue
                
                success = self.align_outcome_to_question(
                    course_id, quiz_id, canvas_question_id, outcome_id
                )
                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
        
        return stats
```

### 3.2 CLI Tool for Teachers

**New File:** `Packager_Canvas/align_outcomes.py`

```python
"""CLI tool to align outcomes after quiz import."""

import argparse
from pathlib import Path
from quizforge.services.outcome_aligner import OutcomeAligner


def main():
    parser = argparse.ArgumentParser(
        description="Align outcomes to Canvas quiz via API"
    )
    parser.add_argument("--canvas-url", required=True, help="Canvas instance URL")
    parser.add_argument("--token", required=True, help="Canvas API token")
    parser.add_argument("--course-id", type=int, required=True)
    parser.add_argument("--quiz-id", type=int, required=True)
    parser.add_argument("--manifest", type=Path, required=True,
                        help="Path to outcome_alignments.json")
    
    args = parser.parse_args()
    
    aligner = OutcomeAligner(args.canvas_url, args.token)
    stats = aligner.process_manifest(
        args.course_id,
        args.quiz_id,
        args.manifest
    )
    
    print(f"\n✓ Successfully aligned: {stats['success']}")
    print(f"✗ Failed: {stats['failed']}")
    print(f"⊘ Skipped: {stats['skipped']}")


if __name__ == "__main__":
    main()
```

**Usage:**
```powershell
python align_outcomes.py \
  --canvas-url https://pearlandisd.instructure.com \
  --token YOUR_API_TOKEN \
  --course-id 12345 \
  --quiz-id 67890 \
  --manifest Finished_Exports/outcome_alignments.json
```

---

## Phase 4: LLM Integration

### 4.1 Update LLM System Prompts

**File:** `LLM_Modules/QF_BASE.md`

Add outcome guidance to Section 5 (Field Definitions):

```markdown
| `Outcomes:` | Optional | Comma-separated outcome codes (e.g., `CS.6.A, CS.7.B`). Leave blank if unknown. |
```

Add to Section 2 (Understanding Teacher Requests):

```markdown
### Outcome Alignment
When teachers reference standards, TEKS, or learning objectives:
- If explicit codes provided (e.g., "CS.6.A"), use verbatim
- If descriptive ("variables and data types"), suggest relevant codes from loaded registry
- If ambiguous, omit `Outcomes:` field rather than guessing
- Multiple outcomes per question allowed when concepts overlap
```

### 4.2 Create Subject-Specific Outcome Modules

**New Files:**
- `LLM_Modules/QF_OUTCOMES_CS.md` (Computer Science TEKS)
- `LLM_Modules/QF_OUTCOMES_ELA7.md` (7th Grade ELA TEKS)

**Content Structure:**
```markdown
# QuizForge Outcome Module: Computer Science TEKS
**Subject:** Computer Science (Programming focus)
**Grade Level:** 6-12
**Standard Set:** Texas Essential Knowledge and Skills

## Quick Reference

### Syntax & Fundamentals
- `CS.6.A` - Define/use primitive data types
- `CS.6.B` - Declare/use variables
- `CS.7.A` - Arithmetic/logic/Boolean operators

### Control Structures
- `CS.8.A` - Selection (if/elif/else)
- `CS.8.B` - Iteration (while/for loops)

### Functions & Modularity
- `CS.9.A` - Define/call functions
- `CS.9.B` - Pass parameters, return values

[Full listing follows...]
```

**LLM Usage:**
- Load relevant outcome module when teacher specifies subject
- Reference codes in question generation
- Auto-suggest outcomes based on question content

### 4.3 Outcome Suggestion Logic

Add to conductor agent logic:

```python
def suggest_outcomes(question: Question, registry: OutcomeRegistry) -> List[str]:
    """Suggest relevant outcome codes based on question content."""
    prompt_lower = question.prompt.lower()
    suggestions = []
    
    # Keyword matching
    keyword_map = {
        "variable": ["CS.6.B"],
        "function": ["CS.9.A", "CS.9.B"],
        "loop": ["CS.8.B"],
        "if statement": ["CS.8.A"],
        "data type": ["CS.6.A"],
        # ... more mappings
    }
    
    for keyword, codes in keyword_map.items():
        if keyword in prompt_lower:
            suggestions.extend(codes)
    
    return list(set(suggestions))  # Deduplicate
```

---

## Implementation Checklist

### Phase 1: Foundation (Weeks 1-2)
- [ ] Add `outcome_ids` and `outcome_tags` to `Question` dataclass
- [ ] Create `OutcomeRegistry` class in `domain/outcomes.py`
- [ ] Implement outcome loader for `dev/outcomes/*.txt` format
- [ ] Update text parser to handle `Outcomes:` field
- [ ] Add validation warnings for unrecognized codes
- [ ] Write unit tests for outcome parsing
- [ ] Update `QF_BASE.md` documentation

### Phase 2: QTI Metadata (Week 3)
- [ ] Extend `render_item_metadata()` to include outcome fields
- [ ] Create `generate_outcome_manifest()` function
- [ ] Include `outcome_alignments.json` in ZIP package
- [ ] Test QTI import with metadata (verify Canvas behavior)
- [ ] Document QTI metadata limitations in README

### Phase 3: API Alignment (Weeks 4-6)
- [ ] Implement `OutcomeAligner` class
- [ ] Add Canvas API endpoint wrappers
- [ ] Create CLI tool `align_outcomes.py`
- [ ] Test with live Canvas course (sandbox first)
- [ ] Handle rate limiting and error cases
- [ ] Write API alignment guide for teachers

### Phase 4: LLM Integration (Ongoing)
- [ ] Create outcome reference modules per subject
- [ ] Update system prompts with outcome guidance
- [ ] Implement outcome suggestion heuristics
- [ ] Test LLM-generated outcome tags for accuracy
- [ ] Refine keyword mappings based on teacher feedback

---

## Testing Strategy

### Unit Tests
```python
def test_outcome_parsing():
    """Verify Outcomes: field correctly parsed."""
    block = """
    Type: MC
    Outcomes: CS.6.A, CS.7.B
    Prompt: Test question
    """
    question = parse_question_block(block)
    assert question.outcome_ids == ["CS.6.A", "CS.7.B"]

def test_outcome_validation():
    """Warn on invalid codes without blocking."""
    registry = OutcomeRegistry()
    registry.load_from_file("dev/outcomes/CS_Outcomes.txt")
    assert registry.validate_code("CS.6.A") is True
    assert registry.validate_code("INVALID.CODE") is False
```

### Integration Tests
1. **Text → QTI:** Generate quiz with outcomes, verify XML metadata
2. **QTI → Canvas:** Import quiz, check if metadata preserved
3. **API Alignment:** Run CLI tool, verify Learning Mastery Gradebook
4. **End-to-End:** LLM generates quiz with outcomes → Canvas alignment complete

### Validation Scenarios
- Single outcome per question
- Multiple outcomes per question
- Mixed: some questions with outcomes, some without
- Invalid outcome codes (should warn, not fail)
- Empty `Outcomes:` field
- Whitespace variations (`CS.6.A`, ` CS.6.A `, `CS.6.A,CS.7.B`)

---

## Success Criteria

### Minimum Viable Product (MVP)
✓ Teachers can manually add `Outcomes:` to text specs  
✓ QTI includes outcome metadata in `<qtimetadata>`  
✓ API tool successfully aligns outcomes post-import  
✓ Alignments visible in Canvas Learning Mastery Gradebook

### Full Feature Set
✓ LLM auto-suggests outcomes based on question content  
✓ Outcome registry supports multiple subjects  
✓ Validation prevents typos via fuzzy matching  
✓ Teacher documentation with examples  
✓ API tool handles bulk alignment (all quizzes in course)

### Quality Metrics
- 90%+ accuracy in LLM outcome suggestions
- <5% false positives (incorrect alignments)
- API alignment completes in <30 seconds for 50-question quiz
- Zero manual XML editing required

---

## Documentation Deliverables

### For Teachers
- [ ] **User Guide:** `User_Docs/guides/OUTCOME_ALIGNMENT.md`
  - How to add outcomes to questions
  - How to use API alignment tool
  - Interpreting Learning Mastery reports
  
- [ ] **Video Tutorial:** Screen recording of end-to-end workflow

### For Developers
- [ ] **Technical Spec:** This document
- [ ] **API Reference:** Canvas outcome endpoints used
- [ ] **Code Comments:** Inline documentation for outcome classes

### For LLM
- [ ] **Outcome Modules:** Subject-specific code references
- [ ] **System Prompt Updates:** Outcome field usage guidance

---

## Risk Mitigation

### Risk: Canvas Ignores QTI Metadata
**Likelihood:** High (documented limitation)  
**Impact:** Medium (requires API fallback)  
**Mitigation:** Always generate JSON manifest + API tool as primary method

### Risk: Outcome Codes Change (TEKS Updates)
**Likelihood:** Low (every 5-10 years)  
**Impact:** High (all tags invalid)  
**Mitigation:** Version outcome registries; maintain legacy mappings

### Risk: Teachers Enter Invalid Codes
**Likelihood:** Medium (typos common)  
**Impact:** Low (validation catches most)  
**Mitigation:** Fuzzy matching + suggestions; warnings not errors

### Risk: LLM Suggests Wrong Outcomes
**Likelihood:** Medium (ambiguous content)  
**Impact:** Medium (inaccurate data tracking)  
**Mitigation:** Teacher review required; mark auto-suggested vs. manual

---

## Future Enhancements

### Phase 5: Advanced Features (Post-MVP)
- **Bulk Re-Alignment:** Update outcomes across multiple existing quizzes
- **Outcome Analytics:** Report on outcome coverage across course
- **Smart Suggestions:** ML model trained on teacher alignments
- **Cross-Subject Mapping:** Suggest ELA outcomes for CS writing prompts
- **Version Control:** Track outcome changes over time
- **Import from Canvas:** Pull existing alignments into QuizForge format

### Integration with Other Systems
- **Google Classroom:** Align to Google Classroom skills tracking
- **Schoology:** Export alignment data for Schoology Learning Objectives
- **PowerSchool:** Direct integration with SIS standards

---

## Appendix A: Example Workflows

### Workflow 1: Teacher Manually Tags Outcomes

1. Teacher writes quiz spec:
```
Title: Python Functions Quiz
---
Type: MC
Points: 10
Outcomes: CS.9.A
Prompt:
What keyword defines a function in Python?
Choices:
- [ ] func
- [x] def
- [ ] function
- [ ] define
---
```

2. Run packager:
```powershell
python run_packager.py quiz_spec.txt
```

3. Import QTI to Canvas (outcomes in metadata)

4. Run alignment tool:
```powershell
python align_outcomes.py --canvas-url ... --quiz-id 12345 --manifest outcome_alignments.json
```

5. Verify in Learning Mastery Gradebook

### Workflow 2: LLM Auto-Generates with Outcomes

1. Teacher prompts LLM:
```
Create a 10-question quiz on Python functions for CS1.
Include outcome alignments.
```

2. LLM loads CS outcome module, generates:
```
Type: MC
Outcomes: CS.9.A
Prompt: [question about function definition]
---
Type: MC
Outcomes: CS.9.B
Prompt: [question about parameters]
---
```

3. Teacher reviews/adjusts outcomes if needed

4. Export → Import → Align (same as Workflow 1)

### Workflow 3: Bulk Update Existing Quizzes

1. Generate manifest for all quizzes in course:
```powershell
python export_outcomes.py --course-id 12345 --output-dir manifests/
```

2. Edit manifests to add missing outcomes

3. Bulk re-align:
```powershell
python align_outcomes.py --bulk --course-id 12345 --manifest-dir manifests/
```

---

## Appendix B: Canvas API Endpoints

### Outcome Groups (List Available Outcomes)
```
GET /api/v1/courses/:course_id/outcome_groups
GET /api/v1/courses/:course_id/outcome_group_links
```

### Outcome Alignments (Link to Questions)
```
POST /api/v1/courses/:course_id/outcome_alignments
GET /api/v1/courses/:course_id/outcome_alignments
DELETE /api/v1/courses/:course_id/outcome_alignments/:id
```

### Quiz Questions (Get IDs Post-Import)
```
GET /api/v1/courses/:course_id/quizzes/:quiz_id/questions
```

### Outcome Results (View Mastery Data)
```
GET /api/v1/courses/:course_id/outcome_results
GET /api/v1/courses/:course_id/outcome_rollups
```

**Rate Limits:** 3000 requests/hour per token (Canvas default)

---

## Appendix C: Sample Outcome Registry Format

**Source:** `dev/outcomes/CS_Outcomes.txt`

```
Name: CS.6.A [S] - Define/Use Primitive Data Types
Friendly Name: CS.6.A [S] - Define/Use Primitive Data Types
Description: define and use data types, including integer, Boolean, character, and string, and their arithmetic, relational, and logical operators in computer programs;
Friendly Description: define and use data types, including integer, Boolean, character, and string, and their arithmetic, relational, and logical operators in computer programs;
```

**Parsed Structure:**
```python
Outcome(
    code="CS.6.A",
    name="CS.6.A [S] - Define/Use Primitive Data Types",
    description="define and use data types...",
    friendly_name="CS.6.A [S] - Define/Use Primitive Data Types",
    friendly_description="define and use data types...",
    category="S"  # Supporting standard
)
```

---

## Contact & Questions

**Project Lead:** W. Beckham  
**Repository:** QuizForge (Pearland ISD)  
**Last Updated:** 2025-11-13  
**Status:** Plan Approved, Implementation Pending
