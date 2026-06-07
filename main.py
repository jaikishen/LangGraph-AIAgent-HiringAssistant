from __future__ import annotations
import sys
from pathlib import Path

SRC = Path(__file__).parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rich import print as rprint
from rich.rule import Rule

GRAPH_OUT = Path(__file__).parent / "graph_out"
GRAPH_OUT.mkdir(exist_ok=True)


def save_graph_assets(app) -> None:
    mmd = GRAPH_OUT / "graph.mmd"
    mmd.write_text(app.get_graph().draw_mermaid())
    rprint(f"[green]Wrote {mmd}[/green]")
    try:
        png = GRAPH_OUT / "graph.png"
        png.write_bytes(app.get_graph().draw_mermaid_png())
        rprint(f"[green]Wrote {png}[/green]")
    except Exception as exc:
        rprint(f"[yellow]Skipped PNG (mermaid CLI not installed): {exc}[/yellow]")


def main() -> None:
    rprint(Rule("HireGraph — building graph"))
    from hiregraph.graph import compile_graph
    app = compile_graph()
    save_graph_assets(app)
    rprint(Rule("Done — graph compiled successfully"))


if __name__ == "__main__":
    main()
