---
name: cc-find-notes
description: Search personal study notes in the notes/ directory. Find notes by date, topic, or keywords. Use when users want to find previously recorded notes.
---

# Search Notes

Search personal study notes in the `notes/` directory. Quickly locate your previous notes by date, topic, or keywords.

**Uses cc-find core search capability, but limited to the notes/ directory.**

## Usage

```
/cc-find-notes binary tree           # Search by topic
/cc-find-notes 2026-03               # Search by date (March notes)
/cc-find-notes                        # No arguments, AI asks what you want to find
```

## Search Scope

- All study notes under `notes/` directory
- Typically organized by date (e.g., `2026-03-05-topic.md`)

## Execution Method

Calls `/cc-find` core search logic, but:
1. Limits search scope to notes/ directory
2. Supports date search ("March", "last week", "2026-03", etc.)
3. Sorts results by modification time in descending order (newest first)
4. Shows note summaries (first few lines of content) for quick identification

## Arguments

$ARGUMENTS
