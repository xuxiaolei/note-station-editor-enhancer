# Note Station Editor Enhancer

> 给 **Synology Note Station Client（macOS）** 加 Markdown、一键美化、代码语法高亮与 Mermaid 图表。一键安装、一键还原。

非官方社区补丁项目，与 Synology 无关联。仓库只包含补丁脚本与插件源码，**不包含任何官方安装包或二进制文件**。

## 背景：为什么会有这个补丁

Note Station 的桌面客户端是 Electron + TinyMCE 4 的富文本编辑器，群晖多年没有实质更新，既不支持 Markdown，也没有插件机制。而笔记又都躺在 NAS 上，换客户端意味着迁移全部笔记与附件，成本比想象中高。

真正在写笔记时，撞上的是这几件事：

| 痛点 | 具体表现 |
|---|---|
| **写了 Markdown 不生效** | 手打 `## 标题`、`- 列表`、`**粗体**`，出来就是一串符号；从 GitHub、Notion、ChatGPT、编辑器里复制过来的内容粘进去还是纯文本，只能一条条手工改成格式 |
| **表格难读** | 默认表格表头没有区分、没有斑马纹，边框与留白松散，几行数据就看串行 |
| **代码块没法看** | 只有等宽字体、没有语法着色，几十行 Java / SQL 一眼看不出结构；粘贴来的代码还常带 Tab 缩进和成片空行 |
| **排版靠手调** | 字号、行距、段距、标题层级每篇都要重设一遍，同一本笔记本里风格都统一不了 |
| **想画图只能截图** | 系统架构、调用链、时序这些关系图，画在别处只能截图贴进来，又大又糊、搜索不到文字 |

## 它怎么解决

| 做法 | 说明 |
|---|---|
| **不换编辑器，只打补丁** | 在原有 TinyMCE 4 上挂三个插件（`syno_markdown` / `syno_beautify` / `syno_mermaid`），工具栏只多三个图标，其它交互一律不动 |
| **样式写进内容本身** | 效果全部是**内联样式**（Mermaid 图则是内嵌图片），不是本地 CSS 覆盖——所以同步到 DSM 网页版、手机 App、导出 HTML 后外观一致，不会「只有这台 Mac 上好看」 |
| **不动笔记格式** | 存的仍是 Note Station 原生 HTML，附件、图表、待办、同步照旧；安装前自动备份 `app.asar`，`--restore` 一条命令回到原版 |

## 能力

| 能力 | 触发方式 | 说明 |
|---|---|---|
| **Markdown 输入转换** | 编辑器工具栏第一个图标（M↓）开关，**深色 = 已开启，浅灰 = 已关闭** | 行首 `# ` `- ` `1. ` `> ` `---` ` ``` ` `- [ ]` 自动变格式；行内 `**粗**` `*斜*` `~~删~~` `` `码` `` 即时转换 |
| **Markdown 粘贴识别** | 直接粘贴 | 粘贴 Markdown 文本自动转成排版好的笔记；按住 **Option** 粘贴 = 原样 |
| **一键美化** | 工具栏第二个图标（四角星，深色常显）/ `Cmd+Alt+B` | 字体、字号 15px、行距 1.85、段距、标题层级、列表、引用、表格（表头底色 + 斑马纹）全部写成内联样式；**按住 Option 只美化表格** |
| **代码块格式化 + 语法高亮** | 跟随「一键美化」，粘贴代码块时也会自动执行一次 | 自动识别语言（Java / JS / TS / Python / Go / Rust / C / C++ / C# / PHP / Ruby / SQL / Shell / JSON / YAML / CSS / HTML / XML）；Tab→4 空格、清行尾空白、压空行、JSON 重排；注释 / 字符串 / 数字 / 关键字 / 方法名 / 标签 / 属性分色 |
| **Mermaid 图表** | 工具栏第三个图标（流程图形状）/ 双击已有的图 | 画流程图、时序图、甘特图、类图、状态图等；边写边预览，插入为图片；**离线渲染**，不访问任何 CDN；已兼容 Note Station 页面里 Prototype.js 造成的样式污染，插入后不会裂图 |

---

## 环境要求

- macOS（Intel / Apple Silicon 均可）
- Note Station 客户端装在 `/Applications/Synology Note Station Client.app`
- `python3`（系统自带或用 `xcode-select --install` 安装；仅用标准库，无需 pip）

已验证版本：**3.0.0-883**（Electron 37 / TinyMCE 4.5.7）。
其它版本先跑 `--check`，锚点对不上会明确报错并**不改任何文件**。

## 用法

从 [Releases](https://github.com/xuxiaolei/note-station-editor-enhancer/releases/latest) 下载 `note-station-editor-enhancer-*.zip` 并解压（也可以直接 clone 本仓库），然后：

```sh
cd note-station-editor-enhancer
./install.command --check     # 1. 先看兼容性（只读，不改文件）
./install.command             # 2. 安装（弹管理员授权）
./install.command --restore   # 出问题一键还原
```

也可以直接双击 `install.command`（第一次可能要在「系统设置 → 隐私与安全性」里允许）。
`restore.command` 就是 `--restore` 的快捷方式。

装完打开 App，编辑器工具栏最左侧会出现三个图标：

```
[撤销] [重做] | [M↓] [☆] [流程图] | 其它原有按钮...
```

### Mermaid 图表怎么用

1. 点工具栏第三个图标（流程图形状）→ 弹出「Mermaid 图表」对话框，左边写源码、右边实时预览。
2. 写好后点「插入」，图会作为图片写进笔记；**源码保存在图片的 `data-mermaid` 属性里**，随时可改。
3. **双击**已插入的图 → 重新打开对话框改源码，点「更新」即就地替换。
4. 对话框左下角「放大预览」：大图在正文里会被缩到栏宽（文字可能很小），放大后可按 100% 原尺寸滚动查看。
5. 粘贴 Markdown 里的 ```` ```mermaid ```` 围栏代码块，点「一键美化」也会转成图。
6. **v3.3.0 及更早版本插入的图如果是裂图（只剩「Mermaid 图表」几个字），不需要手工重画**：升级到 v3.3.1 后打开那篇笔记，插件会自动识别失效的图、用图片里存的源码重新渲染并原地替换。

支持 mermaid 的全部图类型：flowchart / sequence / class / state / er / gantt / pie / journey 等。

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
│   ├── syno_beautify/plugin.min.js   # 一键美化（含代码高亮）
│   ├── syno_mermaid/plugin.min.js    # Mermaid 图表
│   ├── syno_mermaid/mermaid.min.js  # mermaid 11 渲染库（离线内置，3.4 MB）
│   └── content_css/note_content_patch.css  # 表格统一样式
├── test/
│   └── mermaid/             # Mermaid 回归测试（headless Chrome，10 条断言）
└── backup/                  # 首次安装自动生成：app.asar.<版本>.orig.bak
```

安装做的事：

1. `selfcheck.py` 判断版本与锚点 → 不匹配直接退出
2. 备份 `app.asar` 到 `backup/`
3. 解包 → 放入三个插件 → 追加表格 CSS → 修改 `notestation.js`（插件串 2 处 + 工具栏 1 处 + `img` 元素规则）→ 重打包 → 逐文件自检
4. 写回应用，`codesign --force --deep -s -` 重签（adhoc），清除 quarantine

## 必须知道的几件事

1. **重签名后首次启动会弹钥匙串授权**，输入登录密码并选「始终允许」；没授权时窗口会是白屏。
2. **应用自动更新会覆盖补丁**（beta 通道）。升级后重跑一次 `./install.command` 即可，插件与备份都还在。
3. 官方不支持改 asar。原始 `app.asar` 已备份在 `backup/`，`--restore` 可回滚；笔记数据全在 NAS 上，不会丢。
4. 美化会覆盖表格单元格原有的手设底色 / 字号，后悔用 `Cmd+Z`。
5. 新增按钮的图标是内联 SVG（data URI），颜色 `#98a0a9`、描边 1.2，与皮肤自带图标对齐；MD 按钮有深浅两套（`ICON_URI_MD_ON` / `ICON_URI_MD_OFF`），美化按钮为深色 `ICON_URI_BT`。
6. **代码高亮是把着色写成 `span` 的内联样式**，所以随笔记同步、三端一致；副作用是在已着色的代码里继续打字会沿用该 token 的颜色（比如在注释末尾继续输入仍是灰色斜体）。改完内容再点一次「美化」就会重新着色。代码块识别不出语言时按纯文本处理，不会乱上色。
7. **Mermaid 图是以 `data:image/svg+xml;base64` 图片存的**，不是内联 SVG —— TinyMCE 4 的 schema 会把 `<svg>` 整块剥掉，存进去保存后图就没了。代价是：图的大小在插入时就固定，正文栏宽下大图会被压缩、文字很小，需要看清就双击图再点「放大预览」。源码存在图片的 `data-mermaid` 属性里，不会丢。
8. **mermaid 渲染库内置在插件目录里（3.4 MB）**，首次点击时才加载并解析；不访问任何网络，离线可用。
9. **渲染时做了「样式净化」**：Note Station 页面里加载了 Prototype.js 1.7.3，它给 `Array.prototype` 挂了 `each`；mermaid 的解析器会把数组里的函数对象当成样式值拼进 SVG 的 `style="..."` 属性，属性里一旦出现裸的 `<` / `&`，SVG 就不再是合法 XML —— 浏览器拒绝渲染，笔记里就变成一张裂图（预览里则表现为「只有连线、没有节点方框」）。插件在渲染期间临时拦截 `Array.prototype` 的 `join` / `reduce` / `reduceRight`，把函数元素替换为空串，渲染结束立即还原；渲染结果还会做一次 XML 合法性校验，万一仍不合法会先尝试转义修复，修复不了就**直接报错而不是插一张裂图**。

## 常见问题

| 现象 | 处理 |
|---|---|
| 双击 `install.command` 提示「无法打开，因为它来自身份不明的开发者」 | 右键 →「打开」，或先执行 `xattr -dr com.apple.quarantine note-station-editor-enhancer` |
| 提示 `Operation not permitted` / 没有权限 | 用 `sh install.command`，或确认脚本弹出了管理员授权框 |
| 提示「锚点不匹配，该版本未适配」 | 该 App 版本改了内部结构，脚本已中止且未改任何文件；等适配后再装 |
| 装完窗口白屏 | 钥匙串授权弹窗被忽略了：退出 App 重开，输入登录密码并选「始终允许」 |
| 提示缺少 python3 | `xcode-select --install` |
| Mermaid 预览里只有连线、没有节点方框 | v3.3.0 的已知缺陷（Prototype.js 污染了节点样式），升级到 v3.3.1 |
| Mermaid 插入正文后变成裂图（只剩「Mermaid 图表」几个字） | v3.3.0 的已知缺陷。升级到 v3.3.1 后打开该笔记，插件会自动重新渲染并替换；若仍未恢复，双击图重新插入即可（源码存在图的 `data-mermaid` 属性里，不会丢） |
| 点了 Mermaid 图标没反应、一直转圈 | 多半是内嵌的 mermaid 库没加载上（首次点击需要几秒解析 3.4 MB）。先关掉应用重开再试；仍不行请附上控制台报错反馈 |

## 已验证流程

在本机（3.0.0-883）跑过完整闭环：`--check` → 安装 → 校验工具栏图标 → `--restore`（还原后 asar 哈希与备份完全一致）→ 再次安装。
另外把 zip 解压到任意目录重跑安装也已验证（脚本全部使用自身所在目录，与路径无关）。

Mermaid 部分额外做了三层验证：

1. **应用现场复现** —— 在 headless Chrome 里用应用内**真实的** `prototype.js` + `mermaid.min.js` + 插件，跑用户那张 33 节点的 whale 依赖图：SVG 无污染、是合法 XML、33 个节点方框齐全、data URI 图片能正常加载（1921×1408）。
2. **对照实验** —— 把样式净化临时关掉（即 v3.3.0 的行为）再跑同一张图：SVG 从 95 KB 膨胀到 413 KB 且检出 Prototype 污染，证明净化确实是在解决真实问题、而不是碰巧。
3. **回归测试** —— 仓库内 `test/mermaid/` 下的 10 条断言（渲染成功 / 无污染 / 体积正常 / XML 合法 / 有节点 / 图片可加载 / `buildImg` 输出完整等），跑 `./test/mermaid/run_test.sh`（需要装了 Chrome）；修复开启时全绿、关闭时必然报红。

## 改插件后重新分发

直接改 `patch/` 下的文件，然后在目标机重跑 `./install.command`（脚本每次都是从备份还原成干净基线再打补丁，重复执行幂等，不会叠加）。

## 第三方组件

| 组件 | 版本 | 许可 | 用途 |
|---|---|---|---|
| [mermaid](https://github.com/mermaid-js/mermaid) | 11.17.2 | MIT（许可全文见 `patch/syno_mermaid/LICENSE.mermaid`） | Mermaid 图表渲染（`patch/syno_mermaid/mermaid.min.js`，内置离线使用） |

## 更新日志

| 版本 | 内容 |
|---|---|
| **v3.3.1** | **修复 Mermaid 插入正文后裂图 / 预览只有连线没有节点方框** —— 根因是 Note Station 页面里的 Prototype.js 污染了 mermaid 的样式数组。渲染期间临时拦截 `Array.prototype` 的 `join` / `reduce` / `reduceRight`，渲染后校验 SVG 是否为合法 XML；并能自动修复旧版本留下的失效图 |
| v3.3.0 | Mermaid 图表插件（离线渲染）+ 修复库加载路径 + 放大预览 |
| v3.2.0 | Markdown 输入 / 粘贴转换、一键美化、代码块格式化与语法高亮 |

## 免责声明

- 本项目与 Synology（群晖科技）无关联，未获其授权或认可，属个人自用改造的整理版本。
- **不分发**任何官方安装包、`app.asar` 或其它二进制文件；安装脚本只在用户本机对已安装的客户端做本地修改。
- 修改后应用为 adhoc 签名，可能影响自动更新与部分系统的信任判断；请自行评估风险，重要笔记先做备份。
- "Synology"、"Note Station" 为其各自权利人的商标，此处仅用于说明兼容对象。

## License

[MIT](LICENSE) © 2026 xuxiaolei
