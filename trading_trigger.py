import anthropic
import os
import datetime
import sys

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
        print("Skipping — market closed.")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY secret not set in GitHub Secrets.")
        sys.exit(1)

    print(f"API key found. Length: {len(api_key)}")

    try:
        client = anthropic.Anthropic(api_key=api_key)

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

    except anthropic.AuthenticationError:
        print("ERROR: Invalid Anthropic API key. Check your GitHub Secret.")
        sys.exit(1)
    except anthropic.APIError as e:
        print(f"ERROR: Anthropic API error — {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error — {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_trading_session()
