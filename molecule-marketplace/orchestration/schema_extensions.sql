-- AI Orchestration Schema Extensions
-- Extends the existing marketplace database with AI-powered orchestration tables
-- Version: 1.0

-- Workflow execution metrics (extends existing usage_analytics)
CREATE TABLE IF NOT EXISTS workflow_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL UNIQUE,
    template_id INTEGER,
    template_name TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    success BOOLEAN DEFAULT 0,
    execution_time_seconds REAL,
    steps_completed INTEGER DEFAULT 0,
    steps_total INTEGER DEFAULT 0,
    error_messages TEXT,  -- JSON array
    performance_bottlenecks TEXT,  -- JSON array
    resource_usage TEXT,  -- JSON object
    user_variables TEXT,  -- JSON object
    project_context TEXT,  -- JSON object with project info
    optimization_applied TEXT,  -- JSON array of optimizations
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES templates (id)
);

-- Learned usage patterns
CREATE TABLE IF NOT EXISTS usage_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT NOT NULL UNIQUE,
    pattern_type TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    success_rate REAL DEFAULT 0.0,
    avg_execution_time REAL DEFAULT 0.0,
    common_variables TEXT,  -- JSON object
    bottlenecks TEXT,  -- JSON array
    optimization_suggestions TEXT,  -- JSON array
    confidence_score REAL DEFAULT 0.0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Performance benchmarks
CREATE TABLE IF NOT EXISTS performance_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,  -- execution_time, success_rate, resource_usage
    baseline_value REAL NOT NULL,
    current_value REAL NOT NULL,
    improvement_percentage REAL,
    measurement_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    sample_size INTEGER DEFAULT 1
);

-- Optimization recommendations
CREATE TABLE IF NOT EXISTS optimization_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type TEXT NOT NULL,  -- template, workflow, system
    target_id TEXT NOT NULL,
    recommendation_type TEXT NOT NULL,  -- performance, reliability, usability
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    expected_impact TEXT,  -- high, medium, low
    implementation_effort TEXT,  -- high, medium, low
    evidence TEXT,  -- JSON object with supporting data
    status TEXT DEFAULT 'pending',  -- pending, implemented, dismissed
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Execution plans
CREATE TABLE IF NOT EXISTS execution_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL UNIQUE,
    template_name TEXT NOT NULL,
    configuration TEXT NOT NULL,  -- JSON of WorkflowConfiguration
    steps TEXT NOT NULL,  -- JSON of ExecutionStep list
    parallel_groups TEXT,  -- JSON of parallel execution groups
    estimated_duration INTEGER,
    optimization_applied TEXT,  -- JSON array of optimizations
    confidence_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Active executions
CREATE TABLE IF NOT EXISTS active_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL UNIQUE,
    plan_id TEXT NOT NULL,
    template_name TEXT NOT NULL,
    status TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    estimated_end_time DATETIME,
    current_step TEXT,
    progress_percentage REAL DEFAULT 0.0,
    resource_usage TEXT,  -- JSON object
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Execution step results
CREATE TABLE IF NOT EXISTS execution_step_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    status TEXT NOT NULL,
    start_time DATETIME,
    end_time DATETIME,
    duration_seconds REAL,
    output TEXT,
    error_message TEXT,
    resource_usage TEXT,  -- JSON object
    retry_count INTEGER DEFAULT 0,
    FOREIGN KEY (execution_id) REFERENCES active_executions (execution_id)
);

-- Performance predictions
CREATE TABLE IF NOT EXISTS performance_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL,
    prediction_type TEXT NOT NULL,  -- execution_time, success_rate, etc.
    predicted_value REAL NOT NULL,
    actual_value REAL,
    confidence_score REAL,
    features TEXT,  -- JSON object of input features
    prediction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    accuracy_score REAL  -- Calculated after actual value is known
);

-- Learning insights
CREATE TABLE IF NOT EXISTS learning_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id TEXT NOT NULL UNIQUE,
    insight_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    evidence TEXT NOT NULL,  -- JSON object
    confidence_score REAL NOT NULL,
    impact_assessment TEXT NOT NULL,
    actionable_recommendations TEXT NOT NULL,  -- JSON array
    affected_templates TEXT NOT NULL,  -- JSON array
    discovered_at DATETIME NOT NULL,
    status TEXT DEFAULT 'new',
    reviewed_at DATETIME,
    reviewer_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Performance trends tracking
CREATE TABLE IF NOT EXISTS performance_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trend_id TEXT NOT NULL UNIQUE,
    metric_name TEXT NOT NULL,
    template_name TEXT,  -- NULL for system-wide trends
    trend_direction TEXT NOT NULL,
    change_percentage REAL NOT NULL,
    confidence REAL NOT NULL,
    time_period_days INTEGER NOT NULL,
    data_points TEXT NOT NULL,  -- JSON array of [timestamp, value] pairs
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Learning pipeline runs
CREATE TABLE IF NOT EXISTS learning_pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL UNIQUE,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    status TEXT NOT NULL,  -- running, completed, failed
    insights_discovered INTEGER DEFAULT 0,
    trends_identified INTEGER DEFAULT 0,
    recommendations_generated INTEGER DEFAULT 0,
    execution_summary TEXT,  -- JSON object
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- System health metrics
CREATE TABLE IF NOT EXISTS system_health_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_date DATE NOT NULL,
    overall_success_rate REAL,
    avg_execution_time REAL,
    total_executions INTEGER,
    unique_templates_used INTEGER,
    error_rate REAL,
    optimization_effectiveness REAL,
    health_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(metric_date)
);

-- Automated actions log
CREATE TABLE IF NOT EXISTS automated_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id TEXT NOT NULL UNIQUE,
    action_type TEXT NOT NULL,  -- optimization_applied, alert_sent, etc.
    target_type TEXT NOT NULL,  -- template, system, user
    target_id TEXT,
    action_description TEXT NOT NULL,
    trigger_insight_id TEXT,
    execution_status TEXT NOT NULL,  -- pending, completed, failed
    execution_result TEXT,  -- JSON object
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trigger_insight_id) REFERENCES learning_insights (insight_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_workflow_executions_template_name
    ON workflow_executions(template_name);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_start_time
    ON workflow_executions(start_time);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_success
    ON workflow_executions(success);

CREATE INDEX IF NOT EXISTS idx_usage_patterns_type
    ON usage_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_usage_patterns_confidence
    ON usage_patterns(confidence_score);

CREATE INDEX IF NOT EXISTS idx_performance_benchmarks_template
    ON performance_benchmarks(template_name, metric_name);

CREATE INDEX IF NOT EXISTS idx_execution_plans_template
    ON execution_plans(template_name);
CREATE INDEX IF NOT EXISTS idx_active_executions_status
    ON active_executions(status);
CREATE INDEX IF NOT EXISTS idx_execution_step_results_execution
    ON execution_step_results(execution_id);
CREATE INDEX IF NOT EXISTS idx_performance_predictions_template
    ON performance_predictions(template_name, prediction_type);

CREATE INDEX IF NOT EXISTS idx_learning_insights_type ON learning_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_learning_insights_status ON learning_insights(status);
CREATE INDEX IF NOT EXISTS idx_performance_trends_template ON performance_trends(template_name);
CREATE INDEX IF NOT EXISTS idx_system_health_date ON system_health_metrics(metric_date);
CREATE INDEX IF NOT EXISTS idx_automated_actions_status ON automated_actions(execution_status);

-- Views for common AI orchestration queries

-- Template performance summary with AI insights
CREATE VIEW IF NOT EXISTS template_ai_performance AS
SELECT
    t.id,
    t.name,
    t.title,
    t.category,
    t.tech_stack,
    t.download_count,
    t.rating_avg,
    COALESCE(we.total_executions, 0) as ai_executions,
    COALESCE(we.avg_success_rate, 0) as ai_success_rate,
    COALESCE(we.avg_execution_time, 0) as ai_avg_time,
    COALESCE(up.confidence_score, 0) as learning_confidence,
    CASE
        WHEN up.optimization_suggestions IS NOT NULL
        THEN json_array_length(up.optimization_suggestions)
        ELSE 0
    END as optimization_opportunities
FROM templates t
LEFT JOIN (
    SELECT
        template_name,
        COUNT(*) as total_executions,
        AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as avg_success_rate,
        AVG(execution_time_seconds) as avg_execution_time
    FROM workflow_executions
    WHERE start_time > datetime('now', '-30 days')
    GROUP BY template_name
) we ON t.name = we.template_name
LEFT JOIN usage_patterns up ON up.pattern_id = 'template_usage_' || REPLACE(t.name, '-', '_')
WHERE t.is_active = 1;

-- System health dashboard
CREATE VIEW IF NOT EXISTS system_health_dashboard AS
SELECT
    date('now') as report_date,
    COUNT(DISTINCT we.template_name) as active_templates,
    COUNT(*) as total_executions_today,
    AVG(CASE WHEN we.success THEN 1.0 ELSE 0.0 END) as success_rate_today,
    AVG(we.execution_time_seconds) as avg_time_today,
    COUNT(DISTINCT ai.insight_id) as insights_discovered_today,
    COUNT(DISTINCT or_rec.id) as recommendations_pending
FROM workflow_executions we
LEFT JOIN learning_insights ai ON DATE(ai.discovered_at) = date('now')
LEFT JOIN optimization_recommendations or_rec ON or_rec.status = 'pending'
WHERE DATE(we.start_time) = date('now');

-- Learning effectiveness tracking
CREATE VIEW IF NOT EXISTS learning_effectiveness AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as patterns_learned,
    AVG(confidence_score) as avg_confidence,
    COUNT(CASE WHEN confidence_score > 0.8 THEN 1 END) as high_confidence_patterns,
    json_group_array(DISTINCT pattern_type) as pattern_types
FROM usage_patterns
WHERE created_at > datetime('now', '-30 days')
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Optimization impact tracking
CREATE VIEW IF NOT EXISTS optimization_impact AS
SELECT
    template_name,
    COUNT(*) as total_optimizations,
    AVG(improvement_percentage) as avg_improvement,
    MAX(improvement_percentage) as best_improvement,
    json_group_array(DISTINCT metric_name) as optimized_metrics
FROM performance_benchmarks
WHERE improvement_percentage > 0
AND measurement_date > date('now', '-30 days')
GROUP BY template_name
ORDER BY avg_improvement DESC;