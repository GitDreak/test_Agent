"""
Agent 核心类
负责管理对话历史、构造 prompt、调用 LLM
"""
from llm_client import LLMClient

class TestAgent:
    """软件测试 Agent - 内置测试专家角色 Prompt"""

    SYSTEM_PROMPT = """你是一名资深的软件测试工程师，擅长：
1. 根据需求文档设计全面的测试用例（功能测试、边界测试、异常测试）
2. 分析 bug 报告并给出复现步骤和定位思路
3. 评审测试方案的合理性和覆盖率
4. 提出性能测试、安全测试的建议

请用专业但易懂的方式回答，必要时给出具体示例。"""

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.history: list[dict] = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]

    def chat(self, user_input: str) -> str:
        """对话 - 使用流式打字机效果，同时返回完整文本"""
        self.history.append({"role": "user", "content": user_input})
        full_reply = []
        try:
            # 调用流式接口，边收边打印
            for chunk in self.llm.chat_stream(self.history):
                print(chunk, end="", flush=True)
                full_reply.append(chunk)
            print()  # 换行
            reply_text = "".join(full_reply)
            self.history.append({"role": "assistant", "content": reply_text})
            return reply_text
        except Exception as e:
            self.history.pop()
            print()
            error_msg = f"[Agent 错误] {e}"
            print(error_msg)
            return error_msg

    def reset(self):
        self.history = [{"role": "system", "content": self.SYSTEM_PROMPT}]

    def show_history(self):
        for msg in self.history:
            role = msg["role"].upper()
            print(f"\n[{role}]\n{msg['content']}")