from typing import Optional
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
from webviz_subsurface._components.tornado._tornado_data import TornadoData

from ...utils.table_and_figure_utils import (
    update_tornado_figures_xaxis,
    create_data_table,
)
from ..._layout_elements import ElementIds

from .utils import (
    tornado_figure_and_table,
    sens_colors,
    create_realplot,
    tornado_plots_layout,
    tornado_error_layout,
)


class Plots(ViewElementABC):
    def __init__(self) -> None:
        super().__init__()

    def inner_layout(self) -> Component:
        return html.Div(
            id=self.register_component_uuid(ElementIds.TornadoPlots.Custom.Plots.GRAPHS)
        )


class DataTables(ViewElementABC):
    def __init__(
        self,
    ) -> None:
        super().__init__()

    def inner_layout(self) -> Component:
        return []


class TornadoPlotsCustom(ViewABC):
    def __init__(
        self, volumes_model: InplaceVolumesModel, theme: WebvizConfigTheme
    ) -> None:
        super().__init__("Custom")

        self.volumes_model = volumes_model
        self.theme = theme

    def set_callbacks(self) -> None:
        @callback(
            Output(
                self.get_uuid().to_string(),
                "children",
            ),
            Input(self.get_store_uuid(ElementIds.Stores.TORNADO_PLOTS), "data"),
            Input(self.get_store_uuid(ElementIds.Stores.FILTERS), "data"),
        )
        def _update_plots_and_tables(
            selections: dict,
            filters: dict,
        ) -> Component:
            if selections is None:
                raise PreventUpdate

            subplots = selections["Subplots"] is not None
            groups = ["REAL", "ENSEMBLE", "SENSNAME", "SENSCASE", "SENSTYPE"]
            if subplots and selections["Subplots"] not in groups:
                groups.append(selections["Subplots"])

            filters_copy = filters.copy()

            figures = []
            tables = []
            responses = [selections["Response"]]
            for response in responses:
                if selections["Reference"] not in selections["Sensitivities"]:
                    selections["Sensitivities"].append(selections["Reference"])
                filters_copy.update(SENSNAME=selections["Sensitivities"])

                dframe = self.volumes_model.get_df(filters=filters_copy, groups=groups)

                if not dframe.empty:
                    dframe.rename(columns={response: "VALUE"}, inplace=True)
                    df_groups = (
                        dframe.groupby(selections["Subplots"])
                        if subplots
                        else [(None, dframe)]
                    )
                    for group, df in df_groups:
                        if selections["Reference"] in df["SENSNAME"].unique():
                            tornado_data = TornadoData(
                                dframe=df,
                                reference=selections["Reference"],
                                response_name=response,
                                scale=selections["Scale"],
                                cutbyref=bool(selections["Remove no impact"]),
                            )
                            figure, table_data, columns = tornado_figure_and_table(
                                tornado_data=tornado_data,
                                response=response,
                                selections=selections,
                                filters=filters_copy,
                                theme=self.theme,
                                sensitivity_colors=sens_colors(self.volumes_model),
                                font_size=max((20 - (0.4 * len(df_groups))), 10),
                                group=group,
                                use_si_format=response
                                in self.volumes_model.volume_columns,
                            )
                            figures.append(figure)
                            tables.append(table_data)

                            if (
                                response == selections["Response"]
                                and selections["bottom_viz"] == "realplot"
                                and not subplots
                            ):
                                realplot = create_realplot(
                                    df=tornado_data.real_df,
                                    sensitivity_colors=sens_colors(self.volumes_model),
                                )

            if selections["Shared axis"] and selections["Scale"] != "True":
                update_tornado_figures_xaxis(figures)

            bottom_display: Optional[Component] = None
            if selections["bottom_viz"] == "table" and figures:
                bottom_display = create_data_table(
                    columns=columns,
                    selectors=[selections["Subplots"]] if subplots else [],
                    data=[x for table in tables for x in table],
                    height="39vh",
                    table_id={"table_id": f"{self.get_uuid().to_string()}-torntable"},
                )
            elif selections["bottom_viz"] == "realplot" and figures:
                bottom_display = (wcc.Graph(
                        config={"displayModeBar": False},
                        style={"height": "40vh"},
                        figure=realplot,
                    )
                    if not subplots
                    else "Realization plot not available when `Subplots` is active"
                )

            return (
                tornado_plots_layout(
                    view_id=self.get_uuid().to_string(),
                    figures=figures,
                    bottom_display=bottom_display,
                )
                if figures
                else tornado_error_layout(
                    "No data left after filtering"
                    if dframe.empty
                    else f"Reference sensitivity '{selections['Reference']}' not in input data"
                )
            )
