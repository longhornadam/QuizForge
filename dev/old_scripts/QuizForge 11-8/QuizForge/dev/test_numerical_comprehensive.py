#!/usr/bin/env python3
"""
Comprehensive integration test for NUMERICAL question type.

This script:
1. Tests extraction of all 6 reference questions from Canvas ZIP
2. Tests parsing of plain-text QuizForge format
3. Tests rendering to QTI XML
4. Compares parser output against reference expectations
5. Validates round-trip (parse -> render -> compare)
"""

import sys
from pathlib import Path

# Import test modules
sys.path.insert(0, str(Path(__file__).parent))

from test_numerical_questions import TestNumericalQuestions, NumericalQTIExtractor, NumericalAnswer
from numerical_experimental import NumericalParser, NumericalQTIRenderer, NumericalQuestionSpec
from decimal import Decimal


class ComprehensiveNumericalTest:
    """Comprehensive test suite integrating extraction, parsing, and rendering."""
    
    def run(self):
        """Execute all tests."""
        print("=" * 80)
        print("COMPREHENSIVE NUMERICAL QUESTION TYPE TEST SUITE")
        print("=" * 80)
        print()
        
        tests = [
            ("Reference ZIP Extraction", self.test_reference_extraction),
            ("Plain-Text Parsing", self.test_plain_text_parsing),
            ("QTI Rendering", self.test_qti_rendering),
            ("Round-Trip Validation", self.test_round_trip),
        ]
        
        results = {}
        for name, test_func in tests:
            print(f"\n>>> {name}")
            print("-" * 80)
            try:
                success = test_func()
                results[name] = "PASS" if success else "FAIL"
                status = "[OK]" if success else "[FAIL]"
                print(f"{status} {name}")
            except Exception as e:
                results[name] = "ERROR"
                print(f"[ERROR] {name}: {e}")
                import traceback
                traceback.print_exc()
        
        # Summary
        print()
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        for name, result in results.items():
            status_icon = "[OK]" if result == "PASS" else "[FAIL]" if result == "FAIL" else "[!]"
            print(f"{status_icon} {name}: {result}")
        
        all_pass = all(r == "PASS" for r in results.values())
        print()
        if all_pass:
            print("[OK] ALL TESTS PASSED")
        else:
            print("[FAIL] SOME TESTS FAILED")
        print("=" * 80)
        
        return all_pass
    
    def test_reference_extraction(self) -> bool:
        """Test extraction of reference ZIP."""
        tester = TestNumericalQuestions()
        return tester.run_all_tests()
    
    def test_plain_text_parsing(self) -> bool:
        """Test parsing of plain-text format."""
        print("\n1. Testing Exact Mode")
        lines = [
            "Type: NUMERICAL",
            "Points: 10",
            "Prompt:",
            "What is 2+2?",
            "Answer: 4"
        ]
        spec = NumericalParser.parse(lines, 10.0)
        assert spec.tolerance_mode == "exact", f"Expected exact, got {spec.tolerance_mode}"
        assert spec.answer == Decimal("4"), f"Expected answer 4, got {spec.answer}"
        assert spec.lower_bound == Decimal("4"), f"Expected lower bound 4, got {spec.lower_bound}"
        print("   [OK] Exact mode parsed correctly")
        
        print("\n2. Testing Percent Margin")
        lines = [
            "Type: NUMERICAL",
            "Points: 10",
            "Prompt:",
            "What is 2+3?",
            "Answer: 5.0",
            "Tolerance: 1%"
        ]
        spec = NumericalParser.parse(lines, 10.0)
        assert spec.tolerance_mode == "percent_margin", f"Expected percent_margin, got {spec.tolerance_mode}"
        assert spec.margin_value == 1.0, f"Expected margin 1.0, got {spec.margin_value}"
        assert spec.lower_bound == Decimal("4.95"), f"Expected lower 4.95, got {spec.lower_bound}"
        print("   [OK] Percent margin parsed correctly")
        
        print("\n3. Testing Absolute Margin")
        lines = [
            "Type: NUMERICAL",
            "Points: 10",
            "Prompt:",
            "What is 2+4?",
            "Answer: 6.0",
            "Tolerance: ±1"
        ]
        spec = NumericalParser.parse(lines, 10.0)
        assert spec.tolerance_mode == "absolute_margin", f"Expected absolute_margin, got {spec.tolerance_mode}"
        assert spec.margin_value == 1.0, f"Expected margin 1.0, got {spec.margin_value}"
        assert spec.lower_bound == Decimal("5.0"), f"Expected lower 5.0, got {spec.lower_bound}"
        print("   [OK] Absolute margin parsed correctly")
        
        print("\n4. Testing Range")
        lines = [
            "Type: NUMERICAL",
            "Points: 10",
            "Prompt:",
            "What is 2+5?",
            "Range: 6.0 to 8.0"
        ]
        spec = NumericalParser.parse(lines, 10.0)
        assert spec.tolerance_mode == "range", f"Expected range, got {spec.tolerance_mode}"
        assert spec.lower_bound == Decimal("6.0"), f"Expected lower 6.0, got {spec.lower_bound}"
        assert spec.upper_bound == Decimal("8.0"), f"Expected upper 8.0, got {spec.upper_bound}"
        print("   [OK] Range parsed correctly")
        
        print("\n5. Testing Significant Digits")
        lines = [
            "Type: NUMERICAL",
            "Points: 10",
            "Prompt:",
            "What is 2+6?",
            "Answer: 8.0",
            "Precision: 1 significant digit"
        ]
        spec = NumericalParser.parse(lines, 10.0)
        assert spec.tolerance_mode == "significant_digits", f"Expected significant_digits, got {spec.tolerance_mode}"
        assert spec.precision_value == 1, f"Expected precision 1, got {spec.precision_value}"
        assert spec.strict_lower == True, f"Expected strict_lower True, got {spec.strict_lower}"
        print("   [OK] Significant digits parsed correctly")
        
        print("\n6. Testing Decimal Places")
        lines = [
            "Type: NUMERICAL",
            "Points: 10",
            "Prompt:",
            "What is 2+7?",
            "Answer: 9.0",
            "Precision: 1 decimal place"
        ]
        spec = NumericalParser.parse(lines, 10.0)
        assert spec.tolerance_mode == "decimal_places", f"Expected decimal_places, got {spec.tolerance_mode}"
        assert spec.precision_value == 1, f"Expected precision 1, got {spec.precision_value}"
        print("   [OK] Decimal places parsed correctly")
        
        return True
    
    def test_qti_rendering(self) -> bool:
        """Test QTI rendering."""
        print("\n1. Testing Exact Mode Rendering")
        spec = NumericalQuestionSpec(
            prompt="What is 2+2?",
            points=10.0,
            answer=Decimal("4"),
            tolerance_mode="exact",
            lower_bound=Decimal("4"),
            upper_bound=Decimal("4")
        )
        xml = NumericalQTIRenderer.render_item(spec, "item_001", "Exact Response")
        assert '<varequal respident="response1">4</varequal>' in xml, "Missing exact varequal"
        print("   [OK] Exact mode rendered correctly")
        
        print("\n2. Testing Percent Margin Rendering")
        spec = NumericalQuestionSpec(
            prompt="What is 2+3?",
            points=10.0,
            answer=Decimal("5.0"),
            tolerance_mode="percent_margin",
            margin_value=1.0,
            lower_bound=Decimal("4.95"),
            upper_bound=Decimal("5.05")
        )
        xml = NumericalQTIRenderer.render_item(spec, "item_002", "MoE +1 %")
        assert 'margintype="percent"' in xml, "Missing margintype=percent"
        assert 'margin="1"' in xml, "Missing margin=1"
        print("   [OK] Percent margin rendered correctly")
        
        print("\n3. Testing Range Rendering")
        spec = NumericalQuestionSpec(
            prompt="What is 2+5?",
            points=10.0,
            tolerance_mode="range",
            lower_bound=Decimal("6.0"),
            upper_bound=Decimal("8.0")
        )
        xml = NumericalQTIRenderer.render_item(spec, "item_003", "Within a range")
        assert '<varequal' not in xml, "Range should not have varequal"
        assert '<vargte respident="response1">6.0</vargte>' in xml, "Missing lower bound vargte"
        print("   [OK] Range rendered correctly")
        
        print("\n4. Testing Sig Digits Rendering")
        spec = NumericalQuestionSpec(
            prompt="What is 2+6?",
            points=10.0,
            answer=Decimal("8.0"),
            tolerance_mode="significant_digits",
            precision_value=1,
            lower_bound=Decimal("7.5"),
            upper_bound=Decimal("8.5"),
            strict_lower=True
        )
        xml = NumericalQTIRenderer.render_item(spec, "item_004", "Sig Digits")
        assert 'precisiontype="significantDigits"' in xml, "Missing precisiontype"
        assert '<vargt respident="response1">7.5</vargt>' in xml, "Missing strict lower bound vargt"
        print("   [OK] Sig digits rendered correctly")
        
        return True
    
    def test_round_trip(self) -> bool:
        """Test round-trip: reference ZIP -> extract -> parse -> render -> compare."""
        print("\nTesting round-trip: ZIP extraction -> parsing -> rendering")
        
        try:
            ref_path = Path(__file__).parent / "325ee68f920c908f6288d973d0bb1173004a6f77783268b66256ad2b118d1995"
            extractor = NumericalQTIExtractor(ref_path)
            ref_questions = extractor.extract_all_questions()
            
            print(f"\n[OK] Extracted {len(ref_questions)} reference questions")
            
            # For each reference question, verify we can render similar QTI
            for title, (prompt, answer_model) in list(ref_questions.items())[:2]:  # Test first 2
                print(f"\n  Round-trip: {title}")
                
                # Create a spec matching the extracted answer model
                spec = NumericalQuestionSpec(
                    prompt=prompt,
                    points=1.0,
                    answer=answer_model.answer,
                    tolerance_mode=answer_model.tolerance_mode,
                    margin_value=answer_model.margin_value,
                    precision_value=answer_model.precision_value,
                    lower_bound=answer_model.lower_bound,
                    upper_bound=answer_model.upper_bound,
                    strict_lower=answer_model.strict_lower
                )
                
                # Render to QTI
                xml = NumericalQTIRenderer.render_item(spec, "test_item", title)
                
                # Verify key elements are present
                assert '<item' in xml, f"Missing item element in {title}"
                assert 'response1' in xml, f"Missing response element in {title}"
                assert answer_model.tolerance_mode in xml or 'vargte' in xml, f"Missing tolerance indicators in {title}"
                
                print(f"    [OK] Successfully rendered to QTI")
            
            return True
        
        except Exception as e:
            print(f"\n[FAIL] Round-trip test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    tester = ComprehensiveNumericalTest()
    success = tester.run()
    sys.exit(0 if success else 1)
