"""
Agent 核心类 - ReAct + 自动工具兜底
"""
import re
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm_client import LLMClient
from src.tools import get_tools_description, execute_tool

REACT_PROMPT = """你是一名资深的软件测试工程师，擅长：
1. 根据需求设计全面的测试用例
2. 分析 bug 报告并给出定位思路
3. 评审测试方案的合理性和覆盖率
4. 提出性能、安全测试的建议

{tools_desc}

【重要】即使你认为不需要调用工具，你也必须先用 1 句话说明你的思考过程（Thought），再给出最终答案。
思考格式：先写一句话说明你打算怎么回答，再写具体答案。

如果有工具返回的结果，请严格基于工具结果回答，不要自己重新计算或瞎编数字。"""

MAX_ITERATIONS = 3

def parse_react(text: str):
    """从 LLM 回复里提取 Action"""
    match = re.search(r'```(?:\w*\n)?(.*?)```', text, re.DOTALL)
    if not match:
        return None, None
    block = match.group(1)
    action = None
    action_input = None
    for line in block.split('\n'):
        line = line.strip()
        if line.startswith('Action:'):
            action = line[len('Action:'):].strip()
        elif line.startswith('Action Input:'):
            action_input = line[len('Action Input:'):].strip()
    return action, action_input

def auto_detect_tool(user_input: str):
    """自动检测用户意图"""
    text = user_input.lower()

    # 验证等式（如 "测试3+3=0?"）
    eq_match = re.search(r'([\d\.]+)\s*[+\-*/×÷]\s*([\d\.]+)\s*=\s*([\d\.]+)', user_input)
    if eq_match:
        left = eq_match.group(1).replace('×', '*').replace('÷', '/')
        op = re.search(r'[+\-*/×÷]', user_input).group().replace('×', '*').replace('÷', '/')
        right = eq_match.group(3)
        return "verify_eq", f"{left}{op}{right}"

    # 纯数学表达式
    stripped = re.sub(r'[\u4e00-\u9fff\s\?？.,。！!、，]', '', user_input)
    math_match = re.fullmatch(r'[\d\.]+\s*[+\-*/×÷]\s*[\d\.]+', stripped)
    if math_match:
        expr = math_match.group().replace(' ', '').replace('×', '*').replace('÷', '/')
        return "calc", expr

    # 计算率/百分比
    has_numbers = bool(re.search(r'\d+', user_input))
    calc_intent = ['算', '计算', '率', '百分比', '覆盖率', 'bug率', '缺陷率', '%', '多少', '等于']
    if has_numbers and any(kw in text for kw in calc_intent):
        nums = re.findall(r'\d+(?:\.\d+)?', user_input)
        if len(nums) >= 2:
            if any(kw in text for kw in ['率', '百分比', '覆盖率', '%']):
                small = min(float(nums[0]), float(nums[1]))
                big = max(float(nums[0]), float(nums[1]))
                return "calc", f"{small}/{big}*100"
            expr = re.search(r'(\d+(?:\.\d+)?\s*[+\-*/]\s*\d+(?:\.\d+)?)', user_input)
            if expr:
                return "calc", expr.group(1).replace(' ', '')
        elif nums:
            return "calc", nums[0]

    # 查知识/行情/介绍
    TEST_KEYWORDS = ['黑盒测试', '白盒测试', '冒烟测试', '回归测试', '性能测试', '安全测试', 
                     'bug报告', 'bug 报告', '测试用例', '覆盖率', '缺陷率', 'bug率',
                     '软件测试', '测试工程师', '测试职业']
    for kw in ['什么是', '是什么', '介绍一下', '解释一下', '行情', '趋势', '前景', '发展']:
        if kw in user_input:
            for tk in TEST_KEYWORDS:
                if tk in user_input:
                    return "query_knowledge", tk

    # 检测生成用例
    if any(kw in text for kw in ['测试用例', 'test case']):
        return "generate_cases", user_input

    return None, None

# ============ 🎯 新增：验证等式的专用处理 ============
def verify_equation(user_input: str) -> str:
    """验证等式是否正确"""
    eq_match = re.search(r'([\d\.]+)\s*([+\-*/×÷])\s*([\d\.]+)\s*=\s*([\d\.]+)', user_input)
    if not eq_match:
        return "无法解析等式"
    
    a = float(eq_match.group(1))
    op = eq_match.group(2).replace('×', '*').replace('÷', '/')
    b = float(eq_match.group(3))
    expect = float(eq_match.group(4))
    
    expr = f"{a}{op}{b}"
    safe_globals = {"__builtins__": {}}
    actual = eval(expr, safe_globals)
    
    is_correct = abs(actual - expect) < 0.0001
    result = "✅ 正确" if is_correct else f"❌ 错误"
    detail = f"计算 {expr} = {actual}，而不是 {expect}"
    
    if is_correct:
        return f"✅ 等式正确！{expr} = {actual}"
    else:
        return f"❌ 等式错误！{detail}"

class TestAgent:
    """软件测试 Agent"""

    def __init__(self, llm: LLMClient):
        self.llm = llm
        tools_desc = get_tools_description()
        self.history: list[dict] = [
            {"role": "system", "content": REACT_PROMPT.format(tools_desc=tools_desc)}
        ]

    def chat(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        # 自动兜底
        auto_action, auto_input = auto_detect_tool(user_input)
        if auto_action:
            print(f"🛡️  [自动检测] {auto_action}({auto_input})")
            
            # 🎯 新增：验证等式不走通用工具
            if auto_action == "verify_eq":
                reply = verify_equation(user_input)
            else:
                tool_result = execute_tool(auto_action, auto_input)
                print(f"📦  工具返回: {tool_result}")
                if auto_action == "calc":
                    parts = tool_result.split('=', 1)
                    val = parts[1].strip() if len(parts) > 1 else tool_result
                    reply = f"✅ {auto_input} = {val}"
                else:
                    reply = f"✅ {tool_result}"
            
            self.history.append({"role": "assistant", "content": reply})
            print(f"🤖  Agent: {reply}")
            return reply

        # 没触发工具 → 走 LLM
        for iteration in range(1, MAX_ITERATIONS + 1):
            print(f"[迭代 {iteration}] LLM 思考中...")
            full_reply = []
            for chunk in self.llm.chat_stream(self.history):
                print(chunk, end="", flush=True)
                full_reply.append(chunk)
            print()
            reply_text = "".join(full_reply)
            self.history.append({"role": "assistant", "content": reply_text})

            action, action_input = parse_react(reply_text)
            if not action:
                break
            print(f"🔧 LLM 请求工具: {action}({action_input})")
            tool_result = execute_tool(action, action_input)
            self.history.append({"role": "user", "content": f"工具 {action} 返回:\n{tool_result}\n请基于此回答。"})

        return reply_text

    def chat_stream(self, user_input: str):
        """流式 + Trace - yield (content_chunk, trace_line)"""
        trace_lines = []
        
        def trace(msg):
            trace_lines.append(msg)
            print(msg, flush=True)
        
        trace(f"🧑 用户输入: {user_input}")
        self.history.append({"role": "user", "content": user_input})

        # 自动兜底
        auto_action, auto_input = auto_detect_tool(user_input)
        if auto_action:
            trace(f"🔍 [自动检测] {auto_action}")
            
            if auto_action == "verify_eq":
                reply = verify_equation(user_input)
            else:
                trace(f"🔧 调用: {auto_action}({auto_input})")
                tool_result = execute_tool(auto_action, auto_input)
                trace(f"📦 返回: {str(tool_result)[:80]}")
                
                if auto_action == "calc":
                    parts = tool_result.split('=', 1)
                    val = parts[1].strip() if len(parts) > 1 else tool_result
                    reply = f"✅ {auto_input} = {val}"
                else:
                    reply = f"✅ {tool_result}"
            
            self.history.append({"role": "assistant", "content": reply})
            trace(f"📝 输出: {reply}")
            yield reply, "\n".join(trace_lines)
            return

        # LLM 流式  ← 注意这里没有多余缩进！
        full_reply = []
        for iteration in range(1, MAX_ITERATIONS + 1):
            trace(f"🧠 [迭代 {iteration}] 思考中...")
            
            for chunk in self.llm.chat_stream(self.history):
                if chunk:
                    full_reply.append(chunk)
                    yield chunk, "\n".join(trace_lines)
            
            reply_text = "".join(full_reply)
            self.history.append({"role": "assistant", "content": reply_text})
            
            thought_match = re.search(r'思考[:：]\s*(.+?)(?:\n|$)', reply_text[:200])
            if thought_match:
                trace(f"💭 思考: {thought_match.group(1).strip()}")
            else:
                trace(f"💭 直接回答（无需工具）")
            
            trace(f"📝 回复长度: {len(reply_text)} 字符")

            action, action_input = parse_react(reply_text)
            if not action:
                break
            trace(f"🔧 请求工具: {action}({action_input})")
            tool_result = execute_tool(action, action_input)
            trace(f"📦 工具返回: {str(tool_result)[:60]}")
            self.history.append({"role": "user", "content": f"工具 {action} 返回:\n{tool_result}\n请基于此回答。"})
        
        yield "", "\n".join(trace_lines)

    def reset(self):
        tools_desc = get_tools_description()
        self.history = [{"role": "system", "content": REACT_PROMPT.format(tools_desc=tools_desc)}]

    def show_history(self):
        for msg in self.history:
            role = msg["role"].upper()
            print(f"\n[{role}]\n{msg['content']}")