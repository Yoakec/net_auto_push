## Why

网络运维中经常需要同时对多台交换机批量执行命令（如巡检 `show arp`、`dis cu`），目前只能逐台手动 SSH 登录，效率极低且无法留存执行记录。需要一个小型 Web 工具实现"选设备 → 输入命令 → 并发执行 → 实时查看回显 → 自动归档"的完整闭环。

## What Changes

- 新增 FastAPI 后端，提供设备清单管理、命令下发、WebSocket 实时推送
- 新增 Vue 3 前端，分屏布局，Xterm.js 终端组件用于事件流日志和纯净回显弹窗
- 设备数据从 CSV 文件加载（`/data/` 目录），启动即用，无需每次上传
- 支持多设备并发执行命令，并发数前端可调，底层用 asyncio.Semaphore 限流
- 命令来源支持 Snippet Library（CSV 导入的命令库）和手动输入，输入框支持多行批量命令
- 执行结果以原子化 Markdown 文件归档（`/archives/日期_Task/`），方便后续搜索和比对
- 最终 PyInstaller 打包为 `.exe`，双击启动，浏览器访问

## Capabilities

### New Capabilities
- `device-inventory`: 设备清单管理 — CSV 加载、设备列表查询、按 Area/Type 筛选
- `command-execution`: 命令执行引擎 — 多设备并发 SSH 登录、命令下发、翻页处理、Fail-fast 错误中断
- `live-terminal`: 实时终端与回显 — WebSocket 推送事件流，Xterm.js 主终端 + 弹窗纯净回显 + Tab 切换多命令输出
- `snippet-library`: 命令片段库 — CSV 导入预设命令，下拉选中填入输入框，支持手动编辑
- `result-archive`: 结果归档 — 每次任务生成原子化 Markdown 文件，task_summary.json 汇总

### Modified Capabilities
<!-- Greenfield project, no existing specs to modify -->

## Impact

- **新增依赖**: netmiko, FastAPI, uvicorn, Vue 3, Vite, Tailwind CSS, Xterm.js, PyInstaller
- **部署方式**: PyInstaller 单文件 `.exe`，内嵌前端静态文件
- **数据存储**: `/data/` (CSV 设备清单), `/archives/` (Markdown 归档), 无数据库
- **目标环境**: 网络运维工程师的 Windows 专用机，本地 8000 端口访问
