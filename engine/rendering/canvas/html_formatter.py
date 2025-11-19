"""HTML helpers used by the QTI renderer."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape


def html_mattext(text: str) -> ET.Element:
    element = ET.Element("mattext", {"texttype": "text/html"})
    element.text = text
    return element


def serialize_element(element: ET.Element) -> str:
    return ET.tostring(element, encoding="utf-8").decode("utf-8")


def add_passage_numbering(text: str, passage_type: str = "auto") -> Tuple[str, str]:
    if passage_type == "none":
        return text, "none"

    lines = text.split("\n")

    if passage_type == "auto":
        detected_type, confidence = _analyze_passage_content(text, lines)
        passage_type = detected_type if round(confidence, 2) > 0.6 else "prose"  # Conservative fallback

    if passage_type == "poetry":
        numbered: list[str] = []
        non_empty_index = 0
        for line in lines:
            if line.strip():
                non_empty_index += 1
                if non_empty_index == 1 or non_empty_index % 5 == 0:
                    numbered.append(f"{{LINENUM:{non_empty_index:2}}}     {line}")
                else:
                    numbered.append("               " + line)
            else:
                numbered.append("")
        return "\n".join(numbered), "poetry"

    if passage_type in ("prose_short", "prose_long", "prose"):
        # For prose, always number paragraphs regardless of length
        paragraphs = text.split("\n\n")
        numbered = []
        for index, paragraph in enumerate(paragraphs, 1):
            if paragraph.strip():
                numbered.append(f"{{PARANUM:{index}}}     {paragraph}")
            else:
                numbered.append("")
        return "\n\n".join(numbered), "prose"

    return text, "unknown"


def _analyze_passage_content(text: str, lines: List[str]) -> Tuple[str, float]:
    """Analyze passage content to determine type with confidence score.

    Returns:
        Tuple of (passage_type, confidence_score)
        confidence_score ranges from 0.0 to 1.0
    """
    non_empty_lines = [line for line in lines if line.strip()]
    if not non_empty_lines:
        return "unknown", 0.0

    # Basic metrics
    total_lines = len(non_empty_lines)
    avg_line_len = sum(len(line) for line in non_empty_lines) / total_lines
    paragraph_breaks = text.count("\n\n")

    # Initialize scores
    poetry_score = 0.0
    prose_score = 0.0

    # Length-based heuristics
    if avg_line_len < 60:
        poetry_score += 0.3
    else:
        prose_score += 0.2

    # Line count heuristics
    if total_lines < 3:
        return "prose_short", 0.8  # Too short for reliable analysis
    elif total_lines > 10:
        prose_score += 0.2

    # Paragraph structure
    if paragraph_breaks >= 3:
        prose_score += 0.4
    elif paragraph_breaks == 0:
        poetry_score += 0.2

    # Sentence structure analysis
    sentence_endings = text.count('.') + text.count('!') + text.count('?')
    sentences_per_line = sentence_endings / max(total_lines, 1)

    if sentences_per_line < 0.5:  # Fewer than 0.5 sentences per line
        poetry_score += 0.3  # Suggests poetry (multiple lines per sentence)
    else:
        prose_score += 0.2   # Suggests prose (one sentence per line)

    # Line length consistency (poetry often has rhythmic structure)
    if total_lines >= 3:
        line_lengths = [len(line) for line in non_empty_lines]
        avg_len = sum(line_lengths) / len(line_lengths)
        variance = sum((length - avg_len) ** 2 for length in line_lengths) / len(line_lengths)
        std_dev = variance ** 0.5
        consistency_ratio = std_dev / max(avg_len, 1)

        if consistency_ratio < 0.3:  # Very consistent line lengths
            poetry_score += 0.4
        elif consistency_ratio > 0.7:  # Very inconsistent
            prose_score += 0.2

    # Stanza detection (multiple consecutive breaks suggest poetry)
    double_breaks = 0
    for i in range(len(lines) - 1):
        if lines[i].strip() == "" and lines[i + 1].strip() == "":
            double_breaks += 1

    if double_breaks > 0:
        poetry_score += min(double_breaks * 0.2, 0.4)

    # Capitalization patterns (poetry often starts lines with capitals)
    capitalized_starts = sum(1 for line in non_empty_lines if line.strip() and line.strip()[0].isupper())
    cap_ratio = capitalized_starts / total_lines

    if cap_ratio > 0.8:  # Most lines start with capital
        poetry_score += 0.2
    elif cap_ratio < 0.3:  # Few lines start with capital
        prose_score += 0.1

    # Normalize scores
    total_score = poetry_score + prose_score
    if total_score == 0:
        return "prose_short", 0.5

    poetry_confidence = poetry_score / total_score
    prose_confidence = prose_score / total_score

    # Determine winner with confidence
    if poetry_confidence > prose_confidence:
        final_type = "poetry"
        confidence = poetry_confidence
    else:
        final_type = "prose"
        confidence = prose_confidence

    return final_type, min(confidence, 0.95)  # Cap at 95% to allow for edge cases


def syntax_highlight_python(code: str) -> str:
    import re as _re

    keyword_color = "#F92672"
    function_color = "#A6E22E"
    string_color = "#E6DB74"
    comment_color = "#75715E"
    number_color = "#AE81FF"
    builtin_color = "#66D9EF"

    keywords = r"\b(def|class|if|elif|else|for|while|return|import|from|as|try|except|finally|with|lambda|yield|pass|break|continue|raise|assert|del|global|nonlocal|in|is|not|and|or|True|False|None)\b"

    result = xml_escape(code)
    result = _re.sub(r"(#[^\n]*)", f'<span style="color: {comment_color};">\\1</span>', result)
    result = _re.sub(
        r'(?<!span style="color: ' + comment_color + r';">)(["\'])(?:(?=(\\?))\2.)*?\1',
        lambda match: f'<span style="color: {string_color};">{match.group(0)}</span>',
        result,
    )
    result = _re.sub(r'(?<!span>)("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', f'<span style="color: {string_color};">\\1</span>', result)
    result = _re.sub(r"\b(\d+\.?\d*)\b", f'<span style="color: {number_color};">\\1</span>', result)
    result = _re.sub(
        r"\b(def)\s+(\w+)",
        f'<span style="color: {keyword_color};">\\1</span> <span style="color: {function_color};">\\2</span>',
        result,
    )
    result = _re.sub(r"\b(\w+)(?=\s*\()", f'<span style="color: {function_color};">\\1</span>', result)
    result = _re.sub(keywords, f'<span style="color: {keyword_color};">\\1</span>', result)
    builtins = r"\b(print|len|range|str|int|float|list|dict|set|tuple|input|open|enumerate|zip|map|filter|sorted|sum|min|max|abs|all|any|isinstance|type)\b"
    result = _re.sub(builtins, f'<span style="color: {builtin_color};">\\1</span>', result)

    return result


def htmlize_prompt(text: str, *, excerpt_numbering: bool = True) -> str:
    if re.search(r"<\w+[^>]*>", text):
        return text

    monokai_style = (
        "background-color: #272822; "
        "color: #F8F8F2; "
        "padding: 10px; "
        "border-radius: 4px; "
        "font-family: 'Courier New', Consolas, monospace; "
        "overflow-x: auto; "
        "line-height: 1.5;"
    )

    lines = text.split("\n")
    html_parts: list[str] = []
    index = 0

    def esc(value: str) -> str:
        return xml_escape(value)

    def render_excerpt_block(content: str, forced_type: Optional[str] = None) -> str:
        if not excerpt_numbering:
            forced_type = "none"
        numbered_content, passage_type = add_passage_numbering(content, forced_type or "auto")

        import re as _re

        def style_numbers(value: str) -> str:
            num_style = "font-size: 0.85em; font-style: italic; color: #999; font-weight: normal;"
            value = _re.sub(r"\{LINENUM:(\s*\d+)\}", lambda m: f'<span style="{num_style}">{m.group(1)}</span>', value)
            value = _re.sub(r"\{PARANUM:(\d+)\}", lambda m: f'<span style="{num_style}">[{m.group(1)}]</span>', value)
            return value

        styled = style_numbers(numbered_content)

        if passage_type == "poetry":
            lines_html = styled.split("\n")
            line_html = []
            for line in lines_html:
                if line.strip():
                    escaped = esc(line)
                    escaped = re.sub(r'&lt;span style=\"([^\"]*)\"&gt;', r'<span style="\1">', escaped)
                    escaped = escaped.replace("&lt;/span&gt;", "</span>")
                    line_html.append(f'<div style="margin: 0; padding: 0; line-height: 1.6;">{escaped}</div>')
                else:
                    line_html.append('<div style="margin: 0; padding: 0; line-height: 1.6;">&nbsp;</div>')
            return (
                '<div style="margin:10px 0;">'
                '<div style="font-family: inherit; font-size:0.95em; padding:14px 18px; background:#fff; border:1px solid #d9d9d9; border-left:5px solid #4b79ff; '
                'line-height:1.6;">'
                + "".join(line_html)
                + "</div></div>"
            )
        if passage_type in {"prose_short", "prose_long", "prose"}:
            paragraphs = styled.split("\n\n")
            para_html = []
            for paragraph in paragraphs:
                if paragraph.strip():
                    escaped = esc(paragraph)
                    escaped = re.sub(r'&lt;span style=\"([^\"]*)\"&gt;', r'<span style="\1">', escaped)
                    escaped = escaped.replace("&lt;/span&gt;", "</span>")
                    para_html.append(f'<p style="margin: 0 0 0.9em 0; line-height: 1.6;">{escaped}</p>')
            return (
                '<div style="margin:10px 0;">'
                '<div style="font-family: inherit; font-size:0.95em; padding:14px 18px; background:#fff; border:1px solid #d9d9d9; border-left:5px solid #4b79ff; '
                'line-height:1.6;">'
                + "".join(para_html)
                + "</div></div>"
            )
        return (
            '<div style="margin:10px 0;">'
            '<div style="font-family: inherit; font-size:0.95em; padding:14px 18px; background:#fff; border:1px solid #d9d9d9; border-left:5px solid #4b79ff; '
            'line-height:1.6; white-space:pre-wrap;">' + esc(numbered_content) + '</div></div>'
        )

    # If excerpt_numbering is enabled and no special blocks detected, treat as excerpt block
    has_code_fences = "```" in text
    has_excerpt_blocks = ">>>" in text
    has_headings = re.search(r"^#{1,6}\s+", text, re.MULTILINE)
    
    if excerpt_numbering and not (has_code_fences or has_excerpt_blocks or has_headings):
        # Treat entire text as excerpt block
        return render_excerpt_block(text)
        if not excerpt_numbering:
            forced_type = "none"
        numbered_content, passage_type = add_passage_numbering(content, forced_type or "auto")

        import re as _re

        def style_numbers(value: str) -> str:
            num_style = "font-size: 0.85em; font-style: italic; color: #999; font-weight: normal;"
            value = _re.sub(r"\{LINENUM:(\s*\d+)\}", lambda m: f'<span style="{num_style}">{m.group(1)}</span>', value)
            value = _re.sub(r"\{PARANUM:(\d+)\}", lambda m: f'<span style="{num_style}">[{m.group(1)}]</span>', value)
            return value

        styled = style_numbers(numbered_content)

        if passage_type == "poetry":
            lines = styled.split("\n")
            line_html = []
            for line in lines:
                if line.strip():
                    escaped = esc(line)
                    escaped = re.sub(r'&lt;span style=\"([^\"]*)\"&gt;', r'<span style="\1">', escaped)
                    escaped = escaped.replace("&lt;/span&gt;", "</span>")
                    line_html.append(f'<div style="margin: 0; padding: 0; line-height: 1.6;">{escaped}</div>')
                else:
                    line_html.append('<div style="margin: 0; padding: 0; line-height: 1.6;">&nbsp;</div>')
            return (
                '<div style="margin:10px 0;">'
                '<div style="font-family: inherit; font-size:0.95em; padding:14px 18px; background:#fff; border:1px solid #d9d9d9; border-left:5px solid #4b79ff; '
                'line-height:1.6;">'
                + "".join(line_html)
                + "</div></div>"
            )
        if passage_type in {"prose_short", "prose_long", "prose"}:
            paragraphs = styled.split("\n\n")
            para_html = []
            for paragraph in paragraphs:
                if paragraph.strip():
                    escaped = esc(paragraph)
                    escaped = re.sub(r'&lt;span style=\"([^\"]*)\"&gt;', r'<span style="\1">', escaped)
                    escaped.replace("&lt;/span&gt;", "</span>")
                    para_html.append(f'<p style="margin: 0 0 0.9em 0; line-height: 1.6;">{escaped}</p>')
            return (
                '<div style="margin:10px 0;">'
                '<div style="font-family: inherit; font-size:0.95em; padding:14px 18px; background:#fff; border:1px solid #d9d9d9; border-left:5px solid #4b79ff; '
                'line-height:1.6;">'
                + "".join(para_html)
                + "</div></div>"
            )
        return (
            '<div style="margin:10px 0;">'
            '<div style="font-family: inherit; font-size:0.95em; padding:14px 18px; background:#fff; border:1px solid #d9d9d9; border-left:5px solid #4b79ff; '
            'line-height:1.6; white-space:pre-wrap;">' + esc(numbered_content) + '</div></div>'
        )

    while index < len(lines):
        line = lines[index]
        heading = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if heading:
            level = min(len(heading.group(1)), 3)
            html_parts.append(f"<h{level}>{esc(heading.group(2).strip())}</h{level}>")
            index += 1
            continue

        if line.strip().startswith("```"):
            fence = line.strip()
            lang = fence[3:].strip()
            index += 1
            block: list[str] = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                block.append(lines[index])
                index += 1
            if index < len(lines) and lines[index].strip().startswith("```"):
                index += 1
            code = "\n".join(block)
            lang_lower = (lang or "").lower()
            if lang_lower in {"excerpt", "prose", "poetry"}:
                forced = "poetry" if lang_lower == "poetry" else None
                html_parts.append(render_excerpt_block(code, forced_type=forced))
            elif lang_lower == "python":
                highlighted = syntax_highlight_python(code)
                html_parts.append(f"<pre style=\"{monokai_style}\"><code class=\"language-{esc(lang)}\">{highlighted}</code></pre>")
            else:
                html_parts.append(f"<pre style=\"{monokai_style}\"><code class=\"language-{esc(lang)}\">{esc(code)}</code></pre>")
            continue

        if line.strip() == ">>>":
            index += 1
            block: list[str] = []
            while index < len(lines) and lines[index].strip() != ">>>":
                block.append(lines[index])
                index += 1
            if index < len(lines) and lines[index].strip() == ">>>":
                index += 1
            html_parts.append(render_excerpt_block("\n".join(block)))
            continue

        if line.startswith("> "):
            block = [line[2:]]
            index += 1
            while index < len(lines) and lines[index].startswith("> "):
                block.append(lines[index][2:])
                index += 1
            html_parts.append("<blockquote>" + "<br/>".join(esc(item) for item in block) + "</blockquote>")
            continue

        paragraph: list[str] = []
        while index < len(lines) and lines[index].strip() != "":
            if lines[index].strip().startswith("```") or lines[index].strip() == ">>>" or lines[index].startswith("> "):
                break
            paragraph.append(lines[index])
            index += 1
        if index < len(lines) and lines[index].strip() == "":
            while index < len(lines) and lines[index].strip() == "":
                index += 1
        if paragraph:
            joined = "\n".join(paragraph)
            if not excerpt_numbering:
                quote_match = re.search(r'"([^"\n]{40,})"|\u201c([^\u201d\n]{40,})\u201d', joined)
                if quote_match:
                    quoted = quote_match.group(1) or quote_match.group(2) or ""
                    pre = joined[: quote_match.start()].strip()
                    post = joined[quote_match.end() :].strip()
                    if pre:
                        escaped_pre = esc(pre)
                        escaped_pre = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", escaped_pre)
                        html_parts.append(f"<p>{escaped_pre}</p>")
                    html_parts.append(
                        '<div style="margin:10px 0;"><div style="font-family: inherit; font-size:0.95em; padding:14px 18px; background:#fff; border:1px solid #d9d9d9; border-left:5px solid #4b79ff; line-height:1.6;">'
                        + esc(quoted)
                        + "</div></div>"
                    )
                    if post:
                        escaped_post = esc(post)
                        escaped_post = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", escaped_post)
                        html_parts.append(f"<p>{escaped_post}</p>")
                    continue
            escaped = esc(joined)
            escaped = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", escaped)
            html_parts.append(f"<p>{escaped}</p>")
        else:
            html_parts.append("<p></p>")

    return "\n".join(part for part in html_parts if part) or "<p></p>"


def htmlize_choice(text: str) -> str:
    def esc(value: str) -> str:
        return xml_escape(value)

    def repl(match):
        return f"<code>{esc(match.group(1))}</code>"

    processed = re.sub(r"`([^`]+)`", repl, text)
    return f"<p>{esc(processed)}</p>"