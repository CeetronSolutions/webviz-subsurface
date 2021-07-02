from typing import List, Dict, Tuple
from openpyxl.chart.chartspace import ExternalData
import pandas as pd
import sys

if sys.version_info[0] == 3 and sys.version_info[1] >= 8:
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from uuid import uuid4

from webviz_config.common_cache import CACHE
from webviz_subsurface_components import (
    VectorCalculator,
    ExpressionInfo,
    VariableVectorMapInfo,
)


"""
    JSON Schema for predefined expressions configuration

    Used as schema input for json_schema.validate()
"""
PREDEFINED_EXPRESSIONS_JSON_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "required": ["expression", "variableVectorMap"],
        "properties": {
            "expression": {"type": "string", "minLength": 1},
            "variableVectorMap": {
                "type": "object",
                "minProperties": 1,
                "patternProperties": {"^[a-zA-Z]$": {"type": "string"}},
                "additionalProperties": False,
            },
        },
        "additionalProperties": False,
    },
}


class ConfigExpressionData(TypedDict):
    """Type definition for configuration of pre-defined calculated expressions

    Simplified data type to pre-define expressions for user.

    The ConfigExpressionData instance name is the name of the expression - i.e.
    when using a dictionary of ConfigExpressionData the expression name is the dict key

    expression: str, mathematical expression
    variableVectorMap: Dict[str,str], Dictionary with {key, value} = {variableName, vectorName}
    """

    expression: str
    variableVectorMap: Dict[str, str]


def validate_predefined_expression(
    expression: ExpressionInfo, vector_data: list
) -> Tuple[bool, str]:
    """
    Validates predefined expressions for usage in vector calculator

    Predefined expressions can be defined in configuration file. Validation will ensure valid
    mathematical expression parsing and matching equation variables and variable vector map.
    It will also verify provided vector names in map is represented in provided vector data

    Inputs:
    * expression: Predefined expression
    * vector_data: Vector data

    Returns:
    * Tuple of valid state and vaidation message. Validation message is empty for valid expression

    """
    parsed_expression: ExternalData = VectorCalculator.external_parse_data(expression)
    expr = expression["expression"]
    name = expression["name"]

    # Validate expression string
    if not parsed_expression["isValid"]:
        parse_message = parsed_expression["message"]
        message = f'Invalid mathematical expression {expr} in predefined expression "{name}". {parse_message}.'
        return False, message

    # Match variables in expression string and variable names in map
    expression_variables = parsed_expression["variables"]
    map_variables = [elm["variableName"] for elm in expression["variableVectorMap"]]
    if expression_variables != map_variables:
        message = f'Variables {map_variables} in variableVectorMap is inconsistent with variables {expression_variables} in equation "{expr}" for predefined expression "{name}"'
        return False, message

    # Validate vector names
    variable_vector_dict = VectorCalculator.variable_vector_dict(
        expression["variableVectorMap"]
    )
    invalid_vectors: List[str] = []
    for variable in variable_vector_dict:
        vector_name = variable_vector_dict[variable]
        if not is_vector_name_existing(vector_name, vector_data):
            invalid_vectors.append(vector_name)
    if len(invalid_vectors) > 1:
        message = f'Vector names {invalid_vectors} in predefined expression "{name}" are not represented in vector data'
        return False, message
    if len(invalid_vectors) > 0:
        message = f'Vector name {invalid_vectors} in predefined expression "{name}" is not represented in vector data'
        return False, message

    return True, ""


def variable_vector_map_from_dict(
    variable_vector_dict: Dict[str, str]
) -> List[VariableVectorMapInfo]:
    variable_vector_map: List[VariableVectorMapInfo] = []
    for variable in variable_vector_dict:
        variable_vector_map.append(
            {
                "variableName": variable,
                "vectorName": [variable_vector_dict[variable]],
            }
        )
    return variable_vector_map


def expressions_from_config(
    expressions: Dict[str, ConfigExpressionData],
) -> List[ExpressionInfo]:
    output: List[ExpressionInfo] = []
    for expression in expressions:
        output.append(
            {
                "name": expression,
                "expression": expressions[expression]["expression"],
                "id": f"{uuid4()}",
                "variableVectorMap": variable_vector_map_from_dict(
                    expressions[expression]["variableVectorMap"]
                ),
                "isValid": False,  # Set default false? And expect seperate validation?
                "isDeletable": False,
            }
        )
    return output


def is_vector_name_existing(name: str, vector_data: list) -> bool:
    nodes = name.split(":")
    current_child_list = vector_data
    for node in nodes:
        found = False
        for child in current_child_list:
            if child["name"] == node:
                current_child_list = child["children"]
                found = True
                break
        if not found:
            return False
    return found


@CACHE.memoize(timeout=CACHE.TIMEOUT)
def get_selected_expressions(
    expressions: List[ExpressionInfo], selected_names: List[str]
) -> List[ExpressionInfo]:
    selected: List[ExpressionInfo] = []
    for name in selected_names:
        selected_expression: ExpressionInfo = next(
            (elm for elm in expressions if elm["name"] == name), None
        )
        if selected_expression is not None and selected_expression not in selected:
            selected.append(selected_expression)
    return selected


@CACHE.memoize(timeout=CACHE.TIMEOUT)
def get_calculated_vectors(
    expressions: List[ExpressionInfo],
    smry: pd.DataFrame,
) -> pd.DataFrame:
    calculated_vectors: pd.DataFrame = pd.DataFrame()
    for elm in expressions:
        name: str = elm["name"]
        expr: str = elm["expression"]
        var_vec_dict: Dict[str, str] = VectorCalculator.variable_vector_dict(
            elm["variableVectorMap"]
        )

        values: Dict[str, pd.Series] = {}
        for var in var_vec_dict:
            values[var] = smry[var_vec_dict[var]]

        evaluated_expr = VectorCalculator.evaluate_expression(expr, values)
        if evaluated_expr is not None:
            calculated_vectors[name] = evaluated_expr
    return calculated_vectors


@CACHE.memoize(timeout=CACHE.TIMEOUT)
def get_calculated_units(
    expressions: List[ExpressionInfo],
    units: pd.Series,
) -> pd.Series:
    # TODO Update expression handling
    # Future: check equal equal unit on each vector:
    # - if equal unit on + or -: x[m]+y[m] = [m]
    # - If unequal unit on + or -: Set unit "mixed"?
    # - *, / or ^: perform operators on units
    #
    # Utilize ./_datainput/units.py and/or ./_datainput/eclipse_unit.py
    #
    #
    # Now: parse expression str with VectorCalculator.parser.parse()
    # if valid, do string replace with units from smry_meta
    calculated_units: pd.Series = pd.Series()

    for expression in expressions:
        try:
            # Parse only for validation
            VectorCalculator.parser.parse(expression["expression"])
            unit_expr: str = expression["expression"]
            for elm in expression["variableVectorMap"]:
                unit_expr = unit_expr.replace(
                    elm["variableName"], units[elm["vectorName"][0]]
                )

            calculated_units[expression["name"]] = unit_expr
        except:
            continue
    return calculated_units
