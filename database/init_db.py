import sqlite3
import os
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH", "voiceiq.db")

def init_db():
    logger.info(f"Initializing SQLite database at: {DATABASE_PATH}")
    
    # Connect to the database (creates the file if it doesn't exist)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Create test_scenarios table
    logger.info("Creating 'test_scenarios' table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_name TEXT UNIQUE NOT NULL,
        scenario_description TEXT NOT NULL,
        caller_personality TEXT NOT NULL CHECK (
            caller_personality IN ('friendly', 'hostile', 'confused', 'impatient', 'off_topic', 'interrupter')
        ),
        caller_goal TEXT NOT NULL,
        difficulty_level TEXT NOT NULL CHECK (
            difficulty_level IN ('easy', 'medium', 'hard')
        ),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Create test_runs table
    logger.info("Creating 'test_runs' table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_id INTEGER NOT NULL,
        agent_system_prompt TEXT NOT NULL,
        conversation_transcript TEXT NOT NULL, -- JSON string (list of dicts with role, content, turn)
        total_turns INTEGER NOT NULL,
        goal_completed BOOLEAN NOT NULL CHECK (goal_completed IN (0, 1)),
        overall_score REAL NOT NULL,
        scores_breakdown TEXT NOT NULL, -- JSON string (response_relevance, objection_handling, conversation_flow, empathy, goal_completion)
        failure_points TEXT NOT NULL, -- JSON string (list of turn number + reason)
        recommendations TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (scenario_id) REFERENCES test_scenarios(id) ON DELETE CASCADE
    );
    """)
    
    # Create judge_calibration table
    logger.info("Creating 'judge_calibration' table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS judge_calibration (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_run_id INTEGER NOT NULL,
        human_score REAL, -- 0-100, nullable
        human_failure_points TEXT, -- JSON string, nullable
        judge_score REAL NOT NULL, -- 0-100
        score_delta REAL GENERATED ALWAYS AS (judge_score - human_score) STORED, -- computed automatically in sqlite >= 3.31
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (test_run_id) REFERENCES test_runs(id) ON DELETE CASCADE
    );
    """)
    
    # Create indexes
    logger.info("Creating database indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_runs_scenario_id ON test_runs(scenario_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_runs_created_at ON test_runs(created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_judge_calibration_test_run_id ON judge_calibration(test_run_id);")
    
    conn.commit()
    conn.close()
    logger.info("Database initialization completed successfully.")

if __name__ == "__main__":
    init_db()
