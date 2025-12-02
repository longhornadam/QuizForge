"""QTI assessment XML builders."""

from __future__ import annotations

import uuid
from typing import List
import xml.etree.ElementTree as ET

from engine.core.questions import (
    CategorizationQuestion,
    EssayQuestion,
    FITBQuestion,
    FileUploadQuestion,
    MAQuestion,
    MCChoice,
    MCQuestion,
    NumericalQuestion,
    MatchingQuestion,
    OrderingQuestion,
    Question,
    StimulusItem,
    TFQuestion,
)
from engine.core.quiz import Quiz
from engine.utils.text_utils import rand8
from .html_formatter import html_mattext, htmlize_choice, htmlize_item_text, htmlize_prompt, serialize_element
from .numerical_renderer import build_numerical_item


def build_assessment_xml(quiz: Quiz) -> str:
    """Build the main QTI 1.2 assessment XML document.

    This is the core rendering function. It converts a Quiz object into a complete
    QTI assessment with all items, responses, and scoring rules.

    Input flows through:
      Quiz → _build_item() for each question → response structure → scoring rules → XML

    Args:
        quiz: Parsed Quiz object from TextOutlineParser

    Returns:
        str: QTI assessment XML as a string
    """
    root = ET.Element("questestinterop")
    assessment_ident = f"assessment_{rand8()}"
    assessment = ET.SubElement(root, "assessment", {"ident": assessment_ident, "title": quiz.title})

    metadata = ET.SubElement(assessment, "qtimetadata")
    metadata_field = ET.SubElement(metadata, "qtimetadatafield")
    ET.SubElement(metadata_field, "fieldlabel").text = "cc_maxattempts"
    ET.SubElement(metadata_field, "fieldentry").text = "1"

    section = ET.SubElement(assessment, "section", {"ident": "root_section"})

    for index, question in enumerate(quiz.questions, start=1):
        item = _build_item(question, index)
        section.append(item)

    xml_body = serialize_element(root)
    open_tag = "<questestinterop>"
    ns_tag = (
        '<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.imsglobal.org/xsd/ims_qtiasiv1p2 http://www.imsglobal.org/xsd/ims_qtiasiv1p2p1.xsd">'
    )
    xml_body = xml_body.replace(open_tag, ns_tag, 1)
    return "<?xml version=\"1.0\"?>\n" + xml_body + "\n"


def _build_item(question: Question, index: int) -> ET.Element:
    """Build a single QTI <item> element from a Question.

    This function orchestrates item building:
    1. Create <item> wrapper with ID and title
    2. Add <itemmetadata> with question type and points
    3. Add <presentation> with prompt
    4. Call _build_response() for interaction structure
    5. Call _build_scoring() for scoring logic

    Args:
        question: A Question subclass (MCQuestion, TFQuestion, NumericalQuestion, etc.)
        index: Question number (for ID generation and display)

    Returns:
        ET.Element: Complete <item> element ready to insert into QTI section

    Special cases:
    - StimulusItem: 0-point content block, no response/scoring
    - NumericalQuestion: Delegates to build_numerical_item() in numerical.py
    """
    if isinstance(question, NumericalQuestion):
        return build_numerical_item(question, index)

    item_ident = question.forced_ident or f"item_q{index:02d}_{rand8()}"
    item_title = f"Q{index:02d}"
    item = ET.Element("item", {"ident": item_ident, "title": item_title})

    itemmetadata = ET.SubElement(item, "itemmetadata")
    qtimetadata = ET.SubElement(itemmetadata, "qtimetadata")

    def meta_field(label: str, entry: str) -> None:
        field = ET.SubElement(qtimetadata, "qtimetadatafield")
        ET.SubElement(field, "fieldlabel").text = label
        ET.SubElement(field, "fieldentry").text = entry

    if isinstance(question, StimulusItem):
        meta_field("question_type", "text_only_question")
        meta_field("points_possible", "0.0")
    elif isinstance(question, MCQuestion):
        meta_field("question_type", "multiple_choice_question")
        meta_field("calculator_type", "none")
    elif isinstance(question, TFQuestion):
        meta_field("question_type", "true_false_question")
        meta_field("calculator_type", "none")
    elif isinstance(question, MAQuestion):
        meta_field("question_type", "multiple_answers_question")
        meta_field("calculator_type", "none")
    elif isinstance(question, MatchingQuestion):
        meta_field("question_type", "matching_question")
        meta_field("calculator_type", "none")
    elif isinstance(question, EssayQuestion):
        meta_field("question_type", "essay_question")
        meta_field("calculator_type", "none")
    elif isinstance(question, FileUploadQuestion):
        meta_field("question_type", "file_upload_question")
        meta_field("calculator_type", "none")
    elif isinstance(question, FITBQuestion):
        meta_field("question_type", "fill_in_multiple_blanks_question")
        meta_field("calculator_type", "none")
    elif isinstance(question, OrderingQuestion):
        meta_field("question_type", "ordering_question")
        meta_field("calculator_type", "none")
    elif isinstance(question, CategorizationQuestion):
        meta_field("question_type", "categorization_question")
        meta_field("calculator_type", "none")
    else:
        meta_field("question_type", question.qtype)

    if not isinstance(question, StimulusItem):
        meta_field("points_possible", f"{question.points:.1f}")

    if question.parent_stimulus_ident:
        meta_field("parent_stimulus_item_ident", question.parent_stimulus_ident)

    presentation = ET.SubElement(item, "presentation")
    material = ET.SubElement(presentation, "material")
    enable_excerpt_numbering = isinstance(question, StimulusItem)
    material.append(html_mattext(htmlize_prompt(question.prompt, excerpt_numbering=enable_excerpt_numbering)))

    if isinstance(question, StimulusItem):
        return item

    response_info = _build_response(question, presentation)

    if response_info is None or isinstance(question, (EssayQuestion, FileUploadQuestion)):
        return item

    _build_scoring(question, item, response_info)
    return item


def _build_response(question: Question, presentation: ET.Element):
    """Build the <response_lid> or <response_str> element for a question.

    This creates the interaction structure (choices, radio buttons, text input, etc.)
    based on question type. Returns metadata dict for _build_scoring() to use.

    Args:
        question: A Question subclass
        presentation: Parent <presentation> element to add response to

    Returns:
        dict: Metadata for scoring (varies by type). Keys include "type" and type-specific data.
            - {"type": "mc", "correct": "a"}: Multiple choice
            - {"type": "tf", "correct": "true"}: True/False
            - {"type": "ma", "correct": ["a", "b"]}: Multiple answers
            - {"type": "matching", "pairs": [...], "rlids": [...], "answers": {...}}
            - {"type": "ordering", "items": [...]} 
            - {"type": "categorization", "categories": [...], "num_categories": N}
            None: For unscored questions (Essay, FileUpload)

    Raises:
        ValueError: If question structure is invalid
    """
    if isinstance(question, MCQuestion):
        response_lid = ET.SubElement(presentation, "response_lid", {"ident": "response1", "rcardinality": "Single"})
        render_choice = ET.SubElement(response_lid, "render_choice")
        identifiers = [chr(ord("a") + i) for i in range(len(question.choices))]
        for ident, choice in zip(identifiers, question.choices):
            label = ET.SubElement(render_choice, "response_label", {"ident": ident})
            material = ET.SubElement(label, "material")
            material.append(html_mattext(htmlize_choice(choice.text)))
        correct_ident = identifiers[[index for index, choice in enumerate(question.choices) if choice.correct][0]]
        return {"type": "mc", "correct": correct_ident}

    if isinstance(question, TFQuestion):
        response_lid = ET.SubElement(presentation, "response_lid", {"ident": "response1", "rcardinality": "Single"})
        render_choice = ET.SubElement(response_lid, "render_choice")
        for ident, label_text in (("true", "True"), ("false", "False")):
            label = ET.SubElement(render_choice, "response_label", {"ident": ident})
            material = ET.SubElement(label, "material")
            material.append(html_mattext(f"<p>{label_text}</p>"))
        correct = "true" if question.answer_true else "false"
        return {"type": "tf", "correct": correct}

    if isinstance(question, MAQuestion):
        response_lid = ET.SubElement(presentation, "response_lid", {"ident": "response1", "rcardinality": "Multiple"})
        render_choice = ET.SubElement(response_lid, "render_choice")
        identifiers = [chr(ord("a") + i) for i in range(len(question.choices))]
        correct: List[str] = []
        for ident, choice in zip(identifiers, question.choices):
            label = ET.SubElement(render_choice, "response_label", {"ident": ident})
            material = ET.SubElement(label, "material")
            material.append(html_mattext(htmlize_choice(choice.text)))
            if choice.correct:
                correct.append(ident)
        return {"type": "ma", "choices": question.choices, "correct": correct}

    if isinstance(question, MatchingQuestion):
        answer_id_by_text: dict[str, str] = {}
        for pair in question.pairs:
            if pair.answer not in answer_id_by_text:
                answer_id_by_text[pair.answer] = str(uuid.uuid4())

        rlids: List[str] = []
        for pair in question.pairs:
            lid_ident = str(uuid.uuid4())
            rlids.append(lid_ident)
            response_lid = ET.SubElement(presentation, "response_lid", {"ident": lid_ident})
            matq = ET.SubElement(response_lid, "material")
            # Transform code blocks in matching prompts
            prompt_html = htmlize_item_text(pair.prompt)
            matq.append(html_mattext(f"<p>{prompt_html}</p>"))
            render_choice = ET.SubElement(response_lid, "render_choice")
            for answer_text, answer_ident in answer_id_by_text.items():
                rl = ET.SubElement(render_choice, "response_label", {"ident": answer_ident})
                mat = ET.SubElement(rl, "material")
                # Transform code blocks in matching answers
                answer_html = htmlize_item_text(answer_text)
                mat.append(html_mattext(f"<p>{answer_html}</p>"))
        return {"type": "matching", "pairs": question.pairs, "rlids": rlids, "answers": answer_id_by_text}

    if isinstance(question, FITBQuestion):
        token = question.blank_token or uuid.uuid4().hex
        response_lid = ET.SubElement(presentation, "response_lid", {"ident": f"response_{token}"})
        matq = ET.SubElement(response_lid, "material")
        ET.SubElement(matq, "mattext").text = "Question"
        render_choice = ET.SubElement(response_lid, "render_choice")
        for index, variant in enumerate(question.variants):
            resp_ident = f"{token}-{index}"
            label = ET.SubElement(render_choice, "response_label", {
                "scoring_algorithm": "TextContainsAnswer",
                "answer_type": "openEntry",
                "ident": resp_ident,
            })
            mat = ET.SubElement(label, "material")
            ET.SubElement(mat, "mattext", {"texttype": "text/plain"}).text = variant
        return {"type": "fitb", "token": token, "variants": question.variants}

    if isinstance(question, EssayQuestion):
        response_str = ET.SubElement(presentation, "response_str", {"ident": "response1", "rcardinality": "Single"})
        render_fib = ET.SubElement(response_str, "render_fib")
        ET.SubElement(render_fib, "response_label", {"ident": "answer1"})
        return None

    if isinstance(question, FileUploadQuestion):
        response_str = ET.SubElement(presentation, "response_str", {"ident": "response1", "rcardinality": "Single"})
        render_fib = ET.SubElement(response_str, "render_fib")
        ET.SubElement(render_fib, "response_label", {"ident": "answer1"})
        return None

    if isinstance(question, OrderingQuestion):
        response_lid = ET.SubElement(presentation, "response_lid", {"ident": "response1", "rcardinality": "Ordered"})
        render_extension = ET.SubElement(response_lid, "render_extension")
        # Add header if provided
        if question.header:
            mat_top = ET.SubElement(render_extension, "material", {"position": "top"})
            # Transform code blocks in header
            header_html = htmlize_item_text(question.header)
            mat_top.append(html_mattext(f"<p>{header_html}</p>"))
        # Add items
        ims_render = ET.SubElement(render_extension, "ims_render_object", {"shuffle": "No"})
        flow_label = ET.SubElement(ims_render, "flow_label")
        for item in question.items:
            response_label = ET.SubElement(flow_label, "response_label", {"ident": item.ident})
            material = ET.SubElement(response_label, "material")
            # Transform code blocks in ordering items
            item_html = htmlize_item_text(item.text)
            material.append(html_mattext(f"<p>{item_html}</p>"))
        # Add empty bottom material
        mat_bottom = ET.SubElement(render_extension, "material", {"position": "bottom"})
        ET.SubElement(mat_bottom, "mattext").text = ""
        return {"type": "ordering", "items": question.items}

    if isinstance(question, CategorizationQuestion):
        # Build response_lid for each category
        all_items = list(question.items)
        all_item_idents = {item.item_text: item.item_ident for item in all_items}
        # Also include distractors in the item pool
        for dist in question.distractors:
            all_item_idents[dist] = question.distractor_idents[dist]
        
        category_data = []
        for cat_name in question.categories:
            cat_ident = question.category_idents[cat_name]
            response_lid = ET.SubElement(presentation, "response_lid", {"ident": cat_ident, "rcardinality": "Multiple"})
            material = ET.SubElement(response_lid, "material")
            # Transform code blocks in category names
            cat_html = htmlize_item_text(cat_name)
            material.append(html_mattext(f"<p>{cat_html}</p>"))
            render_choice = ET.SubElement(response_lid, "render_choice")
            
            # Add all items (including distractors) to each category
            for item_text, item_ident in all_item_idents.items():
                response_label = ET.SubElement(render_choice, "response_label", {"ident": item_ident})
                mat = ET.SubElement(response_label, "material")
                # Transform code blocks in categorization items
                item_html = htmlize_item_text(item_text)
                mat.append(html_mattext(f"<p>{item_html}</p>"))
            
            # Store which items belong to this category
            correct_items = [item.item_ident for item in all_items if item.category_name == cat_name]
            category_data.append({
                "category_ident": cat_ident,
                "category_name": cat_name,
                "correct_items": correct_items
            })
        
        return {"type": "categorization", "categories": category_data, "num_categories": len(question.categories)}
        
        return {"type": "categorization", "categories": category_data, "num_categories": len(question.categories)}

    response_lid = ET.SubElement(presentation, "response_lid", {"ident": "response1", "rcardinality": "Single"})
    ET.SubElement(response_lid, "render_choice")
    return {"type": "generic"}


def _build_scoring(question: Question, item: ET.Element, response_info) -> None:
    """Build the <resprocessing> element with scoring rules.

    Creates Canvas-compatible scoring logic based on question type.
    Transforms correct answers into QTI condition-action pairs that set SCORE.

    Scoring strategies by type:
    - MC/TF: All-or-nothing (100 or 0)
    - MA: Partial credit per correct choice
    - Matching: Partial credit per correct pair
    - FITB: 100 for any accepted variant
    - Ordering: All-or-nothing (must match exact sequence)
    - Categorization: Partial credit per category

    Args:
        question: A Question subclass
        item: Parent <item> element to add resprocessing to
        response_info: Dict returned from _build_response() with scoring metadata

    Returns:
        None (modifies item in place)
    """
    resprocessing = ET.SubElement(item, "resprocessing")
    outcomes = ET.SubElement(resprocessing, "outcomes")
    ET.SubElement(outcomes, "decvar", {"maxvalue": "100", "minvalue": "0", "varname": "SCORE", "vartype": "Decimal"})

    if response_info["type"] in {"mc", "tf"}:
        respcondition = ET.SubElement(resprocessing, "respcondition", {"continue": "No"})
        conditionvar = ET.SubElement(respcondition, "conditionvar")
        varequal = ET.SubElement(conditionvar, "varequal", {"respident": "response1"})
        varequal.text = response_info["correct"]
        ET.SubElement(respcondition, "setvar", {"action": "Set", "varname": "SCORE"}).text = "100"
        return

    if response_info["type"] == "ma":
        choices: List[MCChoice] = response_info["choices"]
        num_correct = sum(1 for choice in choices if choice.correct)
        num_correct = num_correct or 1
        per = round(100.0 / num_correct, 2)
        running = 0.0
        correct_choices = [choice for choice in choices if choice.correct]
        for idx, choice in enumerate(correct_choices):
            add_value = per
            if idx == len(correct_choices) - 1:
                add_value = round(100.0 - running, 2)
            respcondition = ET.SubElement(resprocessing, "respcondition", {"continue": "Yes"})
            conditionvar = ET.SubElement(respcondition, "conditionvar")
            varequal = ET.SubElement(conditionvar, "varequal", {"respident": "response1"})
            varequal.text = chr(ord("a") + choices.index(choice))
            ET.SubElement(respcondition, "setvar", {"action": "Add", "varname": "SCORE"}).text = f"{add_value:.2f}"
            running += add_value
        return

    if response_info["type"] == "matching":
        pairs = response_info["pairs"]
        rlids = response_info["rlids"]
        answer_map = response_info["answers"]
        num_pairs = max(1, len(pairs))
        per = round(100.0 / num_pairs, 2)
        running = 0.0
        for idx, pair in enumerate(pairs):
            add_value = per
            if idx == len(pairs) - 1:
                add_value = round(100.0 - running, 2)
            respident = rlids[idx]
            correct_label = answer_map[pair.answer]
            respcondition = ET.SubElement(resprocessing, "respcondition")
            conditionvar = ET.SubElement(respcondition, "conditionvar")
            varequal = ET.SubElement(conditionvar, "varequal", {"respident": respident})
            varequal.text = correct_label
            ET.SubElement(respcondition, "setvar", {"action": "Add", "varname": "SCORE"}).text = f"{add_value:.2f}"
            running += add_value
        return

    if response_info["type"] == "fitb":
        token = response_info["token"]
        variants = response_info["variants"]
        for index, _ in enumerate(variants):
            respcondition = ET.SubElement(resprocessing, "respcondition")
            conditionvar = ET.SubElement(respcondition, "conditionvar")
            varequal = ET.SubElement(conditionvar, "varequal", {"respident": f"response_{token}"})
            varequal.text = f"{token}-{index}"
            ET.SubElement(respcondition, "setvar", {"action": "Add", "varname": "SCORE"}).text = "100.00"
        return

    if response_info["type"] == "ordering":
        # All-or-nothing scoring: must match exact order
        items = response_info["items"]
        respcondition = ET.SubElement(resprocessing, "respcondition", {"continue": "No"})
        conditionvar = ET.SubElement(respcondition, "conditionvar")
        # Add varequal for each item in correct order
        for item in items:
            varequal = ET.SubElement(conditionvar, "varequal", {"respident": "response1"})
            varequal.text = item.ident
        ET.SubElement(respcondition, "setvar", {"action": "Set", "varname": "SCORE"}).text = "100"
        return

    if response_info["type"] == "categorization":
        # Partial credit per category
        categories = response_info["categories"]
        num_categories = response_info["num_categories"]
        points_per_category = round(100.0 / num_categories, 2)
        running = 0.0
        
        for idx, cat_data in enumerate(categories):
            # Last category gets remaining points to ensure we hit exactly 100
            if idx == len(categories) - 1:
                add_value = round(100.0 - running, 2)
            else:
                add_value = points_per_category
            
            respcondition = ET.SubElement(resprocessing, "respcondition")
            conditionvar = ET.SubElement(respcondition, "conditionvar")
            # Add varequal for each item that should be in this category
            for item_ident in cat_data["correct_items"]:
                varequal = ET.SubElement(conditionvar, "varequal", {"respident": cat_data["category_ident"]})
                varequal.text = item_ident
            ET.SubElement(respcondition, "setvar", {"action": "Add", "varname": "SCORE"}).text = f"{add_value:.2f}"
            running += add_value
        return