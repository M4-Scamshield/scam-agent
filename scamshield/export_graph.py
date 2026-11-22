"""Export the compiled graph without constructing clients or invoking models."""

import argparse
from pathlib import Path

from langchain_core.runnables.graph import Graph

from scamshield.graph import build_supervisor_graph, CallPipeline
from scamshield.agents.interfaces import OfflineAnalyst, OfflineDetector
from scamshield.agents.supervisor import OfflineSupervisor
from scamshield.agents.url_agent import OfflineURLAnalyst


def build_diagram(*, supervisor: bool = False, compact: bool = False) -> Graph:
    """모델 호출 없이 실제 상·하위 컴파일 그래프를 시각화용으로 연결한다."""
    call = CallPipeline(OfflineDetector(), OfflineAnalyst())
    if not supervisor:
        return call.graph.get_graph()
    diagram = build_supervisor_graph(call, OfflineSupervisor(), OfflineURLAnalyst()).get_graph()
    if compact:
        return diagram

    child = call.graph.get_graph()
    # 하위 START/END를 빼고 기존 call_agent의 입출력 간선을 연결한다.
    child.trim_first_node()
    child.trim_last_node()
    child.nodes["detect_states"] = child.nodes["detect_states"].copy(name="detect_states · Jev")
    child.nodes["judge_states"] = child.nodes["judge_states"].copy(name="judge_states · analysis_agent · Haiku")
    incoming = [edge for edge in diagram.edges if edge.target == "call_agent"]
    outgoing = [edge for edge in diagram.edges if edge.source == "call_agent"]
    diagram.remove_node(diagram.nodes["call_agent"])
    first, last = diagram.extend(child, prefix="call_agent")
    if first is None or last is None:
        raise ValueError("통화 그래프의 입구·출구를 찾지 못했습니다.")
    for edge in incoming:
        diagram.add_edge(diagram.nodes[edge.source], first, edge.data, edge.conditional)
    for edge in outgoing:
        diagram.add_edge(last, diagram.nodes[edge.target], edge.data, edge.conditional)
    return diagram


def main() -> None:
    parser = argparse.ArgumentParser(description="컴파일된 상태별 판단 LangGraph를 Mermaid와 PNG로 출력")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--supervisor", action="store_true", help="Supervisor 그래프 출력")
    parser.add_argument("--compact", action="store_true", help="--supervisor에서 call_agent 내부를 접어서 출력")
    args = parser.parse_args()
    if args.compact and not args.supervisor:
        parser.error("--compact는 --supervisor와 함께 사용하세요.")
    if args.output is None:
        filename = "supervisor-compact-langgraph.png" if args.compact else "supervisor-langgraph.png" if args.supervisor else "scamshield-langgraph.png"
        args.output = Path("docs/architecture") / filename
    diagram = build_diagram(supervisor=args.supervisor, compact=args.compact)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    source = args.output.with_suffix(".mmd")
    source.write_text(diagram.draw_mermaid(), encoding="utf-8")
    # The renderer receives graph topology only; no keys or call data are used.
    png = diagram.draw_mermaid_png(max_retries=0)
    args.output.write_bytes(png)
    print(f"Mermaid: {source}\nPNG: {args.output}")


if __name__ == "__main__":
    main()
