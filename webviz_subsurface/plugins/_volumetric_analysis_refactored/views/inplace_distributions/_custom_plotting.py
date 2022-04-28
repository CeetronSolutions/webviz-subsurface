from typing import Tuple
from webviz_config import WebvizConfigTheme
from webviz_config.webviz_plugin_subclasses import (
    ViewABC,
    ViewElementABC,
)
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate

from dash import Input, Output, callback, html
import webviz_core_components as wcc

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel
from webviz_subsurface._abbreviations.volume_terminology import (
    volume_description,
    volume_unit,
)
from webviz_subsurface._figures import create_figure
from ...utils.table_and_figure_utils import (
    fluid_annotation,
)
from .utils import make_tables

from ..._layout_elements import ElementIds


class Plot(ViewElementABC):
    def __init__(self) -> None:
        super().__init__()

    def inner_layout(self) -> Component:
        return wcc.Graph(
            id=self.register_component_uuid(
                ElementIds.InplaceDistributions.CustomPlotting.Plot.GRAPH
            ),
            config={"displayModeBar": False},
            style={"height": "86vh"},
        )


class DataTable(ViewElementABC):
    def __init__(
        self,
    ) -> None:
        super().__init__()

    def inner_layout(self) -> Component:
        return []


class InplaceDistributionsCustomPlotting(ViewABC):
    def __init__(self, volumes_model: InplaceVolumesModel) -> None:
        super().__init__("Custom plotting")

        self.volumes_model = volumes_model

        column = self.add_column()

        self.plot = Plot()
        column.add_view_element(
            self.plot, ElementIds.InplaceDistributions.CustomPlotting.Plot.ID
        )

        self.response_table = DataTable()
        column.add_view_element(
            self.response_table,
            ElementIds.InplaceDistributions.CustomPlotting.ResponseTable.ID,
        )

        self.property_table = DataTable()
        column.add_view_element(
            self.property_table,
            ElementIds.InplaceDistributions.CustomPlotting.PropertyTable.ID,
        )

    def set_callbacks(self) -> None:
        @callback(
            Output(
                self.plot.component_uuid(
                    ElementIds.InplaceDistributions.CustomPlotting.Plot.GRAPH
                ).to_string(),
                "figure",
            ),
            Output(
                self.plot.component_uuid(
                    ElementIds.InplaceDistributions.CustomPlotting.Plot.GRAPH
                ).to_string(),
                "style",
            ),
            Output(self.response_table.get_uuid().to_string(), "children"),
            Output(self.response_table.get_uuid().to_string(), "hidden"),
            Output(self.property_table.get_uuid().to_string(), "children"),
            Output(self.property_table.get_uuid().to_string(), "hidden"),
            Input(self.get_store_uuid("selections"), "data"),
        )
        def _update_plot_and_tables(
            selections: dict,
        ) -> Tuple[dict, dict, Component, bool, Component, bool]:
            if selections is None:
                raise PreventUpdate

            if not selections["update"]:
                raise PreventUpdate

            selected_data = [
                selections[x]
                for x in ["Subplots", "Color by", "X Response", "Y Response"]
                if selections[x] is not None
            ]
            groups = ["REAL"]
            parameters = []
            for item in selected_data:
                if item in self.volumes_model.selectors and item not in groups:
                    groups.append(item)
                if item in self.volumes_model.parameters and item not in parameters:
                    parameters.append(item)

            # for bo/bg the data should be grouped on fluid zone
            if (
                any(x in selected_data for x in ["BO", "BG"])
                and "FLUID_ZONE" not in groups
            ):
                if "BO" in selected_data and "BG" in selected_data:
                    return html.Div(
                        "Can't plot BO against BG", style={"margin-top": "40px"}
                    )
                selections["filters"]["FLUID_ZONE"] = [
                    "oil" if "BO" in selected_data else "gas"
                ]

            dframe = self.volumes_model.get_df(
                filters=selections["filters"], groups=groups, parameters=parameters
            )

            if dframe.empty:
                return html.Div(
                    "No data left after filtering", style={"margin-top": "40px"}
                )

            df_for_figure = (
                dframe
                if not (
                    selections["Plot type"] == "bar" and not "REAL" in selected_data
                )
                else dframe.groupby([x for x in groups if x != "REAL"])
                .mean()
                .reset_index()
            )

            figure = (
                create_figure(
                    plot_type=selections["Plot type"],
                    data_frame=df_for_figure,
                    x=selections["X Response"],
                    y=selections["Y Response"],
                    nbins=selections["hist_bins"],
                    facet_col=selections["Subplots"],
                    color=selections["Color by"],
                    color_discrete_sequence=selections["Colorscale"],
                    color_continuous_scale=selections["Colorscale"],
                    barmode=selections["barmode"],
                    boxmode=selections["barmode"],
                    layout=dict(
                        title=dict(
                            text=(
                                f"{volume_description(selections['X Response'])}"
                                + (
                                    f" [{volume_unit(selections['X Response'])}]"
                                    if selections["X Response"]
                                    in self.volumes_model.volume_columns
                                    else ""
                                )
                            ),
                            x=0.5,
                            xref="paper",
                            font=dict(size=18),
                        ),
                    ),
                    yaxis=dict(showticklabels=True),
                )
                .add_annotation(fluid_annotation(selections))
                .update_xaxes(
                    {"matches": None} if not selections["X axis matches"] else {}
                )
                .update_yaxes(
                    {"matches": None} if not selections["Y axis matches"] else {}
                )
                .update_xaxes(
                    {"type": "category", "tickangle": 45, "tickfont_size": 12}
                    if selections["X Response"] in self.volumes_model.selectors
                    else {}
                )
            )

            tables = make_tables(
                dframe=dframe,
                responses=list({selections["X Response"], selections["Y Response"]}),
                groups=groups,
                volumemodel=self.volumes_model,
                selections=selections,
                table_type="Statistics table",
                view_height=37,
            )

            response_table_hidden = True
            property_table_hidden = True

            if selections["bottom_viz"] == "table":
                if tables[0] is not None:
                    response_table_hidden = False
                if tables[1] is not None:
                    property_table_hidden = False

            return (
                figure,
                {"height": "86vh"}
                if response_table_hidden and property_table_hidden
                else {"height": "45vh"},
                tables[0] if tables[0] is not None else [],
                response_table_hidden,
                tables[1] if tables[1] is not None else [],
                property_table_hidden,
            )
