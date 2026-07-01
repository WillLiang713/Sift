# DNS 泄露说明

本文记录 `Full.yaml` 的 DNS 泄露修复思路。

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

`Full.yaml` 按用途拆分 DNS：

```yaml
fake-ip-filter:
  - rule-set:fakeip-filter
  - rule-set:private
  - rule-set:google-cn
  - rule-set:apple-cn
  - rule-set:microsoft-cn
  - rule-set:games-cn
  - rule-set:cn-dns

nameserver-policy:
  "rule-set:google-cn":
    - https://dns.alidns.com/dns-query
    - https://doh.pub/dns-query
  "rule-set:apple-cn":
    - https://dns.alidns.com/dns-query
    - https://doh.pub/dns-query
  "rule-set:microsoft-cn":
    - https://dns.alidns.com/dns-query
    - https://doh.pub/dns-query
  "rule-set:games-cn":
    - https://dns.alidns.com/dns-query
    - https://doh.pub/dns-query
  "rule-set:cn-dns":
    - https://dns.alidns.com/dns-query
    - https://doh.pub/dns-query

nameserver:
  - https://cloudflare-dns.com/dns-query
  - https://dns.google/dns-query

default-nameserver:
  - 223.5.5.5
  - 119.29.29.29

direct-nameserver:
  - https://dns.alidns.com/dns-query
  - https://doh.pub/dns-query

proxy-server-nameserver:
  - https://dns.alidns.com/dns-query
  - https://doh.pub/dns-query
```

| 字段 | 用途 |
| --- | --- |
| `fake-ip-filter` | 国内直连规则集返回真实 IP，避免被路由器 nft / 禁 QUIC 规则按 `198.18/16` fake-ip 误处理。 |
| `nameserver-policy` | `google-cn`、`apple-cn`、`microsoft-cn`、`games-cn`、`cn-dns` 等国内直连规则集使用国内 DoH，避免客户端 DNS 查询拿到海外 CDN 结果。 |
| `nameserver` | 默认解析，使用海外 DoH，泄露测试只会看到海外 DNS。 |
| `default-nameserver` | 只负责解析 DoH 服务器域名，必须使用纯 IP。 |
| `direct-nameserver` | 最终直连的域名使用国内 DoH，保留国内 CDN 质量。 |
| `proxy-server-nameserver` | 专门解析代理节点域名，避免开启 `respect-rules` 后出现启动环路。 |

## 国内域名为什么仍然直连

国内域名分两条路径：

1. 命中 `dns.fake-ip-filter` 的国内直连规则集时，客户端直接拿到真实 IP；在 OpenWrt/OpenClash 这类路由器环境里，真实中国 IP 可以继续命中本机的 China IP 直连链路，也不会被禁 QUIC 规则当作 `198.18/16` fake-ip 误拒绝。
2. 未命中 `fake-ip-filter` 的域名仍走 fake-ip 流程：客户端拿到 fake IP，内核再按原始域名匹配 `rules`，命中直连规则后进入 `全球直连`。

因此默认 `nameserver` 仍可以使用海外 DoH；明确国内直连的域名由 `fake-ip-filter` / `nameserver-policy` / `direct-nameserver` 保留国内解析质量。

## 客户端设置

配合 `Full.yaml` 使用时，建议：

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

如果使用 `Nano.yaml` 或 OpenClash 自己覆写 DNS，模板不会提供 `dns.fake-ip-filter`；需要在客户端的 fake-ip-filter 自定义里同步追加国内直连规则集。

改完 DNS 后，清理 DNS/Fake-IP 缓存并重启客户端。

## 绕过大陆为什么仍然干净

泄露测试使用的域名不是国内域名，不会命中 DNS 侧的 `cn-dns` 或路由侧的 `cn`。

因此测试域名继续使用默认 `nameserver`，也就是海外 DoH。

国内域名命中直连规则后通过 `nameserver-policy` / `direct-nameserver` 使用国内 DoH，这是为了国内访问质量，不会影响海外泄露测试结果。

## 复发排查

优先检查：

- 浏览器安全 DNS / DoH 是否关闭。
- 运行配置中的 `nameserver` 是否仍然是海外 DoH。
- 客户端是否重新开启了自定义 DNS、追加上游 DNS 或追加默认 DNS。
- `漏网之鱼` 是否被手动切成 `DIRECT`。
- 终端设备 DNS 是否仍指向路由器路径，而不是公共 DNS。
