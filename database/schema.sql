CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    selected_agents TEXT,
    results TEXT,
    qa_passed BOOLEAN DEFAULT FALSE,
    human_approved BOOLEAN DEFAULT FALSE,
    deployment_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
