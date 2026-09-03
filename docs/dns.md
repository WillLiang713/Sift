# DNS 泄露与 Fake-IP 规则

本文记录 Full / Core 模板的 DNS 分工。Nano 模板不接管 DNS。

## 解析与出口分工

`respect-rules: true` 表示 DNS 上游连接遵循业务路由规则；上游地址不再通过 URL 参数固定策略组。`nameserver-policy` 仍按查询域名选择解析器，因此继续按意图明确分层：

- 明确代理域名（`proxy`）通过 `nameserver-policy` 强制使用海外 DoH（优先于 cn）。
- `cn` + `private` 域名通过 `nameserver-policy` 使用国内 DoH。
- 未命中 `nameserver-policy` 的域名只使用海外 `nameserver`，**不**启用 `fallback` / `fallback-filter`。
- 海外 DoH（代理域 policy + 默认 `nameserver`）的上游连接遵循路由规则。
- 国内解析（`cn`/`private` policy 与 `direct-nameserver`：国内 DoH）不指定策略组。
- `proxy-server-nameserver` 使用国内 DoH 解析代理节点域名，避免启动环路。
- 国内解析不使用 `system`，避免 TUN / DNS 劫持把查询打回内核。

```yaml
nameserver-policy:
  # 明确代理域名使用海外 DoH
  "rule-set:proxy":
    - https://1.1.1.1/dns-query
    - https://8.8.8.8/dns-query

  # 国内及私有域名：国内 DoH（不使用 system）
  "rule-set:cn,private":
    - https://223.5.5.5/dns-query
    - https://1.12.12.12/dns-query

respect-rules: true
direct-nameserver:
  - https://223.5.5.5/dns-query
  - https://1.12.12.12/dns-query

proxy-server-nameserver:
  - https://223.5.5.5/dns-query
  - https://1.12.12.12/dns-query

# 默认解析：仅海外 DoH（无 fallback）
nameserver:
  - https://1.1.1.1/dns-query
  - https://8.8.8.8/dns-query
```

Full/Core 建议显式 `prefer-h3: false`（降低部分网络 DoH H3 首包卡顿）。

模板的 policy key 为 `rule-set:proxy` / `rule-set:cn,private`。所有 DoH 上游都使用 IP 形式，无需额外的 `default-nameserver` bootstrap。

## 为什么禁止 fallback

旧方案曾用「国内 `nameserver` + 海外 `fallback` + `fallback-filter`」并发查询未分类域名：国内结果为 CN 则采用国内结果，否则采用海外结果。

该模式的问题是：`fallback-filter` 只选择最终采用哪一侧结果，**不阻止**并发查询本身。未分类域名即使最终走代理出口，国内 DoH 服务商仍可能看到该查询。对「最终会代理、但未落入 `proxy` / `geolocation-!cn` / `google` 策略」的域名，这会额外暴露 DNS 元数据。

当前模板因此改为：

| 域名意图 | 解析器 |
| --- | --- |
| 明确代理（`proxy`） | 海外 DoH（`nameserver-policy`），上游连接遵循路由规则 |
| 明确国内 / 内网（`cn,private`） | 国内 DoH（`nameserver-policy`）固定直连 |
| 未分类 | 仅海外 `nameserver`，上游连接遵循路由规则 |
| 实际 `DIRECT` 流量 | `direct-nameserver`（国内 DoH），固定直连 |
| 代理节点域名 | `proxy-server-nameserver`（国内 DoH） |

代价：未分类的国内兼容域名若未进 `cn` policy，会走海外解析，可能得到非最优 CDN。Sift 优先避免「未分类却并发打国内 DNS」的泄露面；国内体验主要依赖 `cn` / `private` policy 与路由侧 `cn-lite` 等直连规则。

### GeoIP 数据库

模板不依赖 GeoIP 数据库：路由与 DNS 全部使用 RULE-SET（域名/IP 数据由 rule-provider 自带），**无 GEOIP/GEOSITE 规则，不配置 `geodata-mode` / `geox-url` / `geo-auto-update`**，避免无谓下载。

## Fake-IP 优先级规则

Full/Core 统一使用：

```yaml
fake-ip-filter-mode: rule
```

rule 模式与路由规则一样自上而下匹配。无条件直连域在与 `proxy` 重叠时优先返回 real-IP，其他明确代理域继续返回 `198.18.0.0/16` fake-IP。

### Full

```yaml
fake-ip-filter:
  - RULE-SET,private,real-ip
  - RULE-SET,apple-cn,real-ip
  - RULE-SET,microsoft-cn,real-ip
  - RULE-SET,games-cn,real-ip
  - RULE-SET,proxy,fake-ip
  - MATCH,real-ip
```

### Core

```yaml
fake-ip-filter:
  - RULE-SET,private,real-ip
  - RULE-SET,games-cn,real-ip
  - RULE-SET,proxy,fake-ip
  - MATCH,real-ip
```

Full 的 `apple-cn`、`microsoft-cn`、`games-cn` 以及两档共有的 `private` 都位于路由 `proxy` 前，并且选择无条件直连。它们与 `proxy` 存在交集，例如 `apps.apple.com`、`download.windowsupdate.com`、`steamserver.net` 与 `metacubex.github.io`，因此在 fake-IP 规则中保持相同优先级。Core 的 Apple/Microsoft 服务组可由用户改选代理，不属于无条件直连，故不加入 real-IP 例外。

随后 `proxy` 仍覆盖 `googleapis.cn`、`gvt1.com`、`googleusercontent.com` 和 `xn--ngstr-lra8j.com` 等明确代理域名；其余国内、Tracker、NTP 和兼容域名由 `MATCH` 返回 real-IP。路由侧的 `proxy` 仍位于 `cn-lite` 之前，不能把 `cn-lite` 整体放到 `proxy` 前，否则会让 Google `.cn` 等硬锚点绕过内核。

real-IP 为 OpenWrt/Nikki 等客户端的防火墙前置旁路创造条件，但不保证一定绕过 Mihomo：目标地址若不属于客户端的大陆 IP 旁路范围（例如 Steam 香港 CDN），或客户端未启用相应旁路，连接仍会进入内核再走 `DIRECT`。

## 为什么 Google `.cn` 需要 fake-IP

在 blacklist 旧模式下，`services.googleapis.cn` 同时命中国内集合与代理域名集：

1. DNS 因 cn 过滤而返回中国 real-IP。
2. OpenWrt/Nikki 等客户端可能在防火墙层按 China IP 提前直连。
3. 流量没有进入 Mihomo，因而无法命中更高意图的 `proxy` 规则。

规则模式让这类明确代理域名先获得 fake-IP，确保连接进入 Mihomo 后再按域名规则选择出口；只有位于路由 `proxy` 前的无条件直连域以更高优先级取得 real-IP。`nameserver-policy` 仍为 `proxy` 指定海外 DoH、为 `cn,private` 指定国内 DoH；未分类域名只走海外 `nameserver`，不再进入国内主解析与海外 fallback 的并发选择流程。

## 国内域名为什么仍然直连

国内域名由 fake-IP 规则末尾的 `MATCH,real-ip` 返回 real-IP，并由 `nameserver-policy` 的国内 DoH 解析。显式直连例外只改变 fake-IP 输出，解析器仍由 `nameserver-policy` 独立判断；与 `proxy` 重叠的域名继续使用海外 DoH。路由侧仍使用 `cn-lite` + `cnip`。不要把 DNS 用的 MetaCubeX `cn.mrs` 换入路由兜底。

## 客户端设置

| 选项 | 建议 |
| --- | --- |
| 运行模式 | Fake-IP |
| DNS 劫持 | 开启 |
| DNS 劫持方式 | 优先防火墙转发 |
| 自定义 DNS 设置 | 关闭 |
| Respect Rules | 开启（遵循模板的 `respect-rules: true`） |
| Fake-IP Range | `198.18.0.1/16` |
| Fake-IP 持久化 | 开启 |
| Fake-IP-Filter 覆写 | 关闭 |
| IPv6 总开关 | 开启（模板默认 `true`） |
| IPv6 DNS 解析 | 开启（模板默认 `true`） |

改完 DNS 后，清理客户端 DNS/Fake-IP 缓存并重启 Mihomo。

## IPv6 防泄露

Full / Core 默认同时开启：

```yaml
ipv6: true
dns:
  ipv6: true
```

顶层 `ipv6` 控制 Mihomo 是否建立 IPv6 连接，`dns.ipv6` 控制是否返回 AAAA。如需禁用 IPv6 防泄露，必须将两者一起改为 `false`，并确保浏览器安全 DNS 没有绕过本地 DNS。

## DNS 泄露判读

### 检测网站出现中国 IP 不等于代理泄露

DNS 泄露检测网站通常会发起一批随机域名查询，再把收到查询的递归 DNS 服务器出口 IP、所属地区或运营商展示出来。

当前 Full/Core 模板**默认解析是海外 DoH**，未分类域名不会并发打国内解析器。检测结果中仍可能出现阿里、腾讯等中国大陆 DNS 出口 IP，常见原因包括：

- 查询命中了 `nameserver-policy` 的 `cn` / `private`（国内 DoH）。
- 连接最终 `DIRECT`，经 `direct-nameserver` 用国内 DoH 重新解析。
- `proxy-server-nameserver` 在解析代理节点域名时使用国内 DoH。
- 系统、浏览器安全 DNS、其他应用或 IPv6 绕过了 Mihomo（这才属于需要排查的真实泄露）。

因此：

- 检测页列出的是 **DNS 服务器 IP** 时：出现中国 IP 可能只是国内意图域名 / 直连重解析 / 节点域名解析的预期行为，不能单凭此项判定整站连接使用中国 IP 直连，也不能说明代理域名的 DNS 被国内解析器看到。
- 检测页或网络面板中的 **浏览器实际公网出口 IP** 若与预期代理出口不符，需要继续排查路由与客户端劫持。
- 明确代理域名应命中 `nameserver-policy` 的海外 DoH；该 DoH 上游连接遵循路由规则，而域名对应的业务连接仍应在 Mihomo 面板中进入预期的代理策略链。

本模板对国内 DoH 的使用范围刻意收窄为「明确国内/内网 policy、明确直连重解析、代理节点域名解析」。国内解析不用 `system`，避免 TUN / DNS 劫持把查询打回内核。它追求的是按域名意图分配解析器，并避免未分类查询再并发暴露给国内 DNS；不是把 DNS 元数据隐藏到代理所在地。海外 DoH 内容受 HTTPS 加密，但解析器会看到本地公网出口 IP。

DNS 上游连接统一遵循路由规则，海外 DoH 不再固定到 `节点选择`；`proxy-server-nameserver` 继续负责代理节点域名解析，避免启动环路。若还要避免国内解析器看到查询，则需同时改写 `cn,private` policy 与 `direct-nameserver` 的上游地址（甚至改走海外 DoH），并接受国内解析与 CDN 体验可能下降的代价。
