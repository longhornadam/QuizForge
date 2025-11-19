# Advanced Quizzes API Development Goals

**Focus:** Extend QuizForge from static QTI exports to full Canvas New Quizzes lifecycle management (creation, configuration, differentiation, analytics).

---

## 1. Core Objectives
- Create and publish New Quizzes directly via API without manual import.
- Configure advanced quiz settings (due dates, availability windows, attempts, calculators, feedback policies).
- Apply student accommodations and differentiation (assign to sections, extended time, additional attempts).
- Attach question banks/item banks and align quizzes with outcomes post-import.
- Retrieve submissions for AI-assisted grading and push scores/comments back.

---

## 2. Primary Canvas APIs to Master
- `POST /api/quiz/v1/courses/:course_id/quizzes` – create quiz shells.
- `POST /api/quiz/v1/quizzes/:quiz_id/items` – add New Quiz items (MC, essay, numerical, hot spot, etc.).
- `PUT /api/quiz/v1/quizzes/:quiz_id` – update quiz metadata (due dates, settings, publish state).
- `POST /api/v1/courses/:course_id/quizzes/:quiz_id/assign_to` – differentiation by section/student.
- `POST /api/v1/courses/:course_id/quizzes/:quiz_id/time_extensions` – accommodations (extra minutes/attempts).
- `POST /api/v1/courses/:course_id/outcome_alignments` – align items to TEKS after quiz creation.
- `GET /api/v1/courses/:course_id/assignments/:assignment_id/submissions` – retrieve responses for grading.
- `PUT /api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id` – return grades/comments.

---

## 3. Prototype Milestones
1. **Token Smoke Test** – list existing quizzes, confirm API auth + course IDs.
2. **Quiz Shell Creator** – given metadata JSON, create/publish a New Quiz shell.
3. **Item Builder** – map QuizForge question models to New Quiz item payloads (multiple choice, essay, numerical first).
4. **Outcome Aligner** – after quiz creation, align selected items to outcomes via REST endpoint.
5. **Differentiation Engine** – assign quiz to student groups/sections with custom dates.
6. **Accommodations Toolkit** – apply extra time or attempts per student using extensions endpoint.
7. **Submission Pipeline** – fetch student responses, score via LLM, push rubric-style comments + grades back.

---

## 4. Advanced Scenarios to Explore
- **Result View Settings:** Configure what students can see (item feedback, responses, scores).
- **Item Banks:** Investigate API support for creating/attaching item bank questions.
- **Lockdown Settings:** Toggle calculator, shuffle, access codes, IP filters.
- **Quiz Migration:** Import existing QTI, convert to API-managed quiz, and sync edits afterward.
- **Analytics Hooks:** Use outcome rollups or quiz reports to detect struggling outcomes automatically.

---

## 5. Integration Patterns
- **Declarative Quiz Specs:** JSON/YAML blueprint that QuizForge LLM generates; runner posts to Canvas.
- **Two-Phase Publish:** Draft quiz for teacher review → API call to publish once approved.
- **Reconciliation Script:** Compare Canvas quiz state vs. local spec; update or flag differences.
- **Error Handling:** Capture API errors, log context (payload, quiz name, course) for debugging.

---

## 6. Suggested Next Experiments
1. Build `new_quiz_create.py` prototype that accepts quiz metadata + 1 question and posts to Canvas.
2. Implement `quiz_settings_patch.py` to toggle result view options and due dates.
3. Develop `apply_accommodations.py` to extend time for selected student IDs.
4. Prototype `fetch_quiz_submissions.py` to pull essay responses for AI scoring pilot.
5. Document payload templates for each supported question type (MC, essay, matching, numerical, ordering).
