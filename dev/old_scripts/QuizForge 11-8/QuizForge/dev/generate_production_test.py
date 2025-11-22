#!/usr/bin/env python3
"""
Generate QTI ZIP using the PRODUCTION QuizForge packager (with decimal fix).

This uses the actual quizforge.packager with the _format_decimal fix applied.
"""

import sys
import os
from pathlib import Path
from decimal import Decimal

# Add Packager to path
sys.path.insert(0, str(Path(__file__).parent.parent / "Packager"))

from quizforge.domain.questions import NumericalQuestion, NumericalAnswer
from quizforge.domain.assessment import Assessment
from quizforge.io.qti_writer import QTIWriter


def parse_numerical_test_file(filepath: Path):
    """Parse the numerical_realworld_edgecases.txt file."""
    questions = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by question markers
    blocks = content.split('---QUESTION')[1:]  # Skip header
    
    for i, block in enumerate(blocks, 1):
        lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
        
        q_data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                q_data[key.strip()] = value.strip()
        
        # Parse the question
        prompt = q_data.get('Prompt', f'Question {i}')
        points = float(q_data.get('Points', '1.0'))
        
        # Parse answer spec
        mode = q_data.get('Mode', 'exact').lower()
        answer_val = Decimal(q_data.get('Answer', '0'))
        
        # Create NumericalAnswer based on mode
        if mode == 'range':
            lower = Decimal(q_data.get('Lower', '0'))
            upper = Decimal(q_data.get('Upper', '0'))
            strict = q_data.get('Strict', 'false').lower() == 'true'
            
            answer_spec = NumericalAnswer(
                tolerance_mode='range',
                answer=answer_val,
                lower_bound=lower,
                upper_bound=upper,
                strict_lower=strict
            )
        elif mode == 'percent':
            margin = Decimal(q_data.get('Margin', '0'))
            answer_spec = NumericalAnswer(
                tolerance_mode='percent_margin',
                answer=answer_val,
                margin_value=margin
            )
        elif mode == 'absolute':
            margin = Decimal(q_data.get('Margin', '0'))
            answer_spec = NumericalAnswer(
                tolerance_mode='absolute_margin',
                answer=answer_val,
                margin_value=margin
            )
        elif mode == 'sigfigs':
            precision = int(q_data.get('Precision', '3'))
            answer_spec = NumericalAnswer(
                tolerance_mode='significant_digits',
                answer=answer_val,
                precision_value=precision
            )
        elif mode == 'decimals':
            precision = int(q_data.get('Precision', '2'))
            answer_spec = NumericalAnswer(
                tolerance_mode='decimal_places',
                answer=answer_val,
                precision_value=precision
            )
        else:  # exact
            answer_spec = NumericalAnswer(
                tolerance_mode='exact',
                answer=answer_val
            )
        
        # Create question
        question = NumericalQuestion(
            qtype='numerical_question',
            prompt=prompt,
            answer=answer_spec,
            points=points
        )
        
        questions.append(question)
    
    return questions


def main():
    print("=" * 80)
    print("PRODUCTION PACKAGER - 36 Numerical Questions with Decimal Fix")
    print("=" * 80)
    print()
    
    # Find the test file
    test_file = Path(__file__).parent / "numerical_realworld_edgecases.txt"
    
    if not test_file.exists():
        print(f"❌ ERROR: Test file not found: {test_file}")
        return False
    
    print(f"📖 Reading: {test_file.name}")
    
    try:
        questions = parse_numerical_test_file(test_file)
        print(f"✅ Parsed {len(questions)} questions")
    except Exception as e:
        print(f"❌ ERROR parsing questions: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Create assessment
    assessment = Assessment(
        title="Numerical Edge Cases - Production Test",
        description="36 numerical questions testing all modes with decimal formatting fix",
        questions=questions
    )
    
    print(f"📦 Total points: {sum(q.points for q in questions)}")
    print()
    
    # Generate QTI package
    output_file = Path(__file__).parent / "numerical_production_test.zip"
    
    try:
        print(f"🔨 Generating QTI package...")
        writer = QTIWriter()
        writer.write(assessment, str(output_file))
        
        size_kb = output_file.stat().st_size / 1024
        print(f"✅ Created: {output_file.name}")
        print(f"   Size: {size_kb:.1f} KB")
        print(f"   Questions: {len(questions)}")
        print()
        
    except Exception as e:
        print(f"❌ ERROR generating package: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 80)
    print("✅ SUCCESS - Package ready for Canvas import")
    print("=" * 80)
    print()
    print("📋 Canvas Import Steps:")
    print("   1. Go to Canvas → Quizzes → New Quiz")
    print("   2. Click ... (three dots) → Import Content")
    print(f"   3. Upload: {output_file.name}")
    print()
    print("🔍 Verify:")
    print("   • All 36 questions appear (not just 31)")
    print("   • Q07, Q17, Q18, Q21, Q36 are now visible")
    print("   • Questions with scientific notation display correctly")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
