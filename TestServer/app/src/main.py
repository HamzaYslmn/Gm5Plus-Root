"""App entry point. Auto-discovers routers from api/ and serves web/ as static."""
import importlib
import os
from pathlib import Path

from fastapi import FastAPI

PORT = int(os.getenv("PORT", 8001))

app = FastAPI(title="App", version="1.0.0")


# MARK: Auto-discover routes
_MARKER = b"from fastapi import APIRouter"

def include_all_routers(directory: str, prefix: str):
    """Import .py files under `directory` that define an APIRouter named `router`."""
    api_dir = Path(__file__).parent / directory
    for py in sorted(api_dir.rglob("*.py")):
        if _MARKER not in py.read_bytes():
            continue
        module = api_dir.name + "." + ".".join(py.relative_to(api_dir).with_suffix("").parts)
        try:
            app.include_router(importlib.import_module(module).router, prefix=prefix)
        except Exception as e:
            print(f"Router error {module}: {e}")

include_all_routers("api", "/api")

app.frontend("/", directory=Path(__file__).parent / "web")  # serves web/, yields to /api/* routes

if __name__ == "__main__":
    import uvicorn
    os.chdir(Path(__file__).parent)  # so reload can import main:app and find api/, web/
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)  # 0.0.0.0: reach it from your PC on the LAN
