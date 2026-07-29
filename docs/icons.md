# 策略组图标（Qure Color）

> 仓库：[Koolson/Qure](https://github.com/Koolson/Qure)
> Qure Color 图标库：`https://raw.githubusercontent.com/Koolson/Qure/master/Other/QureColor.json`
> Qure mini 图标库：`https://raw.githubusercontent.com/Koolson/Qure/master/Other/Quremini.json`

本仓库 **hybrid 主模板与全部 variants** 的 `proxy-groups[].icon` 统一使用
Qure **Color**。`demo/` 下的第三方示例配置不在此约束内。

`QureColor.json` 与 `Quremini.json` 是 Quantumult X 的图标库索引，不能直接写进
Mihomo 的 `icon:`。Mihomo 模板必须引用具体的 PNG 文件。

---

## URL 格式

模板使用 GitHub Raw：

```text
https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/{图标名}.png
```

例如：

```yaml
icon: "https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Rocket.png"
```

需要 CDN 时可将同一文件写成：

```text
https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/{图标名}.png
```

同一批模板应保持相同的 URL 基址，不要混用 Raw、jsDelivr 和第三方代理。

---

## 本项目策略组 → 图标映射

映射以常见的 Qure Color Mihomo 配置风格为基础：主选择使用 `Rocket`，服务组优先
使用具体品牌图标；示例未覆盖的 Sift 策略组按 Qure 图标语义补齐。

| 策略组 | 文件名 | 说明 |
| --- | --- | --- |
| 节点选择 | `Rocket.png` | 主代理选择 |
| 手动切换 | `Available.png` | 手动选择可用节点 |
| 自动测速 | `Auto.png` | 自动测速 |
| DNS | `Hijacking.png` | DNS 接管与出口 |
| AI | `ChatGPT.png` | AI 服务 |
| 流媒体 | `Streaming.png` | 国际流媒体 |
| 游戏平台 | `Game.png` | 游戏平台 |
| Telegram | `Telegram_X.png` | Telegram 服务 |
| 苹果服务 | `Apple_1.png` | Apple 服务 |
| 谷歌服务 | `Google_Search.png` | Google 服务 |
| 微软服务 | `Windows_11.png` | Microsoft 服务 |
| OneDrive | `OneDrive.png` | OneDrive 服务 |
| 香港节点 | `Hong_Kong.png` | 香港地区节点 |
| 美国节点 | `United_States.png` | 美国地区节点 |
| 日本节点 | `Japan.png` | 日本地区节点 |
| 新加坡节点 | `Singapore.png` | 新加坡地区节点 |
| 其他节点 | `Airport.png` | 其他地区节点集合 |
| 直连 | `Direct.png` | 直连出口 |
| 广告拦截 | `AdBlack.png` | 广告拦截 |
| 漏网之鱼 | `Final.png` | 最终兜底 |

图标只表达 UI 语义，与策略组名称没有强制对应关系。更换图标时只改 `icon` URL，
不要改组名、组成员或路由规则。

---

## 新增或更换图标

1. 在 [Qure Color 目录](https://github.com/Koolson/Qure/tree/master/IconSet/Color)
   中确认文件存在。
2. 文件名大小写敏感；以仓库中的真实文件名为准。
3. 浏览器打开最终 Raw URL，确认返回图片而不是 404 页面。
4. hybrid 与 variants 的同名策略组必须使用同一个图标 URL。
5. 不要把图标库 JSON 地址写进 Mihomo 的 `icon:`。
6. 远程图标引用仅使用 `Koolson/Qure`；换源或 vendoring 前先核对授权与署名。

---

## Quantumult X 图标库

Quantumult X 可订阅完整图标库，然后在客户端中为订阅条目或自定义策略选择图标。

### PROXY 订阅

机场或代理服务器订阅条目推荐使用 Qure mini：

```text
https://raw.githubusercontent.com/Koolson/Qure/master/Other/Quremini.json
```

这里的“PROXY 订阅”指 Quantumult X 中的机场/节点订阅条目，不是 Mihomo 的策略组。

### 自定义策略

自定义策略组推荐使用 Qure Color：

```text
https://raw.githubusercontent.com/Koolson/Qure/master/Other/QureColor.json
```

添加方法：

1. 长按订阅条目或自定义策略。
2. 选择“图标”。
3. 点击右上角 `+`。
4. 填入相应的图标库订阅地址。
5. 从图标库中选择图标。

---

## 校验

检查模板中不存在旧图标源：

```bash
rg -n 'Vbaethon|HOMOMIX|Icon/Color/Large' rules
```

检查模板没有误用图标库 JSON：

```bash
rg -n 'Quremini\.json|QureColor\.json' rules
```

检查所有模板的图标 URL：

```bash
rg -n 'icon:' rules --glob '*.yaml'
```

逐一验证唯一 URL 时，应跟随重定向并要求 HTTP 成功：

```bash
rg -o 'https://[^" ]+\.png' rules --glob '*.yaml' \
  | sed 's/^[^:]*://' \
  | sort -u \
  | while read -r url; do
      curl -fsSL --range 0-0 "$url" >/dev/null || exit 1
    done
```

最后运行全部模板的 Mihomo 加载验证与补丁格式检查。

---

## 参考

- Qure 主页：https://github.com/Koolson/Qure
- Qure Color：https://github.com/Koolson/Qure/tree/master/IconSet/Color
- Qure mini：https://github.com/Koolson/Qure/tree/master/IconSet/mini
