-- Gas Town MEOW Stack - Molecule Marketplace Database Schema
-- Version: 1.0
-- Purpose: Template storage, versioning, and usage analytics

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Template metadata table
CREATE TABLE templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,           -- Template identifier (e.g., 'web-app-fullstack')
    title TEXT NOT NULL,                 -- Human-readable title
    description TEXT,                    -- Template description
    category TEXT NOT NULL,              -- Category (web-dev, api-dev, testing, etc.)
    tech_stack TEXT NOT NULL,            -- Technology stack (react-node, django-python, etc.)
    version TEXT NOT NULL DEFAULT '1.0.0', -- Semantic version
    author TEXT,                         -- Template author
    tags TEXT,                          -- JSON array of tags for search
    difficulty TEXT DEFAULT 'beginner', -- beginner, intermediate, advanced
    estimated_time INTEGER,             -- Estimated setup time in minutes
    requirements TEXT,                  -- JSON array of requirements/dependencies
    variables TEXT,                     -- JSON object of template variables
    readme_content TEXT,                -- Template documentation
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME,             -- When template was published to marketplace
    is_active BOOLEAN DEFAULT 1,       -- Whether template is available
    download_count INTEGER DEFAULT 0,   -- Usage analytics
    rating_avg REAL DEFAULT 0.0,       -- Average rating (0.0-5.0)
    rating_count INTEGER DEFAULT 0     -- Number of ratings
);

-- Template files table (stores actual workflow files)
CREATE TABLE template_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,            -- Relative path within template
    file_type TEXT NOT NULL,            -- toml, yaml, json, md, sh, etc.
    content TEXT NOT NULL,              -- File content
    is_executable BOOLEAN DEFAULT 0,    -- Whether file should be executable
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES templates (id) ON DELETE CASCADE
);

-- Template dependencies (relationships between templates)
CREATE TABLE template_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    depends_on_id INTEGER NOT NULL,
    dependency_type TEXT DEFAULT 'requires', -- requires, suggests, conflicts
    version_constraint TEXT,            -- Version constraint (^1.0.0, >=2.0.0, etc.)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES templates (id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_id) REFERENCES templates (id) ON DELETE CASCADE,
    UNIQUE(template_id, depends_on_id)
);

-- Template installations (track usage)
CREATE TABLE template_installations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    user_identifier TEXT,              -- User/project identifier
    project_path TEXT,                 -- Where template was installed
    config_values TEXT,                -- JSON object of user-provided config
    installation_status TEXT DEFAULT 'success', -- success, failed, partial
    installed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES templates (id) ON DELETE CASCADE
);

-- Template ratings and reviews
CREATE TABLE template_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    user_identifier TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    helpful_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES templates (id) ON DELETE CASCADE,
    UNIQUE(template_id, user_identifier)
);

-- Usage analytics (track what features are used)
CREATE TABLE usage_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,          -- viewed, downloaded, installed, customized
    user_identifier TEXT,
    metadata TEXT,                      -- JSON object with additional context
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES templates (id) ON DELETE CASCADE
);

-- Search index for full-text search
CREATE VIRTUAL TABLE template_search USING fts5(
    name,
    title,
    description,
    category,
    tech_stack,
    tags,
    content=templates,
    content_rowid=id
);

-- Triggers to maintain search index
CREATE TRIGGER template_search_insert AFTER INSERT ON templates BEGIN
    INSERT INTO template_search(rowid, name, title, description, category, tech_stack, tags)
    VALUES (new.id, new.name, new.title, new.description, new.category, new.tech_stack, new.tags);
END;

CREATE TRIGGER template_search_delete AFTER DELETE ON templates BEGIN
    INSERT INTO template_search(template_search, rowid, name, title, description, category, tech_stack, tags)
    VALUES ('delete', old.id, old.name, old.title, old.description, old.category, old.tech_stack, old.tags);
END;

CREATE TRIGGER template_search_update AFTER UPDATE ON templates BEGIN
    INSERT INTO template_search(template_search, rowid, name, title, description, category, tech_stack, tags)
    VALUES ('delete', old.id, old.name, old.title, old.description, old.category, old.tech_stack, old.tags);
    INSERT INTO template_search(rowid, name, title, description, category, tech_stack, tags)
    VALUES (new.id, new.name, new.title, new.description, new.category, new.tech_stack, new.tags);
END;

-- Indexes for performance
CREATE INDEX idx_templates_category ON templates(category);
CREATE INDEX idx_templates_tech_stack ON templates(tech_stack);
CREATE INDEX idx_templates_is_active ON templates(is_active);
CREATE INDEX idx_templates_created_at ON templates(created_at);
CREATE INDEX idx_templates_download_count ON templates(download_count);
CREATE INDEX idx_templates_rating_avg ON templates(rating_avg);

CREATE INDEX idx_template_files_template_id ON template_files(template_id);
CREATE INDEX idx_template_files_file_type ON template_files(file_type);

CREATE INDEX idx_template_installations_template_id ON template_installations(template_id);
CREATE INDEX idx_template_installations_installed_at ON template_installations(installed_at);

CREATE INDEX idx_usage_analytics_template_id ON usage_analytics(template_id);
CREATE INDEX idx_usage_analytics_action_type ON usage_analytics(action_type);
CREATE INDEX idx_usage_analytics_timestamp ON usage_analytics(timestamp);

-- Views for common queries
CREATE VIEW template_summary AS
SELECT
    t.id,
    t.name,
    t.title,
    t.description,
    t.category,
    t.tech_stack,
    t.version,
    t.difficulty,
    t.estimated_time,
    t.download_count,
    t.rating_avg,
    t.rating_count,
    t.created_at,
    t.updated_at,
    COUNT(tf.id) as file_count
FROM templates t
LEFT JOIN template_files tf ON t.id = tf.template_id
WHERE t.is_active = 1
GROUP BY t.id;

CREATE VIEW popular_templates AS
SELECT *
FROM template_summary
ORDER BY download_count DESC, rating_avg DESC
LIMIT 50;

CREATE VIEW recent_templates AS
SELECT *
FROM template_summary
ORDER BY created_at DESC
LIMIT 20;