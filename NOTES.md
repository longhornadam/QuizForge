# QuizForge Development Notes

## Session: 2025-11-16 - Physical Packaging & Validation

### Completed Work

#### 1. Physical Packaging System (PRODUCTION)
**Module:** `packagers/physical_handler.py`

Generated outputs:
- Student quiz DOCX (printable, formatted)
- Answer key DOCX (simple table for grading)
- Rationale sheet DOCX (corrections with embedded answers)

**Key Features:**
- Smart MC layout: 2-column if choices short, 1-column if long
- Stimulus passages integrated seamlessly
- Uses python-docx library
- Always generated alongside Canvas QTI-ZIP

**Formatting Control:**
- Layout logic: `physical_handler.py`
- Style constants: `default_styles.py`
- Common tweak: Rationale spacing in `_create_rationale_sheet()`

---

#### 2. Validation System (PRODUCTION)
**Module:** `validators/`

##### Point Calculator (`point_calculator.py`)
- Automatic point allocation
- ESSAY/FILEUPLOAD = 2.5x multiplier
- Default: 100 points total
- LLM no longer handles points

##### Answer Balancer (`answer_balancer.py`)
- MC: Distributes correct answers across A/B/C/D
- TF: Balances True/False ~50/50
- MA: Shuffles choices randomly
- Updates correct_index after shuffling
- LLM no longer worries about distribution

**Pipeline Integration:**
```
Parse → Calculate Points → Balance Answers → Package
```

---

#### 3. Token Optimization
**File:** `QF_BASE.md`

**Removed (~750-800 tokens):**
- Point weighting heuristics
- Answer distribution instructions  
- Validation checklist preamble
- Point fields from all examples

**Result:** LLM focuses purely on content quality

---

#### 4. Dual Output By Default
Both Canvas QTI-ZIP and Physical DOCXs generated every time.
- No teacher selection needed
- Storage not a concern (GB+ available)
- Provides flexibility (online or paper testing)

---

### Design Decisions

#### Why Script Handles Points
- LLMs bad at arithmetic
- Consistent results
- Easy teacher editing in Canvas
- Reduces token usage

#### Why Script Handles Answer Distribution
- LLMs can't track distribution across questions
- Deterministic balancing guarantees fairness
- Prevents "all correct answers are A" mistakes

#### Why Always Generate Both Outputs
- Teacher may not know they need both until later
- Minimal storage cost
- Simplifies workflow (no decisions)

#### Why DOCX Instead of PDF
- Teacher has Office365, not Acrobat Pro
- Editable outputs preferred
- Can convert to PDF later if needed

---

### File Organization

```
quizforge/
├── parsers/
│   └── text_parser.py (PRODUCTION)
├── validators/
│   ├── point_calculator.py (NEW - PRODUCTION)
│   └── answer_balancer.py (NEW - PRODUCTION)
├── packagers/
│   ├── packager.py (Router - PRODUCTION)
│   ├── canvas_handler.py (PRODUCTION)
│   └── physical_handler.py (NEW - PRODUCTION)
├── default_styles.py (expanded with DOCX constants)
├── orchestrator.py (calls validators now)
└── QF_BASE.md (slimmed ~800 tokens)
```

---

### Quick Reference: Where to Make Changes

**Points allocation:**
- Logic: `validators/point_calculator.py`
- Multipliers: `default_styles.py` (HEAVY_QUESTION_WEIGHT)

**Answer distribution:**
- Logic: `validators/answer_balancer.py`
- No configuration needed

**Physical formatting:**
- Spacing/layout: `packagers/physical_handler.py`
- Constants: `default_styles.py` (margins, fonts, thresholds)

**LLM behavior:**
- System prompt: `QF_BASE.md`
- Question format rules here

---

### Testing Checklist

When testing changes:
- [ ] Generate quiz with mixed question types
- [ ] Verify Canvas import works
- [ ] Open all 3 DOCX files in Word
- [ ] Check answer key matches quiz
- [ ] Verify point totals = 100
- [ ] Check answer distribution in log file
- [ ] Print one page to verify layout

---

### Future Session Notes

**If formatting needs adjustment:**
1. Physical spacing → `physical_handler.py` functions
2. Style constants → `default_styles.py`
3. Don't touch Canvas packaging (working well)

**If adding question types:**
1. Update `QF_BASE.md` format rules
2. Update parser to handle new type
3. Consider if needs special point weighting
4. Consider if needs distribution balancing
5. Update both Canvas and Physical handlers

**If LLM output quality issues:**
1. Check `QF_BASE.md` - might need more guidance
2. Don't add back point/distribution logic
3. Focus on content-quality instructions

---

### Version History

**v2.3 (2025-11-16):**
- ✅ Physical packaging complete
- ✅ Validation system complete  
- ✅ Token optimization complete
- ✅ Dual output by default

**v2.2 (previous):**
- Canvas packaging working
- Text parser working
- LLM handled points and distribution (suboptimal)

---

### Dependencies

**Python Libraries:**
- python-docx (for physical outputs)
- [other dependencies as needed]

**External:**
- Office365 (for teacher editing)
- Canvas LMS (for imports)

---

### Known Good State

As of 2025-11-16, system fully functional:
- Generates valid Canvas QTI packages
- Generates professional DOCX outputs
- Validates and corrects answer distributions
- Allocates points appropriately
- LLM prompt optimized

**No known bugs in core functionality.**