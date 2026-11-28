import argparse
import json
import sys
import time

from scamshield.graph import build_pipeline
from scamshield.state import DEMO_UTTERANCES, NewLine, PipelineError
from scamshield.agents.supervisor import build_supervisor_pipeline


def print_outcome(outcome) -> None:
    if outcome.analysis_status == "failed":
        print("  분석 실패: 재시도를 완료했거나 복구할 수 없는 오류가 발생했습니다.")
    yes = [code for code, decision in outcome.states.items() if decision.verdict == "Yes"]
    print(f"  Jev Yes: {', '.join(yes) or '없음'}")
    for analysis in outcome.state_analyses:
        fixed = f" (보정: {', '.join(analysis.corrections)})" if analysis.corrections else ""
        print(f"  [{analysis.state}] {analysis.judgment}{fixed}: {analysis.reason}")
    if outcome.status is not None:
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
    parser.add_argument("--supervisor", action="store_true", help="Jev Supervisor를 거쳐 기존 통화 그래프 실행")
    parser.add_argument("--chat", action="append", help="새 채팅 한 건; 여러 번 지정 가능. Supervisor 사용")
    args = parser.parse_args(argv)
    if args.text is not None and args.auto:
        parser.error("--text와 --auto는 함께 사용할 수 없습니다.")
    if args.chat is not None and args.auto:
        parser.error("--chat과 --auto는 함께 사용할 수 없습니다.")
    use_supervisor = args.supervisor or args.chat is not None
    try:
        pipeline = (build_supervisor_pipeline if use_supervisor else build_pipeline)(offline=args.offline)
    except PipelineError as exc:
        print(f"오류 [{exc.stage}/{exc.code}]: {exc.message}", file=sys.stderr)
        return 1
    except Exception:
        print("모델 연결 설정에 실패했습니다. 실행 환경을 확인하세요.", file=sys.stderr)
        return 1

    mode = "OFFLINE: Jev·Haiku 대역 (실제 API 호출 없음)" if args.offline else "LIVE: Jev 상태 감지 / 켜진 상태만 Haiku 판단"
    if use_supervisor:
        mode += " / Supervisor 라우팅 / URL 검색은 Mock"
    print(mode, flush=True)
    history: list[str] = []
    state = None
    failed = False
    def progress(event):
        if event.status == "analyzing":
            retry = f" / 재시도 {event.attempt - 1}/3" if event.attempt > 1 else ""
            print("  분석 중" + retry, flush=True)
    utterances = (args.text,) if args.text is not None else (None,) if args.chat is not None else DEMO_UTTERANCES
    for seq, prepared in enumerate(utterances, start=1):
        print(f"\n발화 {seq}/{len(utterances)}: {prepared}", flush=True)
        if prepared is None:
            utterance = ""
        elif args.auto or args.text is not None:
            utterance = prepared
        else:
            try:
                utterance = input("입력 (Enter = 위 발화): ") or prepared
            except (EOFError, KeyboardInterrupt):
                print("\n입력이 중단되었습니다.", file=sys.stderr)
                return 1
        if prepared is not None and not utterance.strip():
            print("오류 [input/INVALID_INPUT]: 발화는 비어 있지 않은 문자열이어야 합니다.", file=sys.stderr)
            return 1
        # 화자 표시가 없으면 통화 상대의 말로 본다.
        text = utterance if utterance.startswith("[") else "[상대] " + utterance
        try:
            lines = [NewLine(seq=seq, text=text)] if prepared is not None else []
            if use_supervisor:
                chat = [{"id": f"cli-chat-{i}", "seq": i + len(lines), "text": value} for i, value in enumerate(args.chat or [], 1)]
                outcome = pipeline.analyze(history, lines, state, time.time(), chat=chat, on_progress=progress)
            else:
                outcome = pipeline.analyze(history, lines, state, time.time(), on_progress=progress)
        except PipelineError as exc:
            print(f"오류 [{exc.stage}/{exc.code}]: {exc.message}", file=sys.stderr)
            return 1
        if use_supervisor:
            print("  Supervisor 경로: " + (", ".join(outcome.routes) or "없음"))
            if outcome.call:
                print_outcome(outcome.call)
            elif outcome.analysis_status == "failed":
                print("  분석 실패: 이전 구간의 분석이 완료되지 않았습니다.")
            for analysis in outcome.url_analyses:
                label = "Mock" if analysis.tool.is_mock else "조회"
                print(f"  URL({label}): {analysis.url} → {analysis.judgment}: {analysis.reason}")
        else:
            print_outcome(outcome)
        print("  state: " + json.dumps(outcome.state, ensure_ascii=False), flush=True)
        if use_supervisor:
            history.extend(line.text for line in outcome.appended_lines)
        else:
            history.append(text)
        state = outcome.state
        failed = failed or outcome.analysis_status == "failed"
    return 1 if failed else 0
