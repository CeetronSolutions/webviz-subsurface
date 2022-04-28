from typing import List, Optional, Type
from xml.dom.minidom import Element
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from webviz_config import WebvizConfigTheme
from webviz_config.webviz_plugin_subclasses import (
    ViewABC,
    ViewElementABC,
    ViewLayoutElement,
    LayoutElementType,
)
from dash.development.base_component import Component

from dash import Input, Output, State, callback, html, dash_table
from dash.exceptions import PreventUpdate
import webviz_core_components as wcc

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel
from webviz_subsurface._abbreviations.volume_terminology import (
    volume_description,
    volume_unit,
)
from webviz_subsurface._figures import create_figure
from ...utils.table_and_figure_utils import (
    create_data_table,
    create_table_columns,
    fluid_annotation,
)
from ...utils.utils import move_to_end_of_list, to_ranges

from ..._layout_elements import ElementIds


class StockOilTankPlot(ViewElementABC):
    def __init__(self, figure: dict) -> None:
        super().__init__()
        self.figure = figure

    def inner_layout(self) -> Component:
        return wcc.Graph(
            id=self.register_component_uuid(
                ElementIds.InplaceDistributions.CustomPlotting.StockOilTankPlot.GRAPH
            ),
            config={"displayModeBar": False},
            figure=self.figure,
        )


class DataTable(ViewElementABC):
    def __init__(
        self,
        columns: list,
        data: List[dict],
        selectors: Optional[list] = None,
        style_cell: Optional[dict] = None,
        style_cell_conditional: Optional[list] = None,
        style_data_conditional: Optional[list] = None,
    ) -> None:
        super().__init__()
        self.columns = columns
        self.data = data
        self.selectors = selectors
        self.style_cell = style_cell
        self.style_cell_conditional = style_cell_conditional
        self.style_data_conditional = style_data_conditional

    def inner_layout(self) -> Component:
        if not self.data:
            return None

        if self.selectors is None:
            self.selectors = []
        conditional_cell_style = [
            {
                "if": {
                    "column_id": self.selectors
                    + ["Response", "Property", "Sensitivity"]
                },
                "width": "10%",
                "textAlign": "left",
            },
            {"if": {"column_id": "FLUID_ZONE"}, "width": "10%", "textAlign": "right"},
        ]
        if self.style_cell_conditional is not None:
            conditional_cell_style.extend(self.style_cell_conditional)

        self.style_data_conditional = (
            self.style_data_conditional
            if self.style_data_conditional is not None
            else []
        )
        self.style_data_conditional.extend(self.fluid_table_style())

        return (
            dash_table.DataTable(
                id=self.register_component_uuid("table"),
                sort_action="native",
                sort_mode="multi",
                filter_action="native",
                columns=self.columns,
                data=self.data,
                style_as_list_view=True,
                style_cell=self.style_cell,
                style_cell_conditional=conditional_cell_style,
                style_data_conditional=self.style_data_conditional,
                style_table={
                    "overflowY": "auto",
                },
            ),
        )

    def fluid_table_style(self) -> list:
        fluid_colors = {
            "oil": "#007079",
            "gas": "#FF1243",
            "water": "#ADD8E6",
        }
        return [
            {
                "if": {
                    "filter_query": "{FLUID_ZONE} = " + f"'{fluid}'",
                    "column_id": "FLUID_ZONE",
                },
                "color": color,
                "fontWeight": "bold",
            }
            for fluid, color in fluid_colors.items()
        ]


class InplaceDistributionsCustomPlotting(ViewABC):
    def __init__(
        self, volumes_model: InplaceVolumesModel, theme: WebvizConfigTheme
    ) -> None:
        super().__init__("Custom plotting")

        self.volumes_model = volumes_model
        self.theme = theme

    def set_callbacks(self) -> None:
        @callback(
            Output(self.get_uuid().to_string(), "children"),
            Input(self.get_store_uuid("selections"), "data"),
        )
        def _update_page_custom(selections: dict) -> Component:
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

            theme_colors = self.theme.plotly_theme.get("layout", {}).get("colorway", [])

            selections["Fluid annotation"] = True
            selections["X axis matches"] = True
            selections["Y axis matches"] = True
            selections["bottom_viz"] = "table"

            figure = (
                create_figure(
                    plot_type=selections["Plot type"],
                    data_frame=df_for_figure,
                    x=selections["X Response"],
                    y=selections["Y Response"],
                    nbins=15,
                    facet_col=selections["Subplots"],
                    color=selections["Color by"],
                    color_discrete_sequence=theme_colors,
                    color_continuous_scale=theme_colors,
                    barmode="overlay",
                    boxmode="overlay",
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

            plot = StockOilTankPlot(figure)

            column = ViewLayoutElement(
                layout_element_type=LayoutElementType.COLUMN, parent_view=self
            )

            column.add_view_element(plot, "Plot")
            i = 0
            if selections["bottom_viz"] == "table":
                for table in self.make_tables(
                    dframe=dframe,
                    responses=list(
                        {selections["X Response"], selections["Y Response"]}
                    ),
                    groups=groups,
                    volumemodel=self.volumes_model,
                    selections=selections,
                    table_type="Statistics table",
                    view_height=37,
                ):
                    column.add_view_element(table, f"Table-{i}")
                    i += 1

            return column.layout

    def make_tables(
        self,
        dframe: pd.DataFrame,
        responses: list,
        volumemodel: InplaceVolumesModel,
        selections: dict,
        table_type: str,
        view_height: float,
        groups: Optional[list] = None,
    ) -> List[DataTable]:

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
                DataTable(
                    selectors=volumemodel.selectors,
                    columns=create_table_columns(
                        columns=move_to_end_of_list(
                            "FLUID_ZONE", [col] + groups + statcols
                        ),
                        text_columns=[col] + groups,
                        use_si_format=statcols if col == "Response" else None,
                    ),
                    data=data,
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
            DataTable(
                selectors=volumemodel.selectors,
                columns=create_table_columns(
                    columns=dframe.columns, use_si_format=volumemodel.volume_columns
                ),
                data=dframe.iloc[::-1].to_dict("records"),
            )
        ]
