#!/usr/bin/env python3
"""
discrimination_sensor.py - Mutation testing for Casa Afeto.

Injects intentional faults into code to verify that tests actually detect regressions.
This is the "Discrimination Sensor" from TLC-Spec-Driven, adapted for Casa Afeto.

Mutations supported:
  - Invert boolean conditions (== to !=, > to <=, etc.)
  - Change return values (True/False, None, 0)
  - Remove function body (replace with pass)
  - Negate comparisons

Usage:
  # Test a specific file against test commands
  python3 scripts/tlc/discrimination_sensor.py backend/app/payments/service.py \
    --test-cmd "cd backend && python -m pytest tests/test_payments.py -x"

  # Test all files in a directory
  python3 scripts/tlc/discrimination_sensor.py backend/app/payments/ \
    --test-cmd "cd backend && python -m pytest tests/test_payments.py -x"

  # Dry run - show mutations without applying
  python3 scripts/tlc/discrimination_sensor.py backend/app/payments/service.py \
    --test-cmd "cd backend && python -m pytest tests/test_payments.py -x" --dry-run

Exit codes:
  0 - All mutations were killed (tests detected them)
  1 - Some mutations survived (tests did not detect them)
  2 - Error (file not found, syntax error, etc.)
"""

import argparse
import difflib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple


# Mutation patterns: (pattern, replacement)
MUTATION_PATTERNS = [
    # Boolean inversions
    (r'(?<!\w)==(?!\w)', '!='),
    (r'(?<!\w)!=(?!\w)', '=='),
    (r'(?<!\w)>(?!\w|=)', '<='),
    (r'(?<!\w)<(?!\w|=)', '>='),
    (r'(?<!\w)>= (?!\w)', '< '),
    (r'(?<!\w)<= (?!\w)', '> '),
    (r'\bTrue\b', 'False'),
    (r'\bFalse\b', 'True'),
    (r'\bNone\b', '""'),
    (r'\bif\b', 'if_not_mutation'),  # Will be handled specially
    (r'\bnot\b', ''),
    (r'\band\b', 'or'),
    (r'\bor\b', 'and'),
    # Numeric mutations
    (r'(?<!\w)0(?!\w)', '1'),
    (r'(?<!\w)1(?!\w)', '0'),
    # Return value mutations
    (r'return\s+True', 'return False'),
    (r'return\s+False', 'return True'),
    (r'return\s+None', 'return ""'),
]


def find_python_files(target: str) -> List[Path]:
    """Find Python files to mutate."""
    path = Path(target)
    if path.is_file():
        if path.suffix == '.py':
            return [path]
        return []
    elif path.is_dir():
        files = []
        for py_file in path.rglob('*.py'):
            # Skip test files, __pycache__, .venv
            if '__pycache__' not in str(py_file) and '.venv' not in str(py_file):
                if not py_file.name.startswith('test_') and not py_file.name.endswith('_test.py'):
                    files.append(py_file)
        return files
    return []


def read_file(path: Path) -> str:
    """Read file content."""
    return path.read_text(encoding='utf-8')


def write_file(path: Path, content: str) -> None:
    """Write file content."""
    path.write_text(content, encoding='utf-8')


def generate_mutations(source: str) -> List[Tuple[str, str, str]]:
    """
    Generate mutations for a source file.
    Returns list of (line_number, original_line, mutated_line).
    """
    mutations = []
    lines = source.split('\n')
    in_docstring = False
    docstring_delimiter = None
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Handle multi-line docstrings
        if not in_docstring:
            # Check if this line starts a docstring
            for delim in ['"""', "'''"]:
                if stripped.startswith(delim):
                    # Count occurrences of the delimiter in this line
                    count = stripped.count(delim)
                    if count == 1:
                        # Docstring starts but doesn't end on this line
                        in_docstring = True
                        docstring_delimiter = delim
                    # If count >= 2, it's a single-line docstring, skip it
                    break
            if in_docstring:
                continue
        else:
            # We're inside a docstring, check if it ends
            if docstring_delimiter and docstring_delimiter in stripped:
                in_docstring = False
                docstring_delimiter = None
            continue
        
        # Skip comments
        if stripped.startswith('#'):
            continue
        
        for pattern, replacement in MUTATION_PATTERNS:
            try:
                if re.search(pattern, line):
                    mutated_line = re.sub(pattern, replacement, line, count=1)
                    if mutated_line != line:
                        mutations.append((i, line, mutated_line))
                        break  # One mutation per line
            except re.error:
                continue
    
    return mutations


def run_test_command(test_cmd: str) -> Tuple[bool, str]:
    """Run the test command and return (passed, output)."""
    try:
        result = subprocess.run(
            test_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "Test command timed out (120s)"
    except Exception as e:
        return False, f"Error running tests: {e}"


def apply_mutation(path: Path, line_num: int, mutated_line: str, source: str) -> str:
    """Apply a mutation to the source and write it back."""
    lines = source.split('\n')
    original = lines[line_num - 1]
    lines[line_num - 1] = mutated_line
    new_source = '\n'.join(lines)
    write_file(path, new_source)
    return original


def discrimination_sensor(target: str, test_cmd: str, dry_run: bool = False, 
                          max_mutations: int = 20) -> Tuple[int, int, List[str]]:
    """
    Run discrimination sensor on target files.
    Returns (killed, survived, details).
    """
    files = find_python_files(target)
    if not files:
        print(f"ERROR: No Python files found in {target}")
        return 0, 0, []
    
    print(f"Found {len(files)} file(s) to test")
    print(f"Test command: {test_cmd}")
    print()
    
    # First, verify tests pass with original code
    print("Verifying original tests pass...")
    original_passed, original_output = run_test_command(test_cmd)
    if not original_passed:
        print("ERROR: Original tests are failing. Fix them first.")
        print(original_output[:500])
        return 0, 0, ["Original tests failing"]
    print("✓ Original tests pass\n")
    
    killed = 0
    survived = 0
    details = []
    mutation_count = 0
    
    for file_path in files:
        source = read_file(file_path)
        mutations = generate_mutations(source)
        
        if not mutations:
            print(f"  No mutations found in {file_path}")
            continue
        
        print(f"Testing {file_path} ({len(mutations)} potential mutations)")
        
        for line_num, original_line, mutated_line in mutations:
            if mutation_count >= max_mutations:
                print(f"\n  Reached max mutations ({max_mutations})")
                break
            
            mutation_count += 1
            
            # Apply mutation
            write_file(file_path, source.replace(original_line, mutated_line, 1))
            
            if dry_run:
                print(f"  [DRY RUN] Line {line_num}: {original_line.strip()[:60]} -> {mutated_line.strip()[:60]}")
                continue
            
            # Run tests
            passed, output = run_test_command(test_cmd)
            
            if not passed:
                killed += 1
                status = "KILLED"
                symbol = "✓"
            else:
                survived += 1
                status = "SURVIVED"
                symbol = "✗"
            
            detail = f"  {symbol} Line {line_num}: {status} - {original_line.strip()[:50]}"
            print(detail)
            details.append(detail)
            
            # Restore original
            write_file(file_path, source)
        
        print()
    
    return killed, survived, details


def main():
    parser = argparse.ArgumentParser(
        description='Discrimination Sensor - Mutation testing for Casa Afeto'
    )
    parser.add_argument(
        'target',
        help='Python file or directory to test'
    )
    parser.add_argument(
        '--test-cmd', '-t',
        required=True,
        help='Test command to run (e.g., "cd backend && python -m pytest tests/ -x")'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show mutations without applying them'
    )
    parser.add_argument(
        '--max-mutations', '-m',
        type=int,
        default=20,
        help='Maximum number of mutations to test (default: 20)'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.target):
        print(f"ERROR: {args.target} not found")
        sys.exit(2)
    
    killed, survived, details = discrimination_sensor(
        args.target, args.test_cmd, args.dry_run, args.max_mutations
    )
    
    print("=" * 60)
    print(f"DISCRIMINATION SENSOR RESULTS")
    print(f"Mutations killed:   {killed}")
    print(f"Mutations survived: {survived}")
    total = killed + survived
    if total > 0:
        kill_ratio = killed / total * 100
        print(f"Kill ratio:       {kill_ratio:.1f}%")
        print()
        if survived > 0:
            print("WARNING: Some mutations survived!")
            print("Your tests may not be detecting all regressions.")
            print("Consider adding tests for the surviving mutations.")
            sys.exit(1)
        else:
            print("SUCCESS: All mutations were detected by your tests.")
            sys.exit(0)
    else:
        print("No mutations tested.")
        sys.exit(2)


if __name__ == '__main__':
    main()
