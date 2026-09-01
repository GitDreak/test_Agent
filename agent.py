"""
Agent 核心类
负责管理对话历史、构造 prompt、调用 LLM
"""
from llm_client import LLMClient

class TestAgent:
    """
    软件测试 Agent
    可以根据用户描述生成测试用例、测试思路等
    """

    # 系统提示词 - 设定 Agent 角色
    SYSTEM_PROMPT = """你是一名资深的软件测试工程师，擅长：
1. 根据需求文档设计全面的测试用例（功能测试、边界测试、异常测试）
2. 分析 bug 报告并给出复现步骤和定位思路
3. 评审测试方案的合理性和覆盖率
4. 提出性能测试、安全测试的建议

请用专业但易懂的方式回答，必要时给出具体示例。"""

    def __init__(self, llm: LLMClient):
        self.llm = llm
        # 对话历史，用于多轮上下文
        self.history: list[dict] = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]

    def chat(self, user_input: str) -> str:
        """单轮对话"""
        self.history.append({"role": "user", "content": user_input})
        try:
            reply = self.llm.chat(self.history)
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            error_msg = f"[Agent 错误] {e}"
            self.history.pop()  # 移除失败的 user message
            return error_msg

    def reset(self):
        """重置对话历史"""
        self.history = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]

    def show_history(self):
        """打印当前对话历史（调试用）"""
        for msg in self.history:
            role = msg["role"].upper()
            print(f"\n[{role}]\n{msg['content']}")