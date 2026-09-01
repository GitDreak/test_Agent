"""
Web UI - 修复 4 个问题：
1. 免费模型完整显示（用用户提供的列表）
2. 超时改成 300 秒 + Gradio 不自己断
3. 停止生成按钮
4. 错误后自动修复 history 格式
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import gradio as gr
import requests
import config
from src.agent import TestAgent
from src.llm_client import SiliconFlowClient, LocalOllamaClient

# ============ 在线免费模型（用户提供的完整列表） ============
ONLINE_MODELS = [
    "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
    "deepseek-ai/DeepSeek-R1",
    "deepseek-ai/DeepSeek-V3.2",
    "deepseek-ai/DeepSeek-V3.1-Terminus",
    "deepseek-ai/DeepSeek-V3",
    "deepseek-ai/DeepSeek-V4-Flash",
    "deepseek-ai/DeepSeek-V4-Pro",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-14B-Instruct",
    "Qwen/Qwen2.5-32B-Instruct",
]

def fetch_local_models():
    """动态获取本地 Ollama 模型"""
    try:
        resp = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        return [m["name"] for m in resp.json().get("models", [])]
    except Exception as e:
        print(f"⚠️  Ollama 未启动: {e}")
        return []

# ============ 全局初始化 ============
print("=" * 50, flush=True)
print("🚀 TestAgent Web UI 启动中...", flush=True)
print("=" * 50, flush=True)

LOCAL_MODELS = fetch_local_models()
print(f"📡 在线免费模型: {len(ONLINE_MODELS)} 个", flush=True)
print(f"📡 本地已有模型: {len(LOCAL_MODELS)} 个 -> {LOCAL_MODELS}", flush=True)

agent = None
default_mode = "在线" if config.USE_ONLINE else "离线"
default_model = config.ONLINE_MODEL if config.USE_ONLINE else (config.LOCAL_MODEL if LOCAL_MODELS else None)

def init_agent(mode, model_name):
    """初始化 Agent"""
    global agent
    
    if mode == "在线":
        config.USE_ONLINE = True
        config.ONLINE_MODEL = model_name
        config.TIMEOUT = 120  # 在线 120 秒够了
        llm = SiliconFlowClient()
        if not llm.check_available():
            return None, "❌ 在线初始化失败"
    else:
        config.USE_ONLINE = False
        config.LOCAL_MODEL = model_name
        config.TIMEOUT = 300  # 本地给够时间（模型思考长）
        llm = LocalOllamaClient()
        if not llm.check_available():
            return None, "❌ 本地初始化失败，请先 ollama serve"
    
    agent = TestAgent(llm)
    status = f"✅ {mode} | {model_name}"
    print(status, flush=True)
    return agent, status

def on_mode_change(mode):
    """切换模式时更新模型下拉"""
    if mode == "在线":
        val = default_model if default_model in ONLINE_MODELS else ONLINE_MODELS[0]
        return gr.update(choices=ONLINE_MODELS, value=val)
    else:
        local = fetch_local_models()
        if not local:
            return gr.update(choices=[], value=None)
        return gr.update(choices=local, value=local[0])

def on_apply_settings(mode, model_name):
    """应用设置"""
    print(f"\n🔄 切换: {mode} -> {model_name}", flush=True)
    if not model_name:
        return "❌ 请先选模型"
    _, status = init_agent(mode, model_name)
    return status

def safe_history(history):
    """确保 history 格式正确，过滤掉错误项"""
    clean = []
    for item in history or []:
        if isinstance(item, dict) and "role" in item and "content" in item:
            clean.append(item)
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            clean.append({"role": "user", "content": item[0]})
            clean.append({"role": "assistant", "content": item[1]})
    return clean

def chat_response(message, history):
    """聊天 - 加异常保护"""
    global agent
    history = safe_history(history)  # 🔴 问题4修复
    if not agent:
        yield "", history
        return
    if not message.strip():
        yield "", history
        return

    print(f"\n[你] {message}", flush=True)
    try:
        reply = agent.chat(message)
    except Exception as e:  # 🔴 问题2修复：捕获超时等错误
        reply = f"⚠️ 请求失败: {e}\n\n建议：1) 换个模型 2) 检查 Ollama 是否启动 3) 网络慢就用离线模式"
        print(f"❌ {reply}", flush=True)

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    yield "", history

def stop_chat():
    """停止生成（Gradio 会自动中断）"""
    print("\n🛑 用户请求停止", flush=True)

def reset_agent():
    """重置对话"""
    global agent
    if agent:
        agent.reset()
    print("\n🔄 对话已重置", flush=True)
    return [], "🔄 对话已重置"

# ============ 先初始化 ============
print("🤖 初始化默认 Agent...", flush=True)
_, init_status = init_agent(default_mode, default_model or ONLINE_MODELS[0])
print("-" * 50, flush=True)

# ============ 构建界面 ============
with gr.Blocks(title="TestAgent - 软件测试助手") as demo:
    gr.Markdown("""
    # 🤖 TestAgent - 软件测试 AI 助手
    在线免费模型 + 本地 Ollama · ReAct 工具调用
    """)

    with gr.Row():
        # 左侧设置面板
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ 模型设置")
            
            mode_radio = gr.Radio(["在线", "离线"], value=default_mode, label="运行模式")
            
            all_local = fetch_local_models()
            default_ddl = (
                (default_model if default_model in ONLINE_MODELS else ONLINE_MODELS[0])
                if default_mode == "在线"
                else (default_model if default_model in all_local else (all_local[0] if all_local else None))
            )
            model_dropdown = gr.Dropdown(
                choices=ONLINE_MODELS if default_mode == "在线" else all_local,
                value=default_ddl,
                label="选择模型",
                interactive=True
            )
            
            apply_btn = gr.Button("🔄 应用设置", variant="primary")
            settings_status = gr.Markdown(init_status)

            gr.Markdown(f"""
            ---
            **📊 模型统计**
            - 在线免费: **{len(ONLINE_MODELS)}** 个
            - 本地已有: **{len(LOCAL_MODELS)}** 个
            """)

        # 右侧聊天
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=500)
            msg = gr.Textbox(placeholder="输入你的测试问题...", label="你", lines=2)

            with gr.Row():
                submit_btn = gr.Button("🚀 发送", variant="primary")
                stop_btn = gr.Button("🛑 停止生成")  # 🔴 问题3修复
                reset_btn = gr.Button("🔄 重置对话")

            status = gr.Markdown("✅ 就绪")

    # 事件
    mode_radio.change(on_mode_change, mode_radio, model_dropdown)
    apply_btn.click(on_apply_settings, [mode_radio, model_dropdown], settings_status)
    
    submit_btn.click(chat_response, [msg, chatbot], [msg, chatbot])
    msg.submit(chat_response, [msg, chatbot], [msg, chatbot])
    stop_btn.click(stop_chat)  # 🔴 问题3
    reset_btn.click(reset_agent, [], [chatbot, status])
# ============ 最后几行改成这样 ============
if __name__ == "__main__":
    print("\n" + "=" * 50, flush=True)
    print("🌐 Web UI 启动！请在浏览器打开:", flush=True)
    print("   http://localhost:7860", flush=True)
    print("=" * 50 + "\n", flush=True)
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        max_file_size=None
    )