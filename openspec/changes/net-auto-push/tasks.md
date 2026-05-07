## 1. 项目初始化与基础结构

- [x] 1.1 创建后端项目结构: `backend/main.py`, `backend/config.py`, `backend/models.py`, `backend/routes/`, `backend/ws/`, `backend/executor/`
- [x] 1.2 创建 `requirements.txt`: fastapi, uvicorn, netmiko, pandas, python-multipart, websockets
- [x] 1.3 搭建 Vue 3 + Vite + Tailwind + Xterm.js 工程: `frontend/` 目录，`npm create vite@latest`
- [x] 1.4 创建 `/data/` 和 `/archives/` 目录

## 2. 里程碑一: 核心骨架与单点跑通 (MVP)

### 2.1 设备解析与连接验证 (需求 1.1)

- [x] 2.1.1 编写独立验证脚本 `backend/tests/test_netmiko.py`: 读取 `/data/` CSV，连接第一台设备，执行 `show arp`，打印回显
- [x] 2.1.2 实现翻页处理: 登录后发送 `screen-length 0 disable`，验证华为设备分页关闭
- [x] 2.1.3 确认 netmiko huawei device type 兼容性，必要时降级测试 cisco_ios

### 2.2 FastAPI 与 WebSocket 通道 (需求 1.2)

- [x] 2.2.1 实现 FastAPI 应用入口 `backend/main.py`: CORS 配置、路由注册、静态文件挂载
- [x] 2.2.2 实现 `POST /api/upload`: CSV 文件上传接口，解析设备数据
- [x] 2.2.3 实现 `GET /api/inventory`: 返回内存中的设备列表（不含密码字段）
- [x] 2.2.4 实现 `WebSocket /ws/task/{task_id}`: 每秒发送模拟日志（while 循环），验证长连接稳定

### 2.3 前端基础页面 (需求 1.3)

- [x] 2.3.1 实现分屏布局: 左侧设备面板 (30%) + 右侧终端面板 (70%) 的 Flex 布局
- [x] 2.3.2 实现 `DeviceTable.vue`: 读取 `GET /api/inventory`，渲染设备表格（ip, type, area, protocol），含 checkbox 勾选
- [x] 2.3.3 实现文件上传控件: 上传按钮 + `<input type="file">`，调用 `POST /api/upload`
- [x] 2.3.4 引入 Xterm.js，实现主终端组件 `TerminalPanel.vue`，连接 WebSocket，渲染后端模拟日志

### 2.4 端到端串联 (需求 1.4)

- [x] 2.4.1 实现 `POST /api/execute` 初版: 接收 `{device_ips, commands}`，串行执行（不做并发），逐台登录下发命令，结果通过 WebSocket 推送
- [x] 2.4.2 前端 `CommandInput.vue`: 文本框输入命令，点击执行触发 `POST /api/execute`
- [x] 2.4.3 验证全链路: 上传 CSV → 选设备 → 输入命令 → 执行 → 主终端看到事件流 → 确认回显正确

## 3. 里程碑二: 并发执行与丰富交互

### 3.1 并发执行引擎

- [x] 3.1.1 实现 `executor/engine.py`: asyncio.Semaphore 限流、ThreadPoolExecutor 跑 netmiko
- [x] 3.1.2 实现 `executor/device.py`: 单设备连接 + 多命令顺序执行 + 翻页处理 + 输出采集
- [x] 3.1.3 实现 Fail-fast: 单命令报错 → 终止该设备后续命令 → 发送 `device_error`
- [x] 3.1.4 实现 WebSocket 消息协议: `device_start` / `device_output` / `device_done` / `device_error` / `task_progress` / `task_complete`
- [x] 3.1.5 前端 `max_concurrent` 滑块，动态传入并发数

### 3.2 弹窗与 Tab 切换

- [x] 3.2.1 实现前端状态管理: 收集 `device_output` 按 `device_ip` + `command` 存储
- [x] 3.2.2 实现 `ResultCards.vue`: 执行完成后展示卡片（✅/❌、IP、耗时）
- [x] 3.2.3 实现 `OutputModal.vue`: 点击卡片 → Modal 打开，内含 Xterm.js 实例展示纯净回显
- [x] 3.2.4 实现多命令 Tab 切换: 弹窗顶部 Tab 按钮，点击切换 Xterm.js 显示的 command 输出
- [x] 3.2.5 实现「全部复制」: 拼接所有命令回显（带分隔符）写入剪贴板
- [x] 3.2.6 实现「导出 TXT」: 拼接回显并触发浏览器下载

### 3.3 命令片段库 (Snippet Library)

- [x] 3.3.1 实现 `GET /api/snippets`: 返回从 commands.csv 加载的命令片段
- [x] 3.3.2 后端启动时加载 `/data/commands.csv`，支持 category 分组
- [x] 3.3.3 前端 Snippet 下拉: 按 category 分组展现，点击填入 `CommandInput`
- [x] 3.3.4 前端文件上传控件: 支持上传 commands.csv 覆盖当前片段库

## 4. 里程碑三: 归档、部署与打磨

### 4.1 原子化归档

- [x] 4.1.1 实现归档逻辑: `task_complete` 时生成 `/archives/<timestamp>_Task/` 目录
- [x] 4.1.2 生成设备 Markdown 文件: `<ip>_<type>.md`，H1 设备信息、H2 命令、代码块回显、元数据
- [x] 4.1.3 生成 `task_summary.json`: task_id、时间戳、命令列表、各设备状态汇总
- [x] 4.1.4 实现 `GET /api/archives`: 返回历史归档列表

### 4.2 PyInstaller 打包

- [x] 4.2.1 编写 `build.spec`: 包含 `frontend/dist/` 作为 data 目录，处理 cryptography 等 C 扩展
- [ ] 4.2.2 验证打包: 在目标 Windows 环境测试 .exe 启动，浏览器访问正常
- [x] 4.2.3 实现启动时自动打开浏览器: `webbrowser.open("http://localhost:8000")`

### 4.3 体验打磨

- [x] 4.3.1 设备列表按 Area/Type 筛选: 下拉筛选器，组合生效
- [x] 4.3.2 设备搜索: 关键字输入框，按 IP 过滤
- [x] 4.3.3 全局进度条: 顶部进度条显示已完成/总数
- [x] 4.3.4 深色主题: 整体 UI dark mode，Xterm.js 终端配色协调
- [x] 4.3.5 密码脱敏: 前端设备表格不展示密码列，WebSocket 消息不包含密码
