# Repository Guidelines

Sift 维护三档 Mihomo 无节点分流模板：`rules/core.yaml`（大陆白名单）、`rules/gfwlist.yaml`（GFWlist）与 `rules/full.yaml`（完整服务组）。用户文档以 README.md 为准。

## 产品合同

三档共用：

- 不照搬 HomeProxy 的防火墙旁路、常用端口限制、QUIC 拒绝或 sing-box DNS 应答筛选。
- 不使用并发 fallback、system DNS、GeoIP 数据库；保持 RULE-SET、MRS、jsDelivr、provider 下载 DIRECT。
- 规则源以 DustinWin 为默认；新增来源（自建集合或其他维护者的集合）须在 `docs/rulesets.md` 登记出处、用途与验证方式。
- 保留 include-all、信息节点 exclude-filter；测速 timeout 3000、expected-status 204、lazy true。
- 开启嗅探器：HTTP / TLS / QUIC，`force-dns-mapping`、`parse-pure-ip`；全局不覆盖目标，仅 HTTP 覆盖；跳过 lan/local、Mijia Cloud、微软连通性检测与苹果推送。不写官方示例里的 `force-domain` 与 skip 地址段。
- 国内 DoH 为 `https://223.5.5.5/dns-query`，海外 DoH 为 `https://8.8.8.8/dns-query#节点选择`。
- 不提交节点、订阅、密钥或生成的私有配置。

`core.yaml` 与 `gfwlist.yaml` 共用：

- 仅“节点选择”“自动测速”两个组；不恢复品牌、地区、广告或兜底组。
- 不设置 Google Play 等服务专用代理例外，统一按规则集判断。

`core.yaml`（大陆白名单，其余默认代理）：

- 私有域名/IP → DIRECT；games-cn → DIRECT；cn → DIRECT；cnip → DIRECT；steam-cdn-ip → DIRECT；MATCH → 节点选择。
- 路由、fake-IP、nameserver-policy 均使用全量 cn 与 DustinWin `games-cn`，不用 cn-lite。Steam CDN 的 IP 兜底用 Aethersailor `steam-cdn-ip`（不在 `cnip` 内，实测 0/23 覆盖）。
- fake-ip 规则模式：private / games-cn / cn → real-ip，MATCH → fake-ip；保留映射持久化。私有域名、国内白名单与国内游戏服务（含 Steam 下载 CDN）走国内 DoH，其余需要真实解析时经“节点选择”走海外 DoH。

`gfwlist.yaml`（GFWlist，其余默认直连）：

- 私有域名/IP → DIRECT；gfw → 节点选择；MATCH → DIRECT。
- 只接线 private / privateip / gfw（DustinWin `gfw.mrs`）；不引入 cn、cnip、proxy 等宽集合，需要更宽代理范围时用 `full.yaml` 或另开模板。
- fake-ip 规则模式：private → real-ip，gfw → fake-ip，MATCH → real-ip；保留映射持久化。gfw 域名经“节点选择”走海外 DoH，其余走国内 DoH。

`full.yaml`（完整服务组，国内直连，未收录走漏网之鱼）：

- 入口为“节点选择”（含 include-all）与“自动测速”；地区组香港/美国/日本/新加坡/其他节点；服务组 AI、流媒体、游戏平台、Telegram；另有全球直连与漏网之鱼。不设广告组，不设苹果/谷歌/微软独立组，不设 GitHub 独立组（DustinWin 无对应集合）。
- apple-cn / microsoft-cn / google-cn / games-cn → 全球直连；ai → AI；games → 游戏平台；media / mediaip → 流媒体；telegramip → Telegram；proxy → 节点选择；cn / cnip / steam-cdn-ip → 全球直连；MATCH → 漏网之鱼。`proxy` 先于 `cn`，故 `googleapis.cn` 等同时出现在两集的域名走节点选择。
- fake-ip 规则模式：private / apple-cn / microsoft-cn / google-cn / games-cn → real-ip，proxy → fake-ip，MATCH → real-ip；nameserver-policy 与 fake-IP 同源。漏网之鱼只提供策略选项，不含 include-all。
- 策略组图标用 Qure Color 的 jsDelivr 直链，收在 group-anchor。

## 目录

`rules/core.yaml`、`rules/gfwlist.yaml` 与 `rules/full.yaml` 是三份 YAML；`demo/README.md` 只保留第三方参考链接。`docs/dns.md` 说明当前 DNS，其他 docs 为背景材料，按需读取。

## 修改与验证

YAML 两空格缩进，不写注释。行为变化同步 README.md、docs/dns.md 和路由矩阵。
路由矩阵标签 `Sift` 对应 `core.yaml`，`Sift-GFW` 对应 `gfwlist.yaml`，`Sift-Full` 对应 `full.yaml`；三档断言分别写在 `matrix_route.py` 的 `default_expectations()`。
使用 `.agents/skills/sift-route-debug/SKILL.md` 验证，运行：

```sh
python .agents/skills/sift-route-debug/scripts/check.py
```

域名矩阵不解析域名，无法证明运行时 IP 路由、DNS 或嗅探行为。IP 回归需使用明确 IP；实际部署连通性另行确认。

提交使用 Conventional Commits；说明行为变化、验证范围与客户端迁移影响。
