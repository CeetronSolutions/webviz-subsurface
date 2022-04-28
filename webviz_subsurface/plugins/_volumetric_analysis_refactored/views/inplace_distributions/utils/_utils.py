from typing import List, Optional

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from dash import dash_table

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel

from ....utils.table_and_figure_utils import create_data_table, create_table_columns
from ....utils.utils import move_to_end_of_list

# pylint: disable=too-many-locals
def make_tables(
    dframe: pd.DataFrame,
    responses: list,
    volumemodel: InplaceVolumesModel,
    selections: dict,
    table_type: str,
    view_height: float,
    groups: Optional[list] = None,
) -> List[Optional[dash_table.DataTable]]:

    groups = groups if groups is not None else []

    if table_type == "Statistics table":
        statcols = ["Mean", "Stddev", "P90", "P10", "Min", "Max"]
        groups = [x for x in groups if x != "REAL"]
        responses = [x for x in responses if x != "REAL" and x is not None]
        df_groups = dframe.groupby(groups) if groups else [(None, dframe)]

        data_properties = []
        data_volcols = []
        for response in responses:
            if not is_numeric_dtype(dframe[response]):
                continue
            for name, df in df_groups:
                values = df[response]
                data = {
                    "Mean": values.mean(),
                    "Stddev": values.std(),
                    "P10": np.nanpercentile(values, 90),
                    "P90": np.nanpercentile(values, 10),
                    "Min": values.min(),
                    "Max": values.max(),
                }
                if "FLUID_ZONE" not in groups:
                    data.update(
                        FLUID_ZONE=(" + ").join(selections["filters"]["FLUID_ZONE"])
                    )

                for idx, group in enumerate(groups):
                    data[group] = (
                        name if not isinstance(name, tuple) else list(name)[idx]
                    )
                if response in volumemodel.volume_columns:
                    data["Response"] = response
                    data_volcols.append(data)
                else:
                    data["Property"] = response
                    data_properties.append(data)

        if data_volcols and data_properties:
            view_height = view_height / 2

        return [
            create_data_table(
                selectors=volumemodel.selectors,
                columns=create_table_columns(
                    columns=move_to_end_of_list(
                        "FLUID_ZONE", [col] + groups + statcols
                    ),
                    text_columns=[col] + groups,
                    use_si_format=statcols if col == "Response" else None,
                ),
                data=data,
                height=f"{view_height}vh",
                table_id={"table_id": f"{col}"},
            )
            for col, data in zip(
                ["Response", "Property"], [data_volcols, data_properties]
            )
        ]

    # if table type Mean table
    groupby_real = (
        selections["Group by"] is not None and "REAL" in selections["Group by"]
    )
    if "REAL" in groups and not groupby_real:
        groups.remove("REAL")

    columns = responses + [x for x in groups if x not in responses]
    dframe = (
        dframe[columns].groupby(groups).mean().reset_index()
        if groups
        else dframe[responses].mean().to_frame().T
    )

    if "FLUID_ZONE" not in dframe:
        dframe["FLUID_ZONE"] = (" + ").join(selections["filters"]["FLUID_ZONE"])

    dframe = dframe[move_to_end_of_list("FLUID_ZONE", dframe.columns)]
    return [
        create_data_table(
            selectors=volumemodel.selectors,
            columns=create_table_columns(
                columns=dframe.columns, use_si_format=volumemodel.volume_columns
            ),
            data=dframe.iloc[::-1].to_dict("records"),
            height=f"{view_height}vh",
            table_id={"table_id": "meantable"},
        )
    ]
