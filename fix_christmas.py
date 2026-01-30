import re
import os

def fix_content(content):
    # Find all occurrences of "text": "..." where the value has unescaped quotes.
    # We look for "text": " then some content, then ", and then either , or } or whitespace.
    
    def replacer(match):
        prefix = match.group(1)
        value = match.group(2)
        suffix = match.group(3)
        # Escape internal quotes
        fixed_value = value.replace('"', '\\"')
        return f'{prefix}{fixed_value}{suffix}'

    # Regex: "text": " (anything) " (followed by , or } or newline)
    # We use a non-greedy match for the value, but we need to be careful.
    # Actually, we can look for the LAST quote before the comma/brace.
    pattern = r'("text":\s*")(.*?)("(?=\s*[,}]))'
    
    return re.sub(pattern, replacer, content)

filepath = r'C:\githubprojects\QuizForge\DropZone\christmasplayrevision.txt'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

fixed = fix_content(content)
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(fixed)
print("Fixed christmasplayrevision.txt")
