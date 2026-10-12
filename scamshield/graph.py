import re
from collections.abc import Callable
from copy import deepcopy
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from scamshield.jev import fake_jev
from scamshield.roles import Roles
from scamshield.state import (
    CaseLookupResult,
    DemoError,
    JevDecision,
    NO_TOOL_RESPONSE,
    ScamState,
    ToolRequest,
    TurnInput,
    VERIFY_RESPONSE,
    WARN_RESPONSE,
)
from scamshield.tools import case_lookup


def validate_request(request: dict, state: ScamState) -> dict:
    try:
        validated = ToolRequest.model_validate(request).model_dump()
    except ValidationError as exc:
        raise DemoError("verify_agent", "INVALID_OUTPUT", "조회 요청 형식이 잘못되었습니다.") from exc
    # Compare complete hyphenated demo numbers, not substrings of a number.
    case_numbers = {
        number
        for utterance in state["transcript"]
        for number in re.findall(r"[0-9]+(?:-[0-9]+)+", utterance)
    }
    if validated["input"]["case_number"] not in case_numbers:
        raise DemoError("verify_agent", "INVALID_OUTPUT", "대화에 제시된 전체 사건번호와 일치하지 않습니다.")
    return validated


def build_graph(
    roles: Roles,
    *,
    jev: Callable = fake_jev,
    lookup: Callable = case_lookup,
    checkpointer: InMemorySaver | None = None,
):
    def update_context(state: ScamState) -> dict:
        return {
            "utterance": None,
            "transcript": state.get("transcript", []) + [state["utterance"]],
            "phase": state.get("phase", "OBSERVE"),
            "risk": state.get("risk"),
            "verification_results": state.get("verification_results", []),
            "response": None,
            "tool_request": None,
            "verification_attempted": False,
        }

    def detect_with_jev(state: ScamState) -> dict:
        try:
            raw = jev(
                deepcopy(state["transcript"]),
                state["phase"],
                deepcopy(state["verification_results"]),
            )
        except Exception as exc:
            raise DemoError("jev", "CALL_FAILED", "Jev 판단 호출에 실패했습니다.") from exc
        try:
            decision = JevDecision.model_validate(raw)
        except ValidationError as exc:
            raise DemoError("jev", "INVALID_OUTPUT", "Jev 판단 형식이 잘못되었습니다.") from exc
        if state["phase"] == "WARN" and decision.phase != "WARN":
            raise DemoError("jev", "INVALID_TRANSITION", "WARN에서 하향할 수 없습니다.")
        if decision.phase == "VERIFY" and decision.risk < 0.6:
            raise DemoError("jev", "INVALID_TRANSITION", "VERIFY에는 risk >= 0.6이 필요합니다.")
        update = decision.model_dump()
        if decision.phase == "VERIFY" and state["verification_attempted"]:
            update["response"] = VERIFY_RESPONSE
        return update

    def suspect_agent(state: ScamState) -> dict:
        try:
            response = roles.suspect(deepcopy(state))
        except DemoError:
            raise
        except Exception as exc:
            raise DemoError("suspect_agent", "CALL_FAILED", "확인 안내 생성에 실패했습니다.") from exc
        if not isinstance(response, str) or not response.strip():
            raise DemoError("suspect_agent", "INVALID_OUTPUT", "확인 안내가 비어 있습니다.")
        return {"response": response}

    def verify_agent(state: ScamState) -> dict:
        try:
            request = roles.verify(deepcopy(state))
        except DemoError:
            raise
        except Exception as exc:
            raise DemoError("verify_agent", "CALL_FAILED", "조회 요청 선택에 실패했습니다.") from exc
        if request is None:
            return {"tool_request": None, "response": NO_TOOL_RESPONSE}
        return {"tool_request": validate_request(request, state)}

    def tool_execution(state: ScamState) -> dict:
        if state["verification_attempted"] or state["tool_request"] is None:
            raise DemoError("tool_execution", "EXECUTION_CONTRACT_VIOLATION", "조회 실행 한도 또는 요청 계약 위반입니다.")
        request = validate_request(state["tool_request"], state)
        status = "OK"
        try:
            raw = lookup(**request["input"])
        except Exception:
            status = "ERROR"
            result = {"code": "TOOL_EXECUTION_FAILED", "message": "Mock 조회 실행에 실패했습니다."}
        else:
            try:
                result = CaseLookupResult.model_validate(raw).model_dump()
            except ValidationError:
                status = "ERROR"
                result = {"code": "TOOL_RESULT_INVALID", "message": "Mock 조회 결과 형식이 잘못되었습니다."}
        verification = {**request, "status": status, "result": result, "is_mock": True}
        return {
            "verification_results": state["verification_results"] + [verification],
            "tool_request": None,
            "verification_attempted": True,
        }

    def route_decision(state: ScamState) -> str:
        if state["phase"] == "VERIFY":
            return END if state["verification_attempted"] else "verify_agent"
        return {"OBSERVE": END, "SUSPECT": "suspect_agent", "WARN": "warn"}[state["phase"]]

    builder = StateGraph(ScamState, input_schema=TurnInput)
    builder.add_node("update_context", update_context)
    builder.add_node("detect_with_jev", detect_with_jev)
    builder.add_node("suspect_agent", suspect_agent)
    builder.add_node("verify_agent", verify_agent)
    builder.add_node("tool_execution", tool_execution)
    builder.add_node("warn", lambda state: {"response": WARN_RESPONSE})
    builder.add_edge(START, "update_context")
    builder.add_edge("update_context", "detect_with_jev")
    builder.add_conditional_edges("detect_with_jev", route_decision)
    builder.add_conditional_edges(
        "verify_agent", lambda state: "tool_execution" if state["tool_request"] else END
    )
    builder.add_edge("tool_execution", "detect_with_jev")
    builder.add_edge("suspect_agent", END)
    builder.add_edge("warn", END)
    return builder.compile(checkpointer=checkpointer if checkpointer is not None else InMemorySaver())


class CallDemo:
    def __init__(self, roles: Roles, **graph_options: Any):
        self.graph = build_graph(roles, **graph_options)

    def state(self, call_id: str) -> ScamState:
        return deepcopy(self.graph.get_state({"configurable": {"thread_id": call_id}}).values)

    def run_turn(
        self,
        call_id: str,
        utterance: str,
        *,
        on_node: Callable[[str, dict], None] | None = None,
    ) -> dict:
        result_id = call_id if isinstance(call_id, str) and call_id.strip() else None
        if result_id is None or not isinstance(utterance, str) or not utterance.strip():
            return {"callId": result_id, "error": DemoError("input", "INVALID_INPUT", "callId와 발화는 비어 있지 않은 문자열이어야 합니다.").as_dict()}
        config = {"configurable": {"thread_id": call_id}}
        try:
            # Failed calls must restart with a new ID, never resume pending nodes.
            if self.graph.get_state(config).next:
                raise DemoError("runtime", "EXECUTION_CONTRACT_VIOLATION", "중단된 통화입니다. 새 callId로 처음부터 시작하세요.")
            for event in self.graph.stream(
                {"utterance": utterance}, config, stream_mode="updates", durability="sync"
            ):
                if on_node:
                    for name, update in event.items():
                        on_node(name, deepcopy(update))
            state = self.state(call_id)
        except DemoError as exc:
            return {"callId": call_id, "error": exc.as_dict()}
        except Exception:
            return {"callId": call_id, "error": DemoError("runtime", "CALL_FAILED", "Graph 실행 또는 checkpoint 처리에 실패했습니다.").as_dict()}
        return {
            "callId": call_id,
            "risk": state["risk"],
            "phase": state["phase"],
            "response": state["response"],
            "verification_results": state["verification_results"],
        }
