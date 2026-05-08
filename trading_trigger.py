import anthropic
import os
import datetime

AGENT_ID = "agt_011CaqNdUSAnH7rBgBGkXR4z"
ENVIRONMENT_ID = "env_018fWQY1wVF6FdfscF3RSxLT"

def is_market_open():
    today = datetime.date.today()
    if today.weekday() >= 5:
        print(f"Market closed today ({today.strftime('%A')}). Skipping.")
        return False
    return True

def run_trading_session():
    if not is_market_open():
        return

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    print(f"Creating trading session — {datetime.datetime.now()}")

    session = client.beta.sessions.create(
        agent=AGENT_ID,
        environment_id=ENVIRONMENT_ID,
        title=f"Trading Session {datetime.date.today().isoformat()}",
    )
    print(f"Session created: {session.id}")

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
    print("Kickoff message sent. Agent is now running.")

    for event in client.beta.sessions.events.stream(session_id=session.id):
        event_type = getattr(event, 'type', str(event))

        if 'agent.message' in str(event_type):
            content = getattr(event, 'content', [])
            for block in content:
                text = getattr(block, 'text', '')
                if text:
                    print(f"[AGENT] {text[:300]}")

        elif 'agent.tool_use' in str(event_type):
            name = getattr(event, 'name', 'unknown')
            print(f"[TOOL] {name}")

        elif 'session.status_idle' in str(event_type):
            stop = getattr(event, 'stop_reason', {})
            stop_type = getattr(stop, 'type', '') if stop else ''
            if stop_type != 'requires_action':
                print("Session completed for today.")
                break

        elif 'session.error' in str(event_type):
            print(f"[ERROR] {event}")
            break

    print(f"Done — {datetime.datetime.now()}")

if __name__ == "__main__":
    run_trading_session()
