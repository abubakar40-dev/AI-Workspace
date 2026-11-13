"""Minimal Honcho-compatible FastAPI server for Hermes integration."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Honcho Minimal API",
    description="Minimal Honcho API for Hermes local integration",
    version="0.1.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "honcho-minimal"}


@app.post("/v3/sessions")
async def create_session(request: Request):
    """Create a new session."""
    data = await request.json()
    return JSONResponse({
        "id": data.get("id", "session-123"),
        "workspace_id": data.get("workspace_id", "workspace-1"),
        "status": "active",
    })


@app.get("/v3/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a session by ID."""
    return JSONResponse({
        "id": session_id,
        "workspace_id": "workspace-1",
        "status": "active",
    })


@app.post("/v3/messages")
async def create_message(request: Request):
    """Create a new message."""
    data = await request.json()
    return JSONResponse({
        "id": data.get("id", "msg-123"),
        "content": data.get("content", ""),
        "role": data.get("role", "user"),
    })


@app.get("/v3/messages")
async def list_messages():
    """List messages."""
    return JSONResponse({"messages": [], "total": 0})


@app.post("/v3/conclusions")
async def create_conclusion(request: Request):
    """Create a conclusion."""
    data = await request.json()
    return JSONResponse({
        "id": data.get("id", "conc-123"),
        "content": data.get("content", ""),
        "conclusion": data.get("conclusion", ""),
    })


@app.post("/v3/dreams")
async def create_dream(request: Request):
    """Create a dream."""
    data = await request.json()
    return JSONResponse({
        "id": data.get("id", "dream-123"),
        "content": data.get("content", ""),
    })


@app.get("/v3/peers")
async def list_peers():
    """List peers."""
    return JSONResponse({"peers": [], "total": 0})


@app.post("/v3/peers")
async def create_peer(request: Request):
    """Create a peer."""
    data = await request.json()
    return JSONResponse({
        "id": data.get("id", "peer-123"),
        "name": data.get("name", "peer-1"),
    })


@app.get("/v3/keys")
async def list_keys():
    """List keys."""
    return JSONResponse({"keys": [], "total": 0})


@app.post("/v3/keys")
async def create_key(request: Request):
    """Create a key."""
    data = await request.json()
    return JSONResponse({
        "id": data.get("id", "key-123"),
        "key": data.get("key", "api-key"),
    })


@app.get("/v3/workspaces")
async def list_workspaces():
    """List workspaces."""
    return JSONResponse({"workspaces": [], "total": 0})


@app.get("/v3/tenants")
async def list_tenants():
    """List tenants."""
    return JSONResponse({"tenants": [], "total": 0})


@app.get("/v3/summaries")
async def list_summaries():
    """List summaries."""
    return JSONResponse({"summaries": [], "total": 0})


@app.get("/v3/dreams/status")
async def dream_status():
    """Dream status."""
    return JSONResponse({"dreams_enabled": True})


@app.post("/v3/dreams")
async def create_dream_endpoint(request: Request):
    """Create a dream."""
    data = await request.json()
    return JSONResponse({
        "id": data.get("id", "dream-123"),
        "content": data.get("content", ""),
    })


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return JSONResponse({"metrics": "placeholder"})


@app.get("/.well-known/honcho-metadata")
async def honcho_metadata():
    """Honcho metadata endpoint."""
    return {
        "name": "honcho-minimal",
        "version": "0.1.0",
        "description": "Minimal Honcho API for Hermes integration",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
