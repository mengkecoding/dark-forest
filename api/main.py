"""FastAPI app for Dark Forest simulation — REST + WebSocket."""

import json
import uuid
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from engine.runner import SimulationRunner
from engine.config import SimulationConfig

app = FastAPI(title="Dark Forest Simulator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory simulation store
simulations: dict[str, SimulationRunner] = {}
ws_clients: dict[str, list[WebSocket]] = {}


# ── Pydantic models ────────────────────────────────────────

class ConfigInput(BaseModel):
    universe_width: float = 500
    max_turns: int = 500
    hider_count: int = 4
    aggressor_count: int = 3
    diplomat_count: int = 2
    observer_count: int = 2
    cleaner_count: int = 1
    base_detection_range: float = 60
    min_spawn_distance: float = 20

class SimulationCreated(BaseModel):
    id: str
    civ_count: int
    config: dict


# ── REST endpoints ──────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/simulations", response_model=SimulationCreated)
def create_simulation(config: ConfigInput = ConfigInput()):
    sim_id = uuid.uuid4().hex[:8]
    sim_config = SimulationConfig(**{k:v for k,v in config.model_dump().items() if hasattr(SimulationConfig, k)})
    runner = SimulationRunner(sim_config)
    simulations[sim_id] = runner
    return SimulationCreated(
        id=sim_id,
        civ_count=len(runner.universe.civilizations),
        config=config.model_dump(),
    )

@app.get("/api/simulations/{sim_id}")
def get_simulation(sim_id: str):
    runner = simulations.get(sim_id)
    if not runner:
        raise HTTPException(404, "Simulation not found")
    return runner.take_snapshot()

@app.post("/api/simulations/{sim_id}/step")
def step_simulation(sim_id: str):
    runner = simulations.get(sim_id)
    if not runner:
        raise HTTPException(404, "Simulation not found")
    return runner.run_turn()

@app.post("/api/simulations/{sim_id}/run")
def run_simulation(sim_id: str, turns: Optional[int] = None):
    runner = simulations.get(sim_id)
    if not runner:
        raise HTTPException(404, "Simulation not found")
    history = runner.run_simulation(max_turns=turns)
    return {"turns": len(history), "final": history[-1], "history": history}

@app.get("/api/simulations/{sim_id}/history")
def get_history(sim_id: str):
    runner = simulations.get(sim_id)
    if not runner:
        raise HTTPException(404, "Simulation not found")
    return runner.history

@app.delete("/api/simulations/{sim_id}")
def delete_simulation(sim_id: str):
    if sim_id in simulations:
        del simulations[sim_id]
    return {"deleted": sim_id}

@app.get("/api/scenarios")
def list_scenarios():
    scenarios_dir = Path(__file__).parent.parent / "scenarios"
    scenarios = []
    if scenarios_dir.exists():
        for f in sorted(scenarios_dir.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            scenarios.append({"id": f.stem, "name": data.get("name", f.stem),
                              "description": data.get("description", ""), "config": data.get("config", {})})
    return scenarios

@app.post("/api/scenarios/{scenario_id}/run")
def run_scenario(scenario_id: str):
    path = Path(__file__).parent.parent / "scenarios" / f"{scenario_id}.json"
    if not path.exists():
        raise HTTPException(404, f"Scenario '{scenario_id}' not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    config = SimulationConfig(**data["config"])
    sim_id = uuid.uuid4().hex[:8]
    runner = SimulationRunner(config)
    simulations[sim_id] = runner
    history = runner.run_simulation()
    return {"sim_id": sim_id, "turns": len(history), "final": history[-1], "history": history}


# ── WebSocket ───────────────────────────────────────────────

@app.websocket("/ws/{sim_id}")
async def websocket_endpoint(ws: WebSocket, sim_id: str):
    await ws.accept()
    if sim_id not in ws_clients:
        ws_clients[sim_id] = []
    ws_clients[sim_id].append(ws)
    try:
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        ws_clients[sim_id].remove(ws)

async def _broadcast(sim_id: str, data: dict):
    for ws in ws_clients.get(sim_id, []):
        try:
            await ws.send_json(data)
        except Exception:
            pass


# ── Static files (frontend) ─────────────────────────────────

web_dir = Path(__file__).parent.parent / "web"


@app.get("/")
def serve_frontend():
    index = web_dir / "index.html"
    if index.exists():
        return FileResponse(str(index), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return {"message": "Dark Forest API — frontend not built. Use /api/ endpoints."}


@app.get("/api")
def api_root():
    return {"message": "Dark Forest Simulator API", "version": "1.0.0",
            "endpoints": ["/api/health", "/api/simulations", "/api/scenarios"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
