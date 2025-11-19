# Auto-Grader Development Goals

## Overview
Automated grading system using Canvas API to pull student submissions (particularly short-answer/essay responses), grade them using LLMs, and push feedback and scores back to Canvas.

## Current Status

### ✅ Completed (Phase 1)
- **Canvas API Integration**: Successfully authenticate and pull submissions
- **Standard Assignment Support**: Can retrieve `online_text_entry` submissions (essays, SCRs)
- **Data Extraction**: Parse student responses, scores, timestamps, and metadata
- **JSON Export**: Save submission data in structured format for processing

### ⏳ In Progress
- **New Quizzes Support**: Working on question-level response extraction from Quizzes.Next
- **API Permission Issues**: New Quizzes API v1 endpoints returning 404 (may need Canvas admin)

## Goals

### Short Term
1. **Build LLM Grading Engine**
   - Create `canvas_ai_grader.py` module
   - Implement rubric-based grading prompts
   - Support multiple LLM providers (OpenAI, Anthropic)
   - Generate scores and feedback

2. **Test Grade Submission**
   - Verify PUT endpoint for updating grades
   - Test posting feedback as comments
   - Ensure proper error handling

3. **Create Rubric System**
   - Define JSON schema for rubrics
   - Create sample rubrics for ELA assignments
   - Support multiple criteria with point values

### Medium Term
4. **Nightly Automation**
   - Build scheduler for automated grading runs
   - Configuration file for assignments to grade
   - Email notifications for results

5. **Teacher Review Interface**
   - Simple web app to review AI grades before publishing
   - Approve/modify/reject functionality
   - Batch operations

6. **New Quizzes Integration**
   - Resolve API access issues
   - Extract question-level responses from quizzes
   - Support essay questions within quizzes

### Long Term
7. **Advanced Features**
   - Confidence scoring (flag uncertain grades)
   - Learning from teacher modifications
   - Analytics dashboard
   - Multi-attempt support
   - Real-time grading

8. **Standards Integration**
   - Link to Canvas Outcomes/TEKS
   - Track mastery over time
   - Differentiated feedback based on student level

## Technical Details

### API Endpoints Used
- `GET /api/v1/courses/{course_id}/assignments/{assignment_id}/submissions` ✅
- `PUT /api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}` ⏳
- `GET /api/quiz/v1/courses/{course_id}/quizzes` ✅ (partial)
- `GET /api/quiz/v1/quizzes/{quiz_id}/submissions` ❌ (permission issues)

### Files in This Directory
- `canvas_submissions_puller.py` - Pull submissions from Canvas API
- `new_quiz_response_puller.py` - Analyze New Quiz submission structure
- `new_quizzes_api_explorer.py` - Deep dive into New Quizzes API
- `AUTOMATED_GRADING_DESIGN.md` - Complete architecture and implementation plan
- `*.json` - Sample submission data from API calls

### Key Challenges
1. **New Quizzes API Access**: Standard Canvas API doesn't expose question-level responses for New Quizzes
   - Possible solutions: SpeedGrader access, CSV export, admin permissions
2. **Rubric Design**: Need flexible rubric format that works across different assignment types
3. **Feedback Quality**: Ensuring LLM feedback is constructive and grade-appropriate

## Testing Data
- **Course**: ELA 4/5 (ID: 109379)
- **Test Assignment**: "If You Kill Me" Hovey Benjamin SCR (ID: 3286605)
  - Successfully pulled 7 student submissions
  - Full text responses retrieved
- **Test Quiz**: Clark & New Guy Quiz w/ SCR (ID: 3279697)
  - Retrieved submission metadata
  - Question-level responses not accessible yet

## Cost Estimate
- Per assignment (30 students, 200-word responses):
  - GPT-4: ~$0.15
  - Claude Sonnet: ~$0.05
  - GPT-3.5: ~$0.02
- Time savings: ~75 minutes per assignment

## Next Actions
1. Implement `CanvasAIGrader` class with LLM integration
2. Create sample rubric JSON for Hovey Benjamin SCR
3. Test grade submission API
4. Build simple CLI for manual grading first
5. Add nightly scheduler once manual mode proven
6. Investigate Canvas admin help for New Quizzes API access

## Related Documentation
- Canvas API Docs: https://canvas.instructure.com/doc/api/
- New Quizzes API: https://canvas.instructure.com/doc/api/quiz_api.html
- dev_goals.txt (parent) - Overall Canvas API exploration goals
