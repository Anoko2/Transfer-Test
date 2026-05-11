---
name: cc-find-communication
description: Search emails, phone records, office hour notes, and communications with professors/TAs in the communication/ directory. Use when users need to find emails or call records.
argument-hint: "[search description or contact name] or leave empty for AI to ask"
---

# Search Communication Records

Search email drafts, phone scripts, office hour records, and all communications with professors/TAs in the `communication/` directory.

**Uses cc-find core search capability, but limited to the communication/ directory.**

## Usage

```
/cc-find-communication professor reply   # Find communications with professor
/cc-find-communication office hours       # Find office hour records
/cc-find-communication                    # No arguments, AI asks what you want to find
```

## Search Scope

- Email drafts and records (`.md`, `.eml`, `.txt`)
- Phone scripts and call records
- Office hour visit records
- All communications with professors/TAs

## Execution Method

Calls `/cc-find` core search logic, but:
1. Limits search scope to communication/ directory
2. Recognizes contact names (professor names, TA names, etc.) for matching
3. Supports time-based search ("recent", "last week", "March", etc.)
4. Shows file modification time to help users quickly locate records

## Arguments

$ARGUMENTS
