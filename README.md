# 📚 UAA小说下载器

![Python](https://img.shields.io/badge/Python-3.7+-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square)

一个功能强大的[UAA](https://uaadizhi.com/)小说网站下载器，支持自动登录、批量下载、断点续传、章节管理等功能。

## ✨ 主要功能

### 🔐 智能登录系统
- 🤖 **AI验证码识别** - 使用AI API自动识别数学验证码
- 👥 **多账号管理** - 支持配置多个账号，灵活切换
- 🍪 **Cookie自动管理** - 自动保存和验证Cookie有效性

### 📖 下载功能
- 📚 **完整小说下载** - 支持下载整本小说
- 🎯 **精准范围下载** - 指定起始和结束章节
- ⚡ **断点续传** - 支持从上次下载位置继续
- 📊 **实时进度显示** - 显示下载进度和剩余章节

### 🛠️ 实用工具
- ✏️ **章节编号修改** - 批量修改章节编号
- 📜 **浏览器提取脚本** - 生成JavaScript脚本在浏览器中提取章节
- 📈 **进度管理** - 查看、清除、恢复下载进度

## 🚀 快速开始

### 📋 环境要求

- 🐍 Python 3.7 或更高版本
- 🌐 Chrome 浏览器
- 🔑 支持视觉识别的AI API（如OpenAI GPT-4V、Claude等）

### 📦 安装依赖

```bash
# 克隆项目
git clone https://github.com/aizhiqian/uaa_novel_downloader.git
cd uaa_novel_downloader

# 安装依赖
pip install -r requirements.txt
```

### ⚙️ 配置设置

1. **初始化项目**
   ```bash
   python main.py setup
   ```

2. **配置AI API** - 创建 `.env` 文件：
   ```env
   AI_API_BASE_URL=Full_API_request_address
   AI_API_KEY=your_api_key_here
   AI_MODEL=your_model_name_here
   ```

3. **添加账号信息** - 编辑 `config/users.txt`：
   ```
   1. example@email.com password123
   2. another@email.com password456
   ```

### 🎯 使用说明

#### 🔑 登录获取Cookie
```bash
# 使用默认账号登录
python main.py login

# 使用指定账号登录
python main.py login --user 1
```

#### 📚 下载小说
```bash
# 交互式下载（推荐新手）
python main.py download

# 下载整本小说
python main.py download 12345

# 下载指定范围
python main.py download 12345 --start 1 --end 50

# 下载指定数量
python main.py download 12345 --start 10 --count 20
```

#### 📊 管理进度
```bash
# 交互式进度管理
python main.py progress

# 查看所有进度
python main.py progress --view

# 继续下载
python main.py progress --resume --novel-id 12345

# 清除进度
python main.py progress --clear --novel-id 12345
```

#### ✏️ 修改章节编号
```bash
# 交互式修改
python main.py modify

# 按章节编号修改
python main.py modify --file "output/小说.txt" --start 1 --end 50 --increment 10

# 按章节名称修改
python main.py modify --file "output/小说.txt" --start-name "序章" --end-name "终章" --increment -5
```

#### 📜 生成提取脚本
```bash
# 生成浏览器章节提取脚本
python main.py extract
```

## 📁 项目结构

```
uaa_novel_downloader/
├── 📄 main.py              # 主程序入口
├── 📄 requirements.txt     # 依赖包列表
├── 📄 .env                 # 环境变量配置
├── 📄 README.md           # 项目说明
├── 📁 src/                # 源代码目录
│   ├── 📄 auth.py         # 身份验证模块
│   ├── 📄 downloader.py   # 下载器核心
│   ├── 📄 progress.py     # 进度管理
│   ├── 📄 utils.py        # 工具函数
│   ├── 📄 config.py       # 配置管理
│   ├── 📄 logger.py       # 日志系统
│   └── 📄 captcha_solver.py # 验证码识别
├── 📁 config/             # 配置文件目录
│   └── 📄 users.txt       # 用户账号配置
├── 📁 data/               # 数据文件目录
│   ├── 📄 cookies.json    # Cookie数据
│   ├── 📄 progress.json   # 下载进度
│   └── 📄 extract_script.js # 提取脚本
├── 📁 logs/               # 日志文件目录
└── 📁 output/             # 下载的小说文件
```

## 🔧 高级配置

### 🤖 AI API配置说明

支持多种AI服务提供商：

#### OpenAI GPT-4V
```env
AI_API_BASE_URL=https://api.openai.com/v1/chat/completions
AI_API_KEY=sk-your-api-key
AI_MODEL=gpt-4-vision-preview
```

#### Anthropic Claude
```env
AI_API_BASE_URL=https://api.anthropic.com/v1/messages
AI_API_KEY=your-claude-api-key
AI_MODEL=claude-3-opus-20240229
```

#### 自部署模型
```env
AI_API_BASE_URL=http://localhost:8000/v1/chat/completions
AI_API_KEY=your-local-api-key
AI_MODEL=your-model-name
```

### 🌐 网络配置

可在 `src/config.py` 中调整以下参数：

- `RETRY_COUNT`: 请求重试次数（默认3次）
- `RETRY_DELAY`: 重试间隔（默认5秒）
- `CHAPTER_DELAY`: 章节下载间隔（默认5秒）

## 📝 使用示例

### 💡 典型工作流程

1. **首次使用**
   ```bash
   # 1. 初始化项目
   python main.py setup

   # 2. 配置API和账号
   # 编辑 .env 和 config/users.txt

   # 3. 登录
   python main.py login

   # 4. 下载小说
   python main.py download
   ```

2. **日常使用**
   ```bash
   # 直接下载（Cookie有效时）
   python main.py download 12345

   # 继续上次的下载
   python main.py progress --resume --novel-id 12345
   ```

3. **章节管理**
   ```bash
   # 下载后发现章节编号有问题，进行调整
   python main.py modify
   ```

## ❓ 常见问题

### 🔐 登录相关

**Q: 验证码识别失败怎么办？**
- 检查AI API配置是否正确
- 确认API Key有效且有足够额度
- 尝试更换AI模型

**Q: Cookie过期怎么办？**
- 程序会自动提示，重新运行登录命令即可

### 📥 下载相关

**Q: 下载中断怎么办？**
- 使用进度管理功能继续下载
- 程序会自动保存进度，支持断点续传

**Q: 下载速度慢怎么办？**
- 调整 `CHAPTER_DELAY` 参数（注意不要设置太小）
- 检查网络连接

### 🛠️ 技术问题

**Q: Chrome浏览器启动失败**
- 确认Chrome已正确安装
- 检查ChromeDriver是否下载成功
- 尝试关闭其他Chrome进程

## 🔍 API 参数参考

<details>
<summary>点击展开查看API参数详情</summary>

```
https://www.uaa001.com/api/novel/app/novel/search?author=&category=&finished=&excludeTags=&space=&searchType=1&orderType=2&page=1&size=48
```

**排序 orderType**
- +: 降序 -: 升序
- ±1: 上架
- ±2: 更新
- ±3: 观看
- ±4: 收藏
- ±5: 评分
- ±6: 肉量

**来源 source**
- 1: 原创首发
- 2: 会员上传

**长度 space**
- 1: 短篇（小于10万字）
- 2: 中篇（10-100万字）
- 3: 长篇（大于100万字）

**评分 score**
- 1: >1
- 2: >2
- 3: >3
- 4: >4

**状态 finished**
- 0: 连载中
- 1: 已完结

**人称视角 person**
- 1: 男性视角
- 2: 女性视角
- 3: 第二人称
- 4: 第三人称

**肉量 porn**
- 1: 少肉
- 2: 中肉
- 3: 多肉
- 4: 超多肉

**取向 orientation**
- 1: 直男文
- 2: 女主文
- 3: 男男文
- 4: 女女文
</details>

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交Issue和Pull Request来帮助改进项目！

## ⚠️ 免责声明

本工具仅供学习和研究使用，请遵守相关网站的使用条款和版权规定。下载的内容请勿用于商业用途。

---

<div align="center">
  <p>⭐ 如果这个项目对你有帮助，请给它一个星标！</p>
  <p>📧 有问题？欢迎提交 Issue 或联系开发者</p>
</div>
