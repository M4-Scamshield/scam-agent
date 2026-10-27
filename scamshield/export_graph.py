"""Export the compiled graph without constructing clients or invoking models."""

import argparse
from pathlib import Path

from scamshield.graph import build_graph
from scamshield.interfaces import OfflineAnalyst, OfflineDetector


def main() -> None:
    parser = argparse.ArgumentParser(description="컴파일된 2AS LangGraph를 Mermaid와 PNG로 출력")
    parser.add_argument("--output", type=Path, default=Path("docs/architecture/scamshield-langgraph.png"))
    args = parser.parse_args()
    diagram = build_graph(OfflineDetector(), OfflineAnalyst()).get_graph()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    source = args.output.with_suffix(".mmd")
    source.write_text(diagram.draw_mermaid(), encoding="utf-8")
    # The renderer receives graph topology only; no keys or call data are used.
    png = diagram.draw_mermaid_png(max_retries=0)
    args.output.write_bytes(png)
    print(f"Mermaid: {source}\nPNG: {args.output}")


if __name__ == "__main__":
    main()
