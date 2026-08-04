# DNS 泄露与 Fake-IP 白名单

本文记录 Full / Core 模板的 DNS 分工。Nano 模板不接管 DNS。

## 解析与出口分工

`respect-rules: false` 表示 DNS 上游不自动套用业务路由规则；海外 DoH 通过 URL 的 `#节点选择` 参数固定跟随主节点入口。`nameserver-policy` 仍按查询域名选择解析器，因此继续按意图明确分层：

- 明确代理域名（`proxy` / `geolocation-!cn` + `google`）通过 `nameserver-policy` 强制使用海外 DoH（优先于 cn）。
- `cn` + `private` 域名通过 `nameserver-policy` 使用国内 DoH。
- 未命中 `nameserver-policy` 的域名只使用海外 `nameserver`，**不**启用 `fallback` / `fallback-filter`。
- 海外 DoH（代理域 policy + 默认 `nameserver`）固定经 `节点选择`，随主代理出口切换。
- 国内 DoH（`cn`/`private` policy 与 `direct-nameserver`）固定直连，**不**挂策略组，避免把国内解析一并改道到代理。
- `proxy-server-nameserver` 使用国内 DoH 解析代理节点域名，避免启动环路。

```yaml
nameserver-policy:
  # 明确代理域名使用海外 DoH
  "rule-set:proxy":
    - "https://1.1.1.1/dns-query#节点选择"
    - "https://8.8.8.8/dns-query#节点选择"

  # 国内及私有域名使用国内 DoH
  "rule-set:cn,private":
    - https://223.5.5.5/dns-query
    - https://1.12.12.12/dns-query

respect-rules: false
direct-nameserver:
  - https://223.5.5.5/dns-query
  - https://1.12.12.12/dns-query

proxy-server-nameserver:
  - https://223.5.5.5/dns-query
  - https://1.12.12.12/dns-query

# 默认解析：仅海外 DoH（无 fallback）
nameserver:
  - "https://1.1.1.1/dns-query#节点选择"
  - "https://8.8.8.8/dns-query#节点选择"
```

Full/Core 建议显式 `prefer-h3: false`（降低部分网络 DoH H3 首包卡顿）。

主模板与 DustinWin/ACL 变体的 policy key 为 `rule-set:proxy` / `rule-set:cn,private`。MetaCubeX 变体的 policy key 为 `"geosite:geolocation-!cn,google"`（海外 DoH）与 `"geosite:cn,private"`（国内 DoH）。所有 DoH 上游都使用 IP 形式，无需额外的 `default-nameserver` bootstrap。

## 为什么禁止 fallback

旧方案曾用「国内 `nameserver` + 海外 `fallback` + `fallback-filter`」并发查询未分类域名：国内结果为 CN 则采用国内结果，否则采用海外结果。

该模式的问题是：`fallback-filter` 只选择最终采用哪一侧结果，**不阻止**并发查询本身。未分类域名即使最终走代理出口，国内 DoH 服务商仍可能看到该查询。对「最终会代理、但未落入 `proxy` / `geolocation-!cn` / `google` 策略」的域名，这会额外暴露 DNS 元数据。

当前模板因此改为：

| 域名意图 | 解析器 |
| --- | --- |
| 明确代理（`proxy` / `geolocation-!cn,google`） | 海外 DoH（`nameserver-policy`）经 `节点选择` |
| 明确国内 / 内网（`cn,private`） | 国内 DoH（`nameserver-policy`）固定直连 |
| 未分类 | 仅海外 `nameserver`，经 `节点选择` |
| 实际 `DIRECT` 流量 | `direct-nameserver` 国内 DoH，固定直连 |
| 代理节点域名 | `proxy-server-nameserver` 国内 DoH |

代价：未分类的国内兼容域名若未进 `cn` policy，会走海外解析，可能得到非最优 CDN。Sift 优先避免「未分类却并发打国内 DNS」的泄露面；国内体验主要依赖 `cn` / `private` policy 与路由侧 `cn-lite` 等直连规则。

### GeoIP 数据库管理

所有 DNS-enabled Full/Core 模板仍固定 GeoIP 数据源（MMDB，24 小时自动更新）。hybrid 主模板与 DustinWin/ACL 变体为：

```yaml
geodata-mode: false
geox-url:
  mmdb: "https://cdn.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/geoip.metadb"
geo-auto-update: true
geo-update-interval: 24
```

`geodata-mode: false` 选择 MMDB 模式。该数据库服务 Mihomo 内置 GeoIP 查询（例如 MetaCubeX 变体路由中的 `GEOIP,CN` / `GEOIP,telegram`），**不再**服务于已移除的 `fallback-filter`。

综合主模板及 DustinWin/ACL4SSR 的国内 IP 路由仍使用各自的 `cnip` / `ChinaIp` provider，不依赖上述 MMDB 替换路由规则集。MetaCubeX 变体额外通过顶层 `geox-url` 拉取 `geoip.dat` / `geosite.dat` / `geoip.metadb`。

## Fake-IP 白名单

Full/Core 统一使用：

```yaml
fake-ip-filter-mode: whitelist
```

在 whitelist 模式下，`fake-ip-filter` 中列出的域名返回 `198.18.0.0/16` fake-IP；未列入的私有、国内、Tracker、NTP 和其他兼容域名默认返回 real-IP。

### 主模板 / DustinWin Full/Core

```yaml
fake-ip-filter:
  - rule-set:proxy
```

DustinWin `proxy` 是 domain-only `geolocation-!cn + gfwlist`，同时覆盖 `googleapis.cn`、`gvt1.com`、`googleusercontent.com` 和 `xn--ngstr-lra8j.com` 等明确代理域名。它在路由侧仍位于 `cn-lite` 之前。

### ACL4SSR Full/Core

ACL4SSR `ProxyLite` 是 classical provider，不适合 DNS `rule-set:` 引用，因此额外定义 DNS-only DustinWin `proxy` domain provider：

```yaml
fake-ip-filter:
  - rule-set:proxy
```

路由侧仍使用 ACL4SSR `ProxyLite`，并保持在 `ChinaDomain` 之前。

### MetaCubeX Full/Core

```yaml
fake-ip-filter:
  - geosite:geolocation-!cn
  - geosite:google
```

`geosite:google` 用于补足 `geolocation-!cn` 不包含的 Google 全球 `.cn` 例外，**产品锚点是 `googleapis.cn`**（`play.googleapis.com` 已在 `geolocation-!cn` 内）。`gstatic.cn` 等同族域名不是硬合同。MetaCubeX 模板直接使用 geosite，路由侧不定义 `rule-providers`。

## 为什么 Google `.cn` 需要 fake-IP

在 blacklist 旧模式下，`services.googleapis.cn` 同时命中 MetaCubeX cn 与代理域名集：

1. DNS 因 cn 过滤而返回中国 real-IP。
2. OpenWrt/Nikki 等客户端可能在防火墙层按 China IP 提前直连。
3. 流量没有进入 Mihomo，因而无法命中更高意图的 `proxy` / `GEOSITE,google` 规则。

白名单模式让这类明确代理域名先获得 fake-IP，确保连接进入 Mihomo 后再按域名规则选择出口。`nameserver-policy` 为 `proxy` / `geolocation-!cn,google` 指定海外 DoH，为 `cn,private` 指定国内 DoH；未分类域名只走海外 `nameserver`，不再进入国内主解析与海外 fallback 的并发选择流程。

## 国内域名为什么仍然直连

国内域名未列入 fake-IP 白名单，因此返回 real-IP，并由 `nameserver-policy` 的国内 DoH 解析。路由侧仍使用：

- DustinWin / hybrid：`cn-lite` + `cnip`
- ACL4SSR：`ChinaDomain` + `ChinaIp` / `ChinaIpV6`
- MetaCubeX：`GEOSITE,cn` + `GEOIP,CN`

不要把 DNS 用的 MetaCubeX `cn.mrs` 换入 DustinWin / ACL4SSR 路由兜底。

## 客户端设置

| 选项 | 建议 |
| --- | --- |
| 运行模式 | Fake-IP |
| DNS 劫持 | 开启 |
| DNS 劫持方式 | 优先防火墙转发 |
| 自定义 DNS 设置 | 关闭 |
| Respect Rules | 关闭（遵循模板的 `respect-rules: false`） |
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
- 明确代理域名应命中 `nameserver-policy` 的海外 DoH；该 DoH 上游连接固定跟随当前 `节点选择`，而域名对应的业务连接仍应在 Mihomo 面板中进入预期的代理策略链。

本模板对国内 DoH 的使用范围刻意收窄为「明确国内/内网 policy、明确直连重解析、代理节点域名解析」。它追求的是按域名意图分配解析器、缩短 DNS 链路，并避免未分类查询再并发暴露给国内 DNS；不是把 DNS 元数据隐藏到代理所在地。海外 DoH 内容受 HTTPS 加密，但解析器会看到本地公网出口 IP。

海外 DoH 查询固定随 `节点选择` 的当前出口；国内 DoH 与 `proxy-server-nameserver` 仍固定直连，避免国内解析被改道或节点域名解析环路。若还要避免国内解析器看到查询，则需同时改写 `cn,private` policy 与 `direct-nameserver` 的上游地址（甚至改走海外 DoH），并接受国内解析与 CDN 体验可能下降的代价。
