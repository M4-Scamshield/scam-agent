import argparse
import json
import sys
import time

from scamshield.graph import build_pipeline
from scamshield.state import DEMO_UTTERANCES, NewLine, PipelineError


def print_outcome(outcome) -> None:
    yes = [code for code, decision in outcome.states.items() if decision.verdict == "Yes"]
    print(f"  Jev Yes: {', '.join(yes) or '없음'}")
    for analysis in outcome.state_analyses:
        fixed = f" (보정: {', '.join(analysis.corrections)})" if analysis.corrections else ""
        print(f"  [{analysis.state}] {analysis.judgment}{fixed}: {analysis.reason}")
    print(f"  통화 상태: {outcome.status}  점수: {outcome.score}")
    if outcome.message:
        print("  대응: " + outcome.message)
    if outcome.reason:
        print("  이유: " + outcome.reason)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Jev 상태 감지 → 켜진 상태별 Haiku 판단")
    parser.add_argument("--offline", action="store_true", help="Jev·Haiku 모두 명시적인 대역 사용(API 검증 아님)")
    parser.add_argument("--auto", action="store_true", help="준비된 세 발화를 순차 실행")
    parser.add_argument("--text", help="STT 결과에 해당하는 텍스트 한 건 실행; --auto와 함께 사용 불가")
    args = parser.parse_args(argv)
    if args.text is not None and args.auto:
        parser.error("--text와 --auto는 함께 사용할 수 없습니다.")
    try:
        pipeline = build_pipeline(offline=args.offline)
    except PipelineError as exc:
        print(f"오류 [{exc.stage}/{exc.code}]: {exc.message}", file=sys.stderr)
        return 1
    except Exception:
        print("모델 연결 설정에 실패했습니다. 실행 환경을 확인하세요.", file=sys.stderr)
        return 1

    mode = "OFFLINE: Jev·Haiku 대역 (실제 API 호출 없음)" if args.offline else "LIVE: Jev 상태 감지 / 켜진 상태만 Haiku 판단"
    print(mode, flush=True)
    history: list[str] = []
    state = None
    utterances = (args.text,) if args.text is not None else DEMO_UTTERANCES
    for seq, prepared in enumerate(utterances, start=1):
        print(f"\n발화 {seq}/{len(utterances)}: {prepared}", flush=True)
        if args.auto or args.text is not None:
            utterance = prepared
        else:
            try:
                utterance = input("입력 (Enter = 위 발화): ") or prepared
            except (EOFError, KeyboardInterrupt):
                print("\n입력이 중단되었습니다.", file=sys.stderr)
                return 1
        if not utterance.strip():
            print("오류 [input/INVALID_INPUT]: 발화는 비어 있지 않은 문자열이어야 합니다.", file=sys.stderr)
            return 1
        # 화자 표시가 없으면 통화 상대의 말로 본다.
        text = utterance if utterance.startswith("[") else "[상대] " + utterance
        try:
            outcome = pipeline.analyze(history, [NewLine(seq=seq, text=text)], state, time.time())
        except PipelineError as exc:
            print(f"오류 [{exc.stage}/{exc.code}]: {exc.message}", file=sys.stderr)
            return 1
        print_outcome(outcome)
        print("  state: " + json.dumps(outcome.state, ensure_ascii=False), flush=True)
        history.append(text)
        state = outcome.state
    return 0
