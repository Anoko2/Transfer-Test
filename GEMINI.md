## Custom Commands

No CLAUDE.md was present in the source repository. The following commands have been migrated from `.claude/skills/` and are available in `.gemini/commands/`:

| Command | Description |
|---|---|
| `/cc-add-ref-cn` | 收集课程资料（URL/粘贴/截图），自动下载分类整理到本地。中文版 cc-add-ref。 |
| `/cc-add-ref` | Fetch and organize course materials from URLs, pasted text, or screenshots. |
| `/cc-chunk-pdf-cn` | 索引和分拆大型 PDF 课程资料（中文版）。 |
| `/cc-chunk-pdf` | Index and chunk large PDF course materials. |
| `/cc-email` | Draft, send, or analyze course-related emails. |
| `/cc-extract-to-md` | Extract text from URLs, PDFs, or any source files and convert to Markdown. |
| `/cc-find-assignments-cn` | 在 assignments/ 目录中搜索作业和项目（中文版）。 |
| `/cc-find-assignments` | Search assignments and projects in the assignments/ directory. |
| `/cc-find-cn` | 搜索课程仓库中的文本内容（中文版）。 |
| `/cc-find-communication-cn` | 在 communication/ 目录中搜索邮件、电话记录、通信（中文版）。 |
| `/cc-find-communication` | Search emails, phone records, and communications in the communication/ directory. |
| `/cc-find-notes` | Search personal study notes in the notes/ directory. |
| `/cc-find` | Search text content in the course repository. |
| `/migrate` | Migrate a Claude Code project's `.claude/` skills, commands, agents and CLAUDE.md to Codex CLI and Gemini CLI equivalents. |

Gemini auto-discovers `.gemini/commands/` — no setup step is needed.
