# Docker / Coolify

Build with `docker compose build`. Set DASH_USER and DASH_PASS in your shell
or Compose .env, then `docker compose up -d dashboard`. Dashboard: port 8186.
The image includes FFmpeg, Chromium and fonts and runs as UID 10001.
Persist the whole /workspace: SQLite, sessions, media, niche.yaml and .env.
The first start creates a clearly labeled placeholder config with review required.
No Instagram worker runs by default.

Complete interactive configuration with:

```
docker compose exec dashboard ig-agent setup --review --force
```

Connect Instagram using the upstream login instructions and configure a model
provider in /workspace/.env. Do not commit credentials. Once configured and ready
for Instagram activity, remove `/workspace/.setup-required` and run
`docker compose --profile worker up -d`. The worker may publish approved posts,
reply to comments and perform other account actions. Stop it with
`docker compose stop worker`.

For Coolify, create a custom Compose service using the dashboard service and
volume above. Replace build with a Git context pinned to your fork commit, e.g.
`build: {context: "https://github.com/OWNER/instagram-ai-agent.git#COMMIT"}`.
Configure DASH_USER/DASH_PASS as Coolify environment variables. Keep the dashboard
on your LAN or put it behind HTTPS before accessing it over an untrusted network.
The dashboard is a status/review UI; initial setup is done in the container terminal.

## LiteLLM / budgeted OpenRouter gateway

Set `OPENROUTER_BASE_URL` to your LiteLLM `/v1` endpoint and
`OPENROUTER_API_KEY` to a dedicated restricted virtual key, not the master key.
Register the permitted OpenRouter model names in LiteLLM. Store the real
OpenRouter credential only at the gateway. All text, JSON, tool-based structured
output, vision, and setup validation requests use this base URL; failures do not
fall back to the public OpenRouter endpoint.

Optional `OPENROUTER_TEXT_MODELS`, `OPENROUTER_JSON_MODELS`, and
`OPENROUTER_VISION_MODELS` select comma-separated fallback chains. Defaults are
unchanged when unset. LiteLLM must allow and route each listed model. Give both
containers these environment variables when enabling the worker.

Enforce dollar budgets in LiteLLM using one virtual key with simultaneous
`budget_limits` windows (for example `24h` at $1 and `30d` at $10). The agent's
`budget` section only limits Instagram actions, not dollars. Gateway accounting
can lag in-flight requests; these are spend-based stops, not prepaid reservations.
Separate media providers are outside the LLM gateway budget.
