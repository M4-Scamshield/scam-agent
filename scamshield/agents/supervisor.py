"""기존 통화 그래프 위의 Jev Supervisor. 저장은 호출자(서버)가 맡는다."""

from copy import deepcopy
from hashlib import sha256
import json
from math import isfinite

from langgraph.graph import END, START, StateGraph
from pydantic import TypeAdapter, ValidationError

from scamshield.agents.call_agent import CallPipeline, build_pipeline
from scamshield.agents.interfaces import Supervisor, URLAnalyst
from scamshield.state import (
    ChatMessage, ChatReceipt, JevDecision, NewLine, PipelineError,
    SupervisorInput, SupervisorMemory, SupervisorOutcome, SupervisorState, URLAnalysis,
)
from scamshield.agents.url_agent import OfflineURLAnalyst, extract_urls, failed_lookup, has_non_url_text

_CHAT = TypeAdapter(list[ChatMessage])
_LINES = TypeAdapter(list[NewLine])
_HISTORY = TypeAdapter(list[str])


def _fingerprint(message: dict) -> str:
    raw = json.dumps(message, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


class OfflineSupervisor:
    """명시적인 offline 대역. URL을 뺀 텍스트가 있으면 통화 분석도 요청한다."""

    def route_input(self, transcript: list[str], chat: list[dict], pending_urls: list[str]) -> dict:
        call = bool(transcript)
        for message in chat:
            # URL-only 입력은 URL agent만 호출한다. 일반 채팅은 기존 통화 agent로 보낸다.
            call = call or has_non_url_text(message["text"])
        return {
            key: {"verdict": "Yes" if hit else "No", "probability": 0.9 if hit else 0.1}
            for key, hit in (("call", call), ("url", bool(pending_urls)))
        }


def build_supervisor_graph(call_pipeline: CallPipeline, supervisor: Supervisor, url_analyst: URLAnalyst):
    def update_context(state: SupervisorState) -> dict:
        try:
            history = _HISTORY.validate_python(state["history"])
            new_lines = [line.model_dump() for line in _LINES.validate_python(state["new_lines"])]
            chat = [message.model_dump() for message in _CHAT.validate_python(state["chat"])]
            memory = SupervisorMemory.model_validate(state["memory"] or {}).model_dump(mode="json")
            now = float(state["now"])
            if not isfinite(now) or any(not line["text"].strip() for line in new_lines):
                raise ValueError("invalid input")
            unique = {}
            for message in chat:
                mid, fingerprint = message["id"], _fingerprint(message)
                previous = memory["chat_receipts"].get(mid)
                if (mid in unique and unique[mid] != message) or (previous and previous["fingerprint"] != fingerprint):
                    raise ValueError("message ID reused with different content")
                unique[mid] = message
                if previous is None:
                    memory["chat_receipts"][mid] = ChatReceipt(fingerprint=fingerprint).model_dump()
            chat = list(unique.values())
            call_chat = [message for message in chat if not memory["chat_receipts"][message["id"]]["call_done"]]
            seqs = [line["seq"] for line in new_lines] + [message["seq"] for message in call_chat]
            if len(set(seqs)) != len(seqs):
                raise ValueError("new input seq must be unique")
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise PipelineError("input", "INVALID_INPUT", "입력·state 형식 또는 채팅 ID·seq가 잘못되었습니다.") from exc
        chat_urls = {
            message["id"]: extract_urls(message["text"])
            for message in chat if not memory["chat_receipts"][message["id"]]["urls_done"]
        }
        pending = list(dict.fromkeys(url for urls in chat_urls.values() for url in urls if url not in memory["url_cache"]))
        return {
            "history": history, "new_lines": new_lines, "chat": chat, "memory": memory, "now": now,
            "call_chat": call_chat, "chat_urls": chat_urls, "pending_urls": pending,
            "routes": [], "call": None, "url_analyses": [], "appended_lines": [],
        }

    def supervise(state: SupervisorState) -> dict:
        if not state["new_lines"] and not state["call_chat"] and not state["pending_urls"]:
            return {"routes": []}
        try:
            raw = supervisor.route_input(
                [line["text"] for line in state["new_lines"]],
                deepcopy(state["call_chat"]), list(state["pending_urls"]),
            )
            decisions = {key: JevDecision.model_validate(raw[key]).model_dump() for key in ("call", "url")}
        except PipelineError:
            raise
        except (KeyError, TypeError, ValidationError) as exc:
            raise PipelineError("supervisor", "INVALID_OUTPUT", "Supervisor 라우팅 응답이 잘못되었습니다.") from exc
        except Exception as exc:
            raise PipelineError("supervisor", "CALL_FAILED", "Supervisor 호출에 실패했습니다.") from exc
        call = decisions["call"]["verdict"] == "Yes"
        url = decisions["url"]["verdict"] == "Yes"
        # 잘못된 모델 라우팅으로 새 입력을 조용히 버리지 않는다.
        plain_chat = any(not extract_urls(message["text"]) for message in state["call_chat"])
        if ((state["new_lines"] or plain_chat) and not call) or url != bool(state["pending_urls"]):
            raise PipelineError("supervisor", "INVALID_OUTPUT", "Supervisor가 필요한 입력 경로를 누락했습니다.")
        if call and not (state["new_lines"] or state["call_chat"]):
            raise PipelineError("supervisor", "INVALID_OUTPUT", "통화 분석할 새 입력이 없습니다.")
        return {"decisions": decisions, "routes": [name for name, hit in (("call", call), ("url", url)) if hit]}

    def analyze_call(state: SupervisorState) -> dict:
        lines = list(state["new_lines"]) + [
            {"seq": message["seq"], "text": "[사용자 입력] " + message["text"]}
            for message in state["call_chat"]
        ]
        lines.sort(key=lambda line: line["seq"])
        outcome = call_pipeline.analyze(state["history"], lines, state["memory"]["call_state"], state["now"])
        memory = deepcopy(state["memory"])
        memory["call_state"] = outcome.state
        return {"memory": memory, "call": outcome.model_dump(), "appended_lines": lines}

    def analyze_urls(state: SupervisorState) -> dict:
        memory = deepcopy(state["memory"])
        analyses = []
        for url in state["pending_urls"]:
            try:
                result = URLAnalysis.model_validate(url_analyst.analyze_url(url))
                if result.url != url:
                    raise ValueError("unexpected URL")
                # 도구 근거와 모델 판정의 일치를 강제한다.
                expected = {"flagged": "risky", "not_found": "unknown", "error": "error"}[result.tool.status]
                if result.judgment != expected:
                    raise ValueError("unverified judgment")
            except PipelineError:
                raise
            except Exception:
                result = URLAnalysis.model_validate(failed_lookup(url))
            item = result.model_dump()
            analyses.append(item)
            if result.judgment != "error":
                memory["url_cache"][url] = item
        return {"memory": memory, "url_analyses": analyses}

    def finalize(state: SupervisorState) -> dict:
        memory = deepcopy(state["memory"])
        for message in state["chat"]:
            receipt = memory["chat_receipts"][message["id"]]
            receipt["call_done"] = True  # 호출 성공 또는 Supervisor가 URL 전용으로 분류
            if message["id"] in state["chat_urls"]:
                receipt["urls_done"] = all(url in memory["url_cache"] for url in state["chat_urls"][message["id"]])
        # 새 채팅이 이미 조회한 주소를 담으면 결과를 재사용한다. 완료한 채팅 재전송에는 내보내지 않는다.
        results = {item["url"]: item for item in state["url_analyses"]}
        for urls in state["chat_urls"].values():
            for url in urls:
                if url in memory["url_cache"]:
                    results[url] = memory["url_cache"][url]
        return {"outcome": {
            "call": state["call"], "url_analyses": list(results.values()), "routes": state["routes"],
            "appended_lines": state["appended_lines"], "state": memory,
        }}

    builder = StateGraph(SupervisorState, input_schema=SupervisorInput)
    for name, node in (("update_context", update_context), ("supervisor", supervise), ("call_agent", analyze_call), ("url_agent", analyze_urls), ("finalize", finalize)):
        builder.add_node(name, node)
    builder.add_edge(START, "update_context")
    builder.add_edge("update_context", "supervisor")
    builder.add_conditional_edges("supervisor", lambda state: "call" if "call" in state["routes"] else "url" if "url" in state["routes"] else "done", {"call": "call_agent", "url": "url_agent", "done": "finalize"})
    builder.add_conditional_edges("call_agent", lambda state: "url" if "url" in state["routes"] else "done", {"url": "url_agent", "done": "finalize"})
    builder.add_edge("url_agent", "finalize")
    builder.add_edge("finalize", END)
    return builder.compile()


class SupervisorPipeline:
    def __init__(self, call_pipeline: CallPipeline, supervisor: Supervisor, url_analyst: URLAnalyst):
        self.graph = build_supervisor_graph(call_pipeline, supervisor, url_analyst)

    def analyze(self, history: list[str], new_lines: list[NewLine], state: dict | None, now: float, *, chat: list[ChatMessage] | None = None) -> SupervisorOutcome:
        result = self.graph.invoke({"history": history, "new_lines": new_lines, "chat": [] if chat is None else chat, "memory": state, "now": now})
        return SupervisorOutcome.model_validate(result["outcome"])


def build_supervisor_pipeline(offline: bool = False) -> SupervisorPipeline:
    call = build_pipeline(offline=offline)
    if offline:
        return SupervisorPipeline(call, OfflineSupervisor(), OfflineURLAnalyst())
    from scamshield.agents.jev_agent import JevClient
    from scamshield.agents.url_agent import HaikuURLAnalyst

    return SupervisorPipeline(call, JevClient.from_env(), HaikuURLAnalyst.from_env())
