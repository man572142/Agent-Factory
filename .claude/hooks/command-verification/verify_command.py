#!/usr/bin/env python3
"""
Command Verifier - Checks commands against the registry and determines execution permissions.

This script:
- Loads the command registry
- Parses command lines into individual commands
- Checks each command against the registry
- Reports risk levels and permissions
- Determines if execution can proceed automatically

Usage:
    python verify_command.py <command_line>
    python verify_command.py --json <command_line>
    python verify_command.py --registry <path> <command_line>
"""

import sys
import os
import json
from typing import Dict, Any, List, Optional
from parse_command import parse_command_line

# Risk level colors for terminal output
COLORS = {
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "reset": "\033[0m",
    "bold": "\033[1m",
}


def load_registry(registry_path: Optional[str] = None) -> Dict[str, Any]:
    """Load the command registry from JSON file."""
    if registry_path is None:
        # Default to the assets directory relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        registry_path = os.path.join(script_dir, "command_registry.json")

    try:
        with open(registry_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"commands": {}}
    except json.JSONDecodeError:
        return {"commands": {}}


def get_command_info(command_name: str, registry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get information about a command from the registry (simple base-name lookup)."""
    commands = registry.get("commands", {})
    return commands.get(command_name)


def get_command_info_hierarchical(candidates: List[str], tokens: List[str],
                                   registry: Dict[str, Any]) -> tuple:
    """
    Try candidate keys most-specific-first and return (matched_key, info).
    No fallback for subcommand-aware commands: if the registry has entries
    like "git push", then bare "git" won't catch-all for "git <anything>".
    Commands without subcommand entries (e.g., "python") still match normally.
    Returns (None, None) if no match found.
    """
    commands = registry.get("commands", {})
    base = tokens[0] if tokens else ""
    has_subcommand_entries = any(
        k.startswith(base + " ") for k in commands
    ) if base else False

    for candidate in candidates:
        # Skip base-only fallback when subcommand entries exist
        if (has_subcommand_entries
                and " " not in candidate
                and len(tokens) > 1):
            continue
        if candidate in commands:
            return candidate, commands[candidate]
    return None, None


def verify_commands(command_line: str, registry_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify all commands in a command line against the registry.

    Returns a result object containing:
    - all_known: whether all commands are in the registry
    - can_auto_execute: whether all commands can be executed without asking
    - commands: detailed info about each command
    - unknown_commands: list of commands not in registry
    - needs_permission: list of commands that require user permission
    """
    registry = load_registry(registry_path)
    parsed = parse_command_line(command_line)

    result = {
        "original_command": command_line,
        "all_known": True,
        "can_auto_execute": True,
        "highest_risk": "low",
        "commands": [],
        "unknown_commands": [],
        "needs_permission": [],
    }

    risk_priority = {"low": 0, "medium": 1, "high": 2, "critical": 3}

    for cmd in parsed["commands"]:
        cmd_name = cmd["command_name"]
        parts = cmd.get("command_parts", {})
        candidates = parts.get("command_key_candidates", [cmd_name])

        # Hierarchical lookup - most specific first
        tokens = parts.get("tokens", [])
        matched_key, info = get_command_info_hierarchical(candidates, tokens, registry)

        if info is None:
            result["all_known"] = False
            result["can_auto_execute"] = False
            result["unknown_commands"].append(cmd_name)
            result["commands"].append({
                "command_name": cmd_name,
                "full_command": cmd["full_command"],
                "known": False,
                "info": None,
                "matched_key": None,
            })
        else:
            cmd_result = {
                "command_name": cmd_name,
                "full_command": cmd["full_command"],
                "known": True,
                "info": info,
                "matched_key": matched_key,
            }
            result["commands"].append(cmd_result)

            # Check permission
            if info.get("permission") == "AlwaysAsk":
                result["can_auto_execute"] = False
                result["needs_permission"].append(matched_key or cmd_name)

            # Track highest risk
            cmd_risk = info.get("risk", {}).get("level", "low")
            if risk_priority.get(cmd_risk, 0) > risk_priority.get(result["highest_risk"], 0):
                result["highest_risk"] = cmd_risk

    return result


def format_output(result: Dict[str, Any], use_color: bool = True) -> str:
    """Format the verification result for terminal output."""
    lines = []

    c = COLORS if use_color else {k: "" for k in COLORS}

    lines.append(f"{c['bold']}Command Verification Report{c['reset']}")
    lines.append("=" * 50)
    lines.append(f"Command: {result['original_command']}")
    lines.append("")

    # Summary
    if result["can_auto_execute"]:
        lines.append(f"{c['green']}[ALLOW]{c['reset']} All commands can be executed automatically")
    elif result["unknown_commands"]:
        lines.append(f"{c['yellow']}[UNKNOWN]{c['reset']} Some commands are not in the registry")
    else:
        lines.append(f"{c['yellow']}[ASK]{c['reset']} User permission required for some commands")

    lines.append("")
    lines.append(f"Highest Risk Level: {c[get_risk_color(result['highest_risk'])]}{result['highest_risk'].upper()}{c['reset']}")
    lines.append("")

    # Command details
    lines.append("Commands:")
    lines.append("-" * 50)

    for cmd in result["commands"]:
        cmd_name = cmd["command_name"]
        full_cmd = cmd["full_command"]

        if cmd["known"]:
            info = cmd["info"]
            risk = info.get("risk", {})
            risk_level = risk.get("level", "unknown")
            risk_color = risk.get("color", "yellow")
            permission = info.get("permission", "AlwaysAsk")
            description = info.get("description", "No description available")
            matched_key = cmd.get("matched_key")

            color = c.get(risk_color, c["yellow"])
            lines.append(f"  {c['bold']}{cmd_name}{c['reset']}")
            if matched_key and matched_key != cmd_name:
                lines.append(f"    Matched: {matched_key}")
            lines.append(f"    Full: {full_cmd}")
            lines.append(f"    Description: {description}")
            lines.append(f"    Permission: {permission}")
            lines.append(f"    Risk: {color}{risk_level.upper()}{c['reset']} - {risk.get('reason', 'N/A')}")
        else:
            lines.append(f"  {c['bold']}{cmd_name}{c['reset']} {c['yellow']}[UNKNOWN]{c['reset']}")
            lines.append(f"    Full: {full_cmd}")
            lines.append(f"    Status: Not in registry - needs to be added")

        lines.append("")

    # Actions needed
    if result["unknown_commands"]:
        lines.append("Action Required:")
        lines.append(f"  The following commands need to be added to the registry:")
        for cmd in result["unknown_commands"]:
            lines.append(f"    - {cmd}")
        lines.append("")

    if result["needs_permission"]:
        lines.append("Permission Required:")
        lines.append(f"  The following commands require user approval:")
        for cmd in result["needs_permission"]:
            lines.append(f"    - {cmd}")

    return "\n".join(lines)


def get_risk_color(level: str) -> str:
    """Get the color key for a risk level."""
    color_map = {
        "low": "green",
        "medium": "yellow",
        "high": "red",
        "critical": "red",
    }
    return color_map.get(level, "yellow")


def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_command.py [--json] [--registry <path>] <command_line>")
        sys.exit(1)

    json_output = False
    registry_path = None
    command_line = None

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--json":
            json_output = True
        elif sys.argv[i] == "--registry":
            i += 1
            if i < len(sys.argv):
                registry_path = sys.argv[i]
        else:
            command_line = sys.argv[i]
        i += 1

    if command_line is None:
        print("Error: Missing command line argument")
        sys.exit(1)

    result = verify_commands(command_line, registry_path)

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        # Check if we're in a terminal that supports colors
        use_color = sys.stdout.isatty()
        print(format_output(result, use_color))


if __name__ == "__main__":
    main()
