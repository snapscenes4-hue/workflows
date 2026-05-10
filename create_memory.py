import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Create memory store
store = client.beta.memory_stores.create(
    name="trading-memory",
    description="Persistent trading memory — stores trading history, strategy learnings, watchlist, and risk events across all sessions."
)
print(f"✅ Memory Store ID: {store.id}")

# Seed with initial structure
memories = [
    ("/trading-history/README.md", "# Trading History\nAll trades recorded here by date."),
    ("/strategy-learnings/notes.md", "# Strategy Learnings\nWhat worked and what didn't."),
    ("/watchlist/stocks.md", "# Watchlist\nStocks being tracked with notes and price targets."),
    ("/risk-events/notes.md", "# Risk Events\nStocks that caused losses and patterns to avoid."),
]

for path, content in memories:
    client.beta.memory_stores.memories.create(store.id, path=path, content=content)
    print(f"✅ Created: {path}")

print(f"\n🎉 Memory Store ID: {store.id}")
print("Paste this ID back to the builder!")
