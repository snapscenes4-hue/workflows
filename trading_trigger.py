import sys
import os
import re
import datetime
import time
import requests
import base64
import json

AGENT_ID = "agent_011Cap12j53tSWAWcgfi8Nbw"
ENVIRONMENT_ID = "env_018fWQY1wVF6FdfscF3RSxLT"
ACCOUNT_NUMBER = "53826201"
MEMORY_STORE_ID = "memstore_01FM5ZuZ8dM8L4AnFHXHuZM6"
GITHUB_REPO = "snapscenes4-hue/workflows"

print(f"Python version: {sys.version}")
print(f"Agent ID: {AGENT_ID}")
print(f"Environment ID: {ENVIRONMENT_ID}")
print(f"Cycle time: {datetime.datetime.utcnow().isoformat()}Z")

try:
    import anthropic
    print(f"Anthropic SDK version: {anthropic.__version__}")
except ImportError as e:
    print(f"ERROR importing anthropic: {e}")
    sys.exit(1)

try:
    from nacl.public import SealedBox, PublicKey
    from nacl.encoding import RawEncoder
except ImportError as e:
    print(f"ERROR importing PyNaCl: {e}")
    sys.exit(1)

api_key = os.environ.get("ANTHROPIC_API_KEY", "")
questrade_token = os.environ.get("QUESTRADE_REFRESH_TOKEN", "")
github_token = os.environ.get("GH_PUSH_TOKEN", "")

print(f"API key set: {bool(api_key)} | Length: {len(api_key)}")
print(f"Questrade token set: {bool(questrade_token)} | Length: {len(questrade_token)}")
print(f"GitHub token set: {bool(github_token)} | Length: {len(github_token)}")

if not api_key:
    print("ERROR: ANTHROPIC_API_KEY is empty.")
    sys.exit(1)
if not questrade_token:
    print("ERROR: QUESTRADE_REFRESH_TOKEN is empty.")
    sys.exit(1)
if not github_token:
    print("ERROR: GH_PUSH_TOKEN is empty.")
    sys.exit(1)


def update_github_secret(secret_name, secret_value):
    """Encrypt and update a GitHub Actions secret."""
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    # Get repo public key
    key_resp = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/public-key",
        headers=headers
    )
    key_resp.raise_for_status()
    pub_key_data = key_resp.json()

    # Encrypt using PyNaCl SealedBox
    pub_key_bytes = base64.b64decode(pub_key_data["key"])
    sealed_box = SealedBox(PublicKey(pub_key_bytes))
    encrypted = base64.b64encode(sealed_box.encrypt(secret_value.encode())).decode()

    # Write secret
    put_resp = requests.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/{secret_name}",
        headers=headers,
        json={"encrypted_value": encrypted, "key_id": pub_key_data["key_id"]}
    )
    put_resp.raise_for_status()
    print(f"✅ Secret {secret_name} updated for next cycle")


try:
    client = anthropic.Anthropic(api_key=api_key)
    print("Client created OK.")

    # ── CREATE SESSION ──────────────────────────────────────────────────────────
    print("Creating session...")
    session = client.beta.sessions.create(
        agent=AGENT_ID,
        environment_id=ENVIRONMENT_ID,
        title=f"Trading Cycle {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M')}Z",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": MEMORY_STORE_ID,
                "access": "read_write",
                "instructions": (
                    "Persistent trading memory — read at startup to load past trades, "
                    "learnings, watchlist and risk events. Write new learnings after "
                    "each cycle and at end of day."
                )
            }
        ]
    )
    print(f"SUCCESS — Session created: {session.id}")

    # ── SEND TRIGGER MESSAGE ────────────────────────────────────────────────────
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
                    "Execute ALL steps in order. This is ONE 5-MINUTE CYCLE — not a "
                    "full day session. Run Steps 1–10 exactly once, place at most one "
                    "order if signal is strong, regenerate dashboard, push to GitHub, "
                    "then output CYCLE_COMPLETE with NEW_REFRESH_TOKEN so the next "
                    "cycle can authenticate. Do not loop internally."
                )
            }]
        }]
    )
    print("Kickoff message sent — streaming events...")

    # ── STREAM EVENTS ───────────────────────────────────────────────────────────
    new_token = None
    full_output = ""

    with client.beta.sessions.events.stream(session_id=session.id) as stream:
        for event in stream:
            event_type = getattr(event, 'type', str(event))
            print(f"[EVENT] {event_type}")

            if 'agent.message' in str(event_type):
                for block in getattr(event, 'content', []):
                    text = getattr(block, 'text', '')
                    if text:
                        full_output += text
                        print(f"[AGENT] {text[:300]}")

                        # Capture new Questrade refresh token from Step 10
                        match = re.search(r'NEW_REFRESH_TOKEN:\s*(\S+)', text)
                        if match and match.group(1) not in ('none', 'null', ''):
                            new_token = match.group(1)
                            print(f"✅ New refresh token captured ({len(new_token)} chars)")

            elif 'agent.tool_use' in str(event_type):
                print(f"[TOOL] {getattr(event, 'name', 'unknown')}")

            elif 'session.status_idle' in str(event_type):
                stop = getattr(event, 'stop_reason', {})
                if getattr(stop, 'type', '') != 'requires_action':
                    print("✅ Session idle — cycle complete")
                    break

            elif 'session.error' in str(event_type):
                print(f"[ERROR] {event}")
                break

    # ── ROTATE TOKEN FOR NEXT CYCLE ─────────────────────────────────────────────
    if new_token:
        print("Rotating QUESTRADE_REFRESH_TOKEN secret...")
        update_github_secret("QUESTRADE_REFRESH_TOKEN", new_token)
    else:
        print("⚠️  No new token found in agent output — next cycle reuses current token")
        print("    (Check agent output above for CYCLE_COMPLETE block)")

    print(f"✅ Done — {datetime.datetime.utcnow().isoformat()}Z")

except Exception as e:
    print(f"FATAL ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
