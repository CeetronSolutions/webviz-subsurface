from typing import List, Tuple
from webviz_config.webviz_plugin_subclasses import (
    ViewABC,
    ViewElementABC,
)
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate

from dash import Input, Output, callback
import webviz_core_components as wcc

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel
from webviz_subsurface._figures import create_figure
from ...utils.table_and_figure_utils import (
    fluid_annotation,
)

from ..._layout_elements import ElementIds


class Plot(ViewElementABC):
    def __init__(self) -> None:
        super().__init__()

    def inner_layout(self) -> Component:
        return wcc.Graph(
            id=self.register_component_unique_id(
                ElementIds.InplaceDistributions.PlotsPerZoneRegion.GRAPH
            ),
            config={"displayModeBar": False},
            style={"height": "40vh"},
        )


class InplaceDistributionsPlotsPerZoneRegion(ViewABC):
    def __init__(self, volumes_model: InplaceVolumesModel) -> None:
        self.selectors = ["ZONE", "REGION", "FACIES", "FIPNUM", "SET"]
        selectors_string = "/".join(
            [
                x.lower()
                for x in ["ZONE", "REGION", "FACIES", "FIPNUM", "SET"]
                if x in volumes_model.selectors
            ]
        )
        super().__init__(f"Plots per {selectors_string}")

        self.volumes_model = volumes_model

        column = self.add_column()

        self.plots: List[Tuple[Plot, Plot]] = []

        for selector in self.selectors:
            row = column.make_row()
            bar_plot = Plot()
            pie_plot = Plot()
            row.add_view_element(bar_plot, f"{selector}-bar-plot")
            row.add_view_element(pie_plot, f"{selector}-pie-plot")
            self.plots.append((bar_plot, pie_plot))

    def callback_factory(self, index: int, selector: str) -> None:
        @callback(
            Output(
                self.plots[index][0]
                .component_unique_id(
                    ElementIds.InplaceDistributions.PlotsPerZoneRegion.GRAPH
                )
                .to_string(),
                "figure",
            ),
            Output(
                self.plots[index][1]
                .component_unique_id(
                    ElementIds.InplaceDistributions.PlotsPerZoneRegion.GRAPH
                )
                .to_string(),
                "figure",
            ),
            Output(
                self.plots[index][0].get_unique_id().to_string(),
                "hidden",
            ),
            Output(
                self.plots[index][1].get_unique_id().to_string(),
                "hidden",
            ),
            Input(
                self.get_store_unique_id(ElementIds.Stores.INPLACE_DISTRIBUTIONS),
                "data",
            ),
            Input(self.get_store_unique_id(ElementIds.Stores.FILTERS), "data"),
        )
        def _update_plots(
            selections: dict,
            filters: dict,
        ) -> Tuple[dict, dict, bool, bool]:
            if selections is None:
                raise PreventUpdate

            return self.make_figures(selector, selections, filters)

    def set_callbacks(self) -> None:
        for index, selector in enumerate(self.selectors):
            self.callback_factory(index, selector)

    def make_figures(
        self,
        selector: str,
        selections: dict,
        filters: dict,
    ) -> Tuple[dict, dict, bool, bool]:
        if selector not in self.volumes_model.selectors:
            return ({}, {}, True, True)

        color = selections["Color by"] is not None
        groups = list({selector, selections["Color by"]}) if color else [selector]
        dframe = self.volumes_model.get_df(filters=filters, groups=groups)
        piefig = (
            (
                create_figure(
                    plot_type="pie",
                    data_frame=dframe,
                    values=selections["X Response"],
                    names=selector,
                    color_discrete_sequence=selections["Colorscale"],
                    color=selector,
                )
                .update_traces(marker_line=dict(color="#000000", width=1))
                .update_layout(margin=dict(l=10, b=10))
            )
            if not color
            else None
        )
        barfig = create_figure(
            plot_type="bar",
            data_frame=dframe,
            x=selector,
            y=selections["X Response"],
            title=f"{selections['X Response']} per {selector}",
            barmode="overlay" if selector == selections["Color by"] else "group",
            layout={"bargap": 0.05},
            color_discrete_sequence=selections["Colorscale"],
            color=selections["Color by"],
            text=selections["X Response"],
            xaxis=dict(type="category", tickangle=45, tickfont_size=17, title=None),
        ).update_traces(
            texttemplate=(
                "%{text:.3s}"
                if selections["X Response"] in self.volumes_model.volume_columns
                else "%{text:.3g}"
            ),
            textposition="auto",
        )

        if selections["X Response"] not in self.volumes_model.hc_responses:
            barfig.add_annotation(fluid_annotation(selections, filters))
        return (barfig, piefig if piefig else {}, False, piefig is None)
