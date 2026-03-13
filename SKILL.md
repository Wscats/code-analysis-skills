---
name: code-analysis
description: >
  This skill should be used when the user needs to analyze Git repositories,
  compare developer commit patterns, work habits, development efficiency,
  code style, and code quality. Trigger phrases include "analyze code",
  "analyze repository", "compare developers", "code quality report",
  "commit patterns", "developer efficiency", "工作习惯分析", "代码分析",
  "研发效率", "代码质量".
---

# Code Analysis Skill

扫描指定仓库或目录下所有 Git 仓库，分析并对比开发者的提交习惯、工作习惯、研发效率、代码风格和代码质量，生成结构化分析报告。

## 使用场景

- 当用户需要分析某个 Git 仓库的开发者行为时
- 当用户需要对比团队成员的提交习惯和研发效率时
- 当用户需要了解代码质量趋势和代码风格一致性时
- 当用户需要扫描目录下所有 `.git` 仓库进行批量分析时
- 当用户需要生成开发者工作习惯报告（工作时段、周末加班、深夜编码等）时

## 工作流程

### 步骤 1: 确认分析参数

询问用户以下信息：
- **仓库路径**: 单个 Git 仓库路径，或包含多个仓库的父目录
- **分析范围**: 是否扫描目录下所有 `.git` 仓库（`--scan-all`）
- **目标作者**: 指定分析特定开发者（可多选），或分析全部贡献者
- **时间范围**: 可选的起止日期（ISO 格式，如 `2024-01-01`）
- **分支**: 指定分析的分支，默认为当前活跃分支
- **输出格式**: `markdown`（默认）、`json` 或 `html`

### 步骤 2: 执行分析

运行分析脚本：

```bash
# 分析单个仓库（所有贡献者）
python scripts/main.py -r /path/to/repo

# 扫描目录下所有仓库
python scripts/main.py -r /path/to/projects --scan-all

# 对比指定开发者
python scripts/main.py -r /path/to/repo -a "Alice" -a "Bob"

# 指定时间范围 + HTML 输出
python scripts/main.py -r /path/to/repo -s 2024-01-01 -u 2024-12-31 -f html -o report.html

# 保存报告到文件
python scripts/main.py -r /path/to/repo -o report.md
```

### 步骤 3: 解读报告

分析报告包含以下五个维度，逐一向用户解读关键发现：

1. **📝 提交习惯** — 提交频率、提交大小、merge 比率、消息质量
2. **⏰ 工作习惯** — 工作时段分布、周末/深夜编码比例、连续编码天数
3. **🚀 研发效率** — 代码流失率(churn)、返工率(rework)、Bus Factor、文件所有权
4. **🎨 代码风格** — 语言分布、Conventional Commits 遵循率、文件分类
5. **🔍 代码质量** — Bug Fix 比率、Revert 频率、大提交比例、测试覆盖、复杂度

如果有多位开发者，额外提供横向对比摘要表。

## 可用资源

### 脚本

- `scripts/main.py` — 主入口脚本，支持 CLI 参数，执行全部分析并生成报告
- `scripts/scanner.py` — 仓库扫描器，发现单个或递归扫描多个 Git 仓库
- `scripts/analyzers/base_analyzer.py` — 分析器基类，提供 Git 历史遍历和作者过滤
- `scripts/analyzers/commit_analyzer.py` — 提交习惯分析（频率、大小、消息质量）
- `scripts/analyzers/work_habit_analyzer.py` — 工作习惯分析（时段、周末、深夜、连续天数）
- `scripts/analyzers/efficiency_analyzer.py` — 研发效率分析（churn、rework、bus factor）
- `scripts/analyzers/code_style_analyzer.py` — 代码风格分析（语言分布、commit 规范）
- `scripts/analyzers/code_quality_analyzer.py` — 代码质量分析（bug fix、revert、复杂度）
- `scripts/reporters/markdown_reporter.py` — Markdown 格式报告生成器
- `scripts/reporters/json_reporter.py` — JSON 格式报告生成器
- `scripts/reporters/html_reporter.py` — HTML 格式报告生成器（含样式）

### 参考文档

- `references/metrics-guide.md` — 各指标含义、计算方式和健康值参考范围。当用户询问某个指标的含义时，读取此文件。

## 依赖安装

执行分析前需安装 Python 依赖：

```bash
pip install gitpython pydriller radon tabulate jinja2 click
```

## 注意事项

- 分析大型仓库（10万+提交）时可能耗时较长，建议限定时间范围
- Python 代码复杂度分析依赖 `radon` 库，仅对 `.py` 文件生效
- 作者匹配支持模糊匹配（名称或邮箱包含关键字即可）
- 扫描目录时默认最大深度为 5 层，避免过深递归
