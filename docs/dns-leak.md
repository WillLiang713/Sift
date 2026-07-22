# DNS 泄露与 Fake-IP 白名单

本文记录 Full / Core 模板的 DNS 分工。Nano 模板不接管 DNS。

## 解析与出口分工

`respect-rules: true` 使 DNS 查询按最终分流结果选择解析路径。`nameserver-policy` 优先于 `respect-rules`，因此必须按意图明确分层：

- 明确代理域名（`proxy` / `geolocation-!cn` + `google`）通过 `nameserver-policy` 强制使用海外 DoH（优先于 cn）。
- `cn` + `private` 域名通过 `nameserver-policy` 使用国内 DoH。
- 未命中 `nameserver-policy` 的域名由国内 `nameserver` 与海外 `fallback` 并发查询，再由 `fallback-filter` 选择结果。
- 实际命中 `DIRECT` 的域名使用 `direct-nameserver` 国内 DoH。
- `proxy-server-nameserver` 使用国内 DoH 解析代理节点域名，避免启动环路。
```yaml
nameserver-policy:
  # 明确代理域名使用海外 DoH
  "rule-set:proxy":
    - https://1.1.1.1/dns-query
    - https://8.8.8.8/dns-query

  # 国内及私有域名使用国内 DoH
  "rule-set:cn,private":
    - https://223.5.5.5/dns-query
    - https://1.12.12.12/dns-query

respect-rules: true
direct-nameserver:
  - https://223.5.5.5/dns-query
  - https://1.12.12.12/dns-query

nameserver:
  - https://223.5.5.5/dns-query
  - https://1.12.12.12/dns-query

fallback:
  - https://1.1.1.1/dns-query
  - https://8.8.8.8/dns-query

fallback-filter:
  geoip: true
  geoip-code: CN
  ipcidr:
    - 240.0.0.0/4

proxy-server-nameserver:
  - https://223.5.5.5/dns-query
  - https://1.12.12.12/dns-query
```

Full/Core 建议显式 `prefer-h3: false`（降低部分网络 DoH H3 首包卡顿）。

主模板与 DustinWin/ACL 变体的 policy key 为 `rule-set:proxy` / `rule-set:cn,private`。MetaCubeX 变体的 policy key 为 `"geosite:geolocation-!cn,google"`（海外 DoH）与 `"geosite:cn,private"`（国内 DoH）。所有 DoH 上游都使用 IP 形式，无需额外的 `default-nameserver` bootstrap。

## 未分类域名的 fallback

`nameserver-policy` 已命中的查询不会进入 `fallback`。只有未分类域名才会同时查询国内 `nameserver` 和海外 `fallback`：

- 国内结果属于 CN 时，采用国内结果。
- 国内结果不属于 CN 时，采用海外结果。
- 国内结果落入保留地址 `240.0.0.0/4` 时，明确视为异常并采用海外结果。

这里不再添加 `fallback-filter.geosite:gfw` 或 Google/Facebook/YouTube 手写域名：DustinWin/ACL 的 `rule-set:proxy` 与 MetaCubeX 的 `geosite:geolocation-!cn,google` 已在更高优先级的 `nameserver-policy` 中处理这些明确代理域名，避免为 DustinWin/ACL 模板额外引入 GeoSite 数据库依赖。

`fallback-filter` 只选择结果，不阻止并发查询。未分类域名即使最终采用海外结果，国内 DoH 服务商仍可能看到该查询；这是换取未分类域名国内解析/CDN 优先能力的隐私取舍。

### GeoIP 数据库管理

所有 DNS-enabled Full/Core 模板都显式固定 `fallback-filter.geoip-code` 使用的数据库：

```yaml
geodata-mode: false
geox-url:
  mmdb: "https://cdn.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/geoip.metadb"
geo-auto-update: true
geo-update-interval: 24
```

`geodata-mode: false` 选择 MMDB 模式；`geo-auto-update` 每 24 小时更新一次。综合主模板及 DustinWin/ACL4SSR 的国内路由仍使用各自的 `cnip` / `ChinaIp` provider，MMDB 只负责 Mihomo 内置 GeoIP 查询（包括 `fallback-filter`），不替换路由规则集。

## Fake-IP 白名单

Full/Core 统一使用：

```yaml
fake-ip-filter-mode: whitelist
```

在 whitelist 模式下，`fake-ip-filter` 中列出的域名返回 `198.18.0.0/16` fake-IP；未列入的私有、国内、Tracker、NTP 和其他兼容域名默认返回 real-IP。

### DustinWin Full/Core

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

`geosite:google` 用于补足 `geolocation-!cn` 不包含的 `googleapis.cn` / `gstatic.cn` 等 Google 全球 `.cn` 例外。MetaCubeX 模板直接使用 geosite，不定义 `rule-providers`。

## 为什么 Google `.cn` 需要 fake-IP

在 blacklist 旧模式下，`services.googleapis.cn` 同时命中 MetaCubeX cn 与代理域名集：

1. DNS 因 cn 过滤而返回中国 real-IP。
2. OpenWrt/Nikki 等客户端可能在防火墙层按 China IP 提前直连。
3. 流量没有进入 Mihomo，因而无法命中更高意图的 `proxy` / `GEOSITE,google` 规则。

白名单模式让这类明确代理域名先获得 fake-IP，确保连接进入 Mihomo 后再按域名规则选择出口。`nameserver-policy` 为 `proxy`/`geolocation-!cn,google` 指定海外 DoH，为 `cn,private` 指定国内 DoH；只有未分类域名进入国内主解析与海外 fallback 的并发选择流程。

## 国内域名为什么仍然直连

国内域名未列入 fake-IP 白名单，因此返回 real-IP，并由 `nameserver-policy` 的国内 DoH 解析。路由侧仍使用：

- DustinWin：`cn-lite` + `cnip`
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
| Respect Rules | 开启 |
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

对实际直连域名，DNS 测试看到国内解析器是预期行为。明确代理域名应由 `nameserver-policy` 指定的海外 DoH 解析，且连接应在 Mihomo 面板中显示代理策略链。未分类域名会同时查询国内外 DoH，不能用它们判断“零 DNS 元数据泄露”。
