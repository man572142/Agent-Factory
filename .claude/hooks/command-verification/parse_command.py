#!/usr/bin/env python3
"""
Command Parser - Splits command lines into individual commands and extracts command names.

This script parses shell command lines and identifies:
- Individual commands (split by &&, ||, ;, |)
- The base command name (first word of each command)
- Command arguments

Usage:
    python parse_command.py "command_line"
    python parse_command.py --json "command_line"
"""

import sys
import re
import json
import shlex
from typing import List, Dict, Any


def split_command_line(command_line: str) -> List[str]:
    """
    Split a command line into individual commands.
    Handles &&, ||, ;, and | operators while respecting quotes.
    """
    commands = []
    current = []
    i = 0
    in_single_quote = False
    in_double_quote = False
    escape_next = False

    while i < len(command_line):
        char = command_line[i]

        if escape_next:
            current.append(char)
            escape_next = False
            i += 1
            continue

        if char == '\\' and not in_single_quote:
            escape_next = True
            current.append(char)
            i += 1
            continue

        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current.append(char)
            i += 1
            continue

        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(char)
            i += 1
            continue

        if not in_single_quote and not in_double_quote:
            # Check for && operator
            if command_line[i:i+2] == '&&':
                if current:
                    cmd = ''.join(current).strip()
                    if cmd:
                        commands.append(cmd)
                    current = []
                i += 2
                continue

            # Check for || operator
            if command_line[i:i+2] == '||':
                if current:
                    cmd = ''.join(current).strip()
                    if cmd:
                        commands.append(cmd)
                    current = []
                i += 2
                continue

            # Check for ; operator
            if char == ';':
                if current:
                    cmd = ''.join(current).strip()
                    if cmd:
                        commands.append(cmd)
                    current = []
                i += 1
                continue

            # Check for | operator (but not ||)
            if char == '|' and (i + 1 >= len(command_line) or command_line[i+1] != '|'):
                if current:
                    cmd = ''.join(current).strip()
                    if cmd:
                        commands.append(cmd)
                    current = []
                i += 1
                continue

        current.append(char)
        i += 1

    # Add final command
    if current:
        cmd = ''.join(current).strip()
        if cmd:
            commands.append(cmd)

    return commands


def _strip_prefixes(command: str) -> str:
    """Strip env var assignments from the start of a command string."""
    command = command.strip()
    while True:
        match = re.match(r'^[A-Za-z_][A-Za-z0-9_]*=\S*\s+', command)
        if match:
            command = command[match.end():]
        else:
            break
    return command


def _tokenize(command: str) -> List[str]:
    """Tokenize a command string, handling quotes gracefully."""
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def _skip_wrappers(parts: List[str]) -> List[str]:
    """
    Skip sudo, env, and other wrapper commands to get to the real command + args.
    Returns the parts starting from the actual command.
    """
    if not parts:
        return parts

    cmd = parts[0]

    # Handle sudo - skip sudo and its flags
    if cmd == 'sudo':
        i = 1
        while i < len(parts):
            if parts[i].startswith('-'):
                if parts[i] in ['-u', '-g', '-C', '-H', '-P']:
                    i += 2
                else:
                    i += 1
            else:
                return parts[i:]
        return ['sudo']

    # Handle common wrappers
    wrappers = ['time', 'nice', 'nohup', 'env', 'xargs']
    if cmd in wrappers and len(parts) > 1:
        i = 1
        while i < len(parts) and parts[i].startswith('-'):
            i += 1
        if i < len(parts):
            return parts[i:]

    return parts


def extract_command_name(command: str) -> str:
    """
    Extract the base command name from a command string.
    Handles environment variables, sudo, and other prefixes.
    """
    command = _strip_prefixes(command)

    # Handle subshell commands
    if command.startswith('(') or command.startswith('{'):
        return 'subshell'

    # Handle command substitution
    if command.startswith('$'):
        return 'substitution'

    parts = _tokenize(command)
    if not parts:
        return ''

    real_parts = _skip_wrappers(parts)
    return real_parts[0] if real_parts else ''


def extract_command_parts(command: str) -> Dict[str, Any]:
    """
    Extract detailed command parts including subcommands and flags.

    Returns a dict with:
    - base: the base command name (e.g., "git")
    - tokens: all tokens after wrappers (e.g., ["git", "push", "--force", "origin"])
    - flags: all flag tokens (starting with -) (e.g., ["--force"])
    - command_key_candidates: list of registry keys to try, most specific first
      (e.g., ["git push --force origin", "git push --force", "git push", "git"])
    """
    command = _strip_prefixes(command)

    # Handle special command types
    if command.startswith('(') or command.startswith('{'):
        return {"base": "subshell", "tokens": ["subshell"], "flags": [],
                "command_key_candidates": ["subshell"]}
    if command.startswith('$'):
        return {"base": "substitution", "tokens": ["substitution"], "flags": [],
                "command_key_candidates": ["substitution"]}

    parts = _tokenize(command)
    if not parts:
        return {"base": "", "tokens": [], "flags": [], "command_key_candidates": []}

    real_parts = _skip_wrappers(parts)
    if not real_parts:
        return {"base": "", "tokens": [], "flags": [], "command_key_candidates": []}

    base = real_parts[0]
    flags = [t for t in real_parts[1:] if t.startswith('-')]

    # Build candidate keys from most specific to least specific
    # e.g., for ["git", "push", "--force", "origin"]:
    # ["git push --force origin", "git push --force", "git push", "git"]
    candidates = []
    for length in range(len(real_parts), 0, -1):
        candidate = " ".join(real_parts[:length])
        candidates.append(candidate)

    # Also build candidates from subcommand tokens only (flags stripped).
    # This handles cases like "git -C path status" where flags between the
    # base command and subcommand prevent matching "git status".
    # A subcommand token: doesn't start with '-', is a simple word (no path
    # separators or dots), comes after the base command.
    subcommand_tokens = [base]
    i = 1
    while i < len(real_parts):
        token = real_parts[i]
        if token.startswith('-'):
            # Skip flag; if it's a short flag (-X), also skip the next token
            # as it's likely the flag's argument (e.g., -C /path)
            if len(token) == 2 and i + 1 < len(real_parts):
                i += 2
            else:
                i += 1
        else:
            subcommand_tokens.append(token)
            i += 1

    if subcommand_tokens != real_parts:
        for length in range(len(subcommand_tokens), 0, -1):
            candidate = " ".join(subcommand_tokens[:length])
            if candidate not in candidates:
                candidates.append(candidate)

    return {
        "base": base,
        "tokens": real_parts,
        "flags": flags,
        "command_key_candidates": candidates,
    }


def parse_command_line(command_line: str) -> Dict[str, Any]:
    """
    Parse a complete command line and return structured information.
    """
    commands = split_command_line(command_line)

    parsed = {
        "original": command_line,
        "command_count": len(commands),
        "commands": []
    }

    for cmd in commands:
        parts = extract_command_parts(cmd)
        cmd_info = {
            "full_command": cmd,
            "command_name": parts["base"],
            "command_parts": parts,
        }
        parsed["commands"].append(cmd_info)

    return parsed


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_command.py [--json] <command_line>")
        print("  --json    Output in JSON format")
        sys.exit(1)

    json_output = False
    command_line = ""

    if sys.argv[1] == '--json':
        json_output = True
        if len(sys.argv) < 3:
            print("Error: Missing command line argument")
            sys.exit(1)
        command_line = sys.argv[2]
    else:
        command_line = sys.argv[1]

    result = parse_command_line(command_line)

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"Command Line: {result['original']}")
        print(f"Found {result['command_count']} command(s):")
        print()
        for i, cmd in enumerate(result['commands'], 1):
            print(f"  {i}. Command: {cmd['command_name']}")
            print(f"     Full: {cmd['full_command']}")
            print()


if __name__ == "__main__":
    main()
