# Repository Guidelines

面向 agent / 维护者的仓库规范。先读**主文**；改规则或 DNS 时再查**附录**。用户可见行为以 `README.md` 为准。

---

## 这是什么

Sift 是 **Mihomo 无节点分流模板**仓库：只提供策略组、远程规则与分流顺序，不内置订阅/节点。

- **默认推荐**：根目录 hybrid 主模板（多源混合 + 优先 MRS）。
- **可选**：`rules/variants/` 单源变体（保留各源原格式，不强行 MRS）。

---

## 目录一览

| 路径 | 用途 |
| --- | --- |
| `rules/full.yaml` / `core.yaml` / `nano.yaml` | 默认 hybrid 主模板 |
| `rules/variants/` | DustinWin / MetaCubeX / ACL4SSR 单源变体 |
| `demo/` | 对照示例 |
| `docs/` | 专题说明（索引见下；**按需**打开，勿整目录通读） |
| `README.md` | 用户文档（分流/策略组变更时必须同步） |
| `.agents/skills/sift-route-debug/` | 路由矩阵与诊断脚本 |

### docs 索引（按需读）

主文与附录已覆盖分流/DNS **合同**；下列文件是展开说明或环境笔记。改相关主题时再读对应篇，不要默认全读。

| 文件 | 何时读 | 内容 |
| --- | --- | --- |
| [`docs/dns.md`](./docs/dns.md) | 改 Full/Core DNS、fake-IP、`#DNS` 出口、防泄露 | 本仓库模板 DNS 分工与白名单约定 |
| [`docs/dns-flow.md`](./docs/dns-flow.md) | 排查「先规则后解析」、理解 Mihomo 何时才做 DNS | 上游 DNS 解析流程摘要 |
| [`docs/rulesets.md`](./docs/rulesets.md) | 换源/选型规则集、查上游有哪些 list/mrs | DustinWin / blackmatrix7 / ACL 等目录参考（**体积大**，按关键词搜） |
| [`docs/icons.md`](./docs/icons.md) | 改策略组 `icon` | Vbaethon/HOMOMIX CDN 路径与映射表 |
| [`docs/anti-ad.md`](./docs/anti-ad.md) | 路由器 DNS 层 anti-AD | ImmortalWrt / OpenClash dnsmasq 去广告 |
| [`docs/openwrt.md`](./docs/openwrt.md) | 家用网 / 旁路 / OpenWrt 调优背景 | 恩山帖笔记摘要 |
| [`docs/f50-ipv6.md`](./docs/f50-ipv6.md) | 中兴 F50 + ImmortalWrt IPv6 | 移动 SIM 场景 IPv6 复用配置 |

与模板契约冲突时：**以本文件主文 + 附录 + 当前 yaml 为准**；`docs/*` 仅作背景与操作笔记。

---

## 三档模板（产品合同）

| | Full | Core | Nano |
| --- | --- | --- | --- |
| 代表文件 | `rules/full.yaml` | `rules/core.yaml` | `rules/nano.yaml` |
| UI 策略组 | 场景 + 品牌 + 地区 + DNS + 广告 | 基础组 + `苹果服务` + `微软服务` + `DNS` + `直连` + 广告 | 极简 + 广告 |
| DNS / sniffer | 有 | 有 | **无** |
| Apple / Microsoft | 独立服务组（Full） | 独立服务组（默认 `直连`） | 无独立组 |
| OneDrive | `OneDrive` 组 | `OneDrive` 组 | 无 |
| GitHub | `GitHub` 组 | `GitHub` 组 | 无 |
| 未命中 | `漏网之鱼` | `漏网之鱼` | `漏网之鱼` |

模板不含独立广告拦截组（40f3bf7 起移除），广告域由各源国内/Google 集自然落入 `直连` / `节点选择`。`漏网之鱼` 统一默认选择 `节点选择`。

**不要随意扩档位**：

- Core：保留 Apple/Microsoft 服务组，外加 GitHub / OneDrive 独立组；不要添加其他服务/品牌 UI 或地区节点组（`漏网之鱼` 兜底组已纳入 Core 合同，成员对齐 Nano）。
- Nano：不要加 DNS、场景组、品牌/地区组（除非明确改 Nano 定位）。

常用组名保持稳定：`节点选择`、`手动切换`、`自动测速`、`DNS`、`直连`、`漏网之鱼`；服务类组名 `苹果服务`、`微软服务`、`OneDrive`、`GitHub`。

---

## 改规则时的硬约束（先看这里）

规则**自上而下，先命中先生效**。重叠时更具体 / 更高意图的写在前面。

### 1. 必须守住的顺序

| 顺序 | 原因（人话） |
| --- | --- |
| `github`、`onedrive` **在** `microsoft` **前** | Microsoft 集合过宽，会吞掉 GitHub / OneDrive |
| `google`、`proxy`（或 `geolocation-!cn`）**在** `cn-lite` / 宽 `cn` **前** | 否则 `googleapis.cn` 等会被国内直连误伤 |
| 游戏相关 **在** 娱乐分类前（MetaCubeX Full） | `category-entertainment` 与游戏重叠 |

### 2. Google / Play 产品锚点

硬锚点（必须代理；回归以此为准）：

- `googleapis.cn`
- `play.googleapis.com`

出口约定：Full → `谷歌服务`；Core / Nano → `节点选择`；Full/Core DNS fake-IP 白名单须覆盖。

- `gstatic.cn` **不是**硬锚点（展示可以，失败不判契约破）。
- 默认**不要**加 `google@cn → 直连`（Play/API 国内直连易挂）。

### 3. DNS（仅 Full/Core）

| 原则 | 做法 |
| --- | --- |
| 默认解析 | 海外 DoH（`nameserver`） |
| 明确国内/内网 | `nameserver-policy` → 国内 DoH（`cn` + `private`） |
| 明确代理域 | policy → 海外 DoH（见附录 B） |
| DNS 出口 | 仅海外 DoH 用 `#DNS`（默认 `节点选择`）；国内 DoH / `direct-nameserver` 固定直连 |
| **禁止** | 并发 `fallback` / `fallback-filter`（会把未分类域名也扔给国内解析器） |
| fake-IP | **白名单**模式；名单外（国内、Tracker 等）自然真 IP |
| GeoIP | `geodata-mode: false` + MetaCubeX `geoip.metadb`，24h 自动更新 |

**禁止**：

- 把 `trackerslist` 写回 `dns.fake-ip-filter` 或加路由 `RULE-SET,trackerslist,...`
- 用宽 `cn`（完整 DustinWin `cn.list` / DNS 用的 MetaCubeX `cn`）替换路由 `cn-lite`
- 提交订阅链接、节点、密钥、含私有端点的生成配置

### 4. Full/Core 运行时加固（保持一致）

`prefer-h3: false`、sniffer `skip-domain`、url-test `timeout: 3000`、信息节点 `exclude-filter`、rule-provider `proxy: DIRECT`。

Full 的 `其他节点`：`exclude-filter` 必须是各地区组 `filter` 的**精确并集**（含 emoji 与 `(?i)`）。

### 5. 范围外

不修 ShellCrash 对 URL 里 `geosite`/`geoip` 子串的误判；MetaCubeX `meta-rules-dat` 路径在源正确时允许使用。

---

## 验证

无构建步骤。提交前尽量：

```bash
mihomo -t -f rules/full.yaml   # 同步检查 core/nano 与 variants
yamllint rules/*.yaml rules/variants/*.yaml demo/*.yaml
git diff --check
```

- MetaCubeX 变体：路由只能是 `GEOSITE`/`GEOIP`，**不能**出现 `rule-providers:`。
- 路由矩阵 / 域名诊断：见 skill `sift-route-debug`。

YAML：两空格缩进；按意图分块并加短注释。

---

## 提交与 PR

- Conventional Commits，可带 scope：`config` / `rules` / `docs` / `scripts`（中英摘要均可）。
- PR 写清：分流行为变化、验证命令、对旧客户端的兼容风险；模板改动注明影响 hybrid 还是哪家 variants。
- 仅策略组 UI/顺序相关时才需要截图。

图标：远程引用默认 `Vbaethon/HOMOMIX`（`Icon/Color/Large`，jsDelivr）；新增图标须先确认上游 Large 文件存在（防 404），勿随意 vendoring 第三方图标/规则集（先核授权与署名）。

---

# 附录 A — 规则源与接线

## Hybrid 主模板（MRS 优先）

| 用途 | 来源 |
| --- | --- |
| 域名/IP 骨架（ads、proxy、cn-lite、场景等） | DustinWin `mihomo-ruleset/*.mrs` |
| 品牌 + github + **DNS-only** `cn` | MetaCubeX `meta/geo/geosite/*.mrs` |

主路径**不用** blackmatrix7 classical（classical 无法编进 MRS）。

## 单源变体（不强制 MRS）

| 变体 | 格式要点 |
| --- | --- |
| `DustinWin-*.yaml` | text `.list` + 品牌用 blackmatrix7 classical |
| `MetaCubeX-*.yaml` | 纯 `GEOSITE`/`GEOIP` + 顶层 `geox-url`，无 routing `rule-providers` |
| `ACL4SSR-*.yaml` | ACL Clash `.list`；DNS-only DustinWin `proxy`；UnBan+Ban 广告；Full 流媒体拆分 |

DustinWin / ACL 的 list 来自 [DustinWin/ruleset_geodata](https://github.com/DustinWin/ruleset_geodata)。  
DustinWin 无完整品牌集时，variants 可用 blackmatrix7：

| key | 上游 | 备注 |
| --- | --- | --- |
| `google` | `rule/Clash/Google/Google.list` | Full → `谷歌服务`；ACL Full 也用 |
| `apple` | `rule/Clash/Apple/Apple.list` | |
| `microsoft` | `rule/Clash/Microsoft/Microsoft.list` | 需 `classical`（含 keyword/IP/process） |
| `onedrive` | `rule/Clash/OneDrive/OneDrive.list` | 需 `classical` |

`rule-providers` 的 key 尽量与上游文件 basename 一致；blackmatrix7 路径大小写按上游。

## 非 CN 代理层

| 家族 | 提供者 | 位置 |
| --- | --- | --- |
| DustinWin（含 hybrid 骨架） | `proxy`（≈ geolocation-!cn + gfwlist） | 服务/品牌规则之后、`cn-lite` 之前 |
| MetaCubeX | `GEOSITE,geolocation-!cn` | 同上逻辑 |
| ACL4SSR Nano 等 | `ProxyLite` 等 | 见对应 yaml |

**路由**国内域名兜底用 `cn-lite`（DustinWin），不要换成完整 `cn`。  
MetaCubeX `cn.mrs` 在 DustinWin/ACL Full/Core 里仅作 **DNS `nameserver-policy`**，不进 routing 替代 `cn-lite`。

---

# 附录 B — DNS / fake-IP 细节

仅 Full/Core（含对应 variants）。

### fake-IP 白名单

| 家族 | 白名单 |
| --- | --- |
| Hybrid / DustinWin | `rule-set:proxy` |
| ACL4SSR | DNS-only 的 DustinWin `proxy`（路由仍用自家 China 域规则） |
| MetaCubeX | `geosite:geolocation-!cn` + `geosite:google` |

未进白名单的 private / CN / Tracker / 兼容域 → 真 IP。故无需、也不应再塞 `trackerslist`。

### nameserver-policy 两层

| 匹配 | 解析器 |
| --- | --- |
| 代理域：`proxy` 或 `geolocation-!cn,google` | 海外 DoH |
| 国内/内网：`cn,private` | 国内 DoH |

未命中 policy → 只用海外 `nameserver`。海外 DoH（默认 `nameserver` + 代理域 policy）绑定 `DNS`；国内 DoH（`cn`/`private` policy、`direct-nameserver`）与代理节点地址的 `proxy-server-nameserver` 均固定直连，避免国内解析被代理改道或启动环路。

`googleapis.cn` 等 `.cn` 代理域若误走 `cn` policy，会吃到污染或 CDN 锁定解析，故默认海外 + 代理域 policy 强制海外。

---

# 附录 C — 变体与模板特例

## DustinWin variants

**Full**：private 后立刻 `ads → 广告拦截`；`apple-cn` / `microsoft-cn` / `games-cn` 补国内直连；完整 apple/microsoft/onedrive/google 进服务组；`proxy` 在服务/场景后、`cn-lite` 前；`onedrive` 先于 `microsoft`；`google` 先于 `proxy`/`cn-lite`。

**Core**：完整 apple → `苹果服务`、microsoft → `微软服务`，两个服务组默认选择 `直连`；onedrive → `OneDrive`、github → `GitHub`（均默认 `节点选择`，onedrive 紧挨 microsoft 前）；`proxy` 在直连服务规则后、`cn-lite` 前；`直连` 成员顺序：`DIRECT`、`节点选择`、`自动测速`。不要默认加回「仅 CN 品牌补充」除非产品改回旧设计。

**Nano**：仅 `private` / `privateip` / `ads` / `proxy` / `cn-lite` / `cnip`；`ads` 在 `proxy` 前。

## MetaCubeX variants

**Full**：可见组对齐 hybrid Full，分类用 geosite。顺序要点：

1. private 后 `category-ads-all → 广告拦截`
2. 随即 `github → 节点选择`（避免被 microsoft/场景吞）
3. 完整 `apple → 苹果服务`（娱乐场景前）；`apple@cn` 国内直连补充
4. 游戏规则在 `category-entertainment` 前
5. 完整 `microsoft → 微软服务`；`microsoft@cn` 补充
6. `google → 谷歌服务`：场景/品牌之后、`geolocation-!cn` / `cn` 之前（YouTube 仍可先中娱乐）

**Core**：含 `DNS`、`苹果服务`、`微软服务`、`OneDrive`、`GitHub`、`直连` 与 `漏网之鱼`；Apple/Microsoft 分别进入对应服务组，两个服务组默认选择 `直连`；ads 后 github → `GitHub`（先于 microsoft/场景）；onedrive → `OneDrive` 紧挨 microsoft 前；`geolocation-!cn → 节点选择` 在直连服务后、`cn` 前；`MATCH,漏网之鱼`。

**Core/Nano Google**：`GEOSITE,google → 节点选择`（无 UI 组），放在 `geolocation-!cn` 后、`cn` 前。  
**说明**：`geolocation-!cn` 含 `play.googleapis.com` 但不含 `googleapis.cn`；`GEOSITE,google` / DNS `geosite:google` 主要是防止 `googleapis.cn` 掉进宽 CN 直连。

## ACL4SSR

广告链：UnBan + BanAD / BanProgramAD。Full 流媒体按源拆 list。DNS-only `proxy` 仅服务 fake-IP/policy，路由仍走 ACL 域规则 + 国内集。

---

# 附录 D — 速查：hybrid Full 意图链

与 `README` 分流表一致，改 yaml 时对照：

1. 局域网 / 私有 → `DIRECT`
2. 广告 → `广告拦截`
3. Tracker 等 → `直连`（按模板）
4. 国内 Apple / Microsoft / 游戏补充 → `直连`
5. 海外 Apple / AI / 游戏 / 流媒体 / OneDrive / Microsoft / TG / Google → 对应组
6. `proxy`（明确非 CN）→ `节点选择`
7. `cn-lite` / 国内 IP → `直连`
8. 其余 → `漏网之鱼`

细节与域名矩阵以当前 yaml + `sift-route-debug` 为准；本附录描述**意图**，不是逐行拷贝源。
