from typing import Optional

import pandas as pd
import numpy as np
from dash import dash_table, html

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel

from ....utils.table_and_figure_utils import (
    create_data_table,
    create_table_columns,
)

from ....utils.utils import move_to_end_of_list

def add_fluid_zone_column(
    dframe: pd.DataFrame, filters: dict
) -> pd.DataFrame:
    if "FLUID_ZONE" not in dframe and "FLUID_ZONE" in filters:
        dframe["FLUID_ZONE"] = (" + ").join(filters["FLUID_ZONE"])
    return dframe

def compute_highlighted_col(
    df: pd.DataFrame, response: str, value1: str, selections: dict
) -> np.ndarray:
    highlight_mask = (df[response][value1] > selections["Ignore <"]) & (
        df[response]["diff (%)"].abs() > selections["Accept value"]
    )
    return np.where(highlight_mask, "yes", "no")

def create_comparison_df(
    volumemodel: InplaceVolumesModel,
    compare_on: str,
    responses: list,
    selections: dict,
    filters: dict,
    groups: list,
    abssort_on: str = "diff (%)",
    rename_diff_col: bool = False,
) -> pd.DataFrame:

    filters_subset = {
        key: value for key, value in filters.items() if key in ["REGION", "ZONE"]
    }

    resp = selections["Response"]
    adiitional_groups = [
        x
        for x in ["SOURCE", "ENSEMBLE", "SENSNAME_CASE"]
        if x in volumemodel.selectors
    ]
    groups = groups + adiitional_groups
    df = volumemodel.get_df(filters_subset, groups=groups)

    # filter dataframe and set values to compare against
    if not "|" in selections["value1"]:
        value1, value2 = selections["value1"], selections["value2"]
        df = df[df[compare_on].isin([value1, value2])]
    else:
        ens1, sens1 = selections["value1"].split("|")
        ens2, sens2 = selections["value2"].split("|")
        if ens1 == ens2:
            compare_on = "SENSNAME_CASE"
        value1, value2 = (sens1, sens2) if ens1 == ens2 else (ens1, ens2)

        df = df[
            ((df["ENSEMBLE"] == ens1) & (df["SENSNAME_CASE"] == sens1))
            | ((df["ENSEMBLE"] == ens2) & (df["SENSNAME_CASE"] == sens2))
        ]

    # if no data left, or one of the selected SOURCE/ENSEMBLE is not present
    # in the dataframe after filtering, return empty dataframe
    if df.empty or any(x not in df[compare_on].values for x in [value1, value2]):
        return pd.DataFrame()

    df = df.loc[:, groups + responses].pivot_table(
        columns=compare_on,
        index=[x for x in groups if x not in [compare_on, "SENSNAME_CASE"]],
    )
    responses = [x for x in responses if x in df]
    for col in responses:
        df[col, "diff"] = df[col][value2] - df[col][value1]
        df[col, "diff (%)"] = ((df[col][value2] / df[col][value1]) - 1) * 100
        df.loc[df[col]["diff"] == 0, (col, "diff (%)")] = 0
    df = df[responses].replace([np.inf, -np.inf], np.nan).reset_index()

    # remove rows where the selected response is nan
    # can happen for properties where the volume columns are 0
    df = df.loc[~((df[resp][value1].isna()) & (df[resp][value2].isna()))]
    if selections["Remove zeros"]:
        df = df.loc[~((df[resp]["diff"] == 0) & (df[resp][value1] == 0))]

    df["highlighted"] = compute_highlighted_col(df, resp, value1, selections)
    df.columns = df.columns.map(" ".join).str.strip(" ")

    # remove BO∕BG columns if they are nan and drop SOURCE/ENSMEBLE column
    dropcols = [
        x for x in df.columns[df.isna().all()] if x.split(" ")[0] in ["BO", "BG"]
    ] + adiitional_groups
    df = df[[x for x in df.columns if x not in dropcols]]

    if rename_diff_col:
        df = df.rename(
            columns={f"{resp} diff": "diff", f"{resp} diff (%)": "diff (%)"}
        )
    df = add_fluid_zone_column(df, filters_subset)
    return df.sort_values(by=[abssort_on], key=abs, ascending=False)

def find_higlighted_real_count(
    row: pd.Series, df_per_real: pd.DataFrame, groups: list
) -> str:
    query = " & ".join([f"{col}=='{row[col]}'" for col in groups])
    result = df_per_real.query(query) if groups else df_per_real
    return str(len(result[result["highlighted"] == "yes"]))

def create_comparison_table(
    tabletype: str,
    df: pd.DataFrame,
    groupby: list,
    selections: dict,
    filters: dict,
    compare_on: str,
    use_si_format: Optional[bool] = None,
    volumemodel: Optional[InplaceVolumesModel] = None,
) -> dash_table.DataTable:

    diff_mode_percent = selections["Diff mode"] == "diff (%)"

    if selections["Remove non-highlighted"]:
        df = df.loc[df["highlighted"] == "yes"]
        if df.empty:
            return html.Div(
                [
                    html.Div("All data outside highlight criteria!"),
                    html.Div(
                        "To see the data turn off setting 'Display only highlighted data'"
                    ),
                ]
            )

    if tabletype == "multi-response table":
        diff_cols = [x for x in df.columns if x.endswith(selections["Diff mode"])]
        rename_dict = {x: x.split(" ")[0] for x in diff_cols}
        df = df[groupby + diff_cols + ["highlighted"]].rename(columns=rename_dict)
        df = add_fluid_zone_column(df, filters)

        columns = create_table_columns(
            columns=move_to_end_of_list("FLUID_ZONE", df.columns),
            text_columns=groupby,
            use_si_format=volumemodel.volume_columns
            if volumemodel is not None and not diff_mode_percent
            else None,
            use_percentage=list(df.columns) if diff_mode_percent else None,
        )
    else:
        columns = create_table_columns(
            columns=move_to_end_of_list("FLUID_ZONE", df.columns),
            text_columns=groupby,
            use_si_format=list(df.columns) if use_si_format else None,
            use_percentage=["diff (%)"],
        )

    return create_data_table(
        selectors=groupby,
        columns=columns,
        data=df.to_dict("records"),
        table_id={"table_id": f"{compare_on}-comp-table"},
        style_cell={"textAlign": "center"},
        style_data_conditional=[
            {
                "if": {"filter_query": "{highlighted} = 'yes'"},
                "backgroundColor": "rgb(230, 230, 230)",
                "fontWeight": "bold",
            },
        ],
        style_cell_conditional=[
            {"if": {"column_id": "highlighted"}, "display": "None"}
        ],
    )
