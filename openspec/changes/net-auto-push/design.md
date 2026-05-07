## Context

网络运维工程师需要同时对多台华为系交换机批量执行巡检/配置命令。现有方案是逐台手动 SSH 登录，无执行记录留存。目标用户为单人单机场景（Windows 专用机），不考虑多用户、权限、审计等企业级需求。

约束：深信服/华为设备 SSH CLI 登录后默认分页，需自动关闭。设备密码以 CSV 明文存储（测试环境，不可外泄到前端）。

## Goals / Non-Goals

**Goals:**
- 单 `.exe` 部署，双击启动，浏览器即用
- 多设备并发 SSH 执行命令，并发数可调
- WebSocket 实时推送事件流和回显
- Xterm.js 终端组件：主终端看事件流，弹窗看纯净回显
- 命令支持 CSV 预设库 + 手动输入，输入框支持多行
- 每次任务结果自动归档为 Markdown 文件

**Non-Goals:**
- 不支持 Telnet（仅 SSH）
- 不考虑多用户、RBAC、审计日志
- 不做数据库存储（无 SQLite / ORM）
- 不支持设备配置自动备份、Diff 比对等高级功能
- 不做移动端适配

## Decisions

### 1. netmiko + huawei device type

选择 netmiko 而非 scrapli，原因是 netmiko 对华为设备有成熟的 `huawei` driver，`send_command` 内置 `strip_prompt` 和分页处理能力。scrapli 原生 async 的优势在 `ThreadPoolExecutor` 包装后差异不大——并发瓶颈在网络 I/O 而非 Python 事件循环。

netmiko 同步但用 `loop.run_in_executor` 扔进线程池，配合 `asyncio.Semaphore` 限流，并发度由前端选择（默认 5）。

备选 `cisco_ios` device type 用于非华为设备。

### 2. 翻页处理：screen-length 0 disable

登录后立即执行 `screen-length 0 disable`（华为系 / 深信服通用），关闭 More 分页。若设备不支持该命令，依赖 netmiko 的 `send_command` 自动等待提示符的行为兜底。

在 netmiko session 通道建立后、send_command 之前，先发一次 `send_command("screen-length 0 disable", expect_string=r"[>#\]]")` 尝试关闭分页，失败不阻塞后续命令。

### 3. WebSocket 消息协议

六种消息类型，JSON 编码，前端根据 `type` 字段分发到不同 UI 组件：

```jsonc
{"type":"device_start",   "device_ip":"10.1.1.22","device_type":"Huawei","area":"IDC-A"}
{"type":"device_output",  "device_ip":"10.1.1.22","command":"show arp","data":"...","stream":"stdout"}
{"type":"device_done",    "device_ip":"10.1.1.22","status":"success","duration_ms":1200}
{"type":"device_error",   "device_ip":"10.1.1.22","error":"Auth failed","command":"show arp"}
{"type":"task_progress",  "total":10,"completed":3,"running":2,"failed":1}
{"type":"task_complete",  "total":10,"success":9,"failed":1}
```

`device_output` 携带 `command` 字段，前端弹窗据此将回显推入对应 Tab。

### 4. 前端分屏布局

```
┌──────────────────────────────────────────────────────┐
│ Header: 并发选择器 + 执行按钮                        │
├───────────────┬──────────────────────────────────────┤
│ 左侧 30%       │ 右侧 70%                             │
│ DeviceTable   │ Xterm.js 主终端 (事件流)              │
│ (筛选+勾选)    │                                      │
│               │                                      │
│ CommandInput  ├──────────────────────────────────────┤
│ (Snippet +    │ ResultCards                           │
│  手动输入)     │ (点击 → Modal Xterm.js 纯净回显)     │
└───────────────┴──────────────────────────────────────┘
```

### 5. 结果归档：原子化 Markdown 文件

每次 POST /api/execute 创建一个 task_id。任务完成后生成：

```
archives/
└── 2026-05-07_143000_Task/
    ├── 10.1.1.22_Huawei.md
    ├── 10.1.1.24_Huawei.md
    └── task_summary.json
```

每个设备 `.md` 文件以命令为二级标题组织回显，方便 Markdown 阅读器和 VS Code 全局搜索。`task_summary.json` 记录元数据（时间、设备列表、命令列表、各设备状态）。

### 6. 错误处理：Fail-fast per device

某条命令捕获到异常（Auth failed / Timeout / Command error）时：
- 立即向 WebSocket 发送 `device_error`
- 该设备不再执行剩余命令
- 其他正在执行的设备不受影响
- 该设备结果卡片标红，弹窗显示已执行的命令回显 + 错误信息

### 7. 部署：PyInstaller 打包

前端 `npm run build` 输出到 `frontend/dist/`，FastAPI 中：
```python
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
```

PyInstaller `.spec` 将 `frontend/dist/` 作为 data 目录打包。最终产出 `net_auto_push.exe`，启动时：
1. uvicorn 启动在 localhost:8000
2. 自动调用 `webbrowser.open("http://localhost:8000")`
3. `/data/` 和 `/archives/` 目录相对于 .exe 所在路径

## Risks / Trade-offs

- **[风险] netmiko 对深信服设备的兼容性**: 深信服 CLI 可能不完全兼容华为 driver → 先用华为 driver 测试，不通过则降级为 `cisco_ios` 或 `generic`，需求 1.1 脚本优先验证
- **[风险] PyInstaller 打包 cryptography C 扩展**: netmiko 依赖的 paramiko/cryptography 含 C 扩展 → 在需求 3.2 阶段提前测试打包，必要时使用 `--collect-all` 钩子
- **[风险] 大回显导致前端内存压力**: `dis cu` 可能上万行 → 弹窗 Xterm.js 使用虚拟滚动（内置能力），主终端只显示事件流（每设备几行），不会积压
- **[权衡] 无数据库 vs 数据分析**: 纯文件归档利于搜索，但无法做结构化查询 → 当前用户场景是"出问题了回去看某天某设备的回显"，Markdown + VS Code 全局搜索更合适
- **[权衡] 明文密码 CSV**: 测试环境可接受，生产环境需确保 .exe 部署在受控的专用机上
