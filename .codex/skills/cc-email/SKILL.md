---
name: cc-email
description: Draft, send, or analyze course-related emails. Use for communicating with professors, TAs, or classmates about course matters.
---

# Email Manager

Manage course-related email communication through the `communication/` directory.

## Usage

If no arguments provided, show this help:

```
/cc-email                       - Show this help
/cc-email list                  - List all email records
/cc-email draft <subject>       - Draft a new email
/cc-email analyze <text>        - Analyze a received email
/cc-email reply <subject>       - Draft reply to received email
```

If user provides arguments, interpret their intent:
- `list` → Show all email files from communication/INDEX.md
- `draft <subject>` → Create new email draft
- `analyze` → Analyze a received email (user pastes content)
- `reply <subject>` → Draft a reply
- Free text → Interpret as draft request or email content to analyze

## Actions

### List Emails
1. Read `communication/INDEX.md`
2. Filter for `-email-*` suffix files
3. Display with dates and subjects

### Draft Email
1. Read `COURSE_INFO.md` for recipient info (professor, TA)
2. Get subject and purpose from user
3. Draft professional email
4. Save as `communication/YYYY-MM-DD-<subject>-email-draft.md`
5. Update `communication/INDEX.md`

### Analyze Received Email
1. User provides email content
2. Analyze tone, requests, deadlines, action items
3. Summarize key points
4. Suggest response approach
5. Save analysis as `communication/YYYY-MM-DD-<subject>-email-analysis.md`

### Draft Reply
1. Read original email or analysis
2. Draft appropriate reply
3. Match formality level
4. Save as draft

## Email Draft Format

```markdown
# Email: [Subject]

Draft email to [Recipient] regarding [topic]. Purpose: [brief purpose].

---

## Metadata

- **To**: [Recipient name and email]
- **Subject**: [Email subject line]
- **Purpose**: [Why sending this email]

## Draft

[Email content here]

---

## Notes

[Any additional context or follow-up needed]
```

## Email Analysis Format

```markdown
# Email Analysis: [Subject]

Analysis of email received from [Sender] on [Date] regarding [topic].

---

## Summary

[2-3 sentence summary]

## Key Points

- Point 1
- Point 2
- ...

## Action Items

- [ ] Action 1
- [ ] Action 2
- ...

## Tone Assessment

[Formal/informal, positive/negative, urgent/routine]

## Suggested Response Approach

[How to respond]
```

## File Naming

- Drafts: `YYYY-MM-DD-subject-email-draft.md`
- Sent: `YYYY-MM-DD-subject-email-sent.md`
- Analysis: `YYYY-MM-DD-subject-email-analysis.md`

## Arguments

$ARGUMENTS
