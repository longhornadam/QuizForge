"""
Archived experimental implementation of the numerical question type.

This snapshot mirrors the standalone parser and renderer that lived in
`dev/numerical_experimental.py` prior to the 2025-11-08 production merge.
Refer to the Packager package for the maintained code path.
"""

import re
import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class NumericalQuestionSpec:
    """Parsed specification for a numerical question."""
    prompt: str
    points: float
    answer: Optional[Decimal] = None
    tolerance_mode: str = "exact"
    margin_value: Optional[float] = None
    range_min: Optional[Decimal] = None
    range_max: Optional[Decimal] = None
    precision_value: Optional[int] = None
    lower_bound: Optional[Decimal] = None
    upper_bound: Optional[Decimal] = None
    strict_lower: bool = False


class NumericalParser:
    """Parse NUMERICAL question blocks from plain text."""

    @staticmethod
    def parse(lines: list, points: Optional[float] = None) -> NumericalQuestionSpec:
        spec = NumericalQuestionSpec(prompt="", points=points or 1.0)
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("Prompt:"):
                spec.prompt = line[7:].strip()
                i += 1
                while i < len(lines) and not any(
                    lines[i].startswith(kw)
                    for kw in ["Answer:", "Range:", "Tolerance:", "Precision:", "Type:", "Points:"]
                ):
                    spec.prompt += "\n" + lines[i]
                    i += 1
                spec.prompt = spec.prompt.strip()
                continue
            if line.startswith("Answer:"):
                answer_str = line[7:].strip()
                spec.answer = Decimal(answer_str)
                i += 1
                continue
            if line.startswith("Range:"):
                range_str = line[6:].strip()
                match = re.match(r'([-\d.]+)\s+to\s+([-\d.]+)', range_str)
                if match:
                    spec.range_min = Decimal(match.group(1))
                    spec.range_max = Decimal(match.group(2))
                    spec.tolerance_mode = "range"
                i += 1
                continue
            if line.startswith("Tolerance:"):
                tol_str = line[10:].strip()
                spec.tolerance_mode, spec.margin_value = NumericalParser._parse_tolerance(tol_str)
                i += 1
                continue
            if line.startswith("Precision:"):
                prec_str = line[10:].strip()
                spec.tolerance_mode, spec.precision_value = NumericalParser._parse_precision(prec_str)
                i += 1
                continue
            i += 1
        NumericalParser._validate_and_compute_bounds(spec)
        return spec

    @staticmethod
    def _parse_tolerance(tol_str: str) -> tuple:
        tol_str = tol_str.strip()
        if '%' in tol_str:
            match = re.search(r'([\d.]+)\s*%', tol_str)
            if match:
                percent_val = float(match.group(1))
                return "percent_margin", percent_val
        tol_str = tol_str.replace('±', '').strip()
        try:
            abs_val = float(tol_str)
            return "absolute_margin", abs(abs_val)
        except ValueError as exc:
            raise ValueError(f"Cannot parse tolerance: {tol_str}") from exc

    @staticmethod
    def _parse_precision(prec_str: str) -> tuple:
        prec_str = prec_str.lower().strip()
        if 'significant' in prec_str:
            match = re.search(r'(\d+)\s+significant', prec_str)
            if match:
                return "significant_digits", int(match.group(1))
        if 'decimal' in prec_str:
            match = re.search(r'(\d+)\s+decimal', prec_str)
            if match:
                return "decimal_places", int(match.group(1))
        raise ValueError(f"Cannot parse precision: {prec_str}")

    @staticmethod
    def _validate_and_compute_bounds(spec: NumericalQuestionSpec) -> None:
        if spec.tolerance_mode == "exact":
            if spec.answer is None:
                raise ValueError("Exact mode requires Answer field")
            spec.lower_bound = spec.answer
            spec.upper_bound = spec.answer
            spec.strict_lower = False
        elif spec.tolerance_mode == "percent_margin":
            if spec.answer is None or spec.margin_value is None:
                raise ValueError("Percent margin requires Answer and Tolerance fields")
            margin_frac = spec.margin_value / 100.0
            margin_abs = abs(float(spec.answer) * margin_frac)
            spec.lower_bound = spec.answer - Decimal(str(margin_abs))
            spec.upper_bound = spec.answer + Decimal(str(margin_abs))
            spec.strict_lower = False
        elif spec.tolerance_mode == "absolute_margin":
            if spec.answer is None or spec.margin_value is None:
                raise ValueError("Absolute margin requires Answer and Tolerance fields")
            margin_dec = Decimal(str(spec.margin_value))
            spec.lower_bound = spec.answer - margin_dec
            spec.upper_bound = spec.answer + margin_dec
            spec.strict_lower = False
        elif spec.tolerance_mode == "range":
            if spec.range_min is None or spec.range_max is None:
                raise ValueError("Range mode requires Range field")
            spec.lower_bound = spec.range_min
            spec.upper_bound = spec.range_max
            spec.strict_lower = False
        elif spec.tolerance_mode == "significant_digits":
            if spec.answer is None or spec.precision_value is None:
                raise ValueError("Significant digits requires Answer and Precision fields")
            spec.lower_bound, spec.upper_bound = NumericalParser._compute_sig_digit_bounds(
                spec.answer, spec.precision_value
            )
            spec.strict_lower = True
        elif spec.tolerance_mode == "decimal_places":
            if spec.answer is None or spec.precision_value is None:
                raise ValueError("Decimal places requires Answer and Precision fields")
            spec.lower_bound, spec.upper_bound = NumericalParser._compute_decimal_place_bounds(
                spec.answer, spec.precision_value
            )
            spec.strict_lower = True

    @staticmethod
    def _compute_sig_digit_bounds(answer: Decimal, sig_digits: int) -> tuple:
        ans_float = float(answer)
        if ans_float == 0:
            offset = Decimal("0.5")
        else:
            exponent = math.floor(math.log10(abs(ans_float)))
            offset_exp = exponent - sig_digits + 1
            offset = Decimal("0.5") * Decimal(10) ** offset_exp
        lower = answer - offset
        upper = answer + offset
        return lower, upper

    @staticmethod
    def _compute_decimal_place_bounds(answer: Decimal, decimal_places: int) -> tuple:
        offset = Decimal("0.5") * Decimal(10) ** (-decimal_places)
        lower = answer - offset
        upper = answer + offset
        return lower, upper


class NumericalQTIRenderer:
    """Render a NumericalQuestionSpec to QTI XML elements."""

    @staticmethod
    def render_item(spec: NumericalQuestionSpec, item_id: str, title: str) -> str:
        xml_parts = []
        xml_parts.append(f'  <item ident="{item_id}" title="{NumericalQTIRenderer._escape_xml(title)}">')
        xml_parts.append('    <itemmetadata>')
        xml_parts.append('      <qtimetadata>')
        xml_parts.append('        <qtimetadatafield>')
        xml_parts.append('          <fieldlabel>question_type</fieldlabel>')
        xml_parts.append('          <fieldentry>numerical_question</fieldentry>')
        xml_parts.append('        </qtimetadatafield>')
        xml_parts.append('        <qtimetadatafield>')
        xml_parts.append('          <fieldlabel>points_possible</fieldlabel>')
        xml_parts.append(f'          <fieldentry>{spec.points}</fieldentry>')
        xml_parts.append('        </qtimetadatafield>')
        xml_parts.append('      </qtimetadata>')
        xml_parts.append('    </itemmetadata>')
        xml_parts.append('    <presentation>')
        xml_parts.append('      <material>')
        xml_parts.append(
            f'        <mattext texttype="text/html">&lt;p&gt;{NumericalQTIRenderer._escape_html(spec.prompt)}&lt;/p&gt;</mattext>'
        )
        xml_parts.append('      </material>')
        xml_parts.append('      <response_str ident="response1" rcardinality="Single">')
        xml_parts.append('        <render_fib fibtype="Decimal">')
        xml_parts.append('          <response_label ident="answer1"/>')
        xml_parts.append('        </render_fib>')
        xml_parts.append('      </response_str>')
        xml_parts.append('    </presentation>')
        xml_parts.append('    <resprocessing>')
        xml_parts.append('      <outcomes>')
        xml_parts.append('        <decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/>')
        xml_parts.append('      </outcomes>')
        xml_parts.append('      <respcondition continue="No">')
        xml_parts.append('        <conditionvar>')
        mode_dispatch = {
            "exact": NumericalQTIRenderer._render_exact_condition,
            "percent_margin": NumericalQTIRenderer._render_percent_condition,
            "absolute_margin": NumericalQTIRenderer._render_absolute_condition,
            "range": NumericalQTIRenderer._render_range_condition,
            "significant_digits": NumericalQTIRenderer._render_sig_digits_condition,
            "decimal_places": NumericalQTIRenderer._render_decimal_places_condition,
        }
        renderer = mode_dispatch.get(spec.tolerance_mode)
        if renderer:
            xml_parts.extend(renderer(spec))
        xml_parts.append('        </conditionvar>')
        xml_parts.append('        <setvar action="Set" varname="SCORE">100</setvar>')
        xml_parts.append('      </respcondition>')
        xml_parts.append('    </resprocessing>')
        xml_parts.append('  </item>')
        return '\n'.join(xml_parts)

    @staticmethod
    def _render_exact_condition(spec: NumericalQuestionSpec) -> list:
        return [
            '          <or>',
            f'            <varequal respident="response1">{spec.answer}</varequal>',
            '            <and>',
            f'              <vargte respident="response1">{spec.lower_bound}</vargte>',
            f'              <varlte respident="response1">{spec.upper_bound}</varlte>',
            '            </and>',
            '          </or>',
        ]

    @staticmethod
    def _render_percent_condition(spec: NumericalQuestionSpec) -> list:
        margin = NumericalQTIRenderer._format_margin_value(spec.margin_value)
        return [
            '          <or>',
            f'            <varequal respident="response1" margintype="percent" margin="{margin}">{spec.answer}</varequal>',
            '            <and>',
            f'              <vargte respident="response1">{spec.lower_bound}</vargte>',
            f'              <varlte respident="response1">{spec.upper_bound}</varlte>',
            '            </and>',
            '          </or>',
        ]

    @staticmethod
    def _render_absolute_condition(spec: NumericalQuestionSpec) -> list:
        margin = NumericalQTIRenderer._format_margin_value(spec.margin_value)
        return [
            '          <or>',
            f'            <varequal respident="response1" margintype="absolute" margin="{margin}">{spec.answer}</varequal>',
            '            <and>',
            f'              <vargte respident="response1">{spec.lower_bound}</vargte>',
            f'              <varlte respident="response1">{spec.upper_bound}</varlte>',
            '            </and>',
            '          </or>',
        ]

    @staticmethod
    def _render_range_condition(spec: NumericalQuestionSpec) -> list:
        return [
            f'          <vargte respident="response1">{spec.lower_bound}</vargte>',
            f'          <varlte respident="response1">{spec.upper_bound}</varlte>',
        ]

    @staticmethod
    def _render_sig_digits_condition(spec: NumericalQuestionSpec) -> list:
        return [
            '          <or>',
            f'            <varequal respident="response1" precisiontype="significantDigits" precision="{spec.precision_value}">{spec.answer}</varequal>',
            '            <and>',
            f'              <vargt respident="response1">{spec.lower_bound}</vargt>',
            f'              <varlte respident="response1">{spec.upper_bound}</varlte>',
            '            </and>',
            '          </or>',
        ]

    @staticmethod
    def _render_decimal_places_condition(spec: NumericalQuestionSpec) -> list:
        return [
            '          <or>',
            f'            <varequal respident="response1" precisiontype="decimals" precision="{spec.precision_value}">{spec.answer}</varequal>',
            '            <and>',
            f'              <vargt respident="response1">{spec.lower_bound}</vargt>',
            f'              <varlte respident="response1">{spec.upper_bound}</varlte>',
            '            </and>',
            '          </or>',
        ]

    @staticmethod
    def _escape_xml(text: str) -> str:
        return (
            text.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;')
        )

    @staticmethod
    def _escape_html(text: str) -> str:
        escaped = NumericalQTIRenderer._escape_xml(text)
        return escaped.replace('\n', '&lt;br/&gt;')

    @staticmethod
    def _format_margin_value(value: Optional[float]) -> str:
        if value is None:
            return "0"
        dec = Decimal(str(value))
        normalized = dec.normalize()
        if normalized == normalized.to_integral():
            return str(normalized.quantize(Decimal("1")))
        text = format(normalized, 'f')
        if '.' in text:
            text = text.rstrip('0').rstrip('.')
        return text or "0"


def test_parse_and_render() -> None:
    lines_exact = [
        "Type: NUMERICAL",
        "Points: 10",
        "Prompt:",
        "What is 2+2?",
        "Answer: 4",
    ]
    spec_exact = NumericalParser.parse(lines_exact, 10)
    print(
        f"Exact: mode={spec_exact.tolerance_mode}, answer={spec_exact.answer}, bounds=[{spec_exact.lower_bound}, {spec_exact.upper_bound}]"
    )
    lines_percent = [
        "Type: NUMERICAL",
        "Points: 10",
        "Prompt:",
        "What is 2+3?",
        "Answer: 5.0",
        "Tolerance: 1%",
    ]
    spec_percent = NumericalParser.parse(lines_percent, 10)
    print(
        f"Percent: mode={spec_percent.tolerance_mode}, margin={spec_percent.margin_value}, bounds=[{spec_percent.lower_bound}, {spec_percent.upper_bound}]"
    )
    lines_range = [
        "Type: NUMERICAL",
        "Points: 10",
        "Prompt:",
        "What is 2+5?",
        "Range: 6.0 to 8.0",
    ]
    spec_range = NumericalParser.parse(lines_range, 10)
    print(f"Range: mode={spec_range.tolerance_mode}, bounds=[{spec_range.lower_bound}, {spec_range.upper_bound}]")
    lines_sig = [
        "Type: NUMERICAL",
        "Points: 10",
        "Prompt:",
        "What is 2+6?",
        "Answer: 8.0",
        "Precision: 1 significant digit",
    ]
    spec_sig = NumericalParser.parse(lines_sig, 10)
    print(
        f"Sig Digits: mode={spec_sig.tolerance_mode}, precision={spec_sig.precision_value}, bounds=[{spec_sig.lower_bound}, {spec_sig.upper_bound}], strict_lower={spec_sig.strict_lower}"
    )
    print("\n--- Rendering Test ---")
    xml_preview = NumericalQTIRenderer.render_item(spec_sig, "item_123", "Test Question")
    print(xml_preview[:200] + "...")


if __name__ == "__main__":
    test_parse_and_render()
