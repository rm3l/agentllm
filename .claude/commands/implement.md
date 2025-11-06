---
description: Execute and track implementation from plan
argument-hint: <plan-file>
model: sonnet
---

# Implementation Command for B4Racing

This command handles executing and tracking implementations across one or multiple sessions.

## Usage

```bash
/implement <plan-file>
```

Example:
```bash
/implement specs/plans/my-feature.md
```

## Overview

The `/implement` command takes an approved plan document and executes the implementation while tracking progress in a separate implementation log file. This allows implementations to span multiple sessions while maintaining continuity.

## Implementation Tracking

For each plan file `specs/plans/<name>.md`, the command maintains an implementation log at `specs/plans/<name>-implementation.md` that tracks:
- Implementation sessions (date/time started)
- Progress made in each session
- Decisions and changes made
- Issues encountered and how they were resolved
- Current status and next steps

## Process

### 1. Initialization

When invoked, the command:
1. **Locates the plan file** at the specified path
2. **Checks for existing implementation log** (`<plan-name>-implementation.md`)
3. **Reviews architecture documentation**:
   - Start with `docs/architecture/README.md` for system overview
   - Check `specs/plans/monorepo-index.md` for implementation status
   - Review `docs/guides/README.md` for relevant guides
   - Consult package `CLAUDE.md` files for package-specific patterns
4. **Reviews the plan** to understand requirements and approach
5. **Reviews existing implementation log** (if resuming) to understand what's been done
6. **Determines current state** and what work remains

### 2. Session Start

At the beginning of each implementation session:
1. **Create/Update implementation log** with new session entry:
   - Session number and timestamp
   - Summary of what will be tackled in this session
   - Reference to the plan being implemented
2. **Set up task tracking** using TodoWrite for the session's work items
3. **Confirm scope** with user if resuming a previous implementation

### 3. Implementation Execution

During implementation:
1. **Follow the planned approach** from the plan document
2. **Track progress** using TodoWrite tool for task management
3. **Document decisions** as they are made
4. **Handle unexpected issues**:
   - Document the issue in the implementation log
   - Propose solutions to the user
   - Update approach if needed
5. **Maintain communication** with user throughout
6. **Test incrementally** as features are built
7. **Update implementation log** with progress notes

### 4. Session End

At the end of each session (or when pausing):
1. **Update implementation log** with:
   - What was completed in this session
   - What remains to be done
   - Any blockers or issues
   - Next steps for continuation
   - Testing results
2. **Summarize progress** to the user
3. **Identify if more sessions needed** or if implementation is complete

### 5. Completion

When implementation is fully complete:
1. **Final update to implementation log** including:
   - Completion timestamp
   - Summary of all changes made
   - Testing and validation results
   - Any deviations from original plan
   - Lessons learned
2. **Update architecture documentation** if implementation changed the architecture:
   - **Update `specs/plans/monorepo-index.md`** if new components were added:
     - Add new packages, analyzers, data sources, graphics to tracking
     - Update status from 📋 Planned to ✅ Implemented
     - Update time estimates if needed
   - **Update `docs/architecture/README.md`** if major changes:
     - Update "Current Implementation Status" section
     - Add to package list if new packages created
     - Update architecture diagrams if needed
   - **Update package `CLAUDE.md`** if package changed:
     - Update package-specific instructions
     - Add new commands or workflows
     - Update dependencies list
   - **Update `docs/guides/README.md`** if new guides needed:
     - Add new guide entries
     - Update existing guides if patterns changed
3. **Update the original plan document** with link to implementation log
4. **Provide comprehensive summary** to user including:
   - What was implemented
   - Architecture docs that were updated
   - Testing results
   - Next steps or recommendations

## Implementation Log Format

The implementation log follows this structure:

```markdown
# Implementation Log: <Feature Name>

**Plan Document:** `specs/plans/<name>.md`
**Status:** [In Progress | Completed | Blocked]
**Started:** YYYY-MM-DD
**Last Updated:** YYYY-MM-DD HH:MM

---

## Session 1 - YYYY-MM-DD HH:MM

### Goals
- Goal 1
- Goal 2

### Work Completed
- Change 1 with rationale
- Change 2 with rationale

### Decisions Made
- Decision 1: Why and what alternatives were considered
- Decision 2: Context and reasoning

### Issues Encountered
- Issue 1: How it was resolved
- Issue 2: Current blocker (if any)

### Testing
- Tests added/modified
- Test results

### Next Steps
- What remains to be done
- Dependencies or blockers

---

## Session 2 - YYYY-MM-DD HH:MM

[Same structure as Session 1]

---

## Final Summary

### Total Sessions: N
### Overall Changes:
- Summary of all files changed
- Key features implemented
- Architecture decisions

### Testing Results:
- Test coverage
- Integration test results
- Manual testing performed

### Deviations from Plan:
- Any changes from original plan and why

### Lessons Learned:
- What worked well
- What could be improved
- Recommendations for similar tasks
```

## Best Practices

### For Multi-Session Implementations
- Always review the implementation log before starting a new session
- Keep log entries focused and actionable
- Document why decisions were made, not just what was done
- Update "Next Steps" clearly for future sessions
- If blocked, document what's needed to unblock

### For Code Quality
- Follow TDD principles (tests first, then implementation)
- Run tests frequently and document results
- Follow the project constitution and coding standards
- Keep commits logical and well-documented
- Update documentation as you build

### For Communication
- Keep user informed of progress and blockers
- Ask for input when facing architectural decisions
- Provide clear status updates at session boundaries
- Highlight any changes from the original plan

### For Continuity
- Write implementation log entries as if for a future developer
- Include enough context to resume without re-reading everything
- Link to specific files and line numbers where relevant
- Document environment setup or special requirements

### For Architecture Documentation
- Consult `docs/architecture/README.md` at the start of implementation
- Update documentation when adding new components:
  - New package? Add to `specs/plans/monorepo-index.md` and `docs/architecture/README.md`
  - New analyzer? Add to `specs/plans/monorepo-index.md` tracking
  - New data source? Update package list in architecture docs
  - New protocol? Document in package protocol files
- Keep `specs/plans/monorepo-index.md` accurate (don't leave things as 📋 Planned when they're ✅ Implemented)
- Update package `CLAUDE.md` files when adding package features
- Use architecture docs to guide implementation (follow established patterns)

## Workflow Commands

During implementation, you may need to:
- Run all tests: `nox -s test_all`
- Test specific package: `nox -s "tests(pkg='packages/core')"`
- Format code: `nox -s format`
- Run linting: `nox -s lint`
- Install workspace: `uv sync`
- Run package tests directly: `cd packages/core && pytest tests/ -v`

## Example Usage

### Starting a New Implementation
```bash
# User has completed planning with /plan command
# Plan is at specs/plans/my-feature.md

/implement specs/plans/my-feature.md

# Creates specs/plans/my-feature-implementation.md
# Begins Session 1 implementation
```

### Resuming an Implementation
```bash
# Implementation was partially completed in previous session

/implement specs/plans/my-feature.md

# Reads existing specs/plans/my-feature-implementation.md
# Reviews progress and continues with new session
```

## Success Criteria

Implementation is considered complete when:
- ✅ All planned features are implemented
- ✅ All tests pass (including new tests for new features)
- ✅ Code quality checks pass (lint, format)
- ✅ Code documentation is updated (docstrings, comments)
- ✅ Architecture documentation is updated (if architecture changed):
  - `specs/plans/monorepo-index.md` reflects new components
  - `docs/architecture/README.md` updated for major changes
  - Package `CLAUDE.md` files updated for package changes
  - `docs/guides/README.md` updated if new guides added
- ✅ Implementation log is complete with final summary
- ✅ Original plan document is updated with implementation reference
