# anti-AD dnsmasq 去广告

本文记录在 ImmortalWrt/OpenClash 路由器上使用 anti-AD 的 dnsmasq 规则进行 DNS 层广告过滤的方法。

## 当前环境

路由器环境：

| 项目 | 值 |
| --- | --- |
| 系统 | ImmortalWrt 24.10-SNAPSHOT |
| 设备 | CMCC RAX3000M |
| 内核 | 6.6.95 |
| dnsmasq | dnsmasq-full 2.90-r5 |
| OpenClash | luci-app-openclash 0.47.096 |
| DNS 转发 | dnsmasq `53` -> OpenClash `127.0.0.1#7874` |

当前 dnsmasq 生成配置中保留 OpenClash 的运行时目录：

```conf
conf-dir=/tmp/dnsmasq.cfg01411c.d
```

OpenClash 会在该目录注入自己的 dnsmasq 片段，例如 `dnsmasq_openclash_chnroute_pass.conf`。因此不建议通过修改 `dhcp.@dnsmasq[0].confdir` 来加载广告规则，避免覆盖或绕开 OpenClash 的运行时目录。

## 方案选择

采用 anti-AD 官方 dnsmasq 文件：

```text
https://anti-ad.net/anti-ad-for-dnsmasq.conf
```

该文件内容是 dnsmasq 原生规则，例如：

```conf
address=/doubleclick.net/
```

dnsmasq 命中后会直接返回 `NXDOMAIN`，请求不会继续进入 OpenClash DNS。

数据通路为：

```text
终端 DNS 请求
  -> 路由器 dnsmasq:53
    -> anti-AD 本地规则
      -> 命中广告域名：NXDOMAIN
      -> 未命中：转发到 OpenClash 127.0.0.1#7874
```

该方法只影响 DNS 解析阶段，不参与实际 TCP/UDP 数据转发。对测速吞吐通常没有明显影响，主要成本是 dnsmasq 启动时加载约 10 万条规则带来的启动时间和内存开销。

## 已落地配置

规则文件位置：

```sh
/etc/anti-ad/anti-ad-for-dnsmasq.conf
```

`/etc/dnsmasq.conf` 中追加：

```conf
conf-file=/etc/anti-ad/anti-ad-for-dnsmasq.conf
```

UCI 中追加：

```sh
list addnmount '/etc/anti-ad/anti-ad-for-dnsmasq.conf'
```

当前显示为：

```sh
dhcp.cfg01411c.addnmount='/etc/anti-ad/anti-ad-for-dnsmasq.conf'
```

`cfg01411c` 是 OpenWrt/UCI 为匿名 `dnsmasq` 配置段生成的内部 ID，对应 `dhcp.@dnsmasq[0]`。

## 为什么需要 addnmount

这台路由器的 dnsmasq 运行在 `ujail` 沙箱中。启动进程类似：

```sh
/sbin/ujail ... -r /etc/dnsmasq.conf ...
```

`/etc/dnsmasq.conf` 能被沙箱内的 dnsmasq 读取，但 dnsmasq init 脚本不会递归解析该文件，再自动发现里面 include 的外部文件。

因此当 `/etc/dnsmasq.conf` 里写了：

```conf
conf-file=/etc/anti-ad/anti-ad-for-dnsmasq.conf
```

还需要通过 `addnmount` 明确把该文件只读挂进 dnsmasq 沙箱：

```sh
uci add_list dhcp.@dnsmasq[0].addnmount='/etc/anti-ad/anti-ad-for-dnsmasq.conf'
uci commit dhcp
```

实测结果：

```text
inside ujail WITH anti-ad mount:
dnsmasq: syntax check OK

inside ujail WITHOUT anti-ad mount:
dnsmasq: cannot read /etc/anti-ad/anti-ad-for-dnsmasq.conf: No such file or directory
```

`addnmount` 不是广告过滤功能本身。真正加载规则的是 `conf-file=...`；`addnmount` 只负责让沙箱里的 dnsmasq 能看到这个文件。

OpenWrt 上游在 2022-11-27 加入该机制，目的就是给 jailed dnsmasq 暴露额外路径，适用于手动 include 配置文件或使用沙箱外路径的场景。

参考：

- https://lists.infradead.org/pipermail/lede-commits/2022-November/016354.html

## 初次部署命令

```sh
mkdir -p /etc/anti-ad

curl -L -o /etc/anti-ad/anti-ad-for-dnsmasq.conf \
  https://anti-ad.net/anti-ad-for-dnsmasq.conf

grep -qxF 'conf-file=/etc/anti-ad/anti-ad-for-dnsmasq.conf' /etc/dnsmasq.conf || \
  printf '\nconf-file=/etc/anti-ad/anti-ad-for-dnsmasq.conf\n' >> /etc/dnsmasq.conf

uci add_list dhcp.@dnsmasq[0].addnmount='/etc/anti-ad/anti-ad-for-dnsmasq.conf'
uci commit dhcp

dnsmasq --test -C /var/etc/dnsmasq.conf.cfg01411c
/etc/init.d/dnsmasq restart
```

如果有多个 `/var/etc/dnsmasq.conf.*`，应以当前 dnsmasq 进程 `-C` 参数指向的文件为准。

## 自动更新

已新增更新脚本：

```sh
/etc/anti-ad/update.sh
```

脚本逻辑：

1. 下载新规则到 `/tmp`。
2. 检查文件大小是否大于 `100000` 字节。
3. 检查是否包含 `address=/` 规则。
4. 使用 `dnsmasq --test -C "$TMP"` 检查下载文件语法。
5. 使用 `cmp -s "$TMP" "$DEST"` 逐字节比较新旧文件。
6. 文件无变化时直接退出，不写闪存，不重启 dnsmasq。
7. 文件有变化时替换规则文件。
8. 再检查完整 dnsmasq 配置。
9. 通过后重启 dnsmasq。
10. 出错时保留或恢复旧规则。

自动更新任务：

```cron
23 4 * * * /etc/anti-ad/update.sh >/dev/null 2>&1 #anti-ad-cron-task
```

含义是每天凌晨 `04:23` 检查一次。规则无变化时不会写入闪存，也不会重启 dnsmasq。

手动执行：

```sh
/etc/anti-ad/update.sh
```

日志查看：

```sh
logread -e anti-ad
```

## 验证命令

确认 include 和沙箱挂载：

```sh
grep -nF 'conf-file=/etc/anti-ad/anti-ad-for-dnsmasq.conf' /etc/dnsmasq.conf
uci -q show dhcp.@dnsmasq[0] | grep addnmount
ps w | grep '[u]jail.*dnsmasq'
```

确认 dnsmasq 语法：

```sh
dnsmasq --test -C /var/etc/dnsmasq.conf.cfg01411c
```

确认广告域名被拦截：

```sh
nslookup doubleclick.net 127.0.0.1
```

期望结果：

```text
server can't find doubleclick.net: NXDOMAIN
```

确认普通域名仍正常解析：

```sh
nslookup baidu.com 127.0.0.1
```

确认 OpenClash fake-ip 路径仍正常：

```sh
nslookup anyrouter.top 127.0.0.1
```

在 fake-ip 模式下，期望返回 `198.18.0.0/16` 内的 fake-ip。

## 回滚方法

撤掉 anti-AD 时需要同时删除 include、addnmount、cron 和脚本文件。

删除 `/etc/dnsmasq.conf` 中这一行：

```conf
conf-file=/etc/anti-ad/anti-ad-for-dnsmasq.conf
```

删除 UCI 挂载：

```sh
uci del_list dhcp.@dnsmasq[0].addnmount='/etc/anti-ad/anti-ad-for-dnsmasq.conf'
uci commit dhcp
```

删除 cron 中这一行：

```cron
23 4 * * * /etc/anti-ad/update.sh >/dev/null 2>&1 #anti-ad-cron-task
```

重启 cron 和 dnsmasq：

```sh
/etc/init.d/cron restart
dnsmasq --test -C /var/etc/dnsmasq.conf.cfg01411c
/etc/init.d/dnsmasq restart
```

可选删除规则目录：

```sh
rm -rf /etc/anti-ad
```

如果只删除 `addnmount`，但保留 `/etc/dnsmasq.conf` 中的 `conf-file=...`，dnsmasq 下次在 `ujail` 内重启时可能读不到规则文件并启动失败。因此回滚时必须成组处理。

## 注意事项

- 不要把 anti-AD 放进 `/tmp/dnsmasq.cfg01411c.d` 作为长期配置；这是运行时目录，可能被重建。
- 不建议修改 `dhcp.@dnsmasq[0].confdir`，避免影响 OpenClash 注入的 dnsmasq 片段。
- 不建议把 2.9MB 规则直接合并进 `/etc/dnsmasq.conf`，主配置会变得难维护。
- 自动更新当前为每天凌晨检查一次。脚本会先比较新旧文件，规则无变化时不会覆盖文件或重启 dnsmasq。
- `addnmount` 只挂载单个规则文件，不挂载整个 `/etc/anti-ad` 目录，影响范围更小。
