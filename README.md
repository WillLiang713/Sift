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

根目录模板继续使用远程 `.list` 规则集，兼顾通用 Mihomo / ShellCrash 兼容性：

| 文件 | 策略组 | 规则提供商 | 说明 |
| --- | ---: | ---: | --- |
| [`Full.yaml`](./Full.yaml) | 17 | 17 | 完整版：AI、流媒体、游戏平台、Telegram、Apple、Microsoft、OneDrive、地区节点；内置 fake-ip 分流 DNS、域名嗅探和状态持久化，并启用统一延迟与 TCP 并发连接 |
| [`Core.yaml`](./Core.yaml) | 4 | 10 | 核心白名单版：保留基础节点选择、国内白名单、DNS、域名嗅探和状态持久化；完整 Apple / Microsoft 进入 `全球直连`，且 Core 的 `全球直连` 只保留 `DIRECT` 与 `节点选择`，`DIRECT` 排第一 |
| [`Nano.yaml`](./Nano.yaml) | 5 | 5 | 极简版：局域网直连、GFW 代理、国内直连和兜底分流；不接管 DNS |

```text
https://raw.githubusercontent.com/WillLiang713/Sift/main/Full.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/Core.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/Nano.yaml
```

`geodata/` 目录提供 `GEOSITE` / `GEOIP` 路由写法，使用 MetaCubeX `meta-rules-dat`；Full/Core 仅为 DNS fake-ip 兼容补充一个 `fakeip-filter` domain provider：

| 文件 | 策略组 | 规则提供商 | 说明 |
| --- | ---: | ---: | --- |
| [`geodata/Full.yaml`](./geodata/Full.yaml) | 17 | 1 | Geodata 完整版：保留 Full 的策略组结构，路由使用 `category-ai-!cn`、`category-games`、`category-entertainment`、Google、Apple / Microsoft / OneDrive 等 geosite 分流；游戏规则放在娱乐大类之前，避免游戏平台被流媒体抢先命中；DNS 侧额外引用 `fakeip-filter` |
| [`geodata/Core.yaml`](./geodata/Core.yaml) | 4 | 1 | Geodata 核心白名单版：完整 Apple、Microsoft 中国区补充与国内白名单进入 `全球直连`，Google / Google Play 在国内兜底前进入 `节点选择`，未命中流量直接进入 `节点选择`；DNS 侧额外引用 `fakeip-filter` |
| [`geodata/Nano.yaml`](./geodata/Nano.yaml) | 5 | 0 | Geodata 极简版：局域网、GFW、国内域名/IP 与兜底分流；不接管 DNS |

```text
https://raw.githubusercontent.com/WillLiang713/Sift/main/geodata/Full.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/geodata/Core.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/geodata/Nano.yaml
```

## 设计要点

- **无节点**：模板不含 `proxies`，节点由订阅合并或本地配置补充。
- **两套路由写法**：根目录模板使用 DustinWin / blackmatrix7 远程 `.list` 规则集；`geodata/` 模板的路由规则使用 MetaCubeX `GEOSITE` / `GEOIP`，适合希望内置 geodata 统一管理规则的客户端。
- **运行优化**：Full / Core 及其 Geodata 版本默认启用 `unified-delay` 和 `tcp-concurrent`，减少 Reality 等节点测速虚高，并提升多 IP 目标的连接成功率。
- **状态持久化**：Full / Core 及其 Geodata 版本默认保存策略组选择和 fake-ip 映射，重启后保留手动选择并减少 fake-ip 映射变化带来的连接抖动。
- **DNS 分模板**：Nano / `geodata/Nano.yaml` 不接管 DNS，留给客户端本地管理；Full / Core 内置 fake-ip 分流 DNS，Geodata 版本用 `rule-set:fakeip-filter` 补充兼容例外，并用 `geosite:cn,private` 做国内/私有 DNS policy。
- **域名嗅探**：Full / Core 及其 Geodata 版本启用 `sniffer`，从 HTTP Host、TLS SNI 和 QUIC 握手中提取域名，提升 TUN / redir-host / 纯 IP 场景下的规则命中准确率。
- **双层节点选择**：`节点选择` 作为日常总控入口，`手动切换` 才展开全部节点，节点多时面板更清爽。
- **可切换直连**：Full / Nano 的国内服务与国内兜底默认进入 `全球直连`，保持直连优先，同时允许临时切到总控或自动策略排障；Core 的 `全球直连` 只保留 `DIRECT` 与 `节点选择`，且 `DIRECT` 排第一。
- **兜底出口**：Full / Nano 未命中规则进入 `漏网之鱼`；Core 不保留独立兜底组，未命中规则直接进入 `节点选择`。
- **Full 场景分流**：完整模板保留 AI、流媒体、游戏平台、Telegram、Apple、Microsoft、OneDrive 等独立入口。Geodata Full 中游戏规则优先级高于 `category-entertainment`，避免游戏域名被娱乐/流媒体大类提前接走。
- **Core 白名单分流**：核心模板不保留服务 UI 分组和地区节点组；完整 Apple / Microsoft 规则和国内白名单进入 `全球直连`，该组默认 `DIRECT`、可切到 `节点选择`，其余流量全部交给 `MATCH,节点选择`。
- **Nano 极简代理**：极简模板只保留 GFW 代理、国内直连和兜底，不提供地区节点或服务分组。

## 分流顺序

### Full

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | Google / Google Play | `节点选择` |
| 3 | 国内 Apple / Microsoft / 游戏 | `全球直连` |
| 4 | Apple 海外服务 | `苹果服务` |
| 5 | AI 服务 | `AI` |
| 6 | 游戏平台 | `游戏平台` |
| 7 | 流媒体 IP | `流媒体` |
| 8 | OneDrive 网盘 | `OneDrive` |
| 9 | Microsoft 海外服务 | `微软服务` |
| 10 | Telegram IP | `Telegram` |
| 11 | 国内域名 / IP 兜底 | `全球直连` |
| 12 | 未命中流量 | `漏网之鱼` |

### Geodata / Full

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 中国区 Apple / Microsoft / 游戏 | `全球直连` |
| 3 | AI 服务 | `AI` |
| 4 | 游戏平台 / 游戏下载 | `游戏平台` |
| 5 | 娱乐 / 流媒体大类 | `流媒体` |
| 6 | OneDrive / Microsoft / Apple 海外服务 | 对应服务组 |
| 7 | Telegram IP | `Telegram` |
| 8 | Google / Google Play | `节点选择` |
| 9 | 明确非中国域名 | `节点选择` |
| 10 | 国内域名 / IP 兜底 | `全球直连` |
| 11 | 未命中流量 | `漏网之鱼` |

### Core

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | Google / Google Play | `节点选择` |
| 3 | 国内游戏 | `全球直连`（默认 `DIRECT`，可切 `节点选择`） |
| 4 | 完整 Apple / Microsoft | `全球直连`（默认 `DIRECT`，可切 `节点选择`） |
| 5 | 国内域名 / IP 兜底 | `全球直连`（默认 `DIRECT`，可切 `节点选择`） |
| 6 | 未命中流量 | `节点选择` |

### Geodata / Core

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 完整 Apple / Microsoft 中国区 / 游戏中国区补充 | `全球直连`（默认 `DIRECT`，可切 `节点选择`） |
| 3 | Google / Google Play | `节点选择` |
| 4 | 国内域名 / IP 兜底 | `全球直连`（默认 `DIRECT`，可切 `节点选择`） |
| 5 | 未命中流量 | `节点选择` |

### Nano

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | GFW 代理规则命中 | `节点选择` |
| 3 | 国内域名 / IP 兜底 | `全球直连` |
| 4 | 未命中流量 | `漏网之鱼` |

## 策略组

**Full / geodata Full**：`节点选择` · `手动切换` · `自动测速` · `AI` · `流媒体` · `游戏平台` · `Telegram` · `苹果服务` · `微软服务` · `OneDrive` · `香港节点` · `美国节点` · `日本节点` · `新加坡节点` · `其他节点` · `全球直连` · `漏网之鱼`

**Core / geodata Core**：`节点选择` · `手动切换` · `自动测速` · `全球直连`

**Nano / geodata Nano**：`节点选择` · `手动切换` · `自动测速` · `全球直连` · `漏网之鱼`

> Full 的地区组依赖节点名称中的地区关键词自动归类。建议节点命名包含 `HK`、`日本`、`US` 等标识。

## 规则来源

根目录模板的远程规则集主要由 [DustinWin/ruleset_geodata](https://github.com/DustinWin/ruleset_geodata) 提供，统一使用 `format: text` 的 `.list` 以提高客户端兼容性；完整 Google 以及海外 Apple / Microsoft / OneDrive 取自 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)，使用 classical/text 的 `.list`（DustinWin 均无对应完整集，路径均不含 `geosite`/`geoip`）：`google` = `rule/Clash/Google/Google.list`；`apple` = `rule/Clash/Apple/Apple.list`；`microsoft` = `rule/Clash/Microsoft/Microsoft.list`；`onedrive` = `rule/Clash/OneDrive/OneDrive.list`（google / microsoft / onedrive 必须 classical 才能保住 keyword / IP / process 规则）。

DNS 的 `fake-ip-filter` / `nameserver-policy` 只引用国内 DNS 入口；`*-cn` 规则只表达路由直连意图，不代表一定适合国内 DNS 解析。blackmatrix7 的完整 Google / Apple / Microsoft / OneDrive classical 规则只用于路由分流，避免其中的 `PROCESS-NAME` 等规则类型进入 DNS 过滤。

- **Full**：`private` · `privateip` · `google`（blackmatrix7）· `apple-cn` · `apple`（blackmatrix7）· `microsoft-cn` · `microsoft`（blackmatrix7）· `onedrive`（blackmatrix7）· `games-cn` · `ai` · `mediaip` · `games` · `telegramip` · `cn-lite`（路由直连）· `cn`（DNS 国内解析）· `cnip` · `fakeip-filter`（仅供 `dns.fake-ip-filter`）
- **Core**：`private` · `privateip` · `google`（blackmatrix7，完整 Google 规则，进入 `节点选择`）· `apple`（blackmatrix7，完整 Apple 规则，仅用于路由）· `microsoft`（blackmatrix7，完整 Microsoft 规则，仅用于路由）· `games-cn` · `cn-lite`（路由直连）· `cn`（DNS 国内解析）· `cnip` · `fakeip-filter`（仅供 `dns.fake-ip-filter`）
- **Nano**：`private` · `privateip` · `gfw` · `cn-lite`（路由直连）· `cnip`
- **geodata/**：路由使用 [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat) 的 `geoip.dat`、`geosite.dat`、`geoip.metadb`；`rules` 中只使用 `GEOSITE` / `GEOIP`，不使用 `RULE-SET`。Full/Core 仅为 `dns.fake-ip-filter` 定义 `fakeip-filter`（DustinWin，DNS-only）；不再把 `google@cn` 作为直连补充，改用 `GEOSITE,google,节点选择` 放在 `GEOSITE,cn` 前，避免 Google Play / Android 连通性域名被国内兜底送入直连；`GEOIP,CN` 与 `GEOIP,telegram` 不追加 `no-resolve`，保留常规域名解析后的 IP 分流行为。
- [Koolson/Qure](https://github.com/Koolson/Qure)：策略组图标

## 贡献

如有改进建议或发现规则集变更，欢迎提交 Issue 或 Pull Request。
