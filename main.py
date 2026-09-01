"""
CLI 入口 - 交互式测试 Agent
"""
import sys
import io

# Windows 控制台中文乱码修复
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.agent import TestAgent
from src.llm_client import create_llm_client

def main():
    print("=" * 50)
    print("  🤖 TestAgent - 软件测试助手")
    print("=" * 50)

    try:
        llm = create_llm_client()
    except Exception as e:
        print(f"[✗] 初始化失败: {e}")
        return

    agent = TestAgent(llm)

    print("\n✅ Agent 已就绪！输入你的测试问题，或输入命令：")
    print("   /reset  - 重置对话")
    print("   /history - 查看历史")
    print("   /quit   - 退出")
    print("-" * 50)

    while True:
        try:
            user_input = input("\n[你] ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            cmd = user_input.lower()
            if cmd in ("/quit", "/exit"):
                print("👋 再见！")
                break
            elif cmd == "/reset":
                agent.reset()
                print("🔄 对话已重置")
                continue
            elif cmd == "/history":
                agent.show_history()
                continue
            else:
                print(f"❓ 未知命令: {user_input}")
                continue

        print("\n[Agent] ", end="", flush=True)
        agent.chat(user_input)

if __name__ == "__main__":
    main()