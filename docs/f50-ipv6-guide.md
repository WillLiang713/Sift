# ImmortalWrt + 中兴 F50 IPv6 配置复用指南

## 1. 适用场景

本文适用于下面这种网络结构：

```text
中国移动 SIM 卡
      │
中兴 F50 随身 WiFi
      │ USB 网卡（例如 eth2）
ImmortalWrt 路由器
      │
LAN / Wi-Fi 手机和电脑
```

典型特征：

- F50 自己能够获得公网 IPv6；
- ImmortalWrt 的 USB WAN 能获得一个公网 IPv6 地址；
- 上游只提供一个共享的 `/64` 前缀，没有正常下发可供路由器继续划分的 DHCPv6-PD；
- 仅创建 DHCPv6 客户端后，路由器自身可能能用 IPv6，但 LAN 设备不能正常使用；
- 需要使用 RFC 7278 扩展前缀和 NDP 中继。

> 如果上游已经正常下发 `/60`、`/56` 等 DHCPv6-PD，应优先使用标准前缀委派，不需要照搬本文的 NDP 中继设置。

## 2. 配置目标

配置完成后应达到：

- ImmortalWrt 的 USB IPv6 接口获得公网 IPv6；
- LAN 接口获得同一 `/64` 中的路由器地址；
- 手机和电脑通过 RA/SLAAC 自动获得公网 IPv6；
- LAN 设备具有 IPv6 默认路由；
- LAN 设备能够直接访问公网 IPv6；
- IPv6 入站流量仍由 ImmortalWrt 防火墙保护。

## 3. 配置前记录

进入 ImmortalWrt：**网络 → 接口**，先确认 USB WAN 对应的设备名称。

本次实际设备是：

```text
eth2
```

不同路由器上可能显示为 `eth1`、`usb0`、`wwan0` 等，不能直接照抄设备名。

同时确认原有 USB IPv4 WAN 已经能够正常联网。本文新增的 `USB6` 是 IPv6 逻辑接口，不替代原来的 IPv4 接口。

## 4. 新建 USB6 接口

打开：**网络 → 接口 → 添加新接口**。

填写：

| 项目 | 设置 |
|---|---|
| 接口名称 | `USB6` |
| 协议 | DHCPv6 客户端 |
| 设备 | F50 对应的 USB 网卡，例如 `eth2` |

创建后进入 `USB6` 的高级设置：

| 项目 | 设置 | 原因 |
|---|---|---|
| 请求 IPv6 地址 | `try`（尝试） | 请求接口自身的公网 IPv6 地址 |
| 请求 IPv6 前缀长度 | `auto`（自动） | 尝试接收上游提供的前缀信息 |
| 释放 DHCPv6 租约 | 不释放/启用 `norelease` | 接口重连时尽量保持现有租约 |
| 扩展前缀 | 启用 | 使用 RFC 7278，把上游共享 `/64` 延伸给 LAN 使用 |

对应的关键 UCI 参数为：

```text
network.USB6.proto='dhcpv6'
network.USB6.device='eth2'
network.USB6.reqaddress='try'
network.USB6.reqprefix='auto'
network.USB6.norelease='1'
network.USB6.extendprefix='1'
```

## 5. 将 USB6 加入 WAN 防火墙区域

进入：**网络 → 防火墙 → 常规设置 → 区域**。

编辑 `wan` 区域，确认“涵盖的网络”中同时包含：

```text
USB
USB6
```

这样 USB6 会使用 WAN 区域的 IPv6 防火墙规则。不要为了测试而关闭防火墙。

## 6. 配置 USB6 的 IPv6 服务

进入：**网络 → 接口 → USB6 → DHCP 服务器 → IPv6 设置**。

设置如下：

| 项目 | 设置 | 原因 |
|---|---|---|
| 忽略此接口 | 启用 | USB6 是上游，不向 F50 提供 DHCP 服务 |
| RA 服务 | 禁用 | 不在上游接口发送路由通告 |
| DHCPv6 服务 | 禁用 | 不在上游接口充当 DHCPv6 服务器 |
| NDP 代理 | 中继模式 | 在 F50 与 LAN 之间中继 IPv6 邻居发现 |
| 指定为主接口 | 启用 | 指明 USB6 是 NDP 中继的上游接口 |

对应的关键 UCI 参数为：

```text
dhcp.USB6.ignore='1'
dhcp.USB6.master='1'
dhcp.USB6.ndp='relay'
```

“主接口”只表示 **NDP 中继的上游**，不是系统唯一 WAN，也不会阻止以后其他 WAN 接口获取地址。

## 7. 配置 LAN 的 IPv6 前缀

进入：**网络 → 接口 → LAN → 高级设置**。

将 IPv6 分配长度设置为：

```text
64
```

对应 UCI 参数：

```text
network.lan.ip6assign='64'
```

这一步让 LAN 使用扩展出来的 `/64` 前缀。IPv6 SLAAC 的标准局域网前缀通常就是 `/64`。

## 8. 配置 LAN 的 IPv6 服务

进入：**网络 → 接口 → LAN → DHCP 服务器 → IPv6 设置**。

设置如下：

| 项目 | 设置 | 原因 |
|---|---|---|
| RA 服务 | 服务器模式 | 向 LAN 设备通告 IPv6 前缀和默认网关 |
| DHCPv6 服务 | 禁用 | 客户端通过 RA + SLAAC 自动生成地址即可 |
| NDP 代理 | 中继模式 | 把 LAN 客户端的邻居发现与 USB6 上游连通 |
| 指定为主接口 | 不启用 | LAN 是中继下游，USB6 才是主接口 |
| 学习路由 | 启用 | 自动学习 LAN IPv6 客户端的位置并建立相应路由 |

对应的核心 UCI 参数为：

```text
dhcp.lan.ra='server'
dhcp.lan.dhcpv6='disabled'
dhcp.lan.ndp='relay'
```

注意：DHCPv6 服务禁用并不等于禁用 IPv6。手机和电脑仍会根据 RA，通过 SLAAC 自动生成公网 IPv6 地址。

## 9. 应用顺序

建议按以下顺序操作：

1. 新建并配置 `USB6`；
2. 把 `USB6` 加入 `wan` 防火墙区域；
3. 启用 `USB6` 的扩展前缀；
4. 把 LAN 的 IPv6 分配长度设为 `/64`；
5. 设置 USB6 为 NDP 中继主接口；
6. 设置 LAN 的 RA 服务器和 NDP 中继；
7. 保存并应用；
8. 等待约 30 秒，必要时让手机或电脑重新连接 Wi-Fi。

应用过程中网络可能短暂断开。如果 LuCI 没有自动恢复，可重新打开路由器管理地址。

## 10. 配置后的检查方法

### 10.1 在 LuCI 中检查

进入：**状态 → 概览** 或 **网络 → 接口**。

应看到：

- `USB6` 有运营商公网 IPv6 地址，例如以 `2409:` 开头；
- `USB6` 显示 `/64` IPv6 前缀；
- LAN 获得同一前缀中的地址，通常末尾为 `::1/64`；
- `USB6` 和原 USB IPv4 接口都处于运行状态。

本次成功时的结构示例：

```text
USB6 地址：       2409:xxxx:xxxx:xxxx:....../64
扩展前缀：        2409:xxxx:xxxx:xxxx::/64
LAN 路由器地址：  2409:xxxx:xxxx:xxxx::1/64
```

公网前缀可能在断网、重拨或运营商重新分配后发生变化，这是正常现象。

### 10.2 在 Windows 客户端检查

连接 ImmortalWrt 的 Wi-Fi 后运行：

```powershell
ipconfig
```

WLAN 应同时看到：

- `192.168.x.x` IPv4 地址；
- `2409:` 等运营商公网 IPv6 地址；
- `fe80:` 本地链路 IPv6 地址。

然后测试原生 IPv6：

```powershell
ping -6 2400:3200::1
ping -6 2001:4860:4860::8888
ping -6 2606:4700:4700::1111
```

能够收到回复，说明客户端地址、默认路由、上游回程和 NDP 中继均正常。

也可以检查 IPv6 默认路由：

```powershell
Get-NetRoute -InterfaceAlias WLAN -AddressFamily IPv6
```

应存在目标为 `::/0` 的默认路由。

### 10.3 SSH 只读检查

可在路由器上执行：

```sh
ubus call network.interface.USB6 status
ubus call network.interface.lan status
uci show network.USB6
uci show network.lan
uci show dhcp.USB6
uci show dhcp.lan
```

这些命令只读取状态，不会修改配置。

## 11. 常见问题排查

### 路由器有 IPv6，但 LAN 设备没有公网 IPv6

重点检查：

- `network.USB6.extendprefix='1'` 是否启用；
- LAN 的 IPv6 分配长度是否为 `64`；
- LAN 的 RA 服务是否为服务器模式；
- 客户端是否重新连接 Wi-Fi 或重新获取网络配置。

### LAN 设备获得公网 IPv6，但无法访问 IPv6 网站

这是共享 `/64` 场景中最典型的问题。重点检查：

- USB6 的 NDP 代理是否为中继模式；
- USB6 是否被指定为主接口；
- LAN 的 NDP 代理是否为中继模式；
- LAN 是否没有被误设为主接口；
- USB6 是否位于 `wan` 防火墙区域。

只启用扩展前缀，可能会出现“客户端有公网地址，但公网返回流量找不到客户端”的情况。NDP 中继用于补全这条回程路径。

### 客户端只有 `fdxx:` 地址

`fdxx:` 是 ULA 本地 IPv6 地址，不是运营商公网 IPv6。说明公网前缀没有成功传递到 LAN，应检查 USB6 的地址、扩展前缀和 LAN 的 `/64` 分配。

### DHCPv6 禁用是不是会影响 IPv6

不会。当前方案采用：

```text
RA 通告前缀和网关 + SLAAC 自动生成地址
```

DHCPv6 不是客户端获得 IPv6 地址的唯一方式。

### 开启公网 IPv6 会不会让 LAN 完全暴露

不会。设备虽然拥有公网 IPv6 地址，但 ImmortalWrt 的 WAN 防火墙默认会阻止公网主动发起的连接。只有另行添加入站放行规则后，对应服务才可能被公网访问。

## 12. 与标准 DHCPv6-PD 的区别

| 项目 | F50 共享 `/64` | 标准家庭宽带 PD |
|---|---|---|
| 上游提供内容 | 单个共享 `/64` | 通常为 `/60`、`/56` 等可路由前缀 |
| LAN 前缀来源 | RFC 7278 扩展 | DHCPv6-PD 正式委派 |
| 是否需要 NDP 中继 | 需要 | 通常不需要 |
| 转发方式 | 同一 `/64` 上的邻居发现中继 | 不同子网之间的标准 IPv6 路由 |
| 推荐原则 | 上游无 PD 时的兼容方案 | 有 PD 时优先使用 |

例如，另一台 PPPoE 路由器若已经获得真实 `/60` PD，只需把前缀正常分配给 LAN，并开启 LAN 的 RA 服务器即可，不应机械照搬 F50 的 NDP 中继配置。

## 13. 本次成功配置摘要

```text
USB6：
  协议              DHCPv6 客户端
  设备              eth2
  请求地址          try
  请求前缀          auto
  不释放租约        启用
  RFC 7278 扩展前缀 启用
  RA                禁用
  DHCPv6            禁用
  NDP               中继
  主接口            是

LAN：
  IPv6 分配长度     64
  RA                服务器模式
  DHCPv6            禁用
  NDP               中继
  主接口            否
  学习路由          启用

防火墙：
  wan 区域包含      USB、USB6
```

这套设置的核心逻辑是：**USB6 从 F50 接收共享 `/64`，LAN 通过 RA/SLAAC 使用该前缀，再由上下游 NDP 中继保证公网返回流量能够找到 LAN 客户端。**
