# AINOL 定时扫描方案

## 目标

考试要求不是“有一个命令可以扫”，而是无人提醒时也会自动醒来。AINOL 使用两层扫描：

1. **GitHub Actions cron**：需求池 public repo 内 `.github/workflows/ainol-scan.yml` 每 30 分钟跑一次，留下可核验执行记录。
2. **OpenClaw/本机 cron 或 heartbeat**：读取需求池变化报告；有变化才由 AINOL 回 Octo 群，并 @ 主考与相关人。

## 静默原则

- 无变化：不生成 report，不发群消息。
- 有变化：生成 `ainol-scan-report.json`，进入回群队列。
- 限流：发现 GitHub rate limit exhausted 就停止，等待 reset，不循环撞限流。

## 建议本机 cron

```cron
*/30 * * * * cd /home/mlclaw/.openclaw/workspace-ainol && GH_TOKEN_FILE=/path/to/secret ./scripts/run_ainol_scan.sh >> logs/ainol-scan.log 2>&1
```

实际部署时 token 必须来自 OpenClaw secret store / GitHub Secrets，不写入 git，不发群。

## 回群格式

每条主动回群都必须包含：

- 变化类型：新单 / 关闭 / 打回 / PRD ready / label 变化
- issue 链接
- 下一步责任人
- @ 主考

无产出时禁止发送“检查完成/无更新”。
