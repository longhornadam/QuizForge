"""
Quick test to verify the decimal formatting fix resolves the production bug.
Generates a mini QTI package with the 5 problematic questions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Packager'))

from decimal import Decimal
from quizforge.domain.questions import NumericalQuestion, NumericalAnswer
from quizforge.renderers.qti.numerical import build_numerical_item
import xml.etree.ElementTree as ET


def create_test_question(title, answer, lower, upper, strict_lower=False):
    """Create a numerical question for testing."""
    spec = NumericalAnswer(
        tolerance_mode="range",
        answer=answer,
        lower_bound=lower,
        upper_bound=upper,
        strict_lower=strict_lower
    )
    
    return NumericalQuestion(
        qtype="numerical_question",
        prompt=f"Test question: {title}",
        answer=spec,
        points=1.0
    )


def check_decimal_points(xml_string):
    """Check if all numeric values in varequal elements have decimal points."""
    import re
    
    # Find all varequal and vargte/varlte elements
    patterns = [
        r'<varequal[^>]*>([^<]+)</varequal>',
        r'<vargte[^>]*>([^<]+)</vargte>',
        r'<vargt[^>]*>([^<]+)</vargt>',
        r'<varlte[^>]*>([^<]+)</varlte>',
    ]
    
    issues = []
    for pattern in patterns:
        matches = re.findall(pattern, xml_string)
        for match in matches:
            value = match.strip()
            # Check if it's a number without a decimal point
            if value and not '.' in value:
                issues.append(f"Missing decimal point: {value}")
    
    return issues


def main():
    print("=" * 80)
    print("PRODUCTION BUG FIX VERIFICATION")
    print("Testing the 5 questions that failed to display in Canvas")
    print("=" * 80)
    print()
    
    # The 5 problematic questions from production
    test_cases = [
        ("Q07: Large Number", Decimal("1.5E+6"), Decimal("1.4E+6"), Decimal("1.6E+6")),
        ("Q17: Range (50)", Decimal("5E+1"), Decimal("4E+1"), Decimal("6E+1")),
        ("Q18: Range (-20)", Decimal("-2E+1"), Decimal("-3E+1"), Decimal("-1E+1")),
        ("Q21: Very Wide Range", Decimal("1E+6"), Decimal("0"), Decimal("2E+6")),
        ("Q36: Statistics", Decimal("1.1E+2"), Decimal("1.0E+2"), Decimal("1.2E+2")),
    ]
    
    all_passed = True
    
    for i, (title, answer, lower, upper) in enumerate(test_cases, 1):
        print(f"Test {i}: {title}")
        print(f"  Answer: {answer}, Range: [{lower}, {upper}]")
        
        question = create_test_question(title, answer, lower, upper)
        item = build_numerical_item(question, i)
        
        # Convert to string
        xml_string = ET.tostring(item, encoding='unicode')
        
        # Check for decimal points
        issues = check_decimal_points(xml_string)
        
        if issues:
            print(f"  ✗ FAILED: {', '.join(issues)}")
            all_passed = False
        else:
            print(f"  ✓ PASSED: All numeric values have decimal points")
        
        # Show sample of the output
        if "varequal" in xml_string:
            import re
            varequal_match = re.search(r'<varequal[^>]*>([^<]+)</varequal>', xml_string)
            if varequal_match:
                print(f"  Sample: <varequal>{varequal_match.group(1)}</varequal>")
        
        # Show bounds
        import re
        bounds = re.findall(r'<var(gte?|lte)[^>]*>([^<]+)</var', xml_string)
        if bounds:
            print(f"  Bounds: {', '.join([f'{tag}={val}' for tag, val in bounds])}")
        
        print()
    
    print("=" * 80)
    if all_passed:
        print("✓✓✓ SUCCESS! All 5 problematic questions now have proper decimal formatting.")
        print("    The questions should now display correctly in Canvas New Quizzes.")
        return 0
    else:
        print("✗✗✗ FAILURE! Some questions still have missing decimal points.")
        print("    Review the output above for details.")
        return 1


if __name__ == "__main__":
    exit(main())
