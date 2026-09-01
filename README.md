# 🤖 TestAgent - 软件测试 AI 助手

> 一个可在线/离线切换的 AI 测试助手，专为软件测试场景设计。  
> 在线使用 [硅基流动](https://siliconflow.cn/) 云端模型，离线自动降级到本地 [Ollama](https://ollama.com/) 推理。

---

## ✨ 功能特性

- 🔀 **双模式切换** - 云端 API 与本地 Ollama 无缝切换
- 🛡️ **自动降级** - 在线服务不可用时自动 fallback 到本地模型
- 💬 **多轮对话** - 支持上下文记忆的交互式测试助手
- 🏗️ **策略模式架构** - 统一接口，方便扩展其他 LLM 后端
- 🧪 **测试场景专精** - 内置 Prompt 针对测试用例设计、Bug 分析等场景优化

---

## 📐 架构设计
text



               ┌─────────────────────────────────┐
               │         TestAgent (agent.py)    │
               │   管理对话历史 + 系统提示词       │
               └──────────────┬──────────────────┘
                              │ 调用
                              ▼
               ┌─────────────────────────────────┐
               │      create_llm_client()        │
               │     工厂函数 · 自动选择 + 降级    │
               └──────┬────────────────┬─────────┘
                      │                │
          USE_ONLINE=True        USE_ONLINE=False
                      │                │
                      ▼                ▼
      ┌────────────────────┐  ┌────────────────────┐
      │ SiliconFlowClient  │  │ LocalOllamaClient  │
      │ 硅基流动 · 云端 API │  │ 本地 Ollama 推理    │
      │  (OpenAI 兼容协议) │  │  (OpenAI 兼容协议) │
      └────────────────────┘  └────────────────────┘
text




**核心设计原则**：两个后端都遵循 OpenAI Chat Completions 协议，因此上层业务代码完全不需要关心底层是云端还是本地。

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- （可选）[Ollama](https://ollama.com/download/windows) - 离线模式需要
- （可选）硅基流动 API Key - 在线模式需要

### 1. 克隆 & 安装依赖

```powershell
git clone https://github.com/your-username/test_Agent.git cd test_Agent

创建虚拟环境
python -m venv venv .\venv\Scripts\Activate.ps1

安装依赖
pip install -r requirements.txt

text




### 2. 配置

复制 `.env` 并填入你的 API Key：

```powershell
Windows PowerShell
Copy-Item .env.example .env

text




编辑 `.env`：

```env
SILICONFLOW_API_KEY=sk-your-actual-api-key-here

text




### 3. 拉取本地模型（离线模式）

```powershell
ollama serve # 启动服务 ollama pull qwen:7b-chat # 另开终端拉模型

text




### 4. 运行

```powershell
python main.py

text




首次启动会自动检测并连接可用的模型后端。

---

## 📁 项目结构
test_Agent/ ├── config.py # ⚙️ 集中配置（模式开关、模型名、API 地址） ├── llm_client.py # 🔌 LLM 客户端抽象 + 两种实现 + 工厂函数 ├── agent.py # 🧠 Agent 核心（对话管理、Prompt 角色设定） ├── main.py # 🖥️ CLI 交互式入口 ├── requirements.txt # 📦 依赖声明 ├── .env # 🔑 敏感配置（已 gitignore） └── .gitignore

text




---

## 🎯 使用示例
================================================== 🤖 TestAgent - 软件测试助手
[*] 尝试在线模式 (SiliconFlow)... [✓] 在线模式已就绪

✅ Agent 已就绪！输入你的测试问题，或输入命令： /reset - 重置对话 /history - 查看历史 /quit - 退出
[你] 帮我设计一个登录功能的测试用例

[Agent] 好的，针对登录功能，我会从以下几个维度设计测试用例：

【功能测试】

正确的用户名 + 正确的密码 → 登录成功
正确的用户名 + 错误的密码 → 提示密码错误 ...
[你] 这些用例里哪些是边界测试？

[Agent] 在上面的用例中，属于边界测试的有：

用户名为空 / 密码为空
用户名超长 / 密码超长 ...
text




---

## 🏗️ 技术栈

| 类别 | 技术 | 选择理由 |
|------|------|---------|
| 语言 | Python 3.12 | 生态成熟，LLM SDK 支持好 |
| HTTP 客户端 | requests | 轻量，直接对接 OpenAI 兼容接口 |
| 配置管理 | python-dotenv | 分离代码与敏感信息 |
| 在线模型 | 硅基流动 (SiliconFlow) | 国内访问快，免费额度够用 |
| 离线推理 | Ollama + Qwen | 一键部署本地推理，GPU/CPU 都能跑 |

---

## 📝 路线图

- [ ] 🌊 流式输出（打字机效果）
- [ ] 🖥️ Web UI（Gradio / Streamlit）
- [ ] 🔧 工具调用（查询接口文档、执行命令）
- [ ] 🧪 添加 pytest 单元测试
- [ ] 📊 对话历史持久化存储

---

## 📄 License

MIT License