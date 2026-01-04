"""
Usage Pattern Learning System
Analyzes workflow execution patterns to identify optimization opportunities.
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
import statistics

# Add the parent directory to path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.database.db import MoleculeDB

logger = logging.getLogger(__name__)


@dataclass
class UsagePattern:
    """Represents a learned usage pattern."""
    pattern_id: str
    pattern_type: str  # template_usage, workflow_execution, failure_pattern, etc.
    frequency: int
    success_rate: float
    avg_execution_time: float
    common_variables: Dict[str, Any]
    bottlenecks: List[str]
    optimization_suggestions: List[str]
    confidence_score: float
    last_updated: datetime


@dataclass
class WorkflowMetrics:
    """Metrics for workflow execution."""
    execution_id: str
    template_name: str
    start_time: datetime
    end_time: datetime
    success: bool
    execution_time: float
    steps_completed: int
    steps_total: int
    error_messages: List[str]
    performance_bottlenecks: List[str]
    resource_usage: Dict[str, float]
    user_variables: Dict[str, Any]


class UsagePatternLearner:
    """Learns from usage patterns to optimize workflow orchestration."""

    def __init__(self, db_path: str = None):
        """Initialize the usage pattern learner."""
        self.db = MoleculeDB(db_path) if db_path else MoleculeDB()

        # Create extended analytics tables if they don't exist
        self._initialize_learning_tables()

        # Pattern analysis settings
        self.min_pattern_frequency = 3  # Minimum occurrences to consider a pattern
        self.pattern_confidence_threshold = 0.7
        self.learning_window_days = 30

        logger.info("UsagePatternLearner initialized")

    def _initialize_learning_tables(self):
        """Create extended tables for learning analytics."""

        learning_schema = '''
        -- Workflow execution metrics
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
        '''

        try:
            with self.db.get_connection() as conn:
                conn.executescript(learning_schema)
            logger.info("Learning analytics tables initialized")
        except Exception as e:
            logger.error(f"Failed to initialize learning tables: {e}")

    def record_workflow_execution(self, metrics: WorkflowMetrics):
        """Record workflow execution metrics for learning."""

        try:
            # Get template ID if it exists
            template_id = None
            if metrics.template_name:
                template = self.db.get_template(metrics.template_name)
                template_id = template.get('id') if template else None

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO workflow_executions (
                        execution_id, template_id, template_name, start_time, end_time,
                        success, execution_time_seconds, steps_completed, steps_total,
                        error_messages, performance_bottlenecks, resource_usage,
                        user_variables, project_context
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.execution_id, template_id, metrics.template_name,
                    metrics.start_time, metrics.end_time, metrics.success,
                    metrics.execution_time, metrics.steps_completed, metrics.steps_total,
                    json.dumps(metrics.error_messages),
                    json.dumps(metrics.performance_bottlenecks),
                    json.dumps(metrics.resource_usage),
                    json.dumps(metrics.user_variables),
                    json.dumps({})  # project_context - can be extended
                ))
                conn.commit()

            logger.info(f"Recorded workflow execution: {metrics.execution_id}")

            # Trigger pattern analysis for this template
            self._analyze_template_patterns(metrics.template_name)

        except Exception as e:
            logger.error(f"Failed to record workflow execution: {e}")

    def _analyze_template_patterns(self, template_name: str):
        """Analyze patterns for a specific template."""

        try:
            # Get recent executions for this template
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT * FROM workflow_executions
                WHERE template_name = ?
                AND start_time > datetime('now', '-{} days')
                ORDER BY start_time DESC
            '''.format(self.learning_window_days), (template_name,))

            executions = cursor.fetchall()

            if len(executions) < self.min_pattern_frequency:
                return  # Not enough data

            # Calculate aggregate metrics
            success_rate = sum(1 for e in executions if e[5]) / len(executions)  # success column
            execution_times = [e[6] for e in executions if e[6]]  # execution_time_seconds
            avg_time = statistics.mean(execution_times) if execution_times else 0

            # Analyze common variables
            all_variables = []
            common_bottlenecks = []

            for execution in executions:
                if execution[11]:  # user_variables
                    try:
                        variables = json.loads(execution[11])
                        all_variables.append(variables)
                    except:
                        continue

                if execution[9]:  # performance_bottlenecks
                    try:
                        bottlenecks = json.loads(execution[9])
                        common_bottlenecks.extend(bottlenecks)
                    except:
                        continue

            # Find most common variable values
            common_variables = {}
            if all_variables:
                for key in set().union(*all_variables):
                    values = [v.get(key) for v in all_variables if key in v]
                    if values:
                        # Find most common value
                        value_counts = {}
                        for value in values:
                            value_counts[str(value)] = value_counts.get(str(value), 0) + 1
                        most_common = max(value_counts.items(), key=lambda x: x[1])
                        if most_common[1] >= len(values) * 0.6:  # At least 60% frequency
                            common_variables[key] = most_common[0]

            # Find most common bottlenecks
            bottleneck_counts = {}
            for bottleneck in common_bottlenecks:
                bottleneck_counts[bottleneck] = bottleneck_counts.get(bottleneck, 0) + 1

            common_bottlenecks = [b for b, count in bottleneck_counts.items()
                                if count >= len(executions) * 0.3]  # At least 30% frequency

            # Generate optimization suggestions
            suggestions = self._generate_optimization_suggestions(
                template_name, success_rate, avg_time, common_bottlenecks, executions
            )

            # Calculate confidence score
            confidence = self._calculate_pattern_confidence(
                len(executions), success_rate, avg_time, common_bottlenecks
            )

            # Store the pattern
            pattern_id = f"template_usage_{template_name.replace('-', '_')}"
            cursor.execute('''
                INSERT OR REPLACE INTO usage_patterns (
                    pattern_id, pattern_type, frequency, success_rate, avg_execution_time,
                    common_variables, bottlenecks, optimization_suggestions,
                    confidence_score, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern_id, 'template_usage', len(executions), success_rate, avg_time,
                json.dumps(common_variables), json.dumps(common_bottlenecks),
                json.dumps(suggestions), confidence, datetime.now()
            ))

            self.db.conn.commit()
            logger.info(f"Updated usage pattern for template: {template_name}")

        except Exception as e:
            logger.error(f"Failed to analyze template patterns: {e}")

    def _generate_optimization_suggestions(self,
                                         template_name: str,
                                         success_rate: float,
                                         avg_time: float,
                                         bottlenecks: List[str],
                                         executions: List) -> List[str]:
        """Generate optimization suggestions based on patterns."""

        suggestions = []

        # Success rate optimizations
        if success_rate < 0.8:
            suggestions.append(f"Improve template reliability - success rate is {success_rate:.1%}")

            # Analyze failure patterns
            failed_executions = [e for e in executions if not e[5]]  # not success
            if failed_executions:
                error_patterns = {}
                for execution in failed_executions:
                    if execution[8]:  # error_messages
                        try:
                            errors = json.loads(execution[8])
                            for error in errors:
                                error_patterns[error] = error_patterns.get(error, 0) + 1
                        except:
                            continue

                if error_patterns:
                    most_common_error = max(error_patterns.items(), key=lambda x: x[1])
                    suggestions.append(f"Address common error: {most_common_error[0]}")

        # Performance optimizations
        if avg_time > 300:  # More than 5 minutes
            suggestions.append(f"Optimize execution time - average is {avg_time:.1f} seconds")

        # Bottleneck-specific suggestions
        for bottleneck in bottlenecks:
            if 'dependency' in bottleneck.lower():
                suggestions.append("Consider caching dependencies or using faster mirrors")
            elif 'build' in bottleneck.lower():
                suggestions.append("Optimize build process with parallel execution")
            elif 'test' in bottleneck.lower():
                suggestions.append("Parallelize test execution or reduce test scope")
            elif 'download' in bottleneck.lower():
                suggestions.append("Pre-cache large downloads or use CDN")

        # Template-specific suggestions
        if 'react' in template_name.lower():
            if avg_time > 180:
                suggestions.append("Use lighter React starter or optimize webpack config")
        elif 'docker' in template_name.lower():
            if avg_time > 120:
                suggestions.append("Use multi-stage builds or smaller base images")
        elif 'python' in template_name.lower():
            if avg_time > 90:
                suggestions.append("Consider using uv instead of pip for faster dependency resolution")

        return suggestions[:5]  # Limit to top 5 suggestions

    def _calculate_pattern_confidence(self,
                                    sample_size: int,
                                    success_rate: float,
                                    avg_time: float,
                                    bottlenecks: List[str]) -> float:
        """Calculate confidence score for a pattern."""

        confidence = 0.0

        # Sample size factor (more samples = higher confidence)
        size_factor = min(sample_size / 20, 1.0)  # Cap at 20 samples for full confidence
        confidence += size_factor * 0.4

        # Success rate factor (consistent success = higher confidence)
        if success_rate >= 0.9:
            confidence += 0.3
        elif success_rate >= 0.7:
            confidence += 0.2
        elif success_rate >= 0.5:
            confidence += 0.1

        # Time consistency factor (low variance = higher confidence)
        # This would require tracking time variance, simplified for now
        confidence += 0.2  # Assume reasonable consistency

        # Bottleneck consistency factor
        if len(bottlenecks) <= 2:  # Few consistent bottlenecks
            confidence += 0.1

        return min(confidence, 1.0)

    def get_usage_patterns(self,
                          pattern_type: str = None,
                          min_confidence: float = 0.5) -> List[UsagePattern]:
        """Get learned usage patterns."""

        try:
            cursor = self.db.conn.cursor()

            query = '''
                SELECT * FROM usage_patterns
                WHERE confidence_score >= ?
            '''
            params = [min_confidence]

            if pattern_type:
                query += ' AND pattern_type = ?'
                params.append(pattern_type)

            query += ' ORDER BY confidence_score DESC, frequency DESC'

            cursor.execute(query, params)
            rows = cursor.fetchall()

            patterns = []
            for row in rows:
                pattern = UsagePattern(
                    pattern_id=row[1],
                    pattern_type=row[2],
                    frequency=row[3],
                    success_rate=row[4],
                    avg_execution_time=row[5],
                    common_variables=json.loads(row[6] or '{}'),
                    bottlenecks=json.loads(row[7] or '[]'),
                    optimization_suggestions=json.loads(row[8] or '[]'),
                    confidence_score=row[9],
                    last_updated=datetime.fromisoformat(row[10])
                )
                patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"Failed to get usage patterns: {e}")
            return []

    def get_template_insights(self, template_name: str) -> Dict[str, Any]:
        """Get insights for a specific template."""

        try:
            cursor = self.db.conn.cursor()

            # Get execution history
            cursor.execute('''
                SELECT COUNT(*),
                       AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                       AVG(execution_time_seconds) as avg_time,
                       MIN(start_time) as first_use,
                       MAX(start_time) as last_use
                FROM workflow_executions
                WHERE template_name = ?
                AND start_time > datetime('now', '-30 days')
            ''', (template_name,))

            stats = cursor.fetchone()

            if not stats or stats[0] == 0:
                return {'message': 'No recent usage data available'}

            # Get pattern for this template
            pattern_id = f"template_usage_{template_name.replace('-', '_')}"
            cursor.execute('''
                SELECT * FROM usage_patterns WHERE pattern_id = ?
            ''', (pattern_id,))

            pattern_row = cursor.fetchone()

            insights = {
                'template_name': template_name,
                'usage_stats': {
                    'total_executions': stats[0],
                    'success_rate': round(stats[1] or 0, 3),
                    'avg_execution_time': round(stats[2] or 0, 1),
                    'first_use': stats[3],
                    'last_use': stats[4]
                }
            }

            if pattern_row:
                insights['learned_patterns'] = {
                    'common_variables': json.loads(pattern_row[6] or '{}'),
                    'bottlenecks': json.loads(pattern_row[7] or '[]'),
                    'optimization_suggestions': json.loads(pattern_row[8] or '[]'),
                    'confidence_score': round(pattern_row[9], 3)
                }

            # Get recent performance trend
            cursor.execute('''
                SELECT DATE(start_time) as day,
                       AVG(execution_time_seconds) as avg_time,
                       AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate
                FROM workflow_executions
                WHERE template_name = ?
                AND start_time > datetime('now', '-7 days')
                GROUP BY DATE(start_time)
                ORDER BY day DESC
            ''', (template_name,))

            trends = cursor.fetchall()
            insights['performance_trend'] = [
                {
                    'date': trend[0],
                    'avg_time': round(trend[1] or 0, 1),
                    'success_rate': round(trend[2] or 0, 3)
                }
                for trend in trends
            ]

            return insights

        except Exception as e:
            logger.error(f"Failed to get template insights: {e}")
            return {'error': str(e)}

    def update_performance_benchmark(self,
                                   template_name: str,
                                   metric_name: str,
                                   current_value: float):
        """Update performance benchmark for a template."""

        try:
            cursor = self.db.conn.cursor()

            # Get existing benchmark
            cursor.execute('''
                SELECT baseline_value, current_value, sample_size
                FROM performance_benchmarks
                WHERE template_name = ? AND metric_name = ?
                ORDER BY measurement_date DESC LIMIT 1
            ''', (template_name, metric_name))

            existing = cursor.fetchone()

            if existing:
                baseline_value = existing[0]
                # Update with weighted average
                sample_size = existing[2] + 1
                new_current = (existing[1] * existing[2] + current_value) / sample_size
                improvement = ((baseline_value - new_current) / baseline_value * 100
                             if baseline_value > 0 else 0)
            else:
                # First benchmark
                baseline_value = current_value
                new_current = current_value
                improvement = 0.0
                sample_size = 1

            cursor.execute('''
                INSERT INTO performance_benchmarks (
                    template_name, metric_name, baseline_value, current_value,
                    improvement_percentage, sample_size
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (template_name, metric_name, baseline_value, new_current,
                  improvement, sample_size))

            self.db.conn.commit()

            logger.info(f"Updated benchmark for {template_name}.{metric_name}: {improvement:.1f}% improvement")

        except Exception as e:
            logger.error(f"Failed to update performance benchmark: {e}")