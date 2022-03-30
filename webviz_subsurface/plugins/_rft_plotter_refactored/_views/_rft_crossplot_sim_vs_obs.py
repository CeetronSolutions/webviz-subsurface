from typing import List, Type, Union

from dash.development.base_component import Component  # type: ignore
from dash import html, Dash, Input, Output

import webviz_core_components as wcc

from webviz_config.webviz_plugin_subclasses._views import ViewABC, ViewElementABC
from webviz_config.webviz_plugin_subclasses._settings_group_abc import SettingsGroupABC

from .._business_logic import RftPlotterDataModel, filter_frame
from .._figures._crossplot_figure import update_crossplot


class CrossplotGraphSelections(SettingsGroupABC):
    """Settings for crossplot in Settings Drawer"""

    # TODO: Move to shared settings when shared settings for selection of views is supported

    class Elements:
        # pylint: disable=too-few-public-methods
        FILTER_ENSEMBLES = "ensembles-crossplot"
        FILTER_WELLS = "well-crossplot"
        FILTER_ZONES = "zones-crossplot"
        FILTER_DATES = "dates-crossplot"

    def __init__(
        self,
        ensembles: List[str],
        well_names: List[str],
        zone_names: List[str],
        dates: List[str],
    ) -> None:
        super().__init__("Filters")

        self._ensembles = ensembles
        self._well_names = well_names
        self._zone_names = zone_names
        self._dates = dates

    def layout(self) -> Type[Component]:
        return html.Div(
            children=[
                wcc.SelectWithLabel(
                    label="Ensembles",
                    size=min(4, len(self._ensembles)),
                    id=self.register_component_uuid(
                        CrossplotGraphSelections.Elements.FILTER_ENSEMBLES
                    ),
                    options=[
                        {"label": name, "value": name} for name in self._ensembles
                    ],
                    value=self._ensembles,
                    multi=True,
                ),
                wcc.SelectWithLabel(
                    label="Wells",
                    size=min(20, len(self._well_names)),
                    id=self.register_component_uuid(
                        CrossplotGraphSelections.Elements.FILTER_WELLS
                    ),
                    options=[
                        {"label": name, "value": name} for name in self._well_names
                    ],
                    value=self._well_names,
                    multi=True,
                ),
                wcc.SelectWithLabel(
                    label="Zones",
                    size=min(10, len(self._zone_names)),
                    id=self.register_component_uuid(
                        CrossplotGraphSelections.Elements.FILTER_ZONES
                    ),
                    options=[
                        {"label": name, "value": name} for name in self._zone_names
                    ],
                    value=self._zone_names,
                    multi=True,
                ),
                wcc.SelectWithLabel(
                    label="Dates",
                    size=min(10, len(self._dates)),
                    id=self.register_component_uuid(
                        CrossplotGraphSelections.Elements.FILTER_DATES
                    ),
                    options=[{"label": name, "value": name} for name in self._dates],
                    value=self._dates,
                    multi=True,
                ),
            ]
        )


class CrossplotViewElementSettings(SettingsGroupABC):
    """Settings for crossplot in view element settings"""

    class Elements:
        # pylint: disable=too-few-public-methods
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
    class Elements:
        # pylint: disable=too-few-public-methods
        CROSSPLOT_GRAPHS_CONTAINER = "crossplot_graph_container"

    class Settings:
        # pylint: disable=too-few-public-methods
        CROSSPLOT_GRAPH_SETTINGS = "crossplot_graph_settings"

    def __init__(
        self, flex_grow: int = 1, screenshot_filename: str = "webviz-screenshot.png"
    ) -> None:
        super().__init__(flex_grow, screenshot_filename)

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
    class ViewElements:
        # pylint: disable=too-few-public-methods
        CROSSPLOT_VIEW_ELEMENT = "crossplot_view_element"

    class Settings:
        # pylint: disable=too-few-public-methods
        CROSSPLOT_GRAPH_SELECTIONS = "crossplot_graph_selections"

    def __init__(self, data_model: RftPlotterDataModel) -> None:
        super().__init__("RFT Crossplot Sim vs Obs")

        self._data_model = data_model
        self._crossplot_view_element = CrossplotViewElement()

        self.add_view_element(
            self._crossplot_view_element, self.ViewElements.CROSSPLOT_VIEW_ELEMENT
        )
        self.add_settings_group(
            CrossplotGraphSelections(
                ensembles=data_model.ensembles,
                well_names=data_model.well_names,
                zone_names=data_model.zone_names,
                dates=data_model.dates,
            ),
            self.Settings.CROSSPLOT_GRAPH_SELECTIONS,
        )

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
                self.settings_group_uuid(
                    self.Settings.CROSSPLOT_GRAPH_SELECTIONS,
                    CrossplotGraphSelections.Elements.FILTER_WELLS,
                ),
                "value",
            ),
            Input(
                self.settings_group_uuid(
                    self.Settings.CROSSPLOT_GRAPH_SELECTIONS,
                    CrossplotGraphSelections.Elements.FILTER_ZONES,
                ),
                "value",
            ),
            Input(
                self.settings_group_uuid(
                    self.Settings.CROSSPLOT_GRAPH_SELECTIONS,
                    CrossplotGraphSelections.Elements.FILTER_DATES,
                ),
                "value",
            ),
            Input(
                self.settings_group_uuid(
                    self.Settings.CROSSPLOT_GRAPH_SELECTIONS,
                    CrossplotGraphSelections.Elements.FILTER_ENSEMBLES,
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
