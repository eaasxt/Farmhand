"""
AI-Powered Template Recommendation Engine
Uses project analysis to recommend relevant templates with confidence scoring.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

# Add the parent directory to path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.database.db import MoleculeDB

logger = logging.getLogger(__name__)


class TemplateRecommender:
    """Recommends templates based on project analysis."""

    def __init__(self):
        """Initialize the recommender."""
        self.db = MoleculeDB()

        # Technology mapping for template matching
        self.tech_mappings = {
            # Frontend technologies
            'react': ['web-dev', 'react-node', 'react-typescript'],
            'vue': ['web-dev', 'vue-node', 'vue-typescript'],
            'angular': ['web-dev', 'angular-typescript'],
            'svelte': ['web-dev', 'svelte-node'],
            'javascript': ['web-dev', 'vanilla-js'],
            'typescript': ['web-dev', 'typescript'],

            # Backend technologies
            'python': ['api-dev', 'python-fastapi', 'python-django', 'python-flask'],
            'fastapi': ['api-dev', 'python-fastapi'],
            'django': ['web-dev', 'python-django'],
            'flask': ['api-dev', 'python-flask'],
            'nodejs': ['api-dev', 'node-express'],
            'express': ['api-dev', 'node-express'],
            'go': ['api-dev', 'go-gin', 'go-fiber'],
            'rust': ['api-dev', 'rust-actix'],
            'java': ['api-dev', 'java-spring'],
            'spring': ['api-dev', 'java-spring'],

            # Full-stack combinations
            'react+nodejs': ['web-dev', 'react-node'],
            'vue+nodejs': ['web-dev', 'vue-node'],
            'react+python': ['web-dev', 'react-python'],

            # Testing
            'pytest': ['testing', 'python-pytest'],
            'jest': ['testing', 'javascript-jest'],
            'mocha': ['testing', 'javascript-mocha'],
            'cypress': ['testing', 'e2e-cypress'],

            # DevOps
            'docker': ['deployment', 'docker'],
            'kubernetes': ['deployment', 'kubernetes'],
            'terraform': ['deployment', 'terraform'],
            'ansible': ['deployment', 'ansible'],

            # Data & Analytics
            'jupyter': ['data-processing', 'jupyter-python'],
            'pandas': ['data-processing', 'data-analysis'],
            'numpy': ['data-processing', 'scientific-python'],

            # Mobile
            'swift': ['mobile', 'ios-swift'],
            'kotlin': ['mobile', 'android-kotlin'],
            'dart': ['mobile', 'flutter-dart'],
        }

        # Project type to category mapping
        self.project_type_mappings = {
            'web-frontend': ['web-dev'],
            'web-backend': ['api-dev', 'web-dev'],
            'api': ['api-dev'],
            'mobile': ['mobile'],
            'data-science': ['data-processing'],
            'devops': ['deployment'],
            'cli-tool': ['automation', 'cli'],
            'library': ['library'],
            'application': ['web-dev', 'api-dev']
        }

    def recommend_templates(self,
                          project_analysis: Dict[str, Any],
                          limit: int = 10) -> List[Dict[str, Any]]:
        """Recommend templates based on project analysis."""

        recommendations = []

        try:
            # Get all templates
            templates = self.db.list_templates(limit=1000)  # Get all templates

            # Score each template
            for template in templates:
                confidence, reasons = self._calculate_confidence(template, project_analysis)

                if confidence > 0.1:  # Only include templates with >10% confidence
                    recommendations.append({
                        'template': template,
                        'confidence': confidence,
                        'reasons': reasons
                    })

            # Sort by confidence (highest first)
            recommendations.sort(key=lambda x: x['confidence'], reverse=True)

            # Apply diversity filter to avoid too many similar templates
            recommendations = self._apply_diversity_filter(recommendations)

            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    def _calculate_confidence(self,
                            template: Dict[str, Any],
                            analysis: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Calculate confidence score for a template match."""

        confidence = 0.0
        reasons = []

        # Category matching
        project_type = analysis.get('project_type', '')
        template_category = template.get('category', '')

        if project_type in self.project_type_mappings:
            if template_category in self.project_type_mappings[project_type]:
                confidence += 0.3
                reasons.append(f"matches {project_type} project type")

        # Technology stack matching
        template_tech_stack = template.get('tech_stack', '')
        languages = analysis.get('languages', {})
        frameworks = analysis.get('frameworks', [])

        # Language matching
        for language in languages:
            if language in self.tech_mappings:
                for tech_stack in self.tech_mappings[language]:
                    if tech_stack in template_tech_stack:
                        confidence += 0.2
                        reasons.append(f"uses {language}")
                        break

        # Framework matching
        for framework in frameworks:
            if framework in self.tech_mappings:
                for tech_stack in self.tech_mappings[framework]:
                    if tech_stack in template_tech_stack:
                        confidence += 0.25
                        reasons.append(f"uses {framework} framework")
                        break

            # Direct framework name matching
            if framework in template_tech_stack:
                confidence += 0.3
                reasons.append(f"exact {framework} match")

        # Tag matching
        template_tags = template.get('tags', [])
        if isinstance(template_tags, str):
            import json
            try:
                template_tags = json.loads(template_tags)
            except:
                template_tags = []

        for tag in template_tags:
            tag_lower = tag.lower()

            # Check against languages
            for language in languages:
                if language in tag_lower:
                    confidence += 0.1
                    reasons.append(f"tagged with {tag}")

            # Check against frameworks
            for framework in frameworks:
                if framework in tag_lower:
                    confidence += 0.15
                    reasons.append(f"tagged with {tag}")

        # Complexity matching
        complexity_score = analysis.get('complexity_score', 0)
        template_difficulty = template.get('difficulty', 'beginner')

        if complexity_score < 20 and template_difficulty == 'beginner':
            confidence += 0.1
            reasons.append("appropriate for project complexity")
        elif 20 <= complexity_score < 60 and template_difficulty == 'intermediate':
            confidence += 0.15
            reasons.append("matches intermediate complexity")
        elif complexity_score >= 60 and template_difficulty == 'advanced':
            confidence += 0.2
            reasons.append("suitable for complex project")

        # Popular templates get a small boost
        download_count = template.get('download_count', 0)
        if download_count > 100:
            confidence += 0.05
            reasons.append("popular template")

        # High-rated templates get a boost
        rating = template.get('rating_avg', 0.0)
        if rating >= 4.0:
            confidence += 0.1
            reasons.append("highly rated")

        # Missing framework penalty
        if not frameworks and template_category in ['web-dev', 'api-dev']:
            confidence *= 0.8  # Reduce confidence for framework-heavy templates

        # Ensure confidence doesn't exceed 1.0
        confidence = min(confidence, 1.0)

        return confidence, reasons

    def _apply_diversity_filter(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply diversity filtering to avoid too many similar templates."""

        if len(recommendations) <= 5:
            return recommendations

        filtered = []
        seen_categories = set()
        seen_tech_stacks = set()

        # First pass: Take best from each category
        for rec in recommendations:
            template = rec['template']
            category = template.get('category')
            tech_stack = template.get('tech_stack')

            if category not in seen_categories:
                filtered.append(rec)
                seen_categories.add(category)
                seen_tech_stacks.add(tech_stack)

        # Second pass: Fill remaining slots with diverse tech stacks
        remaining_slots = 10 - len(filtered)
        for rec in recommendations:
            if len(filtered) >= remaining_slots + len(seen_categories):
                break

            if rec in filtered:
                continue

            template = rec['template']
            tech_stack = template.get('tech_stack')

            if tech_stack not in seen_tech_stacks:
                filtered.append(rec)
                seen_tech_stacks.add(tech_stack)

        # Third pass: Fill any remaining slots with highest confidence
        for rec in recommendations:
            if len(filtered) >= 10:
                break

            if rec not in filtered:
                filtered.append(rec)

        return filtered

    def get_template_recommendations_for_beads(self, project_path: str) -> List[Dict[str, Any]]:
        """Get template recommendations that can be broken down into beads."""

        from .analyzer import CodebaseAnalyzer

        analyzer = CodebaseAnalyzer()
        analysis = analyzer.analyze_project(Path(project_path))

        recommendations = self.recommend_templates(analysis, limit=5)

        # Filter for templates that work well with beads decomposition
        bead_friendly = []

        for rec in recommendations:
            template = rec['template']
            category = template.get('category', '')

            # These categories typically decompose well into atomic tasks
            if category in ['web-dev', 'api-dev', 'testing', 'deployment']:
                rec['bead_potential'] = self._assess_bead_potential(template)
                bead_friendly.append(rec)

        return bead_friendly

    def _assess_bead_potential(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Assess how well a template can be decomposed into beads."""

        potential = {
            'decomposability': 'medium',
            'estimated_beads': 5,
            'parallel_tracks': [],
            'complexity_factors': []
        }

        category = template.get('category', '')
        tech_stack = template.get('tech_stack', '')

        # Estimate based on template characteristics
        if category == 'web-dev':
            potential['estimated_beads'] = 8
            potential['parallel_tracks'] = ['frontend', 'backend', 'database', 'deployment']

            if 'fullstack' in template.get('name', '').lower():
                potential['estimated_beads'] = 12
                potential['decomposability'] = 'high'

        elif category == 'api-dev':
            potential['estimated_beads'] = 6
            potential['parallel_tracks'] = ['api', 'database', 'testing', 'documentation']
            potential['decomposability'] = 'high'

        elif category == 'testing':
            potential['estimated_beads'] = 4
            potential['parallel_tracks'] = ['unit-tests', 'integration-tests', 'e2e-tests']
            potential['decomposability'] = 'medium'

        elif category == 'deployment':
            potential['estimated_beads'] = 7
            potential['parallel_tracks'] = ['containerization', 'orchestration', 'monitoring', 'ci-cd']
            potential['decomposability'] = 'high'

        # Complexity factors
        if template.get('difficulty') == 'advanced':
            potential['complexity_factors'].append('advanced configuration')
            potential['estimated_beads'] += 3

        if 'microservice' in template.get('description', '').lower():
            potential['complexity_factors'].append('microservice architecture')
            potential['estimated_beads'] += 2

        return potential