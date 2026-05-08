import sys
import os
import datetime

AGENT_ID = "agent_011Cap12j53tSWAWcgfi8Nbw"
ENVIRONMENT_ID = "env_018fWQY1wVF6FdfscF3RSxLT"
ACCOUNT_NUMBER = "53826201"

print(f"Python version: {sys.version}")
print(f"Agent ID: {AGENT_ID}")
print(f"Environment ID: {ENVIRONMENT_ID}")

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

try:
    client = anthropic.Anthropic(api_key=api_key)
    print("Client created OK.")
    print("Creating session...")

    session = client.beta.sessions.create(
        agent=AGENT_ID,
        environment_id=ENVIRONMENT_ID,
        title=f"Trading Session {datetime.date.today().isoformat()}",
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
                    f"Questrade refresh token for this session: {questrade_token}\n"
                    f"Account number: {ACCOUNT_NUMBER}\n\n"
                    "Bootstrap your environment using STEP 1, then authenticate with Questrade "
                    "using the refresh token above (write it to "
                    "/workspace/trading/auth/questrade_token.json), fetch account info, "
                    "then begin your 5-minute trading cycle loop until 4:00 PM ET. "
                    "Log everything. No human will intervene — operate fully autonomously."
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
