---
name: migrate
description: Migrate a Claude Code project's .claude/ skills, commands, agents and CLAUDE.md to Codex CLI (AGENTS.md + .codex/) and Gemini CLI (GEMINI.md + .gemini/) equivalents. Pass an absolute path to the target repo.
argument-hint: <absolute-path-to-target-repo>
---

<!-- NOTE(migrate): allowed-tools dropped — Codex does not support tool allowlists. -->
<!-- NOTE(migrate): disable-model-invocation dropped — Codex has no equivalent. This skill relies on AI reasoning to follow the steps below; verify each step manually. -->

# /migrate — Claude Code → Codex + Gemini migrator

You are running the `/migrate` skill. Your job is to translate a Claude Code project's `.claude/` configuration into Codex CLI and Gemini CLI equivalents inside the same target repository.

## Input

Target repository absolute path: `$1` (alias `$ARGUMENTS`).

## Goal

Read the Claude Code configuration in `$1` and generate, in the same repo:

- `$1/AGENTS.md` — Codex top-level instructions (translated from CLAUDE.md, with `@imports` inlined).
- `$1/.codex/skills/<name>/SKILL.md` — one Codex skill per source command/skill/agent.
- `$1/GEMINI.md` — Gemini top-level instructions (translated from CLAUDE.md, `@imports` rewritten).
- `$1/.gemini/commands/<name>.toml` — one Gemini custom command per source command/skill/agent.
- `$1/MIGRATION_REPORT.md` — a per-artifact table of what was migrated, what was inlined, what needs manual review.

You must NOT modify anything under `$1/.claude/`. The source is read-only.

## Step 0 — Validate input

Refuse to start if any check fails. Print a single clear error and stop.

1. If `$1` is empty, missing, or relative: abort with `Provide an ABSOLUTE path. Usage: /migrate /absolute/path/to/repo`.
2. Run `test -d "$1"` — abort if the path doesn't exist.
3. Run `test -d "$1/.claude"` — abort if there's no `.claude/` to migrate.
4. Check whether any of `$1/AGENTS.md`, `$1/GEMINI.md`, `$1/.codex`, `$1/.gemini`, `$1/MIGRATION_REPORT.md` already exist. If yes, **stop and ask the user** whether to overwrite. Default to stopping. Never silently overwrite. If the user confirms overwrite: **delete each conflicting path completely** before proceeding (dirs removed recursively, files removed individually) — do NOT merge with or patch existing content. Clean slate only.

## Step 1 — Discover sources

Build an inventory before writing anything. Use `Glob` and `Read` (no shell scanning beyond `ls`).

Catalog these source paths if present:

- `$1/CLAUDE.md`, `$1/.claude/CLAUDE.md`, `$1/CLAUDE.local.md` (combine in Claude Code's precedence order: project root > `.claude/` > `.local`).
- `$1/.claude/commands/**/*.md` (note: Claude Code does NOT namespace command subdirs; commands stay flat as `/<name>`).
- `$1/.claude/skills/*/SKILL.md` (each skill is a directory; record sibling files too).
- `$1/.claude/agents/**/*.md`.

For each source artifact, record in your scratchpad:
- source path
- planned Codex target path
- planned Gemini target path
- list of `@`-references inside (resolve relative to the file containing the reference)
- list of bang-backtick shell-injection blocks inside (Claude Code's syntax for inlining shell command output: an exclamation mark immediately followed by a backtick-wrapped command)
- frontmatter fields present (so you can report which got dropped)

## Step 2 — Migrate CLAUDE.md → AGENTS.md and GEMINI.md

If a CLAUDE.md exists at any of the locations above, merge them into a single source string in precedence order, then produce two outputs:

### AGENTS.md (Codex — `@imports` inlined)

Codex does not support `@`-imports. Resolve every `@path/to/file` reference recursively (max 5 hops; track visited paths to break cycles). Replace each reference inline with the imported file's content, wrapped in delimiter comments:

```
<!-- BEGIN imported from <relative-path> -->
<file content>
<!-- END imported from <relative-path> -->
```

Prepend the `## Setup (Codex CLI)` block from Step 5 to the top of the document. Write the result to `$1/AGENTS.md`.

### GEMINI.md (Gemini — `@imports` rewritten)

Gemini supports file injection with `@{path}` syntax. Rewrite every `@path/to/file` reference as `@{path/to/file}`. Do NOT inline. Prepend a `## Custom commands` section listing migrated commands with their descriptions. Write to `$1/GEMINI.md`.

If no CLAUDE.md exists, generate minimal stubs containing only the setup / listing sections.

## Step 3 — Migrate commands and skills

For every `.claude/commands/<name>.md` and every `.claude/skills/<name>/SKILL.md`:

### Codex target — `$1/.codex/skills/<name>/SKILL.md`

Each migrated artifact becomes a Codex skill: a directory named `<name>/` containing a `SKILL.md` file. The directory name and the `name:` frontmatter field MUST match.

1. Parse the YAML frontmatter. Keep only `name`, `description`, and `argument-hint`. Drop the rest. Re-emit minimal YAML frontmatter. The `name` field is REQUIRED for Codex to load the skill — if the source frontmatter does not have one, derive it from the source basename / skill directory name (e.g. `.claude/skills/teach-check-cn/SKILL.md` → `name: teach-check-cn`; for subagents `agent-<name>` per Step 4). The format must match this template exactly:

   ```yaml
   ---
   name: <command-name>
   description: <description text>
   ---
   ```
2. Process the markdown body:
   - **`@path` references**: read the referenced file, recursively expand its own references (≤5 hops), and inline the final content in place using the `<!-- BEGIN imported -->` / `<!-- END imported -->` delimiters from Step 2.
   - **Bang-backtick shell-injection blocks**: keep the literal text verbatim and prepend an HTML comment on the line above:
     `<!-- TODO(migrate): Codex CLI does not support shell injection. Replace this block with the actual output, or remove it. -->`
     Do NOT execute the command.
   - **Argument substitutions** `$ARGUMENTS`, `$1`–`$9`, `$NAMED`: leave verbatim. Codex shares this syntax.
3. Create the directory `$1/.codex/skills/<name>/` if needed and write `SKILL.md` inside it.
4. **For skills only**: if the source skill directory contains files other than `SKILL.md` (e.g. `examples.md`, `scripts/helper.sh`), copy them into `$1/.codex/skills/<name>/` alongside `SKILL.md` (same directory, not a nested subdir). Rewrite any in-prompt references that pointed at sibling files so they remain valid — typically this means stripping the original directory prefix, since siblings are now in the same directory as `SKILL.md`.

### Gemini target — `$1/.gemini/commands/<name>.toml`

1. Parse the YAML frontmatter. Translate to TOML keys:
   - `description: <s>` → `description = "<s>"`
   - All other fields: drop. Record them in MIGRATION_REPORT. Two dropped fields carry functional risk — flag them explicitly in the MIGRATION_REPORT "Things that need manual review" section:
     - `disable-model-invocation: true`: Gemini has no equivalent. The migrated command uses AI reasoning instead of strict step-by-step execution; results may be inconsistent. The user must verify each migration step manually.
     - `allowed-tools`: Gemini has no equivalent. The migrated command has unrestricted tool access. The user should review the command carefully before running it on sensitive repositories.
2. Process the body:
   - `@path` → `@{path}` (Gemini supports this; do not inline).
   - Bang-backtick shell-injection blocks → rewrite to Gemini's `!{cmd}` form (Gemini supports this; do not inline output).
   - `$ARGUMENTS` → `{{args}}`.
   - `$1`–`$9`, `$NAMED` → `{{args}}` (LOSSY: Gemini collapses positional/named args into one bag). Add a TOML comment line above the TOML key: `# NOTE: Claude positional/named arguments collapsed to {{args}} during migration.`
   - **Literal `{{args}}` already in source body**: Before applying the rewrites above, scan the source body for any occurrences of `{{args}}` that are already present as literal text (e.g., instructional content that describes the Gemini target format, such as "rewrite X to `{{args}}`"). These are NOT the skill's own argument references. After all rewrites, any such literal occurrences that remain verbatim in the TOML output will be substituted by Gemini's template engine when the user invokes the command, corrupting the prompt. Escape them by reformulating as prose (e.g., "Gemini args placeholder") or by splitting the pattern across code spans so the complete `{{args}}` token never appears verbatim.
3. Wrap the processed body as a triple-quoted multiline TOML string:
   ```
   prompt = """
   <body>
   """
   ```
   If the body itself contains `"""`, escape as `\"""`.
4. Write the file. Create `.gemini/commands/` if needed.
5. **For skills only**: copy sibling files to `$1/.gemini/commands/<name>/`. Rewrite in-prompt sibling references to use Gemini's syntax: `@{<name>/sibling.md}`.

## Step 4 — Migrate subagents (`.claude/agents/*.md`)

Both Codex and Gemini lack subagent auto-dispatch. Demote each subagent to a manually-invocable command:

### Codex
- Directory: `$1/.codex/skills/agent-<name>/`, file: `SKILL.md`. The frontmatter `name` field MUST be `agent-<name>` to match the directory.
- Prepend an admonition in the body, before any other content:
  > **Note**: This was a Claude Code subagent. Auto-dispatch is not supported in Codex CLI. This has been demoted to a manually-invocable skill — reference it explicitly by the name `agent-<name>` instead of relying on auto-dispatch.
- Otherwise apply Step 3 Codex rules.

### Gemini
- File: `$1/.gemini/commands/agent/<name>.toml` (the `agent/` subdir gives it the namespaced name `/agent:<name>`).
- Prepend the same admonition as a TOML comment block above the `description` key.
- Otherwise apply Step 3 Gemini rules.

## Step 5 — Setup section content

Insert this block verbatim at the top of `$1/AGENTS.md`:

```markdown
## Setup (Codex CLI)

Codex CLI loads skills from `~/.codex/skills/`. Each skill is a directory containing a `SKILL.md` file with `name:` and `description:` frontmatter — Codex auto-discovers skills by their `description`. To activate the skills in this repo, run **once**:

```bash
# Symlink (picks up edits automatically):
ln -s "$(pwd)/.codex/skills" ~/.codex/skills

# OR copy (snapshot, no live updates):
mkdir -p ~/.codex/skills && cp -r .codex/skills/. ~/.codex/skills/
```

Skills are referenced by the `name:` value in their `SKILL.md` frontmatter.

Subagents from the original Claude Code project are exposed as skills named `agent-<name>` since Codex has no subagent auto-dispatch.
```

For `$1/GEMINI.md`, insert a `## Custom commands` section that auto-lists each migrated command name and its description. Gemini auto-discovers `.gemini/commands/`, so no setup step is needed.

## Step 6 — Write `MIGRATION_REPORT.md`

Write a human-readable report at `$1/MIGRATION_REPORT.md`:

```markdown
# Migration Report

Generated by `/migrate` on <ISO 8601 timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ`>.

## Source summary

- Repo: $1
- CLAUDE.md present: yes/no
- Commands: N
- Skills: M
- Subagents: K

## Migrations table

| Source | Codex target | Gemini target | Warnings |
|---|---|---|---|
| `.claude/commands/teachstart.md` | `.codex/skills/teachstart/SKILL.md` | `.gemini/commands/teachstart.toml` | none |
| `.claude/skills/teachcode/SKILL.md` | `.codex/skills/teachcode/SKILL.md` (+ siblings copied) | `.gemini/commands/teachcode.toml` (+ `teachcode/`) | shell injection in body — manual fix needed |
| `.claude/agents/code-reviewer.md` | `.codex/skills/agent-code-reviewer/SKILL.md` | `.gemini/commands/agent/code-reviewer.toml` | auto-dispatch lost |

## Things that need manual review

- Any bang-backtick shell-injection blocks in Codex targets — Codex does not support that syntax. List affected files.
- Subagent auto-dispatch is lost on both targets. List affected agents.
- Gemini args placeholder is lossy vs Claude's `$1..$9` / `$NAMED`. List affected commands.
- Frontmatter fields dropped per file (table below).

## Dropped frontmatter fields

| File | Field | Reason |
|---|---|---|
| (filled per source) | (e.g. `model`, `allowed-tools`) | not supported by target |
```

## Step 7 — Final summary to user

Print:

```
Migration complete.
- Wrote $1/AGENTS.md and $1/GEMINI.md
- Wrote N Codex skills to $1/.codex/skills/<name>/SKILL.md
- Wrote M Gemini commands to $1/.gemini/commands/
- Report: $1/MIGRATION_REPORT.md

Activate Codex skills:
  ln -s "$1/.codex/skills" ~/.codex/skills

Gemini auto-discovers .gemini/commands/ — nothing to do.
```

## Hard constraints — DO NOT

- Do NOT execute any shell command from bang-backtick shell-injection blocks during migration. Preserve as text + TODO comment.
- Do NOT modify anything inside `$1/.claude/`.
- Do NOT use absolute paths inside generated files. References stay relative to the target repo root.
- Do NOT silently overwrite existing AGENTS.md, GEMINI.md, `.codex/`, `.gemini/`. Ask first.
- Do NOT skip MIGRATION_REPORT.md — it's the user's audit trail.
- Do NOT proceed if Step 0 validation fails.
- Do NOT leave partial output on failure. Track every file path created during this run. If any step after the first write fails, delete every path in that list before stopping and report which step failed — so the user can retry on a clean state.
