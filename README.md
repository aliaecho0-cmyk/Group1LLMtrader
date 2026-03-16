# backtrader_copilot - AI Quantitative Backtesting Assistant (Chinese Optimized) / AI量化回测助手（中文优化版）

<div align="center">
  
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![QWEN 3.5](https://img.shields.io/badge/Model-Qwen2.5--Plus-orange)](https://tongyi.aliyun.com/)

</div>

---

## ⚠️ 重要声明 / Important Notice

**English**  
This project is a **secondary development** based on **[Lukas Wesemann](https://github.com/LukasWesemann)'s [backtrader_copilot](https://github.com/LukasWesemann/backtrader_copilot)**.  
The core framework (`bt_copilot.py`, `coding_agent.py`, etc.) is entirely authored by Lukas Wesemann.  
My work is built upon his excellent foundation.

**中文**  
本项目是**二次开发版本**，基于 **[Lukas Wesemann](https://github.com/LukasWesemann) 的 [backtrader_copilot](https://github.com/LukasWesemann/backtrader_copilot)**。  
核心框架（`bt_copilot.py`、`coding_agent.py` 等）完全由 Lukas Wesemann 原创。  
我的工作是在他优秀的基础上进行的扩展和优化。

---

## 👏 致谢原作者 / Credits to the Original Author

### **Lukas Wesemann**  
[GitHub](https://github.com/LukasWesemann) | [Original Repository](https://github.com/LukasWesemann/backtrader_copilot)

> *"If I have seen further, it is by standing on the shoulders of giants."*  
> *"如果我看得比别人远，那是因为我站在巨人的肩膀上。"*

Lukas 的原始项目提供了一个优雅的 AI+量化回测框架，他的核心贡献包括：
- **bt_copilot.py** - 核心回测协调逻辑
- **coding_agent.py** - AI代码生成代理
- **resources/** - 模板和示例文件

**本项目的核心价值都源自他的原创。** 

---

## 📌 Project Introduction / 项目简介

**English**  
This project is a **Chinese-optimized secondary development version** of Lukas Wesemann's **backtrader_copilot** quantitative backtesting framework. It enables users to perform complex quantitative strategy backtesting through **natural language**, with a focus on Chinese user experience.

**中文**  
本项目是 Lukas Wesemann 的 **backtrader_copilot** 量化回测框架的**中文优化二次开发版本**，旨在让用户通过**自然语言**即可完成复杂的量化策略回测，特别优化了中文用户体验。

---

### Core Concept / 核心思想

**English**
User inputs natural language → AI Model → Generates backtrader code → Runs backtest → Outputs results
(Core framework by Lukas Wesemann, AI model adapted for Chinese)

**中文**
用户输入自然语言 → AI模型 → 生成backtrader代码 → 运行回测 → 输出结果
（核心框架由 Lukas Wesemann 开发，AI模型适配中文）

---

## ✨ 原作者贡献 vs 本项目新增 / Original Author's Work vs New Contributions

### 🔵 **原作者 Lukas Wesemann 的核心贡献**
| 文件 | 说明 |
|------|------|
| `bt_copilot.py` | 核心回测协调逻辑 |
| `coding_agent.py` | AI代码生成代理 |
| `main_example.py` | 使用示例 |
| `settings.yaml` | 配置文件模板 |
| `resources/boilerplate_basic.py` | 基础模板 |
| `resources/example_backtest.py` | 回测示例 |
| `resources/prompt_library_default.csv` | 提示库 |
| `README.md` (原始版本) | 项目文档 |

> **这些文件构成了项目的核心价值，我保留了它们的完整版权和原始代码。**

---

### 🟢 **本项目新增内容**
| 文件 | 说明 |
|------|------|
| `app.py` / `appgroup2.py` | Web图形界面（新增） |
| `test_api.py` | API测试工具（新增） |
| `check_my_versions.py` | 环境检查脚本（新增） |
| `requirements.txt` | 依赖管理（新增） |
| `版本信息.txt` | 中文说明文档（新增） |
| `data/stocks.csv` | 内置股票数据（新增） |
| **模型替换** | OpenAI → Qwen3.5-Plus |
| **README.md (当前版本)** | 中英双语文档（新增） |

> **我的工作是在原作者的基础上进行的扩展，所有新增内容都明确标注。**

---

## 🏗️ 项目架构 / Project Architecture

### 文件结构（标注原作者/新增） / File Structure (Author/New)
```
├── app.py                 # Web主界面 🟢 新增
├── appgroup2.py           # Web辅助界面 🟢 新增
├── test_api.py            # API测试工具 🟢 新增
├── check_my_versions.py   # 环境检查脚本 🟢 新增
├── requirements.txt       # 依赖管理 🟢 新增
├── 版本信息.txt            # 中文说明文档 🟢 新增
├── data/
│   └── stocks.csv         # 内置股票数据 🟢 新增
│
├── bt_copilot.py          # 核心框架 🔵 原作者
├── coding_agent.py        # 编码代理 🔵 原作者
├── main_example.py        # 使用示例 🔵 原作者
├── settings.yaml          # 配置文件 🔵 原作者
│
└── resources/             # 资源文件 🔵 原作者
    ├── boilerplate_basic.py
    ├── example_backtest.py
    └── prompt_library_default.csv
```

---

## 📄 许可证 / License

### 🔵 **核心框架部分（原作者）**
```
MIT License
Copyright (c) 2026 Lukas Wesemann
Original source: https://github.com/LukasWesemann/backtrader_copilot
```
This project includes code from Lukas Wesemann's backtrader_copilot.
The core framework (bt_copilot.py, coding_agent.py, resources/, etc.)
is the original work of Lukas Wesemann and is used under MIT License.

### 🟢 **新增部分（本项目）**
```
MIT License
Copyright (c) 2026 Yixue Wang
```
The web interface, Qwen model integration, built-in data, and documentation
are new contributions built upon Lukas Wesemann's framework.

**完整的 MIT 许可证文本请参见 [LICENSE](LICENSE) 文件。**  
For the full MIT License text, please see the [LICENSE](LICENSE) file.