# Agent-Factory

A repository for creating and managing agent skills. This project uses the Anthropic skill-creator to help design, build, package, and iterate on reusable skills for Claude agents.

## Overview

Agent-Factory is your workspace for developing custom skills that can be used across multiple projects. Whenever you have an idea for a new skill, you can come back to this repository to create it using the skill-creator guidance system.

## Getting Started

### Creating a New Skill

The skill-creator provides a guided 6-step process for creating modular skill packages:

1. **Understand concrete examples** - Define how your skill will be used
2. **Plan reusable contents** - Decide what scripts, references, and assets you need
3. **Initialize** - Create the skill structure using `init_skill.py`
4. **Edit** - Implement your skill resources and documentation
5. **Package** - Prepare your skill for use with `package_skill.py`
6. **Iterate** - Refine based on real-world usage

### Utility Scripts

The following scripts are available in `skill-creator/scripts/`:

- **`init_skill.py`** - Initialize a new skill with a given name
  ```bash
  python skill-creator/scripts/init_skill.py <skill-name> --path <output-directory>
  ```

- **`package_skill.py`** - Package a completed skill for distribution
  ```bash
  python skill-creator/scripts/package_skill.py <path/to/skill-folder>
  ```

- **`quick_validate.py`** - Validate your skill structure and configuration

### Skill Structure

Each skill you create should contain:

- **`SKILL.md`** (required) - YAML frontmatter plus markdown instructions defining what the skill does
- **`scripts/`** (optional) - Executable code for deterministic tasks
- **`references/`** (optional) - Documentation and reference materials
- **`assets/`** (optional) - Templates, icons, or output files

## Documentation

See `skill-creator/SKILL.md` for complete documentation on the skill-creator guidance system, including detailed instructions on skill design and best practices.

## License

This project includes the skill-creator from Anthropic's Skills repository, which is licensed under the Apache License 2.0. See `skill-creator/LICENSE.txt` for details.

## Resources

- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- [Skill-Creator Documentation](./skill-creator/SKILL.md)
- [Workflow Reference](./skill-creator/references/workflows.md)
- [Output Patterns Reference](./skill-creator/references/output-patterns.md)
