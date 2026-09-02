"""
工具模块 - 测试领域专用工具
"""
import math
import re
import csv
import io
import json
from datetime import datetime

TOOLS = []

def tool(name, description):
    def decorator(func):
        TOOLS.append({"name": name, "description": description, "func": func})
        return func
    return decorator

# ========== 原有 3 个工具（保留） ==========
@tool(
    name="calc",
    description="执行数学表达式，常用于计算缺陷率、覆盖率。参数：expression (str)"
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
    description="根据功能需求生成结构化测试用例模板。参数：requirement (str)"
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

请补充具体输入数据和预期结果。"""

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
    description="查询软件测试知识库。参数：keyword (str)"
)
def query_knowledge(keyword: str) -> str:
    for key, value in TEST_KNOWLEDGE.items():
        if keyword in key or key in keyword:
            return f"【{key}】{value}"
    return f"未找到 '{keyword}'。可用: {', '.join(TEST_KNOWLEDGE.keys())}"

# ========== 🆕 工具 4: HTTP 请求工具 ==========
@tool(
    name="http_request",
    description="发送 HTTP 请求调试接口。参数格式: GET|POST|URL|JSON参数(可选)\n示例: GET|https://httpbin.org/get  或  POST|https://httpbin.org/post|{\"name\":\"test\"}"
)
def http_request(param_str: str) -> str:
    import requests
    parts = param_str.split("|")
    if len(parts) < 2:
        return "❌ 格式错误，应该是: GET|URL 或 POST|URL|{json}"
    
    method = parts[0].strip().upper()
    url = parts[1].strip()
    
    # 🛡️ 安全检查：禁止内网 IP
    if any(ip in url for ip in ["localhost", "127.0.0.1", "192.168.", "10.", "172.16."]):
        return "🛡️ 安全限制：禁止访问内网地址"
    
    try:
        if method == "GET":
            resp = requests.get(url, timeout=10)
        elif method == "POST":
            json_body = json.loads(parts[2]) if len(parts) > 2 else {}
            resp = requests.post(url, json=json_body, timeout=10)
        else:
            return f"❌ 不支持的方法: {method}"
        
        result = f"✅ HTTP {resp.status_code} | {resp.reason}\n"
        result += f"⏱️  耗时: {resp.elapsed.total_seconds():.2f}s\n"
        result += f"📦 响应: {resp.text[:500]}"
        return result
    except Exception as e:
        return f"❌ 请求失败: {e}"

# ========== 🆕 工具 5: 日志解析工具 ==========
@tool(
    name="parse_log",
    description="解析日志，提取错误/异常栈。参数：log_text (str) - 粘贴的日志内容"
)
def parse_log(log_text: str) -> str:
    if not log_text or len(log_text) < 10:
        return "❌ 日志内容太少，请粘贴完整日志"
    
    errors = []
    # 匹配常见错误关键字
    for keyword in ["ERROR", "Exception", "Traceback", "FATAL", "CRITICAL", "Failed", "失败", "异常"]:
        matches = [(m.start(), log_text[max(0,m.start()-30):m.start()+200]) 
                   for m in re.finditer(keyword, log_text, re.IGNORECASE)]
        errors.extend(matches)
    
    if not errors:
        return "✅ 未检测到明显错误关键字"
    
    errors.sort(key=lambda x: x[0])
    result = f"🔍 共发现 {len(errors)} 处疑似错误：\n\n"
    for i, (pos, ctx) in enumerate(errors[:5], 1):  # 最多展示 5 个
        result += f"【#{i}】位置 {pos}:\n{ctx.strip()}\n---\n"
    
    return result

# ========== 🆕 工具 6: Bug 报告生成 ==========
@tool(
    name="gen_bug_report",
    description="根据问题描述生成标准 Bug 单。参数：description (str) - 问题现象描述"
)
def gen_bug_report(description: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""## 🐛 Bug 报告

**标题**: {description[:50]}...
**严重级别**: [ ] P0-致命 [ ] P1-严重 [x] P2-一般 [ ] P3-轻微
**优先级**: High

---

### 📋 复现步骤
1. 
2. 
3. 

### ✅ 预期结果

### ❌ 实际结果
{description}

### 🌐 环境信息
- 操作系统: 
- 浏览器/设备: 
- 应用版本: 
- 接口地址: 

### 📎 附加信息
- 日志片段: 
- 截图/录屏: 
- 复现概率: [ ] 必现 [x] 偶尔 [ ] 仅特定条件

---
*自动生成于 {now}*"""

# ========== 🆕 工具 7: 用例导出 CSV ==========
@tool(
    name="export_cases",
    description="将测试用例导出为 CSV 格式（可直接存文件或复制）。参数：cases_text (str) - Markdown 表格格式的用例"
)
def export_cases(cases_text: str) -> str:
    # 尝试解析 Markdown 表格
    lines = cases_text.strip().split('\n')
    table_lines = [l for l in lines if l.startswith('|') and not set(l.replace('|','').replace('-','').replace(' ','')).issubset(set('-:'))]
    
    if len(table_lines) < 2:
        return "❌ 未识别到测试用例表格，请确认格式正确"
    
    output = io.StringIO()
    writer = csv.writer(output)
    for line in table_lines:
        row = [cell.strip() for cell in line.split('|')[1:-1]]
        writer.writerow(row)
    
    csv_content = output.getvalue()
    csv_filename = f"test_cases_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return f"✅ 已导出 CSV 文件: {csv_filename}\n\n```csv\n{csv_content}```"

# ============ 执行器（原有） ============
def execute_tool(tool_name: str, arguments: str) -> str:
    for t in TOOLS:
        if t["name"] == tool_name:
            print(f"\n  🔧 [调用工具] {tool_name}({arguments[:50]}...)")
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