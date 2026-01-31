# MarkDown图片本地化工具（单文件免安装版本）

一款用于将 Markdown 文件中的在线图床图片下载到本地的工具，自动更新文档中的图片链接转换为本地链接，有效防止因图床服务失效、链接过期等原因导致的图片丢失问题。

## 为什么需要这个工具？

在编写 Markdown 文档时，我们经常使用在线图床来托管图片。然而，这种方式存在以下风险：

- 图床服务可能关闭或收费
- 图片链接可能过期失效
- 网络环境变化导致无法访问
- 文档迁移时图片丢失

本工具可以一键将所有在线图片下载到本地，并自动更新 Markdown 文件中的链接，让你的文档永久保存完整。

## 功能特性

### 核心功能

- **递归扫描**：自动扫描指定文件夹及所有子文件夹中的 `.md` 文件
- **多格式支持**：同时支持 Markdown 图片语法 `![alt](url)` 和 HTML `<img src="url">` 标签
- **智能过滤**：仅处理 `http://` 和 `https://` 开头的在线图片，忽略本地图片引用
- **自动下载**：将在线图片下载到 Markdown 文件同级的 `assets` 文件夹
- **链接更新**：自动将原始 URL 替换为本地相对路径

### 文件命名策略

- **优先原名**：优先使用 URL 中的原始文件名，保持可读性
- **冲突处理**：当文件名冲突时，自动添加短哈希后缀（如 `image_a1b2c3.png`）
- **格式检测**：无法从 URL 获取扩展名时，根据图片内容自动检测格式

### 其他特性

- **缓存机制**：相同 URL 自动复用已下载的图片，避免重复下载
- **多编码支持**：自动尝试 UTF-8、GBK、GB2312 等多种编码读取文件
- **错误容忍**：单个图片下载失败不影响其他图片处理
- **进度显示**：实时显示处理进度和详细日志
- **单文件打包**：打包为独立 exe 文件，无需安装 Python 环境

## 使用方法

### 方式一：直接使用（推荐）

1. 下载 `dist/MD图片本地化工具.exe`
2. 双击运行程序
3. 点击「浏览」按钮选择包含 Markdown 文件的文件夹
4. 点击「开始处理」按钮
5. 等待处理完成，查看统计结果

### 方式二：从源码运行

```bash
# 克隆项目
git clone <repository-url>
cd md-image-localizer

# 安装依赖
pip install -r requirements.txt

# 运行程序
python src/main.py
```

## 处理示例

### 处理前

```markdown
# 我的文档

这是一张在线图片：
![示例图片](https://example.com/images/photo.png)

这是 HTML 格式的图片：
<img src="https://cdn.example.com/banner.jpg" alt="横幅">
```

### 处理后

```markdown
# 我的文档

这是一张在线图片：
![示例图片](assets/photo.png)

这是 HTML 格式的图片：
<img src="assets/banner.jpg" alt="横幅">
```

同时，图片文件会被下载到 `assets/` 文件夹中。

## 项目结构

```
md-image-localizer/
├── src/                      # 源代码目录
│   ├── __init__.py
│   ├── main.py               # 程序入口
│   ├── gui.py                # GUI 图形界面
│   ├── scanner.py            # Markdown 文件扫描器
│   ├── extractor.py          # 图片链接提取器
│   ├── downloader.py         # 图片下载器
│   ├── replacer.py           # 链接替换器
│   └── localizer.py          # 主处理器（协调各组件）
├── tests/                    # 测试目录
│   ├── test_scanner.py       # 扫描器测试
│   ├── test_extractor.py     # 提取器测试
│   ├── test_downloader.py    # 下载器测试
│   └── test_replacer.py      # 替换器测试
├── dist/                     # 打包输出目录
│   └── MD图片本地化工具.exe   # 可执行文件
├── .kiro/specs/              # 规格文档
├── requirements.txt          # Python 依赖
├── build.spec                # PyInstaller 打包配置
└── README.md                 # 项目说明
```

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    GUI Layer (tkinter)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ FolderSelect│  │ ProgressBar  │  │  ResultDisplay │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Core Logic Layer                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ MDScanner   │  │ImageExtractor│  │ LinkReplacer   │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────────┐│
│  │              ImageDownloader                         ││
│  │  - URL 解析  - 文件名生成  - 下载管理  - 缓存检查   ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## 开发指南

### 环境要求

- Python 3.10 或更高版本
- Windows 操作系统（GUI 基于 tkinter）

### 安装依赖

```bash
pip install -r requirements.txt
```

依赖列表：

- `requests>=2.28.0` - HTTP 请求库
- `Pillow>=9.0.0` - 图片处理库
- `hypothesis>=6.0.0` - 属性测试框架
- `pytest>=7.0.0` - 测试框架

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_scanner.py -v

# 运行并显示覆盖率
python -m pytest tests/ -v --cov=src
```

### 打包为 exe

```bash
# 使用 PyInstaller 打包
python -m PyInstaller build.spec --clean
```

打包完成后，可执行文件位于 `dist/MD图片本地化工具.exe`

## 支持的图片格式

| 格式 | 扩展名     | 自动检测 |
| ---- | ---------- | -------- |
| PNG  | .png       | ✅       |
| JPEG | .jpg/.jpeg | ✅       |
| GIF  | .gif       | ✅       |
| WebP | .webp      | ✅       |
| SVG  | .svg       | ✅       |
| BMP  | .bmp       | ✅       |
| ICO  | .ico       | ✅       |

## 常见问题

### Q: 处理后原文件会被覆盖吗？

A: 是的，程序会直接修改原 Markdown 文件。建议在处理前备份重要文件。

### Q: 下载失败的图片会怎样？

A: 下载失败的图片会被跳过，原链接保持不变，程序会在日志中记录错误信息。

### Q: 支持处理子文件夹吗？

A: 支持，程序会递归扫描所选文件夹及其所有子文件夹中的 Markdown 文件。

### Q: 图片会下载到哪里？

A: 图片会下载到每个 Markdown 文件同级目录下的 `assets` 文件夹中。

## 技术栈

- **Python 3.10+** - 编程语言
- **tkinter** - GUI 框架（Python 内置）
- **requests** - HTTP 请求
- **Pillow** - 图片处理
- **hypothesis** - 属性测试
- **pytest** - 单元测试
- **PyInstaller** - 打包工具
