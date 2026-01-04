"""
Template Processing Engine
Handles template processing, variable substitution, and workflow generation.
"""

import re
import json
import yaml
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Engine for processing templates and generating workflows."""

    def __init__(self):
        """Initialize template engine."""
        self.variable_pattern = re.compile(r'\{\{(\w+)(?:\|([^}]+))?\}\}')
        self.conditional_pattern = re.compile(r'\{\%\s*if\s+(\w+)\s*\%\}(.*?)\{\%\s*endif\s*\%\}', re.DOTALL)
        self.loop_pattern = re.compile(r'\{\%\s*for\s+(\w+)\s+in\s+(\w+)\s*\%\}(.*?)\{\%\s*endfor\s*\%\}', re.DOTALL)

    def process_template(self,
                        template_content: str,
                        variables: Dict[str, Any],
                        file_path: str = "") -> str:
        """Process template content with variable substitution and logic."""

        # First pass: Handle conditionals
        processed = self._process_conditionals(template_content, variables)

        # Second pass: Handle loops
        processed = self._process_loops(processed, variables)

        # Third pass: Handle variables
        processed = self._process_variables(processed, variables)

        # Fourth pass: Handle special functions
        processed = self._process_functions(processed, variables, file_path)

        return processed

    def _process_variables(self, content: str, variables: Dict[str, Any]) -> str:
        """Process variable substitutions."""

        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) else ""

            if var_name in variables:
                value = variables[var_name]
                # Handle different value types
                if isinstance(value, (list, dict)):
                    return json.dumps(value)
                return str(value)
            else:
                return default_value

        return self.variable_pattern.sub(replace_var, content)

    def _process_conditionals(self, content: str, variables: Dict[str, Any]) -> str:
        """Process conditional blocks."""

        def replace_conditional(match):
            condition_var = match.group(1)
            conditional_content = match.group(2)

            # Check if condition is truthy
            if condition_var in variables and self._is_truthy(variables[condition_var]):
                return conditional_content
            else:
                return ""

        return self.conditional_pattern.sub(replace_conditional, content)

    def _process_loops(self, content: str, variables: Dict[str, Any]) -> str:
        """Process loop blocks."""

        def replace_loop(match):
            item_var = match.group(1)
            list_var = match.group(2)
            loop_content = match.group(3)

            if list_var not in variables:
                return ""

            list_value = variables[list_var]
            if not isinstance(list_value, list):
                return ""

            result = []
            for item in list_value:
                # Create a new variable context for the loop
                loop_vars = variables.copy()
                loop_vars[item_var] = item

                # Process the loop content with the item variable
                processed_content = self._process_variables(loop_content, loop_vars)
                result.append(processed_content)

            return "".join(result)

        return self.loop_pattern.sub(replace_loop, content)

    def _process_functions(self, content: str, variables: Dict[str, Any], file_path: str) -> str:
        """Process special template functions."""

        # {{ upper(variable) }}
        content = re.sub(r'\{\{\s*upper\((\w+)\)\s*\}\}',
                        lambda m: str(variables.get(m.group(1), "")).upper(), content)

        # {{ lower(variable) }}
        content = re.sub(r'\{\{\s*lower\((\w+)\)\s*\}\}',
                        lambda m: str(variables.get(m.group(1), "")).lower(), content)

        # {{ snake_case(variable) }}
        content = re.sub(r'\{\{\s*snake_case\((\w+)\)\s*\}\}',
                        lambda m: self._to_snake_case(str(variables.get(m.group(1), ""))), content)

        # {{ kebab_case(variable) }}
        content = re.sub(r'\{\{\s*kebab_case\((\w+)\)\s*\}\}',
                        lambda m: self._to_kebab_case(str(variables.get(m.group(1), ""))), content)

        # {{ camel_case(variable) }}
        content = re.sub(r'\{\{\s*camel_case\((\w+)\)\s*\}\}',
                        lambda m: self._to_camel_case(str(variables.get(m.group(1), ""))), content)

        # {{ file_name }} - get current file name without extension
        content = content.replace("{{ file_name }}", Path(file_path).stem)

        # {{ file_ext }} - get current file extension
        content = content.replace("{{ file_ext }}", Path(file_path).suffix.lstrip('.'))

        return content

    def _is_truthy(self, value: Any) -> bool:
        """Check if a value is truthy."""
        if isinstance(value, str):
            return value.lower() not in ['', 'false', 'no', '0', 'null', 'none']
        elif isinstance(value, (list, dict)):
            return len(value) > 0
        elif isinstance(value, (int, float)):
            return value != 0
        else:
            return bool(value)

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case."""
        text = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        text = re.sub('([a-z0-9])([A-Z])', r'\1_\2', text).lower()
        text = re.sub(r'[\s-]+', '_', text)
        return text

    def _to_kebab_case(self, text: str) -> str:
        """Convert text to kebab-case."""
        return self._to_snake_case(text).replace('_', '-')

    def _to_camel_case(self, text: str) -> str:
        """Convert text to camelCase."""
        words = re.split(r'[\s_-]+', text.lower())
        return words[0] + ''.join(word.capitalize() for word in words[1:])

    def extract_variables(self, template_content: str) -> List[str]:
        """Extract all variable names used in a template."""
        variables = set()

        # Extract from variable patterns
        for match in self.variable_pattern.finditer(template_content):
            variables.add(match.group(1))

        # Extract from conditionals
        for match in self.conditional_pattern.finditer(template_content):
            variables.add(match.group(1))

        # Extract from loops
        for match in self.loop_pattern.finditer(template_content):
            variables.add(match.group(2))  # The list variable

        # Extract from functions
        function_vars = re.findall(r'\{\{\s*\w+\((\w+)\)\s*\}\}', template_content)
        variables.update(function_vars)

        return sorted(list(variables))

    def generate_workflow_toml(self,
                             template_name: str,
                             config: Dict[str, Any],
                             steps: List[Dict[str, Any]]) -> str:
        """Generate a MEOW workflow TOML file."""

        workflow = {
            'metadata': {
                'name': template_name,
                'generated_from_template': True,
                'template_config': config
            },
            'steps': {}
        }

        # Process each step
        for i, step in enumerate(steps):
            step_name = step.get('name', f'step_{i+1}')
            step_config = {
                'type': step.get('type', 'shell'),
                'command': step.get('command', ''),
                'description': step.get('description', ''),
                'depends_on': step.get('depends_on', [])
            }

            # Add environment variables if present
            if 'env' in step:
                step_config['env'] = step['env']

            # Add working directory if present
            if 'working_dir' in step:
                step_config['working_dir'] = step['working_dir']

            workflow['steps'][step_name] = step_config

        # Convert to TOML format
        import toml
        return toml.dumps(workflow)

    def validate_template_config(self,
                                config: Dict[str, Any],
                                schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate template configuration against schema."""

        errors = []

        # Check required variables
        required = schema.get('required', [])
        for var_name in required:
            if var_name not in config:
                errors.append(f"Missing required variable: {var_name}")

        # Check variable types
        properties = schema.get('properties', {})
        for var_name, var_config in properties.items():
            if var_name in config:
                expected_type = var_config.get('type', 'string')
                actual_value = config[var_name]

                if expected_type == 'string' and not isinstance(actual_value, str):
                    errors.append(f"Variable '{var_name}' should be a string")
                elif expected_type == 'integer' and not isinstance(actual_value, int):
                    errors.append(f"Variable '{var_name}' should be an integer")
                elif expected_type == 'boolean' and not isinstance(actual_value, bool):
                    errors.append(f"Variable '{var_name}' should be a boolean")
                elif expected_type == 'array' and not isinstance(actual_value, list):
                    errors.append(f"Variable '{var_name}' should be an array")

                # Check enum values
                if 'enum' in var_config and actual_value not in var_config['enum']:
                    errors.append(f"Variable '{var_name}' must be one of: {var_config['enum']}")

                # Check string patterns
                if 'pattern' in var_config and isinstance(actual_value, str):
                    if not re.match(var_config['pattern'], actual_value):
                        errors.append(f"Variable '{var_name}' doesn't match pattern: {var_config['pattern']}")

        return len(errors) == 0, errors

    def get_template_preview(self,
                           template_files: Dict[str, str],
                           config: Dict[str, Any]) -> Dict[str, str]:
        """Generate a preview of processed template files."""

        preview = {}

        for file_path, content in template_files.items():
            try:
                processed = self.process_template(content, config, file_path)
                preview[file_path] = processed
            except Exception as e:
                preview[file_path] = f"Error processing template: {e}"

        return preview