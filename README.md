<h1 align="center">Sift</h1>

<p align="center">
面向通用代理内核的无节点分流模板 — 只提供策略组、远程规则和分流顺序，不内置节点。
</p>

<p align="center">
  <img alt="Core" src="https://img.shields.io/badge/core-compatible-blue">
  <img alt="Rules" src="https://img.shields.io/badge/rules-mrs%2Flist-green">
  <img alt="Node Free" src="https://img.shields.io/badge/nodes-not%20included-lightgrey">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue">
</p>

## 模板

默认推荐 **综合主模板**（混合规则源 + MRS + 运行时加固）。单源特色模板在 `rules/variants/`。

### 综合主模板（默认）

| 文件 | 策略组 | 说明 |
| --- | ---: | --- |
| [`rules/full.yaml`](./rules/full.yaml) | 20 | 完整场景：DustinWin MRS 骨架 + MetaCubeX 品牌/GitHub/DNS MRS；含 DNS、嗅探、地区与服务组；`github`/`onedrive` 先于 `microsoft` |
| [`rules/core.yaml`](./rules/core.yaml) | 7 | 核心白名单：Apple/Microsoft 进全球直连；GitHub/OneDrive 先于 Microsoft 进节点选择；`MATCH → 漏网之鱼`（默认 `节点选择`） |
| [`rules/nano.yaml`](./rules/nano.yaml) | 6 | 极简：DustinWin MRS；广告 + proxy + 国内兜底；不接管 DNS |

```text
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/full.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/core.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/nano.yaml
```

### 单源变体（`rules/variants/`）

格式保持各源原样（DustinWin/ACL 的 `.list`、MetaCubeX 的 GEOSITE/GEOIP），已叠加测速 timeout、信息节点过滤、sniffer skip-domain、`prefer-h3: false`、provider `proxy: DIRECT` 等加固。

| 路径 | 说明 |
| --- | --- |
| [`variants/DustinWin-*.yaml`](./rules/variants/) | DustinWin text + blackmatrix7 classical 品牌 |
| [`variants/MetaCubeX-*.yaml`](./rules/variants/) | 纯 GEOSITE/GEOIP，无 routing rule-providers |
| [`variants/ACL4SSR-*.yaml`](./rules/variants/) | ACL4SSR `.list`；Full 分服务流媒体；UnBan+Ban 广告链 |

> 旧路径 `rules/DustinWin-full.yaml` 等已迁移到 `rules/variants/`，请更新 raw 链接。

## 设计要点

- **无节点**：模板不含 `proxies`，节点由订阅合并或本地配置补充。
- **综合主模板**：DustinWin MRS（ads/proxy/cn-lite/场景等）+ MetaCubeX geosite MRS（google/apple/microsoft/onedrive/github + DNS cn）；不绑定单一上游。
- **单源变体**：`variants/DustinWin-*` 用 text/classical list；`variants/MetaCubeX-*` 用 GEOSITE/GEOIP；`variants/ACL4SSR-*` 用 ACL Clash list。
- **运行优化**：Full/Core 启用 `unified-delay`、`tcp-concurrent`、`prefer-h3: false`；url-test 含 `timeout: 3000`；include-all 组过滤订阅残渣文案；GeoIP 数据固定使用 MetaCubeX `geoip.metadb`（MMDB，24 小时自动更新）。
- **状态持久化**：Full / Core 及其 MetaCubeX / ACL4SSR 版本默认保存策略组选择和 fake-ip 映射，重启后保留手动选择并减少 fake-ip 映射变化带来的连接抖动。
- **DNS 分模板**：Nano 不接管 DNS；Full/Core 用 fake-IP **白名单**。明确代理/国内域名由 `nameserver-policy` 分别指定海外/国内 DoH；未分类域名默认只使用海外 DoH，不启用并发 `fallback`。海外 DoH（代理域 policy + 默认 `nameserver`）经可手动切换的 `DNS`（默认 `DIRECT`，可改总控/测速/手动节点）；国内 DoH（`cn`/`private` policy 与 `direct-nameserver`）固定直连，不随该组改道；代理节点域名由 `proxy-server-nameserver` 直连解析，避免建立代理前的循环依赖。主模板与 DustinWin/ACL 变体用 `rule-set:proxy`；MetaCubeX 变体用 `geosite:geolocation-!cn` + `geosite:google`。
- **广告拦截可回退**：所有模板提供 `广告拦截`（默认 REJECT）。主模板与 DustinWin 变体用 `ads`；MetaCubeX 用 `category-ads-all`；ACL 用 UnBan + BanAD/BanProgramAD。
- **域名嗅探**：Full/Core 启用 sniffer，并 `skip-domain` 跳过 lan/local/米家/Windows 连通性/Apple Push 等。
- **双层节点选择**：`节点选择` 作为日常总控入口，`手动切换` 才展开全部节点，节点多时面板更清爽。
- **可切换直连**：Full / Nano 的国内服务与国内兜底默认进入 `全球直连`，保持直连优先，同时允许临时切到总控或自动策略排障；Core 的 `全球直连` 保留 `DIRECT`、`节点选择` 与 `自动测速`，且 `DIRECT` 排第一。
- **兜底出口**：Full / Core / Nano 未命中规则均进入 `漏网之鱼`（默认 `节点选择`，可改测速/手动/直连）。
- **Full 场景分流**：主模板保留 AI/流媒体/游戏/Telegram/苹果/谷歌/微软/OneDrive 与地区组；`github` 与 `onedrive` 先于过宽的 `microsoft`；`google` 与 `proxy` 先于 `cn-lite`。
- **Core 白名单分流**：无服务/地区 UI；主模板 Apple/Microsoft → 全球直连，GitHub/OneDrive → 节点选择（均在 microsoft 前），proxy 在 cn-lite 前，`MATCH → 漏网之鱼`。
- **Nano 极简代理**：主模板 DustinWin MRS（ads + proxy + cn-lite/cnip）；无 DNS/嗅探/地区/服务组。

## 分流顺序

### 综合主模板 / Full（默认）

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 广告域名（`ads`） | `广告拦截`（默认 `REJECT`，可切 `DIRECT` / `节点选择`） |
| 3 | BT Tracker | `全球直连` |
| 4 | 国内 Apple / Microsoft / 游戏 | `全球直连` |
| 5 | Apple 海外服务 | `苹果服务` |
| 6 | AI 服务 | `AI` |
| 7 | 游戏平台 | `游戏平台` |
| 8 | 流媒体 IP | `流媒体` |
| 9 | OneDrive 网盘 | `OneDrive` |
| 10 | Microsoft 海外服务 | `微软服务` |
| 11 | Telegram IP | `Telegram` |
| 12 | Google 服务 | `谷歌服务` |
| 13 | 明确非中国域名（`proxy`） | `节点选择` |
| 14 | 国内域名 / IPv4 / IPv6 兜底 | `全球直连` |
| 15 | 未命中流量 | `漏网之鱼` |

### MetaCubeX / Full

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 广告域名（`category-ads-all`） | `广告拦截`（默认 `REJECT`，可切 `DIRECT` / `节点选择`） |
| 3 | GitHub / Copilot | `节点选择` |
| 4 | 中国区 Apple / Microsoft / 游戏 | `全球直连` |
| 5 | Apple 海外服务 | `苹果服务` |
| 6 | AI 服务 | `AI` |
| 7 | 游戏平台 / 游戏下载 | `游戏平台` |
| 8 | 娱乐 / 流媒体大类 | `流媒体` |
| 9 | OneDrive 网盘 | `OneDrive` |
| 10 | Microsoft 海外服务 | `微软服务` |
| 11 | Telegram IP | `Telegram` |
| 12 | Google 服务 | `谷歌服务` |
| 13 | 明确非中国域名 | `节点选择` |
| 14 | 国内域名 / IP 兜底 | `全球直连` |
| 15 | 未命中流量 | `漏网之鱼` |

### ACL4SSR / Full

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | `UnBan` 放行后，`BanAD` / `BanProgramAD` 广告域名 | `广告拦截`（默认 `REJECT`，可切 `DIRECT` / `节点选择`） |
| 3 | 中国区 Google / Steam | `全球直连` |
| 4 | Apple 服务 | `苹果服务` |
| 5 | AI 服务 | `AI` |
| 6 | Steam / Epic / Origin / Sony / Xbox / Nintendo | `游戏平台` |
| 7 | YouTube / Netflix(+IP) / Disney+ / Spotify / TikTok | `流媒体` |
| 8 | OneDrive 网盘 | `OneDrive` |
| 9 | Microsoft 服务 | `微软服务` |
| 10 | Telegram | `Telegram` |
| 11 | Google 服务 | `谷歌服务` |
| 12 | ProxyLite 明确代理域名 | `节点选择` |
| 13 | 国内域名 / IPv4 / IPv6 规则集兜底 | `全球直连` |
| 14 | 未命中流量 | `漏网之鱼` |

### DustinWin / Core

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 广告域名（`ads`） | `广告拦截`（默认 `REJECT`，可切 `DIRECT` / `节点选择`） |
| 3 | 完整 Apple | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 4 | OneDrive | `节点选择`（须在 Microsoft 前） |
| 5 | 完整 Microsoft | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 6 | 国内游戏 | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 7 | 明确非中国域名（`proxy`） | `节点选择` |
| 8 | 国内域名 / IP 兜底 | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 9 | 未命中流量 | `漏网之鱼` |

### MetaCubeX / Core

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 广告域名（`category-ads-all`） | `广告拦截`（默认 `REJECT`，可切 `DIRECT` / `节点选择`） |
| 3 | GitHub / Copilot | `节点选择` |
| 4 | 游戏中国区补充 / 完整 Apple | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 5 | OneDrive | `节点选择`（须在 Microsoft 前） |
| 6 | 完整 Microsoft | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 7 | 明确非中国域名 | `节点选择` |
| 8 | Google 路由例外（`.cn` 全球服务） | `节点选择` |
| 9 | 国内域名 / IP 兜底 | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 10 | 未命中流量 | `漏网之鱼` |

### ACL4SSR / Core

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | `UnBan` 放行后，`BanAD` / `BanProgramAD` 广告域名 | `广告拦截`（默认 `REJECT`，可切 `DIRECT` / `节点选择`） |
| 3 | 中国区 Google / Steam | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 4 | 完整 Apple | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 5 | OneDrive | `节点选择`（须在 Microsoft 前） |
| 6 | 完整 Microsoft | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 7 | ProxyLite 明确代理域名 | `节点选择` |
| 8 | 国内域名 / IPv4 / IPv6 规则集兜底 | `全球直连`（默认 `DIRECT`，可切 `节点选择` / `自动测速`） |
| 9 | 未命中流量 | `漏网之鱼` |

### DustinWin / Nano

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 广告域名（`ads`） | `广告拦截`（默认 `REJECT`，可切 `DIRECT` / `节点选择`） |
| 3 | 明确非中国域名（`proxy`） | `节点选择` |
| 4 | 国内域名 / IPv4 / IPv6 兜底 | `全球直连` |
| 5 | 未命中流量 | `漏网之鱼` |

### MetaCubeX / Nano

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 广告域名（`category-ads-all`） | `广告拦截`（默认 `REJECT`，可切 `DIRECT` / `节点选择`） |
| 3 | 明确非中国域名 | `节点选择` |
| 4 | Google 路由例外（`.cn` 全球服务） | `节点选择` |
| 5 | 国内域名 / IPv4 / IPv6 / GEOIP CN 兜底 | `全球直连` |
| 6 | 未命中流量 | `漏网之鱼` |

### ACL4SSR / Nano

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | `UnBan` 放行后，`BanAD` / `BanProgramAD` 广告域名 | `广告拦截`（默认 `REJECT`，可切 `DIRECT` / `节点选择`） |
| 3 | ProxyLite 明确代理域名 | `节点选择` |
| 4 | 国内域名 / IP 兜底 | `全球直连` |
| 5 | 未命中流量 | `漏网之鱼` |

## 策略组

**Full / MetaCubeX Full / ACL4SSR Full**：`节点选择` · `手动切换` · `自动测速` · `DNS` · `AI` · `流媒体` · `游戏平台` · `Telegram` · `苹果服务` · `谷歌服务` · `微软服务` · `OneDrive` · `香港节点` · `美国节点` · `日本节点` · `新加坡节点` · `其他节点` · `全球直连` · `广告拦截` · `漏网之鱼`

**Core / MetaCubeX Core / ACL4SSR Core**：`节点选择` · `手动切换` · `自动测速` · `DNS` · `全球直连` · `广告拦截` · `漏网之鱼`

**Nano / MetaCubeX Nano / ACL4SSR Nano**：`节点选择` · `手动切换` · `自动测速` · `全球直连` · `广告拦截` · `漏网之鱼`

`广告拦截` 默认选择 `REJECT`。遇到疑似误伤时，可临时切换为 `DIRECT`；若目标本身需要代理，则切换为 `节点选择`。该开关会临时放行整份广告列表，确认具体误伤域名后建议恢复 `REJECT`。

> Full 的地区组依赖节点名称中的地区关键词自动归类。建议节点命名包含 `HK`、`日本`、`US` 等标识。

## 规则来源

`DustinWin-*` 模板的远程规则集主要由 [DustinWin/ruleset_geodata](https://github.com/DustinWin/ruleset_geodata) 提供，通常使用 `format: text` 的 `.list` 以提高客户端兼容性；三档模板都使用 DustinWin `ads`（anti-AD）进入 `广告拦截`。海外 Apple / Microsoft / OneDrive 取自 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)，使用 classical/text 的 `.list`：`apple` = `rule/Clash/Apple/Apple.list`；`microsoft` = `rule/Clash/Microsoft/Microsoft.list`；`onedrive` = `rule/Clash/OneDrive/OneDrive.list`。明确非中国域名使用 DustinWin `proxy`（`geolocation-!cn` + gfwlist），位阶对齐 MetaCubeX `GEOSITE,geolocation-!cn`：路由放在场景/品牌规则之后、`cn-lite` 之前，DNS 中同时用作 fake-IP 白名单，避免 `googleapis.cn` 等在防火墙层被中国 IP 旁路。

DNS 使用 fake-IP 白名单模式：DustinWin 用 `rule-set:proxy`，ACL4SSR 用 DNS-only DustinWin `proxy`，MetaCubeX 用 `geosite:geolocation-!cn` + `geosite:google`。未列入的兼容、私有、Tracker 和国内域名自然返回 real-IP，不再需要 `fakeip-filter` / `trackerslist` provider。`nameserver-policy` 将明确代理域名交给海外 DoH、将 cn + private 交给国内 DoH；未分类域名默认只查询海外 DoH，不再并发请求国内解析器。仅海外 DoH 通过 `#DNS` 绑定策略组（默认 `DIRECT`，可改总控/测速/手动节点）；国内 DoH（`cn`/`private` policy 与 `direct-nameserver`）固定直连，不随该组改道。`proxy-server-nameserver` 继续直连解析代理节点地址，避免 DNS 依赖尚未建立的代理连接。路由国内兜底仍用 `cn-lite` / ACL4SSR `ChinaDomain` / `GEOSITE,cn`。

- **DustinWin-full**：`private` · `privateip` · `ads`（进入 `广告拦截`）· `trackerslist`（DNS-only real-IP，不参与路由）· `google`（blackmatrix7，进入 `谷歌服务`）· `apple-cn` · `apple`（blackmatrix7）· `microsoft-cn` · `microsoft`（blackmatrix7）· `onedrive`（blackmatrix7）· `games-cn` · `ai` · `mediaip` · `games` · `telegramip` · `proxy`（明确非中国域名，进入 `节点选择`）· `cn-lite`（路由直连）· `cnip` · `fakeip-filter` · `cn`（MetaCubeX `cn.mrs`，DNS real-IP + policy）
- **DustinWin-core**：`private` · `privateip` · `ads`（进入 `广告拦截`）· `apple`（blackmatrix7，完整 Apple 规则，仅用于路由）· `onedrive`（blackmatrix7，进入 `节点选择`，须在 `microsoft` 前）· `microsoft`（blackmatrix7，完整 Microsoft 规则，仅用于路由）· `games-cn` · `proxy`（明确非中国域名，进入 `节点选择`）· `cn-lite`（路由直连）· `cnip` · `trackerslist`（DNS-only real-IP）· `fakeip-filter` · `cn`（MetaCubeX `cn.mrs`，DNS real-IP + policy）
- **DustinWin-nano**：`private` · `privateip` · `ads`（进入 `广告拦截`）· `proxy` · `cn-lite`（路由直连）· `cnip`
- **MetaCubeX-***：路由使用 [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat) 的 `geoip.dat`、`geosite.dat`、`geoip.metadb`；`rules` 中只使用 `GEOSITE` / `GEOIP`，不使用 `RULE-SET`。MetaCubeX GeoSite 当前没有 `trackerslist` 标签，因此 Full/Core 为 DNS 定义 DustinWin `fakeip-filter` 与 `trackerslist` 两个 DNS-only provider，后者仅返回 real-IP；国内层用 `geosite:cn` / `geosite:private`。三档模板均在私有规则后用 `GEOSITE,category-ads-all,广告拦截`；Full 将 `GEOSITE,google` 导入 `谷歌服务`（在 `geolocation-!cn` 前）；Core/Nano 用 `GEOSITE,google,节点选择` 夹在 `geolocation-!cn` 与 `cn` 之间。Google/Play 硬锚点是 **`googleapis.cn`** 与 **`play.googleapis.com`**（须代理；DNS 白名单 + 路由）；`GEOSITE,google` / DNS `geosite:google` 主要保证 `googleapis.cn` 不被宽 `cn` 直连（`play.googleapis.com` 已在 `geolocation-!cn`）。`gstatic.cn` 不作硬合同。`GEOSITE,github,节点选择` 放在广告层之后的高优先级位置；Core 在 `GEOSITE,microsoft` 前将 `GEOSITE,onedrive` 导入 `节点选择`（无 OneDrive UI 组）；`GEOIP,CN` 与 `GEOIP,telegram` 不追加 `no-resolve`。
- **ACL4SSR-***：路由使用 [ACL4SSR/ACL4SSR](https://github.com/ACL4SSR/ACL4SSR) 的 Clash `.list` 文件，并以 `classical`/`text` 接入；三档模板均以 `UnBan` 前置直连放行并将 `BanAD` / `BanProgramAD` 导入 `广告拦截`。国内 IP 仅由 `ChinaIp` / `ChinaIpV6` provider 兜底，不追加内置 `GEOIP,CN`。Full/Core 的 DNS 侧与 DustinWin 对齐：`fakeip-filter` / `private` / MetaCubeX `cn.mrs` 同时服务 real-IP 与国内 policy，`trackerslist` 只作为额外 real-IP 例外；路由国内域名仍用 `ChinaDomain`。Full 流媒体使用 ACL 分服务包 `YouTube` · `Netflix` · `NetflixIP` · `DisneyPlus` · `Spotify` · `TikTok`（不再使用 `ProxyMedia`）；`Google`（blackmatrix7）进入 `谷歌服务`；另含 `LocalAreaNetwork` · `ChinaDomain` · `ChinaIp` · `ChinaIpV6` · `GoogleCN` · `SteamCN` · `Apple` · `AI` · `Steam` · `Epic` · `Origin` · `Sony` · `Xbox` · `Nintendo` · `OneDrive` · `Microsoft` · `Telegram` · `ProxyLite` · `trackerslist`（DNS）· `fakeip-filter` · `private` · `cn`（DNS）。Core 包含 `LocalAreaNetwork` · `UnBan` · `BanAD` · `BanProgramAD` · `ChinaDomain` · `ChinaIp` · `ChinaIpV6` · `GoogleCN` · `SteamCN` · `Apple` · `OneDrive`（进入 `节点选择`，须在 `Microsoft` 前）· `Microsoft` · `trackerslist`（DNS）· `fakeip-filter` · `private` · `cn`（DNS）；Nano 包含 `LocalAreaNetwork` · `UnBan` · `BanAD` · `BanProgramAD` · `ProxyLite` · `ChinaDomain` · `ChinaIp` · `ChinaIpV6`。
- [Koolson/Qure](https://github.com/Koolson/Qure)：策略组图标

## 贡献

如有改进建议或发现规则集变更，欢迎提交 Issue 或 Pull Request。
