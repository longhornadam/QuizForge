#!/usr/bin/env python3
"""
Generate a QTI ZIP export from numerical edge case test file.

This script:
1. Parses numerical_realworld_edgecases.txt
2. Converts each question to QTI XML
3. Creates a Canvas-compatible ZIP file
4. Validates the output can be imported into Canvas

Output: numerical_edgecases_export.zip
"""

import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import uuid

# Add experimental module
sys.path.insert(0, str(Path(__file__).parent))
from numerical_experimental import NumericalParser, NumericalQTIRenderer, NumericalQuestionSpec


class QTIQuizBuilder:
    """Build complete QTI assessment with multiple questions."""
    
    def __init__(self, title: str, description: str = ""):
        self.title = title
        self.description = description
        self.questions = []
        self.assessment_id = str(uuid.uuid4()).replace('-', '')[:32]
        self._title_counts: dict[str, int] = {}
    
    def add_question(self, spec: NumericalQuestionSpec, item_id: str, question_num: int) -> None:
        """Add a parsed numerical question."""
        display_title = self._derive_title(spec, fallback=f"Question {question_num}")
        occurrence = self._title_counts.get(display_title, 0)
        self._title_counts[display_title] = occurrence + 1
        if occurrence:
            display_title = f"{display_title} ({occurrence + 1})"
        self.questions.append({
            'spec': spec,
            'item_id': item_id,
            'num': question_num,
            'title': display_title
        })
    
    def build_assessment_xml(self) -> str:
        """Build main assessment XML."""
        lines = []
        lines.append('<?xml version="1.0"?>')
        lines.append('<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.imsglobal.org/xsd/ims_qtiasiv1p2 http://www.imsglobal.org/xsd/ims_qtiasiv1p2p1.xsd">')
        lines.append(f'  <assessment ident="{self.assessment_id}" title="Numerical Edge Cases" external_assignment_id="{uuid.uuid4()}">')
        lines.append('    <qtimetadata>')
        lines.append('      <qtimetadatafield>')
        lines.append('        <fieldlabel>cc_maxattempts</fieldlabel>')
        lines.append('        <fieldentry>1</fieldentry>')
        lines.append('      </qtimetadatafield>')
        lines.append('    </qtimetadata>')
        lines.append('    <section ident="root_section">')
        
        # Add all items
        for q in self.questions:
            item_xml = NumericalQTIRenderer.render_item(q['spec'], q['item_id'], q['title'])
            lines.append(item_xml)
        
        lines.append('    </section>')
        lines.append('  </assessment>')
        lines.append('</questestinterop>')
        
        return '\n'.join(lines)

    @staticmethod
    def _derive_title(spec: NumericalQuestionSpec, fallback: str) -> str:
        """Derive a readable Canvas item title from the prompt."""
        prompt = (spec.prompt or "").strip()
        if not prompt:
            return fallback
        first_line = prompt.splitlines()[0].strip()
        if not first_line:
            return fallback
        if ':' in first_line:
            candidate = first_line.split(':', 1)[0].strip()
            if candidate:
                return candidate
        return first_line
    
    def build_manifest_xml(self) -> str:
        """Build IMS manifest."""
        lines = []
        lines.append('<?xml version="1.0"?>')
        lines.append('<manifest xmlns="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1" xmlns:lom="http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource" xmlns:imsmd="http://www.imsglobal.org/xsd/imsmd_v1p2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" identifier="{}" xsi:schemaLocation="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1 http://www.imsglobal.org/xsd/imscp_v1p1.xsd http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource http://www.imsglobal.org/profile/cc/ccv1p1/LOM/ccv1p1_lomresource_v1p0.xsd http://www.imsglobal.org/xsd/imsmd_v1p2 http://www.imsglobal.org/xsd/imsmd_v1p2p2.xsd">'.format(uuid.uuid4()))
        lines.append('  <metadata>')
        lines.append('    <schema>IMS Content</schema>')
        lines.append('    <schemaversion>1.1.3</schemaversion>')
        lines.append('    <imsmd:lom>')
        lines.append('      <imsmd:general>')
        lines.append('        <imsmd:title>')
        lines.append(f'          <imsmd:string>QTI Quiz Export - {self.title}</imsmd:string>')
        lines.append('        </imsmd:title>')
        lines.append('      </imsmd:general>')
        lines.append('      <imsmd:lifeCycle>')
        lines.append('        <imsmd:contribute>')
        lines.append('          <imsmd:date>')
        lines.append(f'            <imsmd:dateTime>{datetime.now().isoformat()}</imsmd:dateTime>')
        lines.append('          </imsmd:date>')
        lines.append('        </imsmd:contribute>')
        lines.append('      </imsmd:lifeCycle>')
        lines.append('      <imsmd:rights>')
        lines.append('        <imsmd:copyrightAndOtherRestrictions>')
        lines.append('          <imsmd:value>yes</imsmd:value>')
        lines.append('        </imsmd:copyrightAndOtherRestrictions>')
        lines.append('        <imsmd:description>')
        lines.append('          <imsmd:string>Private (Copyrighted)</imsmd:string>')
        lines.append('        </imsmd:description>')
        lines.append('      </imsmd:rights>')
        lines.append('    </imsmd:lom>')
        lines.append('  </metadata>')
        lines.append('  <organizations/>')
        lines.append('  <resources>')
        
        qti_id = str(uuid.uuid4()).replace('-', '')[:32]
        meta_id = str(uuid.uuid4()).replace('-', '')[:32]
        
        lines.append(f'    <resource identifier="{qti_id}" type="imsqti_xmlv1p2">')
        lines.append(f'      <file href="{qti_id}/{qti_id}.xml"/>')
        lines.append(f'      <dependency identifierref="{meta_id}"/>')
        lines.append('    </resource>')
        lines.append(f'    <resource identifier="{meta_id}" type="associatedcontent/imscc_xmlv1p1/learning-application-resource" href="{qti_id}/assessment_meta.xml">')
        lines.append(f'      <file href="{qti_id}/assessment_meta.xml"/>')
        lines.append('    </resource>')
        lines.append('  </resources>')
        lines.append('</manifest>')
        
        return '\n'.join(lines), qti_id
    
    def build_meta_xml(self, total_points: float) -> str:
        """Build Canvas assessment metadata."""
        lines = []
        lines.append('<?xml version="1.0"?>')
        lines.append('<quiz xmlns="http://canvas.instructure.com/xsd/cccv1p0" xmlns:xsi="http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd" identifier="{}">')
        lines.append(f'  <title>{self.title}</title>')
        lines.append('  <description/>')
        lines.append(f'  <points_possible>{total_points}</points_possible>')
        lines.append('  <quiz_type>assignment</quiz_type>')
        lines.append('  <shuffle_questions>false</shuffle_questions>')
        lines.append('  <shuffle_answers>false</shuffle_answers>')
        lines.append('  <calculator_type>none</calculator_type>')
        lines.append('  <allowed_attempts>1</allowed_attempts>')
        lines.append('  <hide_results/>')
        lines.append('  <show_correct_answers>false</show_correct_answers>')
        lines.append('  <one_question_at_a_time>false</one_question_at_a_time>')
        lines.append('</quiz>')
        
        return '\n'.join(lines)
    
    def export_zip(self, output_path: str) -> None:
        """Export as Canvas-compatible QTI ZIP."""
        output_path = Path(output_path)
        
        # Build XMLs
        assessment_xml = self.build_assessment_xml()
        manifest_xml, qti_id = self.build_manifest_xml()
        meta_xml = self.build_meta_xml(sum(q['spec'].points for q in self.questions))
        
        # Create ZIP
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
            # imsmanifest.xml at root
            z.writestr('imsmanifest.xml', manifest_xml)
            
            # Assessment files in subdirectory
            z.writestr(f'{qti_id}/{qti_id}.xml', assessment_xml)
            z.writestr(f'{qti_id}/assessment_meta.xml', meta_xml)
        
        print(f"[OK] Created QTI ZIP: {output_path}")
        print(f"     Size: {output_path.stat().st_size:,} bytes")
        print(f"     Questions: {len(self.questions)}")
        print(f"     Total Points: {sum(q['spec'].points for q in self.questions)}")


def parse_quiz_file(filepath: str) -> tuple:
    """Parse quiz file and extract questions."""
    filepath = Path(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by --- separator
    blocks = content.split('\n---\n')
    
    # First block is metadata
    metadata_lines = blocks[0].split('\n')
    title = ""
    total_points = 0
    keep_points = False
    
    for line in metadata_lines:
        if line.startswith('Title:'):
            title = line[6:].strip()
        elif line.startswith('TotalPoints:'):
            total_points = float(line[12:].strip())
        elif line.startswith('KeepPoints:'):
            keep_points = line[11:].strip().lower() == 'true'
    
    # Parse questions
    questions = []
    for i, block in enumerate(blocks[1:], 1):
        if not block.strip():
            continue
        
        lines = block.split('\n')
        
        # Extract Type and Points
        q_type = None
        points = None
        
        for line in lines:
            if line.startswith('Type:'):
                q_type = line[5:].strip()
            elif line.startswith('Points:'):
                points = float(line[7:].strip())
        
        if q_type == "NUMERICAL" and points:
            spec = NumericalParser.parse(lines, points)
            questions.append({
                'spec': spec,
                'item_id': f"item_{i:03d}",
                'num': i
            })
    
    return title, questions


def main():
    print("=" * 80)
    print("QTI ZIP GENERATOR - NUMERICAL EDGE CASES")
    print("=" * 80)
    print()
    
    # Parse quiz file
    quiz_file = Path(__file__).parent / "numerical_realworld_edgecases.txt"
    
    if not quiz_file.exists():
        print(f"[FAIL] Quiz file not found: {quiz_file}")
        return False
    
    print(f"[OK] Reading: {quiz_file}")
    
    try:
        title, questions = parse_quiz_file(quiz_file)
    except Exception as e:
        print(f"[FAIL] Failed to parse quiz file: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"[OK] Parsed {len(questions)} NUMERICAL questions")
    print()
    
    # Build QTI assessment
    builder = QTIQuizBuilder(title)
    for q in questions:
        builder.add_question(q['spec'], q['item_id'], q['num'])
    
    # Export ZIP
    output_path = Path(__file__).parent / "numerical_edgecases_export.zip"
    
    try:
        builder.export_zip(str(output_path))
    except Exception as e:
        print(f"[FAIL] Failed to create ZIP: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 80)
    print("[OK] EXPORT COMPLETE")
    print("=" * 80)
    print()
    print("You can now import this ZIP into Canvas New Quizzes:")
    print(f"  1. Create a new Quiz")
    print(f"  2. Click ... (three dots)")
    print(f"  3. Select 'Import Content'")
    print(f"  4. Upload: {output_path.name}")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
