"""
配置文件 - 统一管理 Agent 的所有配置
通过环境变量 .env 或直接修改下面的常量来切换模式
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# ==========================================
#  🔀 核心开关：True=在线硅基流动, False=本地Ollama
# ==========================================
USE_ONLINE = True

# ==========================================
#  🌐 在线配置 - 硅基流动 (SiliconFlow)
# ==========================================
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
# 硅基流动上的模型名，和图1一致
ONLINE_MODEL = "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"

# ==========================================
#  💻 离线配置 - 本地 Ollama
# ==========================================
OLLAMA_BASE_URL = "http://localhost:11434"
# 本地拉取的模型名
LOCAL_MODEL = "qwen3.5:4b"

# ==========================================
#  🔄 降级开关
# ==========================================
# True = 在线连不上时自动切到本地
AUTO_FALLBACK = True

# 连接超时秒数
TIMEOUT = 120