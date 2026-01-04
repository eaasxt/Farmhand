#!/usr/bin/env python3
"""
AI Orchestration Setup Script
Sets up the complete AI-optimized orchestration system for Gas Town MEOW stack.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Add molecule marketplace to path
sys.path.append(str(Path(__file__).parent / "molecule-marketplace"))

from core.database.db import MoleculeDB
from orchestration import (
    UsagePatternLearner,
    WorkflowOptimizer,
    SmartOrchestrationEngine,
    ContinuousLearningPipeline
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_ai_orchestration():
    """Set up the complete AI orchestration system."""

    print("🧠 Setting up AI-Optimized Orchestration for Gas Town MEOW Stack")
    print("=" * 70)

    try:
        # Step 1: Initialize database with AI extensions
        print("\n📊 Initializing database with AI orchestration extensions...")
        setup_database()

        # Step 2: Initialize AI orchestration components
        print("\n🔧 Initializing AI orchestration components...")
        components = setup_components()

        # Step 3: Populate with sample data for testing
        print("\n🧪 Setting up sample data for testing...")
        setup_sample_data(components)

        # Step 4: Verify setup
        print("\n✅ Verifying AI orchestration setup...")
        verify_setup(components)

        # Step 5: Display usage examples
        print("\n📋 Setup complete! Here's how to use the AI orchestration:")
        display_usage_examples()

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


def setup_database():
    """Initialize database with AI orchestration extensions."""

    # Initialize marketplace database
    db = MoleculeDB()

    # Read and execute schema extensions
    schema_path = Path(__file__).parent / "molecule-marketplace" / "orchestration" / "schema_extensions.sql"

    if schema_path.exists():
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        # Execute schema extensions using the database connection
        with db.get_connection() as conn:
            conn.executescript(schema_sql)
        print("   ✓ AI orchestration database schema initialized")
    else:
        print("   ⚠️  Schema extensions file not found, using minimal setup")

    return db


def setup_components():
    """Initialize AI orchestration components."""

    components = {}

    # Initialize usage pattern learner
    components['learner'] = UsagePatternLearner()
    print("   ✓ Usage Pattern Learner initialized")

    # Initialize workflow optimizer
    components['optimizer'] = WorkflowOptimizer()
    print("   ✓ Workflow Optimizer initialized")

    # Initialize smart orchestration engine
    components['engine'] = SmartOrchestrationEngine(max_parallel_workers=4)
    print("   ✓ Smart Orchestration Engine initialized")

    # Initialize continuous learning pipeline
    components['pipeline'] = ContinuousLearningPipeline(learning_interval_hours=6)
    print("   ✓ Continuous Learning Pipeline initialized")

    return components


def setup_sample_data(components):
    """Set up sample data for testing the AI orchestration."""

    from orchestration.usage_learner import WorkflowMetrics

    # Sample execution data
    sample_executions = [
        {
            'execution_id': 'sample_001',
            'template_name': 'react-node-fullstack',
            'start_time': datetime.now().replace(hour=9, minute=30),
            'end_time': datetime.now().replace(hour=9, minute=45),
            'success': True,
            'execution_time': 900,  # 15 minutes
            'steps_completed': 8,
            'steps_total': 8,
            'error_messages': [],
            'performance_bottlenecks': ['npm_install', 'webpack_build'],
            'resource_usage': {'cpu': 1.5, 'memory': 2.0, 'disk': 1.0},
            'user_variables': {'project_name': 'awesome-app', 'use_typescript': True}
        },
        {
            'execution_id': 'sample_002',
            'template_name': 'fastapi-rest-api',
            'start_time': datetime.now().replace(hour=10, minute=15),
            'end_time': datetime.now().replace(hour=10, minute=25),
            'success': True,
            'execution_time': 600,  # 10 minutes
            'steps_completed': 6,
            'steps_total': 6,
            'error_messages': [],
            'performance_bottlenecks': ['pip_install'],
            'resource_usage': {'cpu': 1.0, 'memory': 1.2, 'disk': 0.8},
            'user_variables': {'use_async': True, 'database': 'postgresql'}
        },
        {
            'execution_id': 'sample_003',
            'template_name': 'pytest-testing-suite',
            'start_time': datetime.now().replace(hour=11, minute=0),
            'end_time': datetime.now().replace(hour=11, minute=5),
            'success': True,
            'execution_time': 300,  # 5 minutes
            'steps_completed': 4,
            'steps_total': 4,
            'error_messages': [],
            'performance_bottlenecks': [],
            'resource_usage': {'cpu': 0.8, 'memory': 1.0, 'disk': 0.5},
            'user_variables': {'test_type': 'unit', 'coverage': True}
        }
    ]

    # Record sample executions
    for exec_data in sample_executions:
        metrics = WorkflowMetrics(**exec_data)
        components['learner'].record_workflow_execution(metrics)

    print("   ✓ Sample workflow execution data recorded")

    # Generate initial patterns and recommendations
    patterns = components['learner'].get_usage_patterns(min_confidence=0.3)
    recommendations = components['optimizer'].generate_optimization_recommendations(limit=5)

    print(f"   ✓ Generated {len(patterns)} initial usage patterns")
    print(f"   ✓ Generated {len(recommendations)} optimization recommendations")


def verify_setup(components):
    """Verify that the AI orchestration setup is working correctly."""

    # Test 1: Usage pattern learning
    try:
        patterns = components['learner'].get_usage_patterns()
        print(f"   ✓ Usage pattern learning: {len(patterns)} patterns discovered")
    except Exception as e:
        print(f"   ❌ Usage pattern learning failed: {e}")

    # Test 2: Workflow optimization
    try:
        config = components['optimizer'].optimize_workflow_configuration(
            'react-node-fullstack',
            {'variables': {'project_name': 'test-app'}}
        )
        print(f"   ✓ Workflow optimization: {config.optimization_confidence:.1%} confidence")
    except Exception as e:
        print(f"   ❌ Workflow optimization failed: {e}")

    # Test 3: Smart orchestration
    try:
        plan = components['engine'].create_execution_plan(
            'react-node-fullstack',
            {'project_name': 'test-app'}
        )
        print(f"   ✓ Smart orchestration: {len(plan.steps)} steps planned")
    except Exception as e:
        print(f"   ❌ Smart orchestration failed: {e}")

    # Test 4: Learning insights
    try:
        insights = components['engine'].get_orchestration_insights()
        executions = insights.get('total_executions', 0)
        print(f"   ✓ Learning insights: {executions} executions tracked")
    except Exception as e:
        print(f"   ❌ Learning insights failed: {e}")


def display_usage_examples():
    """Display examples of how to use the AI orchestration system."""

    examples = """
🚀 AI Orchestration Usage Examples:

1. Analyze Template Performance:
   python3 molecule-marketplace/cli/marketplace.py orchestration analyze --template react-node-fullstack

2. Get AI Recommendations:
   python3 molecule-marketplace/cli/marketplace.py orchestration recommendations

3. Execute Optimized Workflow:
   python3 molecule-marketplace/cli/marketplace.py orchestration execute react-node-fullstack \\
     --var project_name=my-app --var use_typescript=true

4. Generate Learning Report:
   python3 molecule-marketplace/cli/marketplace.py orchestration learning-report --days 7

5. Start Continuous Learning:
   python3 molecule-marketplace/cli/marketplace.py orchestration start-learning --interval 6

6. Get System Status:
   python3 molecule-marketplace/cli/marketplace.py orchestration status

7. Optimize Specific Template:
   python3 molecule-marketplace/cli/marketplace.py orchestration optimize react-node-fullstack \\
     --project-path . --var use_typescript=true

📊 Integration with Existing MEOW Stack:

• Beads Integration: Templates suggest beads for task decomposition
• GUPP Automation: Dynamic workflow adjustments based on patterns
• Molecule Database: Persistent analytics and learning storage
• Formula CLI: Extended with 'orchestration' command group

🧠 AI Learning Features:

• Usage Pattern Recognition: Learns from successful/failed workflows
• Performance Optimization: Automatically tunes execution parameters
• Intelligent Scheduling: ML-driven task priority and resource allocation
• Failure Prevention: Predicts and prevents common workflow issues
• Continuous Improvement: Self-optimizing system that gets better over time

⚡ Advanced Capabilities:

• Parallel Execution Optimization: Smart grouping of independent tasks
• Resource Allocation: Dynamic CPU/memory scaling based on usage patterns
• Performance Prediction: ML models predict execution time and success rate
• Bottleneck Detection: Automatically identifies and suggests fixes for slowdowns
• Template Recommendations: AI-powered suggestions based on codebase analysis

🔗 MEOW Stack Integration Points:

Phase 1 (Molecules): Template orchestration with TOML workflow generation
Phase 2 (Engine): Automated execution with GUPP hooks and optimization
Phase 3 (Orchestra): Multi-service coordination with intelligent resource management
Phase 4 (Workflow): AI-optimized templates with continuous learning and improvement

The AI orchestration system is now ready to learn from your workflows and
continuously improve the Gas Town MEOW stack experience! 🎯
"""
    print(examples)


def create_sample_workflow():
    """Create a sample workflow to test the AI orchestration."""

    try:
        from orchestration import SmartOrchestrationEngine

        engine = SmartOrchestrationEngine()

        # Create a test execution plan
        plan = engine.create_execution_plan(
            'react-node-fullstack',
            {'project_name': 'sample-ai-app', 'use_typescript': True},
            {'project_path': '/tmp/sample-ai-app', 'project_size': 'medium'}
        )

        print(f"\n🧪 Created sample execution plan:")
        print(f"   Template: {plan.template_name}")
        print(f"   Steps: {len(plan.steps)}")
        print(f"   Estimated duration: {plan.estimated_duration}s")
        print(f"   Optimization confidence: {plan.confidence_score:.1%}")
        print(f"   Applied optimizations: {', '.join(plan.optimization_applied)}")

    except Exception as e:
        print(f"❌ Failed to create sample workflow: {e}")


def main():
    """Main setup function."""

    # Check if we're in the right directory
    if not Path("molecule-marketplace").exists():
        print("❌ Error: molecule-marketplace directory not found")
        print("   Please run this script from the project root directory")
        sys.exit(1)

    # Run the setup
    setup_ai_orchestration()

    # Create sample workflow
    create_sample_workflow()

    print("\n🎉 AI Orchestration setup complete!")
    print("   The Gas Town MEOW stack now includes intelligent workflow optimization,")
    print("   usage pattern learning, and continuous performance improvement.")


if __name__ == "__main__":
    main()