"""
Test suite for numerical question decimal formatting fix.

Canvas New Quizzes requires all numeric values in varequal elements
to include a decimal point. This test validates the fix for the bug
where 5 questions failed to display in production due to missing
decimal points in integer and scientific notation values.

Bug Context:
- Known-good: "4.0", "1.5E+6" (all 36 questions displayed)
- Broken: "4", "1.5E6" (31 displayed, 5 failed)
- Failed questions: Q07, Q17, Q18, Q21, Q36 (large numbers, ranges, scientific notation)
"""

from decimal import Decimal
from quizforge.renderers.qti.numerical import _format_decimal


def test_integer_formatting():
    """Integer values must include .0 suffix"""
    assert _format_decimal(Decimal("4")) == "4.0"
    assert _format_decimal(Decimal("6")) == "6.0"
    assert _format_decimal(Decimal("-5")) == "-5.0"
    assert _format_decimal(Decimal("0")) == "0.0"
    assert _format_decimal(Decimal("100")) == "100.0"
    assert _format_decimal(Decimal("1000000")) == "1000000.0"


def test_decimal_formatting():
    """Decimals should preserve at least one trailing zero"""
    assert _format_decimal(Decimal("4.0")) == "4.0"
    assert _format_decimal(Decimal("4.5")) == "4.5"
    assert _format_decimal(Decimal("3.14159")) == "3.14159"
    # Strip excessive trailing zeros but keep the decimal point
    assert _format_decimal(Decimal("4.000")) == "4.0"
    assert _format_decimal(Decimal("3.1400")) == "3.14"


def test_scientific_notation_with_decimal():
    """Scientific notation with decimal in mantissa"""
    assert _format_decimal(Decimal("1.1E+2")) == "1.1E+2"
    assert _format_decimal(Decimal("6.674E-11")) == "6.674E-11"
    assert _format_decimal(Decimal("1.5E+6")) == "1.5E+6"


def test_scientific_notation_without_decimal():
    """Scientific notation without decimal must add .0 to mantissa"""
    # These were causing the production bug
    assert _format_decimal(Decimal("5E+1")) == "5.0E+1"
    assert _format_decimal(Decimal("-2E+1")) == "-2.0E+1"
    assert _format_decimal(Decimal("1E+6")) == "1.0E+6"
    assert _format_decimal(Decimal("2E-3")) == "2.0E-3"


def test_production_failure_cases():
    """
    Test the exact values from the 5 questions that failed in production.
    
    Q07: Large Number (1.5E+6)
    Q17-Q18: Range questions (5E+1, -2E+1)
    Q21: Very Wide Range (1E+6)
    Q36: Statistics with bounds (1.1E+2)
    """
    # Q07 - should already work (has decimal)
    assert _format_decimal(Decimal("1.5E+6")) == "1.5E+6"
    
    # Q17-Q18 - these were broken
    assert _format_decimal(Decimal("5E+1")) == "5.0E+1"
    assert _format_decimal(Decimal("-2E+1")) == "-2.0E+1"
    
    # Q21 - this was broken
    assert _format_decimal(Decimal("1E+6")) == "1.0E+6"
    
    # Q36 - might have had issues with bounds
    assert _format_decimal(Decimal("1.1E+2")) == "1.1E+2"


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    assert _format_decimal(Decimal("0.0")) == "0.0"
    assert _format_decimal(Decimal("-0")) == "0.0"
    assert _format_decimal(Decimal("0.001")) == "0.001"
    assert _format_decimal(Decimal("-3.5")) == "-3.5"
    assert _format_decimal(Decimal("1E-10")) == "1.0E-10"


def test_normalize_behavior():
    """Test that Decimal.normalize() behavior is handled correctly"""
    # normalize() converts 10.0 to 1E+1, ensure we handle it
    normalized = Decimal("10.0").normalize()
    result = _format_decimal(normalized)
    # Should be either "10.0" or "1.0E+1" depending on normalize behavior
    assert "." in result, f"Result {result} must contain decimal point"
    assert result in ["10.0", "1.0E+1"], f"Unexpected format: {result}"


if __name__ == "__main__":
    # Run all tests
    test_integer_formatting()
    test_decimal_formatting()
    test_scientific_notation_with_decimal()
    test_scientific_notation_without_decimal()
    test_production_failure_cases()
    test_edge_cases()
    test_normalize_behavior()
    print("✓ All decimal formatting tests passed!")
