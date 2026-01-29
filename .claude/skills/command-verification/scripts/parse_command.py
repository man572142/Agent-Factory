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


def extract_command_name(command: str) -> str:
    """
    Extract the base command name from a command string.
    Handles environment variables, sudo, and other prefixes.
    """
    command = command.strip()

    # Skip environment variable assignments at the start
    while True:
        match = re.match(r'^[A-Za-z_][A-Za-z0-9_]*=\S*\s+', command)
        if match:
            command = command[match.end():]
        else:
            break

    # Handle subshell commands
    if command.startswith('(') or command.startswith('{'):
        return 'subshell'

    # Handle command substitution
    if command.startswith('$'):
        return 'substitution'

    try:
        parts = shlex.split(command)
    except ValueError:
        # If shlex fails, fall back to simple split
        parts = command.split()

    if not parts:
        return ''

    cmd = parts[0]

    # Handle sudo - return the actual command after sudo
    if cmd == 'sudo':
        # Skip sudo flags
        i = 1
        while i < len(parts):
            if parts[i].startswith('-'):
                # Skip flag and its argument if needed
                if parts[i] in ['-u', '-g', '-C', '-H', '-P']:
                    i += 2
                else:
                    i += 1
            else:
                return parts[i] if i < len(parts) else 'sudo'
        return 'sudo'

    # Handle common wrappers
    wrappers = ['time', 'nice', 'nohup', 'env', 'xargs']
    if cmd in wrappers and len(parts) > 1:
        # Find the actual command
        i = 1
        while i < len(parts) and parts[i].startswith('-'):
            i += 1
        if i < len(parts):
            return parts[i]

    return cmd


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
        cmd_info = {
            "full_command": cmd,
            "command_name": extract_command_name(cmd),
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
