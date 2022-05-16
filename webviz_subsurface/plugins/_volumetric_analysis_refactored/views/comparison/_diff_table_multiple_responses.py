from typing import Tuple

from webviz_config.webviz_plugin_subclasses._views import ViewABC, ViewElementABC

from dash import Input, Output, callback, html
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate
import webviz_core_components as wcc
from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel

from ..._layout_elements import ElementIds
from .utils import (
    create_comparison_df,
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
                    id=self.register_component_unique_id(ElementIds.Comparison.HEADER)
                ),
                html.Div(
                    style={"margin-bottom": "30px", "font-weight": "bold"},
                    children=[
                        html.Div(
                            id=self.register_component_unique_id(
                                ElementIds.Comparison.SELECTION
                            )
                        ),
                        html.Div(
                            id=self.register_component_unique_id(
                                ElementIds.Comparison.FILTER
                            )
                        ),
                    ],
                ),
                html.Div(
                    id=self.register_component_unique_id(ElementIds.Comparison.TABLE)
                ),
            ]
        )


class DiffTableMultipleResponses(ViewABC):
    def __init__(self, compare_on: str, volumes_model: InplaceVolumesModel):
        super().__init__("Difference table for multiple responses")
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
                .component_unique_id(ElementIds.Comparison.HEADER)
                .to_string(),
                "children",
            ),
            Output(
                self.view_element(
                    ElementIds.Comparison.DiffTableSelectedResponse.VIEW_TABLE
                )
                .component_unique_id(ElementIds.Comparison.SELECTION)
                .to_string(),
                "children",
            ),
            Output(
                self.view_element(
                    ElementIds.Comparison.DiffTableSelectedResponse.VIEW_TABLE
                )
                .component_unique_id(ElementIds.Comparison.FILTER)
                .to_string(),
                "children",
            ),
            Output(
                self.view_element(
                    ElementIds.Comparison.DiffTableSelectedResponse.VIEW_TABLE
                )
                .component_unique_id(ElementIds.Comparison.TABLE)
                .to_string(),
                "children",
            ),
            Input(
                self.get_store_unique_id(f"{self.compare_on.lower()}_comparison"),
                "data",
            ),
            Input(self.get_store_unique_id(ElementIds.Stores.FILTERS), "data"),
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

        filters = { key: filters[key] for key in filters.keys() if key not in ["FIPNUM", "SET"] }

        groupby = selections["Group by"] if selections["Group by"] is not None else []

        # for hc responses and bo/bg the data should be grouped
        # on fluid zone to avoid misinterpretations
        if (
            selections["Response"] in self.volumes_model.hc_responses + ["BO", "BG"]
            and "FLUID_ZONE" not in groupby
        ):
            groupby.append("FLUID_ZONE")

        # select max one hc_response for a cleaner table
        responses = [selections["Response"]] + [
            col
            for col in self.volumes_model.responses
            if col not in self.volumes_model.hc_responses
            and col != selections["Response"]
        ]
        df = create_comparison_df(
            self.volumes_model,
            compare_on=compare_on,
            selections=selections,
            filters=filters,
            responses=responses,
            abssort_on=f"{selections['Response']} diff (%)",
            groups=groupby,
        )
        if df.empty:
            return ("", "No data left after filtering", "", None)

        filter_info = "SOURCE" if compare_on != "SOURCE" else "ENSEMBLE"

        return (
            f"Table showing differences for {selections['Response']}",
            f"From {selections['value1'].replace('|', ':  ')} "
            f"to {selections['value2'].replace('|', ':  ')}",
            f"{filter_info.capitalize()} {filters[filter_info][0]}",
            create_comparison_table(
                tabletype="multi-response table",
                df=df,
                groupby=groupby,
                selections=selections,
                filters=filters,
                use_si_format=selections["Response"]
                in self.volumes_model.volume_columns,
                compare_on=compare_on,
            ),
        )
