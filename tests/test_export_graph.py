from scamshield.export_graph import build_diagram


def edges(diagram):
    return {(edge.source, edge.target, edge.data, edge.conditional) for edge in diagram.edges}


def test_expanded_diagram_shows_analysis_and_preserves_both_skip_paths():
    diagram = build_diagram(supervisor=True)
    assert "call_agent" not in diagram.nodes
    assert "analysis_agent" in diagram.nodes["call_agent:judge_states"].name
    assert "Jev" in diagram.nodes["call_agent:detect_states"].name
    assert {
        ("supervisor", "call_agent:update_context", "call", True),
        ("call_agent:detect_states", "call_agent:judge_states", "judge", True),
        ("call_agent:detect_states", "call_agent:finalize", "skip", True),
        ("call_agent:finalize", "url_agent", "url", True),
        ("call_agent:finalize", "finalize", "done", True),
        ("supervisor", "url_agent", "url", True),
        ("supervisor", "finalize", "done", True),
    } <= edges(diagram)
    assert all(edge.source in diagram.nodes and edge.target in diagram.nodes for edge in diagram.edges)
    assert "subgraph call_agent" in diagram.draw_mermaid()


def test_compact_and_call_only_views_remain_available_without_model_calls(monkeypatch):
    def unexpected_call(*args, **kwargs):
        raise AssertionError("export must not invoke models or tools")

    monkeypatch.setattr("scamshield.agents.interfaces.OfflineDetector.detect_states", unexpected_call)
    monkeypatch.setattr("scamshield.agents.supervisor.OfflineSupervisor.route_input", unexpected_call)
    monkeypatch.setattr("scamshield.agents.url_agent.OfflineURLAnalyst.analyze_url", unexpected_call)
    assert "call_agent" in build_diagram(supervisor=True, compact=True).nodes
    assert "call_agent:judge_states" in build_diagram(supervisor=True).nodes
    assert "judge_states" in build_diagram().nodes
