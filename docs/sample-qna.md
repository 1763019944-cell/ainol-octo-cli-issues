# AINOL 产品问答样例

## Q1：octo-cli 是什么？

`octo-cli` 是 Octo 生态的命令行接口，定位是给 AI Agent Bot 从 OpenClaw、Claude Code 等运行时通过 `exec` 调用的单二进制 REST 客户端；它每次调用在 stdout 输出结构化 JSON envelope，错误走 stderr，且没有交互式 I/O。来源: README.md#L7-L11

## Q2：支持哪些 token？

支持的 token 格式包括：`app_`、`bf_`、`uk_`、`octo_loop_`，分别被格式分类为 `app_bot`、`user_bot`、`user_key`、`loop_credential`。这个分类只是 token 格式判断，真实主体要由服务端验证。来源: internal/credential/token.go#L3-L27

## Q3：`OCTO_TOKEN` 和 `OCTO_BOT_TOKEN` 谁优先？

`OCTO_TOKEN` 优先于 `OCTO_BOT_TOKEN`；EnvProvider 会按 `OCTO_TOKEN` → `OCTO_BOT_TOKEN` 的顺序读取第一个非空 token。来源: internal/credential/env_provider.go#L8-L16

## Q4：输出 envelope 长什么样？

成功时 envelope 至少包含 `ok: true`、`identity` 和 `data`；分页响应会额外拆出 `_pagination`，也可能带 `_rate_limit`、`_notice`。来源: internal/output/envelope.go#L36-L75

错误时 envelope 是 `ok: false` 加 `error` 对象，`error` 包含 `type`、`code`、`message`，并可选带 `hint`、`detail`。来源: internal/output/envelope.go#L96-L123

## Q5：退出码怎么分？

`auth_error` 退出码是 3；`validation` 和 `config` 退出码是 2；其他错误默认退出码是 1。来源: internal/output/errors.go#L46-L56

## Q6：全局参数有哪些？

根命令全局参数包括 `--format`、`--jq/-q`、`--dry-run`、`--verbose`、`--timeout`、`--no-retry`、`--space`、`--bot-id`、`--profile`。来源: cmd/root.go#L47-L56

## Q7：matter 域能不能用？

我不建议把 `matter` 当成当前可用命令面。虽然 spec 里有 matter 操作，但 `matter.json` 设置了 `x-octo-disabled: true`，根命令初始化后会移除 disabled service 的命令子树。来源: internal/registry/specs/matter.json#L8-L12；来源: cmd/root.go#L101-L123

## Q8：本地 token 存在哪里？安全吗？

默认存在 `~/.octo-cli`，可用 `OCTO_CONFIG_DIR` 改；非 secret 元数据在 `config.json`，token 在 AES-256-GCM 加密的 `credentials.enc`。这个设计能降低离机泄漏风险，但不能防同一 OS 用户下的进程读取，所以互不信任 bot 应使用不同 OS 用户或不同 `OCTO_CONFIG_DIR`。来源: internal/authstore/authstore.go#L1-L10
