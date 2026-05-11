---
name: cc-find-assignments
description: Search assignments and projects in the assignments/ directory. Find specific assignments, project requirements, submission files, etc. Use when users need to find assignment-related content.
argument-hint: "[assignment number or project name] or leave empty for AI to ask"
---

# Search Assignments and Projects

Search all assignments, project requirements, and submission files in the `assignments/` directory.

**Uses cc-find core search capability, but limited to the assignments/ directory.**

## Usage

```
/cc-find-assignments assignment 3      # Find assignment 3
/cc-find-assignments project requirements  # Find project-related files
/cc-find-assignments                    # No arguments, AI asks what you want to find
```

## Search Scope

- Assignment instruction documents
- Project requirements and specifications
- Submitted code and files
- Assignment grades and feedback

## Execution Method

Calls `/cc-find` core search logic, but:
1. Limits search scope to assignments/ directory
2. Supports assignment number search ("assignment 3", "assignment3", "hw3", etc.)
3. Supports project name search
4. Shows assignment due dates and status (if available)

## Arguments

$ARGUMENTS
