"""Convenience entry point for running the server directly with uvicorn."""
from debate.server.app import create_app

app = create_app(config_path="examples/config.yaml")
