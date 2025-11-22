import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
import sys

p = sys.argv[1] if len(sys.argv) > 1 else 'test_mixed.zip'
with zipfile.ZipFile(p, 'r') as z:
    names = z.namelist()
    print('ZIP entries:', names)
    # find folder GUID and assessment xml
    assess_xml_name = None
    for n in names:
        if n.endswith('.xml') and '/' in n and n.count('/')==1 and not n.endswith('assessment_meta.xml'):
            assess_xml_name = n
            break
    if not assess_xml_name:
        raise SystemExit('assessment xml not found')
    print('Assessment XML:', assess_xml_name)
    data = z.read(assess_xml_name)

# Parse the XML
root = ET.fromstring(data)
items = root.findall('.//{http://www.imsglobal.org/xsd/ims_qtiasiv1p2}item')
print('Item count:', len(items))
# Count by qtimetadata question_type
counts = Counter()
for it in items:
    qtype = None
    for md in it.findall('.//{http://www.imsglobal.org/xsd/ims_qtiasiv1p2}qtimetadatafield'):
        lab = md.find('{http://www.imsglobal.org/xsd/ims_qtiasiv1p2}fieldlabel')
        ent = md.find('{http://www.imsglobal.org/xsd/ims_qtiasiv1p2}fieldentry')
        if lab is not None and ent is not None and (lab.text or '').strip()=='question_type':
            qtype = (ent.text or '').strip()
            break
    counts[qtype] += 1
print('Counts by question_type:', dict(counts))
