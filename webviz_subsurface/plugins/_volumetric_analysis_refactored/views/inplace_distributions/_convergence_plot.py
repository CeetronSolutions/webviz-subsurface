from typing import Tuple
from time import sleep

import pandas as pd
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
from ...utils.utils import to_ranges

from ..._layout_elements import ElementIds


class Plot(ViewElementABC):
    def __init__(self) -> None:
        super().__init__()

    def inner_layout(self) -> Component:
        return wcc.Graph(
            id=self.register_component_uuid(
                ElementIds.InplaceDistributions.ConvergencePlot.Plot.GRAPH
            ),
            config={"displayModeBar": False},
            style={"height": "86vh"},
        )


class InplaceDistributionsConvergencePlot(ViewABC):
    def __init__(self, volumes_model: InplaceVolumesModel) -> None:
        super().__init__("Convergence plot Mean/P10/P90")

        self.volumes_model = volumes_model

        column = self.add_column()

        self.plot = Plot()
        column.add_view_element(
            self.plot, ElementIds.InplaceDistributions.ConvergencePlot.Plot.ID
        )

    def set_callbacks(self) -> None:
        @callback(
            Output(
                self.plot.component_uuid(
                    ElementIds.InplaceDistributions.ConvergencePlot.Plot.GRAPH
                ).to_string(),
                "figure",
            ),
            Input(self.get_store_uuid("selections"), "data"),
        )
        def _update_plot_and_tables(
            selections: dict,
        ) -> dict:
            if selections is None:
                raise PreventUpdate

            subplots = selections["Subplots"] if selections["Subplots"] is not None else []
            groups = ["REAL"]
            if subplots and subplots not in groups:
                groups.append(subplots)

            dframe = self.volumes_model.get_df(filters=selections["filters"], groups=groups)
            dframe = dframe.sort_values(by=["REAL"])

            if dframe.empty:
                return html.Div(
                    "No data left after filtering", style={"margin-top": "40px"}
                )

            dfs = []
            df_groups = dframe.groupby(subplots) if subplots else [(None, dframe)]
            for _, df in df_groups:
                for calculation in ["mean", "p10", "p90"]:
                    df_stat = df.reset_index(drop=True).copy()
                    df_stat[selections["X Response"]] = (
                        (df_stat[selections["X Response"]].expanding().mean())
                        if calculation == "mean"
                        else df_stat[selections["X Response"]]
                        .expanding()
                        .quantile(0.1 if calculation == "p90" else 0.9)
                    )
                    df_stat["calculation"] = calculation
                    df_stat["index"] = df_stat.index + 1
                    dfs.append(df_stat)
            if dfs:
                dframe = pd.concat(dfs)

            title = (
                f"<b>Convergence plot of mean/p10/p90 for {selections['X Response']} </b>"
                "  -  shaded areas indicates failed/filtered out realizations"
            )

            figure = (
                create_figure(
                    plot_type="line",
                    data_frame=dframe,
                    x="REAL",
                    y=selections["X Response"],
                    facet_col=selections["Subplots"],
                    color="calculation",
                    custom_data=["calculation", "index"],
                    title=title,
                    yaxis=dict(showticklabels=True),
                )
                .update_traces(
                    hovertemplate=(
                        f"{selections['X Response']} %{{y}} <br>"
                        f"%{{customdata[0]}} for realizations {dframe['REAL'].min()}-%{{x}}<br>"
                        "Realization count: %{customdata[1]} <extra></extra>"
                    ),
                    line_width=3.5,
                )
                .update_traces(line_color="black", selector={"name": "mean"})
                .update_traces(
                    line=dict(color="firebrick", dash="dash"), selector={"name": "p10"}
                )
                .update_traces(
                    line=dict(color="royalblue", dash="dash"), selector={"name": "p90"}
                )
                .update_xaxes({"matches": None} if not selections["X axis matches"] else {})
                .update_yaxes({"matches": None} if not selections["Y axis matches"] else {})
            )
            if selections["X Response"] not in self.volumes_model.hc_responses:
                figure.add_annotation(fluid_annotation(selections))

            missing_reals = [
                x
                for x in range(dframe["REAL"].min(), dframe["REAL"].max())
                if x not in dframe["REAL"].unique()
            ]
            if missing_reals:
                for real_range in to_ranges(missing_reals):
                    figure.add_vrect(
                        x0=real_range[0] - 0.5,
                        x1=real_range[1] + 0.5,
                        fillcolor="gainsboro",
                        layer="below",
                        opacity=0.4,
                        line_width=0,
                    )

            return figure
