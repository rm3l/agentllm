---
description: Review last commit and branch changes
argument-hint: [commit-ref]
model: haiku
---

# Catchup Command

Review current working changes or a specific commit plus all modified/untracked files in the current git branch.

## Purpose

This command helps bring Claude up to speed after a session restart (`/clear`) by:
- **Without arguments**: Review only current working changes (modified and untracked files)
- **With commit-ref**: Analyze a specific commit AND current working changes

## Arguments

- `commit-ref` (optional) - Git commit reference to analyze
  - If omitted: Only analyze current working changes
  - If provided: Analyze the specified commit PLUS current working changes
  - Examples: `HEAD`, `HEAD~1`, `abc123`, `main~2`

## Workflow

**If commit-ref argument is provided ($1):**
1. Use `git log -1 --stat $1` to see the commit message and files changed
2. Use `git show $1` to see the actual changes (diff) in the specified commit

**Always:**
3. Use `git status --porcelain` to find modified and untracked files
4. For modified files (` M`, `M `, `MM` prefix): Use `git diff` to see changes
5. For untracked files (`??` prefix): Read each file to understand new additions
6. Provide summary:
   - **If commit analyzed**: What was accomplished in the commit, then current working changes
   - **If no commit**: Only current working changes (modified and untracked files)

## Usage

Run this command after:
- Starting a new session
- Using `/clear` to reset context
- Switching to a different branch with existing work

**Examples:**
- `/catchup` - Review only current working changes (modified and untracked files)
- `/catchup HEAD` - Review last commit AND current working changes
- `/catchup HEAD~1` - Review previous commit AND current working changes
- `/catchup abc123` - Review specific commit by hash AND current working changes

## Implementation

**If $1 is provided (commit-ref argument):**
1. Run `git log -1 --stat $1` to see the commit summary
2. Run `git show $1` to see the detailed diff of the specified commit

**Always (current working changes):**
3. Run `git status --porcelain` to find modified and untracked files
4. For modified files: Run `git diff` to see the actual changes
5. For untracked files (lines starting with `??`): Read each file to understand new additions

**Summarize:**
- **If commit analyzed**: Two-part summary:
  1. What was accomplished in commit $1 (key changes and intent)
  2. Current working changes (modified and untracked files)
- **If no commit**: Single summary of current working changes only

**Important**: Do not make any modifications - this is a read-only analysis
