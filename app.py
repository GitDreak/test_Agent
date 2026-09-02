"""
Web UI - TestAgent
功能: API Key UI输入 / 硬编码免费模型 + API验证 / 自动清理端口 / 本地Ollama
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import gradio as gr
import requests
import subprocess
import config
from src.agent import TestAgent
from src.llm_client import SiliconFlowClient, LocalOllamaClient

# ============ 自动清理端口 ============
def kill_port(port):
    try:
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split("\n"):
            if f":{port}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                if pid.isdigit() and pid != "0":
                    print(f"🧹 清理旧进程 PID={pid}", flush=True)
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=3)
    except Exception:
        pass

kill_port(7860)

# ============ 硬编码免费模型（用户截图确认 ¥0/M Tokens） ============
# ============ 候选池（官网截图标了 ¥0 的） ============
CANDIDATE_MODELS = [
    "Qwen/Qwen3.5-4B",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen3-8B",
    "THUDM/GLM-4-9B-0414",
    "THUDM/GLM-Z1-9B-0414",
    "deepseek-ai/DeepSeek-V3",
    "deepseek-ai/DeepSeek-V3.2",
]

def fetch_online_models(api_key=None):
    """🔑 先 ping 再返回 - 逐个发 tiny 请求，200 才算真能用"""
    if not api_key:
        api_key = config.SILICONFLOW_API_KEY
    
    if not api_key:
        return CANDIDATE_MODELS
    
    valid = []
    for mid in CANDIDATE_MODELS:
        try:
            resp = requests.post(
                f"{config.SILICONFLOW_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": mid,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 3  # 只让它吐 3 个 token，几乎不花钱
                },
                timeout=10
            )
            if resp.status_code == 200:
                valid.append(mid)
                print(f"  ✅ {mid}")
            else:
                print(f"  ❌ {mid} ({resp.status_code})")
        except Exception as e:
            print(f"  ❌ {mid} (超时)")
    
    if not valid:
        print("⚠️  没一个能在线跑，返回候选池兜底")
        return CANDIDATE_MODELS
    
    return valid

def fetch_local_models():
    try:
        resp = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        return []

# ============ 全局状态 ============
print("=" * 50, flush=True)
print("🚀 TestAgent Web UI 启动中...", flush=True)
print("=" * 50, flush=True)

FREE_MODELS = fetch_online_models()
LOCAL_MODELS = fetch_local_models()

print(f"📡 免费模型: {len(FREE_MODELS)} 个 -> {FREE_MODELS}", flush=True)
print(f"📡 本地模型: {len(LOCAL_MODELS)} 个 -> {LOCAL_MODELS}", flush=True)

agent = None
current_api_key = config.SILICONFLOW_API_KEY or ""
default_mode = "在线" if config.USE_ONLINE else "离线"

# ============ 核心函数 ============
def init_agent(mode, model_name, api_key):
    global agent, current_api_key
    
    current_api_key = api_key or config.SILICONFLOW_API_KEY
    config.SILICONFLOW_API_KEY = current_api_key
    
    if mode == "在线":
        if not current_api_key:
            return "❌ 请先填入 API Key"
        config.USE_ONLINE = True
        config.ONLINE_MODEL = model_name
        config.TIMEOUT = 120
        llm = SiliconFlowClient()
        if not llm.check_available():
            # 🆕 在线初始化失败 → 自动尝试离线
            local = fetch_local_models()
            if local:
                config.USE_ONLINE = False
                config.LOCAL_MODEL = local[0]
                config.TIMEOUT = 300
                llm = LocalOllamaClient()
                if llm.check_available():
                    agent = TestAgent(llm)
                    status = f"⚠️ 在线不可用，已自动切离线 | {local[0]}"
                    print(status, flush=True)
                    return status
            return "❌ 在线+离线都不可用，请检查 API Key 或 Ollama"
    else:
        config.USE_ONLINE = False
        config.LOCAL_MODEL = model_name
        config.TIMEOUT = 300
        llm = LocalOllamaClient()
        if not llm.check_available():
            return "❌ 本地初始化失败，请先 ollama serve"
    
    agent = TestAgent(llm)
    status = f"✅ {mode} | {model_name}"
    print(status, flush=True)
    return status

def refresh_models(api_key):
    """换 Key 后重新验证免费模型"""
    free = fetch_online_models(api_key)
    print(f"🔄 刷新: {len(free)} 个可用", flush=True)
    return (
        gr.update(choices=free, value=(free[0] if free else None)),
        f"📊 可用免费模型: **{len(free)}** 个"
    )

def on_mode_change(mode, api_key):
    if mode == "在线":
        free = fetch_online_models(api_key)
        return gr.update(choices=free, value=(free[0] if free else None))
    else:
        local = fetch_local_models()
        return gr.update(choices=local, value=(local[0] if local else None))

def safe_history(history):
    clean = []
    for item in history or []:
        if isinstance(item, dict) and "role" in item and "content" in item:
            clean.append(item)
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            clean.append({"role": "user", "content": item[0]})
            clean.append({"role": "assistant", "content": item[1]})
    return clean

def chat_response(message, history):
    global agent
    history = safe_history(history)
    if not agent:
        yield "", history, "⚠️ 请先应用设置初始化"
        return
    if not message.strip():
        yield "", history, ""
        return

    print(f"\n[你] {message}", flush=True)
    history.append({"role": "user", "content": message})
    
    full_reply = ""
    try:
        # 确保调的是 chat_stream，不是 chat
        for chunk, trace_text in agent.chat_stream(message):
            full_reply += chunk
            if history and history[-1]["role"] == "assistant":
                history[-1]["content"] = full_reply
            else:
                history.append({"role": "assistant", "content": full_reply})
            yield "", history, trace_text
    except Exception as e:
        full_reply = f"⚠️ 请求失败: {e}"
        print(f"❌ {full_reply}", flush=True)
        if history and history[-1]["role"] == "assistant":
            history[-1]["content"] = full_reply
        yield "", history, f"❌ {full_reply}"

def reset_agent():
    global agent
    if agent:
        agent.reset()
    print("\n🔄 对话已重置", flush=True)
    return [], "🔄 对话已重置"

# ============ 构建界面 ============
with gr.Blocks(title="TestAgent - 软件测试助手") as demo:
    gr.Markdown("""
    # 🤖 TestAgent - 软件测试 AI 助手
    在线免费模型 + 本地 Ollama · ReAct 工具调用
    """)

    with gr.Row():
        # 左侧设置面板
        with gr.Column(scale=1):
            gr.Markdown("### 🔑 API Key")
            
            api_key_input = gr.Textbox(
                value=current_api_key,
                placeholder="输入 SiliconFlow API Key...",
                label="API Key",
                type="password"
            )
            
            refresh_btn = gr.Button("🔄 刷新模型")
            model_stats = gr.Markdown(
                f"📊 可用免费模型: **{len(FREE_MODELS)}** 个"
            )
            
            gr.Markdown("### ⚙️ 模型设置")
            
            mode_radio = gr.Radio(["在线", "离线"], value=default_mode, label="运行模式")
            
            model_dropdown = gr.Dropdown(
                choices=FREE_MODELS if default_mode == "在线" else LOCAL_MODELS,
                value=(FREE_MODELS[0] if default_mode == "在线" and FREE_MODELS 
                       else (LOCAL_MODELS[0] if LOCAL_MODELS else None)),
                label="选择模型",
                interactive=True
            )
            
            apply_btn = gr.Button("🔄 应用设置", variant="primary")
            settings_status = gr.Markdown("⏳ 点击应用后初始化...")

        # 右侧聊天
                # 右侧：聊天 + Trace 两栏
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=400)
            
            with gr.Row():
                with gr.Column(scale=2):
                    msg = gr.Textbox(placeholder="输入你的测试问题...", label="你", lines=2)
                    with gr.Row():
                        submit_btn = gr.Button("🚀 发送", variant="primary")
                        stop_btn = gr.Button("🛑 停止生成")
                        reset_btn = gr.Button("🔄 重置对话")
                with gr.Column(scale=1):
                    trace_box = gr.Textbox(
                        label="🔍 Agent Trace（思考链路）",
                        lines=10,
                        interactive=False
                        # ❌ show_copy_button=True  删掉这行
                    )

            status = gr.Markdown("✅ 等待应用设置...")

    # 事件绑定
    refresh_btn.click(refresh_models, [api_key_input], [model_dropdown, model_stats])
    mode_radio.change(on_mode_change, [mode_radio, api_key_input], model_dropdown)
    apply_btn.click(init_agent, [mode_radio, model_dropdown, api_key_input], settings_status)
    
    submit_btn.click(chat_response, [msg, chatbot], [msg, chatbot, trace_box])
    msg.submit(chat_response, [msg, chatbot], [msg, chatbot, trace_box])
    stop_btn.click(lambda: print("🛑 停止", flush=True))
    reset_btn.click(reset_agent, [], [chatbot, status])

if __name__ == "__main__":
    print("\n" + "=" * 50, flush=True)
    print("🌐 打开: http://localhost:7860", flush=True)
    print("=" * 50 + "\n", flush=True)
    demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True)