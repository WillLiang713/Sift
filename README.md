<h1 align="center">Sift</h1>

<p align="center">
面向通用代理内核的无节点分流模板 — 只提供策略组、远程规则和分流顺序，不内置节点。
</p>

<p align="center">
  <img alt="Core" src="https://img.shields.io/badge/core-compatible-blue">
  <img alt="Rules" src="https://img.shields.io/badge/rules-list-green">
  <img alt="Node Free" src="https://img.shields.io/badge/nodes-not%20included-lightgrey">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue">
</p>

## 模板

`rules/` 存放可直接使用的无节点 Mihomo 配置模板，文件名按规则上游和档位命名：

| 文件 | 策略组 | 规则提供商 | 说明 |
| --- | ---: | ---: | --- |
| [`rules/DustinWin-full.yaml`](./rules/DustinWin-full.yaml) | 17 | 17 | DustinWin 规则集完整版：AI、流媒体、游戏平台、Telegram、Apple、Microsoft、OneDrive、地区节点；内置 fake-ip 分流 DNS、域名嗅探和状态持久化 |
| [`rules/DustinWin-core.yaml`](./rules/DustinWin-core.yaml) | 4 | 9 | DustinWin 规则集核心白名单版：保留基础节点选择、国内白名单、DNS、域名嗅探和状态持久化；完整 Apple / Microsoft 进入 `全球直连` |
| [`rules/DustinWin-nano.yaml`](./rules/DustinWin-nano.yaml) | 5 | 5 | DustinWin 规则集极简版：局域网直连、明确非中国域名、国内直连和兜底分流；不接管 DNS |
| [`rules/MetaCubeX-full.yaml`](./rules/MetaCubeX-full.yaml) | 17 | 1 | MetaCubeX Geodata 完整版：保留 Full 的策略组结构，使用 `GEOSITE` / `GEOIP` 分流；DNS 侧额外引用 `fakeip-filter` |
| [`rules/MetaCubeX-core.yaml`](./rules/MetaCubeX-core.yaml) | 4 | 1 | MetaCubeX Geodata 核心白名单版：完整 Apple、Microsoft 中国区补充与国内白名单进入 `全球直连`；DNS 侧额外引用 `fakeip-filter` |
| [`rules/MetaCubeX-nano.yaml`](./rules/MetaCubeX-nano.yaml) | 5 | 0 | MetaCubeX Geodata 极简版：局域网、明确非中国域名、国内域名/IP 与兜底分流；不接管 DNS |
| [`rules/ACL4SSR-full.yaml`](./rules/ACL4SSR-full.yaml) | 17 | 22 | ACL4SSR 规则集完整版：保留 AI、流媒体、游戏平台、Telegram、Apple、Microsoft、OneDrive、地区节点；内置 fake-ip 分流 DNS、域名嗅探和状态持久化 |
| [`rules/ACL4SSR-core.yaml`](./rules/ACL4SSR-core.yaml) | 4 | 11 | ACL4SSR 规则集核心白名单版：GoogleCN / SteamCN、Apple / Microsoft 与国内白名单进入 `全球直连` |
| [`rules/ACL4SSR-nano.yaml`](./rules/ACL4SSR-nano.yaml) | 5 | 5 | ACL4SSR 规则集极简版：局域网直连、`ProxyLite` 代理、国内直连和兜底分流；不接管 DNS |

```text
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/DustinWin-full.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/DustinWin-core.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/DustinWin-nano.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/MetaCubeX-full.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/MetaCubeX-core.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/MetaCubeX-nano.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/ACL4SSR-full.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/ACL4SSR-core.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/ACL4SSR-nano.yaml
```

## 设计要点

- **无节点**：模板不含 `proxies`，节点由订阅合并或本地配置补充。
- **三类规则来源**：`DustinWin-*` 使用 DustinWin / blackmatrix7 远程 `.list` 规则集；`MetaCubeX-*` 使用 MetaCubeX `GEOSITE` / `GEOIP`；`ACL4SSR-*` 使用 ACL4SSR Clash `.list` 路由规则，DNS 侧与 DustinWin 模板共用 domain provider。
- **运行优化**：Full / Core 及其 Geodata 版本默认启用 `unified-delay` 和 `tcp-concurrent`，减少 Reality 等节点测速虚高，并提升多 IP 目标的连接成功率。
- **状态持久化**：Full / Core 及其 MetaCubeX / ACL4SSR 版本默认保存策略组选择和 fake-ip 映射，重启后保留手动选择并减少 fake-ip 映射变化带来的连接抖动。
- **DNS 分模板**：所有 Nano 模板不接管 DNS，留给客户端本地管理；Full / Core 内置 fake-ip 分流 DNS。DustinWin 与 ACL4SSR 版本统一使用 DustinWin `fakeip-filter` / `private` / `cn` 做 DNS rule-set；MetaCubeX 版本使用同一 `fakeip-filter`，并用 `geosite:private` / `geosite:cn` 做私有/国内 DNS 规则。
- **域名嗅探**：Full / Core 及其 MetaCubeX / ACL4SSR 版本启用 `sniffer`，从 HTTP Host、TLS SNI 和 QUIC 握手中提取域名，提升 TUN / redir-host / 纯 IP 场景下的规则命中准确率。
- **双层节点选择**：`节点选择` 作为日常总控入口，`手动切换` 才展开全部节点，节点多时面板更清爽。
- **可切换直连**：Full / Nano 的国内服务与国内兜底默认进入 `全球直连`，保持直连优先，同时允许临时切到总控或自动策略排障；Core 的 `全球直连` 保留 `DIRECT`、`节点选择` 与 `自动测速`，且 `DIRECT` 排第一。
- **兜底出口**：Full / Nano 未命中规则进入 `漏网之鱼`；Core 不保留独立兜底组，未命中规则直接进入 `节点选择`。
- **Full 场景分流**：完整模板保留 AI、流媒体、游戏平台、Telegram、Apple、Microsoft、OneDrive 等独立入口。Geodata Full 中游戏规则优先级高于 `category-entertainment`，避免游戏域名被娱乐/流媒体大类提前接走；GitHub 先于 Microsoft 单独进入 `节点选择`，避免被官方 Microsoft 大类带入直连。
- **Core 白名单分流**：核心模板不保留服务 UI 分组和地区节点组；完整 Apple / Microsoft 规则和国内白名单进入 `全球直连`，该组默认 `DIRECT`、可切到 `节点选择` 或 `自动测速`，其余流量全部交给 `MATCH,节点选择`。
- **Nano 极简代理**：Nano 使用 `proxy`，Geodata Nano 使用 `geolocation-!cn`，ACL4SSR Nano 使用 `ProxyLite`，代理明确非中国域名；三者都保留国内直连和兜底，不提供地区节点或服务分组。

## 分流顺序

### DustinWin / Full

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | BT Tracker | `全球直连` |
| 3 | 国内 Apple / Microsoft / 游戏 | `全球直连` |
| 4 | Apple 海外服务 | `苹果服务` |
| 5 | AI 服务 | `AI` |
| 6 | 游戏平台 | `游戏平台` |
| 7 | 流媒体 IP | `流媒体` |
| 8 | OneDrive 网盘 | `OneDrive` |
| 9 | Microsoft 海外服务 | `微软服务` |
| 10 | Telegram IP | `Telegram` |
| 11 | 国内域名 / IPv4 / IPv6 兜底 | `全球直连` |
| 12 | 未命中流量 | `漏网之鱼` |

### MetaCubeX / Full

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | GitHub / Copilot | `节点选择` |
| 3 | 中国区 Apple / Microsoft / 游戏 | `全球直连` |
| 4 | Apple 海外服务 | `苹果服务` |
| 5 | AI 服务 | `AI` |
| 6 | 游戏平台 / 游戏下载 | `游戏平台` |
| 7 | 娱乐 / 流媒体大类 | `流媒体` |
| 8 | OneDrive 网盘 | `OneDrive` |
| 9 | Microsoft 海外服务 | `微软服务` |
| 10 | Telegram IP | `Telegram` |
| 11 | 明确非中国域名 | `节点选择` |
| 12 | 国内域名 / IP 兜底 | `全球直连` |
| 13 | 未命中流量 | `漏网之鱼` |

### ACL4SSR / Full

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 中国区 Google / Steam | `全球直连` |
| 3 | Apple 服务 | `苹果服务` |
| 4 | AI 服务 | `AI` |
| 5 | Steam / Epic / Origin / Sony / Xbox / Nintendo | `游戏平台` |
| 6 | 流媒体 | `流媒体` |
| 7 | OneDrive 网盘 | `OneDrive` |
| 8 | Microsoft 服务 | `微软服务` |
| 9 | Telegram | `Telegram` |
| 10 | ProxyLite 明确代理域名 | `节点选择` |
| 11 | 国内域名 / IPv4 / IPv6 / GEOIP CN 兜底 | `全球直连` |
| 12 | 未命中流量 | `漏网之鱼` |

### DustinWin / Core

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 国内游戏 | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 3 | 完整 Apple / Microsoft | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 4 | 国内域名 / IP 兜底 | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 5 | 未命中流量 | `节点选择` |

### MetaCubeX / Core

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | GitHub / Copilot | `节点选择` |
| 3 | 游戏中国区补充 / 完整 Apple | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 4 | 完整 Microsoft | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 5 | 国内域名 / IP 兜底 | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 6 | 未命中流量 | `节点选择` |

### ACL4SSR / Core

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 中国区 Google / Steam | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 3 | 完整 Apple / Microsoft | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 4 | 国内域名 / IPv4 / IPv6 / GEOIP CN 兜底 | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 5 | 未命中流量 | `节点选择` |

### DustinWin / Nano

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 明确非中国域名 | `节点选择` |
| 3 | 国内域名 / IPv4 / IPv6 兜底 | `全球直连` |
| 4 | 未命中流量 | `漏网之鱼` |

### MetaCubeX / Nano

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 明确非中国域名 | `节点选择` |
| 3 | 国内域名 / IPv4 / IPv6 / GEOIP CN 兜底 | `全球直连` |
| 4 | 未命中流量 | `漏网之鱼` |

### ACL4SSR / Nano

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | ProxyLite 明确代理域名 | `节点选择` |
| 3 | 国内域名 / IP 兜底 | `全球直连` |
| 4 | 未命中流量 | `漏网之鱼` |

## 策略组

**Full / MetaCubeX Full / ACL4SSR Full**：`节点选择` · `手动切换` · `自动测速` · `AI` · `流媒体` · `游戏平台` · `Telegram` · `苹果服务` · `微软服务` · `OneDrive` · `香港节点` · `美国节点` · `日本节点` · `新加坡节点` · `其他节点` · `全球直连` · `漏网之鱼`

**Core / MetaCubeX Core / ACL4SSR Core**：`节点选择` · `手动切换` · `自动测速` · `全球直连`

**Nano / MetaCubeX Nano / ACL4SSR Nano**：`节点选择` · `手动切换` · `自动测速` · `全球直连` · `漏网之鱼`

> Full 的地区组依赖节点名称中的地区关键词自动归类。建议节点命名包含 `HK`、`日本`、`US` 等标识。

## 规则来源

`DustinWin-*` 模板的远程规则集主要由 [DustinWin/ruleset_geodata](https://github.com/DustinWin/ruleset_geodata) 提供，统一使用 `format: text` 的 `.list` 以提高客户端兼容性；Full 的 BT Tracker 补充取自 [DustinWin/domain-list-custom](https://github.com/DustinWin/domain-list-custom)，使用 classical/text 的 `.list`；海外 Apple / Microsoft / OneDrive 取自 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)，使用 classical/text 的 `.list`（DustinWin 均无对应完整集，路径均不含 `geosite`/`geoip`）：`apple` = `rule/Clash/Apple/Apple.list`；`microsoft` = `rule/Clash/Microsoft/Microsoft.list`；`onedrive` = `rule/Clash/OneDrive/OneDrive.list`（microsoft / onedrive 必须 classical 才能保住 keyword / IP / process 规则）。

DNS 的 `fake-ip-filter` / `nameserver-policy` 只引用国内 DNS 入口；`*-cn` 规则只表达路由直连意图，不代表一定适合国内 DNS 解析。blackmatrix7 的完整 Apple / Microsoft / OneDrive classical 规则只用于路由分流，避免其中的 `PROCESS-NAME` 等规则类型进入 DNS 过滤。

- **DustinWin-full**：`private` · `privateip` · `trackerslist`（BT Tracker）· `apple-cn` · `apple`（blackmatrix7）· `microsoft-cn` · `microsoft`（blackmatrix7）· `onedrive`（blackmatrix7）· `games-cn` · `ai` · `mediaip` · `games` · `telegramip` · `cn-lite`（路由直连）· `cn`（DNS 国内解析）· `cnip` · `fakeip-filter`（仅供 `dns.fake-ip-filter`）
- **DustinWin-core**：`private` · `privateip` · `apple`（blackmatrix7，完整 Apple 规则，仅用于路由）· `microsoft`（blackmatrix7，完整 Microsoft 规则，仅用于路由）· `games-cn` · `cn-lite`（路由直连）· `cn`（DNS 国内解析）· `cnip` · `fakeip-filter`（仅供 `dns.fake-ip-filter`）
- **DustinWin-nano**：`private` · `privateip` · `proxy` · `cn-lite`（路由直连）· `cnip`
- **MetaCubeX-***：路由使用 [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat) 的 `geoip.dat`、`geosite.dat`、`geoip.metadb`；`rules` 中只使用 `GEOSITE` / `GEOIP`，不使用 `RULE-SET`。Full/Core 仅为 `dns.fake-ip-filter` 定义 `fakeip-filter`（DustinWin，DNS-only）；不再添加 Google 专门分流，相关域名交给明确非中国域名、国内兜底或最终兜底处理；`GEOSITE,github,节点选择` 放在高优先级位置，避免官方 Microsoft / 场景大类中的 GitHub / Copilot 相关域名被提前接走；`GEOIP,CN` 与 `GEOIP,telegram` 不追加 `no-resolve`，保留常规域名解析后的 IP 分流行为。
- **ACL4SSR-***：路由使用 [ACL4SSR/ACL4SSR](https://github.com/ACL4SSR/ACL4SSR) 的 Clash `.list` 文件，并以 `classical`/`text` 接入；Full/Core 的 DNS 侧与 DustinWin 模板对齐，统一使用 DustinWin `fakeip-filter` / `private` / `cn`，避免把含 `IP-CIDR` / `no-resolve` 的 ACL4SSR classical 列表放进 DNS rule-set。Full 包含 `LocalAreaNetwork` · `ChinaDomain` · `ChinaIp` · `ChinaIpV6` · `GoogleCN` · `SteamCN` · `Apple` · `AI` · `Steam` · `Epic` · `Origin` · `Sony` · `Xbox` · `Nintendo` · `ProxyMedia` · `OneDrive` · `Microsoft` · `Telegram` · `ProxyLite` · `fakeip-filter` · `private` · `cn`；Core 包含 `LocalAreaNetwork` · `ChinaDomain` · `ChinaIp` · `ChinaIpV6` · `GoogleCN` · `SteamCN` · `Apple` · `Microsoft` · `fakeip-filter` · `private` · `cn`；Nano 包含 `LocalAreaNetwork` · `ProxyLite` · `ChinaDomain` · `ChinaIp` · `ChinaIpV6`。
- [Koolson/Qure](https://github.com/Koolson/Qure)：策略组图标

## 贡献

如有改进建议或发现规则集变更，欢迎提交 Issue 或 Pull Request。
