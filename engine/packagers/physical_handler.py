"""Physical quiz DOCX handler.

Converts validated Quiz objects into printable DOCX files.
Generates student quiz + answer key + rationale sheet.
Performs NO validation - trusts input is perfect.
"""

from pathlib import Path
from typing import Dict, List
import re
from engine.core.quiz import Quiz
from engine.rendering.physical.styles.default_styles import (
    DOCX_FONT_FAMILY,
    DOCX_TITLE_SIZE,
    DOCX_HEADING_SIZE,
    DOCX_BODY_SIZE,
    DOCX_SMALL_SIZE,
    DOCX_MARGIN_TOP,
    DOCX_MARGIN_BOTTOM,
    DOCX_MARGIN_LEFT,
    DOCX_MARGIN_RIGHT,
    DOCX_PARA_SPACING_BEFORE,
    DOCX_PARA_SPACING_AFTER,
    DOCX_LINE_SPACING,
    MC_TWO_COLUMN_THRESHOLD,
    TABLE_HEADER_BOLD,
    TABLE_GRID_LINES,
    TABLE_COL_WIDTHS,
    LOG_ANSWER_CHOICE_STATS,
    LOG_QUESTION_LENGTH_STATS,
    LOG_POINT_VALUE_DISTRIBUTION,
    LOG_STIMULUS_USAGE
)


class PhysicalHandler:
    """Generate printable DOCX files."""
    
    def package(self, quiz: Quiz, output_base: str) -> Dict[str, str]:
        """Create student quiz, answer key, and rationale sheet DOCX files.
        
        Args:
            quiz: Validated Quiz object
            output_base: Base directory for output files
            
        Returns:
            Dict with 'quiz_path', 'key_path', 'rationale_path'
        """
        try:
            results = generate_physical_outputs(quiz, output_base)
            return results
        except Exception as e:
            # Log error and return partial results
            error_log_path = Path(output_base) / "physical_error.log"
            error_log_path.write_text(f"Physical generation failed: {e}", encoding='utf-8')
            return {
                'quiz_path': '',
                'key_path': '',
                'rationale_path': '',
                'error_log': str(error_log_path)
            }


def generate_physical_outputs(quiz: Quiz, output_folder: str) -> Dict[str, str]:
    """
    Generate all three physical DOCX files.
    
    Args:
        quiz: Validated Quiz object
        output_folder: Path to quiz-specific output folder
        
    Returns:
        {
            'quiz_path': str,
            'key_path': str, 
            'rationale_path': str,
            'log_path': str
        }
    """
    # Create student quiz DOCX
    quiz_path = _create_student_quiz(quiz, output_folder)
    
    # Create answer key DOCX
    key_path = _create_answer_key(quiz, output_folder)
    
    # Create rationale sheet DOCX
    rationale_path = _create_rationale_sheet(quiz, output_folder)
    
    # Generate validation log
    log_path = Path(output_folder) / "physical_validation.log"
    _log_validation_stats(quiz, str(log_path))
    
    # Return paths
    return {
        'quiz_path': quiz_path,
        'key_path': key_path,
        'rationale_path': rationale_path,
        'log_path': str(log_path)
    }


def _create_student_quiz(quiz: Quiz, output_folder: str) -> str:
    """Generate student-facing quiz DOCX."""
    from docx import Document
    from docx.shared import Inches, Pt
    
    doc = Document()
    
    # Set margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(DOCX_MARGIN_TOP)
        section.bottom_margin = Inches(DOCX_MARGIN_BOTTOM)
        section.left_margin = Inches(DOCX_MARGIN_LEFT)
        section.right_margin = Inches(DOCX_MARGIN_RIGHT)
    
    # Add quiz title
    title = doc.add_paragraph(quiz.title)
    title_format = title.runs[0].font
    title_format.name = DOCX_FONT_FAMILY
    title_format.size = Pt(DOCX_TITLE_SIZE)
    title_format.bold = True
    
    # Add blank lines for student name/date
    doc.add_paragraph('Name: _________________________  Date: __________')
    doc.add_paragraph()  # blank line
    
    # Process questions grouped by stimulus
    stimulus_groups = _group_questions_by_stimulus(quiz.questions)
    
    question_number = 1
    for group in stimulus_groups:
        if group['stimulus']:
            # Add stimulus passage
            p = doc.add_paragraph()
            stimulus_run = p.add_run(_clean_prompt_text(group['stimulus']))
            stimulus_run.italic = True
            stimulus_run.font.name = DOCX_FONT_FAMILY
            stimulus_run.font.size = Pt(DOCX_BODY_SIZE)
            doc.add_paragraph()  # spacing
        
        # Add questions in this group
        for q in group['questions']:
            _add_question_to_doc(doc, q, question_number)
            question_number += 1
    
    # Save document
    output_path = Path(output_folder) / f"{quiz.title.replace(' ', '_')}.docx"
    doc.save(str(output_path))
    return str(output_path)


def _create_answer_key(quiz: Quiz, output_folder: str) -> str:
    """Generate teacher answer key DOCX."""
    from docx import Document
    from docx.shared import Inches, Pt
    
    doc = Document()
    
    # Set margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(DOCX_MARGIN_TOP)
        section.bottom_margin = Inches(DOCX_MARGIN_BOTTOM)
        section.left_margin = Inches(DOCX_MARGIN_LEFT)
        section.right_margin = Inches(DOCX_MARGIN_RIGHT)
    
    # Add title
    title = doc.add_paragraph(f"{quiz.title} - Answer Key")
    title_format = title.runs[0].font
    title_format.name = DOCX_FONT_FAMILY
    title_format.size = Pt(DOCX_TITLE_SIZE)
    title_format.bold = True
    
    doc.add_paragraph()  # spacing
    
    # Get scorable questions only
    scorable_questions = quiz.scorable_questions()
    num_questions = len(scorable_questions)
    
    if num_questions > 0:
        # Create table: header + data rows
        table = doc.add_table(rows=num_questions + 1, cols=3)
        table.style = 'Table Grid'
        
        # Set column widths
        table.columns[0].width = Inches(TABLE_COL_WIDTHS['question_num'])
        table.columns[1].width = Inches(TABLE_COL_WIDTHS['correct_answer'])
        table.columns[2].width = Inches(TABLE_COL_WIDTHS['points'])
        
        # Header row
        header_cells = table.rows[0].cells
        header_cells[0].text = 'Question #'
        header_cells[1].text = 'Correct Answer'
        header_cells[2].text = 'Points'
        
        # Bold headers if configured
        if TABLE_HEADER_BOLD:
            for cell in header_cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
                        run.font.name = DOCX_FONT_FAMILY
                        run.font.size = Pt(DOCX_BODY_SIZE)
        
        # Data rows
        question_number = 1
        for idx, question in enumerate(quiz.questions, start=1):
            from engine.core.questions import StimulusItem, StimulusEnd
            
            # Skip non-scorable questions
            if isinstance(question, (StimulusItem, StimulusEnd)):
                continue
                
            row_cells = table.rows[question_number].cells
            
            # Question number
            row_cells[0].text = str(question_number)
            
            # Correct answer
            answer_text = _get_correct_answer_text(question)
            row_cells[1].text = answer_text
            
            # Points
            row_cells[2].text = str(question.points)
            
            # Style the data cells
            for cell in row_cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = DOCX_FONT_FAMILY
                        run.font.size = Pt(DOCX_BODY_SIZE)
            
            question_number += 1
        
        # Add total points
        doc.add_paragraph()
        total_points = quiz.total_points()
        total_para = doc.add_paragraph(f"Total Points: {total_points}")
        total_format = total_para.runs[0].font
        total_format.name = DOCX_FONT_FAMILY
        total_format.size = Pt(DOCX_BODY_SIZE)
        total_format.bold = True
    
    # Save document
    output_path = Path(output_folder) / f"{quiz.title.replace(' ', '_')}_KEY.docx"
    doc.save(str(output_path))
    return str(output_path)


def _create_rationale_sheet(quiz: Quiz, output_folder: str) -> str:
    """Generate student rationale/corrections sheet DOCX."""
    from docx import Document
    from docx.shared import Inches, Pt
    
    doc = Document()
    
    # Set margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(DOCX_MARGIN_TOP)
        section.bottom_margin = Inches(DOCX_MARGIN_BOTTOM)
        section.left_margin = Inches(DOCX_MARGIN_LEFT)
        section.right_margin = Inches(DOCX_MARGIN_RIGHT)
    
    # Add title
    title = doc.add_paragraph(f"{quiz.title} - Rationales")
    title_format = title.runs[0].font
    title_format.name = DOCX_FONT_FAMILY
    title_format.size = Pt(DOCX_TITLE_SIZE)
    title_format.bold = True
    
    # Add instructions
    instructions = doc.add_paragraph("Use this sheet to write corrections for questions you missed.")
    instructions_format = instructions.runs[0].font
    instructions_format.name = DOCX_FONT_FAMILY
    instructions_format.size = Pt(DOCX_BODY_SIZE)
    
    doc.add_paragraph()  # blank line
    
    # Build rationale lookup by item_id if available
    rationale_lookup = {}
    for entry in quiz.rationales or []:
        if isinstance(entry, dict):
            item_id = entry.get("item_id")
            if item_id:
                rationale_lookup[item_id] = entry.get("text") or entry.get("correct") or ""
        elif isinstance(entry, str):
            # fallback parsing "id: text"
            if ":" in entry:
                item_id, text = entry.split(":", 1)
                rationale_lookup[item_id.strip()] = text.strip()
    
    # Process questions
    question_number = 1
    for question in quiz.questions:
        from engine.core.questions import StimulusItem, StimulusEnd
        
        # Skip non-scorable questions
        if isinstance(question, (StimulusItem, StimulusEnd)):
            continue
        
        # Skip ESSAY and FILEUPLOAD (no rationales needed)
        if question.qtype in ['ESSAY', 'FILEUPLOAD']:
            question_number += 1
            continue
        
        rationale = None
        q_id = getattr(question, "forced_ident", None)
        if q_id and q_id in rationale_lookup:
            rationale = rationale_lookup[q_id]

        # Fallback to basic rationale if missing
        if not rationale:
            rationale = _format_rationale_with_answer(question)
        
        # Format: "Q# - Rationale text"
        p = doc.add_paragraph()
        q_prefix = p.add_run(f"Q{question_number} - ")
        q_prefix.bold = True
        q_prefix.font.name = DOCX_FONT_FAMILY
        q_prefix.font.size = Pt(DOCX_BODY_SIZE)
        
        rationale_run = p.add_run(rationale)
        rationale_run.font.name = DOCX_FONT_FAMILY
        rationale_run.font.size = Pt(DOCX_BODY_SIZE)
        
        # No blank lines needed between rationales
        
        question_number += 1
    

    # Footer removed as per updated requirements
    
    # Save document
    output_path = Path(output_folder) / f"{quiz.title.replace(' ', '_')}_RATIONALE.docx"
    doc.save(str(output_path))
    return str(output_path)


def _log_validation_stats(quiz: Quiz, log_path: str) -> None:
    """Write validation statistics to log file."""
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write("\n" + "="*60 + "\n")
        log.write("PHYSICAL QUIZ VALIDATION STATISTICS\n")
        log.write("="*60 + "\n\n")
        
        if LOG_ANSWER_CHOICE_STATS:
            _log_answer_choice_analysis(quiz, log)
        
        if LOG_QUESTION_LENGTH_STATS:
            _log_question_length_analysis(quiz, log)
        
        if LOG_POINT_VALUE_DISTRIBUTION:
            _log_point_distribution(quiz, log)
        
        if LOG_STIMULUS_USAGE:
            _log_stimulus_analysis(quiz, log)


def _log_answer_choice_analysis(quiz: Quiz, log):
    """Log MC answer choice statistics."""
    log.write("ANSWER CHOICE STATISTICS\n")
    log.write("-" * 40 + "\n")
    
    from engine.core.questions import MCQuestion
    mc_questions = [q for q in quiz.questions if isinstance(q, MCQuestion)]
    
    if not mc_questions:
        log.write("No multiple choice questions found.\n\n")
        return
    
    # Choice length stats
    all_choice_lengths = []
    for q in mc_questions:
        for choice in q.choices:
            all_choice_lengths.append(len(choice.text))
    
    log.write(f"Total MC questions: {len(mc_questions)}\n")
    log.write(f"Average choice length: {sum(all_choice_lengths)/len(all_choice_lengths):.1f} chars\n")
    log.write(f"Min choice length: {min(all_choice_lengths)} chars\n")
    log.write(f"Max choice length: {max(all_choice_lengths)} chars\n")
    
    # Correct answer distribution
    correct_positions = []
    for q in mc_questions:
        for idx, choice in enumerate(q.choices):
            if choice.correct:
                correct_positions.append(idx)
                break
    
    log.write(f"\nCorrect answer distribution:\n")
    for pos in range(max(correct_positions) + 1):
        count = correct_positions.count(pos)
        letter = chr(65 + pos)
        log.write(f"  {letter}: {count} ({count/len(mc_questions)*100:.1f}%)\n")
    
    # Two-column layout eligibility
    two_col_eligible = 0
    for q in mc_questions:
        choice_lengths = [len(choice.text) for choice in q.choices]
        if all(length < MC_TWO_COLUMN_THRESHOLD for length in choice_lengths):
            two_col_eligible += 1
    log.write(f"\nQuestions eligible for 2-column layout: {two_col_eligible}/{len(mc_questions)}\n")
    log.write("\n")


def _log_question_length_analysis(quiz: Quiz, log):
    """Log question text length statistics."""
    log.write("QUESTION LENGTH STATISTICS\n")
    log.write("-" * 40 + "\n")
    
    question_lengths = [len(q.prompt) for q in quiz.questions]
    
    log.write(f"Total questions: {len(quiz.questions)}\n")
    log.write(f"Average question length: {sum(question_lengths)/len(question_lengths):.1f} chars\n")
    log.write(f"Min question length: {min(question_lengths)} chars\n")
    log.write(f"Max question length: {max(question_lengths)} chars\n")
    
    # Identify very long questions
    long_threshold = 200
    long_questions = [(i+1, q) for i, q in enumerate(quiz.questions) if len(q.prompt) > long_threshold]
    
    if long_questions:
        log.write(f"\nQuestions over {long_threshold} chars (may need formatting review):\n")
        for q_num, q in long_questions:
            log.write(f"  Q{q_num}: {len(q.prompt)} chars\n")
    
    log.write("\n")


def _log_point_distribution(quiz: Quiz, log):
    """Log point value distribution."""
    log.write("POINT VALUE DISTRIBUTION\n")
    log.write("-" * 40 + "\n")
    
    from engine.core.questions import StimulusItem, StimulusEnd
    scorable_questions = [q for q in quiz.questions if not isinstance(q, (StimulusItem, StimulusEnd))]
    point_values = [q.points for q in scorable_questions]
    total_points = sum(point_values)
    
    log.write(f"Total points: {total_points}\n")
    log.write(f"Average points per question: {total_points/len(scorable_questions):.2f}\n")
    
    # Point value breakdown
    unique_values = sorted(set(point_values))
    log.write(f"\nPoint value breakdown:\n")
    for val in unique_values:
        count = point_values.count(val)
        log.write(f"  {val} pt: {count} questions ({count/len(scorable_questions)*100:.1f}%)\n")
    
    log.write("\n")


def _log_stimulus_analysis(quiz: Quiz, log):
    """Log stimulus passage usage statistics."""
    log.write("STIMULUS USAGE STATISTICS\n")
    log.write("-" * 40 + "\n")
    
    from engine.core.questions import StimulusItem, StimulusEnd
    questions_with_stimuli = []
    stimulus_groups = {}
    
    for i, q in enumerate(quiz.questions):
        if isinstance(q, StimulusItem):
            # Start of stimulus group
            current_stimulus = q.prompt
            if current_stimulus not in stimulus_groups:
                stimulus_groups[current_stimulus] = []
        elif isinstance(q, StimulusEnd):
            # End of stimulus group
            current_stimulus = None
        elif current_stimulus:
            # Question belongs to current stimulus
            questions_with_stimuli.append(q)
            stimulus_groups[current_stimulus].append(i + 1)  # 1-indexed
    
    log.write(f"Questions with stimuli: {len(questions_with_stimuli)}/{len(quiz.scorable_questions())}\n")
    
    if questions_with_stimuli:
        stimulus_lengths = [len(stimulus) for stimulus in stimulus_groups.keys()]
        log.write(f"Average stimulus length: {sum(stimulus_lengths)/len(stimulus_lengths):.1f} chars\n")
        log.write(f"Unique stimuli: {len(stimulus_groups)}\n")
        log.write(f"Questions per stimulus (avg): {len(questions_with_stimuli)/len(stimulus_groups):.1f}\n")
    
    log.write("\n")


def _group_questions_by_stimulus(questions):
    """Group questions by their stimulus associations."""
    from engine.core.questions import StimulusItem, StimulusEnd
    
    groups = []
    current_stimulus = None
    current_questions = []
    
    for q in questions:
        if isinstance(q, StimulusItem):
            # Save previous group if exists
            if current_questions:
                groups.append({'stimulus': current_stimulus, 'questions': current_questions})
            
            # Start new stimulus group
            current_stimulus = q.prompt
            current_questions = []
        elif isinstance(q, StimulusEnd):
            # End current stimulus group
            if current_questions:
                groups.append({'stimulus': current_stimulus, 'questions': current_questions})
            current_stimulus = None
            current_questions = []
        else:
            # Regular question
            current_questions.append(q)
    
    # Add final group
    if current_questions:
        groups.append({'stimulus': current_stimulus, 'questions': current_questions})
    
    return groups


def _add_question_to_doc(doc, question, question_number):
    """Add single question with smart formatting."""
    from docx.shared import Pt, Inches
    from engine.core.questions import (
        MCQuestion,
        TFQuestion,
        NumericalQuestion,
        MAQuestion,
        MatchingQuestion,
        FITBQuestion,
        OrderingQuestion,
        CategorizationQuestion,
        EssayQuestion,
        FileUploadQuestion,
    )
    
    # Add question text
    q_text = _clean_prompt_text(question.prompt)
    if isinstance(question, FITBQuestion):
        token = getattr(question, "blank_token", "")
        if token and f"[{token}]" in q_text:
            q_text = q_text.replace(f"[{token}]", "__________________")
    p = doc.add_paragraph(f"{question_number}. {q_text}")
    p.paragraph_format.space_before = Pt(DOCX_PARA_SPACING_BEFORE)
    p.paragraph_format.space_after = Pt(DOCX_PARA_SPACING_AFTER)
    p.paragraph_format.line_spacing = DOCX_LINE_SPACING
    
    # Style the question text
    for run in p.runs:
        run.font.name = DOCX_FONT_FAMILY
        run.font.size = Pt(DOCX_BODY_SIZE)
    
    if isinstance(question, (MCQuestion, MAQuestion)):
        choices = [choice.text for choice in question.choices]
        _add_mc_single_column(doc, choices)
    
    elif isinstance(question, TFQuestion):
        # Options already in prompt; nothing extra needed
        pass
    
    elif isinstance(question, MatchingQuestion):
        _add_matching_block(doc, question.pairs)
    
    elif isinstance(question, FITBQuestion):
        # Inline blank already in prompt; no extra line
        pass
    
    elif isinstance(question, OrderingQuestion):
        _add_ordering_block(doc, question.items)
    
    elif isinstance(question, CategorizationQuestion):
        _add_categorization_block(doc, question)
    
    elif isinstance(question, NumericalQuestion):
        doc.add_paragraph('Answer: _____________')
    
    elif isinstance(question, EssayQuestion):
        doc.add_paragraph('Answer: _____________')
    
    elif isinstance(question, FileUploadQuestion):
        # Instructions only; no answer line
        pass
    
    else:
        doc.add_paragraph('Answer: _____________')
    
    # Add spacing after question
    doc.add_paragraph()


def _add_mc_two_column(doc, choices):
    """Add MC choices in 2-column table format."""
    from docx.shared import Pt
    
    table = doc.add_table(rows=(len(choices) + 1) // 2, cols=2)
    table.style = 'Table Grid'
    
    for idx, choice in enumerate(choices):
        row = idx // 2
        col = idx % 2
        cell = table.rows[row].cells[col]
        cell.text = f"{chr(65+idx)}. {choice}"
        
        # Style the cell text
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.name = DOCX_FONT_FAMILY
                run.font.size = Pt(DOCX_BODY_SIZE)


def _add_mc_single_column(doc, choices):
    """Add MC choices in single column."""
    from docx.shared import Pt, Inches
    
    for idx, choice in enumerate(choices):
        p = doc.add_paragraph(f"{chr(65+idx)}. {choice}")
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.space_before = Pt(DOCX_PARA_SPACING_BEFORE)
        p.paragraph_format.space_after = Pt(DOCX_PARA_SPACING_AFTER)
        p.paragraph_format.line_spacing = DOCX_LINE_SPACING
        
        # Style the text
        for run in p.runs:
            run.font.name = DOCX_FONT_FAMILY
        run.font.size = Pt(DOCX_BODY_SIZE)


def _add_matching_block(doc, pairs: List):
    """Render matching as blanks plus legend letters."""
    from docx.shared import Pt, Inches
    letters = [chr(65 + idx) for idx in range(len(pairs))]

    # Definitions with blanks
    for pair in pairs:
        p = doc.add_paragraph(f"_____: {pair.answer}")
        p.paragraph_format.space_before = Pt(DOCX_PARA_SPACING_BEFORE)
        p.paragraph_format.space_after = Pt(DOCX_PARA_SPACING_AFTER)
        for run in p.runs:
            run.font.name = DOCX_FONT_FAMILY
            run.font.size = Pt(DOCX_BODY_SIZE)

    # Legend for terms
    for letter, pair in zip(letters, pairs):
        p = doc.add_paragraph(f"{letter} – {pair.prompt}")
        p.paragraph_format.left_indent = Inches(0.15)
        for run in p.runs:
            run.font.name = DOCX_FONT_FAMILY
            run.font.size = Pt(DOCX_BODY_SIZE)


def _add_ordering_block(doc, items):
    """Render ordering items with blanks for numbering."""
    from docx.shared import Pt, Inches
    for text in items:
        p = doc.add_paragraph(f"_____: {text.text if hasattr(text, 'text') else text}")
        p.paragraph_format.left_indent = Inches(0.15)
        p.paragraph_format.space_before = Pt(DOCX_PARA_SPACING_BEFORE)
        p.paragraph_format.space_after = Pt(DOCX_PARA_SPACING_AFTER)
        for run in p.runs:
            run.font.name = DOCX_FONT_FAMILY
            run.font.size = Pt(DOCX_BODY_SIZE)


def _add_categorization_block(doc, question):
    """Render categorization with category hints and blanks."""
    from docx.shared import Pt, Inches
    categories = question.categories if hasattr(question, "categories") else []
    if categories:
        cat_line = "Categories: " + ", ".join(categories)
        p = doc.add_paragraph(cat_line)
        for run in p.runs:
            run.font.name = DOCX_FONT_FAMILY
            run.font.size = Pt(DOCX_BODY_SIZE)

    # Combine items and distractors in display order
    items = getattr(question, "items", [])
    distractors = getattr(question, "distractors", []) or []

    for entry in items:
        label = entry.item_text if hasattr(entry, "item_text") else entry.get("label", "")
        p = doc.add_paragraph(f"_____: {label}")
        p.paragraph_format.left_indent = Inches(0.15)
        p.paragraph_format.space_before = Pt(DOCX_PARA_SPACING_BEFORE)
        p.paragraph_format.space_after = Pt(DOCX_PARA_SPACING_AFTER)
        for run in p.runs:
            run.font.name = DOCX_FONT_FAMILY
            run.font.size = Pt(DOCX_BODY_SIZE)

    for label in distractors:
        p = doc.add_paragraph(f"_____: {label}")
        p.paragraph_format.left_indent = Inches(0.15)
        p.paragraph_format.space_before = Pt(DOCX_PARA_SPACING_BEFORE)
        p.paragraph_format.space_after = Pt(DOCX_PARA_SPACING_AFTER)
        for run in p.runs:
            run.font.name = DOCX_FONT_FAMILY
            run.font.size = Pt(DOCX_BODY_SIZE)


def _add_tf_options(doc):
    """Add True/False options."""
    from docx.shared import Pt, Inches
    
    # Add options in a simple format
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.space_before = Pt(DOCX_PARA_SPACING_BEFORE)
    p.paragraph_format.space_after = Pt(DOCX_PARA_SPACING_AFTER)
    p.paragraph_format.line_spacing = DOCX_LINE_SPACING
    
    run = p.add_run("A. True    B. False")
    run.font.name = DOCX_FONT_FAMILY
    run.font.size = Pt(DOCX_BODY_SIZE)


def _get_correct_answer_text(question):
    """Get the correct answer text for a question."""
    from engine.core.questions import (
        MCQuestion, 
        TFQuestion, 
        NumericalQuestion,
        MAQuestion,
        MatchingQuestion,
        FITBQuestion,
        EssayQuestion,
        FileUploadQuestion
    )
    
    if isinstance(question, MCQuestion):
        # Find correct choice letter
        for idx, choice in enumerate(question.choices):
            if choice.correct:
                return chr(65 + idx)  # A, B, C, D...
        return "?"
    
    elif isinstance(question, TFQuestion):
        return "True" if question.answer_true else "False"
    
    elif isinstance(question, NumericalQuestion):
        return str(question.answer.answer)
    
    elif isinstance(question, MAQuestion):
        # List all correct choices
        correct_letters = []
        for idx, choice in enumerate(question.choices):
            if choice.correct:
                correct_letters.append(chr(65 + idx))
        return ", ".join(correct_letters) if correct_letters else "?"
    
    elif isinstance(question, MatchingQuestion):
        # List pairs as "left→right" format
        pairs = []
        for pair in question.pairs:
            # Format: "term → match"
            pairs.append(f"{pair.prompt} → {pair.answer}")
        return "; ".join(pairs) if pairs else "?"
    
    elif isinstance(question, FITBQuestion):
        # List all accepted answers
        if hasattr(question, 'accepted_answers') and question.accepted_answers:
            return ", ".join(question.accepted_answers)
        return "?"
    
    elif isinstance(question, (EssayQuestion, FileUploadQuestion)):
        # These are subjectively graded
        return "See rubric"
    
    else:
        # Catch-all for unknown types
        return "See rubric"


def _format_rationale_with_answer(question):
    """
    Ensure rationale has answer embedded properly.
    
    Good: "Sarah is the antagonist because she opposes the protagonist."
    Bad: "The antagonist is Sarah." (answer not embedded in explanation)
    """
    # For now, since quiz data doesn't have rationales, generate basic ones
    return _generate_basic_rationale(question)


def _generate_basic_rationale(question):
    """Generate simple rationale with answer embedded."""
    from engine.core.questions import MCQuestion, TFQuestion, NumericalQuestion
    
    if isinstance(question, MCQuestion):
        # Find correct choice
        for idx, choice in enumerate(question.choices):
            if choice.correct:
                correct_letter = chr(65 + idx)
                correct_text = choice.text
                return f"The correct answer is {correct_letter}: {correct_text}."
    
    elif isinstance(question, TFQuestion):
        answer = "True" if question.answer_true else "False"
        return f"The correct answer is {answer}."
    
    elif isinstance(question, NumericalQuestion):
        correct_value = str(question.answer.answer)
        return f"The correct answer is {correct_value}."
    
    else:
        return "See teacher for explanation."


def _clean_prompt_text(prompt: str) -> str:
    """Strip markdown code fences and trim whitespace for DOCX display."""
    # Remove simple ``` fences
    cleaned = re.sub(r"```[a-zA-Z]*", "", prompt)
    cleaned = cleaned.replace("```", "")
    return cleaned.strip()


def _log_validation_stats(quiz: Quiz, log_path: str) -> None:
    """Write validation statistics to log file."""
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write("\n" + "="*60 + "\n")
        log.write("PHYSICAL QUIZ VALIDATION STATISTICS\n")
        log.write("="*60 + "\n\n")
        
        if LOG_ANSWER_CHOICE_STATS:
            _log_answer_choice_analysis(quiz, log)
        
        if LOG_QUESTION_LENGTH_STATS:
            _log_question_length_analysis(quiz, log)
        
        if LOG_POINT_VALUE_DISTRIBUTION:
            _log_point_distribution(quiz, log)
        
        if LOG_STIMULUS_USAGE:
            _log_stimulus_analysis(quiz, log)


def _log_answer_choice_analysis(quiz: Quiz, log):
    """Log MC answer choice statistics."""
    log.write("ANSWER CHOICE STATISTICS\n")
    log.write("-" * 40 + "\n")
    
    from engine.core.questions import MCQuestion
    mc_questions = [q for q in quiz.questions if isinstance(q, MCQuestion)]
    
    if not mc_questions:
        log.write("No multiple choice questions found.\n\n")
        return
    
    # Choice length stats
    all_choice_lengths = []
    for q in mc_questions:
        for choice in q.choices:
            all_choice_lengths.append(len(choice.text))
    
    log.write(f"Total MC questions: {len(mc_questions)}\n")
    log.write(f"Average choice length: {sum(all_choice_lengths)/len(all_choice_lengths):.1f} chars\n")
    log.write(f"Min choice length: {min(all_choice_lengths)} chars\n")
    log.write(f"Max choice length: {max(all_choice_lengths)} chars\n")
    
    # Correct answer distribution
    correct_positions = []
    for q in mc_questions:
        for idx, choice in enumerate(q.choices):
            if choice.correct:
                correct_positions.append(idx)
                break
    
    log.write(f"\nCorrect answer distribution:\n")
    for pos in range(max(correct_positions) + 1):
        count = correct_positions.count(pos)
        letter = chr(65 + pos)
        log.write(f"  {letter}: {count} ({count/len(mc_questions)*100:.1f}%)\n")
    
    # Two-column layout eligibility
    two_col_eligible = 0
    for q in mc_questions:
        choice_lengths = [len(choice.text) for choice in q.choices]
        if all(length < MC_TWO_COLUMN_THRESHOLD for length in choice_lengths):
            two_col_eligible += 1
    log.write(f"\nQuestions eligible for 2-column layout: {two_col_eligible}/{len(mc_questions)}\n")
    log.write("\n")


def _log_question_length_analysis(quiz: Quiz, log):
    """Log question text length statistics."""
    log.write("QUESTION LENGTH STATISTICS\n")
    log.write("-" * 40 + "\n")
    
    question_lengths = [len(q.prompt) for q in quiz.questions]
    
    log.write(f"Total questions: {len(quiz.questions)}\n")
    log.write(f"Average question length: {sum(question_lengths)/len(question_lengths):.1f} chars\n")
    log.write(f"Min question length: {min(question_lengths)} chars\n")
    log.write(f"Max question length: {max(question_lengths)} chars\n")
    
    # Identify very long questions
    long_threshold = 200
    long_questions = [(i+1, q) for i, q in enumerate(quiz.questions) if len(q.prompt) > long_threshold]
    
    if long_questions:
        log.write(f"\nQuestions over {long_threshold} chars (may need formatting review):\n")
        for q_num, q in long_questions:
            log.write(f"  Q{q_num}: {len(q.prompt)} chars\n")
    
    log.write("\n")


def _log_point_distribution(quiz: Quiz, log):
    """Log point value distribution."""
    log.write("POINT VALUE DISTRIBUTION\n")
    log.write("-" * 40 + "\n")
    
    from engine.core.questions import StimulusItem, StimulusEnd
    scorable_questions = [q for q in quiz.questions if not isinstance(q, (StimulusItem, StimulusEnd))]
    point_values = [q.points for q in scorable_questions]
    total_points = sum(point_values)
    
    log.write(f"Total points: {total_points}\n")
    log.write(f"Average points per question: {total_points/len(scorable_questions):.2f}\n")
    
    # Point value breakdown
    unique_values = sorted(set(point_values))
    log.write(f"\nPoint value breakdown:\n")
    for val in unique_values:
        count = point_values.count(val)
        log.write(f"  {val} pt: {count} questions ({count/len(scorable_questions)*100:.1f}%)\n")
    
    log.write("\n")


def _log_stimulus_analysis(quiz: Quiz, log):
    """Log stimulus passage usage statistics."""
    log.write("STIMULUS USAGE STATISTICS\n")
    log.write("-" * 40 + "\n")
    
    from engine.core.questions import StimulusItem, StimulusEnd
    questions_with_stimuli = []
    stimulus_groups = {}
    current_stimulus = None
    
    for i, q in enumerate(quiz.questions):
        if isinstance(q, StimulusItem):
            # Start of stimulus group
            current_stimulus = q.prompt
            if current_stimulus not in stimulus_groups:
                stimulus_groups[current_stimulus] = []
        elif isinstance(q, StimulusEnd):
            # End of stimulus group
            current_stimulus = None
        elif current_stimulus:
            # Question belongs to current stimulus
            questions_with_stimuli.append(q)
            stimulus_groups[current_stimulus].append(i + 1)  # 1-indexed
    
    log.write(f"Questions with stimuli: {len(questions_with_stimuli)}/{len(quiz.scorable_questions())}\n")
    
    if questions_with_stimuli:
        stimulus_lengths = [len(stimulus) for stimulus in stimulus_groups.keys()]
        log.write(f"Average stimulus length: {sum(stimulus_lengths)/len(stimulus_lengths):.1f} chars\n")
        log.write(f"Unique stimuli: {len(stimulus_groups)}\n")
        log.write(f"Questions per stimulus (avg): {len(questions_with_stimuli)/len(stimulus_groups):.1f}\n")
    
    log.write("\n")
