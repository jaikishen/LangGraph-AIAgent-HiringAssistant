"""Start the HireGraph FastAPI server."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "hiregraph.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],
    )
