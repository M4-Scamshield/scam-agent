"""Public entrypoint; implementations live in agents/."""

from scamshield.agents.call_agent import CallPipeline, FALLBACK_MESSAGE, build_graph, build_pipeline

__all__ = ["CallPipeline", "FALLBACK_MESSAGE", "build_graph", "build_pipeline"]
