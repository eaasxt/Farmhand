#!/usr/bin/env python3
"""
Enhanced Template Engine v2 - Gas Town Phase B Implementation
============================================================

Advanced template processing with property access, complex object support,
nested conditionals, improved type validation, and Gas Town integration.

New Features in v2:
- Property access: {{user.name}}, {{config.database.host}}
- Array/list access: {{items[0]}}, {{users[i].email}}
- Advanced conditionals: {% if user.role == 'admin' %}
- Nested loops: {% for category in categories %} {% for item in category.items %}
- Complex type validation with schema support
- Gas Town workflow integration
- Molecule cooking pipeline enhancements
"""

import json
import re
import os
import ast
import operator
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path
import subprocess
from dataclasses import dataclass
from enum import Enum


class VariableType(Enum):
    """Supported variable types for validation."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    OBJECT = "object"
    ANY = "any"


@dataclass
class TypeSchema:
    """Type schema for variable validation."""
    type: VariableType
    required: bool = True
    default: Any = None
    constraints: Optional[Dict[str, Any]] = None
    nested_schema: Optional[Dict[str, 'TypeSchema']] = None


class TemplateEngineV2:
    """Enhanced template processing with Gas Town v2 features."""

    def __init__(self):
        self.variables = {}
        self.type_schemas = {}
        self.functions = {
            # String transformations
            'snake_case': self._snake_case,
            'kebab_case': self._kebab_case,
            'camel_case': self._camel_case,
            'pascal_case': self._pascal_case,
            'upper': lambda x: str(x).upper(),
            'lower': lambda x: str(x).lower(),
            'title': lambda x: str(x).title(),
            'capitalize': lambda x: str(x).capitalize(),

            # List operations
            'join': lambda x, sep=',': sep.join(str(i) for i in x) if isinstance(x, list) else str(x),
            'length': lambda x: len(x) if hasattr(x, '__len__') else 0,
            'first': lambda x: x[0] if isinstance(x, (list, tuple)) and x else None,
            'last': lambda x: x[-1] if isinstance(x, (list, tuple)) and x else None,

            # Date/time formatting
            'date_format': self._format_date,
            'iso_date': lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x),

            # Type conversions
            'string': lambda x: str(x),
            'int': lambda x: int(x) if str(x).isdigit() else 0,
            'float': lambda x: float(x) if self._is_float(str(x)) else 0.0,

            # Gas Town specific
            'agent_name': self._extract_agent_name,
            'convoy_status': self._get_convoy_status,
            'bead_link': self._create_bead_link,
        }

        # Comparison operators for conditionals
        self.operators = {
            '==': operator.eq,
            '!=': operator.ne,
            '<': operator.lt,
            '<=': operator.le,
            '>': operator.gt,
            '>=': operator.ge,
            'in': lambda a, b: a in b,
            'not_in': lambda a, b: a not in b,
            'contains': lambda a, b: b in a,
            'starts_with': lambda a, b: str(a).startswith(str(b)),
            'ends_with': lambda a, b: str(a).endswith(str(b))
        }

    def process_template_v2(
        self,
        template_content: str,
        variables: Dict[str, Any],
        type_schemas: Optional[Dict[str, TypeSchema]] = None,
        validate_types: bool = True,
        enable_property_access: bool = True,
        enable_nested_loops: bool = True
    ) -> str:
        """
        Enhanced multi-pass template processing with v2 features.

        Processing order:
        1. Type validation with schema support
        2. Nested conditional block processing
        3. Nested loop construct processing
        4. Property access variable substitution
        5. Function pipeline application
        """

        self.variables = variables.copy()
        self.type_schemas = type_schemas or {}

        # Stage 1: Type validation
        if validate_types:
            validation_result = self._validate_variables_v2(variables)
            if not validation_result["valid"]:
                raise ValueError(f"Type validation failed: {validation_result['errors']}")

        # Stage 2: Process nested conditionals
        content = self._process_nested_conditionals(template_content)

        # Stage 3: Process nested loops
        if enable_nested_loops:
            content = self._process_nested_loops(content)
        else:
            content = self._process_simple_loops(content)

        # Stage 4: Property access variable substitution
        if enable_property_access:
            content = self._substitute_property_variables(content, self.variables)
        else:
            content = self._substitute_simple_variables(content, self.variables)

        return content

    def cook_molecule_v2(
        self,
        formula: str,
        ingredients: Dict[str, Any],
        cooking_stages: Optional[List[str]] = None,
        output_format: str = "text"
    ) -> Dict[str, Any]:
        """
        Enhanced 3-stage cooking pipeline: Formula → Protomolecule → Molecule.

        Supports multiple cooking stages and output formats.
        """

        cooking_stages = cooking_stages or ["validate", "process", "finalize"]
        cooking_log = []

        try:
            # Stage 1: Validation and preparation
            if "validate" in cooking_stages:
                validation_result = self._validate_cooking_ingredients(formula, ingredients)
                cooking_log.append({
                    "stage": "validation",
                    "status": "success" if validation_result["valid"] else "failed",
                    "details": validation_result
                })

                if not validation_result["valid"]:
                    raise ValueError(f"Cooking validation failed: {validation_result['errors']}")

            # Stage 2: Template processing (Protomolecule)
            if "process" in cooking_stages:
                protomolecule = self.process_template_v2(
                    template_content=formula,
                    variables=ingredients,
                    validate_types=True,
                    enable_property_access=True,
                    enable_nested_loops=True
                )
                cooking_log.append({
                    "stage": "processing",
                    "status": "success",
                    "protomolecule_size": len(protomolecule)
                })
            else:
                protomolecule = formula

            # Stage 3: Finalization and formatting (Molecule)
            if "finalize" in cooking_stages:
                molecule = self._finalize_molecule(protomolecule, output_format)
                cooking_log.append({
                    "stage": "finalization",
                    "status": "success",
                    "output_format": output_format,
                    "molecule_size": len(molecule)
                })
            else:
                molecule = protomolecule

            return {
                "status": "success",
                "formula": formula,
                "protomolecule": protomolecule,
                "molecule": molecule,
                "cooking_log": cooking_log,
                "cooked_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            cooking_log.append({
                "stage": "error",
                "status": "failed",
                "error": str(e)
            })

            return {
                "status": "failed",
                "error": str(e),
                "cooking_log": cooking_log,
                "failed_at": datetime.now(timezone.utc).isoformat()
            }

    def _validate_variables_v2(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced variable validation with schema support."""

        errors = []
        warnings = []

        for var_name, schema in self.type_schemas.items():
            if var_name not in variables:
                if schema.required:
                    errors.append(f"Required variable '{var_name}' is missing")
                elif schema.default is not None:
                    variables[var_name] = schema.default
                    warnings.append(f"Using default value for '{var_name}': {schema.default}")
                continue

            value = variables[var_name]
            validation_result = self._validate_single_variable(var_name, value, schema)

            if not validation_result["valid"]:
                errors.extend(validation_result["errors"])
            warnings.extend(validation_result.get("warnings", []))

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _validate_single_variable(self, name: str, value: Any, schema: TypeSchema) -> Dict[str, Any]:
        """Validate single variable against its schema."""

        errors = []
        warnings = []

        # Type validation
        if schema.type != VariableType.ANY:
            if not self._check_type_compatibility(value, schema.type):
                errors.append(f"Variable '{name}' expected {schema.type.value}, got {type(value).__name__}")

        # Constraint validation
        if schema.constraints:
            constraint_result = self._validate_constraints(name, value, schema.constraints)
            errors.extend(constraint_result["errors"])
            warnings.extend(constraint_result["warnings"])

        # Nested schema validation (for objects and dicts)
        if schema.nested_schema and isinstance(value, dict):
            for nested_name, nested_schema in schema.nested_schema.items():
                nested_value = value.get(nested_name)
                if nested_value is not None:
                    nested_result = self._validate_single_variable(
                        f"{name}.{nested_name}", nested_value, nested_schema
                    )
                    errors.extend(nested_result["errors"])
                    warnings.extend(nested_result["warnings"])

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _process_nested_conditionals(self, content: str) -> str:
        """Process nested conditional blocks with enhanced operators."""

        # Enhanced pattern to handle nested conditionals
        def process_conditional_level(text: str, depth: int = 0) -> str:
            if depth > 10:  # Prevent infinite recursion
                return text

            # Pattern for if...endif blocks with potential nesting
            pattern = r'{%\s*if\s+(.+?)\s*%}(.*?){%\s*endif\s*%}'

            def replace_conditional(match):
                condition = match.group(1).strip()
                block_content = match.group(2)

                # Evaluate condition with enhanced operators
                if self._evaluate_enhanced_condition(condition):
                    # Process nested conditionals in the content
                    return process_conditional_level(block_content, depth + 1)
                else:
                    return ""

            # Process conditionals at current level
            while re.search(pattern, text, re.DOTALL):
                text = re.sub(pattern, replace_conditional, text, flags=re.DOTALL)

            return text

        return process_conditional_level(content)

    def _process_nested_loops(self, content: str) -> str:
        """Process nested loop constructs with enhanced features."""

        def process_loop_level(text: str, depth: int = 0) -> str:
            if depth > 5:  # Prevent excessive nesting
                return text

            # Enhanced pattern for for...endfor loops
            pattern = r'{%\s*for\s+(\w+)\s+in\s+(\w+(?:\.\w+)*(?:\[\w*\])*)\s*%}(.*?){%\s*endfor\s*%}'

            def replace_loop(match):
                item_var = match.group(1)
                list_expr = match.group(2)
                loop_content = match.group(3)

                # Resolve list expression (supports property access)
                loop_list = self._resolve_variable_expression(list_expr)

                if not isinstance(loop_list, (list, tuple)):
                    return f"<!-- Loop error: {list_expr} is not iterable -->"

                result_parts = []
                for i, item in enumerate(loop_list):
                    # Create loop context with enhanced variables
                    loop_context = self.variables.copy()
                    loop_context[item_var] = item
                    loop_context[f"{item_var}_index"] = i
                    loop_context[f"{item_var}_first"] = i == 0
                    loop_context[f"{item_var}_last"] = i == len(loop_list) - 1

                    # Temporarily update variables for nested processing
                    old_variables = self.variables
                    self.variables = loop_context

                    # Process nested content (including nested loops)
                    processed_content = self._substitute_property_variables(
                        process_loop_level(loop_content, depth + 1),
                        loop_context
                    )

                    result_parts.append(processed_content)

                    # Restore variables
                    self.variables = old_variables

                return "".join(result_parts)

            # Process loops at current level
            while re.search(pattern, text, re.DOTALL):
                text = re.sub(pattern, replace_loop, text, flags=re.DOTALL)

            return text

        return process_loop_level(content)

    def _substitute_property_variables(self, content: str, context: Dict[str, Any]) -> str:
        """Enhanced variable substitution with property access support."""

        # Enhanced pattern for property access and function calls
        # Supports: {{var}}, {{obj.prop}}, {{arr[0]}}, {{var|function}}, {{obj.prop|function}}
        pattern = r'\{\{\s*([^|}]+?)(\|([^}]+?))?\s*\}\}'

        def replace_variable(match):
            var_expression = match.group(1).strip()
            function_chain = match.group(3)

            try:
                # Resolve variable expression (property access, array access, etc.)
                value = self._resolve_variable_expression(var_expression, context)

                # Apply function chain if specified
                if function_chain:
                    value = self._apply_function_chain(value, function_chain)

                return str(value)

            except Exception as e:
                return f"{{{{ ERROR: {str(e)} }}}}"

        return re.sub(pattern, replace_variable, content)

    def _resolve_variable_expression(
        self,
        expression: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Resolve complex variable expressions with property and array access.

        Supports:
        - Simple variables: user
        - Property access: user.name, config.database.host
        - Array access: items[0], users[i], data[key]
        - Mixed access: users[0].profile.name
        """

        if context is None:
            context = self.variables

        # Split expression into parts
        parts = self._parse_expression(expression)

        # Start with the root variable
        current_value = context.get(parts[0])
        if current_value is None:
            raise ValueError(f"Variable '{parts[0]}' not found")

        # Navigate through the expression
        for part in parts[1:]:
            if part['type'] == 'property':
                if isinstance(current_value, dict):
                    current_value = current_value.get(part['name'])
                elif hasattr(current_value, part['name']):
                    current_value = getattr(current_value, part['name'])
                else:
                    raise ValueError(f"Property '{part['name']}' not found")

            elif part['type'] == 'array':
                index = part['index']

                # Resolve index if it's a variable
                if isinstance(index, str) and not index.isdigit():
                    index = context.get(index, index)

                try:
                    if isinstance(index, str) and index.isdigit():
                        index = int(index)

                    current_value = current_value[index]
                except (IndexError, KeyError, TypeError):
                    raise ValueError(f"Index '{index}' not valid for array access")

            if current_value is None:
                break

        return current_value

    def _parse_expression(self, expression: str) -> List[Dict[str, Any]]:
        """Parse variable expression into navigable parts."""

        parts = []
        tokens = re.split(r'(\.|[\[\]])', expression)

        i = 0
        while i < len(tokens):
            token = tokens[i].strip()

            if not token or token in ['.', '[', ']']:
                i += 1
                continue

            if i == 0:
                # Root variable
                parts.append({'type': 'root', 'name': token})
            elif i > 0 and tokens[i-1] == '.':
                # Property access
                parts.append({'type': 'property', 'name': token})
            elif i > 0 and tokens[i-1] == '[':
                # Array access
                parts.append({'type': 'array', 'index': token})

            i += 1

        return parts

    def _evaluate_enhanced_condition(self, condition: str) -> bool:
        """Enhanced conditional expression evaluation with complex operators."""

        condition = condition.strip()

        # Handle negation
        if condition.startswith('!'):
            return not self._evaluate_enhanced_condition(condition[1:].strip())

        # Handle logical operators (and, or)
        for logical_op in [' and ', ' or ']:
            if logical_op in condition:
                parts = condition.split(logical_op, 1)
                left_result = self._evaluate_enhanced_condition(parts[0].strip())
                right_result = self._evaluate_enhanced_condition(parts[1].strip())

                if logical_op.strip() == 'and':
                    return left_result and right_result
                else:  # or
                    return left_result or right_result

        # Handle comparison operators
        for op_str, op_func in self.operators.items():
            if f" {op_str} " in condition:
                parts = condition.split(f" {op_str} ", 1)
                left_val = self._resolve_condition_value(parts[0].strip())
                right_val = self._resolve_condition_value(parts[1].strip())

                try:
                    return op_func(left_val, right_val)
                except Exception:
                    return False

        # Simple variable truth value
        return self._get_variable_truth_value(condition)

    def _resolve_condition_value(self, value_str: str) -> Any:
        """Resolve value in conditional expression (supports variables and literals)."""

        value_str = value_str.strip()

        # String literal
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]

        # Number literal
        if value_str.isdigit():
            return int(value_str)

        if self._is_float(value_str):
            return float(value_str)

        # Boolean literal
        if value_str.lower() in ['true', 'false']:
            return value_str.lower() == 'true'

        # Variable expression
        try:
            return self._resolve_variable_expression(value_str)
        except Exception:
            return value_str

    def _apply_function_chain(self, value: Any, function_chain: str) -> Any:
        """Apply chain of functions to value using pipe syntax."""

        functions = [f.strip() for f in function_chain.split('|') if f.strip()]

        for func_expr in functions:
            # Parse function and arguments
            if '(' in func_expr and ')' in func_expr:
                func_name = func_expr.split('(')[0]
                args_str = func_expr.split('(')[1].rstrip(')')
                args = [arg.strip().strip('"\'') for arg in args_str.split(',') if arg.strip()]
            else:
                func_name = func_expr
                args = []

            if func_name in self.functions:
                try:
                    if args:
                        value = self.functions[func_name](value, *args)
                    else:
                        value = self.functions[func_name](value)
                except Exception as e:
                    raise ValueError(f"Function '{func_name}' failed: {str(e)}")
            else:
                raise ValueError(f"Unknown function: {func_name}")

        return value

    def _validate_constraints(self, name: str, value: Any, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Validate value against constraints."""

        errors = []
        warnings = []

        # Length constraints
        if 'min_length' in constraints:
            if hasattr(value, '__len__') and len(value) < constraints['min_length']:
                errors.append(f"'{name}' length {len(value)} < minimum {constraints['min_length']}")

        if 'max_length' in constraints:
            if hasattr(value, '__len__') and len(value) > constraints['max_length']:
                errors.append(f"'{name}' length {len(value)} > maximum {constraints['max_length']}")

        # Value constraints
        if 'min_value' in constraints and isinstance(value, (int, float)):
            if value < constraints['min_value']:
                errors.append(f"'{name}' value {value} < minimum {constraints['min_value']}")

        if 'max_value' in constraints and isinstance(value, (int, float)):
            if value > constraints['max_value']:
                errors.append(f"'{name}' value {value} > maximum {constraints['max_value']}")

        # Pattern constraints
        if 'pattern' in constraints and isinstance(value, str):
            if not re.match(constraints['pattern'], value):
                errors.append(f"'{name}' does not match pattern {constraints['pattern']}")

        # Allowed values
        if 'allowed_values' in constraints:
            if value not in constraints['allowed_values']:
                errors.append(f"'{name}' value '{value}' not in allowed values: {constraints['allowed_values']}")

        return {"errors": errors, "warnings": warnings}

    def _check_type_compatibility(self, value: Any, expected_type: VariableType) -> bool:
        """Check if value is compatible with expected type."""

        type_checkers = {
            VariableType.STRING: lambda v: isinstance(v, str),
            VariableType.INTEGER: lambda v: isinstance(v, int) and not isinstance(v, bool),
            VariableType.FLOAT: lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            VariableType.BOOLEAN: lambda v: isinstance(v, bool),
            VariableType.LIST: lambda v: isinstance(v, (list, tuple)),
            VariableType.DICT: lambda v: isinstance(v, dict),
            VariableType.OBJECT: lambda v: hasattr(v, '__dict__') or isinstance(v, dict),
            VariableType.ANY: lambda v: True
        }

        checker = type_checkers.get(expected_type)
        return checker(value) if checker else False

    def _validate_cooking_ingredients(self, formula: str, ingredients: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ingredients for molecule cooking."""

        errors = []
        warnings = []

        # Check for required template variables
        required_vars = re.findall(r'\{\{\s*([^|}]+?)(?:\|[^}]+?)?\s*\}\}', formula)

        for var_expr in required_vars:
            root_var = var_expr.split('.')[0].split('[')[0]
            if root_var not in ingredients:
                errors.append(f"Required ingredient '{root_var}' missing for template")

        # Check for template syntax errors
        syntax_checks = [
            (r'{%\s*if\s+.*?%}.*?{%\s*endif\s*%}', "Conditional blocks"),
            (r'{%\s*for\s+.*?%}.*?{%\s*endfor\s*%}', "Loop constructs")
        ]

        for pattern, description in syntax_checks:
            matches = re.findall(pattern, formula, re.DOTALL)
            if matches:
                # Basic syntax validation would go here
                pass

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "required_variables": list(set(var_expr.split('.')[0] for var_expr in required_vars))
        }

    def _finalize_molecule(self, protomolecule: str, output_format: str) -> str:
        """Finalize protomolecule into final molecule format."""

        if output_format == "json":
            return json.dumps({"content": protomolecule}, indent=2)
        elif output_format == "yaml":
            return f"content: |\n  {protomolecule.replace(chr(10), chr(10) + '  ')}"
        elif output_format == "markdown":
            return f"# Generated Molecule\n\n{protomolecule}\n"
        else:  # text (default)
            return protomolecule

    # Helper functions
    def _snake_case(self, text: str) -> str:
        return re.sub(r'(?<!^)(?=[A-Z])', '_', str(text)).lower().replace(' ', '_').replace('-', '_')

    def _kebab_case(self, text: str) -> str:
        return re.sub(r'(?<!^)(?=[A-Z])', '-', str(text)).lower().replace(' ', '-').replace('_', '-')

    def _camel_case(self, text: str) -> str:
        components = str(text).replace('_', ' ').replace('-', ' ').split()
        return components[0].lower() + ''.join(x.title() for x in components[1:])

    def _pascal_case(self, text: str) -> str:
        components = str(text).replace('_', ' ').replace('-', ' ').split()
        return ''.join(x.title() for x in components)

    def _format_date(self, value: Any, format_str: str = "%Y-%m-%d") -> str:
        if hasattr(value, 'strftime'):
            return value.strftime(format_str)
        return str(value)

    def _is_float(self, text: str) -> bool:
        try:
            float(text)
            return True
        except ValueError:
            return False

    def _extract_agent_name(self, agent_spec: str) -> str:
        # Extract agent name from various formats
        if isinstance(agent_spec, dict):
            return agent_spec.get('name', 'Unknown')
        return str(agent_spec).split('@')[0]

    def _get_convoy_status(self, convoy_id: str) -> str:
        # Simulate convoy status lookup
        return f"convoy_{convoy_id}_status"

    def _create_bead_link(self, bead_id: str) -> str:
        return f"[{bead_id}](bead://{bead_id})"

    def _get_variable_truth_value(self, var_name: str) -> bool:
        """Get truth value of variable for conditionals."""
        try:
            value = self._resolve_variable_expression(var_name)
            if isinstance(value, bool):
                return value
            elif isinstance(value, (int, float)):
                return value != 0
            elif isinstance(value, str):
                return value.lower() not in ['', 'false', '0', 'no', 'none']
            elif isinstance(value, (list, dict)):
                return len(value) > 0
            else:
                return value is not None
        except Exception:
            return False

    def _process_simple_loops(self, content: str) -> str:
        """Fallback to simple loop processing if nested loops are disabled."""

        pattern = r'{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}(.*?){%\s*endfor\s*%}'

        def replace_loop(match):
            item_var = match.group(1)
            list_var = match.group(2)
            loop_content = match.group(3)

            if list_var not in self.variables:
                return f"<!-- Loop error: {list_var} not found -->"

            loop_list = self.variables[list_var]
            if not isinstance(loop_list, (list, tuple)):
                return f"<!-- Loop error: {list_var} is not iterable -->"

            result_parts = []
            for item in loop_list:
                # Create temporary context with loop variable
                loop_context = self.variables.copy()
                loop_context[item_var] = item

                # Simple variable substitution
                processed_content = self._substitute_simple_variables(loop_content, loop_context)
                result_parts.append(processed_content)

            return "".join(result_parts)

        # Process simple loops
        while re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, replace_loop, content, flags=re.DOTALL)

        return content

    def _substitute_simple_variables(self, content: str, context: Dict[str, Any]) -> str:
        """Simple variable substitution without property access."""

        pattern = r'\{\{\s*(\w+)(?:\|([^}]+?))?\s*\}\}'

        def replace_variable(match):
            var_name = match.group(1)
            function_chain = match.group(2)

            if var_name not in context:
                return f"{{{{ {var_name} }}}}"

            value = context[var_name]

            # Apply function chain if specified
            if function_chain:
                try:
                    value = self._apply_function_chain(value, function_chain)
                except Exception as e:
                    return f"{{{{ ERROR: {str(e)} }}}}"

            return str(value)

        return re.sub(pattern, replace_variable, content)


# CLI interface for Enhanced Template Engine v2

def test_template_v2():
    """Test template engine v2 capabilities."""

    engine = TemplateEngineV2()

    # Test complex template with property access
    template = """
# {{project.name|title}} - {{project.type|upper}}

## Team Information
Project Manager: {{team.manager.name}}
Email: {{team.manager.email}}

## Team Members
{% for member in team.members %}
- {{member.name}} ({{member.role}}) - {{member.email}}
  {% if member.skills %}
  Skills: {{member.skills|join:', '}}
  {% endif %}
{% endfor %}

## Configuration
Database Host: {{config.database.host}}
Database Port: {{config.database.port}}
API Endpoint: {{config.api.base_url}}/{{config.api.version}}

## Environment Settings
{% if config.environment == 'production' %}
🔴 PRODUCTION Environment - Use with caution!
Logging Level: ERROR
Debug Mode: Disabled
{% endif %}

{% if config.environment == 'development' %}
🟡 DEVELOPMENT Environment
Logging Level: DEBUG
Debug Mode: Enabled
{% endif %}

## Deployment Instructions
{% for step in deployment.steps %}
{{step_index + 1}}. {{step.action}}
   Command: `{{step.command}}`
   {% if step.notes %}
   Notes: {{step.notes}}
   {% endif %}

{% endfor %}

Generated at: {{metadata.generated_at|date_format('%Y-%m-%d %H:%M:%S')}}
"""

    # Test data with complex nested structure
    data = {
        "project": {
            "name": "gas town deere",
            "type": "multi-agent system"
        },
        "team": {
            "manager": {
                "name": "Alice Johnson",
                "email": "alice@example.com"
            },
            "members": [
                {
                    "name": "Bob Smith",
                    "role": "Backend Developer",
                    "email": "bob@example.com",
                    "skills": ["Python", "FastAPI", "PostgreSQL"]
                },
                {
                    "name": "Carol Davis",
                    "role": "Frontend Developer",
                    "email": "carol@example.com",
                    "skills": ["React", "TypeScript", "CSS"]
                },
                {
                    "name": "David Wilson",
                    "role": "DevOps Engineer",
                    "email": "david@example.com",
                    "skills": ["Docker", "Kubernetes", "AWS"]
                }
            ]
        },
        "config": {
            "environment": "production",
            "database": {
                "host": "prod-db.example.com",
                "port": 5432
            },
            "api": {
                "base_url": "https://api.example.com",
                "version": "v2"
            }
        },
        "deployment": {
            "steps": [
                {
                    "action": "Build Docker image",
                    "command": "docker build -t gas-town:latest .",
                    "notes": "Make sure all dependencies are included"
                },
                {
                    "action": "Deploy to production",
                    "command": "kubectl apply -f k8s/production.yaml",
                    "notes": "Monitor logs during deployment"
                },
                {
                    "action": "Verify deployment",
                    "command": "curl https://api.example.com/health",
                    "notes": None
                }
            ]
        },
        "metadata": {
            "generated_at": datetime.now()
        }
    }

    try:
        result = engine.process_template_v2(
            template_content=template,
            variables=data,
            validate_types=False,  # Skip validation for demo
            enable_property_access=True,
            enable_nested_loops=True
        )

        print("🎉 Enhanced Template Engine v2 Test Result:")
        print("=" * 60)
        print(result)
        print("=" * 60)
        print("✅ Template processing completed successfully!")

    except Exception as e:
        print(f"❌ Template processing failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_template_v2()
    else:
        print("Enhanced Template Engine v2 - Gas Town Phase B")
        print("Usage: python enhanced_template_engine_v2.py test")