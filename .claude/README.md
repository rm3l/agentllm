# B4Racing Monorepo - Claude Configuration

## Overview

This is the **workspace root** `.claude/` directory for the B4Racing monorepo.

- Workspace-level agents and commands apply to **all packages**
- Package-specific `.claude/` directories can override these settings
- When working in a package, settings cascade: workspace → package

## Agents

- **analyzer-creator**: Create telemetry analyzers following TDD
- **template-creator**: Create Jinja2 report templates
- **integration-test-creator**: Create integration tests
- **python-pro**: Python 3.12+ expertise and optimization

## Commands

- **/plan**: Plan features and tasks
- **/implement**: Execute implementations with tracking

## Package Development

When spawning Claude sessions in package directories:
1. Package `.claude/` inherits from workspace root
2. Package can override with its own agents/commands
3. Use nox from monorepo root for multi-package tasks
4. Use direct commands (pytest, ruff) in package directories

## Architecture

See `docs/architecture/README.md` for system overview.
