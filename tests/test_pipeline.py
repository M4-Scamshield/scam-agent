"""Graph 전체 시나리오를 CLI에서 직접 확인하는 대화형 점검 스크립트.

사용자가 STT 텍스트(보이스피싱 데이터)를 한 줄씩 입력하면 같은 통화로 누적하며,
Graph의 각 노드가 실행될 때마다 현재 노드 단계·Jev 응답·LLM 응답·State 상태를
출력한다. pytest 자동 수집 대상이 아니라(테스트 함수가 없다) 사람이 직접 실행해
노드별 흐름을 눈으로 확인하는 용도다.

실행:
  # 실제 API 없이 명시적 대역으로 흐름만 확인
  python -X utf8 -m tests.test_pipeline --offline

  # 실제 Jev·Gemini 호출(.env의 키 필요)
  uv run --locked --env-file .env python -X utf8 -m tests.test_pipeline

그래프가 끝나면 다시 발화를 입력받으며, '종료'(또는 exit/quit)를 넣거나
Ctrl+C/Ctrl+D를 누르면 종료한다. 빈 줄은 종료가 아니라 재입력이다.
"""

import argparse
import json
import sys
from copy import deepcopy
from uuid import uuid4

from scamshield.graph import CallPipeline
from scamshield.interfaces import OfflineAnalyst, OfflineDetector
from scamshield.state import PipelineError

# 노드 이름 → 사람이 읽을 단계 설명. Graph.build_graph의 노드와 1:1로 맞춘다.
NODE_LABELS = {
    "update_context": "입력 반영 · 대화 기록(transcript) 갱신",
    "detect_with_jev": "Jev 탐지 · Yes/No와 P(Yes) 판단",
    "respond_with_llm": "Gemini 분석·대응 (Yes 경로에서만 실행)",
}

RULE = "─" * 68


def _dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


class NodeTracer:
    """스트리밍되는 노드별 update를 누적 State로 재구성하며 CLI에 출력한다.

    Graph는 노드마다 바뀐 키만 update로 내보낸다. 같은 통화의 State는 이전
    상태 위에 각 update를 덮어쓰며 재구성되므로, 노드가 실행될 때마다 그
    시점의 전체 State와 이번 노드가 갱신한 항목을 함께 보여줄 수 있다.
    """

    def __init__(self):
        self.step = 0
        self.state: dict = {}

    def __call__(self, name: str, update: dict) -> None:
        self.step += 1
        self.state.update(update)
        label = NODE_LABELS.get(name, "(알 수 없는 노드)")

        print(RULE)
        print(f"▶ STEP {self.step} · 현재 노드: {name}")
        print(f"             {label}")
        print(RULE)

        # [JEV 응답] 현재 State의 판단값. detect_with_jev 노드에서 채워진다.
        changed_jev = "jev_decision" in update
        decision = self.state.get("jev_decision")
        print("[JEV 응답]" + ("  ← 이 노드에서 갱신됨" if changed_jev else ""))
        if decision:
            print(f"    verdict       : {decision['verdict']}")
            print(f"    probability   : {decision['probability']}  (P(보이스피싱=Yes))")
        else:
            print("    (아직 판단 없음)")

        # [LLM 응답] Yes 경로에서 respond_with_llm 노드가 채운다. No면 None 유지.
        changed_llm = "analysis" in update
        analysis = self.state.get("analysis")
        print("[LLM 응답]" + ("  ← 이 노드에서 갱신됨" if changed_llm else ""))
        if analysis:
            verdict = "피싱(True)" if analysis["is_phishing"] else "오탐/피싱 아님(False)"
            print(f"    재판단(is_phishing): {verdict}")
            print(f"    분석(reason)  : {analysis['reason']}")
            if analysis["response"]:
                print(f"    대응(response): {analysis['response']}")
            else:
                print("    대응(response): None (오탐 · 대응 없이 다음 발화 대기)")
        else:
            print("    (없음 · No 경로이거나 아직 분석 전)")

        # [STATE 상태] 이 노드 실행 직후의 전체 State 스냅샷.
        print("[STATE 상태]")
        for line in _dump(self.state).splitlines():
            print("    " + line)
        print()


def _build_pipeline(offline: bool) -> tuple[CallPipeline, str]:
    if offline:
        return CallPipeline(OfflineDetector(), OfflineAnalyst()), "OFFLINE 대역 (실제 API 호출 없음)"
    from scamshield.gemini import GeminiAnalyst
    from scamshield.jev import JevClient

    return CallPipeline(JevClient.from_env(), GeminiAnalyst()), "LIVE (실제 Jev·Gemini 호출)"


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Graph 전체 시나리오를 노드별로 확인하는 대화형 CLI")
    parser.add_argument("--offline", action="store_true", help="두 모델 모두 명시적 대역 사용 (API 검증 아님)")
    parser.add_argument("--call-id", help="재사용할 callId (기본값: 새 UUID)")
    args = parser.parse_args(argv)

    try:
        pipeline, mode = _build_pipeline(args.offline)
    except PipelineError as exc:
        print(f"오류 [{exc.stage}/{exc.code}]: {exc.message}", file=sys.stderr)
        return 1
    except Exception:
        print("모델 연결 설정에 실패했습니다. 실행 환경을 확인하세요.", file=sys.stderr)
        return 1

    call_id = args.call_id or str(uuid4())
    tracer = NodeTracer()

    print(f"모드: {mode}")
    print(f"callId: {call_id}")
    print("보이스피싱 데이터(STT 텍스트)를 한 줄씩 입력하세요. '종료'를 입력하면 끝납니다.")

    turn = 0
    while True:
        try:
            utterance = input("\n발화 입력 ('종료' 입력 시 종료) > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n입력이 중단되었습니다.")
            break
        if utterance in {"종료", "exit", "quit"}:
            print("종료합니다.")
            break
        if not utterance:
            # 빈 줄은 종료가 아니라 재입력. 그래프가 끝나면 계속 다음 발화를 받는다.
            print("빈 입력입니다. 발화를 입력하거나 '종료'로 끝내세요.")
            continue

        turn += 1
        print(f"\n╔═ 턴 {turn} · 입력: {utterance}")

        result = pipeline.run_turn(call_id, utterance, on_node=tracer)

        print(RULE)
        if "error" in result:
            error = result["error"]
            print(f"✖ 실행 오류 [{error['stage']}/{error['code']}]: {error['message']}")
            print("  중단된 통화는 이어서 실행할 수 없습니다. 새 callId로 다시 시작하세요.")
            print(f"  턴 결과: {_dump(result)}")
            break

        print("✔ 턴 결과:")
        for line in _dump(result).splitlines():
            print("    " + line)
        transcript = pipeline.state(call_id).get("transcript", [])
        print(f"  통화 누적: 대화 {len(transcript)}개")

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
