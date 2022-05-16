from typing import Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from webviz_config.webviz_plugin_subclasses import (
    ViewABC,
    ViewElementABC,
)
from dash.development.base_component import Component

from dash import Input, Output, callback, html, callback_context
import webviz_core_components as wcc

from ..._layout_elements import ElementIds


class Plot(ViewElementABC):
    def __init__(self) -> None:
        super().__init__()

    def inner_layout(self) -> Component:
        return wcc.Graph(
            id=self.register_component_unique_id(
                ElementIds.InplaceDistributions.CustomPlotting.Plot.GRAPH
            ),
            config={"displayModeBar": False},
        )


class FipFileQCPlots(ViewABC):
    def __init__(self, disjoint_set_df: pd.DataFrame) -> None:
        super().__init__("Custom plotting")

        self.disjoint_set_df = disjoint_set_df

        column = self.add_column()

        column.add_view_element(
            Plot(), ElementIds.FipFile.QCPlots.ZONE_REGION_HEATMAP
        )

        column.add_view_element(
            Plot(), ElementIds.FipFile.QCPlots.ZONE_FIPNUM_HEATMAP
        )

        column.add_view_element(
            Plot(), ElementIds.FipFile.QCPlots.REGION_FIPNUM_HEATMAP
        )

    def set_callbacks(self) -> None:
        @callback(
            Output(self.view_element(ElementIds.FipFile.QCPlots.ZONE_REGION_HEATMAP).get_unique_id().to_string(), "children"),
            Output(self.view_element(ElementIds.FipFile.QCPlots.ZONE_FIPNUM_HEATMAP).get_unique_id().to_string(), "children"),
            Output(self.view_element(ElementIds.FipFile.QCPlots.REGION_FIPNUM_HEATMAP).get_unique_id().to_string(), "children"),
            Input(self.get_store_unique_id(ElementIds.Stores.FILTERS), "data"),
        )
        def _update_page_fipfileqc(
            filters: dict
            ) -> Tuple[wcc.Graph, wcc.Graph, wcc.Graph]:
                ctx = callback_context.triggered[0]

                filters = { key: filters[key] for key in filters if key in ["REGION", "ZONE", "FIPNUM", "SET"]}

                df = self.disjoint_set_df[["SET", "FIPNUM", "REGION", "ZONE", "REGZONE"]]

                for filt, values in filters.items():
                    df = df.loc[df[filt].isin(values)]

                df = df.sort_values(by=["SET"])

                df["FIPNUM"] = df["FIPNUM"].astype(str)
                return (
                        self.create_heatmap(df=df, y="ZONE", x="REGION"),
                        self.create_heatmap(df=df, y="ZONE", x="FIPNUM"),
                        self.create_heatmap(df=df, y="REGION", x="FIPNUM"),
                )

    @staticmethod
    def create_heatmap(df: pd.DataFrame, y: str, x: str) -> wcc.Graph:
        """Create heatmap"""
        unique_y = df[y].unique()
        unique_x = sorted(df[x].unique(), key=int if x == "FIPNUM" else None)
        data = []
        for y_elm in unique_y:
            set_list = []
            for x_elm in unique_x:
                set_idx = df.loc[(df[y] == y_elm) & (df[x] == x_elm), "SET"]
                set_list.append(set_idx.iloc[0] if not set_idx.empty else None)
            data.append(set_list)

        return wcc.Graph(
            config={"displayModeBar": False},
            style={"height": "28vh"},
            figure=go.Figure(
                data=go.Heatmap(
                    z=data,
                    x=unique_x,
                    y=unique_y,
                    colorscale=(
                        px.colors.qualitative.Safe
                        + px.colors.qualitative.T10
                        + px.colors.qualitative.Set1
                    ),
                    showscale=False,
                    hovertemplate="SET: %{z} <br>"
                    + f"{x}: %{{x}} <br>"
                    + f"{y}: %{{y}} <extra></extra>",
                )
            )
            .update_layout(
                margin={"l": 20, "r": 20, "t": 20, "b": 20}, plot_bgcolor="white"
            )
            .update_xaxes(title_text=x, tickangle=45, ticks="outside", **FipFileQCPlots.axis_variables())
            .update_yaxes(title_text=y, **FipFileQCPlots.axis_variables()),
        )

    @staticmethod
    def axis_variables() -> dict:
        return {"showline": True, "linewidth": 2, "linecolor": "black", "mirror": True}
