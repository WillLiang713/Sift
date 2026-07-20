# DNS 泄露说明

本文记录 Full / Core 模板的 DNS 泄露修复思路。

## 问题现象

测试时，公网 IP 已经是海外出口，但 DNS 服务器仍显示中国移动、阿里等国内服务商。

这说明代理流量本身已经走对了，但默认 DNS 解析还在使用国内上游。

## 根因

旧配置把国内 DoH 放在默认 `nameserver`：

```yaml
nameserver:
  - https://223.5.5.5/dns-query
  - https://doh.pub/dns-query
```

`respect-rules: true` 让 DNS 查询按最终分流结果选择解析路径。模板配合 `direct-nameserver`：实际直连的域名使用国内 DoH，代理域名使用默认海外 DoH；`nameserver-policy` 仍可按域名强制指定国内 DoH。

因此，对实际直连的测试域名，DNS 泄露测试可能看到国内 DNS；对代理域名，则应看到默认海外 DNS。

## 当前分工

Full/Core 模板按用途拆分 DNS。`fake-ip-filter` 与 `nameserver-policy` **共用** MetaCubeX geosite **cn**（DustinWin/ACL4SSR 为 `rule-set:cn` → `cn.mrs`；MetaCubeX 为 `geosite:cn`）外加 `private`，覆盖国内域名 real-IP 与国内 DoH。`trackerslist` 只额外进入 `fake-ip-filter`，让 BT Tracker 返回 real-IP；它不进入 `nameserver-policy`，也不改变路由出口。`*-cn` 规则只表达路由直连意图，不进入静态 DNS。未命中 cn 但实际直连的流量仍由 `respect-rules` 与 `direct-nameserver` 使用国内 DoH。

```yaml
fake-ip-filter:
  - rule-set:fakeip-filter
  - rule-set:private
  - rule-set:trackerslist
  - rule-set:cn

nameserver-policy:
  "rule-set:cn,private":
    - https://223.5.5.5/dns-query
    - https://1.12.12.12/dns-query

respect-rules: true
direct-nameserver:
  - https://223.5.5.5/dns-query
  - https://1.12.12.12/dns-query

nameserver:
  - https://1.1.1.1/dns-query
  - https://8.8.8.8/dns-query

proxy-server-nameserver:
  - https://223.5.5.5/dns-query
  - https://1.12.12.12/dns-query
```

DustinWin / ACL4SSR 的 DNS-only `cn` provider，以及所有 Full/Core 共用的 Tracker real-IP provider：

```yaml
cn:
  type: http
  behavior: domain
  format: mrs
  path: ./ruleset/metacubex/cn.mrs
  url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/cn.mrs"
  interval: 86400

trackerslist:
  type: http
  behavior: domain
  format: mrs
  path: ./ruleset/dustinwin/trackerslist.mrs
  url: "https://github.com/DustinWin/ruleset_geodata/releases/download/mihomo-ruleset/trackerslist.mrs"
  interval: 86400
```

路由侧仍用 DustinWin `cn-lite` 或 ACL4SSR `ChinaDomain`，**不要**把 DNS 用的 MetaCubeX `cn` 替换进路由兜底。

所有 DoH 上游都写成 IP 形式（`223.5.5.5`=阿里、`1.12.12.12`=doh.pub、`1.1.1.1`=Cloudflare、`8.8.8.8`=Google），因此不再需要 `default-nameserver` 去 bootstrap 解析 DoH 服务器域名。

| 字段 | 用途 |
| --- | --- |
| `fake-ip-filter` | 兼容例外 + Tracker + MetaCubeX cn 返回真实 IP，避免被路由器 nft / 禁 QUIC 规则按 `198.18/16` fake-ip 误处理。Tracker 仅影响 real-IP，不改变路由。 |
| `nameserver-policy` | 与 filter 同源：MetaCubeX cn + private 静态使用国内 DoH。`*-cn` 与 blackmatrix7 完整品牌包不进 policy。 |
| `direct-nameserver` | 在 `respect-rules` 下，实际命中 `DIRECT` 的 DNS 查询使用国内 DoH（含未进 cn 的直连域）。 |
| `nameserver` | 默认解析，使用海外 DoH（IP 形式），供代理路径使用。 |
| `proxy-server-nameserver` | 专门解析代理节点域名，避免开启 `respect-rules` 后出现启动环路。 |

DNS 静态规则保留 `fakeip-filter`、`private`、`trackerslist`、MetaCubeX `cn`；其中 `trackerslist` 只在 `fake-ip-filter` 中使用，不会进入路由或强制直连。DNS 不会引用 `*-cn` 路由补充，也不会引用完整 `rule-set:apple` / `rule-set:microsoft` / `rule-set:onedrive`（blackmatrix7 classical 可能含 `PROCESS-NAME` 等）。完整 Apple / Microsoft 仍在路由侧进入 `全球直连`；在 `DIRECT` 选中时由 `direct-nameserver` 使用国内 DoH。Core 路由侧将 `onedrive` 放在 `microsoft` 前进入 `节点选择`（无 OneDrive UI 组）。Core 的 `全球直连` 保留 `DIRECT`、`节点选择` 和 `自动测速`，且 `DIRECT` 排第一。

`rules/MetaCubeX-full.yaml` / `rules/MetaCubeX-core.yaml` 的路由规则仍只用 `GEOSITE` / `GEOIP`；MetaCubeX GeoSite 没有 `trackerslist` 标签，因此 DNS 侧额外补充 DustinWin `fakeip-filter` 与 `trackerslist` 两个 provider，国内层直接用 geodata：

```yaml
rule-providers:
  fakeip-filter:
    type: http
    behavior: domain
    format: text
    interval: 86400
    path: ./ruleset/dustinwin/fakeip-filter.list
    url: "https://cdn.jsdelivr.net/gh/DustinWin/ruleset_geodata@mihomo-ruleset/fakeip-filter.list"
  trackerslist:
    type: http
    behavior: domain
    format: mrs
    interval: 86400
    path: ./ruleset/dustinwin/trackerslist.mrs
    url: "https://github.com/DustinWin/ruleset_geodata/releases/download/mihomo-ruleset/trackerslist.mrs"

fake-ip-filter:
  - rule-set:fakeip-filter
  - geosite:private
  - rule-set:trackerslist
  - geosite:cn
nameserver-policy:
  "geosite:cn,private":
    - https://223.5.5.5/dns-query
    - https://1.12.12.12/dns-query
```

`rules/MetaCubeX-nano.yaml` 与 `rules/DustinWin-nano.yaml` 一样不接管 DNS。

本仓库**不**为 ShellCrash 对 URL 中 `geosite`/`geoip` 子串的启发式误判做规避；若客户端因此多下 geo 库，应在客户端侧处理。

## 国内域名为什么仍然直连

国内域名分两条路径：

1. 命中 `dns.fake-ip-filter`（`fakeip-filter` / `private` / MetaCubeX `cn`）时，客户端直接拿到真实 IP，并用 `nameserver-policy` 的国内 DoH 解析；在 OpenWrt/OpenClash 这类路由器环境里，真实中国 IP 可以继续命中本机的 China IP 直连链路，也不会被禁 QUIC 规则当作 `198.18/16` fake-ip 误拒绝。
2. 未命中 cn 的域名仍走 fake-ip 流程：客户端拿到 fake IP，内核再按原始域名匹配 `rules`；命中直连后由 `direct-nameserver` 使用国内 DoH，路由侧仍靠 `cn-lite` / `ChinaDomain` / `GEOSITE,cn` 等直连。

因此默认 `nameserver` 仍可以使用海外 DoH；MetaCubeX cn 同时管 real-IP 与静态国内 DoH；其余实际直连靠 `direct-nameserver`。

## 客户端设置

配合 Full / Core 模板使用时，建议：

| 选项 | 建议 |
| --- | --- |
| 运行模式 | Fake-IP |
| DNS 劫持 | 开启 |
| DNS 劫持方式 | 优先防火墙转发 |
| 自定义 DNS 设置 | 关闭 |
| 追加上游 DNS | 关闭 |
| 追加默认 DNS | 关闭 |
| Respect Rules | 开启 |
| Fake-IP Range | `198.18.0.1/16` |
| Fake-IP 持久化 | 开启 |
| Fake-IP-Filter 覆写 | 关闭 |
| IPv6 总开关 | 开启（模板默认 `true`） |
| IPv6 DNS 解析 | 开启（模板默认 `true`） |

如果使用 Nano 模板或 OpenClash 自己覆写 DNS，模板不会提供 `dns.fake-ip-filter`；需要在客户端的 fake-ip-filter 自定义里同步追加国内直连规则集。

改完 DNS 后，清理 DNS/Fake-IP 缓存并重启客户端。

## IPv6 防泄露

Full / Core 模板默认开启双栈：

```yaml
ipv6: true

dns:
  ipv6: true
```

顶层 `ipv6` 控制 Mihomo 是否建立 IPv6 连接，`dns.ipv6` 控制是否返回 AAAA 回应；二者不能相互替代。

若网络环境不需要 IPv6，或 TUN/TProxy 只接管 IPv4、担心运营商 IPv6 绕过代理，应同时改为：

```yaml
ipv6: false

dns:
  ipv6: false
```

仅关 `dns.ipv6` 不会阻断已缓存、由浏览器安全 DNS 或其他解析器拿到的 IPv6 地址。修改后应清理系统、浏览器和 Mihomo 的 DNS/Fake-IP 缓存，关闭可能绕过本地 DNS 的浏览器安全 DNS，并重启客户端。开启 IPv6 时请确保代理链路同样接管 IPv6。

## 绕过大陆为什么仍然干净

泄露测试使用的域名不是国内域名，不会命中 DNS 侧的 MetaCubeX `cn` 或路由侧的 `cn-lite` / `ChinaDomain` / `GEOSITE,cn`。

因此代理测试域名继续使用默认 `nameserver`，也就是海外 DoH。
