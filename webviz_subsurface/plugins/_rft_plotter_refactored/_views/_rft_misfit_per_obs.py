from dataclasses import dataclass
from typing import List, Type, Union

from dash.development.base_component import Component
from dash import html, Dash, Input, Output

import webviz_core_components as wcc

from webviz_config.webviz_plugin_subclasses._views import ViewABC, ViewElementABC

from .._business_logic import RftPlotterDataModel, filter_frame
from .._figures._errorplot_figure import update_errorplot
from .._shared_settings import ViewFilters


class MisfitPlotViewElement(ViewElementABC):
    @dataclass(frozen=True)
    class Elements:
        ERRORPLOT_GRAPH_CONTAINER = "errorplot_graph_container"

    def __init__(
        self, flex_grow: int = 1, screenshot_filename: str = "webviz-screenshot.png"
    ) -> None:
        super().__init__(
            flex_grow, screenshot_filename, ViewElementABC.LoadingMask.Graph
        )

    def layout(self) -> Union[str, Type[Component]]:
        return html.Div(
            id=self.register_component_uuid(
                MisfitPlotViewElement.Elements.ERRORPLOT_GRAPH_CONTAINER
            ),
            children=[],
        )


class RftMisfitPerObservation(ViewABC):
    @dataclass(frozen=True)
    class ViewElements:
        MISFIT_PLOT_VIEW_ELEMENT = "misfit_plot_view_element"

    @dataclass(frozen=True)
    class Settings:
        MISFIT_PLOT_SELECTIONS = "misfit_plot_selections"

    def __init__(
        self,
        data_model: RftPlotterDataModel,
        shared_filters_id: str,
    ) -> None:
        super().__init__("RFT Misfit Per Observation")

        self._data_model = data_model

        self._misfit_plot_view_element = MisfitPlotViewElement()
        self.add_view_element(
            self._misfit_plot_view_element, self.ViewElements.MISFIT_PLOT_VIEW_ELEMENT
        )
        self._shared_filters_id = shared_filters_id

    def _set_callbacks(self, app: Dash) -> None:
        @app.callback(
            Output(
                self.view_element_uuid(
                    self.ViewElements.MISFIT_PLOT_VIEW_ELEMENT,
                    MisfitPlotViewElement.Elements.ERRORPLOT_GRAPH_CONTAINER,
                ),
                "children",
            ),
            Input(
                self.shared_settings_group_uuid(
                    self._shared_filters_id, ViewFilters.Elements.FILTER_WELLS
                ),
                "value",
            ),
            Input(
                self.shared_settings_group_uuid(
                    self._shared_filters_id, ViewFilters.Elements.FILTER_ZONES
                ),
                "value",
            ),
            Input(
                self.shared_settings_group_uuid(
                    self._shared_filters_id, ViewFilters.Elements.FILTER_DATES
                ),
                "value",
            ),
            Input(
                self.shared_settings_group_uuid(
                    self._shared_filters_id, ViewFilters.Elements.FILTER_ENSEMBLES
                ),
                "value",
            ),
        )
        def _errorplot(
            wells: List[str], zones: List[str], dates: List[str], ensembles: List[str]
        ) -> Union[str, List[wcc.Graph]]:
            df = filter_frame(
                self._data_model.ertdatadf,
                {"WELL": wells, "ZONE": zones, "DATE": dates, "ENSEMBLE": ensembles},
            )
            if df.empty:
                return "No data matching the given filter criteria"
            return [update_errorplot(df, self._data_model.enscolors)]
