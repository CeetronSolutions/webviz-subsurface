from typing import Optional, Tuple, Union

import pandas as pd
from webviz_config.webviz_plugin_subclasses._views import ViewABC, ViewElementABC

from dash import dash_table, Input, Output, callback, callback_context, html
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate
import webviz_core_components as wcc
from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel

from ..._layout_elements import ElementIds
from .utils import (
    create_comparison_df,
    find_higlighted_real_count,
    create_comparison_table,
)


class DataTable(ViewElementABC):
    def __init__(
        self,
    ) -> None:
        super().__init__()

    def inner_layout(self) -> Component:
        return html.Div(
            [
                wcc.Header(
                    id=self.register_component_uuid(ElementIds.Comparison.HEADER)
                ),
                html.Div(
                    style={"margin-bottom": "30px", "font-weight": "bold"},
                    children=[
                        html.Div(
                            id=self.register_component_uuid(
                                ElementIds.Comparison.SELECTION
                            )
                        ),
                        html.Div(
                            id=self.register_component_uuid(
                                ElementIds.Comparison.FILTER
                            )
                        ),
                    ],
                ),
                html.Div(id=self.register_component_uuid(ElementIds.Comparison.TABLE)),
            ]
        )


class DiffTableSelectedResponse(ViewABC):
    def __init__(self, compare_on: str, volumes_model: InplaceVolumesModel):
        super().__init__("Difference table for selected response")
        self.volumes_model = volumes_model
        self.compare_on = compare_on

        self.add_view_element(
            DataTable(), ElementIds.Comparison.DiffTableSelectedResponse.VIEW_TABLE
        )

    def set_callbacks(self) -> None:
        @callback(
            Output(
                self.view_element(
                    ElementIds.Comparison.DiffTableSelectedResponse.VIEW_TABLE
                )
                .component_uuid(ElementIds.Comparison.HEADER)
                .to_string(),
                "children",
            ),
            Output(
                self.view_element(
                    ElementIds.Comparison.DiffTableSelectedResponse.VIEW_TABLE
                )
                .component_uuid(ElementIds.Comparison.SELECTION)
                .to_string(),
                "children",
            ),
            Output(
                self.view_element(
                    ElementIds.Comparison.DiffTableSelectedResponse.VIEW_TABLE
                )
                .component_uuid(ElementIds.Comparison.FILTER)
                .to_string(),
                "children",
            ),
            Output(
                self.view_element(
                    ElementIds.Comparison.DiffTableSelectedResponse.VIEW_TABLE
                )
                .component_uuid(ElementIds.Comparison.TABLE)
                .to_string(),
                "children",
            ),
            Input(self.get_store_uuid(f"{self.compare_on.lower()}_comparison"), "data"),
            Input(self.get_store_uuid(ElementIds.Stores.FILTERS), "data"),
        )
        def _update_page_ens_comp(
            selections: dict,
            filters: dict,
        ) -> Tuple[str, str, str, Component]:
            if selections is None:
                raise PreventUpdate

            return self.comparison_callback(
                compare_on="SENSNAME_CASE"
                if self.compare_on == "Sensitivity"
                else "ENSEMBLE",
                selections=selections,
                filters=filters,
            )

    def comparison_callback(
        self,
        compare_on: str,
        selections: dict,
        filters: dict,
    ) -> Tuple[str, str, str, Component]:
        if selections["value1"] == selections["value2"]:
            return ("", "Comparison between equal data", "", None)

        # Handle None in highlight criteria input
        for key in ["Accept value", "Ignore <"]:
            selections[key] = selections[key] if selections[key] is not None else 0

        groupby = selections["Group by"] if selections["Group by"] is not None else []
        group_on_fluid = "FLUID_ZONE" in groupby
        # for hc responses and bo/bg the data should be grouped
        # on fluid zone to avoid misinterpretations
        if (
            selections["Response"] in self.volumes_model.hc_responses + ["BO", "BG"]
            and "FLUID_ZONE" not in groupby
        ):
            groupby.append("FLUID_ZONE")

        if compare_on == "SOURCE" or "REAL" in groupby:
            diffdf_real = create_comparison_df(
                self.volumes_model,
                compare_on=compare_on,
                selections=selections,
                filters=filters,
                responses=[selections["Response"]],
                groups=groupby + (["REAL"] if "REAL" not in groupby else []),
                rename_diff_col=True,
            )

        if "REAL" not in groupby:
            diffdf_group = create_comparison_df(
                self.volumes_model,
                compare_on=compare_on,
                selections=selections,
                filters=filters,
                responses=[selections["Response"]],
                groups=groupby,
                rename_diff_col=True,
            )
            if compare_on == "SOURCE" and not diffdf_group.empty:
                # Add column with number of highlighted realizations
                diffdf_group["💡 reals"] = diffdf_group.apply(
                    lambda row: find_higlighted_real_count(row, diffdf_real, groupby),
                    axis=1,
                )

        df = diffdf_group if "REAL" not in groupby else diffdf_real
        if df.empty:
            return ("", "No data left after filtering", "", None)

        filter_info = "SOURCE" if compare_on != "SOURCE" else "ENSEMBLE"

        return (
            f"Table showing differences for {selections['Response']}",
            f"From {selections['value1'].replace('|', ':  ')} "
            f"to {selections['value2'].replace('|', ':  ')}",
            f"{filter_info.capitalize()} {filters[filter_info][0]}",
            create_comparison_table(
                tabletype="single-response table",
                df=df,
                groupby=groupby,
                selections=selections,
                filters=filters,
                use_si_format=selections["Response"]
                in self.volumes_model.volume_columns,
                compare_on=compare_on,
            ),
        )
