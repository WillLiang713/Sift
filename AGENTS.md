# Repository Guidelines

Sift 维护三档 Mihomo 无节点分流模板：`rules/core.yaml`（大陆白名单）、`rules/gfwlist.yaml`（GFWlist）与 `rules/full.yaml`（完整服务组）。用户文档以 README.md 为准。

## 规则集格式（MRS）

- **尽可能使用 MRS**（`format: mrs`）作为 rule-provider 交付格式，优先于 `.list` / classical 文本集，以降低加载体积与匹配开销、保证性能。
- 三档模板的 domain / ipcidr 提供者默认走 MRS 锚点（如 `mrs-domain` / `mrs-ip`）；新增或更换规则源时，优先选上游已发布的 `.mrs`。
- 仅当上游没有可用 MRS、或必须保留 classical 语义时，才允许临时使用其他格式，并在 PR 说明原因与回退计划。
- 不要把「能跑」当成「可以混用格式」：同一行为的规则集，有 MRS 就不要并行引入 `.list` / classical。

## 产品合同（摘要）

三档共用：

- 规则主源仍以 DustinWin 为主；Aethersailor / MetaCubeX 等仅作窄补充（如 Custom Direct、Steam CDN、Telegram 域名）。
- 保留 include-all 与信息节点 exclude-filter；健康检查默认 interval 60、timeout 3000、expected-status 204、max-failed-times 2、lazy true。
- 开启嗅探（HTTP / TLS / QUIC）；不提交节点、订阅或密钥。

`core.yaml` / `gfwlist.yaml`：策略组保持精简（节点选择 / 自动测速 / 故障转移），不恢复品牌独立组。

`full.yaml`：可有服务组与地区组；`apple-cn` / `microsoft-cn` / `google-cn` / `games-cn` → 全球直连。

## 修改与验证

YAML 两空格缩进，不写注释。行为变化同步 README（如有）与路由矩阵。

验证：

```sh
python .agents/skills/sift-route-debug/scripts/check.py
```

提交使用 Conventional Commits；说明行为变化、验证范围与客户端迁移影响。
