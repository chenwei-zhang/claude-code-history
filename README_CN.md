<div align="right">
  <strong>中文</strong> | <a href="README.md">English</a>
</div>

# Claude Code History Viewer

一个简单的 Web 应用，用于查看 Claude Code 的对话历史记录。

## 功能特性

- 📁 浏览所有 Claude Code 项目
- 💬 查看项目中的对话历史
- 🎨 现代化的 Web 界面
- 🔍 支持查看完整的消息内容，包括思考过程和工具调用
- 🚀 自动端口检测，如果默认端口被占用会自动使用其他可用端口

## 系统要求

- Python 3.6 或更高版本
- 已安装 Claude Code 并生成过对话历史

## 安装步骤

### 使用 pip 安装（推荐）

最简单的方式是使用 pip 安装：

```bash
pip install claude-code-history
```

或从源码安装：

```bash
pip install git+https://github.com/chenwei-zhang/claude-code-history.git
```

### 从源码安装

1. 克隆或下载此项目：
   ```bash
   git clone https://github.com/chenwei-zhang/claude-code-history.git
   cd claude-code-history
   ```

2. 安装包：
   ```bash
   pip install .
   ```

3. 确保已安装 Python 3.6+：
   ```bash
   python3 --version
   ```

项目使用 Python 标准库，无需安装额外依赖。

## 使用方法

安装后，可以使用 `claude-code-history` 命令运行应用：

1. 运行应用：
   
   使用默认端口 8000：
   ```bash
   claude-code-history
   ```
   
   或指定自定义端口：
   ```bash
   claude-code-history --port 8080
   ```
   
   也可以使用简写形式：
   ```bash
   claude-code-history -p 8080
   ```

   如果从源码安装但未使用 pip，仍可以运行：
   ```bash
   python3 app.py
   ```

2. 打开浏览器访问：
   ```
   http://localhost:8000
   ```
   （如果指定了其他端口，请使用相应的端口号）
   
   如果指定的端口被占用，程序会自动使用其他可用端口（+1, +2...），并在终端显示实际使用的端口。

3. 在浏览器中浏览你的 Claude Code 项目历史

4. 停止服务器：
   - 在终端按 `Ctrl+C`

## 项目结构

```
claude-code-history/
├── claude_code_history/  # 包目录
│   ├── __init__.py      # 包初始化文件
│   └── app.py           # 主程序
├── app.py               # 旧版入口点（向后兼容）
├── pyproject.toml       # 包配置文件
├── README.md            # 使用说明（英文）
├── README_CN.md         # 使用说明（中文）
└── requirements.txt     # 依赖文件
```

## 工作原理

应用会读取 Claude Code 存储对话历史的位置：
- macOS/Linux: `~/.claude/projects/`
- Windows: `%USERPROFILE%\.claude\projects\`

每个项目文件夹包含多个 `.jsonl` 文件，每个文件代表一次对话会话。应用会解析这些文件并在 Web 界面中展示。

## 功能说明

### 项目列表
- 显示所有 Claude Code 项目
- 点击项目卡片查看该项目的对话列表

### 对话列表
- 显示项目中的所有对话
- 按时间倒序排列（最新的在前）
- 显示对话摘要或第一条消息的预览

### 对话详情
- 完整显示所有用户和助手的消息
- 支持查看思考过程（thinking）
- 支持查看工具调用（tool_use）和工具结果（tool_result）
- 显示时间戳和模型信息

## 常见问题

### Q: 端口被占用怎么办？
A: 程序会自动检测并使用其他可用端口。如果默认端口 8000 被占用，会自动尝试 8001, 8002 等端口，并在终端显示实际使用的端口。

### Q: 找不到项目怎么办？
A: 确保你已经使用过 Claude Code 并生成过对话历史。项目数据存储在 `~/.claude/projects/` 目录下。

### Q: 可以修改端口吗？
A: 可以！使用 `--port` 或 `-p` 参数指定端口，例如：`python3 app.py --port 8080`。如果不指定，默认使用 8000 端口。

### Q: 支持哪些操作系统？
A: 支持所有运行 Python 3.6+ 的操作系统，包括 macOS、Linux 和 Windows。

## 技术说明

- 使用 Python 标准库 `http.server` 创建 Web 服务器
- 使用 JSONL 格式解析对话历史
- 纯前端渲染，无需数据库
- 响应式设计，支持移动设备

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 作者

Created for viewing Claude Code conversation history.

