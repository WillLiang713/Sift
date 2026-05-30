# Sift

面向 Mihomo 的无节点配置模板。模板只提供策略组、规则提供商和分流规则；节点请通过订阅合并或手动补充，DNS 与 fake-ip 行为建议交由客户端管理。

## 模板

### Full.yaml

完整模板，包含 AI、流媒体、Google、Apple、Microsoft、开发工具、游戏平台和地区节点组。

```text
https://raw.githubusercontent.com/WillLiang713/Sift/main/Full.yaml
```

### Mini.yaml

极简模板，仅保留节点选择、自动测速、AI、流媒体和漏网之鱼。

```text
https://raw.githubusercontent.com/WillLiang713/Sift/main/Mini.yaml
```

## 分流

### Full.yaml

1. 局域网 / 私有地址 -> `DIRECT`
2. 国内服务 / 国内游戏 / 国内域名 / 国内 IP -> `DIRECT`
3. AI -> `AI`
4. 流媒体 -> `流媒体`
5. 游戏平台 -> `游戏平台`
6. 开发工具 -> `开发工具`
7. Google / Apple / Microsoft -> 对应策略组
8. GFW -> `节点选择`
9. 其他 -> `漏网之鱼`

### Mini.yaml

1. 局域网 / 私有地址 -> `DIRECT`
2. 国内服务 / 国内游戏 / 国内域名 / 国内 IP -> `DIRECT`
3. AI -> `AI`
4. 流媒体 -> `流媒体`
5. GFW -> `节点选择`
6. 其他 -> `漏网之鱼`

## 规则来源

- DustinWin MRS：基础规则、国内服务、国内域名/IP、AI、流媒体、游戏、GFW。
- MetaCubeX MRS：`Full.yaml` 的开发工具、Google、Apple、Microsoft。
- Koolson/Qure、Orz-3/mini：策略组图标。

`rule-providers` 名称与规则文件名保持一致，例如 `category-dev` 对应 `category-dev.mrs`。

## 使用

1. 复制上方模板链接。
2. 与节点订阅合并，或手动补充 `proxies`。
3. 自建节点建议在名称中保留地区关键词，例如 `自建-HK-01` 或 `自建-日本-东京`，以便自动进入对应地区组。
4. 使用支持 Mihomo `rule-providers` 和 `RULE-SET` 的客户端加载配置。

## 验证

```bash
node --check scripts/convert.js
mihomo -t -f Full.yaml
mihomo -t -f Mini.yaml
git diff --check
```

## License

本项目以 [MIT License](./LICENSE) 发布。远程规则和图标的版权与使用条款归上游项目所有。
