import logging
import os
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from math import floor, isfinite

from langgraph.graph import END, START, StateGraph
from pydantic import TypeAdapter, ValidationError

from scamshield.agents.interfaces import Analyst, Detector, OfflineAnalyst, OfflineDetector
from scamshield.agents.jev_agent import CONTEXT_LINES
from scamshield.context import prepare_context, validate_evidence
from scamshield.state import (
    AgentMemory,
    AgentState,
    AnalysisOutcome,
    AnalyzeInput,
    JevDecision,
    NewLine,
    PipelineError,
    StateJudgment,
)
from scamshield.tactics import ABSOLUTE_STATES, CORE, HALF_LIFE_S, POINTS, PRIORITY, STATES

logger = logging.getLogger("scamshield")

FALLBACK_MESSAGE = "사기 수법과 맞는 요구가 있습니다. 송금·정보 제공·앱 설치를 멈추고, 통화를 끊은 뒤 기관 대표번호로 직접 확인하세요."

_NEW_LINES = TypeAdapter(list[NewLine])


def state_points(handled: dict, now: float) -> dict[str, float]:
    """상태별 점수 칸. risky는 고정, uncertain은 1분마다 절반(5 미만은 0), within_normal은 0."""
    points = {}
    for code, item in handled.items():
        risky, uncertain = POINTS[code]
        if item["judgment"] == "risky":
            points[code] = risky
        elif item["judgment"] == "uncertain":
            value = uncertain * 0.5 ** floor(max(0.0, now - item["judged_at"]) / HALF_LIFE_S)
            points[code] = value if value >= 5 else 0
        else:
            points[code] = 0
    return points


def _merge(old: dict, new: dict) -> dict:
    return {
        "probability": new["probability"],
        "seqs": old.get("seqs", []) + new["seqs"],
        "lines": old.get("lines", []) + new["lines"],
    }


def route(states: dict, memory: dict, seqs: list[int], lines: list[int]) -> dict:
    """이번에 Haiku를 부를 상태 {code: {probability, seqs, lines}}. memory의 seen·held를 고친다.
    seqs는 BE 줄 번호(근거), lines는 대화상 줄 번호(Haiku에게 감지된 대사를 가리킴)다."""
    yes = [code for code in PRIORITY if states[code]["verdict"] == "Yes"]
    handled = memory["handled"]
    candidates = {
        code: {"probability": states[code]["probability"], "seqs": list(seqs), "lines": list(lines)}
        for code in yes
        if handled.get(code, {}).get("judgment") != "risky"
    }
    core_seen = any(code in CORE for code in memory["seen"])
    memory["seen"] = [code for code in PRIORITY if code in memory["seen"] or code in yes]
    if core_seen:
        return candidates
    held = memory["held"]
    if not any(code in CORE for code in yes):
        for code, item in candidates.items():
            held[code] = _merge(held.get(code, {}), item)
        return {}
    todo = {code: dict(item) for code, item in held.items()}
    for code, item in candidates.items():
        todo[code] = _merge(todo.get(code, {}), item)
    memory["held"] = {}
    return {code: todo[code] for code in PRIORITY if code in todo}


def build_graph(detector: Detector, analyst: Analyst):
    def update_context(state: AgentState) -> dict:
        try:
            new_lines = [line.model_dump() for line in _NEW_LINES.validate_python(state["new_lines"])]
            memory = AgentMemory.model_validate(state["memory"] or {}).model_dump(mode="json")
            history, line_seqs = prepare_context(state["history"], new_lines, memory)
            now = float(state["now"])
            if not isfinite(now):
                raise ValueError("invalid time")
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise PipelineError("input", "INVALID_INPUT", "history·new_lines·state·now 형식이 잘못되었습니다.") from exc
        if not new_lines:
            raise PipelineError("input", "INVALID_INPUT", "new_lines는 1줄 이상이어야 합니다.")
        return {
            "history": history,
            "new_lines": new_lines,
            "memory": memory,
            "now": now,
            "lines": history + [line["text"] for line in new_lines],
            "line_seqs": line_seqs,
            "state_analyses": [],
        }

    def detect_states(state: AgentState) -> dict:
        n_new = len(state["new_lines"])
        window = state["lines"][-(CONTEXT_LINES + n_new):]
        try:
            raw = detector.detect_states(list(window), n_new)
        except PipelineError:
            raise
        except Exception as exc:
            raise PipelineError("jev", "CALL_FAILED", "Jev 판단 호출에 실패했습니다.") from exc
        try:
            states = {code: JevDecision.model_validate(raw[code]).model_dump() for code in STATES}
        except (KeyError, TypeError, ValidationError) as exc:
            raise PipelineError("jev", "INVALID_OUTPUT", "Jev 상태별 판단 형식이 잘못되었습니다.") from exc
        memory = deepcopy(state["memory"])
        first = len(state["history"]) + 1
        positions = list(range(first, first + n_new))
        todo = route(states, memory, [line["seq"] for line in state["new_lines"]], positions)
        return {"states": states, "memory": memory, "todo": todo}

    def judge_states(state: AgentState) -> dict:
        memory = deepcopy(state["memory"])
        handled = memory["handled"]
        requests = {
            code: {
                "state": code,
                "probability": item["probability"],
                "lines": list(state["lines"]),
                "line_seqs": list(state["line_seqs"]),
                # 예전 state의 보류 항목에는 lines가 없을 수 있다. 그때는 이번 새 줄을 가리킨다.
                "detected_lines": item.get("lines") or list(range(len(state["history"]) + 1, len(state["lines"]) + 1)),
                "call_context": dict(memory["call_context"]),
                "previous": deepcopy(handled.get(code)),
            }
            for code, item in state["todo"].items()
        }
        with ThreadPoolExecutor(max_workers=len(requests)) as pool:
            futures = {code: pool.submit(analyst.judge, request) for code, request in requests.items()}
            results = {}
            for code in PRIORITY:
                if code not in futures:
                    continue
                try:
                    results[code] = validate_evidence(StateJudgment.model_validate(futures[code].result()), requests[code])
                except PipelineError:
                    raise
                except ValidationError:
                    logger.warning("state %s skipped: INVALID_OUTPUT", code)
                except Exception as exc:
                    logger.warning("state %s skipped: %s", code, getattr(exc, "code", type(exc).__name__))

        analyses = []
        for code, result in results.items():
            judgment, corrections = result.judgment, []
            evidence_seqs = [state["line_seqs"][line - 1] for line in result.evidence_lines]
            context_seqs = [state["line_seqs"][line - 1] for line in result.context_lines]
            if code in ABSOLUTE_STATES and result.absolute_line and judgment != "risky":
                judgment = "risky"
                corrections.append("absolute_line")
            if any(tool.status == "flagged" for tool in result.tools) and judgment != "risky":
                judgment = "risky"
                corrections.append("tool_flagged")
            for tool in result.tools:
                if tool.status == "error":
                    logger.warning("state %s tool %s: error", code, tool.name)
            analyses.append({
                "state": code,
                "judgment": judgment,
                "model_judgment": result.judgment,
                "corrections": corrections,
                "reason": result.reason,
                "response": result.response,
                "actions": result.actions,
                "tools": [tool.model_dump() for tool in result.tools],
                "evidence_seqs": evidence_seqs,
                "context_seqs": context_seqs,
            })
            handled[code] = {
                "judgment": judgment,
                "reason": result.reason,
                "response": result.response,
                "actions": result.actions,
                "evidence_seqs": evidence_seqs,
                "context_seqs": context_seqs,
                "judged_at": state["now"],
            }
            for key, value in result.call_context.model_dump().items():
                if value:
                    memory["call_context"][key] = value
        return {"memory": memory, "state_analyses": analyses}

    def finalize(state: AgentState) -> dict:
        memory = state["memory"]
        handled = memory["handled"]
        points = state_points(handled, state["now"])
        risky = [code for code in PRIORITY if handled.get(code, {}).get("judgment") == "risky"]
        watch = [code for code in PRIORITY if handled.get(code, {}).get("judgment") == "uncertain" and points[code] > 0]
        status = "위험" if risky else "주의" if watch else "정상"
        # 사용자 화면의 근거는 가장 중요한 상태 하나의 이유만 쓴다(여럿을 이으면 길고, uncertain의 "근거 부족"이 섞인다).
        # 위험이면 가장 최근에 risky가 된 상태(같은 때면 우선순위)를 쓴다. 위험 뒤 갱신 경고에 새 근거가 보이게 한다.
        latest = max((handled[code]["judged_at"] for code in risky), default=None)
        top = ([code for code in risky if handled[code]["judged_at"] == latest] or watch or [None])[0]
        message = (handled[top]["response"] or FALLBACK_MESSAGE) if risky else None
        outcome = {
            "status": status,
            "score": min(100, round(sum(points.values()))),
            "message": message,
            "reason": (handled[top]["reason"] or None) if top else None,
            "evidence_seqs": sorted({seq for code in risky for seq in handled[code]["evidence_seqs"]}),
            "context_seqs": sorted({seq for code in risky for seq in handled[code]["context_seqs"]}),
            "states": state["states"],
            "state_analyses": state["state_analyses"],
            "state": memory,
        }
        return {"outcome": outcome}

    builder = StateGraph(AgentState, input_schema=AnalyzeInput)
    builder.add_node("update_context", update_context)
    builder.add_node("detect_states", detect_states)
    builder.add_node("judge_states", judge_states)
    builder.add_node("finalize", finalize)
    builder.add_edge(START, "update_context")
    builder.add_edge("update_context", "detect_states")
    builder.add_conditional_edges(
        "detect_states",
        lambda state: "judge" if state["todo"] else "skip",
        {"judge": "judge_states", "skip": "finalize"},
    )
    builder.add_edge("judge_states", "finalize")
    builder.add_edge("finalize", END)
    return builder.compile()


class CallPipeline:
    """Stateless: 통화 상태는 analyze 입력의 state로만 받고 출력의 state로 돌려준다."""

    def __init__(self, detector: Detector, analyst: Analyst):
        self.graph = build_graph(detector, analyst)

    def analyze(self, history: list[str | NewLine], new_lines: list[NewLine], state: dict | None, now: float) -> AnalysisOutcome:
        result = self.graph.invoke({"history": history, "new_lines": new_lines, "memory": state, "now": now})
        return AnalysisOutcome.model_validate(result["outcome"])


def build_pipeline(offline: bool = False) -> CallPipeline:
    if offline:
        return CallPipeline(OfflineDetector(), OfflineAnalyst())
    from scamshield.agents.analysis_agent import HaikuAnalyst
    from scamshield.agents.jev_agent import JevClient

    for name in ("TYPESAFE_API_KEY", "ANTHROPIC_API_KEY"):
        if not os.environ.get(name, "").strip():
            raise PipelineError("config", "config", f"{name} 환경변수가 필요합니다.")
    try:
        return CallPipeline(JevClient.from_env(), HaikuAnalyst.from_env())
    except PipelineError as exc:
        raise PipelineError("config", "config", exc.message) from exc
