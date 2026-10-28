# Note Station Editor Enhancer

> 给 **Synology Note Station Client（macOS）** 加 Markdown、一键美化与代码语法高亮。一键安装、一键还原。

非官方社区补丁项目，与 Synology 无关联。仓库只包含补丁脚本与插件源码，**不包含任何官方安装包或二进制文件**。

| 能力 | 触发方式 | 说明 |
|---|---|---|
| **Markdown 输入转换** | 编辑器工具栏第一个图标（M↓）开关，**深色 = 已开启，浅灰 = 已关闭** | 行首 `# ` `- ` `1. ` `> ` `---` ` ``` ` `- [ ]` 自动变格式；行内 `**粗**` `*斜*` `~~删~~` `` `码` `` 即时转换 |
| **Markdown 粘贴识别** | 直接粘贴 | 粘贴 Markdown 文本自动转成排版好的笔记；按住 **Option** 粘贴 = 原样 |
| **一键美化** | 工具栏第二个图标（四角星，深色常显）/ `Cmd+Alt+B` | 字体、字号 15px、行距 1.85、段距、标题层级、列表、引用、表格（表头底色 + 斑马纹）全部写成内联样式；**按住 Option 只美化表格** |
| **代码块格式化 + 语法高亮** | 跟随「一键美化」，粘贴代码块时也会自动执行一次 | 自动识别语言（Java / JS / TS / Python / Go / Rust / C / C++ / C# / PHP / Ruby / SQL / Shell / JSON / YAML / CSS / HTML / XML）；Tab→4 空格、清行尾空白、压空行、JSON 重排；注释 / 字符串 / 数字 / 关键字 / 方法名 / 标签 / 属性分色 |

美化与粘贴写入的都是**内联样式**，所以 DSM 网页版、手机 App、导出 HTML 三端外观一致。笔记存储格式仍是 Note Station 原生 HTML，同步、附件、图表、待办不受影响。

---

## 环境要求

- macOS（Intel / Apple Silicon 均可）
- Note Station 客户端装在 `/Applications/Synology Note Station Client.app`
- `python3`（系统自带或用 `xcode-select --install` 安装；仅用标准库，无需 pip）

已验证版本：**3.0.0-883**（Electron 37 / TinyMCE 4.5.7）。
其它版本先跑 `--check`，锚点对不上会明确报错并**不改任何文件**。

## 用法

把整个 `note-station-editor-enhancer` 文件夹拷到目标电脑，然后：

```sh
cd note-station-editor-enhancer
./install.command --check     # 1. 先看兼容性（只读，不改文件）
./install.command             # 2. 安装（弹管理员授权）
./install.command --restore   # 出问题一键还原
```

也可以直接双击 `install.command`（第一次可能要在「系统设置 → 隐私与安全性」里允许）。
`restore.command` 就是 `--restore` 的快捷方式。

装完打开 App，编辑器工具栏最左侧会出现两个图标：

```
[撤销] [重做] | [M↓] [☆] | 其它原有按钮...
```

## 套件结构

```
note-station-editor-enhancer/
├── install.command          # 安装 / 检查 / 还原 入口
├── restore.command          # 还原快捷方式
├── lib/
│   ├── asar_tool.py         # 纯标准库的 asar 解包 / 重打包 / 自检
│   ├── build_patch.py       # 放插件 + 追加样式 + 改 notestation.js
│   ├── selfcheck.py         # 只读兼容性检查
│   └── apply_root.sh        # 提权后的实际执行体
├── patch/
│   ├── syno_markdown/plugin.min.js   # Markdown 输入 / 粘贴转换
│   ├── syno_beautify/plugin.min.js   # 一键美化
│   └── content_css/note_content_patch.css  # 表格统一样式
└── backup/                  # 首次安装自动生成：app.asar.<版本>.orig.bak
```

安装做的事：

1. `selfcheck.py` 判断版本与锚点 → 不匹配直接退出
2. 备份 `app.asar` 到 `backup/`
3. 解包 → 放入两个插件 → 追加表格 CSS → 修改 `notestation.js` 三处 → 重打包 → 逐文件自检
4. 写回应用，`codesign --force --deep -s -` 重签（adhoc），清除 quarantine

## 必须知道的几件事

1. **重签名后首次启动会弹钥匙串授权**，输入登录密码并选「始终允许」；没授权时窗口会是白屏。
2. **应用自动更新会覆盖补丁**（beta 通道）。升级后重跑一次 `./install.command` 即可，插件与备份都还在。
3. 官方不支持改 asar。原始 `app.asar` 已备份在 `backup/`，`--restore` 可回滚；笔记数据全在 NAS 上，不会丢。
4. 美化会覆盖表格单元格原有的手设底色 / 字号，后悔用 `Cmd+Z`。
5. 新增按钮的图标是内联 SVG（data URI），颜色 `#98a0a9`、描边 1.2，与皮肤自带图标对齐；MD 按钮有深浅两套（`ICON_URI_MD_ON` / `ICON_URI_MD_OFF`），美化按钮为深色 `ICON_URI_BT`。
6. **代码高亮是把着色写成 `span` 的内联样式**，所以随笔记同步、三端一致；副作用是在已着色的代码里继续打字会沿用该 token 的颜色（比如在注释末尾继续输入仍是灰色斜体）。改完内容再点一次「美化」就会重新着色。代码块识别不出语言时按纯文本处理，不会乱上色。

## 常见问题

| 现象 | 处理 |
|---|---|
| 双击 `install.command` 提示「无法打开，因为它来自身份不明的开发者」 | 右键 →「打开」，或先执行 `xattr -dr com.apple.quarantine note-station-editor-enhancer` |
| 提示 `Operation not permitted` / 没有权限 | 用 `sh install.command`，或确认脚本弹出了管理员授权框 |
| 提示「锚点不匹配，该版本未适配」 | 该 App 版本改了内部结构，脚本已中止且未改任何文件；等适配后再装 |
| 装完窗口白屏 | 钥匙串授权弹窗被忽略了：退出 App 重开，输入登录密码并选「始终允许」 |
| 提示缺少 python3 | `xcode-select --install` |

## 已验证流程

在本机（3.0.0-883）跑过完整闭环：`--check` → 安装 → 校验工具栏图标 → `--restore`（还原后 asar 哈希与备份完全一致）→ 再次安装。
另外把 zip 解压到任意目录重跑安装也已验证（脚本全部使用自身所在目录，与路径无关）。

## 改插件后重新分发

直接改 `patch/` 下的文件，然后在目标机重跑 `./install.command`（脚本每次都是从备份还原成干净基线再打补丁，重复执行幂等，不会叠加）。

## 免责声明

- 本项目与 Synology（群晖科技）无关联，未获其授权或认可，属个人自用改造的整理版本。
- **不分发**任何官方安装包、`app.asar` 或其它二进制文件；安装脚本只在用户本机对已安装的客户端做本地修改。
- 修改后应用为 adhoc 签名，可能影响自动更新与部分系统的信任判断；请自行评估风险，重要笔记先做备份。
- "Synology"、"Note Station" 为其各自权利人的商标，此处仅用于说明兼容对象。

## License

[MIT](LICENSE) © 2026 xuxiaolei
