"""
工具模块 - Agent 可调用的外部工具
"""
import math

TOOLS = []

def tool(name, description):
    def decorator(func):
        TOOLS.append({"name": name, "description": description, "func": func})
        return func
    return decorator

@tool(
    name="calc",
    description="执行 Python 数学表达式，返回结果。常用于计算覆盖率、缺陷率、统计数据。\n参数：expression (str) 如 '3/50*100'"
)
def calc(expression: str) -> str:
    safe_globals = {"__builtins__": {}, "math": math}
    try:
        result = eval(expression, safe_globals)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"

@tool(
    name="generate_cases",
    description="根据功能需求生成结构化的测试用例模板。\n参数：requirement (str) 如 '用户登录'"
)
def generate_cases(requirement: str) -> str:
    return f"""【{requirement} - 测试用例模板】

| 用例ID | 类型 | 测试场景 | 输入 | 预期结果 |
|--------|------|----------|------|----------|
| TC001 | 功能测试 | 正常流程 | - | - |
| TC002 | 边界测试 | 空值 | - | - |
| TC003 | 边界测试 | 最大/最小值 | - | - |
| TC004 | 异常测试 | 非法输入 | - | - |
| TC005 | 异常测试 | 网络异常 | - | - |
| TC006 | 异常测试 | 权限不足 | - | - |

请在此基础上补充具体的输入数据和预期结果。"""

TEST_KNOWLEDGE = {
    "黑盒测试": "不关注内部实现，只验证输入输出。方法：等价类划分、边界值分析、决策表、状态迁移。",
    "白盒测试": "关注内部代码逻辑。方法：语句覆盖、分支覆盖、条件覆盖、路径覆盖。",
    "冒烟测试": "对新版本做最基本的功能验证，确认系统能启动、核心功能可用。",
    "回归测试": "修改代码后重新运行已有用例，确认没有引入新 bug。",
    "性能测试": "关注响应时间、吞吐量、并发数、资源占用。工具：JMeter、Locust。",
    "安全测试": "OWASP Top 10：SQL 注入、XSS、CSRF、越权访问、敏感信息泄露等。",
    "bug报告": "标准格式：标题、环境、复现步骤、预期结果、实际结果、截图/日志、严重级别。",
}

@tool(
    name="query_knowledge",
    description="查询软件测试知识库，返回术语解释。\n参数：keyword (str) 如 '黑盒测试'"
)
def query_knowledge(keyword: str) -> str:
    for key, value in TEST_KNOWLEDGE.items():
        if keyword in key or key in keyword:
            return f"【{key}】{value}"
    return f"未找到 '{keyword}'。可用关键词: {', '.join(TEST_KNOWLEDGE.keys())}"

def execute_tool(tool_name: str, arguments: str) -> str:
    for t in TOOLS:
        if t["name"] == tool_name:
            print(f"\n  🔧 [调用工具] {tool_name}({arguments})")
            try:
                return t["func"](arguments)
            except Exception as e:
                return f"工具执行失败: {e}"
    return f"未找到工具: {tool_name}"

def get_tools_description() -> str:
    lines = ["可用工具：\n"]
    for t in TOOLS:
        lines.append(f"- {t['name']}: {t['description']}\n")
    return "\n".join(lines)
