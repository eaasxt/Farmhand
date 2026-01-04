"""
Continuous Learning Pipeline
Automated system for collecting analytics, identifying patterns, and improving orchestration.
"""

import sys
import json
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import logging
import math
import statistics
from concurrent.futures import ThreadPoolExecutor
import uuid

# Add the parent directory to path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.database.db import MoleculeDB
from .usage_learner import UsagePatternLearner, UsagePattern
from .workflow_optimizer import WorkflowOptimizer, OptimizationRecommendation

logger = logging.getLogger(__name__)


@dataclass
class LearningInsight:
    """Represents a learning insight discovered by the pipeline."""
    insight_id: str
    insight_type: str  # performance_trend, failure_pattern, optimization_opportunity, etc.
    title: str
    description: str
    evidence: Dict[str, Any]
    confidence_score: float
    impact_assessment: str  # high, medium, low
    actionable_recommendations: List[str]
    affected_templates: List[str]
    discovered_at: datetime
    status: str = "new"  # new, reviewed, implemented, dismissed


@dataclass
class PerformanceTrend:
    """Represents a performance trend over time."""
    metric_name: str
    template_name: Optional[str]
    trend_direction: str  # improving, degrading, stable
    change_percentage: float
    confidence: float
    time_period_days: int
    data_points: List[Tuple[datetime, float]]


@dataclass
class LearningReport:
    """Comprehensive learning report."""
    report_id: str
    generated_at: datetime
    time_period: timedelta
    total_executions: int
    performance_trends: List[PerformanceTrend]
    new_insights: List[LearningInsight]
    optimization_opportunities: List[OptimizationRecommendation]
    system_health_score: float
    key_findings: List[str]
    recommended_actions: List[str]


class ContinuousLearningPipeline:
    """Automated pipeline for continuous learning and optimization."""

    def __init__(self, db_path: str = None, learning_interval_hours: int = 6):
        """Initialize the continuous learning pipeline."""
        self.db = MoleculeDB(db_path) if db_path else MoleculeDB()
        self.usage_learner = UsagePatternLearner(db_path)
        self.optimizer = WorkflowOptimizer(db_path)

        self.learning_interval = timedelta(hours=learning_interval_hours)
        self.last_learning_run = None
        self.is_running = False

        # Learning pipeline configuration
        self.trend_analysis_window = 14  # days
        self.min_data_points_for_trend = 5
        self.insight_confidence_threshold = 0.6
        self.performance_degradation_threshold = 0.15  # 15% degradation

        # Initialize learning pipeline tables
        self._initialize_learning_pipeline_tables()

        logger.info(f"ContinuousLearningPipeline initialized with {learning_interval_hours}h interval")

    def _initialize_learning_pipeline_tables(self):
        """Initialize tables for learning pipeline tracking."""

        pipeline_schema = '''
        -- Learning insights storage
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
        CREATE INDEX IF NOT EXISTS idx_learning_insights_type ON learning_insights(insight_type);
        CREATE INDEX IF NOT EXISTS idx_learning_insights_status ON learning_insights(status);
        CREATE INDEX IF NOT EXISTS idx_performance_trends_template ON performance_trends(template_name);
        CREATE INDEX IF NOT EXISTS idx_system_health_date ON system_health_metrics(metric_date);
        CREATE INDEX IF NOT EXISTS idx_automated_actions_status ON automated_actions(execution_status);
        '''

        try:
            self.db._execute_script(pipeline_schema)
            logger.info("Learning pipeline tables initialized")
        except Exception as e:
            logger.error(f"Failed to initialize learning pipeline tables: {e}")

    async def start_continuous_learning(self):
        """Start the continuous learning pipeline."""

        if self.is_running:
            logger.warning("Learning pipeline is already running")
            return

        self.is_running = True
        logger.info("Starting continuous learning pipeline")

        try:
            while self.is_running:
                # Run learning cycle
                await self._run_learning_cycle()

                # Wait for next cycle
                await asyncio.sleep(self.learning_interval.total_seconds())

        except Exception as e:
            logger.error(f"Continuous learning pipeline error: {e}")
        finally:
            self.is_running = False
            logger.info("Continuous learning pipeline stopped")

    def stop_continuous_learning(self):
        """Stop the continuous learning pipeline."""
        self.is_running = False
        logger.info("Stopping continuous learning pipeline")

    async def _run_learning_cycle(self):
        """Run a single learning cycle."""

        run_id = f"learning_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()

        # Track the run
        self._start_pipeline_run(run_id, start_time)

        try:
            logger.info(f"Starting learning cycle: {run_id}")

            # Step 1: Collect and analyze usage patterns
            patterns = self.usage_learner.get_usage_patterns(min_confidence=0.4)
            logger.info(f"Analyzed {len(patterns)} usage patterns")

            # Step 2: Identify performance trends
            trends = await self._identify_performance_trends()
            logger.info(f"Identified {len(trends)} performance trends")

            # Step 3: Discover new insights
            insights = await self._discover_insights(patterns, trends)
            logger.info(f"Discovered {len(insights)} new insights")

            # Step 4: Generate optimization recommendations
            recommendations = self.optimizer.generate_optimization_recommendations()
            logger.info(f"Generated {len(recommendations)} recommendations")

            # Step 5: Update system health metrics
            health_score = await self._update_system_health_metrics()
            logger.info(f"System health score: {health_score:.2f}")

            # Step 6: Execute automated actions
            actions_executed = await self._execute_automated_actions(insights, recommendations)
            logger.info(f"Executed {actions_executed} automated actions")

            # Step 7: Store insights and trends
            await self._store_learning_results(insights, trends)

            # Complete the run
            end_time = datetime.now()
            self._complete_pipeline_run(
                run_id, end_time, 'completed',
                len(insights), len(trends), len(recommendations)
            )

            self.last_learning_run = end_time
            logger.info(f"Learning cycle {run_id} completed successfully")

        except Exception as e:
            logger.error(f"Learning cycle {run_id} failed: {e}")
            self._complete_pipeline_run(run_id, datetime.now(), 'failed', error=str(e))

    async def _identify_performance_trends(self) -> List[PerformanceTrend]:
        """Identify performance trends across templates and system."""

        trends = []

        try:
            cursor = self.db.conn.cursor()

            # Get all templates that have execution data
            cursor.execute('''
                SELECT DISTINCT template_name
                FROM workflow_executions
                WHERE start_time > datetime('now', '-' || ? || ' days')
            ''', (self.trend_analysis_window,))

            templates = [row[0] for row in cursor.fetchall()]

            # Analyze trends for each template
            for template_name in templates:
                template_trends = await self._analyze_template_trends(template_name)
                trends.extend(template_trends)

            # Analyze system-wide trends
            system_trends = await self._analyze_system_trends()
            trends.extend(system_trends)

        except Exception as e:
            logger.error(f"Failed to identify performance trends: {e}")

        return trends

    async def _analyze_template_trends(self, template_name: str) -> List[PerformanceTrend]:
        """Analyze performance trends for a specific template."""

        trends = []

        try:
            cursor = self.db.conn.cursor()

            # Get daily metrics for the template
            cursor.execute('''
                SELECT DATE(start_time) as day,
                       AVG(execution_time_seconds) as avg_time,
                       AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                       COUNT(*) as executions
                FROM workflow_executions
                WHERE template_name = ?
                AND start_time > datetime('now', '-' || ? || ' days')
                GROUP BY DATE(start_time)
                ORDER BY day
            ''', (template_name, self.trend_analysis_window))

            daily_data = cursor.fetchall()

            if len(daily_data) < self.min_data_points_for_trend:
                return trends

            # Analyze execution time trend
            time_trend = self._calculate_trend(
                [(datetime.fromisoformat(row[0]), row[1]) for row in daily_data if row[1]]
            )
            if time_trend:
                trends.append(PerformanceTrend(
                    metric_name='execution_time',
                    template_name=template_name,
                    trend_direction=time_trend['direction'],
                    change_percentage=time_trend['change_percentage'],
                    confidence=time_trend['confidence'],
                    time_period_days=self.trend_analysis_window,
                    data_points=[(datetime.fromisoformat(row[0]), row[1]) for row in daily_data if row[1]]
                ))

            # Analyze success rate trend
            success_trend = self._calculate_trend(
                [(datetime.fromisoformat(row[0]), row[2]) for row in daily_data if row[2] is not None]
            )
            if success_trend:
                trends.append(PerformanceTrend(
                    metric_name='success_rate',
                    template_name=template_name,
                    trend_direction=success_trend['direction'],
                    change_percentage=success_trend['change_percentage'],
                    confidence=success_trend['confidence'],
                    time_period_days=self.trend_analysis_window,
                    data_points=[(datetime.fromisoformat(row[0]), row[2]) for row in daily_data if row[2] is not None]
                ))

        except Exception as e:
            logger.error(f"Failed to analyze template trends for {template_name}: {e}")

        return trends

    async def _analyze_system_trends(self) -> List[PerformanceTrend]:
        """Analyze system-wide performance trends."""

        trends = []

        try:
            cursor = self.db.conn.cursor()

            # Get system-wide daily metrics
            cursor.execute('''
                SELECT DATE(start_time) as day,
                       AVG(execution_time_seconds) as avg_time,
                       AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                       COUNT(*) as total_executions,
                       COUNT(DISTINCT template_name) as unique_templates
                FROM workflow_executions
                WHERE start_time > datetime('now', '-' || ? || ' days')
                GROUP BY DATE(start_time)
                ORDER BY day
            ''', (self.trend_analysis_window,))

            daily_data = cursor.fetchall()

            if len(daily_data) < self.min_data_points_for_trend:
                return trends

            # System execution time trend
            time_trend = self._calculate_trend(
                [(datetime.fromisoformat(row[0]), row[1]) for row in daily_data if row[1]]
            )
            if time_trend:
                trends.append(PerformanceTrend(
                    metric_name='system_execution_time',
                    template_name=None,
                    trend_direction=time_trend['direction'],
                    change_percentage=time_trend['change_percentage'],
                    confidence=time_trend['confidence'],
                    time_period_days=self.trend_analysis_window,
                    data_points=[(datetime.fromisoformat(row[0]), row[1]) for row in daily_data if row[1]]
                ))

            # System success rate trend
            success_trend = self._calculate_trend(
                [(datetime.fromisoformat(row[0]), row[2]) for row in daily_data if row[2] is not None]
            )
            if success_trend:
                trends.append(PerformanceTrend(
                    metric_name='system_success_rate',
                    template_name=None,
                    trend_direction=success_trend['direction'],
                    change_percentage=success_trend['change_percentage'],
                    confidence=success_trend['confidence'],
                    time_period_days=self.trend_analysis_window,
                    data_points=[(datetime.fromisoformat(row[0]), row[2]) for row in daily_data if row[2] is not None]
                ))

        except Exception as e:
            logger.error(f"Failed to analyze system trends: {e}")

        return trends

    def _calculate_trend(self, data_points: List[Tuple[datetime, float]]) -> Optional[Dict[str, Any]]:
        """Calculate trend direction and magnitude from data points."""

        if len(data_points) < 3:
            return None

        try:
            # Sort by date
            data_points.sort(key=lambda x: x[0])

            # Extract values
            values = [point[1] for point in data_points]

            # Calculate linear regression to determine trend
            n = len(values)
            x_values = list(range(n))

            # Simple linear regression
            mean_x = statistics.mean(x_values)
            mean_y = statistics.mean(values)

            numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, values))
            denominator = sum((x - mean_x) ** 2 for x in x_values)

            if denominator == 0:
                return None

            slope = numerator / denominator

            # Calculate correlation coefficient for confidence
            std_x = statistics.stdev(x_values) if n > 1 else 0
            std_y = statistics.stdev(values) if n > 1 else 0

            correlation = 0
            if std_x > 0 and std_y > 0:
                correlation = numerator / (n * std_x * std_y)

            # Determine trend direction and magnitude
            first_value = values[0]
            last_value = values[-1]

            if first_value == 0:
                change_percentage = 0
            else:
                change_percentage = ((last_value - first_value) / first_value) * 100

            if abs(change_percentage) < 5:  # Less than 5% change
                direction = 'stable'
            elif change_percentage > 0:
                direction = 'improving' if slope > 0 else 'degrading'
            else:
                direction = 'degrading' if slope < 0 else 'improving'

            confidence = min(0.9, abs(correlation))  # Cap confidence at 90%

            return {
                'direction': direction,
                'change_percentage': abs(change_percentage),
                'confidence': confidence,
                'slope': slope
            }

        except Exception as e:
            logger.error(f"Failed to calculate trend: {e}")
            return None

    async def _discover_insights(self,
                               patterns: List[UsagePattern],
                               trends: List[PerformanceTrend]) -> List[LearningInsight]:
        """Discover actionable insights from patterns and trends."""

        insights = []

        try:
            # Insight 1: Performance degradation alerts
            for trend in trends:
                if (trend.trend_direction == 'degrading' and
                    trend.change_percentage > self.performance_degradation_threshold * 100 and
                    trend.confidence > 0.6):

                    insight = self._create_performance_degradation_insight(trend)
                    if insight:
                        insights.append(insight)

            # Insight 2: Template optimization opportunities
            for pattern in patterns:
                if pattern.confidence_score > self.insight_confidence_threshold:
                    optimization_insight = self._create_optimization_insight(pattern)
                    if optimization_insight:
                        insights.append(optimization_insight)

            # Insight 3: Usage pattern anomalies
            anomaly_insights = await self._detect_usage_anomalies(patterns)
            insights.extend(anomaly_insights)

            # Insight 4: Resource utilization insights
            resource_insights = await self._analyze_resource_utilization()
            insights.extend(resource_insights)

            # Filter by confidence threshold
            insights = [i for i in insights if i.confidence_score >= self.insight_confidence_threshold]

        except Exception as e:
            logger.error(f"Failed to discover insights: {e}")

        return insights

    def _create_performance_degradation_insight(self, trend: PerformanceTrend) -> Optional[LearningInsight]:
        """Create insight for performance degradation."""

        target_name = trend.template_name or 'system'

        return LearningInsight(
            insight_id=f"perf_degradation_{target_name}_{datetime.now().strftime('%Y%m%d')}",
            insight_type='performance_degradation',
            title=f"Performance degradation detected in {target_name}",
            description=f"{trend.metric_name} has degraded by {trend.change_percentage:.1f}% "
                       f"over the last {trend.time_period_days} days.",
            evidence={
                'trend_direction': trend.trend_direction,
                'change_percentage': trend.change_percentage,
                'confidence': trend.confidence,
                'metric_name': trend.metric_name,
                'data_points': len(trend.data_points)
            },
            confidence_score=trend.confidence,
            impact_assessment='high' if trend.change_percentage > 25 else 'medium',
            actionable_recommendations=[
                f"Investigate recent changes to {target_name}",
                "Review resource allocation and optimization settings",
                "Check for external dependencies causing slowdowns",
                "Consider scaling resources or optimizing workflows"
            ],
            affected_templates=[trend.template_name] if trend.template_name else [],
            discovered_at=datetime.now()
        )

    def _create_optimization_insight(self, pattern: UsagePattern) -> Optional[LearningInsight]:
        """Create insight for optimization opportunities."""

        if pattern.success_rate < 0.9 or pattern.avg_execution_time > 300:
            template_name = pattern.pattern_id.replace('template_usage_', '').replace('_', '-')

            return LearningInsight(
                insight_id=f"optimization_opportunity_{template_name}_{datetime.now().strftime('%Y%m%d')}",
                insight_type='optimization_opportunity',
                title=f"Optimization opportunity for {template_name}",
                description=f"Template shows success rate of {pattern.success_rate:.1%} "
                           f"and average execution time of {pattern.avg_execution_time:.1f}s. "
                           f"Optimization could improve performance.",
                evidence={
                    'success_rate': pattern.success_rate,
                    'avg_execution_time': pattern.avg_execution_time,
                    'frequency': pattern.frequency,
                    'bottlenecks': pattern.bottlenecks,
                    'optimization_suggestions': pattern.optimization_suggestions
                },
                confidence_score=pattern.confidence_score,
                impact_assessment=self._assess_optimization_impact(pattern),
                actionable_recommendations=pattern.optimization_suggestions,
                affected_templates=[template_name],
                discovered_at=datetime.now()
            )

        return None

    def _assess_optimization_impact(self, pattern: UsagePattern) -> str:
        """Assess the impact level of an optimization opportunity."""

        if pattern.success_rate < 0.7 or pattern.avg_execution_time > 600:
            return 'high'
        elif pattern.success_rate < 0.85 or pattern.avg_execution_time > 300:
            return 'medium'
        else:
            return 'low'

    async def _detect_usage_anomalies(self, patterns: List[UsagePattern]) -> List[LearningInsight]:
        """Detect anomalous usage patterns."""

        insights = []

        try:
            # Look for unusual patterns
            for pattern in patterns:
                template_name = pattern.pattern_id.replace('template_usage_', '').replace('_', '-')

                # Unusual failure rate
                if pattern.frequency > 10 and pattern.success_rate < 0.5:
                    insights.append(LearningInsight(
                        insight_id=f"anomaly_high_failure_{template_name}_{datetime.now().strftime('%Y%m%d')}",
                        insight_type='usage_anomaly',
                        title=f"High failure rate detected for {template_name}",
                        description=f"Template has unusually high failure rate of {1-pattern.success_rate:.1%} "
                                   f"across {pattern.frequency} executions.",
                        evidence={'pattern': asdict(pattern)},
                        confidence_score=pattern.confidence_score,
                        impact_assessment='high',
                        actionable_recommendations=[
                            "Investigate common failure causes",
                            "Review template configuration and dependencies",
                            "Consider disabling template until issues are resolved"
                        ],
                        affected_templates=[template_name],
                        discovered_at=datetime.now()
                    ))

                # Unusually long execution times
                if pattern.avg_execution_time > 1800:  # 30 minutes
                    insights.append(LearningInsight(
                        insight_id=f"anomaly_long_execution_{template_name}_{datetime.now().strftime('%Y%m%d')}",
                        insight_type='usage_anomaly',
                        title=f"Unusually long execution times for {template_name}",
                        description=f"Template takes an average of {pattern.avg_execution_time/60:.1f} minutes "
                                   f"to execute, which is significantly longer than expected.",
                        evidence={'pattern': asdict(pattern)},
                        confidence_score=pattern.confidence_score,
                        impact_assessment='medium',
                        actionable_recommendations=[
                            "Profile template execution to identify bottlenecks",
                            "Consider breaking template into smaller components",
                            "Review resource allocation and parallel execution opportunities"
                        ],
                        affected_templates=[template_name],
                        discovered_at=datetime.now()
                    ))

        except Exception as e:
            logger.error(f"Failed to detect usage anomalies: {e}")

        return insights

    async def _analyze_resource_utilization(self) -> List[LearningInsight]:
        """Analyze resource utilization patterns."""

        insights = []

        try:
            cursor = self.db.conn.cursor()

            # Get recent execution data
            cursor.execute('''
                SELECT template_name, AVG(execution_time_seconds) as avg_time,
                       COUNT(*) as execution_count
                FROM workflow_executions
                WHERE start_time > datetime('now', '-7 days')
                GROUP BY template_name
                HAVING COUNT(*) >= 5
                ORDER BY avg_time DESC
            ''')

            template_data = cursor.fetchall()

            # Identify resource-intensive templates
            if template_data:
                slowest_templates = template_data[:3]  # Top 3 slowest

                for template_name, avg_time, count in slowest_templates:
                    if avg_time > 600:  # More than 10 minutes
                        insights.append(LearningInsight(
                            insight_id=f"resource_intensive_{template_name}_{datetime.now().strftime('%Y%m%d')}",
                            insight_type='resource_utilization',
                            title=f"Resource-intensive template: {template_name}",
                            description=f"Template {template_name} consumes significant resources with "
                                       f"average execution time of {avg_time/60:.1f} minutes.",
                            evidence={
                                'avg_execution_time': avg_time,
                                'execution_count': count,
                                'resource_category': 'high'
                            },
                            confidence_score=0.8,
                            impact_assessment='medium',
                            actionable_recommendations=[
                                "Consider resource scaling for this template",
                                "Implement resource pooling and caching",
                                "Review template for optimization opportunities"
                            ],
                            affected_templates=[template_name],
                            discovered_at=datetime.now()
                        ))

        except Exception as e:
            logger.error(f"Failed to analyze resource utilization: {e}")

        return insights

    async def _update_system_health_metrics(self) -> float:
        """Update daily system health metrics."""

        try:
            cursor = self.db.conn.cursor()
            today = datetime.now().date()

            # Calculate daily metrics
            cursor.execute('''
                SELECT AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                       AVG(execution_time_seconds) as avg_time,
                       COUNT(*) as total_executions,
                       COUNT(DISTINCT template_name) as unique_templates
                FROM workflow_executions
                WHERE DATE(start_time) = ?
            ''', (today,))

            daily_stats = cursor.fetchone()

            if daily_stats and daily_stats[2] > 0:  # Have executions today
                success_rate = daily_stats[0] or 0
                avg_time = daily_stats[1] or 0
                total_executions = daily_stats[2]
                unique_templates = daily_stats[3]

                # Calculate error rate
                error_rate = 1.0 - success_rate

                # Calculate health score (simplified)
                health_score = (
                    success_rate * 0.4 +  # Success rate weight: 40%
                    min(1.0, 300 / max(avg_time, 1)) * 0.3 +  # Speed factor: 30%
                    min(1.0, total_executions / 10) * 0.2 +  # Usage factor: 20%
                    min(1.0, unique_templates / 5) * 0.1  # Diversity factor: 10%
                )

                # Store metrics
                cursor.execute('''
                    INSERT OR REPLACE INTO system_health_metrics (
                        metric_date, overall_success_rate, avg_execution_time,
                        total_executions, unique_templates_used, error_rate,
                        health_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (today, success_rate, avg_time, total_executions,
                      unique_templates, error_rate, health_score))

                self.db.conn.commit()
                return health_score
            else:
                return 0.5  # Default health score when no data

        except Exception as e:
            logger.error(f"Failed to update system health metrics: {e}")
            return 0.5

    async def _execute_automated_actions(self,
                                       insights: List[LearningInsight],
                                       recommendations: List[OptimizationRecommendation]) -> int:
        """Execute automated actions based on insights and recommendations."""

        actions_executed = 0

        try:
            for insight in insights:
                # Auto-execute low-effort, high-impact actions
                if (insight.impact_assessment == 'high' and
                    insight.confidence_score > 0.8 and
                    insight.insight_type in ['performance_degradation', 'usage_anomaly']):

                    action_executed = await self._execute_insight_action(insight)
                    if action_executed:
                        actions_executed += 1

            for recommendation in recommendations:
                # Auto-execute certain types of recommendations
                if (recommendation.effort_level == 'low' and
                    recommendation.impact_level in ['medium', 'high'] and
                    recommendation.priority_score > 70):

                    action_executed = await self._execute_recommendation_action(recommendation)
                    if action_executed:
                        actions_executed += 1

        except Exception as e:
            logger.error(f"Failed to execute automated actions: {e}")

        return actions_executed

    async def _execute_insight_action(self, insight: LearningInsight) -> bool:
        """Execute automated action for an insight."""

        try:
            action_id = f"action_{insight.insight_id}_{uuid.uuid4().hex[:8]}"

            # Example automated actions
            if insight.insight_type == 'performance_degradation':
                # Could trigger alerting, resource scaling, etc.
                action_description = f"Performance alert sent for {insight.title}"

            elif insight.insight_type == 'usage_anomaly':
                # Could trigger investigation, temporary disabling, etc.
                action_description = f"Investigation triggered for {insight.title}"

            else:
                return False

            # Log the action
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO automated_actions (
                    action_id, action_type, target_type, target_id,
                    action_description, trigger_insight_id, execution_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                action_id, 'insight_response', 'system', None,
                action_description, insight.insight_id, 'completed'
            ))
            self.db.conn.commit()

            logger.info(f"Executed automated action: {action_description}")
            return True

        except Exception as e:
            logger.error(f"Failed to execute insight action: {e}")
            return False

    async def _execute_recommendation_action(self, recommendation: OptimizationRecommendation) -> bool:
        """Execute automated action for a recommendation."""

        try:
            # For now, just log the recommendation - in practice, could apply optimizations
            action_id = f"action_{recommendation.id}_{uuid.uuid4().hex[:8]}"
            action_description = f"Optimization recommendation logged: {recommendation.title}"

            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO automated_actions (
                    action_id, action_type, target_type, target_id,
                    action_description, execution_status
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                action_id, 'optimization_recommendation', 'template',
                recommendation.target_id, action_description, 'completed'
            ))
            self.db.conn.commit()

            return True

        except Exception as e:
            logger.error(f"Failed to execute recommendation action: {e}")
            return False

    async def _store_learning_results(self,
                                    insights: List[LearningInsight],
                                    trends: List[PerformanceTrend]):
        """Store discovered insights and trends."""

        try:
            cursor = self.db.conn.cursor()

            # Store insights
            for insight in insights:
                cursor.execute('''
                    INSERT OR REPLACE INTO learning_insights (
                        insight_id, insight_type, title, description, evidence,
                        confidence_score, impact_assessment, actionable_recommendations,
                        affected_templates, discovered_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    insight.insight_id, insight.insight_type, insight.title,
                    insight.description, json.dumps(insight.evidence),
                    insight.confidence_score, insight.impact_assessment,
                    json.dumps(insight.actionable_recommendations),
                    json.dumps(insight.affected_templates), insight.discovered_at
                ))

            # Store trends
            for trend in trends:
                trend_id = f"trend_{trend.metric_name}_{trend.template_name or 'system'}_{datetime.now().strftime('%Y%m%d')}"
                cursor.execute('''
                    INSERT OR REPLACE INTO performance_trends (
                        trend_id, metric_name, template_name, trend_direction,
                        change_percentage, confidence, time_period_days, data_points
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trend_id, trend.metric_name, trend.template_name,
                    trend.trend_direction, trend.change_percentage, trend.confidence,
                    trend.time_period_days, json.dumps([(dp[0].isoformat(), dp[1]) for dp in trend.data_points])
                ))

            self.db.conn.commit()

        except Exception as e:
            logger.error(f"Failed to store learning results: {e}")

    def _start_pipeline_run(self, run_id: str, start_time: datetime):
        """Record the start of a pipeline run."""

        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO learning_pipeline_runs (run_id, start_time, status)
                VALUES (?, ?, ?)
            ''', (run_id, start_time, 'running'))
            self.db.conn.commit()

        except Exception as e:
            logger.error(f"Failed to start pipeline run tracking: {e}")

    def _complete_pipeline_run(self, run_id: str, end_time: datetime, status: str,
                              insights: int = 0, trends: int = 0, recommendations: int = 0, error: str = None):
        """Complete a pipeline run record."""

        try:
            cursor = self.db.conn.cursor()

            summary = {
                'insights_discovered': insights,
                'trends_identified': trends,
                'recommendations_generated': recommendations
            }

            cursor.execute('''
                UPDATE learning_pipeline_runs
                SET end_time = ?, status = ?, insights_discovered = ?,
                    trends_identified = ?, recommendations_generated = ?,
                    execution_summary = ?, error_message = ?
                WHERE run_id = ?
            ''', (end_time, status, insights, trends, recommendations,
                  json.dumps(summary), error, run_id))
            self.db.conn.commit()

        except Exception as e:
            logger.error(f"Failed to complete pipeline run tracking: {e}")

    def generate_learning_report(self, days: int = 7) -> LearningReport:
        """Generate a comprehensive learning report."""

        report_id = f"learning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        generated_at = datetime.now()
        time_period = timedelta(days=days)

        try:
            cursor = self.db.conn.cursor()

            # Get execution statistics
            cursor.execute('''
                SELECT COUNT(*) as total_executions,
                       AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as avg_success_rate
                FROM workflow_executions
                WHERE start_time > datetime('now', '-' || ? || ' days')
            ''', (days,))

            stats = cursor.fetchone()
            total_executions = stats[0] if stats else 0

            # Get recent insights
            cursor.execute('''
                SELECT * FROM learning_insights
                WHERE discovered_at > datetime('now', '-' || ? || ' days')
                ORDER BY confidence_score DESC
            ''', (days,))

            insight_rows = cursor.fetchall()
            new_insights = []
            for row in insight_rows:
                insight = LearningInsight(
                    insight_id=row[1],
                    insight_type=row[2],
                    title=row[3],
                    description=row[4],
                    evidence=json.loads(row[5]),
                    confidence_score=row[6],
                    impact_assessment=row[7],
                    actionable_recommendations=json.loads(row[8]),
                    affected_templates=json.loads(row[9]),
                    discovered_at=datetime.fromisoformat(row[10]),
                    status=row[11]
                )
                new_insights.append(insight)

            # Get recent trends
            cursor.execute('''
                SELECT * FROM performance_trends
                WHERE created_at > datetime('now', '-' || ? || ' days')
                ORDER BY confidence DESC
            ''', (days,))

            trend_rows = cursor.fetchall()
            performance_trends = []
            for row in trend_rows:
                data_points = json.loads(row[8])
                trend = PerformanceTrend(
                    metric_name=row[2],
                    template_name=row[3],
                    trend_direction=row[4],
                    change_percentage=row[5],
                    confidence=row[6],
                    time_period_days=row[7],
                    data_points=[(datetime.fromisoformat(dp[0]), dp[1]) for dp in data_points]
                )
                performance_trends.append(trend)

            # Get optimization recommendations
            optimization_opportunities = self.optimizer.generate_optimization_recommendations(limit=5)

            # Calculate system health score
            cursor.execute('''
                SELECT AVG(health_score) FROM system_health_metrics
                WHERE metric_date > date('now', '-' || ? || ' days')
            ''', (days,))

            health_result = cursor.fetchone()
            system_health_score = health_result[0] if health_result and health_result[0] else 0.5

            # Generate key findings
            key_findings = self._generate_key_findings(new_insights, performance_trends, total_executions)

            # Generate recommended actions
            recommended_actions = self._generate_recommended_actions(new_insights, optimization_opportunities)

            report = LearningReport(
                report_id=report_id,
                generated_at=generated_at,
                time_period=time_period,
                total_executions=total_executions,
                performance_trends=performance_trends,
                new_insights=new_insights,
                optimization_opportunities=optimization_opportunities,
                system_health_score=system_health_score,
                key_findings=key_findings,
                recommended_actions=recommended_actions
            )

            return report

        except Exception as e:
            logger.error(f"Failed to generate learning report: {e}")
            # Return empty report
            return LearningReport(
                report_id=report_id,
                generated_at=generated_at,
                time_period=time_period,
                total_executions=0,
                performance_trends=[],
                new_insights=[],
                optimization_opportunities=[],
                system_health_score=0.5,
                key_findings=[f"Report generation failed: {str(e)}"],
                recommended_actions=["Review system logs for errors"]
            )

    def _generate_key_findings(self,
                             insights: List[LearningInsight],
                             trends: List[PerformanceTrend],
                             total_executions: int) -> List[str]:
        """Generate key findings from insights and trends."""

        findings = []

        findings.append(f"Processed {total_executions} workflow executions in the analysis period")

        if insights:
            high_impact_insights = [i for i in insights if i.impact_assessment == 'high']
            if high_impact_insights:
                findings.append(f"Discovered {len(high_impact_insights)} high-impact issues requiring attention")

            findings.append(f"Total of {len(insights)} insights discovered across all categories")

        if trends:
            degrading_trends = [t for t in trends if t.trend_direction == 'degrading']
            if degrading_trends:
                findings.append(f"Identified {len(degrading_trends)} performance degradation trends")

            improving_trends = [t for t in trends if t.trend_direction == 'improving']
            if improving_trends:
                findings.append(f"Detected {len(improving_trends)} performance improvements")

        if not insights and not trends:
            findings.append("No significant issues or trends detected - system operating normally")

        return findings

    def _generate_recommended_actions(self,
                                    insights: List[LearningInsight],
                                    recommendations: List[OptimizationRecommendation]) -> List[str]:
        """Generate recommended actions from insights and recommendations."""

        actions = []

        # High-priority insights
        high_priority_insights = [i for i in insights
                                if i.impact_assessment == 'high' and i.confidence_score > 0.7]

        for insight in high_priority_insights[:3]:  # Top 3
            actions.append(f"Address {insight.insight_type}: {insight.title}")

        # High-value recommendations
        high_value_recs = sorted(recommendations, key=lambda x: x.priority_score, reverse=True)[:2]

        for rec in high_value_recs:
            actions.append(f"Implement optimization: {rec.title}")

        if not actions:
            actions.append("Continue monitoring system performance and user feedback")

        return actions