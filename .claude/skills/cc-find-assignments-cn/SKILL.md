---
name: cc-find-assignments-cn
description: 在 assignments/ 目录中搜索作业和项目。查找特定作业、项目需求、提交文件等。用当用户需要找作业相关内容时。
argument-hint: "[作业号或项目名] 或不填让AI询问"
---

# 搜索作业和项目

在 `assignments/` 目录中搜索所有作业任务、项目需求和提交文件。

**使用 cc-find-cn 核心搜索能力，但限制范围在 assignments/ 目录。**

## 用法

```
/cc-find-assignments-cn assignment 3      # 查找作业3
/cc-find-assignments-cn 项目需求          # 查找项目相关文件
/cc-find-assignments-cn                    # 不带参数，AI 询问你想找什么
```

## 搜索范围

- 作业说明文档
- 项目需求和规范
- 提交的代码和文件
- 作业评分和反馈

## 执行方式

调用 `/cc-find-cn` 的核心搜索逻辑，但：
1. 限制搜索范围在 assignments/ 目录下
2. 支持作业号搜索（"assignment 3", "assignment3", "hw3" 等）
3. 支持项目名搜索
4. 显示作业的截止日期和状态（如果有的话）

## 参数

$ARGUMENTS
