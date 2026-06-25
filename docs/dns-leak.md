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
nameserver:
  - https://cloudflare-dns.com/dns-query
  - https://dns.google/dns-query

direct-nameserver:
  - https://dns.alidns.com/dns-query
  - https://doh.pub/dns-query

proxy-server-nameserver:
  - https://223.5.5.5/dns-query
  - https://doh.pub/dns-query
```

| 字段 | 用途 |
| --- | --- |
| `nameserver` | 默认解析，使用海外 DoH，泄露测试只会看到海外 DNS。 |
| `direct-nameserver` | 最终直连的域名使用国内 DoH，保留国内 CDN 质量。 |
| `proxy-server-nameserver` | 专门解析代理节点域名，避免开启 `respect-rules` 后出现启动环路。 |
| `default-nameserver` | 只负责解析 DoH 服务器域名，必须使用纯 IP。 |

## 国内域名为什么仍然直连

国内域名不是靠“先用国内 DNS 解析”来判断的。

fake-ip 模式下的主要流程是：

1. 客户端请求域名。
2. 内核返回 fake IP。
3. 客户端连接 fake IP。
4. 内核根据 fake IP 找回原始域名。
5. 原始域名匹配 `rules`。
6. 命中 `cn`、`google-cn`、`apple-cn`、`microsoft-cn`、`games-cn`，或后续命中 `GEOIP,CN`。
7. 策略进入 `全球直连`。
8. 如果 `全球直连` 当前是 `DIRECT`，真实 IP 使用 `direct-nameserver` 解析。

关键点是：

```text
先由 rules 判断最终出口，再按最终出口选择 DNS。
```

所以默认 `nameserver` 可以使用海外 DoH；确认直连的国内域名仍然会使用国内 DoH。

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

改完 DNS 后，清理 DNS/Fake-IP 缓存并重启客户端。

## 绕过大陆为什么仍然干净

泄露测试使用的域名不是国内域名，不会命中 `cn` 或国内直连规则。

因此测试域名继续使用默认 `nameserver`，也就是海外 DoH。

国内域名命中直连规则后使用 `direct-nameserver`，这是为了国内访问质量，不会影响海外泄露测试结果。

## 复发排查

优先检查：

- 浏览器安全 DNS / DoH 是否关闭。
- 运行配置中的 `nameserver` 是否仍然是海外 DoH。
- 客户端是否重新开启了自定义 DNS、追加上游 DNS 或追加默认 DNS。
- `漏网之鱼` 是否被手动切成 `DIRECT`。
- 终端设备 DNS 是否仍指向路由器路径，而不是公共 DNS。
