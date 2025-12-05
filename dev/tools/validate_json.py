#!/usr/bin/env python3
"""Validate QuizForge JSON file and report any issues."""
import json
import re
import sys

def validate_quiz(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract JSON from tags
    match = re.search(r'<QUIZFORGE_JSON>\s*(.*?)\s*</QUIZFORGE_JSON>', content, re.DOTALL)
    if not match:
        print("ERROR: No <QUIZFORGE_JSON> tags found")
        return False
    
    json_str = match.group(1)
    
    try:
        data = json.loads(json_str)
        print(f"JSON is valid!")
        print(f"  Title: {data.get('title', 'N/A')}")
        print(f"  Version: {data.get('version', 'N/A')}")
        print(f"  Items: {len(data.get('items', []))}")
        print(f"  Rationales: {len(data.get('rationales', []))}")
        
        # Check item types
        types = {}
        for item in data.get('items', []):
            t = item.get('type', 'UNKNOWN')
            types[t] = types.get(t, 0) + 1
        print(f"  Item types: {types}")
        
        # Check for potential issues
        issues = []
        for i, item in enumerate(data.get('items', [])):
            item_id = item.get('id', f'item_{i}')
            item_type = item.get('type', 'UNKNOWN')
            
            # Check for unescaped quotes in prompts
            prompt = item.get('prompt', '')
            if '\"' in prompt and '\\\"' not in json_str:
                issues.append(f"{item_id}: May have unescaped quotes in prompt")
            
            # Check MC/MA have choices
            if item_type in ['MC', 'MA'] and not item.get('choices'):
                issues.append(f"{item_id}: Missing choices for {item_type}")
            
            # Check ORDERING has items
            if item_type == 'ORDERING' and not item.get('items'):
                issues.append(f"{item_id}: Missing items for ORDERING")
        
        if issues:
            print(f"\nPotential issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"\nNo structural issues detected.")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        # Try to find the problematic line
        lines = json_str.split('\n')
        if e.lineno and e.lineno <= len(lines):
            print(f"Near line {e.lineno}: {lines[e.lineno-1][:100]}...")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python validate_json.py <filepath>")
        sys.exit(1)
    validate_quiz(sys.argv[1])
