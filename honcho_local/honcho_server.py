from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Path, Query
import uvicorn
import asyncio
import json
import hashlib
from typing import Optional, List, Dict, Any
import psycopg
from pgvector.psycopg import register_vector

@asynccontextmanager
async def lifespan(app: FastAPI):
    register_vector(psycopg.connect("host=/var/run/postgresql port=5433 dbname=honcho user=postgres"))
    yield

app = FastAPI(title="Honcho API", version="2.8.0", lifespan=lifespan)
API_V3 = "/v3"

def get_conn():
    conn = psycopg.connect("host=/var/run/postgresql port=5433 dbname=honcho user=postgres")
    conn.autocommit = True
    return conn

def qdict(cur):
    "Convert psycopg cursor result to list of dicts."
    cols = [c[0] for c in cur.description] if cur.description else []
    return [dict(zip(cols, row)) for row in cur.fetchall()] if cols else []

# Workspaces
@app.post(f"{API_V3}/workspaces/{{workspace_id}}")
async def cw(workspace_id: str):
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT * FROM workspaces WHERE id=%s", (workspace_id,))
            r = qdict(cur)
            if r: return r[0]
            cur.execute("INSERT INTO workspaces (id,metadata,configuration) VALUES (%s,%s,%s)", (workspace_id, "{}", "{}"))
            return {"id": workspace_id, "uid": None, "metadata": {}, "configuration": {}, "created_at": None, "updated_at": None}
    finally:
        c.close()

@app.get(f"{API_V3}/workspaces/{{workspace_id}}")
async def gw(workspace_id: str):
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT * FROM workspaces WHERE id=%s", (workspace_id,))
            r = qdict(cur)
            if r: return r[0]
            raise HTTPException(404, "Workspace not found")
    finally:
        c.close()

@app.get(f"{API_V3}/workspaces/")
async def lw(filters: Optional[Dict] = None):
    c = get_conn()
    try:
        with c.cursor() as cur:
            q = "SELECT * FROM workspaces WHERE TRUE"
            p = []
            if filters and filters.get("id"): q += " AND id=%s"; p.append(filters["id"])
            cur.execute(q, p)
            return qdict(cur)
    finally:
        c.close()

# Peers
@app.post(f"{API_V3}/workspaces/{{workspace_id}}/peers")
async def cp(workspace_id: str, peer_id: str, metadata: Optional[Dict] = None, configuration: Optional[Dict] = None):
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT * FROM peers WHERE id=%s AND workspace_id=%s", (peer_id, workspace_id))
            r = qdict(cur)
            if r: return r[0]
            cur.execute("INSERT INTO peers (id,workspace_id,metadata,configuration) VALUES (%s,%s,%s,%s)", 
                       (peer_id, workspace_id, json.dumps(metadata or {}), json.dumps(configuration or {})))
            return {"id": peer_id, "workspace_id": workspace_id, "metadata": metadata or {}, "configuration": configuration or {}}
    finally:
        c.close()

@app.get(f"{API_V3}/workspaces/{{workspace_id}}/peers/{{peer_id}}")
async def gp(workspace_id: str, peer_id: str):
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT * FROM peers WHERE id=%s AND workspace_id=%s", (peer_id, workspace_id))
            r = qdict(cur)
            if r: return r[0]
            raise HTTPException(404, "Peer not found")
    finally:
        c.close()

@app.get(f"{API_V3}/workspaces/{{workspace_id}}/peers/")
async def lp(workspace_id: str, filters: Optional[Dict] = None):
    c = get_conn()
    try:
        with c.cursor() as cur:
            q = "SELECT * FROM peers WHERE workspace_id=%s"
            p = [workspace_id]
            if filters:
                for k, v in filters.items(): q += f" AND {k}=%s"; p.append(v)
            cur.execute(q, p)
            return qdict(cur)
    finally:
        c.close()

# Sessions
@app.post(f"{API_V3}/workspaces/{{workspace_id}}/sessions/{{session_id}}")
async def cs(workspace_id: str, session_id: str, metadata: Optional[Dict] = None, configuration: Optional[Dict] = None):
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT * FROM sessions WHERE id=%s AND workspace_id=%s", (session_id, workspace_id))
            r = qdict(cur)
            if r: return r[0]
            cur.execute("INSERT INTO sessions (id,workspace_id,metadata,configuration,is_active) VALUES (%s,%s,%s,%s,TRUE)",
                       (session_id, workspace_id, json.dumps(metadata or {}), json.dumps(configuration or {})))
            return {"id": session_id, "workspace_id": workspace_id, "metadata": metadata or {}, "configuration": configuration or {}, "is_active": True}
    finally:
        c.close()

@app.get(f"{API_V3}/workspaces/{{workspace_id}}/sessions/{{session_id}}")
async def gs(workspace_id: str, session_id: str):
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT * FROM sessions WHERE id=%s AND workspace_id=%s", (session_id, workspace_id))
            r = qdict(cur)
            if r: return r[0]
            raise HTTPException(404, "Session not found")
    finally:
        c.close()

@app.get(f"{API_V3}/workspaces/{{workspace_id}}/sessions/")
async def ls(workspace_id: str, scope: Optional[str] = None):
    c = get_conn()
    try:
        with c.cursor() as cur:
            q = "SELECT * FROM sessions WHERE workspace_id=%s"
            p = [workspace_id]
            if scope: q += " AND scope=%s"; p.append(scope)
            cur.execute(q, p)
            return qdict(cur)
    finally:
        c.close()

# Scopes
@app.post(f"{API_V3}/workspaces/{{workspace_id}}/scopes/{{scope_id}}")
async def sc(workspace_id: str, scope_id: str, metadata: Optional[Dict] = None):
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT * FROM scopes WHERE id=%s AND workspace_id=%s", (scope_id, workspace_id))
            r = qdict(cur)
            if r: return r[0]
            cur.execute("INSERT INTO scopes (id,workspace_id,metadata) VALUES (%s,%s,%s)", (scope_id, workspace_id, json.dumps(metadata or {})))
            return {"id": scope_id, "workspace_id": workspace_id, "metadata": metadata or {}}
    finally:
        c.close()

@app.get(f"{API_V3}/workspaces/{{workspace_id}}/scopes/{{scope_id}}")
async def gs2(workspace_id: str, scope_id: str):
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT * FROM scopes WHERE id=%s AND workspace_id=%s", (scope_id, workspace_id))
            r = qdict(cur)
            if r: return r[0]
            raise HTTPException(404, "Scope not found")
    finally:
        c.close()

@app.get(f"{API_V3}/workspaces/{{workspace_id}}/scopes/")
async def ls2(workspace_id: str):
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT * FROM scopes WHERE workspace_id=%s")
            return qdict(cur)
    finally:
        c.close()

# Messages
@app.post(f"{API_V3}/workspaces/{{workspace_id}}/sessions/{{session_id}}/messages/")
async def cm(workspace_id: str, session_id: str, peer_id: str, role: str = "user", content: str = "", embedding: Optional[List[float]] = None):
    mid = hashlib.md5(f"{session_id}:{peer_id}:{content}".encode()).hexdigest()[:20]
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("""INSERT INTO messages (id,session_id,peer_id,role,content,embedding,created_at) VALUES (%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT (id) DO NOTHING""",
                       (mid, session_id, peer_id, role, content, embedding))
            cur.execute("UPDATE sessions SET updated_at=NOW() WHERE id=%s AND workspace_id=%s", (session_id, workspace_id))
            return {"id": mid, "session_id": session_id, "peer_id": peer_id, "role": role, "content": content, "embedding": embedding}
    finally:
        c.close()

@app.get(f"{API_V3}/workspaces/{{workspace_id}}/sessions/{{session_id}}/messages/")
async def lm(workspace_id: str, session_id: str, peer_id: Optional[str] = None, limit: int = 50):
    c = get_conn()
    try:
        with c.cursor() as cur:
            q = "SELECT * FROM messages WHERE session_id=%s"
            p = [session_id]
            if peer_id: q += " AND peer_id=%s"; p.append(peer_id)
            q += " ORDER BY created_at DESC LIMIT %s"; p.append(limit)
            cur.execute(q, p)
            return qdict(cur)
    finally:
        c.close()

# Conclusions
@app.post(f"{API_V3}/workspaces/{{workspace_id}}/conclusions/")
async def cc(workspace_id: str, observed_id: str, observer_id: str, content: str, embedding: Optional[List[float]] = None):
    cid = hashlib.md5(f"{workspace_id}:{observer_id}:{observed_id}".encode()).hexdigest()[:20]
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("""INSERT INTO conclusions (id,workspace_id,observed_id,observer_id,content,embedding,created_at) VALUES (%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT (id) DO NOTHING""",
                       (cid, workspace_id, observed_id, observer_id, content, embedding))
            return {"id": cid, "workspace_id": workspace_id, "observed_id": observed_id, "observer_id": observer_id, "content": content, "embedding": embedding}
    finally:
        c.close()

@app.get(f"{API_V3}/workspaces/{{workspace_id}}/conclusions/")
async def lc(workspace_id: str, observed_id: Optional[str] = None, filters: Optional[Dict] = None):
    c = get_conn()
    try:
        with c.cursor() as cur:
            q = "SELECT * FROM conclusions WHERE workspace_id=%s"
            p = [workspace_id]
            if observed_id: q += " AND observed_id=%s"; p.append(observed_id)
            if filters:
                for k, v in filters.items(): q += f" AND {k}=%s"; p.append(v)
            cur.execute(q, p)
            return qdict(cur)
    finally:
        c.close()

# Chat
@app.post(f"{API_V3}/workspaces/{{workspace_id}}/chat")
async def chat(workspace_id: str, query: str, session_id: Optional[str] = None, reasoning_level: str = "low", scope: Optional[List[str]] = None, include_evidence: bool = False):
    c = get_conn()
    try:
        with c.cursor() as cur:
            mq = "SELECT m.content,m.peer_id,m.role,m.created_at FROM messages m WHERE m.session_id=%s OR m.session_id IS NULL"
            params = [session_id] if session_id else []
            cur.execute(mq, params)
            rows = cur.fetchall()
            results = []
            for row in rows:
                ctext = row[0] if row[0] else ""
                if query.lower() in ctext.lower():
                    results.append({"content": ctext, "peer_id": row[1], "role": row[2], "created_at": str(row[3])})
            if include_evidence:
                return {"answer": " ".join(r["content"] for r in results[:3]) if results else "", "evidence": [{"content": r["content"], "peer_id": r["peer_id"]} for r in results[:5]]}
            return {"answer": " ".join(r["content"] for r in results[:3]) if results else ""}
    finally:
        c.close()

# Health
@app.get("/health")
async def health():
    c = get_conn()
    try:
        with c.cursor() as cur: cur.execute("SELECT 1")
        return {"status": "ok", "service": "honcho-server", "database": "connected"}
    except Exception as e: return {"status": "error", "service": "honcho-server", "detail": str(e)}, 500
    finally: c.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8123)
