"""
CLI 入口 - 交互式测试 Agent
"""
from agent import TestAgent
from llm_client import create_llm_client

def main():
    print("=" * 50)
    print("  🤖 TestAgent - 软件测试助手")
    print("=" * 50)

    # 1. 初始化 LLM 客户端
    try:
        llm = create_llm_client()
    except Exception as e:
        print(f"[✗] 初始化失败: {e}")
        return

    # 2. 创建 Agent
    agent = TestAgent(llm)

    print("\n✅ Agent 已就绪！输入你的测试问题，或输入命令：")
    print("   /reset  - 重置对话")
    print("   /history - 查看历史")
    print("   /quit   - 退出")
    print("-" * 50)

    # 3. 主循环
    while True:
        try:
            user_input = input("\n🧑‍💻 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")
            break

        if not user_input:
            continue

        # 处理命令
        if user_input.startswith("/"):
            cmd = user_input.lower()
            if cmd == "/quit" or cmd == "/exit":
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

        # 正常对话
        print("\n🤖 Agent: ", end="", flush=True)
        reply = agent.chat(user_input)
        print(reply)

if __name__ == "__main__":
    main()