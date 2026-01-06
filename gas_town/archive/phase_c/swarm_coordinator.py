#!/usr/bin/env python3
"""
Gas Town Phase C: Swarm Coordinator System
==========================================

Implements coordinated parallel team system for 20-25 agent scalability.
Provides intelligent work distribution, conflict resolution, and team coordination
for large-scale multi-agent operations.

Key Features:
- Dynamic team formation and load balancing
- Intelligent work distribution algorithms
- Real-time conflict detection and resolution
- Agent capability-based task assignment
- Integration with health monitoring for optimal utilization
- Hierarchical coordination with specialized team leaders
"""

import json
import sqlite3
import logging
import threading
import time
import asyncio
import math
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from pathlib import Path
from contextlib import contextmanager
from collections import defaultdict, deque

# Import Phase C components
from persistent_molecule_state import PersistentMoleculeState, MoleculeState
from enhanced_health_monitor import EnhancedHealthMonitor, HealthLevel, HealthMetrics


class TeamType(Enum):
    """Types of agent teams for different coordination patterns."""
    PARALLEL = "parallel"        # Independent parallel work
    PIPELINE = "pipeline"        # Sequential dependency chain
    MESH = "mesh"               # Complex interdependent work
    SPECIALIST = "specialist"    # Domain-specific expert teams
    EMERGENCY = "emergency"     # Rapid response teams


class WorkloadType(Enum):
    """Categories of work that determine distribution strategy."""
    CPU_INTENSIVE = "cpu_intensive"
    IO_BOUND = "io_bound"
    MEMORY_INTENSIVE = "memory_intensive"
    COORDINATION_HEAVY = "coordination_heavy"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"


class AgentCapability(Enum):
    """Agent capabilities for intelligent task assignment."""
    FRONTEND_DEV = "frontend_dev"
    BACKEND_DEV = "backend_dev"
    DATABASE_OPS = "database_ops"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEVOPS = "devops"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COORDINATION = "coordination"
    ANALYSIS = "analysis"


@dataclass
class AgentProfile:
    """Comprehensive agent profile for optimal task assignment."""
    agent_name: str
    capabilities: List[AgentCapability]
    performance_rating: float  # 0.0 - 1.0 based on historical performance
    current_load: float       # 0.0 - 1.0 current workload
    health_status: HealthLevel
    team_preferences: List[TeamType]
    last_active: str
    specialization_score: Dict[WorkloadType, float]
    collaboration_rating: float  # How well they work in teams
    availability_window: Optional[Tuple[str, str]]  # Time window when available

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['capabilities'] = [cap.value for cap in self.capabilities]
        result['health_status'] = self.health_status.value
        result['team_preferences'] = [pref.value for pref in self.team_preferences]
        result['specialization_score'] = {k.value: v for k, v in self.specialization_score.items()}
        return result


@dataclass
class Team:
    """Represents a coordinated team of agents."""
    team_id: str
    team_type: TeamType
    leader_agent: Optional[str]
    member_agents: List[str]
    assigned_workload: List[str]  # Molecule IDs or task IDs
    target_capability: List[AgentCapability]
    estimated_completion: str
    performance_metrics: Dict[str, float]
    coordination_overhead: float  # 0.0 - 1.0, cost of coordination
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['team_type'] = self.team_type.value
        result['target_capability'] = [cap.value for cap in self.target_capability]
        return result


@dataclass
class WorkDistributionPlan:
    """Plan for distributing work across agent teams."""
    plan_id: str
    total_workload: List[str]
    team_assignments: Dict[str, List[str]]  # team_id -> work items
    estimated_completion: str
    load_balance_score: float  # 0.0 - 1.0, how well balanced
    conflict_risk_score: float  # 0.0 - 1.0, risk of conflicts
    coordination_complexity: float  # 0.0 - 1.0, coordination overhead
    created_at: str


class SwarmCoordinator:
    """
    Coordinated parallel team system for large-scale multi-agent operations.

    Manages teams of 20-25 agents through intelligent distribution algorithms,
    conflict resolution, and performance optimization.
    """

    def __init__(self,
                 db_path: str = "/home/ubuntu/.gas_town/swarm_coordinator.db",
                 molecule_state: Optional[PersistentMoleculeState] = None,
                 health_monitor: Optional[EnhancedHealthMonitor] = None,
                 max_agents: int = 25,
                 team_size_range: Tuple[int, int] = (3, 7),
                 coordination_intervals: Optional[Dict[str, float]] = None):
        """
        Initialize the swarm coordination system.

        Args:
            db_path: Path to SQLite database for coordination data
            molecule_state: PersistentMoleculeState for crash recovery integration
            health_monitor: EnhancedHealthMonitor for agent health awareness
            max_agents: Maximum number of agents to coordinate
            team_size_range: (min, max) agents per team
            coordination_intervals: Custom coordination intervals in seconds
        """
        self.db_path = Path(db_path)
        self.molecule_state = molecule_state or PersistentMoleculeState()
        self.health_monitor = health_monitor or EnhancedHealthMonitor()
        self.max_agents = max_agents
        self.min_team_size, self.max_team_size = team_size_range

        # Configuration
        self.intervals = coordination_intervals or {
            'team_rebalancing': 300,     # Rebalance teams every 5 minutes
            'conflict_detection': 60,    # Check for conflicts every minute
            'performance_assessment': 180, # Assess team performance every 3 minutes
            'workload_distribution': 120  # Redistribute work every 2 minutes
        }

        # Thread-safe coordination state
        self._lock = threading.RLock()
        self._coordination_active = False
        self._coordination_threads: Dict[str, threading.Thread] = {}

        # In-memory coordination state
        self._agent_profiles: Dict[str, AgentProfile] = {}
        self._active_teams: Dict[str, Team] = {}
        self._work_queue: deque = deque()
        self._conflict_registry: Dict[str, Dict[str, Any]] = {}

        # Performance tracking
        self._performance_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._team_formation_algorithms: Dict[TeamType, Callable] = {}

        # Initialize components
        self._init_database()
        self._init_logging()
        self._register_team_formation_algorithms()

        logging.info(f"SwarmCoordinator initialized for {max_agents} agents")

    def _init_database(self) -> None:
        """Initialize SQLite database with swarm coordination tables."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # Agent profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_profiles (
                    agent_name TEXT PRIMARY KEY,
                    capabilities TEXT NOT NULL,
                    performance_rating REAL NOT NULL DEFAULT 0.5,
                    current_load REAL NOT NULL DEFAULT 0.0,
                    health_status TEXT NOT NULL DEFAULT 'healthy',
                    team_preferences TEXT NOT NULL,
                    last_active TEXT NOT NULL,
                    specialization_score TEXT NOT NULL,
                    collaboration_rating REAL NOT NULL DEFAULT 0.5,
                    availability_window TEXT,
                    updated_at REAL NOT NULL DEFAULT (julianday('now'))
                )
            """)

            # Teams table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    team_id TEXT PRIMARY KEY,
                    team_type TEXT NOT NULL,
                    leader_agent TEXT,
                    member_agents TEXT NOT NULL,
                    assigned_workload TEXT NOT NULL,
                    target_capability TEXT NOT NULL,
                    estimated_completion TEXT,
                    performance_metrics TEXT NOT NULL,
                    coordination_overhead REAL NOT NULL DEFAULT 0.1,
                    created_at TEXT NOT NULL,
                    updated_at REAL NOT NULL DEFAULT (julianday('now'))
                )
            """)

            # Work distribution plans table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_distribution_plans (
                    plan_id TEXT PRIMARY KEY,
                    total_workload TEXT NOT NULL,
                    team_assignments TEXT NOT NULL,
                    estimated_completion TEXT,
                    load_balance_score REAL NOT NULL,
                    conflict_risk_score REAL NOT NULL,
                    coordination_complexity REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at REAL NOT NULL DEFAULT (julianday('now'))
                )
            """)

            # Conflict registry table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conflict_registry (
                    conflict_id TEXT PRIMARY KEY,
                    conflict_type TEXT NOT NULL,
                    involved_agents TEXT NOT NULL,
                    involved_teams TEXT NOT NULL,
                    conflict_description TEXT NOT NULL,
                    resolution_strategy TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    updated_at REAL NOT NULL DEFAULT (julianday('now'))
                )
            """)

            # Performance history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    performance_metrics TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at REAL NOT NULL DEFAULT (julianday('now'))
                )
            """)

            # Indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_profiles_health
                ON agent_profiles(health_status, current_load)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_teams_type_status
                ON teams(team_type, updated_at DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conflicts_status
                ON conflict_registry(status, created_at DESC)
            """)

            conn.commit()

    def _init_logging(self) -> None:
        """Setup logging for swarm coordination events."""
        log_file = self.db_path.parent / "swarm_coordinator.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    @contextmanager
    def _get_db_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def start_coordination(self) -> None:
        """Start all coordination loops in background threads."""
        with self._lock:
            if self._coordination_active:
                self.logger.warning("Coordination already active")
                return

            self._coordination_active = True

            # Start coordination threads
            coordination_tasks = {
                'team_rebalancing': self._team_rebalancing_loop,
                'conflict_detection': self._conflict_detection_loop,
                'performance_assessment': self._performance_assessment_loop,
                'workload_distribution': self._workload_distribution_loop
            }

            for task_name, task_func in coordination_tasks.items():
                thread = threading.Thread(
                    target=task_func,
                    name=f"swarm_coordinator_{task_name}",
                    daemon=True
                )
                thread.start()
                self._coordination_threads[task_name] = thread

            self.logger.info("Swarm coordination started")

    def stop_coordination(self) -> None:
        """Stop all coordination loops gracefully."""
        with self._lock:
            if not self._coordination_active:
                return

            self._coordination_active = False

            # Wait for threads to finish
            for thread in self._coordination_threads.values():
                thread.join(timeout=5.0)

            self._coordination_threads.clear()
            self.logger.info("Swarm coordination stopped")

    def register_agent(self,
                      agent_name: str,
                      capabilities: List[AgentCapability],
                      specializations: Dict[WorkloadType, float] = None,
                      team_preferences: List[TeamType] = None) -> AgentProfile:
        """
        Register an agent with the swarm coordination system.

        Args:
            agent_name: Unique agent identifier
            capabilities: List of agent capabilities
            specializations: Workload type specialization scores (0.0-1.0)
            team_preferences: Preferred team types

        Returns:
            Created agent profile
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Default specializations based on capabilities
        if specializations is None:
            specializations = self._infer_specializations(capabilities)

        # Default team preferences
        if team_preferences is None:
            team_preferences = [TeamType.PARALLEL, TeamType.PIPELINE]

        # Get initial health status if health monitor available
        health_status = HealthLevel.HEALTHY
        if self.health_monitor:
            agent_metrics = self.health_monitor._agent_metrics.get(agent_name)
            if agent_metrics:
                health_status = agent_metrics.health_level

        profile = AgentProfile(
            agent_name=agent_name,
            capabilities=capabilities,
            performance_rating=0.5,  # Start with neutral rating
            current_load=0.0,
            health_status=health_status,
            team_preferences=team_preferences,
            last_active=timestamp,
            specialization_score=specializations,
            collaboration_rating=0.5,  # Start with neutral collaboration rating
            availability_window=None
        )

        self._agent_profiles[agent_name] = profile
        self._persist_agent_profile(profile)

        self.logger.info(f"Registered agent {agent_name} with capabilities: {[c.value for c in capabilities]}")
        return profile

    def form_team(self,
                  workload: List[str],
                  required_capabilities: List[AgentCapability],
                  team_type: TeamType = TeamType.PARALLEL,
                  preferred_agents: List[str] = None) -> Optional[Team]:
        """
        Form an optimal team for the given workload.

        Args:
            workload: List of work items (molecule IDs, task IDs)
            required_capabilities: Capabilities needed for the work
            team_type: Type of team coordination needed
            preferred_agents: Specific agents to include if available

        Returns:
            Formed team or None if unable to form suitable team
        """
        with self._lock:
            # Use appropriate team formation algorithm
            if team_type in self._team_formation_algorithms:
                algorithm = self._team_formation_algorithms[team_type]
                return algorithm(workload, required_capabilities, preferred_agents)
            else:
                # Default to parallel team formation
                return self._form_parallel_team(workload, required_capabilities, preferred_agents)

    def distribute_work(self, work_items: List[str]) -> WorkDistributionPlan:
        """
        Create an optimal work distribution plan across active teams.

        Args:
            work_items: List of work items to distribute

        Returns:
            Work distribution plan
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        plan_id = f"distribution_{int(time.time())}"

        # Analyze work characteristics
        work_analysis = self._analyze_workload(work_items)

        # Get available teams and their capabilities
        available_teams = self._get_available_teams()

        # Create distribution plan using optimization algorithm
        team_assignments = self._optimize_work_distribution(work_items, available_teams, work_analysis)

        # Calculate plan metrics
        load_balance_score = self._calculate_load_balance(team_assignments)
        conflict_risk_score = self._assess_conflict_risk(team_assignments)
        coordination_complexity = self._calculate_coordination_complexity(team_assignments)

        # Estimate completion time
        estimated_completion = self._estimate_completion_time(team_assignments)

        plan = WorkDistributionPlan(
            plan_id=plan_id,
            total_workload=work_items,
            team_assignments=team_assignments,
            estimated_completion=estimated_completion,
            load_balance_score=load_balance_score,
            conflict_risk_score=conflict_risk_score,
            coordination_complexity=coordination_complexity,
            created_at=timestamp
        )

        self._persist_distribution_plan(plan)
        self.logger.info(f"Created work distribution plan {plan_id} for {len(work_items)} items")
        return plan

    def detect_conflicts(self) -> List[Dict[str, Any]]:
        """
        Detect potential conflicts between agents or teams.

        Returns:
            List of detected conflicts
        """
        conflicts = []

        # Check for resource conflicts
        resource_conflicts = self._detect_resource_conflicts()
        conflicts.extend(resource_conflicts)

        # Check for coordination conflicts
        coordination_conflicts = self._detect_coordination_conflicts()
        conflicts.extend(coordination_conflicts)

        # Check for performance conflicts
        performance_conflicts = self._detect_performance_conflicts()
        conflicts.extend(performance_conflicts)

        # Persist new conflicts
        for conflict in conflicts:
            if conflict['conflict_id'] not in self._conflict_registry:
                self._conflict_registry[conflict['conflict_id']] = conflict
                self._persist_conflict(conflict)

        return conflicts

    def resolve_conflict(self, conflict_id: str, resolution_strategy: str = "auto") -> bool:
        """
        Resolve a detected conflict using specified strategy.

        Args:
            conflict_id: ID of conflict to resolve
            resolution_strategy: Resolution approach ("auto", "rebalance", "reassign", "escalate")

        Returns:
            True if conflict was resolved, False otherwise
        """
        if conflict_id not in self._conflict_registry:
            self.logger.warning(f"Conflict {conflict_id} not found")
            return False

        conflict = self._conflict_registry[conflict_id]

        try:
            if resolution_strategy == "auto":
                success = self._auto_resolve_conflict(conflict)
            elif resolution_strategy == "rebalance":
                success = self._rebalance_teams(conflict)
            elif resolution_strategy == "reassign":
                success = self._reassign_agents(conflict)
            elif resolution_strategy == "escalate":
                success = self._escalate_conflict(conflict)
            else:
                self.logger.error(f"Unknown resolution strategy: {resolution_strategy}")
                return False

            if success:
                conflict['status'] = 'resolved'
                conflict['resolved_at'] = datetime.now(timezone.utc).isoformat()
                self._update_conflict(conflict)
                self.logger.info(f"Resolved conflict {conflict_id} using {resolution_strategy}")

            return success

        except Exception as e:
            self.logger.error(f"Failed to resolve conflict {conflict_id}: {e}")
            return False

    def get_swarm_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the swarm coordination system."""
        with self._lock:
            # Calculate swarm metrics
            total_agents = len(self._agent_profiles)
            healthy_agents = sum(1 for profile in self._agent_profiles.values()
                               if profile.health_status == HealthLevel.HEALTHY)
            total_teams = len(self._active_teams)
            active_conflicts = len([c for c in self._conflict_registry.values()
                                  if c['status'] == 'active'])

            # Calculate utilization
            total_capacity = sum(1.0 - profile.current_load for profile in self._agent_profiles.values())
            avg_utilization = 1.0 - (total_capacity / max(total_agents, 1))

            # Team distribution
            team_distribution = defaultdict(int)
            for team in self._active_teams.values():
                team_distribution[team.team_type] += 1

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "coordination_active": self._coordination_active,
                "swarm_metrics": {
                    "total_agents": total_agents,
                    "healthy_agents": healthy_agents,
                    "agent_health_ratio": healthy_agents / max(total_agents, 1),
                    "total_teams": total_teams,
                    "average_utilization": avg_utilization,
                    "active_conflicts": active_conflicts
                },
                "team_distribution": dict(team_distribution),
                "work_queue_size": len(self._work_queue),
                "performance_trends": self._get_performance_trends()
            }

    def generate_coordination_dashboard(self) -> str:
        """Generate real-time swarm coordination dashboard."""
        with self._lock:
            dashboard = []
            dashboard.append("🎯 SWARM COORDINATION DASHBOARD - Phase C Intelligence")
            dashboard.append("=" * 70)
            dashboard.append("")

            status = self.get_swarm_status()

            # Swarm overview
            dashboard.append("SWARM OVERVIEW:")
            metrics = status["swarm_metrics"]
            dashboard.append(f"  Agents: {metrics['total_agents']}/{self.max_agents} "
                           f"({metrics['healthy_agents']} healthy)")
            dashboard.append(f"  Teams: {metrics['total_teams']} active")
            dashboard.append(f"  Utilization: {metrics['average_utilization']:.1%}")
            dashboard.append(f"  Conflicts: {metrics['active_conflicts']} active")
            dashboard.append("")

            # Team distribution
            if status["team_distribution"]:
                dashboard.append("TEAM DISTRIBUTION:")
                for team_type, count in status["team_distribution"].items():
                    dashboard.append(f"  {team_type.replace('_', ' ').title()}: {count} teams")
                dashboard.append("")

            # Agent health status
            dashboard.append("AGENT STATUS:")
            for agent_name, profile in list(self._agent_profiles.items())[:10]:  # Show top 10
                health_emoji = self._get_health_emoji(profile.health_status)
                load_bar = self._get_load_bar(profile.current_load)
                caps = len(profile.capabilities)
                dashboard.append(f"  {health_emoji} {agent_name:<12} │ {load_bar} │ {caps} capabilities")
            dashboard.append("")

            # Active teams
            if self._active_teams:
                dashboard.append("ACTIVE TEAMS:")
                for team_id, team in list(self._active_teams.items())[:5]:  # Show top 5
                    team_type_emoji = {"parallel": "⚡", "pipeline": "🔄", "mesh": "🕸️",
                                     "specialist": "🎯", "emergency": "🚨"}
                    emoji = team_type_emoji.get(team.team_type.value, "👥")
                    member_count = len(team.member_agents)
                    workload_count = len(team.assigned_workload)
                    dashboard.append(f"  {emoji} {team_id:<12} │ {member_count} agents │ {workload_count} tasks")
                dashboard.append("")

            return "\n".join(dashboard)

    # Team formation algorithms
    def _register_team_formation_algorithms(self) -> None:
        """Register team formation algorithms for different team types."""
        self._team_formation_algorithms = {
            TeamType.PARALLEL: self._form_parallel_team,
            TeamType.PIPELINE: self._form_pipeline_team,
            TeamType.MESH: self._form_mesh_team,
            TeamType.SPECIALIST: self._form_specialist_team,
            TeamType.EMERGENCY: self._form_emergency_team
        }

    def _form_parallel_team(self, workload: List[str], capabilities: List[AgentCapability],
                           preferred_agents: List[str] = None) -> Optional[Team]:
        """Form a parallel work team."""
        # Get available agents
        available_agents = self._get_available_agents(capabilities, preferred_agents)

        if len(available_agents) < self.min_team_size:
            self.logger.warning("Not enough available agents for parallel team")
            return None

        # Select optimal team size (target around middle of range)
        optimal_size = min(self.max_team_size, max(self.min_team_size,
                          len(workload) // 2 + 1))

        # Sort by performance and availability
        sorted_agents = sorted(available_agents,
                             key=lambda a: (self._agent_profiles[a].performance_rating,
                                          -self._agent_profiles[a].current_load),
                             reverse=True)

        selected_agents = sorted_agents[:optimal_size]

        # No leader needed for parallel teams - all agents work independently
        team = Team(
            team_id=f"parallel_{int(time.time())}",
            team_type=TeamType.PARALLEL,
            leader_agent=None,
            member_agents=selected_agents,
            assigned_workload=workload,
            target_capability=capabilities,
            estimated_completion=self._estimate_team_completion(selected_agents, workload),
            performance_metrics={},
            coordination_overhead=0.1,  # Low overhead for parallel work
            created_at=datetime.now(timezone.utc).isoformat()
        )

        self._active_teams[team.team_id] = team
        self._persist_team(team)

        self.logger.info(f"Formed parallel team {team.team_id} with {len(selected_agents)} agents")
        return team

    def _form_pipeline_team(self, workload: List[str], capabilities: List[AgentCapability],
                           preferred_agents: List[str] = None) -> Optional[Team]:
        """Form a pipeline team with sequential coordination."""
        available_agents = self._get_available_agents(capabilities, preferred_agents)

        if len(available_agents) < self.min_team_size:
            return None

        # For pipeline, we need agents with complementary capabilities
        # Sort by specialization diversity
        selected_agents = self._select_diverse_agents(available_agents, capabilities,
                                                    min(self.max_team_size, len(workload)))

        # Select leader with highest coordination rating
        leader = max(selected_agents,
                    key=lambda a: self._agent_profiles[a].collaboration_rating)

        team = Team(
            team_id=f"pipeline_{int(time.time())}",
            team_type=TeamType.PIPELINE,
            leader_agent=leader,
            member_agents=selected_agents,
            assigned_workload=workload,
            target_capability=capabilities,
            estimated_completion=self._estimate_team_completion(selected_agents, workload),
            performance_metrics={},
            coordination_overhead=0.3,  # Higher overhead for sequential coordination
            created_at=datetime.now(timezone.utc).isoformat()
        )

        self._active_teams[team.team_id] = team
        self._persist_team(team)

        self.logger.info(f"Formed pipeline team {team.team_id} with leader {leader}")
        return team

    def _form_mesh_team(self, workload: List[str], capabilities: List[AgentCapability],
                       preferred_agents: List[str] = None) -> Optional[Team]:
        """Form a mesh team for complex interdependent work."""
        available_agents = self._get_available_agents(capabilities, preferred_agents)

        # Mesh teams need high collaboration agents
        high_collab_agents = [a for a in available_agents
                             if self._agent_profiles[a].collaboration_rating > 0.7]

        if len(high_collab_agents) < self.min_team_size:
            # Fall back to best available if not enough high-collaboration agents
            high_collab_agents = sorted(available_agents,
                                      key=lambda a: self._agent_profiles[a].collaboration_rating,
                                      reverse=True)[:self.max_team_size]

        selected_agents = high_collab_agents[:min(self.max_team_size, len(high_collab_agents))]

        # Select coordinator (not necessarily leader, more of a facilitator)
        coordinator = max(selected_agents,
                         key=lambda a: (self._agent_profiles[a].collaboration_rating +
                                       self._agent_profiles[a].performance_rating) / 2)

        team = Team(
            team_id=f"mesh_{int(time.time())}",
            team_type=TeamType.MESH,
            leader_agent=coordinator,
            member_agents=selected_agents,
            assigned_workload=workload,
            target_capability=capabilities,
            estimated_completion=self._estimate_team_completion(selected_agents, workload),
            performance_metrics={},
            coordination_overhead=0.5,  # Highest overhead for complex coordination
            created_at=datetime.now(timezone.utc).isoformat()
        )

        self._active_teams[team.team_id] = team
        self._persist_team(team)

        self.logger.info(f"Formed mesh team {team.team_id} with coordinator {coordinator}")
        return team

    def _form_specialist_team(self, workload: List[str], capabilities: List[AgentCapability],
                             preferred_agents: List[str] = None) -> Optional[Team]:
        """Form a specialist team with domain experts."""
        # Find agents with high specialization in required capabilities
        specialist_agents = []
        for agent_name, profile in self._agent_profiles.items():
            if preferred_agents and agent_name not in preferred_agents:
                continue
            if profile.health_status in [HealthLevel.CRITICAL, HealthLevel.OFFLINE]:
                continue
            if profile.current_load > 0.8:  # Too busy
                continue

            # Check if agent has required capabilities with high performance
            capability_match = sum(1 for cap in capabilities if cap in profile.capabilities)
            if capability_match > 0 and profile.performance_rating > 0.7:
                specialist_agents.append((agent_name, capability_match, profile.performance_rating))

        if not specialist_agents:
            self.logger.warning("No specialist agents available for required capabilities")
            return None

        # Sort by capability match and performance
        specialist_agents.sort(key=lambda x: (x[1], x[2]), reverse=True)
        selected_agents = [agent[0] for agent in specialist_agents[:self.max_team_size]]

        if len(selected_agents) < self.min_team_size:
            return None

        # Most specialized agent becomes leader
        leader = selected_agents[0]

        team = Team(
            team_id=f"specialist_{int(time.time())}",
            team_type=TeamType.SPECIALIST,
            leader_agent=leader,
            member_agents=selected_agents,
            assigned_workload=workload,
            target_capability=capabilities,
            estimated_completion=self._estimate_team_completion(selected_agents, workload),
            performance_metrics={},
            coordination_overhead=0.2,  # Lower overhead due to expertise
            created_at=datetime.now(timezone.utc).isoformat()
        )

        self._active_teams[team.team_id] = team
        self._persist_team(team)

        self.logger.info(f"Formed specialist team {team.team_id} led by expert {leader}")
        return team

    def _form_emergency_team(self, workload: List[str], capabilities: List[AgentCapability],
                            preferred_agents: List[str] = None) -> Optional[Team]:
        """Form an emergency response team for urgent work."""
        # Get immediately available agents regardless of current load
        available_agents = []
        for agent_name, profile in self._agent_profiles.items():
            if preferred_agents and agent_name not in preferred_agents:
                continue
            if profile.health_status == HealthLevel.OFFLINE:
                continue
            if profile.current_load < 0.9:  # Allow higher load for emergency
                available_agents.append(agent_name)

        if len(available_agents) < 2:  # Emergency teams can be smaller
            self.logger.warning("Not enough agents available for emergency team")
            return None

        # Select most responsive and capable agents
        emergency_agents = sorted(available_agents,
                                key=lambda a: (
                                    self._agent_profiles[a].performance_rating,
                                    -self._agent_profiles[a].current_load,
                                    self._agent_profiles[a].collaboration_rating
                                ), reverse=True)

        selected_agents = emergency_agents[:min(5, len(emergency_agents))]  # Max 5 for emergency

        # Highest performer leads
        leader = selected_agents[0]

        team = Team(
            team_id=f"emergency_{int(time.time())}",
            team_type=TeamType.EMERGENCY,
            leader_agent=leader,
            member_agents=selected_agents,
            assigned_workload=workload,
            target_capability=capabilities,
            estimated_completion=self._estimate_team_completion(selected_agents, workload, urgent=True),
            performance_metrics={},
            coordination_overhead=0.15,  # Low overhead for speed
            created_at=datetime.now(timezone.utc).isoformat()
        )

        self._active_teams[team.team_id] = team
        self._persist_team(team)

        self.logger.info(f"Formed emergency team {team.team_id} with {len(selected_agents)} agents")
        return team

    # Coordination loops
    def _team_rebalancing_loop(self) -> None:
        """Continuously rebalance teams for optimal performance."""
        while self._coordination_active:
            try:
                self._rebalance_all_teams()
            except Exception as e:
                self.logger.error(f"Error in team rebalancing: {e}")
            time.sleep(self.intervals['team_rebalancing'])

    def _conflict_detection_loop(self) -> None:
        """Continuously detect and resolve conflicts."""
        while self._coordination_active:
            try:
                conflicts = self.detect_conflicts()
                for conflict in conflicts:
                    self.resolve_conflict(conflict['conflict_id'], "auto")
            except Exception as e:
                self.logger.error(f"Error in conflict detection: {e}")
            time.sleep(self.intervals['conflict_detection'])

    def _performance_assessment_loop(self) -> None:
        """Continuously assess and update performance metrics."""
        while self._coordination_active:
            try:
                self._assess_all_performance()
            except Exception as e:
                self.logger.error(f"Error in performance assessment: {e}")
            time.sleep(self.intervals['performance_assessment'])

    def _workload_distribution_loop(self) -> None:
        """Continuously optimize workload distribution."""
        while self._coordination_active:
            try:
                if self._work_queue:
                    work_items = []
                    # Process queued work in batches
                    for _ in range(min(10, len(self._work_queue))):
                        if self._work_queue:
                            work_items.append(self._work_queue.popleft())

                    if work_items:
                        self.distribute_work(work_items)
            except Exception as e:
                self.logger.error(f"Error in workload distribution: {e}")
            time.sleep(self.intervals['workload_distribution'])

    # Helper methods for team formation and coordination
    def _get_available_agents(self, required_capabilities: List[AgentCapability],
                             preferred_agents: List[str] = None) -> List[str]:
        """Get agents available for team formation."""
        available = []
        for agent_name, profile in self._agent_profiles.items():
            if preferred_agents and agent_name not in preferred_agents:
                continue
            if profile.health_status in [HealthLevel.CRITICAL, HealthLevel.OFFLINE]:
                continue
            if profile.current_load > 0.9:  # Too busy
                continue
            if any(cap in profile.capabilities for cap in required_capabilities):
                available.append(agent_name)
        return available

    def _select_diverse_agents(self, agents: List[str], capabilities: List[AgentCapability],
                              target_count: int) -> List[str]:
        """Select agents with diverse, complementary capabilities."""
        if len(agents) <= target_count:
            return agents

        selected = []
        remaining = agents.copy()

        # First, select agents with most required capabilities
        capability_counts = []
        for agent in agents:
            profile = self._agent_profiles[agent]
            count = sum(1 for cap in capabilities if cap in profile.capabilities)
            capability_counts.append((agent, count))

        capability_counts.sort(key=lambda x: x[1], reverse=True)

        # Select top agents ensuring diversity
        for agent, _ in capability_counts:
            if len(selected) >= target_count:
                break
            selected.append(agent)

        return selected[:target_count]

    def _infer_specializations(self, capabilities: List[AgentCapability]) -> Dict[WorkloadType, float]:
        """Infer workload specializations from agent capabilities."""
        specializations = {}

        # Map capabilities to workload types
        capability_mapping = {
            AgentCapability.FRONTEND_DEV: [WorkloadType.CREATIVE, WorkloadType.IO_BOUND],
            AgentCapability.BACKEND_DEV: [WorkloadType.CPU_INTENSIVE, WorkloadType.ANALYTICAL],
            AgentCapability.DATABASE_OPS: [WorkloadType.IO_BOUND, WorkloadType.MEMORY_INTENSIVE],
            AgentCapability.TESTING: [WorkloadType.ANALYTICAL, WorkloadType.CPU_INTENSIVE],
            AgentCapability.DOCUMENTATION: [WorkloadType.CREATIVE, WorkloadType.IO_BOUND],
            AgentCapability.DEVOPS: [WorkloadType.COORDINATION_HEAVY, WorkloadType.ANALYTICAL],
            AgentCapability.SECURITY: [WorkloadType.ANALYTICAL, WorkloadType.CPU_INTENSIVE],
            AgentCapability.PERFORMANCE: [WorkloadType.CPU_INTENSIVE, WorkloadType.MEMORY_INTENSIVE],
            AgentCapability.COORDINATION: [WorkloadType.COORDINATION_HEAVY],
            AgentCapability.ANALYSIS: [WorkloadType.ANALYTICAL, WorkloadType.MEMORY_INTENSIVE]
        }

        # Initialize all workload types with base score
        for workload_type in WorkloadType:
            specializations[workload_type] = 0.2

        # Increase scores based on capabilities
        for capability in capabilities:
            if capability in capability_mapping:
                for workload_type in capability_mapping[capability]:
                    specializations[workload_type] = min(0.9, specializations[workload_type] + 0.3)

        return specializations

    def _get_health_emoji(self, health_level: HealthLevel) -> str:
        """Get emoji representation for health level."""
        emoji_map = {
            HealthLevel.HEALTHY: "🟢",
            HealthLevel.DEGRADED: "🟡",
            HealthLevel.STRUGGLING: "🟠",
            HealthLevel.CRITICAL: "🔴",
            HealthLevel.OFFLINE: "⚫"
        }
        return emoji_map.get(health_level, "❓")

    def _get_load_bar(self, load: float) -> str:
        """Get visual load bar representation."""
        bar_length = 8
        filled = int(load * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        return f"{bar} {load:.1%}"

    # Placeholder methods for complex algorithms
    def _analyze_workload(self, work_items: List[str]) -> Dict[str, Any]:
        """Analyze workload characteristics for optimal distribution."""
        return {"complexity": "medium", "estimated_duration": len(work_items) * 30}

    def _get_available_teams(self) -> List[Team]:
        """Get teams available for additional work."""
        return [team for team in self._active_teams.values()
                if len(team.assigned_workload) < 5]  # Simple availability check

    def _optimize_work_distribution(self, work_items: List[str], teams: List[Team],
                                   analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """Optimize distribution of work across teams."""
        # Simple round-robin distribution for now
        assignments = {}
        for i, item in enumerate(work_items):
            if teams:
                team = teams[i % len(teams)]
                if team.team_id not in assignments:
                    assignments[team.team_id] = []
                assignments[team.team_id].append(item)
        return assignments

    def _calculate_load_balance(self, assignments: Dict[str, List[str]]) -> float:
        """Calculate how well balanced the work distribution is."""
        if not assignments:
            return 1.0

        work_counts = [len(work_list) for work_list in assignments.values()]
        if not work_counts:
            return 1.0

        avg_work = sum(work_counts) / len(work_counts)
        max_deviation = max(abs(count - avg_work) for count in work_counts)
        return max(0.0, 1.0 - (max_deviation / max(avg_work, 1.0)))

    def _assess_conflict_risk(self, assignments: Dict[str, List[str]]) -> float:
        """Assess risk of conflicts in work assignments."""
        # Simplified conflict risk assessment
        return 0.1  # Low risk for now

    def _calculate_coordination_complexity(self, assignments: Dict[str, List[str]]) -> float:
        """Calculate coordination complexity for assignments."""
        # More teams = higher coordination complexity
        num_teams = len(assignments)
        return min(1.0, num_teams / 10.0)

    def _estimate_completion_time(self, assignments: Dict[str, List[str]]) -> str:
        """Estimate when all work will be completed."""
        if not assignments:
            return datetime.now(timezone.utc).isoformat()

        max_work = max(len(work_list) for work_list in assignments.values())
        estimated_hours = max_work * 0.5  # 30 minutes per work item
        completion_time = datetime.now(timezone.utc) + timedelta(hours=estimated_hours)
        return completion_time.isoformat()

    def _estimate_team_completion(self, agents: List[str], workload: List[str], urgent: bool = False) -> str:
        """Estimate when team will complete assigned workload."""
        if not agents or not workload:
            return datetime.now(timezone.utc).isoformat()

        # Base estimate: 30 minutes per work item per agent
        work_per_agent = len(workload) / len(agents)
        base_hours = work_per_agent * 0.5

        # Adjust for team efficiency
        avg_performance = sum(self._agent_profiles[agent].performance_rating
                            for agent in agents) / len(agents)
        efficiency_multiplier = 0.5 + avg_performance  # 0.5 to 1.5 range

        adjusted_hours = base_hours / efficiency_multiplier

        if urgent:
            adjusted_hours *= 0.7  # Emergency teams work faster

        completion_time = datetime.now(timezone.utc) + timedelta(hours=adjusted_hours)
        return completion_time.isoformat()

    # Conflict detection and resolution
    def _detect_resource_conflicts(self) -> List[Dict[str, Any]]:
        """Detect resource conflicts between teams."""
        return []  # Placeholder

    def _detect_coordination_conflicts(self) -> List[Dict[str, Any]]:
        """Detect coordination conflicts."""
        return []  # Placeholder

    def _detect_performance_conflicts(self) -> List[Dict[str, Any]]:
        """Detect performance-related conflicts."""
        return []  # Placeholder

    def _auto_resolve_conflict(self, conflict: Dict[str, Any]) -> bool:
        """Automatically resolve a conflict."""
        return True  # Placeholder

    def _rebalance_teams(self, conflict: Dict[str, Any]) -> bool:
        """Resolve conflict by rebalancing teams."""
        return True  # Placeholder

    def _reassign_agents(self, conflict: Dict[str, Any]) -> bool:
        """Resolve conflict by reassigning agents."""
        return True  # Placeholder

    def _escalate_conflict(self, conflict: Dict[str, Any]) -> bool:
        """Escalate conflict to human operator."""
        return True  # Placeholder

    def _rebalance_all_teams(self) -> None:
        """Rebalance all teams for optimal performance."""
        pass  # Placeholder

    def _assess_all_performance(self) -> None:
        """Assess performance of all agents and teams."""
        pass  # Placeholder

    def _get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trends for dashboard."""
        return {"trend": "stable"}  # Placeholder

    # Database persistence methods
    def _persist_agent_profile(self, profile: AgentProfile) -> None:
        """Persist agent profile to database."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agent_profiles
                (agent_name, capabilities, performance_rating, current_load, health_status,
                 team_preferences, last_active, specialization_score, collaboration_rating,
                 availability_window)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.agent_name,
                json.dumps([cap.value for cap in profile.capabilities]),
                profile.performance_rating,
                profile.current_load,
                profile.health_status.value,
                json.dumps([pref.value for pref in profile.team_preferences]),
                profile.last_active,
                json.dumps({k.value: v for k, v in profile.specialization_score.items()}),
                profile.collaboration_rating,
                json.dumps(profile.availability_window) if profile.availability_window else None
            ))
            conn.commit()

    def _persist_team(self, team: Team) -> None:
        """Persist team to database."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO teams
                (team_id, team_type, leader_agent, member_agents, assigned_workload,
                 target_capability, estimated_completion, performance_metrics,
                 coordination_overhead, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                team.team_id,
                team.team_type.value,
                team.leader_agent,
                json.dumps(team.member_agents),
                json.dumps(team.assigned_workload),
                json.dumps([cap.value for cap in team.target_capability]),
                team.estimated_completion,
                json.dumps(team.performance_metrics),
                team.coordination_overhead,
                team.created_at
            ))
            conn.commit()

    def _persist_distribution_plan(self, plan: WorkDistributionPlan) -> None:
        """Persist distribution plan to database."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO work_distribution_plans
                (plan_id, total_workload, team_assignments, estimated_completion,
                 load_balance_score, conflict_risk_score, coordination_complexity, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan.plan_id,
                json.dumps(plan.total_workload),
                json.dumps(plan.team_assignments),
                plan.estimated_completion,
                plan.load_balance_score,
                plan.conflict_risk_score,
                plan.coordination_complexity,
                plan.created_at
            ))
            conn.commit()

    def _persist_conflict(self, conflict: Dict[str, Any]) -> None:
        """Persist conflict to database."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO conflict_registry
                (conflict_id, conflict_type, involved_agents, involved_teams,
                 conflict_description, resolution_strategy, status, created_at, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conflict['conflict_id'],
                conflict['conflict_type'],
                json.dumps(conflict['involved_agents']),
                json.dumps(conflict['involved_teams']),
                conflict['conflict_description'],
                conflict.get('resolution_strategy'),
                conflict['status'],
                conflict['created_at'],
                conflict.get('resolved_at')
            ))
            conn.commit()

    def _update_conflict(self, conflict: Dict[str, Any]) -> None:
        """Update conflict in database."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE conflict_registry
                SET status = ?, resolved_at = ?, resolution_strategy = ?
                WHERE conflict_id = ?
            """, (
                conflict['status'],
                conflict.get('resolved_at'),
                conflict.get('resolution_strategy'),
                conflict['conflict_id']
            ))
            conn.commit()


# Example usage and testing
if __name__ == "__main__":
    # Initialize the swarm coordination system
    coordinator = SwarmCoordinator()

    try:
        # Register some sample agents
        coordinator.register_agent(
            "BlackCastle",
            [AgentCapability.COORDINATION, AgentCapability.ANALYSIS],
            team_preferences=[TeamType.MESH, TeamType.SPECIALIST]
        )

        coordinator.register_agent(
            "BlueLake",
            [AgentCapability.FRONTEND_DEV, AgentCapability.TESTING],
            team_preferences=[TeamType.PARALLEL, TeamType.PIPELINE]
        )

        coordinator.register_agent(
            "RedBear",
            [AgentCapability.BACKEND_DEV, AgentCapability.DATABASE_OPS],
            team_preferences=[TeamType.SPECIALIST, TeamType.PARALLEL]
        )

        # Start coordination
        coordinator.start_coordination()
        print("Swarm coordination started...")

        # Form a team and assign work
        team = coordinator.form_team(
            workload=["task1", "task2", "task3"],
            required_capabilities=[AgentCapability.FRONTEND_DEV, AgentCapability.TESTING],
            team_type=TeamType.PARALLEL
        )

        if team:
            print(f"Formed team: {team.team_id} with {len(team.member_agents)} agents")

        # Create work distribution plan
        plan = coordinator.distribute_work(["task4", "task5", "task6", "task7"])
        print(f"Created distribution plan: {plan.plan_id}")

        # Generate dashboard
        dashboard = coordinator.generate_coordination_dashboard()
        print("\n" + dashboard)

        # Get status
        status = coordinator.get_swarm_status()
        print(f"\nSwarm Status: {status['swarm_metrics']['total_agents']} agents coordinated")

        # Keep coordinating for a while
        time.sleep(30)

    except KeyboardInterrupt:
        print("\nStopping swarm coordination...")
    finally:
        coordinator.stop_coordination()
        print("Swarm coordination stopped.")