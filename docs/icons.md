# 策略组图标（HOMOMIX Large）

> 仓库：[Vbaethon/HOMOMIX](https://github.com/Vbaethon/HOMOMIX) — 面向 Mihomo / MetaCubeX / Zashboard 的彩色图标集  
> 面板图标包（可选）：`https://raw.githubusercontent.com/Vbaethon/HOMOMIX/main/HOMOMIX.json`

本仓库 **hybrid 主模板与全部 variants** 的 `proxy-groups[].icon` 统一使用 HOMOMIX **Color/Large**（满高版）。  
`demo/` 下第三方样例配置**不**在此约束内。

---

## CDN 链接格式

默认 jsDelivr（与规则集同源加速）：

```
https://cdn.jsdelivr.net/gh/Vbaethon/HOMOMIX@main/Icon/Color/Large/{图标名}.png
```

GitHub Raw：

```
https://raw.githubusercontent.com/Vbaethon/HOMOMIX/main/Icon/Color/Large/{图标名}.png
```

| 路径 | 说明 |
|------|------|
| `Icon/Color/Large/` | 满高版本（**本项目默认**） |
| `Icon/Color/` | 等高版本（更小；仅在明确需要时使用） |

新增图标时务必使用 **Large** 路径下的同名文件，不要写回非 Large 路径。

---

## 本项目策略组 → 图标映射

| 策略组 | 文件名 | CDN（jsDelivr Large） |
|--------|--------|------------------------|
| 节点选择 | `Link.png` | `…/Icon/Color/Large/Link.png` |
| 手动切换 | `Remote.png` | `…/Icon/Color/Large/Remote.png` |
| 自动测速 | `Auto_Link.png` | `…/Icon/Color/Large/Auto_Link.png` |
| DNS | `Network.png` | `…/Icon/Color/Large/Network.png` |
| AI | `AI.png` | `…/Icon/Color/Large/AI.png` |
| 流媒体 | `Stream.png` | `…/Icon/Color/Large/Stream.png` |
| 游戏平台 | `Game.png` | `…/Icon/Color/Large/Game.png` |
| 电报消息 | `Telegram.png` | `…/Icon/Color/Large/Telegram.png` |
| 苹果服务 | `Apple.png` | `…/Icon/Color/Large/Apple.png` |
| 谷歌服务 | `Google.png` | `…/Icon/Color/Large/Google.png` |
| 微软服务 | `Microsoft.png` | `…/Icon/Color/Large/Microsoft.png` |
| OneDrive | `OneDrive.png` | `…/Icon/Color/Large/OneDrive.png` |
| 香港节点 | `Hong_Kong.png` | `…/Icon/Color/Large/Hong_Kong.png` |
| 美国节点 | `USA.png` | `…/Icon/Color/Large/USA.png` |
| 日本节点 | `Japan.png` | `…/Icon/Color/Large/Japan.png` |
| 新加坡节点 | `Singapore.png` | `…/Icon/Color/Large/Singapore.png` |
| 其他节点 | `Global.png` | `…/Icon/Color/Large/Global.png` |
| 全球直连 | `DIRECT.png` | `…/Icon/Color/Large/DIRECT.png` |
| 广告拦截 | `Adblock.png` | `…/Icon/Color/Large/Adblock.png` |
| 漏网之鱼 | `Fish.png` | `…/Icon/Color/Large/Fish.png` |

完整 URL 示例：

```yaml
icon: "https://cdn.jsdelivr.net/gh/Vbaethon/HOMOMIX@main/Icon/Color/Large/Link.png"
```

---

## 新增 / 换图标时的硬约束

1. **先确认 Large 文件存在**（文件名大小写敏感），任选其一：
   - 浏览 [Icon/Color/Large](https://github.com/Vbaethon/HOMOMIX/tree/main/Icon/Color/Large)
   - `gh api repos/Vbaethon/HOMOMIX/contents/Icon/Color/Large/<Name>.png`
   - `HEAD` / 浏览器打开最终 CDN URL，期望 **HTTP 200** 且有 body
2. **不要**假设 Qure 旧文件名仍可用（例如 `US.png` → 现为 `USA.png`，`Direct.png` → `DIRECT.png`）。
3. 图标名与策略组名**无强制对应**，只改 `icon` URL，不改组名与分流。
4. hybrid 与各 variants 的同名策略组保持**同一图标 URL**，避免 UI 不一致。
5. 远程引用默认仅限 `Vbaethon/HOMOMIX` 的 **Large** 路径；换源或 vendoring 前先核授权与署名（见 `AGENTS.md`）。

### 快速校验（PowerShell）

对当前模板中所有图标做 HEAD 探测：

```powershell
$urls = [System.Collections.Generic.HashSet[string]]::new()
Get-ChildItem rules -Recurse -Filter *.yaml | ForEach-Object {
  Get-Content $_.FullName | ForEach-Object {
    if ($_ -match 'icon:\s*"(https://[^"]+)"') { [void]$urls.Add($Matches[1]) }
  }
}
$fail = @()
foreach ($u in ($urls | Sort-Object)) {
  if ($u -notmatch '/Icon/Color/Large/') { $fail += "NOT_LARGE $u"; continue }
  try {
    $r = Invoke-WebRequest -Uri $u -Method Head -UseBasicParsing -TimeoutSec 25
    if ([int]$r.StatusCode -ne 200) { $fail += "$u -> $($r.StatusCode)" }
    else { Write-Host "OK  $([IO.Path]::GetFileName($u))" }
  } catch { $fail += "$u -> $($_.Exception.Message)" }
}
if ($fail.Count) { $fail; throw "icon check failed" }
```

---

## 从 Qure / 等高版迁来的对照（历史）

旧默认源为 [Koolson/Qure](https://github.com/Koolson/Qure) `IconSet/Color`。主要文件名差异：

| 旧 Qure | 现 HOMOMIX（Large） |
|---------|---------------------|
| `Proxy.png` | `Link.png` |
| `Available.png` | `Remote.png` |
| `Auto.png` | `Auto_Link.png` |
| `Hijacking.png` | `Network.png` |
| `ForeignMedia.png` | `Stream.png` |
| `Apple_1.png` | `Apple.png` |
| `US.png` | `USA.png` |
| `Direct.png` | `DIRECT.png` |
| `AdBlack.png` | `Adblock.png` |
| `Final.png` | `Fish.png` |
| 同名：`AI` / `Game` / `Telegram` / `Google` / `Microsoft` / `OneDrive` / `Hong_Kong` / `Japan` / `Singapore` / `Global` | 仅换 base → `Icon/Color/Large/` |

---

## 参考

- HOMOMIX 主页：https://github.com/Vbaethon/HOMOMIX  
- Large 目录：https://github.com/Vbaethon/HOMOMIX/tree/main/Icon/Color/Large  
- 图标预览：见上游 README 内嵌表  
