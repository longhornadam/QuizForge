"""
Validate the numerical decimal formatting fix for Canvas QTI.

This script tests the fix for the production bug where 5 numerical questions
failed to display due to missing decimal points in varequal values.
"""

import sys
import os
# Add Packager directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Packager'))

from decimal import Decimal
from quizforge.renderers.qti.numerical import _format_decimal


def test_case(description, value, expected):
    """Test a single formatting case."""
    result = _format_decimal(value)
    status = "✓" if result == expected else "✗"
    print(f"{status} {description:50} {str(value):15} → {result:15} (expected: {expected})")
    return result == expected


def main():
    print("=" * 100)
    print("NUMERICAL DECIMAL FORMATTING VALIDATION")
    print("=" * 100)
    print()
    
    all_passed = True
    
    print("1. INTEGER FORMATTING (must have .0 suffix)")
    print("-" * 100)
    all_passed &= test_case("Simple integer 4", Decimal("4"), "4.0")
    all_passed &= test_case("Simple integer 6", Decimal("6"), "6.0")
    all_passed &= test_case("Negative integer -5", Decimal("-5"), "-5.0")
    all_passed &= test_case("Zero", Decimal("0"), "0.0")
    # Note: Decimal.normalize() may convert large integers to scientific notation
    result = _format_decimal(Decimal("1000000"))
    if result in ["1000000.0", "1.0E+6"]:
        print(f"✓ Large integer                                      1000000         → {result:15} (normalized)")
    else:
        print(f"✗ Large integer                                      1000000         → {result:15} (unexpected)")
        all_passed = False
    print()
    
    print("2. DECIMAL FORMATTING (preserve decimal point)")
    print("-" * 100)
    all_passed &= test_case("Simple decimal 4.0", Decimal("4.0"), "4.0")
    all_passed &= test_case("Decimal 4.5", Decimal("4.5"), "4.5")
    all_passed &= test_case("Pi approximation", Decimal("3.14159"), "3.14159")
    all_passed &= test_case("Trailing zeros stripped", Decimal("4.000"), "4.0")
    all_passed &= test_case("Some trailing zeros", Decimal("3.1400"), "3.14")
    print()
    
    print("3. SCIENTIFIC NOTATION WITH DECIMAL (already correct)")
    print("-" * 100)
    all_passed &= test_case("110 as scientific", Decimal("1.1E+2"), "1.1E+2")
    all_passed &= test_case("Gravitational constant", Decimal("6.674E-11"), "6.674E-11")
    all_passed &= test_case("1.5 million", Decimal("1.5E+6"), "1.5E+6")
    print()
    
    print("4. SCIENTIFIC NOTATION WITHOUT DECIMAL (THE BUG - must add .0)")
    print("-" * 100)
    all_passed &= test_case("50 as scientific", Decimal("5E+1"), "5.0E+1")
    all_passed &= test_case("-20 as scientific", Decimal("-2E+1"), "-2.0E+1")
    all_passed &= test_case("1 million", Decimal("1E+6"), "1.0E+6")
    # Note: Decimal.normalize() may NOT convert small decimals to scientific
    result = _format_decimal(Decimal("2E-3"))
    if result in ["2.0E-3", "0.002"]:
        print(f"✓ Small scientific                                   2E-3            → {result:15} (normalized)")
    else:
        print(f"✗ Small scientific                                   2E-3            → {result:15} (unexpected)")
        all_passed = False
    print()
    
    print("5. PRODUCTION FAILURE CASES (The 5 questions that didn't display)")
    print("-" * 100)
    all_passed &= test_case("Q07: Large Number", Decimal("1.5E+6"), "1.5E+6")
    all_passed &= test_case("Q17-Q18: Range (50)", Decimal("5E+1"), "5.0E+1")
    all_passed &= test_case("Q17-Q18: Range (-20)", Decimal("-2E+1"), "-2.0E+1")
    all_passed &= test_case("Q21: Very Wide Range", Decimal("1E+6"), "1.0E+6")
    all_passed &= test_case("Q36: Statistics", Decimal("1.1E+2"), "1.1E+2")
    print()
    
    print("6. EDGE CASES")
    print("-" * 100)
    all_passed &= test_case("Zero decimal", Decimal("0.0"), "0.0")
    all_passed &= test_case("Small decimal", Decimal("0.001"), "0.001")
    all_passed &= test_case("Negative decimal", Decimal("-3.5"), "-3.5")
    all_passed &= test_case("Tiny scientific", Decimal("1E-10"), "1.0E-10")
    print()
    
    print("=" * 100)
    if all_passed:
        print("✓✓✓ ALL TESTS PASSED! The decimal formatting fix is working correctly.")
        print("    All numeric values now include decimal points as required by Canvas.")
        return 0
    else:
        print("✗✗✗ SOME TESTS FAILED! Review the output above.")
        return 1


if __name__ == "__main__":
    exit(main())
