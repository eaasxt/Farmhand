#!/usr/bin/env python3
"""
Formula CLI Marketplace Extension
Extends the formula CLI with marketplace commands for template management.
"""

import sys
import json
import click
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Add the parent directory to path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.database.db import MoleculeDB
from core.storage.template_storage import TemplateStorage
from core.engine.template_engine import TemplateEngine
from discovery.analyzer import CodebaseAnalyzer
from discovery.recommender import TemplateRecommender

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@click.group()
def marketplace():
    """Molecule Marketplace commands for template-driven development."""
    pass


@marketplace.command()
@click.option('--db-path', help='Database path (defaults to ~/.local/share/molecule-marketplace/marketplace.db)')
def init(db_path):
    """Initialize the molecule marketplace."""

    try:
        db = MoleculeDB(db_path) if db_path else MoleculeDB()
        storage = TemplateStorage()

        click.echo("🧪 Initializing Molecule Marketplace...")

        # Create initial template library if empty
        categories = db.get_categories()
        if not categories:
            click.echo("📦 Creating initial template library...")
            _create_initial_templates(db, storage)

        stats = storage.get_storage_stats()

        click.echo(f"✅ Marketplace initialized!")
        click.echo(f"📊 Templates: {stats['template_count']}")
        click.echo(f"💾 Storage: {stats['total_size_mb']} MB")
        click.echo(f"📁 Location: {stats['storage_root']}")

    except Exception as e:
        click.echo(f"❌ Failed to initialize marketplace: {e}", err=True)
        sys.exit(1)


@marketplace.command()
@click.option('--category', help='Filter by category')
@click.option('--tech-stack', help='Filter by technology stack')
@click.option('--limit', default=20, help='Number of templates to show')
@click.option('--sort', 'sort_by', default='download_count',
              type=click.Choice(['download_count', 'rating_avg', 'created_at', 'title']),
              help='Sort templates by')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def list(category, tech_stack, limit, sort_by, output_json):
    """List available templates."""

    try:
        db = MoleculeDB()
        templates = db.list_templates(
            category=category,
            tech_stack=tech_stack,
            limit=limit,
            sort_by=sort_by
        )

        if output_json:
            click.echo(json.dumps(templates, indent=2))
            return

        if not templates:
            click.echo("No templates found.")
            return

        click.echo(f"📦 Found {len(templates)} templates:\n")

        for template in templates:
            tags = ', '.join(template.get('tags', []))

            click.echo(f"🔥 {template['name']} v{template['version']}")
            click.echo(f"   📝 {template['title']}")
            click.echo(f"   📂 {template['category']} | 🛠️  {template['tech_stack']}")
            click.echo(f"   ⭐ {template['rating_avg']:.1f} ({template['rating_count']}) | "
                      f"📥 {template['download_count']} downloads")
            if template['estimated_time']:
                click.echo(f"   ⏱️  ~{template['estimated_time']} minutes")
            if tags:
                click.echo(f"   🏷️  {tags}")
            click.echo("")

    except Exception as e:
        click.echo(f"❌ Failed to list templates: {e}", err=True)
        sys.exit(1)


@marketplace.command()
@click.argument('query')
@click.option('--limit', default=10, help='Number of results to show')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def search(query, limit, output_json):
    """Search templates by name, description, or tags."""

    try:
        db = MoleculeDB()
        templates = db.search_templates(query, limit=limit)

        if output_json:
            click.echo(json.dumps(templates, indent=2))
            return

        if not templates:
            click.echo(f"No templates found for query: {query}")
            return

        click.echo(f"🔍 Search results for '{query}' ({len(templates)} found):\n")

        for template in templates:
            tags = ', '.join(template.get('tags', []))

            click.echo(f"🔥 {template['name']} v{template['version']}")
            click.echo(f"   📝 {template['title']}")
            click.echo(f"   📂 {template['category']} | 🛠️  {template['tech_stack']}")
            click.echo(f"   ⭐ {template['rating_avg']:.1f} | 📥 {template['download_count']} downloads")
            if template.get('description'):
                desc = template['description'][:100] + "..." if len(template['description']) > 100 else template['description']
                click.echo(f"   💬 {desc}")
            click.echo("")

    except Exception as e:
        click.echo(f"❌ Failed to search templates: {e}", err=True)
        sys.exit(1)


@marketplace.command()
@click.argument('template_name')
@click.option('--version', help='Template version (defaults to latest)')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def show(template_name, version, output_json):
    """Show detailed information about a template."""

    try:
        db = MoleculeDB()
        template = db.get_template(name=template_name)

        if not template:
            click.echo(f"Template not found: {template_name}")
            sys.exit(1)

        if output_json:
            click.echo(json.dumps(template, indent=2))
            return

        # Display template information
        click.echo(f"🔥 {template['name']} v{template['version']}")
        click.echo(f"📝 {template['title']}")
        click.echo(f"📂 Category: {template['category']}")
        click.echo(f"🛠️  Tech Stack: {template['tech_stack']}")
        click.echo(f"👤 Author: {template['author'] or 'Unknown'}")
        click.echo(f"📅 Created: {template['created_at']}")
        click.echo(f"⭐ Rating: {template['rating_avg']:.1f}/5.0 ({template['rating_count']} reviews)")
        click.echo(f"📥 Downloads: {template['download_count']}")
        click.echo(f"🎯 Difficulty: {template['difficulty']}")

        if template['estimated_time']:
            click.echo(f"⏱️  Estimated time: {template['estimated_time']} minutes")

        if template['tags']:
            tags = ', '.join(template['tags'])
            click.echo(f"🏷️  Tags: {tags}")

        if template['description']:
            click.echo(f"\n📄 Description:")
            click.echo(f"   {template['description']}")

        if template['requirements']:
            click.echo(f"\n📋 Requirements:")
            for req in template['requirements']:
                click.echo(f"   • {req}")

        # Show template variables
        if template['variables']:
            click.echo(f"\n⚙️  Configuration Variables:")
            for var_name, var_config in template['variables'].items():
                var_type = var_config.get('type', 'string')
                var_desc = var_config.get('description', '')
                default_val = var_config.get('default', '')
                required = var_config.get('required', False)

                req_marker = " (required)" if required else ""
                default_marker = f" [default: {default_val}]" if default_val else ""

                click.echo(f"   • {var_name} ({var_type}){req_marker}{default_marker}")
                if var_desc:
                    click.echo(f"     {var_desc}")

        # Show template files
        storage = TemplateStorage()
        files = storage.load_template_files(template_name, version)

        if files:
            click.echo(f"\n📁 Template Files ({len(files)}):")
            for file_path in sorted(files.keys()):
                file_size = len(files[file_path])
                click.echo(f"   • {file_path} ({file_size} bytes)")

        if template['readme_content']:
            click.echo(f"\n📖 README:")
            click.echo(template['readme_content'])

    except Exception as e:
        click.echo(f"❌ Failed to show template: {e}", err=True)
        sys.exit(1)


@marketplace.command()
@click.argument('template_name')
@click.argument('target_path', type=click.Path())
@click.option('--config', type=click.Path(exists=True), help='JSON config file with template variables')
@click.option('--var', multiple=True, help='Set template variables (--var key=value)')
@click.option('--version', help='Template version (defaults to latest)')
@click.option('--dry-run', is_flag=True, help='Show what would be installed without actually installing')
def install(template_name, target_path, config, var, version, dry_run):
    """Install a template to the target directory."""

    try:
        db = MoleculeDB()
        storage = TemplateStorage()
        engine = TemplateEngine()

        # Get template information
        template = db.get_template(name=template_name)
        if not template:
            click.echo(f"❌ Template not found: {template_name}")
            sys.exit(1)

        # Parse configuration
        config_values = {}

        # Load from config file
        if config:
            config_values.update(json.loads(Path(config).read_text()))

        # Parse command-line variables
        for var_assignment in var:
            if '=' not in var_assignment:
                click.echo(f"❌ Invalid variable format: {var_assignment}. Use --var key=value")
                sys.exit(1)
            key, value = var_assignment.split('=', 1)
            config_values[key] = value

        # Validate configuration
        template_vars = template.get('variables', {})
        if template_vars:
            is_valid, errors = engine.validate_template_config(config_values, template_vars)
            if not is_valid:
                click.echo("❌ Configuration errors:")
                for error in errors:
                    click.echo(f"   • {error}")
                sys.exit(1)

        target = Path(target_path)

        if dry_run:
            click.echo(f"🔍 Dry run - would install {template_name} to {target}")
            files = storage.load_template_files(template_name, version)
            preview = engine.get_template_preview(files, config_values)

            click.echo(f"\n📁 Files to be created:")
            for file_path in sorted(preview.keys()):
                processed_path = engine.process_template(file_path, config_values)
                click.echo(f"   • {processed_path}")
            return

        click.echo(f"📦 Installing {template_name} to {target}...")

        # Install template
        installed_files = storage.install_template(
            template_name, target, config_values, version
        )

        # Record installation
        db.record_installation(
            template['id'],
            user_identifier=str(Path.cwd()),
            project_path=str(target),
            config_values=config_values
        )

        click.echo(f"✅ Successfully installed {template_name}!")
        click.echo(f"📁 Created {len(installed_files)} files in {target}")

        # Show next steps if available
        if template.get('readme_content'):
            click.echo("\n📖 Next Steps:")
            click.echo(template['readme_content'])

    except Exception as e:
        click.echo(f"❌ Failed to install template: {e}", err=True)
        sys.exit(1)


@marketplace.command()
@click.option('--project-path', default='.', type=click.Path(exists=True),
              help='Project path to analyze')
@click.option('--limit', default=5, help='Number of recommendations to show')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def recommend(project_path, limit, output_json):
    """Get AI-powered template recommendations for your project."""

    try:
        analyzer = CodebaseAnalyzer()
        recommender = TemplateRecommender()

        click.echo("🔍 Analyzing your project...")

        analysis = analyzer.analyze_project(Path(project_path))
        recommendations = recommender.recommend_templates(analysis, limit=limit)

        if output_json:
            click.echo(json.dumps(recommendations, indent=2))
            return

        if not recommendations:
            click.echo("No specific recommendations found for your project.")
            return

        click.echo(f"\n🎯 Recommended templates based on your project:\n")

        for i, rec in enumerate(recommendations, 1):
            template = rec['template']
            confidence = rec['confidence']
            reasons = rec['reasons']

            click.echo(f"{i}. 🔥 {template['name']} ({confidence:.0%} match)")
            click.echo(f"   📝 {template['title']}")
            click.echo(f"   📂 {template['category']} | 🛠️  {template['tech_stack']}")
            click.echo(f"   💡 Why: {', '.join(reasons)}")
            click.echo("")

        click.echo("💡 Use 'formula marketplace install <template_name>' to install a template.")

    except Exception as e:
        click.echo(f"❌ Failed to get recommendations: {e}", err=True)
        sys.exit(1)


@marketplace.command()
def categories():
    """List all available template categories."""

    try:
        db = MoleculeDB()
        categories = db.get_categories()

        if not categories:
            click.echo("No categories found.")
            return

        click.echo("📂 Available Categories:\n")

        for category, count in categories:
            click.echo(f"   {category:<20} ({count} templates)")

    except Exception as e:
        click.echo(f"❌ Failed to list categories: {e}", err=True)
        sys.exit(1)


@marketplace.command()
def stats():
    """Show marketplace statistics."""

    try:
        db = MoleculeDB()
        storage = TemplateStorage()

        storage_stats = storage.get_storage_stats()
        categories = db.get_categories()
        tech_stacks = db.get_tech_stacks()

        click.echo("📊 Molecule Marketplace Statistics\n")

        click.echo(f"📦 Templates: {storage_stats['template_count']}")
        click.echo(f"📂 Categories: {len(categories)}")
        click.echo(f"🛠️  Tech Stacks: {len(tech_stacks)}")
        click.echo(f"💾 Storage: {storage_stats['total_size_mb']} MB")
        click.echo(f"📁 Location: {storage_stats['storage_root']}")

        click.echo("\n📈 Popular Categories:")
        for category, count in categories[:5]:
            click.echo(f"   {category}: {count} templates")

        click.echo("\n🔥 Popular Tech Stacks:")
        for tech_stack, count in tech_stacks[:5]:
            click.echo(f"   {tech_stack}: {count} templates")

    except Exception as e:
        click.echo(f"❌ Failed to get stats: {e}", err=True)
        sys.exit(1)


def _create_initial_templates(db: MoleculeDB, storage: TemplateStorage):
    """Create initial template library."""

    # This will be populated with actual templates later
    # For now, just create placeholder structure

    initial_templates = [
        {
            'name': 'web-app-fullstack',
            'title': 'Full-Stack Web Application',
            'category': 'web-dev',
            'tech_stack': 'react-node',
            'description': 'Complete full-stack web application with React frontend and Node.js backend',
            'tags': ['react', 'nodejs', 'fullstack', 'webapp']
        },
        {
            'name': 'api-rest-fastapi',
            'title': 'REST API with FastAPI',
            'category': 'api-dev',
            'tech_stack': 'python-fastapi',
            'description': 'RESTful API service built with FastAPI and Pydantic',
            'tags': ['fastapi', 'rest', 'api', 'python']
        },
        {
            'name': 'testing-pytest-suite',
            'title': 'Python Testing Suite',
            'category': 'testing',
            'tech_stack': 'python-pytest',
            'description': 'Comprehensive testing setup with pytest, coverage, and CI integration',
            'tags': ['pytest', 'testing', 'coverage', 'ci']
        }
    ]

    for template_data in initial_templates:
        try:
            template_id = db.create_template(**template_data)
            click.echo(f"   ✅ Created: {template_data['name']}")
        except Exception as e:
            click.echo(f"   ❌ Failed to create {template_data['name']}: {e}")


if __name__ == '__main__':
    marketplace()