import argparse
import json
import sys
from uuid import uuid4

from scamshield.graph import CallPipeline
from scamshield.interfaces import OfflineAnalyst, OfflineDetector
from scamshield.state import DEMO_UTTERANCES, PipelineError


def print_node(name: str, update: dict) -> None:
    print(f"  [{name}]", flush=True)
    if update.get("jev_decision"):
        decision = update["jev_decision"]
        print(f"    verdict={decision['verdict']} probability(Yes)={decision['probability']}")
    if update.get("analysis"):
        print("    분석: " + update["analysis"]["reason"])
        print("    대응: " + update["analysis"]["response"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Jev 탐지 → Yes일 때 Gemini 분석·대응하는 2AS")
    parser.add_argument("--offline", action="store_true", help="두 모델 모두 명시적인 대역 사용(API 검증 아님)")
    parser.add_argument("--auto", action="store_true", help="준비된 세 발화를 순차 실행")
    parser.add_argument("--text", help="STT 결과에 해당하는 텍스트 한 건 실행; --auto와 함께 사용 불가")
    args = parser.parse_args(argv)
    if args.text is not None and args.auto:
        parser.error("--text와 --auto는 함께 사용할 수 없습니다.")
    try:
        if args.offline:
            pipeline = CallPipeline(OfflineDetector(), OfflineAnalyst())
            mode = "OFFLINE: Jev·Gemini 대역 (실제 API 호출 없음)"
        else:
            from scamshield.gemini import GeminiAnalyst
            from scamshield.jev import JevClient

            pipeline = CallPipeline(JevClient.from_env(), GeminiAnalyst())
            mode = "LIVE: Jev 탐지 / Yes일 때만 Gemini 분석·대응"
    except PipelineError as exc:
        print(f"오류 [{exc.stage}/{exc.code}]: {exc.message}", file=sys.stderr)
        return 1
    except Exception:
        print("모델 연결 설정에 실패했습니다. 실행 환경을 확인하세요.", file=sys.stderr)
        return 1

    call_id = str(uuid4())
    print(f"{mode}\ncallId={call_id}", flush=True)
    utterances = (args.text,) if args.text is not None else DEMO_UTTERANCES
    for index, prepared in enumerate(utterances, start=1):
        print(f"\n발화 {index}/{len(utterances)}: {prepared}", flush=True)
        if args.auto or args.text is not None:
            utterance = prepared
        else:
            try:
                utterance = input("입력 (Enter = 위 발화): ") or prepared
            except (EOFError, KeyboardInterrupt):
                print("\n입력이 중단되었습니다.", file=sys.stderr)
                return 1
        result = pipeline.run_turn(call_id, utterance, on_node=print_node)
        print("  결과: " + json.dumps(result, ensure_ascii=False), flush=True)
        if "error" in result:
            print("실행을 중단합니다. 새 callId로 다시 시작하세요.", file=sys.stderr)
            return 1
        print(f"  통화 누적: 대화 {len(pipeline.state(call_id)['transcript'])}개")
    return 0
