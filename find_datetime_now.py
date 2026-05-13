#!/usr/bin/env python3
"""Find all datetime.now() calls in the project."""

import os
import re
from pathlib import Path

def find_datetime_now_calls(root_dir):
    """Find all datetime.now() calls in Python files."""
    results = []
    pattern = re.compile(r'datetime\.now\(\)')
    
    for root, dirs, files in os.walk(root_dir):
        # Skip virtual environments and cache directories
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', '.kiro']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line_num, line in enumerate(lines, 1):
                            if pattern.search(line):
                                # Get context (previous and next line)
                                prev_line = lines[line_num-2].strip() if line_num > 1 else ""
                                next_line = lines[line_num].strip() if line_num < len(lines) else ""
                                
                                results.append({
                                    'file': filepath.replace(root_dir, '').lstrip('\\'),
                                    'line_num': line_num,
                                    'code': line.strip(),
                                    'prev': prev_line,
                                    'next': next_line
                                })
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return results

if __name__ == "__main__":
    root = r'd:\Povaly Group\Applications\pova-bot\src'
    results = find_datetime_now_calls(root)
    
    print(f"Found {len(results)} datetime.now() calls:\n")
    print("=" * 100)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['file']}:{result['line_num']}")
        print(f"   Code: {result['code']}")
        if result['prev']:
            print(f"   Prev: {result['prev']}")
        if result['next']:
            print(f"   Next: {result['next']}")
    
    print("\n" + "=" * 100)
    print(f"\nTotal: {len(results)} datetime.now() calls found")
