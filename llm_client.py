"""
LLM 客户端模块
采用策略模式，统一在线/离线两种调用方式
- 在线: 硅基流动 (OpenAI 兼容接口)
- 离线: 本地 Ollama (OpenAI 兼容接口)
"""
import requests
from abc import ABC, abstractmethod

import config

# ==================================================
#  🧱 抽象基类 - 定义统一接口
# ==================================================
class LLMClient(ABC):
    """所有 LLM 客户端的基类，保证对外接口一致"""

    @abstractmethod
    def chat(self, messages: list[dict], **kwargs) -> str:
        """
        发送消息给模型，返回回复文本
        :param messages: [{"role": "user", "content": "..."}, ...]
        :return: 模型回复的纯文本
        """
        pass

    @abstractmethod
    def check_available(self) -> bool:
        """检测模型是否可用"""
        pass

# ==================================================
#  🌐 在线 - 硅基流动
# ==================================================
class SiliconFlowClient(LLMClient):
    """调用硅基流动 API"""

    def __init__(self):
        self.api_key = config.SILICONFLOW_API_KEY
        self.base_url = config.SILICONFLOW_BASE_URL
        self.model = config.ONLINE_MODEL

    def check_available(self) -> bool:
        if not self.api_key:
            print("  [!] SiliconFlow API Key 未配置")
            return False
        try:
            resp = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=config.TIMEOUT,
            )
            return resp.status_code == 200
        except requests.RequestException as e:
            print(f"  [!] SiliconFlow 连接失败: {e}")
            return False

    def chat(self, messages: list[dict], **kwargs) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=config.TIMEOUT)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

# ==================================================
#  💻 离线 - 本地 Ollama
# ==================================================
class LocalOllamaClient(LLMClient):
    """调用本地 Ollama 服务"""

    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.LOCAL_MODEL

    def check_available(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            models = resp.json().get("models", [])
            available = any(m["name"].startswith(self.model) for m in models)
            if not available:
                print(f"  [!] 本地模型 {self.model} 未找到，请先执行: ollama pull {self.model}")
            return available
        except requests.RequestException as e:
            print(f"  [!] Ollama 未启动: {e}")
            print(f"      请执行: ollama serve")
            return False

    def chat(self, messages: list[dict], **kwargs) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 2048),
            },
        }
        resp = requests.post(url, json=payload, timeout=config.TIMEOUT)
        resp.raise_for_status()
        return resp.json()["message"]["content"]

# ==================================================
#  🏭 工厂函数 - 自动选择 + 降级
# ==================================================
def create_llm_client() -> LLMClient:
    """
    根据配置创建 LLM 客户端
    - USE_ONLINE=True: 先尝试硅基流动，失败则降级到本地
    - USE_ONLINE=False: 直接用本地 Ollama
    """
    if config.USE_ONLINE:
        client = SiliconFlowClient()
        print("[*] 尝试在线模式 (SiliconFlow)...")
        if client.check_available():
            print("[✓] 在线模式已就绪")
            return client
        if config.AUTO_FALLBACK:
            print("[↓] 自动降级到本地 Ollama...")
        else:
            raise ConnectionError("在线模式不可用，降级已禁用")

    # 使用本地
    client = LocalOllamaClient()
    if not client.check_available():
        raise ConnectionError("本地 Ollama 不可用，请检查服务是否启动")
    print("[✓] 本地模式已就绪")
    return client