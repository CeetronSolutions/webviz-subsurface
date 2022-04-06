from dataclasses import dataclass
from typing import List, Type, Union

from dash.development.base_component import Component
from dash import html, Dash, Input, Output

import webviz_core_components as wcc

from webviz_config.webviz_plugin_subclasses._views import ViewABC, ViewElementABC
from webviz_config.webviz_plugin_subclasses._settings_group_abc import SettingsGroupABC

from .._business_logic import RftPlotterDataModel, filter_frame
from .._figures._crossplot_figure import update_crossplot
from .._shared_settings import ViewFilters


class CrossplotViewElementSettings(SettingsGroupABC):
    """Settings for crossplot in view element settings"""

    @dataclass(frozen=True)
    class Elements:
        CROSSPLOT_COLOR_BY = "crossplot-color-by"
        CROSSPLOT_SIZE_BY = "crossplot-size-by"

    def __init__(self) -> None:
        super().__init__("Plot Settings")

    def layout(self) -> Type[Component]:
        return html.Div(
            children=[
                wcc.Dropdown(
                    label="Color by",
                    id=self.register_component_uuid(
                        CrossplotViewElementSettings.Elements.CROSSPLOT_COLOR_BY
                    ),
                    options=[
                        {
                            "label": "Misfit",
                            "value": "ABSDIFF",
                        },
                        {
                            "label": "Standard Deviation",
                            "value": "STDDEV",
                        },
                    ],
                    value="STDDEV",
                    clearable=False,
                ),
                wcc.Dropdown(
                    label="Size by",
                    id=self.register_component_uuid(
                        CrossplotViewElementSettings.Elements.CROSSPLOT_SIZE_BY
                    ),
                    options=[
                        {
                            "label": "Standard Deviation",
                            "value": "STDDEV",
                        },
                        {
                            "label": "Misfit",
                            "value": "ABSDIFF",
                        },
                    ],
                    value="ABSDIFF",
                    clearable=False,
                ),
            ]
        )


class CrossplotViewElement(ViewElementABC):
    @dataclass(frozen=True)
    class Elements:
        CROSSPLOT_GRAPHS_CONTAINER = "crossplot_graph_container"

    @dataclass(frozen=True)
    class Settings:
        CROSSPLOT_GRAPH_SETTINGS = "crossplot_graph_settings"

    def __init__(
        self, flex_grow: int = 1, screenshot_filename: str = "webviz-screenshot.png"
    ) -> None:
        super().__init__(
            flex_grow, screenshot_filename, ViewElementABC.LoadingMask.Graph
        )

        self.add_settings_group(
            CrossplotViewElementSettings(), self.Settings.CROSSPLOT_GRAPH_SETTINGS
        )

    def layout(self) -> Union[str, Type[Component]]:
        return html.Div(
            id=self.register_component_uuid(
                CrossplotViewElement.Elements.CROSSPLOT_GRAPHS_CONTAINER
            )
        )


class RftCrossplotSimVsObs(ViewABC):
    @dataclass(frozen=True)
    class ViewElements:
        CROSSPLOT_VIEW_ELEMENT = "crossplot_view_element"

    @dataclass(frozen=True)
    class Settings:
        CROSSPLOT_GRAPH_SELECTIONS = "crossplot_graph_selections"

    def __init__(
        self,
        data_model: RftPlotterDataModel,
        shared_filters_id: str,
    ) -> None:
        super().__init__("RFT Crossplot Sim vs Obs")

        self._data_model = data_model
        self._crossplot_view_element = CrossplotViewElement()

        self.add_view_element(
            self._crossplot_view_element, self.ViewElements.CROSSPLOT_VIEW_ELEMENT
        )
        self._shared_filters_id = shared_filters_id

    def _set_callbacks(self, app: Dash) -> None:
        @app.callback(
            Output(
                self.view_element_uuid(
                    self.ViewElements.CROSSPLOT_VIEW_ELEMENT,
                    CrossplotViewElement.Elements.CROSSPLOT_GRAPHS_CONTAINER,
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
            Input(
                self._crossplot_view_element.setting_group_uuid(
                    CrossplotViewElement.Settings.CROSSPLOT_GRAPH_SETTINGS,
                    CrossplotViewElementSettings.Elements.CROSSPLOT_SIZE_BY,
                ),
                "value",
            ),
            Input(
                self._crossplot_view_element.setting_group_uuid(
                    CrossplotViewElement.Settings.CROSSPLOT_GRAPH_SETTINGS,
                    CrossplotViewElementSettings.Elements.CROSSPLOT_COLOR_BY,
                ),
                "value",
            ),
        )
        def _crossplot(
            wells: List[str],
            zones: List[str],
            dates: List[str],
            ensembles: List[str],
            sizeby: str,
            colorby: str,
        ) -> Union[str, List[wcc.Graph]]:
            df = filter_frame(
                self._data_model.ertdatadf,
                {"WELL": wells, "ZONE": zones, "DATE": dates, "ENSEMBLE": ensembles},
            )
            if df.empty:
                return "No data matching the given filter criteria"
            return update_crossplot(df, sizeby, colorby)
