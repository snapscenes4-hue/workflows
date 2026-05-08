import sys
print(f"Python version: {sys.version}")

try:
    import anthropic
    print(f"Anthropic SDK version: {anthropic.__version__}")
except ImportError as e:
    print(f"ERROR importing anthropic: {e}")
    sys.exit(1)

import os
import datetime

AGENT_ID = "agt_011Caqr6NAkdMGVUTLSt2ska6"
ENVIRONMENT_ID = "env_018fWQY1wVF6FdfscF3RSxLT"

api_key = os.environ.get("ANTHROPIC_API_KEY", "")
print(f"API key set: {bool(api_key)} | Length: {len(api_key)}")

if not api_key:
    print("ERROR: ANTHROPIC_API_KEY is empty or not set.")
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
    print(f"Session created: {session.id}")

    print("Sending kickoff message...")
    client.beta.sessions.events.send(
        session_id=session.id,
        events=[{
            "type": "user.message",
            "content": [{
                "type": "text",
                "text": (
                    f"NYSE is now open. Today is {datetime.date.today().isoformat()}. "
                    "Bootstrap your environment, check trading mode, authenticate with Questrade, "
                    "then begin your 5-minute trading cycle loop until 4:00 PM ET. "
                    "Log everything. No human will intervene — operate fully autonomously."
                )
            }]
        }]
    )
    print("Kickoff sent. Streaming events...")

    for event in client.beta.sessions.events.stream(session_id=session.id):
        event_type = getattr(event, 'type', str(event))
        print(f"[EVENT] {event_type}")

        if 'agent.message' in str(event_type):
            content = getattr(event, 'content', [])
            for block in content:
                text = getattr(block, 'text', '')
                if text:
                    print(f"[AGENT] {text[:200]}")

        elif 'agent.tool_use' in str(event_type):
            print(f"[TOOL] {getattr(event, 'name', 'unknown')}")

        elif 'session.status_idle' in str(event_type):
            stop = getattr(event, 'stop_reason', {})
            stop_type = getattr(stop, 'type', '') if stop else ''
            if stop_type != 'requires_action':
                print("Session complete.")
                break

        elif 'session.error' in str(event_type):
            print(f"[ERROR] {event}")
            break

    print("Done.")

except Exception as e:
    print(f"FATAL ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
