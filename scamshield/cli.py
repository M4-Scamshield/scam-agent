import argparse
import json
import os
import sys
from uuid import uuid4

from scamshield.graph import CallDemo
from scamshield.roles import DemoRoles
from scamshield.state import DEMO_UTTERANCES, DemoError


def print_node(name: str, update: dict) -> None:
    print(f"  [{name}]", flush=True)
    if "phase" in update:
        print(f"    phase={update['phase']} risk={update['risk']}")
    if update.get("tool_request"):
        print("    Tool 선택: " + json.dumps(update["tool_request"], ensure_ascii=False))
    if name == "tool_execution":
        print("    Tool 결과: " + json.dumps(update["verification_results"][-1], ensure_ascii=False))
    if update.get("response"):
        print("    안내: " + update["response"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ScamShield 세 발화 순차 통화 데모")
    parser.add_argument("--offline", action="store_true", help="Gemini 대신 Agent 대역 사용(API 검증 아님)")
    parser.add_argument("--auto", action="store_true", help="준비된 세 발화를 입력 대기 없이 실행")
    args = parser.parse_args(argv)
    try:
        if args.offline:
            roles = DemoRoles()
            mode = "OFFLINE: Agent 대역, Gemini 호출 없음"
        else:
            from scamshield.gemini import DEFAULT_MODEL, GeminiRoles

            roles = GeminiRoles.from_env()
            mode = "Gemini: " + os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
    except DemoError as exc:
        print(f"오류 [{exc.stage}/{exc.code}]: {exc.message}", file=sys.stderr)
        return 1
    except Exception:
        print("Gemini 연결 설정에 실패했습니다. 모델명과 실행 환경을 확인하세요.", file=sys.stderr)
        return 1

    call_id = str(uuid4())
    demo = CallDemo(roles)
    print(f"{mode}\nFake Jev / Mock case_lookup 데모\ncallId={call_id}", flush=True)
    for index, prepared in enumerate(DEMO_UTTERANCES, start=1):
        print(f"\n발화 {index}/3: {prepared}", flush=True)
        if args.auto:
            utterance = prepared
        else:
            try:
                utterance = input("입력 (Enter = 위 발화): ") or prepared
            except (EOFError, KeyboardInterrupt):
                print("\n입력이 중단되었습니다. 새 실행으로 처음부터 시작하세요.", file=sys.stderr)
                return 1
        result = demo.run_turn(call_id, utterance, on_node=print_node)
        print("  결과: " + json.dumps(result, ensure_ascii=False), flush=True)
        if "error" in result:
            print("시나리오를 중단합니다. 명령을 다시 실행하면 새 callId로 시작합니다.", file=sys.stderr)
            return 1
        state = demo.state(call_id)
        print(f"  통화 누적: 대화 {len(state['transcript'])}개 / 조회 {len(state['verification_results'])}개")
    return 0
