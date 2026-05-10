import sys
import os
import datetime

AGENT_ID = "agent_011Cap12j53tSWAWcgfi8Nbw"
ENVIRONMENT_ID = "env_018fWQY1wVF6FdfscF3RSxLT"
ACCOUNT_NUMBER = "53826201"
MEMORY_STORE_ID = "memstore_01FM5ZuZ8dM8L4AnFHXHuZM6"

print(f"Python version: {sys.version}")
print(f"Agent ID: {AGENT_ID}")
print(f"Environment ID: {ENVIRONMENT_ID}")
print(f"Memory Store ID: {MEMORY_STORE_ID}")

try:
    import anthropic
    print(f"Anthropic SDK version: {anthropic.__version__}")
except ImportError as e:
    print(f"ERROR importing anthropic: {e}")
    sys.exit(1)

api_key = os.environ.get("ANTHROPIC_API_KEY", "")
print(f"API key set: {bool(api_key)} | Length: {len(api_key)}")
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY is empty.")
    sys.exit(1)

questrade_token = os.environ.get("QUESTRADE_REFRESH_TOKEN", "")
print(f"Questrade token set: {bool(questrade_token)} | Length: {len(questrade_token)}")
if not questrade_token:
    print("ERROR: QUESTRADE_REFRESH_TOKEN is empty.")
    sys.exit(1)

github_token = os.environ.get("GH_PUSH_TOKEN", "")
print(f"GitHub token set: {bool(github_token)} | Length: {len(github_token)}")
if not github_token:
    print("ERROR: GH_PUSH_TOKEN is empty.")
    sys.exit(1)

try:
    client = anthropic.Anthropic(api_key=api_key)
    print("Client created OK.")
    print("Creating session...")

    session = client.beta.sessions.create(
        agent=AGENT_ID,
        environment_id=ENVIRONMENT_ID,
        title=f"Trading Session {datetime.date.today().isoformat()}",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": MEMORY_STORE_ID,
                "access": "read_write",
                "instructions": "Persistent trading memory — read at startup to load past trades, learnings, watchlist and risk events. Write new learnings after each cycle and at end of day."
            }
        ]
    )
    print(f"SUCCESS — Session created: {session.id}")

    client.beta.sessions.events.send(
        session_id=session.id,
        events=[{
            "type": "user.message",
            "content": [{
                "type": "text",
                "text": (
                    f"NYSE is now open. Today is {datetime.date.today().isoformat()}.\n\n"
                    f"refresh_token: {questrade_token}\n"
                    f"account: {ACCOUNT_NUMBER}\n"
                    f"github_token: {github_token}\n\n"
                    "Execute ALL 12 steps in order. Start with STEP 1 bootstrap, "
                    "then STEP 2 read persistent memory, authenticate with Questrade, "
                    "run market research, generate dashboard, push to GitHub, "
                    "run trading cycle if market is open, update memory with learnings, "
                    "and write session summary. No human will intervene — operate fully autonomously."
                )
            }]
        }]
    )
    print("Kickoff message sent. Agent is running autonomously.")

    for event in client.beta.sessions.events.stream(session_id=session.id):
        event_type = getattr(event, 'type', str(event))
        print(f"[EVENT] {event_type}")

        if 'agent.message' in str(event_type):
            for block in getattr(event, 'content', []):
                text = getattr(block, 'text', '')
                if text:
                    print(f"[AGENT] {text[:200]}")

        elif 'agent.tool_use' in str(event_type):
            print(f"[TOOL] {getattr(event, 'name', 'unknown')}")

        elif 'session.status_idle' in str(event_type):
            stop = getattr(event, 'stop_reason', {})
            if getattr(stop, 'type', '') != 'requires_action':
                print("Session complete for today.")
                break

        elif 'session.error' in str(event_type):
            print(f"[ERROR] {event}")
            break

    print(f"Done — {datetime.datetime.now()}")

except Exception as e:
    print(f"FATAL ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
