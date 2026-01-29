#!/usr/bin/env python3
"""
Add Command - Adds a new command to the registry.

This script allows adding new commands to the command registry
with their descriptions, permissions, and risk levels.

Usage:
    python add_command.py <name> <description> <permission> <risk_level> <risk_reason>
    python add_command.py --json '{"name": "...", "description": "...", ...}'
    python add_command.py --interactive

Arguments:
    name: Command name (e.g., "grep", "npm")
    description: What the command does
    permission: "AlwaysAllow" or "AlwaysAsk"
    risk_level: "low", "medium", "high", or "critical"
    risk_reason: Why this risk level was assigned
"""

import sys
import os
import json
from typing import Dict, Any, Optional

REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "assets",
    "command_registry.json"
)

RISK_COLORS = {
    "low": "green",
    "medium": "yellow",
    "high": "red",
    "critical": "red",
}


def load_registry(path: str = REGISTRY_PATH) -> Dict[str, Any]:
    """Load the command registry."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "version": "1.0.0",
            "description": "Registry of known commands",
            "commands": {}
        }


def save_registry(registry: Dict[str, Any], path: str = REGISTRY_PATH) -> bool:
    """Save the command registry."""
    try:
        with open(path, "w") as f:
            json.dump(registry, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving registry: {e}", file=sys.stderr)
        return False


def add_command(
    name: str,
    description: str,
    permission: str,
    risk_level: str,
    risk_reason: str,
    registry_path: str = REGISTRY_PATH
) -> Dict[str, Any]:
    """
    Add a new command to the registry.

    Returns a result object with status and any errors.
    """
    # Validate inputs
    if permission not in ["AlwaysAllow", "AlwaysAsk"]:
        return {
            "success": False,
            "error": f"Invalid permission: {permission}. Must be 'AlwaysAllow' or 'AlwaysAsk'"
        }

    if risk_level not in ["low", "medium", "high", "critical"]:
        return {
            "success": False,
            "error": f"Invalid risk level: {risk_level}. Must be 'low', 'medium', 'high', or 'critical'"
        }

    registry = load_registry(registry_path)

    # Check if command already exists
    if name in registry.get("commands", {}):
        return {
            "success": False,
            "error": f"Command '{name}' already exists in the registry",
            "existing": registry["commands"][name]
        }

    # Create command entry
    command_entry = {
        "name": name,
        "description": description,
        "permission": permission,
        "risk": {
            "level": risk_level,
            "color": RISK_COLORS.get(risk_level, "yellow"),
            "reason": risk_reason
        }
    }

    # Add to registry
    if "commands" not in registry:
        registry["commands"] = {}

    registry["commands"][name] = command_entry

    # Save
    if save_registry(registry, registry_path):
        return {
            "success": True,
            "command": command_entry,
            "message": f"Successfully added '{name}' to the registry"
        }
    else:
        return {
            "success": False,
            "error": "Failed to save registry"
        }


def interactive_add():
    """Interactive mode for adding a command."""
    print("Add New Command to Registry")
    print("=" * 40)
    print()

    name = input("Command name: ").strip()
    if not name:
        print("Error: Command name is required")
        return

    description = input("Description: ").strip()
    if not description:
        print("Error: Description is required")
        return

    print("\nPermission options:")
    print("  1. AlwaysAllow - Can execute without asking")
    print("  2. AlwaysAsk   - Must ask user before executing")
    perm_choice = input("Choose permission (1 or 2): ").strip()
    permission = "AlwaysAllow" if perm_choice == "1" else "AlwaysAsk"

    print("\nRisk level options:")
    print("  1. low      - Safe, read-only or minimal impact")
    print("  2. medium   - Some risk, modifies files or installs packages")
    print("  3. high     - Significant risk, security implications")
    print("  4. critical - Maximum risk, system-level access")
    risk_choice = input("Choose risk level (1-4): ").strip()
    risk_map = {"1": "low", "2": "medium", "3": "high", "4": "critical"}
    risk_level = risk_map.get(risk_choice, "medium")

    risk_reason = input("Risk reason (why this risk level?): ").strip()
    if not risk_reason:
        risk_reason = "No reason provided"

    result = add_command(name, description, permission, risk_level, risk_reason)

    print()
    if result["success"]:
        print(f"Success: {result['message']}")
    else:
        print(f"Error: {result['error']}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--interactive":
        interactive_add()
        return

    if sys.argv[1] == "--json":
        if len(sys.argv) < 3:
            print("Error: Missing JSON argument")
            sys.exit(1)
        try:
            data = json.loads(sys.argv[2])
            result = add_command(
                data["name"],
                data["description"],
                data["permission"],
                data.get("risk_level", data.get("risk", {}).get("level", "medium")),
                data.get("risk_reason", data.get("risk", {}).get("reason", "No reason provided"))
            )
            print(json.dumps(result, indent=2))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing JSON: {e}")
            sys.exit(1)
        return

    if len(sys.argv) < 6:
        print("Error: Missing arguments")
        print("Usage: python add_command.py <name> <description> <permission> <risk_level> <risk_reason>")
        sys.exit(1)

    result = add_command(
        sys.argv[1],  # name
        sys.argv[2],  # description
        sys.argv[3],  # permission
        sys.argv[4],  # risk_level
        sys.argv[5],  # risk_reason
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
