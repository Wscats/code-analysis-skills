# 指标含义与健康值参考

本文档说明代码分析技能产出的各项指标的含义、计算方式和建议的健康值范围。

## 📝 提交习惯指标

| 指标 | 含义 | 计算方式 | 健康值范围 |
|------|------|---------|-----------|
| Total Commits | 总提交次数 | 统计所有非过滤提交 | — |
| Merge Ratio | 合并提交占比 | merge_commits / total_commits | < 30% |
| Avg Commits/Active Day | 每个活跃日的平均提交数 | total_commits / unique_active_days | 2-8 |
| Avg Message Length | 平均提交消息长度(字符) | sum(msg_len) / count | 30-100 |
| Avg Lines Added | 平均每次提交新增行数 | sum(added) / count | 10-200 |
| Avg Lines Deleted | 平均每次提交删除行数 | sum(deleted) / count | 5-100 |
| Avg Files Changed | 平均每次提交修改文件数 | sum(files) / count | 1-10 |

## ⏰ 工作习惯指标

| 指标 | 含义 | 计算方式 | 关注阈值 |
|------|------|---------|---------|
| Peak Hour | 提交最多的小时 | mode(commit_hours) | — |
| Weekend Ratio | 周末提交占比 | weekend_commits / total | > 20% 需关注 |
| Late Night Ratio | 深夜(22:00-05:00)提交占比 | late_night_commits / total | > 15% 需关注 |
| Longest Streak | 最长连续编码天数 | 连续日期计数 | — |
| Avg Gap Between Commits | 两次提交的平均间隔(小时) | avg(time_gaps) | — |

### 时段定义

| 时段 | 时间范围 |
|------|---------|
| Early Morning | 05:00 - 08:59 |
| Morning | 09:00 - 11:59 |
| Afternoon | 12:00 - 17:59 |
| Evening | 18:00 - 21:59 |
| Late Night | 22:00 - 04:59 |

## 🚀 研发效率指标

| 指标 | 含义 | 计算方式 | 健康值范围 |
|------|------|---------|-----------|
| Churn Rate | 代码流失率（写了又删的比例） | total_deleted / total_added | < 50% |
| Rework Ratio | 返工率（7天内重复修改同一文件） | rework_mods / total_mods | < 30% |
| Lines per Commit | 每次提交的总变更行数 | (added + deleted) / commits | 20-300 |
| Ownership Ratio | 文件所有权比例（贡献 >50% 的文件） | owned_files / unique_files | — |
| Bus Factor | 仓库平均总线因子（每个文件的独立贡献者数） | avg(unique_authors_per_file) | > 2 为佳 |

### 指标解读

- **Churn Rate 高**: 可能表示需求变更频繁、技术方案不稳定或探索性编码
- **Rework Ratio 高**: 可能表示代码质量问题、需求不明确或 review 反馈多
- **Bus Factor 低**: 知识集中在少数人手中，团队有风险

## 🎨 代码风格指标

| 指标 | 含义 | 计算方式 | 建议 |
|------|------|---------|------|
| Conventional Commit Ratio | 遵循 Conventional Commits 规范的比例 | conventional_count / total | > 80% 为佳 |
| Issue Reference Ratio | 提交消息中引用 Issue/Ticket 的比例 | issue_ref_count / total | > 50% 为佳 |
| Language Distribution | 修改的文件语言分布 | 按文件扩展名统计 | — |
| File Category Distribution | 修改的文件类别分布 | source/test/config/docs 等 | — |

### Conventional Commits 格式

```
<type>(<scope>): <description>
```

支持的 type: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

## 🔍 代码质量指标

| 指标 | 含义 | 计算方式 | 关注阈值 |
|------|------|---------|---------|
| Bug Fix Ratio | Bug 修复提交占比 | bugfix_commits / total | > 40% 需关注 |
| Revert Ratio | 回滚提交占比 | revert_commits / total | > 5% 需关注 |
| Large Commit Ratio | 大提交(>500行变更)占比 | large_commits / total | > 20% 需关注 |
| Test Modification Ratio | 测试文件修改占文件修改总数的比例 | test_mods / total_mods | > 20% 为佳 |
| Doc Modification Ratio | 文档文件修改占比 | doc_mods / total_mods | — |
| Avg Python Complexity | Python 代码平均圈复杂度 | radon cc_visit 结果平均 | < 10 为佳 |

### 圈复杂度参考

| 复杂度 | 等级 | 说明 |
|--------|------|------|
| 1-5 | A | 低风险，容易维护 |
| 6-10 | B | 中等，仍可接受 |
| 11-20 | C | 高风险，建议重构 |
| 21-50 | D | 非常高，应当拆分 |
| 50+ | F | 不可维护 |
