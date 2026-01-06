#!/usr/bin/env python3
"""
Setup script for Gas Town MEOW Stack Molecule Marketplace
Initializes the database and loads initial templates.
"""

import sys
import json
import logging
from pathlib import Path

# Add the marketplace modules to path
sys.path.append(str(Path(__file__).parent / "molecule-marketplace"))

from core.database.db import MoleculeDB
from core.storage.template_storage import TemplateStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_marketplace():
    """Initialize the molecule marketplace."""

    print("🧪 Setting up Gas Town MEOW Stack Molecule Marketplace...")

    # Initialize database and storage
    db = MoleculeDB()
    storage = TemplateStorage()

    # Load initial templates
    templates_dir = Path(__file__).parent / "molecule-marketplace" / "templates"

    initial_templates = [
        {
            'name': 'react-node-fullstack',
            'title': 'React + Node.js Full-Stack Application',
            'category': 'web-dev',
            'tech_stack': 'react-node',
            'description': 'Complete full-stack web application with React frontend, Node.js/Express backend, and PostgreSQL database',
            'version': '1.0.0',
            'author': 'Gas Town MEOW Stack',
            'tags': ['react', 'nodejs', 'express', 'postgresql', 'fullstack', 'typescript'],
            'difficulty': 'intermediate',
            'estimated_time': 45,
            'requirements': ['Node.js 18+', 'npm or yarn', 'PostgreSQL', 'Git'],
            'variables': {
                'project_name': {
                    'type': 'string',
                    'description': 'Name of your project',
                    'required': True,
                    'pattern': '^[a-z0-9-]+$'
                },
                'project_title': {
                    'type': 'string',
                    'description': 'Human-readable project title',
                    'required': True
                },
                'database_name': {
                    'type': 'string',
                    'description': 'PostgreSQL database name',
                    'required': True,
                    'default': '{{snake_case(project_name)}}_db'
                },
                'api_port': {
                    'type': 'integer',
                    'description': 'API server port',
                    'default': 3001
                },
                'frontend_port': {
                    'type': 'integer',
                    'description': 'Frontend development server port',
                    'default': 3000
                },
                'use_typescript': {
                    'type': 'boolean',
                    'description': 'Use TypeScript for both frontend and backend',
                    'default': True
                },
                'include_auth': {
                    'type': 'boolean',
                    'description': 'Include JWT authentication system',
                    'default': True
                },
                'include_testing': {
                    'type': 'boolean',
                    'description': 'Include testing setup (Jest, React Testing Library, Supertest)',
                    'default': True
                }
            },
            'readme_content': """
# React + Node.js Full-Stack Template

This template creates a complete full-stack web application with:

- React frontend with TypeScript support
- Node.js/Express backend API
- PostgreSQL database integration
- JWT authentication (optional)
- Testing setup with Jest
- Docker configuration for development

## Getting Started

1. Install the template:
   ```bash
   formula marketplace install react-node-fullstack ./my-project
   ```

2. Configure your project variables when prompted

3. Follow the generated README instructions to set up your development environment

## Features

- Modern React with hooks and functional components
- Express.js REST API with middleware
- PostgreSQL database with migrations
- JWT-based authentication system
- Comprehensive testing suite
- Docker development environment
- Production-ready configuration

## Requirements

- Node.js 18 or higher
- PostgreSQL database
- Git for version control

The template will guide you through the complete setup process.
            """
        },
        {
            'name': 'fastapi-rest-api',
            'title': 'FastAPI REST API Service',
            'category': 'api-dev',
            'tech_stack': 'python-fastapi',
            'description': 'High-performance REST API service built with FastAPI, Pydantic, and PostgreSQL',
            'version': '1.0.0',
            'author': 'Gas Town MEOW Stack',
            'tags': ['fastapi', 'python', 'rest', 'api', 'pydantic', 'postgresql'],
            'difficulty': 'beginner',
            'estimated_time': 30,
            'requirements': ['Python 3.8+', 'pip or poetry', 'PostgreSQL'],
            'variables': {
                'service_name': {
                    'type': 'string',
                    'description': 'Name of your API service',
                    'required': True,
                    'pattern': '^[a-z0-9-]+$'
                },
                'api_port': {
                    'type': 'integer',
                    'description': 'API server port',
                    'default': 8000
                },
                'include_auth': {
                    'type': 'boolean',
                    'description': 'Include JWT authentication',
                    'default': True
                },
                'include_database': {
                    'type': 'boolean',
                    'description': 'Include PostgreSQL database integration',
                    'default': True
                }
            }
        },
        {
            'name': 'pytest-testing-suite',
            'title': 'Python Testing Suite with pytest',
            'category': 'testing',
            'tech_stack': 'python-pytest',
            'description': 'Comprehensive testing setup with pytest, coverage reporting, and CI integration',
            'version': '1.0.0',
            'author': 'Gas Town MEOW Stack',
            'tags': ['pytest', 'testing', 'python', 'coverage', 'ci'],
            'difficulty': 'beginner',
            'estimated_time': 20,
            'requirements': ['Python 3.8+', 'pip'],
            'variables': {
                'project_name': {
                    'type': 'string',
                    'description': 'Name of your project',
                    'required': True
                },
                'include_coverage': {
                    'type': 'boolean',
                    'description': 'Include coverage reporting',
                    'default': True
                }
            }
        },
        {
            'name': 'docker-microservice',
            'title': 'Containerized Microservice',
            'category': 'deployment',
            'tech_stack': 'docker-kubernetes',
            'description': 'Docker-based microservice with Kubernetes deployment configurations',
            'version': '1.0.0',
            'author': 'Gas Town MEOW Stack',
            'tags': ['docker', 'kubernetes', 'microservice', 'deployment'],
            'difficulty': 'advanced',
            'estimated_time': 60,
            'requirements': ['Docker', 'Kubernetes (optional)'],
            'variables': {
                'service_name': {
                    'type': 'string',
                    'description': 'Name of your microservice',
                    'required': True
                },
                'namespace': {
                    'type': 'string',
                    'description': 'Kubernetes namespace',
                    'default': 'default'
                }
            }
        },
        {
            'name': 'vue-spa',
            'title': 'Vue.js Single Page Application',
            'category': 'web-dev',
            'tech_stack': 'vue-node',
            'description': 'Modern Vue.js SPA with Vue Router, Vuex, and API integration',
            'version': '1.0.0',
            'author': 'Gas Town MEOW Stack',
            'tags': ['vue', 'spa', 'vuex', 'router', 'frontend'],
            'difficulty': 'intermediate',
            'estimated_time': 35,
            'requirements': ['Node.js 16+', 'npm or yarn'],
            'variables': {
                'app_name': {
                    'type': 'string',
                    'description': 'Application name',
                    'required': True
                },
                'use_typescript': {
                    'type': 'boolean',
                    'description': 'Use TypeScript',
                    'default': False
                }
            }
        }
    ]

    # Create templates in database
    created_count = 0
    for template_data in initial_templates:
        try:
            # Check if template already exists
            existing = db.get_template(name=template_data['name'])
            if existing:
                print(f"  ⚠️  Template '{template_data['name']}' already exists, skipping...")
                continue

            # Create template
            template_id = db.create_template(**template_data)
            created_count += 1
            print(f"  ✅ Created template: {template_data['name']} (ID: {template_id})")

            # For the React template, also store the actual template files
            if template_data['name'] == 'react-node-fullstack':
                template_file_path = templates_dir / "web-dev" / "react-node-fullstack" / "template.toml"
                if template_file_path.exists():
                    template_content = template_file_path.read_text()
                    file_id = db.add_template_file(
                        template_id,
                        'template.toml',
                        template_content,
                        'toml',
                        False
                    )
                    print(f"    📄 Added template file: template.toml (ID: {file_id})")

        except Exception as e:
            print(f"  ❌ Failed to create template '{template_data['name']}': {e}")

    print(f"\n📦 Created {created_count} new templates")

    # Show marketplace statistics
    categories = db.get_categories()
    tech_stacks = db.get_tech_stacks()

    print(f"\n📊 Marketplace Summary:")
    print(f"  📂 Categories: {len(categories)}")
    print(f"  🛠️  Tech stacks: {len(tech_stacks)}")

    print(f"\n📂 Available Categories:")
    for category, count in categories:
        print(f"  • {category}: {count} templates")

    storage_stats = storage.get_storage_stats()
    print(f"\n💾 Storage: {storage_stats['total_size_mb']} MB in {storage_stats['storage_root']}")

    print(f"\n✅ Molecule Marketplace setup complete!")
    print(f"\n🚀 Try it out:")
    print(f"  formula marketplace list")
    print(f"  formula marketplace search react")
    print(f"  formula marketplace install react-node-fullstack ./my-project")


if __name__ == '__main__':
    setup_marketplace()