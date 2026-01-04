"""
Smart Orchestration Engine
AI-driven orchestration that learns from usage patterns and optimizes execution.
"""

import sys
import json
import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time
import uuid
from enum import Enum

# Add the parent directory to path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.database.db import MoleculeDB
from .usage_learner import UsagePatternLearner, WorkflowMetrics
from .workflow_optimizer import WorkflowOptimizer, WorkflowConfiguration

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class ExecutionStep:
    """Represents a single execution step."""
    step_id: str
    name: str
    command: str
    dependencies: List[str]
    timeout: int
    retry_policy: Dict[str, Any]
    resource_requirements: Dict[str, float]
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    output: str = ""
    error: str = ""


@dataclass
class ExecutionPlan:
    """Represents an optimized execution plan."""
    plan_id: str
    template_name: str
    steps: List[ExecutionStep]
    parallel_groups: List[List[str]]  # Step IDs grouped for parallel execution
    estimated_duration: int
    resource_allocation: Dict[str, float]
    optimization_applied: List[str]
    confidence_score: float


@dataclass
class ExecutionResult:
    """Results from workflow execution."""
    execution_id: str
    plan_id: str
    template_name: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime]
    total_duration: Optional[int]
    steps_completed: int
    steps_total: int
    success_rate: float
    performance_metrics: Dict[str, Any]
    errors: List[str]
    optimization_feedback: Dict[str, Any]


class SmartOrchestrationEngine:
    """AI-driven orchestration engine that learns and optimizes."""

    def __init__(self, db_path: str = None, max_parallel_workers: int = 4):
        """Initialize the smart orchestration engine."""
        self.db = MoleculeDB(db_path) if db_path else MoleculeDB()
        self.usage_learner = UsagePatternLearner(db_path)
        self.optimizer = WorkflowOptimizer(db_path)

        self.max_parallel_workers = max_parallel_workers
        self.active_executions: Dict[str, ExecutionResult] = {}
        self.execution_history: List[ExecutionResult] = []

        # Performance prediction models (simplified)
        self.performance_models = {
            'execution_time': self._predict_execution_time,
            'success_rate': self._predict_success_rate,
            'resource_usage': self._predict_resource_usage
        }

        # Initialize orchestration tables
        self._initialize_orchestration_tables()

        logger.info(f"SmartOrchestrationEngine initialized with {max_parallel_workers} workers")

    def _initialize_orchestration_tables(self):
        """Initialize tables for orchestration tracking."""

        orchestration_schema = '''
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

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_execution_plans_template
            ON execution_plans(template_name);
        CREATE INDEX IF NOT EXISTS idx_active_executions_status
            ON active_executions(status);
        CREATE INDEX IF NOT EXISTS idx_execution_step_results_execution
            ON execution_step_results(execution_id);
        CREATE INDEX IF NOT EXISTS idx_performance_predictions_template
            ON performance_predictions(template_name, prediction_type);
        '''

        try:
            self.db._execute_script(orchestration_schema)
            logger.info("Orchestration tables initialized")
        except Exception as e:
            logger.error(f"Failed to initialize orchestration tables: {e}")

    def create_execution_plan(self,
                            template_name: str,
                            user_variables: Dict[str, Any] = None,
                            user_context: Dict[str, Any] = None) -> ExecutionPlan:
        """Create an optimized execution plan for a template."""

        try:
            plan_id = f"plan_{template_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Get optimized configuration
            context = user_context or {}
            if user_variables:
                context['variables'] = user_variables

            config = self.optimizer.optimize_workflow_configuration(template_name, context)

            # Generate execution steps
            steps = self._generate_execution_steps(template_name, config, user_variables)

            # Create parallel execution groups
            parallel_groups = self._create_parallel_groups(steps, config.parallel_execution_groups)

            # Estimate execution duration
            estimated_duration = self._estimate_execution_duration(steps, parallel_groups)

            # Create execution plan
            plan = ExecutionPlan(
                plan_id=plan_id,
                template_name=template_name,
                steps=steps,
                parallel_groups=parallel_groups,
                estimated_duration=estimated_duration,
                resource_allocation=config.resource_allocation,
                optimization_applied=self._get_applied_optimizations(config),
                confidence_score=config.optimization_confidence
            )

            # Store plan in database
            self._store_execution_plan(plan, config)

            logger.info(f"Created execution plan {plan_id} for {template_name}")
            return plan

        except Exception as e:
            logger.error(f"Failed to create execution plan: {e}")
            raise

    def _generate_execution_steps(self,
                                template_name: str,
                                config: WorkflowConfiguration,
                                user_variables: Dict[str, Any] = None) -> List[ExecutionStep]:
        """Generate execution steps based on template and configuration."""

        # This is a simplified implementation - in practice, this would
        # parse the template files and generate actual execution commands

        template = self.db.get_template(template_name)
        if not template:
            raise ValueError(f"Template {template_name} not found")

        category = template.get('category', 'unknown')
        tech_stack = template.get('tech_stack', '')

        steps = []
        step_counter = 1

        # Common initialization steps
        init_step = ExecutionStep(
            step_id=f"step_{step_counter:03d}",
            name="Initialize project structure",
            command=f"template_init {template_name}",
            dependencies=[],
            timeout=config.timeout_settings.get('default', 300),
            retry_policy=config.retry_policies.get('default', {}),
            resource_requirements={'cpu': 0.5, 'memory': 0.5}
        )
        steps.append(init_step)
        step_counter += 1

        # Category-specific steps
        if category == 'web-dev':
            steps.extend(self._generate_web_dev_steps(step_counter, config, tech_stack))
            step_counter += len(steps) - 1
        elif category == 'api-dev':
            steps.extend(self._generate_api_dev_steps(step_counter, config, tech_stack))
            step_counter += len(steps) - 1
        elif category == 'testing':
            steps.extend(self._generate_testing_steps(step_counter, config))
            step_counter += len(steps) - 1
        elif category == 'deployment':
            steps.extend(self._generate_deployment_steps(step_counter, config))

        # Apply user variables to commands
        if user_variables:
            for step in steps:
                step.command = self._substitute_variables(step.command, user_variables)

        return steps

    def _generate_web_dev_steps(self,
                              start_counter: int,
                              config: WorkflowConfiguration,
                              tech_stack: str) -> List[ExecutionStep]:
        """Generate steps for web development templates."""

        steps = []
        counter = start_counter

        if 'react' in tech_stack or 'node' in tech_stack:
            # Frontend setup
            steps.append(ExecutionStep(
                step_id=f"step_{counter:03d}",
                name="Install frontend dependencies",
                command="npm install",
                dependencies=[f"step_{start_counter-1:03d}"],
                timeout=config.timeout_settings.get('dependency_install', 900),
                retry_policy=config.retry_policies.get('network', {}),
                resource_requirements={'cpu': 1.0, 'memory': 1.0, 'network': 1.0}
            ))
            counter += 1

            # Backend setup (if full-stack)
            if 'fullstack' in tech_stack or 'node' in tech_stack:
                steps.append(ExecutionStep(
                    step_id=f"step_{counter:03d}",
                    name="Setup backend API",
                    command="create_api_structure",
                    dependencies=[f"step_{start_counter-1:03d}"],
                    timeout=config.timeout_settings.get('default', 300),
                    retry_policy=config.retry_policies.get('default', {}),
                    resource_requirements={'cpu': 0.5, 'memory': 0.5}
                ))
                counter += 1

            # Build process
            steps.append(ExecutionStep(
                step_id=f"step_{counter:03d}",
                name="Build application",
                command="npm run build",
                dependencies=[f"step_{start_counter:03d}"],
                timeout=config.timeout_settings.get('build', 1200),
                retry_policy=config.retry_policies.get('build', {}),
                resource_requirements={'cpu': 2.0, 'memory': 1.5}
            ))
            counter += 1

        return steps

    def _generate_api_dev_steps(self,
                              start_counter: int,
                              config: WorkflowConfiguration,
                              tech_stack: str) -> List[ExecutionStep]:
        """Generate steps for API development templates."""

        steps = []
        counter = start_counter

        # Install dependencies
        if 'python' in tech_stack:
            cmd = "uv sync" if config.optimized_variables.get('use_uv', False) else "pip install -r requirements.txt"
        elif 'node' in tech_stack:
            cmd = "npm install"
        else:
            cmd = "install_dependencies"

        steps.append(ExecutionStep(
            step_id=f"step_{counter:03d}",
            name="Install dependencies",
            command=cmd,
            dependencies=[f"step_{start_counter-1:03d}"],
            timeout=config.timeout_settings.get('dependency_install', 900),
            retry_policy=config.retry_policies.get('network', {}),
            resource_requirements={'cpu': 1.0, 'memory': 1.0, 'network': 1.0}
        ))
        counter += 1

        # Database setup
        steps.append(ExecutionStep(
            step_id=f"step_{counter:03d}",
            name="Setup database",
            command="setup_database",
            dependencies=[f"step_{counter-1:03d}"],
            timeout=config.timeout_settings.get('default', 300),
            retry_policy=config.retry_policies.get('default', {}),
            resource_requirements={'cpu': 0.5, 'memory': 0.8, 'disk': 1.0}
        ))
        counter += 1

        # Run tests
        steps.append(ExecutionStep(
            step_id=f"step_{counter:03d}",
            name="Run API tests",
            command="run_tests",
            dependencies=[f"step_{counter-1:03d}"],
            timeout=config.timeout_settings.get('test', 600),
            retry_policy=config.retry_policies.get('default', {}),
            resource_requirements={'cpu': 1.0, 'memory': 1.0}
        ))

        return steps

    def _generate_testing_steps(self,
                              start_counter: int,
                              config: WorkflowConfiguration) -> List[ExecutionStep]:
        """Generate steps for testing templates."""

        steps = []
        counter = start_counter

        steps.append(ExecutionStep(
            step_id=f"step_{counter:03d}",
            name="Setup test framework",
            command="setup_test_framework",
            dependencies=[f"step_{start_counter-1:03d}"],
            timeout=config.timeout_settings.get('default', 300),
            retry_policy=config.retry_policies.get('default', {}),
            resource_requirements={'cpu': 0.5, 'memory': 0.5}
        ))
        counter += 1

        steps.append(ExecutionStep(
            step_id=f"step_{counter:03d}",
            name="Run test suite",
            command="run_test_suite",
            dependencies=[f"step_{counter-1:03d}"],
            timeout=config.timeout_settings.get('test', 600),
            retry_policy={'max_attempts': 1, 'backoff': 'none'},  # Tests should be deterministic
            resource_requirements={'cpu': 1.5, 'memory': 1.0}
        ))

        return steps

    def _generate_deployment_steps(self,
                                 start_counter: int,
                                 config: WorkflowConfiguration) -> List[ExecutionStep]:
        """Generate steps for deployment templates."""

        steps = []
        counter = start_counter

        steps.append(ExecutionStep(
            step_id=f"step_{counter:03d}",
            name="Build Docker image",
            command="docker_build",
            dependencies=[f"step_{start_counter-1:03d}"],
            timeout=config.timeout_settings.get('build', 1800),
            retry_policy=config.retry_policies.get('build', {}),
            resource_requirements={'cpu': 2.0, 'memory': 2.0, 'disk': 2.0}
        ))
        counter += 1

        steps.append(ExecutionStep(
            step_id=f"step_{counter:03d}",
            name="Deploy application",
            command="deploy_application",
            dependencies=[f"step_{counter-1:03d}"],
            timeout=config.timeout_settings.get('deploy', 1800),
            retry_policy=config.retry_policies.get('default', {}),
            resource_requirements={'cpu': 1.0, 'memory': 1.0, 'network': 1.5}
        ))

        return steps

    def _substitute_variables(self, command: str, variables: Dict[str, Any]) -> str:
        """Substitute user variables in command strings."""
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in command:
                command = command.replace(placeholder, str(value))
        return command

    def _create_parallel_groups(self,
                              steps: List[ExecutionStep],
                              configured_groups: List[List[str]]) -> List[List[str]]:
        """Create parallel execution groups from steps."""

        # Build dependency graph
        step_map = {step.step_id: step for step in steps}

        # If no configured groups, create simple dependency-based groups
        if not configured_groups:
            return self._create_dependency_based_groups(steps)

        # Map configured groups to actual step IDs
        parallel_groups = []
        used_steps = set()

        for group_pattern in configured_groups:
            group = []
            for step in steps:
                if step.step_id in used_steps:
                    continue

                # Match step names to group patterns
                for pattern in group_pattern:
                    if pattern.lower() in step.name.lower() or pattern.lower() in step.command.lower():
                        group.append(step.step_id)
                        used_steps.add(step.step_id)
                        break

            if group:
                parallel_groups.append(group)

        # Add remaining steps as individual groups
        for step in steps:
            if step.step_id not in used_steps:
                parallel_groups.append([step.step_id])

        return parallel_groups

    def _create_dependency_based_groups(self, steps: List[ExecutionStep]) -> List[List[str]]:
        """Create parallel groups based on dependencies."""

        parallel_groups = []
        processed = set()

        # Group steps by dependency level
        levels = {}
        for step in steps:
            level = len(step.dependencies)
            if level not in levels:
                levels[level] = []
            levels[level].append(step.step_id)

        # Each level can be executed in parallel
        for level in sorted(levels.keys()):
            parallel_groups.append(levels[level])

        return parallel_groups

    def _estimate_execution_duration(self,
                                   steps: List[ExecutionStep],
                                   parallel_groups: List[List[str]]) -> int:
        """Estimate total execution duration considering parallelism."""

        total_duration = 0

        for group in parallel_groups:
            # For parallel groups, use the maximum timeout of steps in the group
            group_duration = 0
            for step_id in group:
                step = next(s for s in steps if s.step_id == step_id)
                group_duration = max(group_duration, step.timeout)

            total_duration += group_duration

        return total_duration

    def _get_applied_optimizations(self, config: WorkflowConfiguration) -> List[str]:
        """Get list of optimizations applied to the configuration."""

        optimizations = []

        if config.parallel_execution_groups:
            optimizations.append("parallel_execution")

        if config.resource_allocation.get('cpu', 1.0) > 1.0:
            optimizations.append("cpu_scaling")

        if config.resource_allocation.get('memory', 1.0) > 1.0:
            optimizations.append("memory_scaling")

        if config.optimized_variables:
            optimizations.append("variable_optimization")

        if any(policy.get('max_attempts', 0) > 1 for policy in config.retry_policies.values()):
            optimizations.append("retry_policies")

        return optimizations

    def _store_execution_plan(self, plan: ExecutionPlan, config: WorkflowConfiguration):
        """Store execution plan in database."""

        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO execution_plans (
                    plan_id, template_name, configuration, steps, parallel_groups,
                    estimated_duration, optimization_applied, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plan.plan_id,
                plan.template_name,
                json.dumps(asdict(config)),
                json.dumps([asdict(step) for step in plan.steps]),
                json.dumps(plan.parallel_groups),
                plan.estimated_duration,
                json.dumps(plan.optimization_applied),
                plan.confidence_score
            ))
            self.db.conn.commit()

        except Exception as e:
            logger.error(f"Failed to store execution plan: {e}")

    def execute_plan(self,
                    plan: ExecutionPlan,
                    progress_callback: Callable[[str, float, str], None] = None) -> ExecutionResult:
        """Execute a workflow plan with smart orchestration."""

        execution_id = f"exec_{plan.template_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        start_time = datetime.now()
        result = ExecutionResult(
            execution_id=execution_id,
            plan_id=plan.plan_id,
            template_name=plan.template_name,
            status=ExecutionStatus.RUNNING,
            start_time=start_time,
            end_time=None,
            total_duration=None,
            steps_completed=0,
            steps_total=len(plan.steps),
            success_rate=0.0,
            performance_metrics={},
            errors=[],
            optimization_feedback={}
        )

        # Track active execution
        self.active_executions[execution_id] = result
        self._store_active_execution(result, plan)

        try:
            # Execute steps in parallel groups
            for group_index, group in enumerate(plan.parallel_groups):
                group_start = time.time()

                if len(group) == 1:
                    # Single step execution
                    step_id = group[0]
                    step = next(s for s in plan.steps if s.step_id == step_id)
                    self._execute_step(step, result, progress_callback)
                else:
                    # Parallel execution
                    self._execute_parallel_group(group, plan.steps, result, progress_callback)

                group_duration = time.time() - group_start
                result.performance_metrics[f'group_{group_index}_duration'] = group_duration

                # Update progress
                progress = (group_index + 1) / len(plan.parallel_groups)
                if progress_callback:
                    progress_callback(execution_id, progress, f"Completed group {group_index + 1}")

            # Finalize result
            result.end_time = datetime.now()
            result.total_duration = int((result.end_time - result.start_time).total_seconds())
            result.success_rate = result.steps_completed / result.steps_total
            result.status = ExecutionStatus.SUCCESS if result.steps_completed == result.steps_total else ExecutionStatus.FAILED

            # Generate optimization feedback
            result.optimization_feedback = self._generate_optimization_feedback(result, plan)

            # Record workflow metrics for learning
            metrics = WorkflowMetrics(
                execution_id=execution_id,
                template_name=plan.template_name,
                start_time=result.start_time,
                end_time=result.end_time,
                success=result.status == ExecutionStatus.SUCCESS,
                execution_time=result.total_duration or 0,
                steps_completed=result.steps_completed,
                steps_total=result.steps_total,
                error_messages=result.errors,
                performance_bottlenecks=[],  # Could be extracted from step timings
                resource_usage=result.performance_metrics,
                user_variables={}  # Would need to pass through from original request
            )
            self.usage_learner.record_workflow_execution(metrics)

            logger.info(f"Execution {execution_id} completed with status: {result.status}")

        except Exception as e:
            logger.error(f"Execution {execution_id} failed: {e}")
            result.status = ExecutionStatus.FAILED
            result.errors.append(str(e))
            result.end_time = datetime.now()
            result.total_duration = int((result.end_time - result.start_time).total_seconds())

        finally:
            # Clean up
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

            self.execution_history.append(result)
            self._cleanup_active_execution(execution_id)

        return result

    def _execute_step(self,
                     step: ExecutionStep,
                     result: ExecutionResult,
                     progress_callback: Callable[[str, float, str], None] = None):
        """Execute a single step."""

        step.start_time = datetime.now()
        step.status = ExecutionStatus.RUNNING

        try:
            # This is a simulation - in practice, would execute actual commands
            logger.info(f"Executing step {step.step_id}: {step.name}")

            # Simulate execution time (in practice, would run actual command)
            import random
            execution_time = random.uniform(1, 5)  # 1-5 seconds simulation
            time.sleep(execution_time)

            # Simulate success/failure
            success_probability = 0.9  # 90% success rate for simulation
            if random.random() < success_probability:
                step.status = ExecutionStatus.SUCCESS
                step.output = f"Step {step.name} completed successfully"
                result.steps_completed += 1
            else:
                step.status = ExecutionStatus.FAILED
                step.error = f"Simulated failure in {step.name}"
                result.errors.append(step.error)

        except Exception as e:
            step.status = ExecutionStatus.FAILED
            step.error = str(e)
            result.errors.append(step.error)
        finally:
            step.end_time = datetime.now()
            step_duration = (step.end_time - step.start_time).total_seconds()

            # Store step result
            self._store_step_result(result.execution_id, step, step_duration)

    def _execute_parallel_group(self,
                              group: List[str],
                              steps: List[ExecutionStep],
                              result: ExecutionResult,
                              progress_callback: Callable[[str, float, str], None] = None):
        """Execute a group of steps in parallel."""

        group_steps = [s for s in steps if s.step_id in group]

        with ThreadPoolExecutor(max_workers=min(len(group_steps), self.max_parallel_workers)) as executor:
            futures = {executor.submit(self._execute_step, step, result, progress_callback): step
                      for step in group_steps}

            for future in as_completed(futures):
                step = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Parallel step {step.step_id} failed: {e}")

    def _store_active_execution(self, result: ExecutionResult, plan: ExecutionPlan):
        """Store active execution in database."""

        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO active_executions (
                    execution_id, plan_id, template_name, status, start_time,
                    estimated_end_time, progress_percentage
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.execution_id,
                result.plan_id,
                result.template_name,
                result.status.value,
                result.start_time,
                result.start_time + timedelta(seconds=plan.estimated_duration),
                0.0
            ))
            self.db.conn.commit()

        except Exception as e:
            logger.error(f"Failed to store active execution: {e}")

    def _store_step_result(self, execution_id: str, step: ExecutionStep, duration: float):
        """Store step execution result."""

        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO execution_step_results (
                    execution_id, step_id, step_name, status, start_time, end_time,
                    duration_seconds, output, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                execution_id, step.step_id, step.name, step.status.value,
                step.start_time, step.end_time, duration,
                step.output, step.error
            ))
            self.db.conn.commit()

        except Exception as e:
            logger.error(f"Failed to store step result: {e}")

    def _cleanup_active_execution(self, execution_id: str):
        """Remove completed execution from active tracking."""

        try:
            cursor = self.db.conn.cursor()
            cursor.execute('DELETE FROM active_executions WHERE execution_id = ?', (execution_id,))
            self.db.conn.commit()

        except Exception as e:
            logger.error(f"Failed to cleanup active execution: {e}")

    def _generate_optimization_feedback(self,
                                      result: ExecutionResult,
                                      plan: ExecutionPlan) -> Dict[str, Any]:
        """Generate feedback on optimization effectiveness."""

        feedback = {
            'plan_accuracy': {},
            'optimization_effectiveness': {},
            'recommendations': []
        }

        # Compare actual vs estimated duration
        if result.total_duration and plan.estimated_duration:
            duration_accuracy = 1.0 - abs(result.total_duration - plan.estimated_duration) / plan.estimated_duration
            feedback['plan_accuracy']['duration'] = max(0.0, min(1.0, duration_accuracy))

        # Analyze optimization effectiveness
        for optimization in plan.optimization_applied:
            if optimization == 'parallel_execution':
                # Check if parallel execution was effective
                group_times = [v for k, v in result.performance_metrics.items() if k.startswith('group_')]
                if group_times:
                    avg_group_time = sum(group_times) / len(group_times)
                    feedback['optimization_effectiveness']['parallel_execution'] = {
                        'avg_group_duration': avg_group_time,
                        'groups_count': len(group_times),
                        'estimated_benefit': plan.estimated_duration * 0.3  # Rough estimate
                    }

        # Generate recommendations
        if result.success_rate < 1.0:
            feedback['recommendations'].append("Consider improving error handling and validation")

        if result.total_duration and result.total_duration > plan.estimated_duration * 1.5:
            feedback['recommendations'].append("Execution took significantly longer than estimated - review resource allocation")

        return feedback

    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an execution."""

        if execution_id in self.active_executions:
            result = self.active_executions[execution_id]
            progress = result.steps_completed / result.steps_total

            return {
                'execution_id': execution_id,
                'status': result.status.value,
                'progress': progress,
                'steps_completed': result.steps_completed,
                'steps_total': result.steps_total,
                'start_time': result.start_time.isoformat(),
                'errors': result.errors
            }

        # Check execution history
        for result in self.execution_history:
            if result.execution_id == execution_id:
                return {
                    'execution_id': execution_id,
                    'status': result.status.value,
                    'progress': 1.0 if result.status == ExecutionStatus.SUCCESS else result.steps_completed / result.steps_total,
                    'total_duration': result.total_duration,
                    'success_rate': result.success_rate,
                    'end_time': result.end_time.isoformat() if result.end_time else None
                }

        return None

    def _predict_execution_time(self, template_name: str, context: Dict[str, Any]) -> Tuple[float, float]:
        """Predict execution time for a template (value, confidence)."""

        # Get historical data
        insights = self.usage_learner.get_template_insights(template_name)
        avg_time = insights.get('usage_stats', {}).get('avg_execution_time', 300)

        # Adjust for context (simplified)
        multiplier = 1.0
        if context.get('project_size') == 'large':
            multiplier = 1.5
        elif context.get('project_size') == 'small':
            multiplier = 0.7

        predicted_time = avg_time * multiplier
        confidence = 0.7 if insights.get('usage_stats', {}).get('total_executions', 0) > 5 else 0.3

        return predicted_time, confidence

    def _predict_success_rate(self, template_name: str, context: Dict[str, Any]) -> Tuple[float, float]:
        """Predict success rate for a template (value, confidence)."""

        insights = self.usage_learner.get_template_insights(template_name)
        base_success_rate = insights.get('usage_stats', {}).get('success_rate', 0.8)

        # Adjust for optimizations
        if context.get('optimizations_applied'):
            base_success_rate = min(0.95, base_success_rate + 0.05)

        confidence = 0.8 if insights.get('usage_stats', {}).get('total_executions', 0) > 10 else 0.4

        return base_success_rate, confidence

    def _predict_resource_usage(self, template_name: str, context: Dict[str, Any]) -> Tuple[Dict[str, float], float]:
        """Predict resource usage for a template (usage_dict, confidence)."""

        # Base resource usage prediction
        usage = {'cpu': 1.0, 'memory': 1.0, 'disk': 1.0, 'network': 0.5}

        # Template-specific adjustments
        if 'docker' in template_name.lower():
            usage.update({'cpu': 1.5, 'memory': 2.0, 'disk': 2.0})
        elif 'build' in template_name.lower():
            usage.update({'cpu': 2.0, 'memory': 1.5})

        confidence = 0.6  # Medium confidence for resource prediction

        return usage, confidence

    def get_orchestration_insights(self) -> Dict[str, Any]:
        """Get insights about orchestration performance."""

        try:
            insights = {
                'active_executions': len(self.active_executions),
                'total_executions': len(self.execution_history),
                'recent_performance': {},
                'optimization_impact': {},
                'recommendations': []
            }

            if self.execution_history:
                recent_executions = self.execution_history[-10:]  # Last 10 executions

                # Calculate recent performance metrics
                success_rates = [e.success_rate for e in recent_executions]
                durations = [e.total_duration for e in recent_executions if e.total_duration]

                insights['recent_performance'] = {
                    'avg_success_rate': sum(success_rates) / len(success_rates) if success_rates else 0,
                    'avg_duration': sum(durations) / len(durations) if durations else 0,
                    'total_errors': sum(len(e.errors) for e in recent_executions)
                }

                # Analyze optimization impact
                optimized_executions = [e for e in recent_executions
                                      if e.optimization_feedback.get('optimization_effectiveness')]
                if optimized_executions:
                    insights['optimization_impact']['optimized_count'] = len(optimized_executions)
                    insights['optimization_impact']['avg_improvement'] = 'data_available'

            return insights

        except Exception as e:
            logger.error(f"Failed to generate orchestration insights: {e}")
            return {'error': str(e)}