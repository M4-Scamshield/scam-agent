from copy import deepcopy

import pytest

from scamshield.graph import CallDemo
from scamshield.jev import fake_jev
from scamshield.roles import DemoRoles
from scamshield.state import DEMO_UTTERANCES, NO_TOOL_RESPONSE, VERIFY_RESPONSE, WARN_RESPONSE
from scamshield.tools import case_lookup


def test_three_utterances_checkpoint_and_call_isolation():
    lookups, decisions, events = [], [], []

    def lookup(**args):
        lookups.append(args)
        return case_lookup(**args)

    def jev(transcript, previous_phase, results):
        decisions.append((deepcopy(transcript), deepcopy(results)))
        return fake_jev(transcript, previous_phase, results)

    demo = CallDemo(DemoRoles(), lookup=lookup, jev=jev)
    for index, utterance in enumerate(DEMO_UTTERANCES):
        result = demo.run_turn("a", utterance, on_node=lambda name, update: events.append((name, update)))
        assert result["phase"] == ("OBSERVE", "SUSPECT", "WARN")[index]
        assert result["risk"] == (0.1, 0.5, 0.9)[index]
    assert result["response"] == WARN_RESPONSE
    assert [e[0] for e in events] == [
        "update_context", "detect_with_jev",
        "update_context", "detect_with_jev", "suspect_agent",
        "update_context", "detect_with_jev", "verify_agent", "tool_execution", "detect_with_jev", "warn",
    ]
    selected = events[7][1]
    assert selected == {"tool_request": {"tool": "case_lookup", "input": {"case_number": "2026-12345"}}}
    assert lookups == [{"case_number": "2026-12345"}]
    assert len(decisions) == 4
    assert decisions[2][0] == decisions[3][0] == list(DEMO_UTTERANCES)
    assert decisions[2][1] == []
    assert decisions[3][1][0]["result"]["lookup_status"] == "NOT_FOUND"
    state = demo.state("a")
    assert state["transcript"] == list(DEMO_UTTERANCES)
    assert len(state["verification_results"]) == 1
    assert state["utterance"] is None and state["tool_request"] is None
    assert state["verification_attempted"] is True

    # The selection is persisted before the execution node stores its result.
    snapshots = list(demo.graph.get_state_history({"configurable": {"thread_id": "a"}}))
    pending = next(s for s in snapshots if s.next == ("tool_execution",))
    assert pending.values["tool_request"] == selected["tool_request"]
    assert pending.values["verification_results"] == []
    assert pending.values["verification_attempted"] is False

    assert demo.run_turn("b", DEMO_UTTERANCES[0])["phase"] == "OBSERVE"
    assert demo.state("b")["transcript"] == [DEMO_UTTERANCES[0]]
    assert demo.state("b")["verification_results"] == []
    assert demo.state("a") == state
    demo.run_turn("a", "추가 발화")
    assert len(demo.state("a")["verification_results"]) == 1
    assert demo.state("a")["verification_attempted"] is False
    assert demo.state("a")["phase"] == "WARN"


@pytest.mark.parametrize("lookup_status, expected", [("NOT_FOUND", "WARN"), ("FOUND", "SUSPECT")])
def test_jev_uses_matching_latest_mock_result_and_context(lookup_status, expected):
    result = {"tool": "case_lookup", "input": {"case_number": "2026-12345"}, "status": "OK", "is_mock": True, "result": {"lookup_status": lookup_status}}
    assert fake_jev(list(DEMO_UTTERANCES), "VERIFY", [result])["phase"] == expected
    wrong_number = {**result, "input": {"case_number": "other"}}
    assert fake_jev(list(DEMO_UTTERANCES), "VERIFY", [wrong_number])["phase"] == "VERIFY"
    assert fake_jev([DEMO_UTTERANCES[2]], "OBSERVE", [result])["phase"] == "OBSERVE"
    for failed_status in ("ERROR", "TIMEOUT"):
        failure = {**result, "status": failed_status}
        assert fake_jev(list(DEMO_UTTERANCES), "VERIFY", [result, failure])["phase"] == "VERIFY"
    assert fake_jev(list(DEMO_UTTERANCES), "VERIFY", [{**result, "is_mock": False}])["phase"] == "VERIFY"


def test_still_verify_ends_without_second_tool_and_next_turn_can_verify():
    calls, judgments = [], []

    def jev(transcript, previous_phase, results):
        judgments.append(len(results))
        return {"phase": "VERIFY", "risk": 0.7}

    def lookup(**args):
        calls.append(args)
        raise RuntimeError("lookup failed")

    demo = CallDemo(DemoRoles(), jev=jev, lookup=lookup)
    result = demo.run_turn("a", DEMO_UTTERANCES[2])
    assert result["phase"] == "VERIFY"
    assert result["response"] == VERIFY_RESPONSE
    assert judgments == [0, 1] and len(calls) == 1
    assert result["verification_results"][0]["status"] == "ERROR"
    demo.run_turn("a", DEMO_UTTERANCES[2])
    assert judgments == [0, 1, 1, 2] and len(calls) == 2
    assert len(demo.state("a")["transcript"]) == 2
    assert len(demo.state("a")["verification_results"]) == 2


def test_no_request_has_no_execution_or_rejudgment():
    demo = CallDemo(DemoRoles(), jev=lambda *args: {"phase": "VERIFY", "risk": 0.7})
    events = []
    result = demo.run_turn("a", "사건번호를 아직 모릅니다.", on_node=lambda name, _: events.append(name))
    assert events == ["update_context", "detect_with_jev", "verify_agent"]
    assert result["response"] == NO_TOOL_RESPONSE
    assert result["verification_results"] == []


def test_invalid_input_does_not_mutate_state():
    demo = CallDemo(DemoRoles())
    demo.run_turn("a", DEMO_UTTERANCES[0])
    before = demo.state("a")
    assert demo.run_turn("a", "  ")["error"]["stage"] == "input"
    assert demo.run_turn("", "hello")["callId"] is None
    assert demo.state("a") == before


@pytest.mark.parametrize("decision", [
    {"phase": "VERIFY", "risk": 0.5},
    {"phase": "UNKNOWN", "risk": 0.7},
    {"phase": "WARN", "risk": float("nan")},
])
def test_invalid_jev_decision_is_error_before_tool(decision):
    demo = CallDemo(DemoRoles(), jev=lambda *args: decision)
    assert demo.run_turn("a", DEMO_UTTERANCES[2])["error"]["stage"] == "jev"
    assert demo.state("a")["verification_results"] == []


def test_response_reset_and_original_utterance_preserved():
    demo = CallDemo(DemoRoles())
    utterance = "  같은 문장  "
    demo.run_turn("a", utterance)
    demo.run_turn("a", utterance)
    assert demo.state("a")["transcript"] == [utterance, utterance]
    assert demo.state("a")["response"] is None
