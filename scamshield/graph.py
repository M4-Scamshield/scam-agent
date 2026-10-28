from collections.abc import Callable
from copy import deepcopy

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from scamshield.interfaces import Analyst, Detector
from scamshield.state import JevDecision, LLMAnalysis, PipelineError, ScamState, TurnInput


def build_graph(detector: Detector, analyst: Analyst, *, checkpointer=None):
    def update_context(state: ScamState) -> dict:
        utterance = state.get("utterance")
        if not isinstance(utterance, str) or not utterance.strip():
            raise PipelineError("input", "INVALID_INPUT", "발화는 비어 있지 않은 문자열이어야 합니다.")
        return {
            "utterance": None,
            "transcript": state.get("transcript", []) + [utterance],
            "jev_decision": None,
            "analysis": None,
        }

    def detect_with_jev(state: ScamState) -> dict:
        try:
            raw = detector.detect(deepcopy(state["transcript"]))
        except PipelineError:
            raise
        except Exception as exc:
            raise PipelineError("jev", "CALL_FAILED", "Jev 판단 호출에 실패했습니다.") from exc
        try:
            return {"jev_decision": JevDecision.model_validate(raw).model_dump()}
        except ValidationError as exc:
            raise PipelineError("jev", "INVALID_OUTPUT", "Jev 판단 형식이 잘못되었습니다.") from exc

    def respond_with_llm(state: ScamState) -> dict:
        try:
            raw = analyst.analyze(deepcopy(state))
        except PipelineError:
            raise
        except Exception as exc:
            raise PipelineError("llm", "CALL_FAILED", "Gemini 분석·대응 생성에 실패했습니다.") from exc
        try:
            return {"analysis": LLMAnalysis.model_validate(raw).model_dump()}
        except ValidationError as exc:
            raise PipelineError("llm", "INVALID_OUTPUT", "Gemini 분석·대응 형식이 잘못되었습니다.") from exc

    builder = StateGraph(ScamState, input_schema=TurnInput)
    builder.add_node("update_context", update_context)
    builder.add_node("detect_with_jev", detect_with_jev)
    builder.add_node("respond_with_llm", respond_with_llm)
    builder.add_edge(START, "update_context")
    builder.add_edge("update_context", "detect_with_jev")
    builder.add_conditional_edges(
        "detect_with_jev",
        lambda state: state["jev_decision"]["verdict"],
        {"Yes": "respond_with_llm", "No": END},
    )
    builder.add_edge("respond_with_llm", END)
    return builder.compile(checkpointer=checkpointer if checkpointer is not None else InMemorySaver())


class CallPipeline:
    def __init__(self, detector: Detector, analyst: Analyst, *, checkpointer=None):
        self.graph = build_graph(detector, analyst, checkpointer=checkpointer)

    def state(self, call_id: str) -> ScamState:
        return deepcopy(self.graph.get_state({"configurable": {"thread_id": call_id}}).values)

    def run_turn(self, call_id: str, utterance: str, *, on_node: Callable | None = None) -> dict:
        result_id = call_id if isinstance(call_id, str) and call_id.strip() else None
        if result_id is None or not isinstance(utterance, str) or not utterance.strip():
            return {"callId": result_id, "error": PipelineError("input", "INVALID_INPUT", "callId와 발화는 비어 있지 않은 문자열이어야 합니다.").as_dict()}
        config = {"configurable": {"thread_id": call_id}}
        try:
            if self.graph.get_state(config).next:
                raise PipelineError("runtime", "EXECUTION_CONTRACT_VIOLATION", "중단된 통화입니다. 새 callId로 시작하세요.")
            for event in self.graph.stream(
                {"utterance": utterance}, config, stream_mode="updates", durability="sync"
            ):
                if on_node:
                    for name, update in event.items():
                        on_node(name, deepcopy(update))
            state = self.state(call_id)
        except PipelineError as exc:
            return {"callId": call_id, "error": exc.as_dict()}
        except Exception:
            return {"callId": call_id, "error": PipelineError("runtime", "CALL_FAILED", "Graph 실행 또는 checkpoint 처리에 실패했습니다.").as_dict()}
        return {"callId": call_id, "jev_decision": state["jev_decision"], "analysis": state["analysis"]}
