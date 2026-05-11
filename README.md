# Transfer-Test

## `/migrate` — Claude Code 配置迁移工具

将 Claude Code 项目的 `.claude/` 配置（skills、commands、agents、CLAUDE.md）自动迁移到 **Codex CLI** 和 **Gemini CLI** 的等效格式。

### 生成的文件

| 文件 | 说明 |
|---|---|
| `AGENTS.md` | Codex 顶层指令（从 CLAUDE.md 合并，`@imports` 内联展开） |
| `.codex/skills/<name>/SKILL.md` | 每个 skill/command/agent 对应一个 Codex skill |
| `GEMINI.md` | Gemini 顶层指令（`@imports` 改写为 `@{path}` 语法） |
| `.gemini/commands/<name>.toml` | 每个 skill/command/agent 对应一个 Gemini command |
| `MIGRATION_REPORT.md` | 迁移报告，列出所有转换结果和需要人工检查的项目 |

### 使用方法

在 Claude Code 中运行：

```
/migrate <目标仓库的绝对路径>
```

**参数：**
- 必须是**绝对路径**
- 目标仓库必须包含 `.claude/` 目录

**如果目标目录已有迁移文件（`AGENTS.md`、`.codex/`、`.gemini/` 等），工具会先询问你是否覆盖，不会静默覆盖。**

---

### 示例

假设你有一个课程助手项目在 `/workspaces/my-course`，其中包含若干 Claude Code skills，现在想同时支持 Codex 和 Gemini：

```
/migrate /workspaces/my-course
```

迁移完成后，目录结构如下：

```
my-course/
├── .claude/                  ← 原始配置，只读，不会被修改
│   └── skills/
│       ├── cc-find/
│       └── cc-email/
│
├── .codex/                   ← 新增：Codex CLI 配置
│   └── skills/
│       ├── cc-find/
│       │   └── SKILL.md
│       └── cc-email/
│           └── SKILL.md
│
├── .gemini/                  ← 新增：Gemini CLI 配置
│   └── commands/
│       ├── cc-find.toml
│       └── cc-email.toml
│
├── AGENTS.md                 ← 新增：Codex 顶层指令
├── GEMINI.md                 ← 新增：Gemini 顶层指令
└── MIGRATION_REPORT.md       ← 新增：迁移报告
```

**激活 Codex skills（运行一次）：**

```bash
# 软链接方式（自动同步本地修改）：
ln -s "$(pwd)/.codex/skills" ~/.codex/skills

# 或复制方式（静态快照）：
mkdir -p ~/.codex/skills && cp -r .codex/skills/. ~/.codex/skills/
```

**Gemini 无需额外配置**，会自动发现 `.gemini/commands/` 目录。

---

### 注意事项

- **`$ARGUMENTS` → `{{args}}`**：Gemini TOML 中所有参数引用统一合并为 `{{args}}`，位置参数/命名参数信息会丢失
- **`disable-model-invocation: true`**：Gemini 不支持此字段，迁移后命令改用普通 AI 推理执行，行为可能有差异
- **子 agent（`.claude/agents/`）**：Codex 和 Gemini 均不支持自动分发，迁移后降级为手动调用的普通 skill/command
- **Shell 注入块（\`!cmd\`）**：Codex 不支持，迁移时保留原文并添加 TODO 注释，需人工处理
- **迁移报告**：查看 `MIGRATION_REPORT.md` 了解所有被丢弃的字段和需要人工确认的项目
