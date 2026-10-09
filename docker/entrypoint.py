"""Initialize an empty persistent workspace; never replace user configuration."""
import os
from pathlib import Path
import shutil
import sys

from instagram_ai_agent.core.config import NicheConfig, load_env

args = sys.argv[1:]
load_env()
if args and args[0] == "dashboard":
    if not os.environ.get("DASH_USER") or not os.environ.get("DASH_PASS"):
        raise SystemExit("Set DASH_USER and DASH_PASS before exposing the dashboard.")
    if not Path("niche.yaml").exists():
        import yaml
        config = NicheConfig(
            niche="Setup required", sub_topics=["Configure your content theme"],
            target_audience="Not configured yet",
            voice={"tone": ["clear"], "persona": "Pending account and content configuration."},
            aesthetic={"palette": ["#000000", "#ffffff"]},
            hashtags={"core": ["setup", "required", "placeholder"]}, safety={"require_review": True},
        )
        Path("niche.yaml").write_text(yaml.safe_dump(config.model_dump(mode="json")))
        Path(".setup-required").touch()
    for source in Path("/opt/seed-data").rglob("*"):
        target = Path("data") / source.relative_to("/opt/seed-data")
        if source.is_file() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
if args and args[0] == "run":
    if Path(".setup-required").exists() or not Path("niche.yaml").exists():
        raise SystemExit("Complete ig-agent setup, then remove /workspace/.setup-required before starting the worker.")
os.execvp("ig-agent", ["ig-agent", *args])
