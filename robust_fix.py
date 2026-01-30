import re
import os
import json

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the payload
    match = re.search(r'(<QUIZFORGE_JSON>)(.*?)(</QUIZFORGE_JSON>)', content, re.DOTALL)
    if not match:
        # If no tags, maybe it's raw JSON
        try:
            json.loads(content)
            return # Already valid
        except json.JSONDecodeError:
            # Try to fix raw content
            fixed_payload = fix_json_string_escaping(content)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_payload)
            return

    header, payload, footer = match.groups()
    fixed_payload = fix_json_string_escaping(payload)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(header + fixed_payload + footer)

def fix_json_string_escaping(payload):
    # This is tricky without a real parser, but we can try to find "key": "value"
    # and escape quotes in value.
    
    lines = payload.splitlines()
    fixed_lines = []
    for line in lines:
        # Match "key": "value" patterns
        # We assume keys don't have spaces usually or are known ones
        match = re.match(r'^(\s*"[^"]+":\s*")(.*)(",?\s*)$', line)
        if match:
            prefix, value, suffix = match.groups()
            # Normalize and escape
            temp_value = value.replace('\\"', '"')
            fixed_value = temp_value.replace('"', '\\"')
            fixed_lines.append(prefix + fixed_value + suffix)
        else:
            fixed_lines.append(line)
    
    return "\n".join(fixed_lines)

dropzone = r'C:\githubprojects\QuizForge\DropZone'
for filename in os.listdir(dropzone):
    if filename.endswith(('.txt', '.json', '.md')):
        filepath = os.path.join(dropzone, filename)
        print(f"Fixing {filename}...")
        try:
            fix_file(filepath)
        except Exception as e:
            print(f"  Error fixing {filename}: {e}")

