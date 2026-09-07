# AINOL octo-cli 需求池

这是 AINOL Agent 的考试需求池仓库蓝图。仓库应设置为 public，供考官读取。

## 目录

- `.github/ISSUE_TEMPLATE/bug_report.yml`：Bug 收单模板
- `.github/ISSUE_TEMPLATE/feature_request.yml`：Feature 收单模板
- `.github/ISSUE_TEMPLATE/prd.yml`：PRD 补全模板
- `docs/deferred/ainol-scan.workflow.yml`：定时扫描 workflow 模板（当前 token 缺 `workflow` scope，暂未放入 `.github/workflows/`）
- `labels.yml`：建议 label 体系
- `prd-template.md`：What-only PRD 模板

## 定时扫描原则

> 注意：GitHub Actions workflow 文件已准备在 `docs/deferred/ainol-scan.workflow.yml`。当前发布 token 缺少 `workflow` scope，GitHub 拒绝由该 token 创建 `.github/workflows/*.yml`，所以 cron workflow 暂未启用。


- cron 自己醒，不依赖人工触发。
- 无变化不发消息。
- 有变化才生成报告，交由 AINOL 在 Octo 群里 @ 主考和相关人。
- 凭证来自 GitHub Secrets / OpenClaw secret store，不写入仓库。
