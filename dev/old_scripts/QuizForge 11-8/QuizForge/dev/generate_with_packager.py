#!/usr/bin/env python3
"""
Generate QTI ZIP using PRODUCTION packager with decimal fix.
Converts numerical_realworld_edgecases.txt to QuizForge text format.
"""

import sys
from pathlib import Path

# Add Packager to path
sys.path.insert(0, str(Path(__file__).parent.parent / "Packager"))

from quizforge.services.packager import Packager


def convert_to_quizforge_format(input_file: Path) -> str:
    """Convert numerical test file to QuizForge text outline format."""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Start output
    output_lines = [
        "# Numerical Edge Cases - Production Test",
        "36 numerical questions testing all tolerance modes with decimal formatting fix",
        ""
    ]
    
    # Split by question markers
    blocks = content.split('---QUESTION')[1:]
    
    for i, block in enumerate(blocks, 1):
        lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
        
        q_data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                q_data[key.strip()] = value.strip()
        
        # Build QuizForge question
        prompt = q_data.get('Prompt', f'Question {i}')
        points = q_data.get('Points', '1.0')
        mode = q_data.get('Mode', 'exact').lower()
        answer = q_data.get('Answer', '0')
        
        output_lines.append(f"## [numerical] Q{i:02d}: {prompt[:50]}")
        output_lines.append(f"Points: {points}")
        output_lines.append("")
        output_lines.append(prompt)
        output_lines.append("")
        
        # Build answer specification based on mode
        if mode == 'range':
            lower = q_data.get('Lower', '0')
            upper = q_data.get('Upper', '0')
            strict = q_data.get('Strict', 'false')
            output_lines.append(f"answer: {answer}")
            output_lines.append(f"tolerance: range")
            output_lines.append(f"range: {lower} to {upper}")
            if strict.lower() == 'true':
                output_lines.append(f"strict_lower: true")
        
        elif mode == 'percent':
            margin = q_data.get('Margin', '0')
            output_lines.append(f"answer: {answer}")
            output_lines.append(f"tolerance: percent")
            output_lines.append(f"margin: {margin}")
        
        elif mode == 'absolute':
            margin = q_data.get('Margin', '0')
            output_lines.append(f"answer: {answer}")
            output_lines.append(f"tolerance: absolute")
            output_lines.append(f"margin: {margin}")
        
        elif mode == 'sigfigs':
            precision = q_data.get('Precision', '3')
            output_lines.append(f"answer: {answer}")
            output_lines.append(f"tolerance: significant_digits")
            output_lines.append(f"precision: {precision}")
        
        elif mode == 'decimals':
            precision = q_data.get('Precision', '2')
            output_lines.append(f"answer: {answer}")
            output_lines.append(f"tolerance: decimal_places")
            output_lines.append(f"precision: {precision}")
        
        else:  # exact
            output_lines.append(f"answer: {answer}")
            output_lines.append(f"tolerance: exact")
        
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")
    
    return '\n'.join(output_lines)


def main():
    print("=" * 80)
    print("PRODUCTION PACKAGER - 36 Numerical Questions (Decimal Fix Applied)")
    print("=" * 80)
    print()
    
    # Find test file
    test_file = Path(__file__).parent / "numerical_realworld_edgecases.txt"
    
    if not test_file.exists():
        print(f"❌ ERROR: Test file not found: {test_file}")
        return False
    
    print(f"📖 Reading: {test_file.name}")
    
    # Convert to QuizForge format
    try:
        quizforge_text = convert_to_quizforge_format(test_file)
        print(f"✅ Converted to QuizForge text format")
    except Exception as e:
        print(f"❌ ERROR converting file: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Package using production packager
    output_file = Path(__file__).parent / "numerical_production_test.zip"
    
    try:
        print(f"🔨 Packaging with QuizForge (decimal fix applied)...")
        packager = Packager()
        result = packager.package_text(quizforge_text)
        
        # Write to file
        with open(output_file, 'wb') as f:
            f.write(result.zip_bytes)
        
        size_kb = Path(output_file).stat().st_size / 1024
        print(f"✅ Created: {output_file.name}")
        print(f"   Size: {size_kb:.1f} KB")
        print(f"   Questions: {len(result.quiz.questions)}")
        print(f"   Total Points: {result.quiz.total_points()}")
        print()
        
        # Show inspection
        print("📋 Package Inspection:")
        print(f"   GUID: {result.guid}")
        print(f"   Valid: {result.inspection.valid}")
        if result.inspection.errors:
            print("   Errors:", result.inspection.errors)
        print()
        
    except Exception as e:
        print(f"❌ ERROR packaging: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 80)
    print("✅ SUCCESS - Package ready for Canvas!")
    print("=" * 80)
    print()
    print("📋 Canvas Import Steps:")
    print("   1. Go to Canvas → Quizzes → New Quiz")
    print("   2. Click ... (three dots) → Import Content")
    print(f"   3. Upload: {output_file.name}")
    print()
    print("🔍 Key Verification Points:")
    print("   ✓ All 36 questions should appear (not just 31)")
    print("   ✓ Q07, Q17, Q18, Q21, Q36 now visible (previously failed)")
    print("   ✓ All numeric values have decimal points (4.0 not 4)")
    print("   ✓ Scientific notation formatted correctly (5.0E+1 not 5E+1)")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
