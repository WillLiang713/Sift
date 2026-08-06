# Repository Guidelines

面向 agent / 维护者的仓库规范。先读**主文**；改规则或 DNS 时再查**附录**。用户可见行为以 `README.md` 为准。

---

## 这是什么

Sift 是 **Mihomo 无节点分流模板**仓库：只提供策略组、远程规则与分流顺序，不内置订阅/节点。

- **唯一产品线**：Full / Core / Nano 三档 hybrid 模板（多源混合 + 优先 MRS）。

---

## 目录一览

| 路径 | 用途 |
| --- | --- |
| `rules/full.yaml` / `core.yaml` / `nano.yaml` | hybrid 三档主模板 |
| `demo/` | 对照示例 |
| `docs/` | 专题说明（索引见下；**按需**打开，勿整目录通读） |
| `README.md` | 用户文档（分流/策略组变更时必须同步） |
| `.agents/skills/sift-route-debug/` | 路由矩阵与诊断脚本 |

### docs 索引（按需读）

主文与附录已覆盖分流/DNS **合同**；下列文件是展开说明。改相关主题时再读对应篇，不要默认全读。

| 文件 | 何时读 | 内容 |
| --- | --- | --- |
| [`docs/dns.md`](./docs/dns.md) | 改 Full/Core DNS、fake-IP、`#节点选择` 出口、防泄露 | 本仓库模板 DNS 分工与白名单约定 |
| [`docs/dns-flow.md`](./docs/dns-flow.md) | 排查「先规则后解析」、理解 Mihomo 何时才做 DNS | 上游 DNS 解析流程摘要 |
| [`docs/rulesets.md`](./docs/rulesets.md) | 换源/选型规则集、查上游有哪些 list/mrs | DustinWin / blackmatrix7 / ACL 等目录参考（**体积大**，按关键词搜） |
| [`docs/icons.md`](./docs/icons.md) | 改策略组 `icon` | Vbaethon/HOMOMIX CDN 路径与映射表 |

与模板契约冲突时：**以本文件主文 + 附录 + 当前 yaml 为准**；`docs/*` 仅作背景与操作笔记。

---

## 三档模板（产品合同）

| | Full | Core | Nano |
| --- | --- | --- | --- |
| 代表文件 | `rules/full.yaml` | `rules/core.yaml` | `rules/nano.yaml` |
| UI 策略组 | 场景 + 品牌 + 地区 | 基础组 + `苹果服务` + `微软服务` + `全球直连` | 极简 |
| DNS / sniffer | 有 | 有 | **无** |
| Apple / Microsoft | 独立服务组（Full） | 独立服务组（默认 `全球直连`） | 无独立组 |
| 广告拦截 | Full/Core：`广告拦截` 组（默认 `REJECT`，可切 `PASS`） | 同左 | 无 |
| OneDrive | 无独立规则：域在 `微软服务` 集内（geosite microsoft） | 同左 | 无 |
| GitHub | Full：`GitHub` 组（`geosite/github` 规则前置）；Core：规则 → `节点选择` | Core 同左，无组 | 无 |
| 未命中 | `漏网之鱼` | `漏网之鱼` | `漏网之鱼` |

Full/Core 有 `广告拦截` 组（规则 `RULE-SET,ads` 置于最前，DustinWin `ads.mrs` 纯 domain；默认 `REJECT` 拦截，切 `PASS` 放行给后续规则）。Nano 无广告组，广告域自然落入兜底。`漏网之鱼` 统一默认选择 `节点选择`。

**不要随意扩档位**：

- Core：保留 Apple/Microsoft 服务组（GitHub / OneDrive 无独立组）；不要添加其他服务/品牌 UI 或地区节点组（`漏网之鱼` 兜底组已纳入 Core 合同，成员对齐 Nano）。
- Nano：不要加 DNS、场景组、品牌/地区组（除非明确改 Nano 定位）。

常用组名保持稳定：`节点选择`、`自动测速`、`全球直连`、`漏网之鱼`；Full 保留 `手动切换` 与 `GitHub` 组，Core/Nano 不提供该组；服务类组名 `苹果服务`、`微软服务`；广告类组名 `广告拦截`。`GitHub` 组（Full）：规则 `geosite/github` 置于 `microsoft` 前 → `GitHub` 组；Core 同规则 → `节点选择`。`OneDrive` 无独立组与规则，域在 `geosite microsoft` 内 → `微软服务`。Full/Core 不提供独立 DNS 策略组，海外 DoH 固定使用 `#节点选择`。

---

## 改规则时的硬约束（先看这里）

规则**自上而下，先命中先生效**。重叠时更具体 / 更高意图的写在前面。

### 1. 必须守住的顺序

| 顺序 | 原因（人话） |
| --- | --- |
| `github` **在** `microsoft` **前** | geosite microsoft 含 github（include:github），须先截走 GitHub → `节点选择` |
| `microsoft` **在** `proxy` 前 | geosite microsoft 承接 OneDrive 域（include:onedrive），先命中 `微软服务` |
| `google`、`proxy` **在** `cn-lite` 前 | 否则 `googleapis.cn` 等会被国内直连误伤 |
| Full 的服务域名、`proxy`、`cn-lite` **在** `mediaip` / `telegramip` / `cnip` 前 | 先完成域名分类，避免服务 IP 集提前触发解析；`privateip,no-resolve` 可保留在开头 |

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
| DNS 出口 | 仅海外 DoH 固定用 `#节点选择`；国内 DoH / `direct-nameserver` 固定直连 |
| **禁止** | 并发 `fallback` / `fallback-filter`（会把未分类域名也扔给国内解析器） |
| fake-IP | **白名单**模式；名单外（国内、Tracker 等）自然真 IP |
| GeoIP | 不依赖 geodata：路由与 DNS 全 RULE-SET（数据自带），不配 `geox-url`，无 GEOIP/GEOSITE 规则 |

**禁止**：

- 把 `trackerslist` 写回 `dns.fake-ip-filter` 或加路由 `RULE-SET,trackerslist,...`
- 用宽 `cn`（完整 DustinWin `cn.mrs` / DNS 用的 `cn`）替换路由 `cn-lite`
- 提交订阅链接、节点、密钥、含私有端点的生成配置

### 4. Full/Core 运行时加固（保持一致）

`prefer-h3: false`、sniffer `skip-domain`、url-test `timeout: 3000` + `expected-status: 204` + `lazy: true`、信息节点 `exclude-filter`、rule-provider `proxy: DIRECT`。

需要动态收集全部可用节点的组统一使用 `include-all: true`，同时兼容 `proxies` 与 `proxy-providers`；不要退回只收集出站节点的 `include-all-proxies`。

Full 的 `其他节点`：`exclude-filter` 必须是各地区组 `filter` 的**精确并集**（含 emoji 与 `(?i)`）。

### 5. 范围外

不修 ShellCrash 对 URL 里 `geosite`/`geoip` 子串的误判；MetaCubeX `meta-rules-dat` 路径在源正确时允许使用。

---

## 验证

无构建步骤。提交前尽量：

```bash
mihomo -t -f rules/full.yaml   # 同步检查 core/nano
yamllint rules/*.yaml demo/*.yaml
git diff --check
```

- 路由矩阵 / 域名诊断：见 skill `sift-route-debug`。

YAML：两空格缩进；按意图分块并加短注释。

---

## 提交与 PR

- Conventional Commits，可带 scope：`config` / `rules` / `docs` / `scripts`（中英摘要均可）。
- PR 写清：分流行为变化、验证命令、对旧客户端的兼容风险，并注明影响 Full/Core/Nano 哪一档。
- 仅策略组 UI/顺序相关时才需要截图。

图标：远程引用默认 `Vbaethon/HOMOMIX`（`Icon/Color/Large`，jsDelivr）；新增图标须先确认上游 Large 文件存在（防 404），勿随意 vendoring 第三方图标/规则集（先核授权与署名）。

---

# 附录 A — 规则源与接线

## Hybrid 模板（MRS 优先）

| 用途 | 来源 |
| --- | --- |
| 域名/IP 骨架（proxy、cn、private、cn-lite、ai/media/games/apple-cn/microsoft-cn/games-cn、cnip/mediaip/privateip/telegramip） | DustinWin `mihomo-ruleset/*.mrs`（jsDelivr 加速直链） |
| 品牌（github/apple/google/microsoft/telegram） | MetaCubeX `meta/geo/geosite/*.mrs`（纯 domain，jsDelivr 加速直链） |

GitHub 有独立规则（`geosite/github`，纯 domain）→ Full `GitHub` 组 / Core `节点选择`，须置于 `microsoft` 前（geosite microsoft 含 github）；OneDrive 无独立规则，域在 `geosite microsoft` 内（include:onedrive）→ `微软服务`。全模板零 classical（品牌层用 MetaCubeX geosite）。

`cn` 为 DustinWin 全量 MRS（DNS-only，勿用于路由）；品牌层用 MetaCubeX geosite（纯 domain MRS，jsDelivr）。
全部规则集走 jsDelivr 分支加速直链（DustinWin `ruleset_geodata@mihomo-ruleset`、MetaCubeX `meta-rules-dat@meta`），不使用 github releases 直链（国内直连不稳）；模板不依赖 geodata（无 GEOIP/GEOSITE 规则，不配 `geox-url`）。

## 非 CN 代理层

hybrid 模板使用 DustinWin `proxy`（约等于 geolocation-!cn + gfwlist）作为非 CN 代理层，放在服务/品牌规则之后、`cn-lite` 之前。

**路由**国内域名兜底用 `cn-lite`（DustinWin），不要换成完整 `cn`。  
DustinWin `cn.mrs` 仅作 Full/Core 的 **DNS `nameserver-policy`**，不进 routing 替代 `cn-lite`。

---

# 附录 B — DNS / fake-IP 细节

仅 Full/Core。

### fake-IP 白名单

fake-IP 白名单使用 `rule-set:proxy`。

未进白名单的 private / CN / Tracker / 兼容域 → 真 IP。故无需、也不应再塞 `trackerslist`。

### nameserver-policy 两层

| 匹配 | 解析器 |
| --- | --- |
| 代理域：`proxy` | 海外 DoH |
| 国内/内网：`cn,private` | 国内 DoH |

未命中 policy → 只用海外 `nameserver`。海外 DoH（默认 `nameserver` + 代理域 policy）固定绑定 `节点选择`；国内 DoH（`cn`/`private` policy、`direct-nameserver`）与代理节点地址的 `proxy-server-nameserver` 均固定直连，避免国内解析被代理改道或启动环路。

`googleapis.cn` 等 `.cn` 代理域若误走 `cn` policy，会吃到污染或 CDN 锁定解析，故默认海外 + 代理域 policy 强制海外。

---

# 附录 C — 速查：hybrid Full 意图链

与 `README` 分流表一致，改 yaml 时对照：

1. 局域网 / 私有 → `DIRECT`
2. 广告 → 按模板规则落入 `直连` / `节点选择`
3. Tracker 等 → `直连`（按模板）
4. 国内 Apple / Microsoft / 游戏补充 → `直连`
5. 海外 Apple / AI / 游戏 / 流媒体 / OneDrive / Microsoft / TG / Google → 对应组
6. `proxy`（明确非 CN）→ `节点选择`
7. `cn-lite` / 国内 IP → `直连`
8. 其余 → `漏网之鱼`

细节与域名矩阵以当前 yaml + `sift-route-debug` 为准；本附录描述**意图**，不是逐行拷贝源。
