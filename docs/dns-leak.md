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

`respect-rules: true` 只表示 DNS 上游连接也遵守分流规则。它不会把国内 DNS 上游变成海外 DNS 上游。

因此，只要默认解析器是国内 DNS，泄露测试就可能看到国内 DNS。

## 当前分工

`rules/dustinwin-full.yaml` / `rules/dustinwin-core.yaml` 按用途拆分 DNS，并且 DNS 侧只引用 `cn` 这个完整国内 DNS 入口。`*-cn` 规则只表达路由直连意图，不代表一定适合国内 DNS 解析：

```yaml
fake-ip-filter:
  - rule-set:fakeip-filter
  - rule-set:private
  - rule-set:cn

nameserver-policy:
  "rule-set:cn":
    - https://223.5.5.5/dns-query
    - https://1.12.12.12/dns-query

nameserver:
  - https://1.1.1.1/dns-query
  - https://8.8.8.8/dns-query

proxy-server-nameserver:
  - https://223.5.5.5/dns-query
  - https://1.12.12.12/dns-query
```

所有 DoH 上游都写成 IP 形式（`223.5.5.5`=阿里、`1.12.12.12`=doh.pub、`1.1.1.1`=Cloudflare、`8.8.8.8`=Google），因此不再需要 `default-nameserver` 去 bootstrap 解析 DoH 服务器域名。

| 字段 | 用途 |
| --- | --- |
| `fake-ip-filter` | 国内直连规则集返回真实 IP，避免被路由器 nft / 禁 QUIC 规则按 `198.18/16` fake-ip 误处理。 |
| `nameserver-policy` | 只让 `cn` 使用国内 DoH；`apple-cn`、`microsoft-cn`、`games-cn` 等 `*-cn` 路由补充规则不进入 DNS policy。完整 `google` 路由规则进入 `节点选择`，不作为国内 DNS policy 条件。 |
| `nameserver` | 默认解析，使用海外 DoH（IP 形式），泄露测试只会看到海外 DNS。 |
| `proxy-server-nameserver` | 专门解析代理节点域名，避免开启 `respect-rules` 后出现启动环路。 |

DNS 侧只保留 `fakeip-filter`、`private`、`cn`，不会引用 `*-cn` 路由补充规则，也不会引用完整 `rule-set:apple` / `rule-set:microsoft`，因为 blackmatrix7 classical 规则中可能包含 `PROCESS-NAME` 等非域名规则类型，不适合 `fake-ip-filter` / `nameserver-policy`。完整 `rule-set:apple` / `rule-set:microsoft` 仍只在路由侧进入 `全球直连`；Core 的 `全球直连` 保留 `DIRECT`、`节点选择` 和 `自动测速`，且 `DIRECT` 排第一。

`rules/metacubex-full.yaml` / `rules/metacubex-core.yaml` 的路由规则仍只用 `GEOSITE` / `GEOIP`；但 MetaCubeX `meta-rules-dat` 当前没有 `geosite:fakeip-filter` 分类，所以 DNS 侧按 Mihomo 官方示例允许的 `rule-set:<name>` 方式额外补充一个 DustinWin domain provider：

```yaml
rule-providers:
  fakeip-filter:
    type: http
    behavior: domain
    format: text
    interval: 86400
    path: ./ruleset/dustinwin/fakeip-filter.list
    url: "https://cdn.jsdelivr.net/gh/DustinWin/ruleset_geodata@mihomo-ruleset/fakeip-filter.list"

fake-ip-filter:
  - rule-set:fakeip-filter
  - geosite:private
  - geosite:cn
nameserver-policy:
  "geosite:cn,private":
    - https://223.5.5.5/dns-query
    - https://1.12.12.12/dns-query
```

`rules/metacubex-nano.yaml` 与 `rules/dustinwin-nano.yaml` 一样不接管 DNS。

## 国内域名为什么仍然直连

国内域名分两条路径：

1. 命中 `dns.fake-ip-filter` 的国内直连规则集时，客户端直接拿到真实 IP；在 OpenWrt/OpenClash 这类路由器环境里，真实中国 IP 可以继续命中本机的 China IP 直连链路，也不会被禁 QUIC 规则当作 `198.18/16` fake-ip 误拒绝。
2. 未命中 `fake-ip-filter` 的域名仍走 fake-ip 流程：客户端拿到 fake IP，内核再按原始域名匹配 `rules`，命中直连规则后进入 `全球直连`。

因此默认 `nameserver` 仍可以使用海外 DoH；明确国内直连的域名由 `fake-ip-filter` / `nameserver-policy` 保留国内解析质量。

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
| IPv6 DNS 解析 | 未主动使用 IPv6 时关闭 |

如果使用 Nano 模板或 OpenClash 自己覆写 DNS，模板不会提供 `dns.fake-ip-filter`；需要在客户端的 fake-ip-filter 自定义里同步追加国内直连规则集。

改完 DNS 后，清理 DNS/Fake-IP 缓存并重启客户端。

## 绕过大陆为什么仍然干净

泄露测试使用的域名不是国内域名，不会命中 DNS 侧的 `cn` 或路由侧的 `cn-lite`。

因此测试域名继续使用默认 `nameserver`，也就是海外 DoH。

国内域名命中直连规则后通过 `nameserver-policy` 使用国内 DoH，这是为了国内访问质量，不会影响海外泄露测试结果。

## 复发排查

优先检查：

- 浏览器安全 DNS / DoH 是否关闭。
- 运行配置中的 `nameserver` 是否仍然是海外 DoH。
- 客户端是否重新开启了自定义 DNS、追加上游 DNS 或追加默认 DNS。
- `漏网之鱼`（Full / Nano）或 `节点选择`（Core）是否被手动切成 `DIRECT`。
- 终端设备 DNS 是否仍指向路由器路径，而不是公共 DNS。
