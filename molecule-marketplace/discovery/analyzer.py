"""
Codebase Analysis for Template Recommendations
Analyzes project structure, technologies, and patterns to suggest relevant templates.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
import logging

logger = logging.getLogger(__name__)


class CodebaseAnalyzer:
    """Analyzes codebases to understand their structure and technology stack."""

    def __init__(self):
        """Initialize the analyzer."""
        self.file_extensions = {
            # Web Technologies
            'javascript': ['.js', '.jsx', '.mjs'],
            'typescript': ['.ts', '.tsx'],
            'html': ['.html', '.htm'],
            'css': ['.css', '.scss', '.sass', '.less'],
            'vue': ['.vue'],
            'svelte': ['.svelte'],

            # Backend Languages
            'python': ['.py'],
            'java': ['.java'],
            'go': ['.go'],
            'rust': ['.rs'],
            'php': ['.php'],
            'ruby': ['.rb'],
            'csharp': ['.cs'],
            'cpp': ['.cpp', '.cc', '.cxx'],
            'c': ['.c'],

            # Configuration & Data
            'json': ['.json'],
            'yaml': ['.yml', '.yaml'],
            'toml': ['.toml'],
            'xml': ['.xml'],
            'sql': ['.sql'],

            # Documentation
            'markdown': ['.md', '.mdx'],
            'text': ['.txt'],

            # Shell & Scripts
            'shell': ['.sh', '.bash', '.zsh'],
            'dockerfile': ['Dockerfile'],
            'makefile': ['Makefile', 'makefile'],

            # Mobile
            'swift': ['.swift'],
            'kotlin': ['.kt', '.kts'],
            'dart': ['.dart'],

            # Other
            'r': ['.r', '.R'],
            'matlab': ['.m'],
            'scala': ['.scala'],
            'clojure': ['.clj', '.cljs'],
            'elixir': ['.ex', '.exs'],
        }

        self.framework_indicators = {
            # Frontend Frameworks
            'react': ['package.json', 'yarn.lock', 'node_modules'],
            'vue': ['vue.config.js', 'nuxt.config.js'],
            'angular': ['angular.json', '@angular'],
            'svelte': ['svelte.config.js'],
            'next': ['next.config.js'],
            'nuxt': ['nuxt.config.js'],
            'gatsby': ['gatsby-config.js'],

            # Backend Frameworks
            'fastapi': ['requirements.txt', 'pyproject.toml'],
            'django': ['manage.py', 'settings.py'],
            'flask': ['app.py', 'requirements.txt'],
            'express': ['package.json', 'node_modules'],
            'spring': ['pom.xml', 'build.gradle'],
            'rails': ['Gemfile', 'config/application.rb'],
            'laravel': ['composer.json', 'artisan'],

            # DevOps & Deployment
            'docker': ['Dockerfile', 'docker-compose.yml'],
            'kubernetes': ['*.yaml', '*.yml'],
            'terraform': ['*.tf'],
            'ansible': ['playbook.yml', 'inventory'],

            # Testing
            'pytest': ['pytest.ini', 'conftest.py'],
            'jest': ['jest.config.js'],
            'mocha': ['.mocharc.*'],
            'cypress': ['cypress.json'],

            # Build Tools
            'webpack': ['webpack.config.js'],
            'vite': ['vite.config.js'],
            'rollup': ['rollup.config.js'],
            'parcel': ['.parcelrc'],

            # Databases
            'postgresql': ['*.sql', 'migrations'],
            'mongodb': ['*.js'],
            'redis': ['redis.conf'],
        }

    def analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """Analyze a project and return comprehensive information."""

        analysis = {
            'path': str(project_path),
            'languages': {},
            'frameworks': [],
            'file_types': {},
            'directory_structure': {},
            'config_files': [],
            'package_managers': [],
            'testing_setup': [],
            'ci_cd': [],
            'documentation': [],
            'project_type': None,
            'complexity_score': 0,
            'suggestions': []
        }

        if not project_path.exists():
            logger.warning(f"Project path does not exist: {project_path}")
            return analysis

        try:
            # Analyze file structure
            self._analyze_files(project_path, analysis)

            # Detect frameworks and tools
            self._detect_frameworks(project_path, analysis)

            # Analyze package management
            self._analyze_package_management(project_path, analysis)

            # Determine project type
            self._determine_project_type(analysis)

            # Calculate complexity score
            self._calculate_complexity(analysis)

            # Generate suggestions
            self._generate_suggestions(analysis)

            logger.info(f"Analyzed project: {len(analysis['languages'])} languages, "
                       f"{len(analysis['frameworks'])} frameworks detected")

        except Exception as e:
            logger.error(f"Error analyzing project {project_path}: {e}")

        return analysis

    def _analyze_files(self, project_path: Path, analysis: Dict[str, Any]):
        """Analyze file types and languages in the project."""

        skip_dirs = {'.git', '.venv', 'venv', 'node_modules', '__pycache__',
                    '.mypy_cache', 'dist', 'build', '.next', '.nuxt'}

        file_count = 0
        max_files = 10000  # Prevent analyzing huge repos

        for root, dirs, files in os.walk(project_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            root_path = Path(root)
            relative_root = root_path.relative_to(project_path)

            if file_count > max_files:
                break

            for file_name in files:
                if file_count > max_files:
                    break

                file_path = root_path / file_name
                file_ext = file_path.suffix.lower()

                # Count file types
                if file_ext:
                    analysis['file_types'][file_ext] = analysis['file_types'].get(file_ext, 0) + 1

                # Detect languages
                for lang, extensions in self.file_extensions.items():
                    if file_ext in extensions or file_name in extensions:
                        analysis['languages'][lang] = analysis['languages'].get(lang, 0) + 1
                        break

                # Track config files
                if self._is_config_file(file_name):
                    analysis['config_files'].append(str(file_path.relative_to(project_path)))

                # Track documentation
                if file_ext in ['.md', '.rst', '.txt'] or 'readme' in file_name.lower():
                    analysis['documentation'].append(str(file_path.relative_to(project_path)))

                file_count += 1

    def _detect_frameworks(self, project_path: Path, analysis: Dict[str, Any]):
        """Detect frameworks and tools used in the project."""

        for framework, indicators in self.framework_indicators.items():
            for indicator in indicators:
                # Check for specific files
                if indicator.count('.') > 0 and not indicator.startswith('*'):
                    if (project_path / indicator).exists():
                        analysis['frameworks'].append(framework)
                        break

                # Check for patterns in package.json or similar
                elif framework in ['react', 'vue', 'angular'] and (project_path / 'package.json').exists():
                    package_json = project_path / 'package.json'
                    try:
                        content = json.loads(package_json.read_text())
                        deps = {**content.get('dependencies', {}), **content.get('devDependencies', {})}

                        if framework in str(deps).lower():
                            analysis['frameworks'].append(framework)
                            break
                    except Exception:
                        continue

                # Check for Python requirements
                elif framework in ['fastapi', 'django', 'flask'] and (project_path / 'requirements.txt').exists():
                    requirements = project_path / 'requirements.txt'
                    try:
                        content = requirements.read_text().lower()
                        if framework in content:
                            analysis['frameworks'].append(framework)
                            break
                    except Exception:
                        continue

    def _analyze_package_management(self, project_path: Path, analysis: Dict[str, Any]):
        """Analyze package management tools used."""

        package_files = {
            'npm': ['package.json', 'package-lock.json'],
            'yarn': ['yarn.lock'],
            'pnpm': ['pnpm-lock.yaml'],
            'pip': ['requirements.txt', 'requirements-dev.txt'],
            'poetry': ['pyproject.toml', 'poetry.lock'],
            'pipenv': ['Pipfile', 'Pipfile.lock'],
            'conda': ['environment.yml', 'environment.yaml'],
            'maven': ['pom.xml'],
            'gradle': ['build.gradle', 'build.gradle.kts'],
            'cargo': ['Cargo.toml'],
            'composer': ['composer.json'],
            'bundler': ['Gemfile'],
            'go_mod': ['go.mod']
        }

        for tool, files in package_files.items():
            for file_name in files:
                if (project_path / file_name).exists():
                    analysis['package_managers'].append(tool)
                    break

    def _determine_project_type(self, analysis: Dict[str, Any]):
        """Determine the primary type of project."""

        languages = analysis['languages']
        frameworks = analysis['frameworks']

        # Web application
        if any(fw in frameworks for fw in ['react', 'vue', 'angular', 'svelte', 'next']):
            analysis['project_type'] = 'web-frontend'
        elif any(fw in frameworks for fw in ['express', 'fastapi', 'django', 'flask', 'spring', 'rails']):
            analysis['project_type'] = 'web-backend'
        elif 'javascript' in languages and 'html' in languages:
            analysis['project_type'] = 'web-frontend'

        # API/Microservice
        elif any(fw in frameworks for fw in ['fastapi', 'express', 'spring']) or 'api' in str(analysis['config_files']).lower():
            analysis['project_type'] = 'api'

        # Mobile application
        elif any(lang in languages for lang in ['swift', 'kotlin', 'dart']):
            analysis['project_type'] = 'mobile'

        # Data Science/ML
        elif 'python' in languages and any(term in str(analysis).lower() for term in ['jupyter', 'notebook', 'pandas', 'numpy']):
            analysis['project_type'] = 'data-science'

        # DevOps/Infrastructure
        elif any(fw in frameworks for fw in ['docker', 'kubernetes', 'terraform', 'ansible']):
            analysis['project_type'] = 'devops'

        # CLI Tool
        elif len(languages) == 1 and not frameworks:
            primary_lang = max(languages.keys(), key=languages.get)
            if primary_lang in ['python', 'go', 'rust']:
                analysis['project_type'] = 'cli-tool'

        # Library/Package
        elif any(pm in analysis['package_managers'] for pm in ['poetry', 'cargo', 'maven', 'composer']):
            analysis['project_type'] = 'library'

        # Default to general application
        else:
            analysis['project_type'] = 'application'

    def _calculate_complexity(self, analysis: Dict[str, Any]):
        """Calculate a complexity score based on project characteristics."""

        score = 0

        # Language diversity
        score += len(analysis['languages']) * 2

        # Framework usage
        score += len(analysis['frameworks']) * 3

        # File count (estimated)
        total_files = sum(analysis['file_types'].values())
        if total_files > 1000:
            score += 20
        elif total_files > 100:
            score += 10
        elif total_files > 50:
            score += 5

        # Configuration complexity
        score += len(analysis['config_files'])

        # Package managers (indicates dependency management)
        score += len(analysis['package_managers']) * 2

        analysis['complexity_score'] = min(score, 100)  # Cap at 100

    def _generate_suggestions(self, analysis: Dict[str, Any]):
        """Generate suggestions based on analysis."""

        suggestions = []

        # Testing suggestions
        if not any(fw in analysis['frameworks'] for fw in ['pytest', 'jest', 'mocha']):
            suggestions.append('Consider adding automated testing')

        # Documentation suggestions
        if not analysis['documentation']:
            suggestions.append('Add project documentation')

        # CI/CD suggestions
        if not any(cf for cf in analysis['config_files'] if 'ci' in cf.lower() or 'github' in cf.lower()):
            suggestions.append('Consider setting up CI/CD')

        # Docker suggestions
        if 'docker' not in analysis['frameworks'] and analysis['project_type'] in ['web-backend', 'api']:
            suggestions.append('Consider containerizing with Docker')

        analysis['suggestions'] = suggestions

    def _is_config_file(self, filename: str) -> bool:
        """Check if a file is a configuration file."""

        config_patterns = [
            'config', 'conf', '.env', 'settings', 'docker', 'makefile',
            'webpack', 'babel', 'eslint', 'prettier', 'jest', 'cypress',
            'package.json', 'requirements.txt', 'pyproject.toml',
            'Cargo.toml', 'go.mod', 'composer.json'
        ]

        filename_lower = filename.lower()
        return any(pattern in filename_lower for pattern in config_patterns)