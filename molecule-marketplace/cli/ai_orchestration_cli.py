"""
AI Orchestration CLI Commands
Extends the marketplace CLI with AI-powered orchestration capabilities.
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import click
import logging

# Add the parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from orchestration import (
    UsagePatternLearner,
    WorkflowOptimizer,
    SmartOrchestrationEngine,
    ContinuousLearningPipeline
)

logger = logging.getLogger(__name__)


@click.group(name='orchestration')
def orchestration_cli():
    """AI-powered orchestration commands for workflow optimization."""
    pass


@orchestration_cli.command('analyze')
@click.option('--template', '-t', help='Specific template to analyze')
@click.option('--days', '-d', default=30, help='Days of data to analyze')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def analyze_usage_patterns(template: str, days: int, output_json: bool):
    """Analyze usage patterns and performance metrics."""

    try:
        learner = UsagePatternLearner()

        if template:
            # Analyze specific template
            insights = learner.get_template_insights(template)

            if output_json:
                click.echo(json.dumps(insights, indent=2, default=str))
            else:
                _display_template_insights(template, insights)
        else:
            # Analyze all patterns
            patterns = learner.get_usage_patterns(min_confidence=0.5)

            if output_json:
                patterns_data = [
                    {
                        'pattern_id': p.pattern_id,
                        'pattern_type': p.pattern_type,
                        'frequency': p.frequency,
                        'success_rate': p.success_rate,
                        'avg_execution_time': p.avg_execution_time,
                        'confidence_score': p.confidence_score,
                        'optimization_suggestions': p.optimization_suggestions
                    }
                    for p in patterns
                ]
                click.echo(json.dumps(patterns_data, indent=2))
            else:
                _display_usage_patterns(patterns)

    except Exception as e:
        click.echo(f"❌ Error analyzing usage patterns: {e}", err=True)
        sys.exit(1)


@orchestration_cli.command('optimize')
@click.argument('template_name')
@click.option('--project-path', default='.', help='Project path for context analysis')
@click.option('--var', 'variables', multiple=True, help='Variables in key=value format')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def optimize_workflow(template_name: str, project_path: str, variables: List[str], output_json: bool):
    """Generate optimized workflow configuration for a template."""

    try:
        optimizer = WorkflowOptimizer()

        # Parse variables
        user_variables = {}
        for var in variables:
            if '=' in var:
                key, value = var.split('=', 1)
                user_variables[key] = value

        # Create user context
        user_context = {
            'variables': user_variables,
            'project_path': project_path,
            'project_size': _detect_project_size(project_path)
        }

        # Generate optimized configuration
        config = optimizer.optimize_workflow_configuration(template_name, user_context)

        if output_json:
            from dataclasses import asdict
            click.echo(json.dumps(asdict(config), indent=2, default=str))
        else:
            _display_workflow_configuration(template_name, config)

    except Exception as e:
        click.echo(f"❌ Error optimizing workflow: {e}", err=True)
        sys.exit(1)


@orchestration_cli.command('execute')
@click.argument('template_name')
@click.option('--project-path', default='.', help='Project path for installation')
@click.option('--var', 'variables', multiple=True, help='Variables in key=value format')
@click.option('--optimize/--no-optimize', default=True, help='Apply AI optimizations')
@click.option('--progress/--no-progress', default=True, help='Show progress updates')
def execute_optimized_workflow(template_name: str, project_path: str, variables: List[str],
                               optimize: bool, progress: bool):
    """Execute workflow with AI-powered orchestration."""

    try:
        # Parse variables
        user_variables = {}
        for var in variables:
            if '=' in var:
                key, value = var.split('=', 1)
                user_variables[key] = value

        # Create orchestration engine
        engine = SmartOrchestrationEngine(max_parallel_workers=4)

        # Create execution context
        user_context = {
            'variables': user_variables,
            'project_path': project_path,
            'project_size': _detect_project_size(project_path),
            'optimize': optimize
        }

        click.echo(f"🚀 Creating optimized execution plan for {template_name}...")

        # Create execution plan
        plan = engine.create_execution_plan(template_name, user_variables, user_context)

        click.echo(f"📋 Plan created with {len(plan.steps)} steps, estimated duration: {plan.estimated_duration}s")
        click.echo(f"🎯 Optimization confidence: {plan.confidence_score:.1%}")
        click.echo(f"⚡ Applied optimizations: {', '.join(plan.optimization_applied)}")

        if click.confirm("Execute the optimized workflow?"):
            click.echo("🔄 Executing workflow...")

            def progress_callback(execution_id: str, progress_pct: float, message: str):
                if progress:
                    click.echo(f"📊 Progress: {progress_pct:.1%} - {message}")

            # Execute the plan
            result = engine.execute_plan(plan, progress_callback if progress else None)

            # Display results
            _display_execution_results(result)
        else:
            click.echo("🛑 Execution cancelled")

    except Exception as e:
        click.echo(f"❌ Error executing workflow: {e}", err=True)
        sys.exit(1)


@orchestration_cli.command('recommendations')
@click.option('--template', '-t', help='Specific template to get recommendations for')
@click.option('--limit', '-l', default=10, help='Maximum number of recommendations')
@click.option('--impact', type=click.Choice(['high', 'medium', 'low']), help='Filter by impact level')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def get_optimization_recommendations(template: str, limit: int, impact: str, output_json: bool):
    """Get AI-generated optimization recommendations."""

    try:
        optimizer = WorkflowOptimizer()
        recommendations = optimizer.generate_optimization_recommendations(template, limit)

        # Filter by impact if specified
        if impact:
            recommendations = [r for r in recommendations if r.impact_level == impact]

        if output_json:
            from dataclasses import asdict
            recs_data = [asdict(rec) for rec in recommendations]
            click.echo(json.dumps(recs_data, indent=2, default=str))
        else:
            _display_recommendations(recommendations)

    except Exception as e:
        click.echo(f"❌ Error getting recommendations: {e}", err=True)
        sys.exit(1)


@orchestration_cli.command('insights')
@click.option('--days', '-d', default=7, help='Days of data to include in insights')
@click.option('--type', 'insight_type', help='Filter by insight type')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def get_orchestration_insights(days: int, insight_type: str, output_json: bool):
    """Get orchestration insights and system health metrics."""

    try:
        engine = SmartOrchestrationEngine()
        insights = engine.get_orchestration_insights()

        if output_json:
            click.echo(json.dumps(insights, indent=2, default=str))
        else:
            _display_orchestration_insights(insights)

    except Exception as e:
        click.echo(f"❌ Error getting insights: {e}", err=True)
        sys.exit(1)


@orchestration_cli.command('learning-report')
@click.option('--days', '-d', default=7, help='Days of data to include in report')
@click.option('--output', '-o', help='Output file path')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def generate_learning_report(days: int, output: str, output_json: bool):
    """Generate comprehensive learning and optimization report."""

    try:
        pipeline = ContinuousLearningPipeline()
        report = pipeline.generate_learning_report(days)

        if output_json:
            from dataclasses import asdict
            report_data = asdict(report)
            report_json = json.dumps(report_data, indent=2, default=str)

            if output:
                with open(output, 'w') as f:
                    f.write(report_json)
                click.echo(f"📝 Report saved to {output}")
            else:
                click.echo(report_json)
        else:
            if output:
                _save_text_report(report, output)
                click.echo(f"📝 Report saved to {output}")
            else:
                _display_learning_report(report)

    except Exception as e:
        click.echo(f"❌ Error generating learning report: {e}", err=True)
        sys.exit(1)


@orchestration_cli.command('start-learning')
@click.option('--interval', default=6, help='Learning cycle interval in hours')
@click.option('--background/--foreground', default=False, help='Run in background')
def start_continuous_learning(interval: int, background: bool):
    """Start continuous learning pipeline."""

    try:
        pipeline = ContinuousLearningPipeline(learning_interval_hours=interval)

        click.echo(f"🧠 Starting continuous learning pipeline (interval: {interval}h)")

        if background:
            # In a real implementation, this would fork a daemon process
            click.echo("📡 Background learning not implemented yet - run in foreground")
            return

        # Run in foreground
        click.echo("🔄 Running continuous learning (Ctrl+C to stop)...")

        try:
            asyncio.run(pipeline.start_continuous_learning())
        except KeyboardInterrupt:
            click.echo("\n🛑 Stopping continuous learning pipeline...")
            pipeline.stop_continuous_learning()

    except Exception as e:
        click.echo(f"❌ Error starting learning pipeline: {e}", err=True)
        sys.exit(1)


@orchestration_cli.command('status')
@click.option('--execution-id', help='Check status of specific execution')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def get_orchestration_status(execution_id: str, output_json: bool):
    """Get status of orchestration system or specific execution."""

    try:
        engine = SmartOrchestrationEngine()

        if execution_id:
            status = engine.get_execution_status(execution_id)
            if status:
                if output_json:
                    click.echo(json.dumps(status, indent=2, default=str))
                else:
                    _display_execution_status(status)
            else:
                click.echo(f"❌ Execution {execution_id} not found")
        else:
            # Show overall system status
            insights = engine.get_orchestration_insights()
            if output_json:
                click.echo(json.dumps(insights, indent=2, default=str))
            else:
                _display_system_status(insights)

    except Exception as e:
        click.echo(f"❌ Error getting status: {e}", err=True)
        sys.exit(1)


# Helper functions for display

def _display_template_insights(template_name: str, insights: Dict[str, Any]):
    """Display template insights in a readable format."""

    click.echo(f"\n📊 Insights for {template_name}")
    click.echo("=" * 50)

    if 'error' in insights:
        click.echo(f"❌ Error: {insights['error']}")
        return

    if 'message' in insights:
        click.echo(f"ℹ️  {insights['message']}")
        return

    stats = insights.get('usage_stats', {})
    if stats:
        click.echo(f"📈 Usage Statistics:")
        click.echo(f"   Total executions: {stats.get('total_executions', 0)}")
        click.echo(f"   Success rate: {stats.get('success_rate', 0):.1%}")
        click.echo(f"   Average time: {stats.get('avg_execution_time', 0):.1f}s")

    patterns = insights.get('learned_patterns', {})
    if patterns:
        click.echo(f"\n🧠 Learned Patterns:")
        if patterns.get('optimization_suggestions'):
            click.echo(f"   💡 Suggestions:")
            for suggestion in patterns['optimization_suggestions']:
                click.echo(f"      • {suggestion}")

        if patterns.get('bottlenecks'):
            click.echo(f"   🚧 Common bottlenecks:")
            for bottleneck in patterns['bottlenecks']:
                click.echo(f"      • {bottleneck}")

    trends = insights.get('performance_trend', [])
    if trends:
        click.echo(f"\n📉 Performance Trends (last 7 days):")
        for trend in trends[-3:]:  # Show last 3 days
            click.echo(f"   {trend['date']}: {trend['avg_time']:.1f}s, {trend['success_rate']:.1%}")


def _display_usage_patterns(patterns: List):
    """Display usage patterns in a readable format."""

    click.echo(f"\n📊 Usage Patterns Analysis")
    click.echo("=" * 50)

    if not patterns:
        click.echo("No significant patterns found.")
        return

    for pattern in patterns[:10]:  # Show top 10
        template_name = pattern.pattern_id.replace('template_usage_', '').replace('_', '-')
        click.echo(f"\n🔍 {template_name}")
        click.echo(f"   Frequency: {pattern.frequency} executions")
        click.echo(f"   Success rate: {pattern.success_rate:.1%}")
        click.echo(f"   Avg time: {pattern.avg_execution_time:.1f}s")
        click.echo(f"   Confidence: {pattern.confidence_score:.1%}")

        if pattern.optimization_suggestions:
            click.echo(f"   💡 Top suggestion: {pattern.optimization_suggestions[0]}")


def _display_workflow_configuration(template_name: str, config):
    """Display workflow configuration in a readable format."""

    click.echo(f"\n⚙️  Optimized Configuration for {template_name}")
    click.echo("=" * 50)

    click.echo(f"🎯 Optimization confidence: {config.optimization_confidence:.1%}")

    if config.optimized_variables:
        click.echo(f"\n📝 Optimized variables:")
        for key, value in config.optimized_variables.items():
            click.echo(f"   {key}: {value}")

    if config.parallel_execution_groups:
        click.echo(f"\n⚡ Parallel execution groups:")
        for i, group in enumerate(config.parallel_execution_groups, 1):
            click.echo(f"   Group {i}: {', '.join(group)}")

    if config.resource_allocation:
        click.echo(f"\n💾 Resource allocation:")
        for resource, allocation in config.resource_allocation.items():
            click.echo(f"   {resource}: {allocation:.1f}x")

    if config.performance_targets:
        click.echo(f"\n🎯 Performance targets:")
        for metric, target in config.performance_targets.items():
            click.echo(f"   {metric}: {target}")


def _display_execution_results(result):
    """Display execution results in a readable format."""

    click.echo(f"\n✅ Execution Results")
    click.echo("=" * 50)

    status_emoji = "✅" if result.status.value == "success" else "❌"
    click.echo(f"{status_emoji} Status: {result.status.value}")
    click.echo(f"⏱️  Duration: {result.total_duration}s")
    click.echo(f"📊 Steps completed: {result.steps_completed}/{result.steps_total}")
    click.echo(f"📈 Success rate: {result.success_rate:.1%}")

    if result.errors:
        click.echo(f"\n❌ Errors ({len(result.errors)}):")
        for error in result.errors[:3]:  # Show first 3 errors
            click.echo(f"   • {error}")

    if result.optimization_feedback:
        click.echo(f"\n🔧 Optimization feedback:")
        if 'plan_accuracy' in result.optimization_feedback:
            accuracy = result.optimization_feedback['plan_accuracy']
            for metric, score in accuracy.items():
                click.echo(f"   {metric} accuracy: {score:.1%}")


def _display_recommendations(recommendations: List):
    """Display optimization recommendations in a readable format."""

    click.echo(f"\n💡 Optimization Recommendations")
    click.echo("=" * 50)

    if not recommendations:
        click.echo("No recommendations available.")
        return

    for rec in recommendations:
        impact_emoji = {"high": "🔥", "medium": "⚡", "low": "💡"}.get(rec.impact_level, "💡")
        effort_emoji = {"high": "🏗️", "medium": "🔧", "low": "⚙️"}.get(rec.effort_level, "🔧")

        click.echo(f"\n{impact_emoji} {rec.title}")
        click.echo(f"   📝 {rec.description}")
        click.echo(f"   {effort_emoji} Effort: {rec.effort_level}")
        click.echo(f"   🎯 Priority: {rec.priority_score:.0f}")

        if rec.expected_improvement:
            improvements = [f"{k}: {v:.1f}%" for k, v in rec.expected_improvement.items()]
            click.echo(f"   📈 Expected improvement: {', '.join(improvements)}")


def _display_orchestration_insights(insights: Dict[str, Any]):
    """Display orchestration insights in a readable format."""

    click.echo(f"\n🧠 Orchestration Insights")
    click.echo("=" * 50)

    click.echo(f"🔄 Active executions: {insights.get('active_executions', 0)}")
    click.echo(f"📊 Total executions: {insights.get('total_executions', 0)}")

    recent = insights.get('recent_performance', {})
    if recent:
        click.echo(f"\n📈 Recent Performance:")
        click.echo(f"   Success rate: {recent.get('avg_success_rate', 0):.1%}")
        click.echo(f"   Average duration: {recent.get('avg_duration', 0):.1f}s")
        click.echo(f"   Total errors: {recent.get('total_errors', 0)}")


def _display_learning_report(report):
    """Display learning report in a readable format."""

    click.echo(f"\n📋 Learning Report - {report.generated_at.strftime('%Y-%m-%d %H:%M')}")
    click.echo("=" * 60)

    click.echo(f"⏱️  Period: {report.time_period.days} days")
    click.echo(f"🔄 Total executions: {report.total_executions}")
    click.echo(f"🏥 System health: {report.system_health_score:.1%}")

    click.echo(f"\n🔍 Key Findings:")
    for finding in report.key_findings:
        click.echo(f"   • {finding}")

    click.echo(f"\n💡 Recommended Actions:")
    for action in report.recommended_actions:
        click.echo(f"   • {action}")

    if report.performance_trends:
        click.echo(f"\n📉 Performance Trends:")
        for trend in report.performance_trends[:5]:  # Top 5
            direction_emoji = {"improving": "📈", "degrading": "📉", "stable": "➡️"}.get(trend.trend_direction, "📊")
            target = trend.template_name or "system"
            click.echo(f"   {direction_emoji} {target} {trend.metric_name}: {trend.change_percentage:.1f}%")


def _display_execution_status(status: Dict[str, Any]):
    """Display execution status in a readable format."""

    click.echo(f"\n📊 Execution Status: {status['execution_id']}")
    click.echo("=" * 50)

    status_emoji = {"running": "🔄", "success": "✅", "failed": "❌", "pending": "⏳"}.get(status['status'], "❓")
    click.echo(f"{status_emoji} Status: {status['status']}")
    click.echo(f"📈 Progress: {status['progress']:.1%}")
    click.echo(f"📋 Steps: {status['steps_completed']}/{status['steps_total']}")

    if 'start_time' in status:
        click.echo(f"🕐 Started: {status['start_time']}")

    if status.get('errors'):
        click.echo(f"❌ Errors: {len(status['errors'])}")


def _display_system_status(insights: Dict[str, Any]):
    """Display overall system status."""

    click.echo(f"\n🖥️  Orchestration System Status")
    click.echo("=" * 50)

    click.echo(f"🔄 Active executions: {insights.get('active_executions', 0)}")
    click.echo(f"📊 Total processed: {insights.get('total_executions', 0)}")

    recent = insights.get('recent_performance', {})
    if recent:
        health_emoji = "🟢" if recent.get('avg_success_rate', 0) > 0.9 else "🟡" if recent.get('avg_success_rate', 0) > 0.7 else "🔴"
        click.echo(f"{health_emoji} System health: {recent.get('avg_success_rate', 0):.1%} success rate")


def _detect_project_size(project_path: str) -> str:
    """Detect project size based on directory structure."""

    try:
        path = Path(project_path)
        if not path.exists():
            return 'small'

        # Count files and directories
        file_count = len(list(path.rglob('*')))

        if file_count > 1000:
            return 'large'
        elif file_count > 100:
            return 'medium'
        else:
            return 'small'
    except:
        return 'medium'


def _save_text_report(report, output_path: str):
    """Save learning report as text file."""

    with open(output_path, 'w') as f:
        f.write(f"Learning Report - {report.generated_at.strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Period: {report.time_period.days} days\n")
        f.write(f"Total executions: {report.total_executions}\n")
        f.write(f"System health score: {report.system_health_score:.1%}\n\n")

        f.write("Key Findings:\n")
        for finding in report.key_findings:
            f.write(f"  • {finding}\n")
        f.write("\n")

        f.write("Recommended Actions:\n")
        for action in report.recommended_actions:
            f.write(f"  • {action}\n")
        f.write("\n")

        if report.new_insights:
            f.write("Discovered Insights:\n")
            for insight in report.new_insights:
                f.write(f"  • {insight.title} ({insight.impact_assessment} impact)\n")
                f.write(f"    {insight.description}\n")
            f.write("\n")


if __name__ == '__main__':
    # Enable for testing
    orchestration_cli()