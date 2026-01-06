"""
Intelligent Workflow Optimization Engine
Uses machine learning and historical data to optimize workflow execution.
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
import math
from collections import defaultdict

# Add the parent directory to path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.database.db import MoleculeDB
from .usage_learner import UsagePatternLearner, WorkflowMetrics

logger = logging.getLogger(__name__)


@dataclass
class OptimizationRecommendation:
    """Represents a workflow optimization recommendation."""
    id: str
    target_type: str  # template, workflow, system
    target_id: str
    title: str
    description: str
    impact_level: str  # high, medium, low
    effort_level: str  # high, medium, low
    expected_improvement: Dict[str, float]  # metric -> improvement percentage
    implementation_steps: List[str]
    evidence: Dict[str, Any]
    priority_score: float
    created_at: datetime


@dataclass
class WorkflowConfiguration:
    """Optimized workflow configuration."""
    template_name: str
    optimized_variables: Dict[str, Any]
    parallel_execution_groups: List[List[str]]
    resource_allocation: Dict[str, float]
    timeout_settings: Dict[str, int]
    retry_policies: Dict[str, Dict[str, Any]]
    performance_targets: Dict[str, float]
    optimization_confidence: float


class WorkflowOptimizer:
    """Optimizes workflows based on learned patterns and performance data."""

    def __init__(self, db_path: str = None):
        """Initialize the workflow optimizer."""
        self.db = MoleculeDB(db_path) if db_path else MoleculeDB()
        self.usage_learner = UsagePatternLearner(db_path)

        # Optimization parameters
        self.optimization_targets = {
            'execution_time': {'weight': 0.4, 'direction': 'minimize'},
            'success_rate': {'weight': 0.4, 'direction': 'maximize'},
            'resource_efficiency': {'weight': 0.2, 'direction': 'maximize'}
        }

        self.parallel_execution_patterns = {
            'web-dev': {
                'frontend_setup': ['install_deps', 'setup_build'],
                'backend_setup': ['create_api', 'setup_database'],
                'testing_setup': ['unit_tests', 'integration_tests'],
                'deployment_prep': ['docker_build', 'env_config']
            },
            'api-dev': {
                'core_setup': ['project_init', 'dependency_install'],
                'api_development': ['routes', 'middleware', 'auth'],
                'data_layer': ['models', 'migrations', 'seeds'],
                'quality_assurance': ['tests', 'linting', 'docs']
            },
            'testing': {
                'test_setup': ['framework_config', 'test_data'],
                'test_execution': ['unit_tests', 'integration_tests'],
                'test_reporting': ['coverage', 'reports', 'ci_integration']
            }
        }

        logger.info("WorkflowOptimizer initialized")

    def optimize_workflow_configuration(self,
                                      template_name: str,
                                      user_context: Dict[str, Any] = None) -> WorkflowConfiguration:
        """Generate optimized configuration for a workflow."""

        try:
            # Get template insights and patterns
            insights = self.usage_learner.get_template_insights(template_name)
            patterns = self.usage_learner.get_usage_patterns('template_usage', min_confidence=0.6)

            # Find relevant pattern for this template
            relevant_pattern = None
            pattern_id = f"template_usage_{template_name.replace('-', '_')}"
            for pattern in patterns:
                if pattern.pattern_id == pattern_id:
                    relevant_pattern = pattern
                    break

            # Start with base configuration
            config = WorkflowConfiguration(
                template_name=template_name,
                optimized_variables={},
                parallel_execution_groups=[],
                resource_allocation={},
                timeout_settings={},
                retry_policies={},
                performance_targets={},
                optimization_confidence=0.5
            )

            # Optimize variables based on learned patterns
            if relevant_pattern and relevant_pattern.common_variables:
                config.optimized_variables.update(relevant_pattern.common_variables)

            # Apply user context
            if user_context:
                config.optimized_variables.update(user_context.get('variables', {}))

            # Determine parallel execution strategy
            template_category = self._get_template_category(template_name)
            if template_category in self.parallel_execution_patterns:
                config.parallel_execution_groups = self._optimize_parallel_execution(
                    template_category, insights, relevant_pattern
                )

            # Set resource allocation
            config.resource_allocation = self._calculate_resource_allocation(
                template_name, insights, user_context
            )

            # Configure timeouts based on historical data
            config.timeout_settings = self._optimize_timeout_settings(
                template_name, insights
            )

            # Set retry policies
            config.retry_policies = self._generate_retry_policies(
                template_name, relevant_pattern
            )

            # Set performance targets
            config.performance_targets = self._set_performance_targets(
                template_name, insights
            )

            # Calculate optimization confidence
            config.optimization_confidence = self._calculate_optimization_confidence(
                insights, relevant_pattern, user_context
            )

            logger.info(f"Generated optimized configuration for {template_name}")
            return config

        except Exception as e:
            logger.error(f"Failed to optimize workflow configuration: {e}")
            # Return basic configuration
            return WorkflowConfiguration(
                template_name=template_name,
                optimized_variables=user_context.get('variables', {}) if user_context else {},
                parallel_execution_groups=[],
                resource_allocation={'cpu': 1.0, 'memory': 1.0},
                timeout_settings={'default': 1800},  # 30 minutes
                retry_policies={'default': {'max_attempts': 3, 'backoff': 'exponential'}},
                performance_targets={'execution_time': 300, 'success_rate': 0.9},
                optimization_confidence=0.3
            )

    def _get_template_category(self, template_name: str) -> str:
        """Get template category from name."""
        template = self.db.get_template(template_name)
        if template:
            return template.get('category', 'unknown')

        # Infer from name if template not found
        if 'react' in template_name or 'vue' in template_name or 'web' in template_name:
            return 'web-dev'
        elif 'api' in template_name or 'fastapi' in template_name or 'express' in template_name:
            return 'api-dev'
        elif 'test' in template_name or 'pytest' in template_name:
            return 'testing'
        else:
            return 'unknown'

    def _optimize_parallel_execution(self,
                                   category: str,
                                   insights: Dict[str, Any],
                                   pattern: Any) -> List[List[str]]:
        """Optimize parallel execution groups based on category and patterns."""

        if category not in self.parallel_execution_patterns:
            return []

        base_groups = list(self.parallel_execution_patterns[category].values())

        # Adjust based on performance insights
        if insights.get('usage_stats', {}).get('avg_execution_time', 0) > 600:  # > 10 minutes
            # Increase parallelization for slow workflows
            return self._increase_parallelization(base_groups)
        elif insights.get('usage_stats', {}).get('success_rate', 1.0) < 0.8:
            # Reduce parallelization for unreliable workflows
            return self._reduce_parallelization(base_groups)

        return base_groups

    def _increase_parallelization(self, base_groups: List[List[str]]) -> List[List[str]]:
        """Increase parallelization by splitting larger groups."""
        optimized_groups = []
        for group in base_groups:
            if len(group) > 2:
                # Split large groups
                mid = len(group) // 2
                optimized_groups.append(group[:mid])
                optimized_groups.append(group[mid:])
            else:
                optimized_groups.append(group)
        return optimized_groups

    def _reduce_parallelization(self, base_groups: List[List[str]]) -> List[List[str]]:
        """Reduce parallelization by merging groups."""
        if len(base_groups) <= 1:
            return base_groups

        # Merge smaller groups
        optimized_groups = []
        i = 0
        while i < len(base_groups):
            current_group = base_groups[i]
            if i + 1 < len(base_groups) and len(current_group) <= 2 and len(base_groups[i + 1]) <= 2:
                # Merge with next group
                optimized_groups.append(current_group + base_groups[i + 1])
                i += 2
            else:
                optimized_groups.append(current_group)
                i += 1

        return optimized_groups

    def _calculate_resource_allocation(self,
                                     template_name: str,
                                     insights: Dict[str, Any],
                                     user_context: Dict[str, Any] = None) -> Dict[str, float]:
        """Calculate optimal resource allocation."""

        # Base allocation
        allocation = {'cpu': 1.0, 'memory': 1.0, 'disk': 1.0, 'network': 1.0}

        # Adjust based on template type
        if 'docker' in template_name.lower():
            allocation['cpu'] = 1.5
            allocation['memory'] = 2.0
        elif 'build' in template_name.lower() or 'compile' in template_name.lower():
            allocation['cpu'] = 2.0
            allocation['memory'] = 1.5
        elif 'data' in template_name.lower() or 'ml' in template_name.lower():
            allocation['memory'] = 3.0
            allocation['disk'] = 2.0

        # Adjust based on historical performance
        avg_time = insights.get('usage_stats', {}).get('avg_execution_time', 0)
        if avg_time > 600:  # > 10 minutes
            allocation['cpu'] *= 1.5
            allocation['memory'] *= 1.2
        elif avg_time > 1800:  # > 30 minutes
            allocation['cpu'] *= 2.0
            allocation['memory'] *= 1.5

        # Consider user context
        if user_context:
            project_size = user_context.get('project_size', 'medium')
            if project_size == 'large':
                for key in allocation:
                    allocation[key] *= 1.3
            elif project_size == 'small':
                for key in allocation:
                    allocation[key] *= 0.8

        return allocation

    def _optimize_timeout_settings(self,
                                 template_name: str,
                                 insights: Dict[str, Any]) -> Dict[str, int]:
        """Optimize timeout settings based on historical data."""

        # Base timeouts (in seconds)
        timeouts = {
            'default': 1800,     # 30 minutes
            'dependency_install': 900,   # 15 minutes
            'build': 1200,       # 20 minutes
            'test': 600,         # 10 minutes
            'deploy': 1800       # 30 minutes
        }

        # Adjust based on average execution time
        avg_time = insights.get('usage_stats', {}).get('avg_execution_time', 0)
        if avg_time > 0:
            # Set timeout to 3x average time (with minimum and maximum bounds)
            suggested_timeout = max(300, min(7200, int(avg_time * 3)))
            timeouts['default'] = suggested_timeout

            # Adjust other timeouts proportionally
            ratio = suggested_timeout / 1800
            for key in timeouts:
                if key != 'default':
                    timeouts[key] = max(300, int(timeouts[key] * ratio))

        # Template-specific adjustments
        if 'docker' in template_name.lower():
            timeouts['build'] = max(timeouts['build'], 2400)  # At least 40 minutes
        elif 'test' in template_name.lower():
            timeouts['test'] = max(timeouts['test'], 900)     # At least 15 minutes

        return timeouts

    def _generate_retry_policies(self,
                               template_name: str,
                               pattern: Any) -> Dict[str, Dict[str, Any]]:
        """Generate retry policies based on failure patterns."""

        policies = {
            'default': {
                'max_attempts': 3,
                'backoff': 'exponential',
                'base_delay': 10,
                'max_delay': 300
            },
            'network': {
                'max_attempts': 5,
                'backoff': 'exponential',
                'base_delay': 5,
                'max_delay': 120
            },
            'build': {
                'max_attempts': 2,
                'backoff': 'linear',
                'base_delay': 30,
                'max_delay': 60
            }
        }

        # Adjust based on success rate
        if pattern and pattern.success_rate < 0.7:
            # Increase retry attempts for unreliable workflows
            policies['default']['max_attempts'] = 5
            policies['default']['max_delay'] = 600

        # Template-specific adjustments
        if 'docker' in template_name.lower() or 'build' in template_name.lower():
            policies['default']['max_attempts'] = 2  # Docker builds are expensive to retry
        elif 'test' in template_name.lower():
            policies['default']['max_attempts'] = 1  # Tests should be deterministic

        return policies

    def _set_performance_targets(self,
                               template_name: str,
                               insights: Dict[str, Any]) -> Dict[str, float]:
        """Set performance targets based on historical data and best practices."""

        # Default targets
        targets = {
            'execution_time': 300,    # 5 minutes
            'success_rate': 0.95,     # 95%
            'resource_efficiency': 0.8  # 80%
        }

        # Adjust based on template type
        if 'docker' in template_name.lower():
            targets['execution_time'] = 900  # 15 minutes for Docker builds
        elif 'api' in template_name.lower():
            targets['execution_time'] = 180  # 3 minutes for API templates
        elif 'test' in template_name.lower():
            targets['execution_time'] = 120  # 2 minutes for test templates

        # Adjust based on historical performance
        stats = insights.get('usage_stats', {})
        if stats.get('avg_execution_time'):
            # Target 20% improvement over current average
            targets['execution_time'] = max(60, stats['avg_execution_time'] * 0.8)

        if stats.get('success_rate'):
            # Target improvement over current rate (but cap at 95%)
            targets['success_rate'] = min(0.95, stats['success_rate'] + 0.05)

        return targets

    def _calculate_optimization_confidence(self,
                                         insights: Dict[str, Any],
                                         pattern: Any,
                                         user_context: Dict[str, Any] = None) -> float:
        """Calculate confidence in the optimization."""

        confidence = 0.0

        # Data quality factor
        stats = insights.get('usage_stats', {})
        execution_count = stats.get('total_executions', 0)
        if execution_count >= 10:
            confidence += 0.4
        elif execution_count >= 5:
            confidence += 0.2
        elif execution_count >= 2:
            confidence += 0.1

        # Pattern quality factor
        if pattern:
            confidence += pattern.confidence_score * 0.3

        # Success rate factor
        success_rate = stats.get('success_rate', 0)
        if success_rate >= 0.9:
            confidence += 0.2
        elif success_rate >= 0.7:
            confidence += 0.1

        # User context factor
        if user_context and len(user_context.get('variables', {})) > 0:
            confidence += 0.1

        return min(confidence, 1.0)

    def generate_optimization_recommendations(self,
                                            template_name: str = None,
                                            limit: int = 10) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations for templates or the system."""

        recommendations = []

        try:
            # Get all patterns with room for improvement
            patterns = self.usage_learner.get_usage_patterns(min_confidence=0.5)

            for pattern in patterns:
                if template_name and pattern.pattern_id != f"template_usage_{template_name.replace('-', '_')}":
                    continue

                target_template = pattern.pattern_id.replace('template_usage_', '').replace('_', '-')

                # Generate recommendations based on pattern analysis
                if pattern.success_rate < 0.9:
                    rec = self._create_reliability_recommendation(target_template, pattern)
                    if rec:
                        recommendations.append(rec)

                if pattern.avg_execution_time > 300:  # > 5 minutes
                    rec = self._create_performance_recommendation(target_template, pattern)
                    if rec:
                        recommendations.append(rec)

                if pattern.bottlenecks:
                    rec = self._create_bottleneck_recommendation(target_template, pattern)
                    if rec:
                        recommendations.append(rec)

            # Sort by priority score
            recommendations.sort(key=lambda x: x.priority_score, reverse=True)

            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Failed to generate optimization recommendations: {e}")
            return []

    def _create_reliability_recommendation(self,
                                         template_name: str,
                                         pattern: Any) -> Optional[OptimizationRecommendation]:
        """Create recommendation to improve reliability."""

        impact = (0.9 - pattern.success_rate) * 100  # Percentage point improvement
        if impact < 5:  # Less than 5pp improvement
            return None

        return OptimizationRecommendation(
            id=f"reliability_{template_name}_{datetime.now().strftime('%Y%m%d')}",
            target_type='template',
            target_id=template_name,
            title=f"Improve {template_name} reliability",
            description=f"Current success rate is {pattern.success_rate:.1%}. "
                       f"Implementing error handling and validation could improve reliability by {impact:.1f}pp.",
            impact_level='high' if impact > 15 else 'medium',
            effort_level='medium',
            expected_improvement={'success_rate': impact},
            implementation_steps=self._generate_reliability_steps(pattern),
            evidence={
                'current_success_rate': pattern.success_rate,
                'execution_count': pattern.frequency,
                'common_bottlenecks': pattern.bottlenecks
            },
            priority_score=self._calculate_priority_score(impact, 'high', pattern.frequency),
            created_at=datetime.now()
        )

    def _create_performance_recommendation(self,
                                         template_name: str,
                                         pattern: Any) -> Optional[OptimizationRecommendation]:
        """Create recommendation to improve performance."""

        target_time = min(300, pattern.avg_execution_time * 0.7)  # 30% improvement or 5 min max
        improvement = ((pattern.avg_execution_time - target_time) / pattern.avg_execution_time) * 100

        if improvement < 10:  # Less than 10% improvement
            return None

        return OptimizationRecommendation(
            id=f"performance_{template_name}_{datetime.now().strftime('%Y%m%d')}",
            target_type='template',
            target_id=template_name,
            title=f"Optimize {template_name} execution time",
            description=f"Current average execution time is {pattern.avg_execution_time:.1f}s. "
                       f"Optimization could reduce this by {improvement:.1f}% to {target_time:.1f}s.",
            impact_level='high' if improvement > 30 else 'medium',
            effort_level='medium',
            expected_improvement={'execution_time': improvement},
            implementation_steps=self._generate_performance_steps(pattern, template_name),
            evidence={
                'current_avg_time': pattern.avg_execution_time,
                'target_time': target_time,
                'execution_count': pattern.frequency,
                'bottlenecks': pattern.bottlenecks
            },
            priority_score=self._calculate_priority_score(improvement, 'medium', pattern.frequency),
            created_at=datetime.now()
        )

    def _create_bottleneck_recommendation(self,
                                        template_name: str,
                                        pattern: Any) -> Optional[OptimizationRecommendation]:
        """Create recommendation to address bottlenecks."""

        if not pattern.bottlenecks:
            return None

        primary_bottleneck = pattern.bottlenecks[0]

        return OptimizationRecommendation(
            id=f"bottleneck_{template_name}_{datetime.now().strftime('%Y%m%d')}",
            target_type='template',
            target_id=template_name,
            title=f"Address {primary_bottleneck} bottleneck in {template_name}",
            description=f"'{primary_bottleneck}' is a common bottleneck occurring in "
                       f"{len(pattern.bottlenecks)} workflow executions.",
            impact_level='medium',
            effort_level='low' if 'dependency' in primary_bottleneck.lower() else 'medium',
            expected_improvement={'execution_time': 20, 'success_rate': 5},
            implementation_steps=self._generate_bottleneck_steps(primary_bottleneck, template_name),
            evidence={
                'bottleneck': primary_bottleneck,
                'frequency': pattern.frequency,
                'all_bottlenecks': pattern.bottlenecks
            },
            priority_score=self._calculate_priority_score(20, 'medium', pattern.frequency),
            created_at=datetime.now()
        )

    def _generate_reliability_steps(self, pattern: Any) -> List[str]:
        """Generate implementation steps for reliability improvements."""
        steps = [
            "Analyze failure patterns from execution logs",
            "Add comprehensive error handling and validation",
            "Implement health checks and dependency verification"
        ]

        if pattern.bottlenecks:
            for bottleneck in pattern.bottlenecks[:2]:
                if 'dependency' in bottleneck.lower():
                    steps.append("Add dependency availability checks")
                elif 'network' in bottleneck.lower():
                    steps.append("Implement network retry mechanisms")

        steps.append("Add automated testing and rollback capabilities")
        return steps

    def _generate_performance_steps(self, pattern: Any, template_name: str) -> List[str]:
        """Generate implementation steps for performance improvements."""
        steps = []

        if 'docker' in template_name.lower():
            steps.extend([
                "Optimize Dockerfile with multi-stage builds",
                "Use smaller base images",
                "Implement build caching"
            ])
        elif 'node' in template_name.lower() or 'react' in template_name.lower():
            steps.extend([
                "Optimize package.json dependencies",
                "Implement parallel build processes",
                "Use faster package managers (pnpm/yarn)"
            ])
        elif 'python' in template_name.lower():
            steps.extend([
                "Use uv for faster dependency resolution",
                "Implement parallel test execution",
                "Optimize import paths and lazy loading"
            ])

        # Add parallel execution
        steps.append("Implement parallel task execution")
        steps.append("Add resource pooling and caching")

        return steps

    def _generate_bottleneck_steps(self, bottleneck: str, template_name: str) -> List[str]:
        """Generate implementation steps for bottleneck resolution."""
        steps = []

        if 'dependency' in bottleneck.lower():
            steps = [
                "Implement dependency caching",
                "Use faster package mirrors or CDN",
                "Pre-install common dependencies"
            ]
        elif 'build' in bottleneck.lower():
            steps = [
                "Enable parallel build processes",
                "Implement incremental builds",
                "Optimize compiler flags"
            ]
        elif 'test' in bottleneck.lower():
            steps = [
                "Parallelize test execution",
                "Optimize test data setup",
                "Implement test result caching"
            ]
        elif 'network' in bottleneck.lower():
            steps = [
                "Use local mirrors/proxies",
                "Implement connection pooling",
                "Add retry mechanisms with backoff"
            ]
        else:
            steps = [
                "Analyze bottleneck root cause",
                "Implement caching strategies",
                "Optimize resource allocation"
            ]

        return steps

    def _calculate_priority_score(self,
                                impact: float,
                                effort: str,
                                frequency: int) -> float:
        """Calculate priority score for recommendations."""

        # Normalize impact (0-100 scale)
        impact_score = min(impact / 50, 1.0)  # Cap at 50% improvement

        # Effort modifier
        effort_modifiers = {'low': 1.0, 'medium': 0.7, 'high': 0.4}
        effort_score = effort_modifiers.get(effort, 0.7)

        # Frequency modifier (more frequent issues get higher priority)
        frequency_score = min(frequency / 20, 1.0)  # Cap at 20 executions

        return impact_score * effort_score * frequency_score * 100