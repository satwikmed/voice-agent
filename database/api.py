import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json

app = FastAPI(title="VoiceIQ API")

# Configure CORS so React app can call it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(PROJECT_ROOT, "voiceiq.db")

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/scenarios")
def get_scenarios():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_scenarios ORDER BY id")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.get("/api/runs")
def get_runs():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tr.id, tr.scenario_id, ts.scenario_name, ts.difficulty_level, 
               tr.overall_score, tr.total_turns, tr.goal_completed, tr.created_at
        FROM test_runs tr
        JOIN test_scenarios ts ON tr.scenario_id = ts.id
        ORDER BY tr.created_at DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.get("/api/runs/{run_id}")
def get_run_detail(run_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tr.*, ts.scenario_name, ts.scenario_description, ts.difficulty_level, ts.caller_personality
        FROM test_runs tr
        JOIN test_scenarios ts ON tr.scenario_id = ts.id
        WHERE tr.id = ?
    """, (run_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    
    data = dict(row)
    # Deserialize JSON fields
    try:
        data["conversation_transcript"] = json.loads(data["conversation_transcript"])
    except:
        pass
    try:
        data["scores_breakdown"] = json.loads(data["scores_breakdown"])
    except:
        pass
    try:
        data["failure_points"] = json.loads(data["failure_points"])
    except:
        pass
        
    return data

@app.get("/api/calibration")
def get_calibration():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT jc.*, tr.overall_score as judge_score_computed, 
               tr.scores_breakdown, tr.failure_points as run_failure_points,
               ts.scenario_name
        FROM judge_calibration jc
        JOIN test_runs tr ON jc.test_run_id = tr.id
        JOIN test_scenarios ts ON tr.scenario_id = ts.id
        WHERE jc.human_score IS NOT NULL
        ORDER BY jc.created_at
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

class SimulationRequest(BaseModel):
    agent_prompt: str
    scenario_id: int

@app.post("/api/simulate")
async def run_live_simulation(payload: SimulationRequest):
    import sys
    sys.path.insert(0, PROJECT_ROOT)
    from simulator.agent_simulator import run_simulation
    from simulator.judge import evaluate_with_consistency
    from simulator.scenarios import get_scenario_by_name
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_scenarios WHERE id = ?", (payload.scenario_id,))
    scen_row = cursor.fetchone()
    if not scen_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Recreate the Scenario object
    from simulator.scenarios import Scenario
    scenario = Scenario(
        id=scen_row["id"],
        scenario_name=scen_row["scenario_name"],
        scenario_description=scen_row["scenario_description"],
        caller_personality=scen_row["caller_personality"],
        caller_goal=scen_row["caller_goal"],
        difficulty_level=scen_row["difficulty_level"]
    )
    
    try:
        # Run simulation loop
        sim_result = await run_simulation(payload.agent_prompt, scenario)
        
        # Run LLM Judge evaluation
        eval_result = await evaluate_with_consistency(sim_result["transcript"], scenario.scenario_description)
        
        # Save results to database
        dimensions = ["response_relevance", "objection_handling", "conversation_flow", "empathy", "goal_completion"]
        scores_breakdown = {d: eval_result.get(d, 0) for d in dimensions}
        
        cursor.execute(
            """INSERT INTO test_runs
               (scenario_id, agent_system_prompt, conversation_transcript,
                total_turns, goal_completed, overall_score, scores_breakdown,
                failure_points, recommendations)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                scenario.id,
                payload.agent_prompt,
                json.dumps(sim_result["transcript"]),
                sim_result["total_turns"],
                1 if sim_result["goal_completed"] else 0,
                eval_result["overall_score"],
                json.dumps(scores_breakdown),
                json.dumps(eval_result.get("failure_points", [])),
                "\n".join(eval_result.get("recommendations", [])),
            ),
        )
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "run_id": run_id,
            "transcript": sim_result["transcript"],
            "total_turns": sim_result["total_turns"],
            "goal_completed": sim_result["goal_completed"],
            "overall_score": eval_result["overall_score"],
            "scores_breakdown": scores_breakdown,
            "failure_points": eval_result.get("failure_points", []),
            "recommendations": eval_result.get("recommendations", [])
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

