"""Export the compiled graph without constructing clients or invoking models."""

import argparse
from pathlib import Path

from scamshield.graph import build_graph
from scamshield.agents.interfaces import OfflineAnalyst, OfflineDetector
from scamshield.agents.supervisor import build_supervisor_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="컴파일된 상태별 판단 LangGraph를 Mermaid와 PNG로 출력")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--supervisor", action="store_true", help="Supervisor 그래프 출력")
    args = parser.parse_args()
    if args.output is None:
        filename = "supervisor-langgraph.png" if args.supervisor else "scamshield-langgraph.png"
        args.output = Path("docs/architecture") / filename
    graph = build_supervisor_pipeline(offline=True).graph if args.supervisor else build_graph(OfflineDetector(), OfflineAnalyst())
    diagram = graph.get_graph()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    source = args.output.with_suffix(".mmd")
    source.write_text(diagram.draw_mermaid(), encoding="utf-8")
    # The renderer receives graph topology only; no keys or call data are used.
    png = diagram.draw_mermaid_png(max_retries=0)
    args.output.write_bytes(png)
    print(f"Mermaid: {source}\nPNG: {args.output}")


if __name__ == "__main__":
    main()
