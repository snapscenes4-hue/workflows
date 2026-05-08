# Autonomous Trading Bot

Runs daily at NYSE open (9:30 AM ET) via GitHub Actions.
Paper trades for 5 days, then auto-switches to live Questrade trading.

## Agent Details
- Agent ID: agt_011CaqNdUSAnH7rBgBGkXR4z
- Environment ID: env_018fWQY1wVF6FdfscF3RSxLT
- Broker: Questrade (Account: 53826201)

## Setup
1. Add `ANTHROPIC_API_KEY` to GitHub Secrets
2. Push these files to main branch
3. GitHub Actions triggers automatically every weekday at 9:30 AM ET

## Daily Logs (written by agent)
- Trade cycle logs → /workspace/trading/logs/
- Strategy learnings → /workspace/trading/learnings/
- Paper portfolio → /workspace/trading/paper/paper_portfolio.json
- Config (paper/live mode) → /workspace/trading/config.json
