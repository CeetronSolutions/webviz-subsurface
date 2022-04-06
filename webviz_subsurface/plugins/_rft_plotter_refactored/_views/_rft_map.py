from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple, Type, Union

from dash.development.base_component import Component  # type: ignore
from dash import html, Dash, Input, Output, State
from dash.exceptions import PreventUpdate

import webviz_core_components as wcc
from webviz_config.webviz_plugin_subclasses._views import ViewABC, ViewElementABC
from webviz_config.webviz_plugin_subclasses._settings_group_abc import SettingsGroupABC

from .._business_logic import RftPlotterDataModel, filter_frame
from .._figures._formation_figure import FormationFigure
from .._figures._map_figure import MapFigure


class MapPlotSelections(SettingsGroupABC):
    """Settings for map in Settings Drawer"""

    @dataclass(frozen=True)
    class Elements:
        MAP_ENSEMBLE = "map-ensemble"
        MAP_DATE_RANGE = "map-date-range"
        MAP_ZONES = "map-zones"

    def __init__(
        self,
        ensembles: List[str],
        zone_names: List[str],
        start_date: Any,  # TODO: Set correct type
        end_date: Any,  # TODO: Set correct type
        date_marks: Dict[str, Dict[str, Any]],
    ) -> None:
        super().__init__("Map Plot Selections")
        self._ensembles = ensembles
        self._zone_names = zone_names
        self._start_date = start_date
        self._end_date = end_date
        self._date_marks = date_marks

    def layout(self) -> Type[Component]:
        return html.Div(
            children=[
                wcc.Dropdown(
                    label="Ensemble",
                    id=self.register_component_uuid(self.Elements.MAP_ENSEMBLE),
                    options=[{"label": ens, "value": ens} for ens in self._ensembles],
                    value=self._ensembles[0] if self._ensembles else None,
                    clearable=False,
                ),
                wcc.RangeSlider(
                    label="Filter date range",
                    id=self.register_component_uuid(self.Elements.MAP_DATE_RANGE),
                    min=self._start_date,
                    max=self._end_date,
                    value=[self._start_date, self._end_date],
                    marks=self._date_marks,
                ),
                wcc.SelectWithLabel(
                    label="Zone filter",
                    size=min(10, len(self._zone_names)),
                    id=self.register_component_uuid(self.Elements.MAP_ZONES),
                    options=[
                        {"label": name, "value": name} for name in self._zone_names
                    ],
                    value=self._zone_names,
                    multi=True,
                ),
            ]
        )


class MapPlotViewElementSettings(SettingsGroupABC):
    """Settings for map in view element settings"""

    @dataclass(frozen=True)
    class Elements:
        MAP_SIZE_BY = "map-size-by"
        MAP_COLOR_BY = "map-color-by"

    def __init__(self) -> None:
        super().__init__("Map Plot Settings")

    def layout(self) -> Type[Component]:
        return html.Div(
            children=[
                wcc.Dropdown(
                    label="Size points by",
                    id=self.register_component_uuid(self.Elements.MAP_SIZE_BY),
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
                wcc.Dropdown(
                    label="Color points by",
                    id=self.register_component_uuid(self.Elements.MAP_COLOR_BY),
                    options=[
                        {
                            "label": "Misfit",
                            "value": "ABSDIFF",
                        },
                        {
                            "label": "Standard Deviation",
                            "value": "STDDEV",
                        },
                        {
                            "label": "Year",
                            "value": "YEAR",
                        },
                    ],
                    value="STDDEV",
                    clearable=False,
                ),
            ]
        )


class MapPlotViewElement(ViewElementABC):
    @dataclass(frozen=True)
    class Elements:
        MAP_PLOT = "map_plot"

    @dataclass(frozen=True)
    class Settings:
        MAP_PLOT_SETTINGS = "map_plot_settings"

    def __init__(
        self,
        flex_grow: int = 1,
        screenshot_filename: str = "webviz-screenshot.png",
    ) -> None:
        super().__init__(
            flex_grow, screenshot_filename, ViewElementABC.LoadingMask.Graph
        )

        self.add_settings_group(
            MapPlotViewElementSettings(), self.Settings.MAP_PLOT_SETTINGS
        )

    def layout(self) -> Union[str, Type[Component]]:
        return wcc.Graph(
            style={"height": "84vh"},
            id=self.register_component_uuid(self.Elements.MAP_PLOT),
        )


class FormationsGraphSelections(SettingsGroupABC):
    """Settings for formations graph in Settings Drawer"""

    @dataclass(frozen=True)
    class Elements:
        FORMATIONS_ENSEMBLE = "formations-ensemble"
        FORMATIONS_WELL = "formations-well"
        FORMATIONS_DATE = "formations-date"

    def __init__(
        self,
        ensembles: List[str],
        well_names: List[str],
        date_in_well: Callable[[str], List[str]],
    ) -> None:
        super().__init__("Formations Graph Selections")
        self._ensembles = ensembles
        self._well_names = well_names
        self._initial_well = self._well_names[0] if self._well_names else None
        self._dates_in_well = (
            date_in_well(self._initial_well) if self._initial_well else []
        )

    def layout(self) -> Type[Component]:
        return html.Div(
            children=[
                wcc.Dropdown(
                    label="Ensemble",
                    id=self.register_component_uuid(self.Elements.FORMATIONS_ENSEMBLE),
                    options=[{"label": ens, "value": ens} for ens in self._ensembles],
                    value=self._ensembles[0] if self._ensembles else None,
                    multi=True,
                    clearable=False,
                ),
                wcc.Dropdown(
                    label="Well",
                    id=self.register_component_uuid(self.Elements.FORMATIONS_WELL),
                    options=[
                        {"label": well, "value": well} for well in self._well_names
                    ],
                    value=self._initial_well,
                    clearable=False,
                ),
                wcc.Dropdown(
                    label="Date",
                    id=self.register_component_uuid(self.Elements.FORMATIONS_DATE),
                    options=[
                        {"label": date, "value": date} for date in self._dates_in_well
                    ],
                    clearable=False,
                    value=self._dates_in_well[0] if self._dates_in_well else None,
                ),
            ]
        )


class FormationsGraphViewElementsSettings(SettingsGroupABC):
    """Settings for formations graph in view element settings"""

    @dataclass(frozen=True)
    class Elements:
        FORMATIONS_LINETYPE = "formations-linetype"
        FORMATIONS_DEPTHOPTION = "formations-depthoption"

    def __init__(self) -> None:
        super().__init__("Formations Graph Settings")

    def layout(self) -> Type[Component]:
        return html.Div(
            children=[
                wcc.RadioItems(
                    label="Plot simulations as",
                    id=self.register_component_uuid(self.Elements.FORMATIONS_LINETYPE),
                    options=[
                        {
                            "label": "Realization lines",
                            "value": "realization",
                        },
                        {
                            "label": "Statistical fanchart",
                            "value": "fanchart",
                        },
                    ],
                    value="realization",
                ),
                wcc.RadioItems(
                    label="Depth option",
                    id=self.register_component_uuid(
                        self.Elements.FORMATIONS_DEPTHOPTION
                    ),
                    options=[
                        {
                            "label": "TVD",
                            "value": "TVD",
                        },
                        {
                            "label": "MD",
                            "value": "MD",
                        },
                    ],
                    value="TVD",
                ),
            ]
        )


class FormationsGraphViewElement(ViewElementABC):
    @dataclass(frozen=True)
    class Elements:
        FORMATONS_GRAPH = "formations_graph"

    @dataclass(frozen=True)
    class Settings:
        FORMATION_GRAPH_SETTINGS = "formation_graph_settings"

    def __init__(
        self, flex_grow: int = 1, screenshot_filename: str = "webviz-screenshot.png"
    ) -> None:
        super().__init__(
            flex_grow, screenshot_filename, ViewElementABC.LoadingMask.Graph
        )

        self.add_settings_group(
            FormationsGraphViewElementsSettings(),
            self.Settings.FORMATION_GRAPH_SETTINGS,
        )

    def layout(self) -> Union[str, Type[Component]]:
        return wcc.Graph(
            style={"height": "84vh"},
            id=self.register_component_uuid(self.Elements.FORMATONS_GRAPH),
        )


class RftMap(ViewABC):
    @dataclass(frozen=True)
    class ViewElements:
        MAP_PLOT_ROW_ELEMENT = "map_plot_row_element"
        FORMATONS_GRAPH_ROW_ELEMENT = "formations_graph_row_element"

    @dataclass(frozen=True)
    class Settings:
        MAP_PLOT_SELECTIONS = "MapPlotSelections"
        FORMATION_GRAPH_SELECTIONS = "FormationGraphSelections"

    def __init__(self, data_model: RftPlotterDataModel) -> None:
        super().__init__("RFT Map")

        self._data_model = data_model

        self.map_plot_view_element = MapPlotViewElement()
        self.formations_graph_view_element = FormationsGraphViewElement()

        row = self.add_row()
        row.add_view_element(
            self.map_plot_view_element, RftMap.ViewElements.MAP_PLOT_ROW_ELEMENT
        )
        row.add_view_element(
            self.formations_graph_view_element,
            RftMap.ViewElements.FORMATONS_GRAPH_ROW_ELEMENT,
        )

        self.add_settings_group(
            MapPlotSelections(
                ensembles=data_model.ensembles,
                zone_names=data_model.zone_names,
                start_date=data_model.ertdatadf["DATE_IDX"].min(),
                end_date=data_model.ertdatadf["DATE_IDX"].max(),
                date_marks=data_model.date_marks,
            ),
            RftMap.Settings.MAP_PLOT_SELECTIONS,
        )
        self.add_settings_group(
            FormationsGraphSelections(
                ensembles=data_model.ensembles,
                well_names=data_model.well_names,
                date_in_well=data_model.date_in_well,
            ),
            RftMap.Settings.FORMATION_GRAPH_SELECTIONS,
        )

    def _set_callbacks(self, app: Dash) -> None:
        @app.callback(
            Output(
                self.view_element_uuid(
                    self.ViewElements.MAP_PLOT_ROW_ELEMENT,
                    MapPlotViewElement.Elements.MAP_PLOT,
                ),
                "figure",
            ),
            Input(
                self.settings_group_uuid(
                    RftMap.Settings.MAP_PLOT_SELECTIONS,
                    MapPlotSelections.Elements.MAP_ENSEMBLE,
                ),
                "value",
            ),
            Input(
                self.settings_group_uuid(
                    RftMap.Settings.MAP_PLOT_SELECTIONS,
                    MapPlotSelections.Elements.MAP_DATE_RANGE,
                ),
                "value",
            ),
            Input(
                self.settings_group_uuid(
                    RftMap.Settings.MAP_PLOT_SELECTIONS,
                    MapPlotSelections.Elements.MAP_ZONES,
                ),
                "value",
            ),
            Input(
                self.map_plot_view_element.setting_group_uuid(
                    MapPlotViewElement.Settings.MAP_PLOT_SETTINGS,
                    MapPlotViewElementSettings.Elements.MAP_SIZE_BY,
                ),
                "value",
            ),
            Input(
                self.map_plot_view_element.setting_group_uuid(
                    MapPlotViewElement.Settings.MAP_PLOT_SETTINGS,
                    MapPlotViewElementSettings.Elements.MAP_COLOR_BY,
                ),
                "value",
            ),
        )
        def _update_map(
            ensemble: str,
            dates: List[float],
            zones: List[str],
            sizeby: str,
            colorby: str,
        ) -> Dict[str, Any]:
            figure = MapFigure(self._data_model.ertdatadf, ensemble, zones)
            if self._data_model.faultlinesdf is not None:
                figure.add_fault_lines(self._data_model.faultlinesdf)
            figure.add_misfit_plot(sizeby, colorby, dates)

            _output = {"data": figure.traces, "layout": figure.layout}
            return _output

        @app.callback(
            Output(
                self.view_element_uuid(
                    self.ViewElements.FORMATONS_GRAPH_ROW_ELEMENT,
                    FormationsGraphViewElement.Elements.FORMATONS_GRAPH,
                ),
                "figure",
            ),
            Input(
                self.settings_group_uuid(
                    RftMap.Settings.FORMATION_GRAPH_SELECTIONS,
                    FormationsGraphSelections.Elements.FORMATIONS_WELL,
                ),
                "value",
            ),
            Input(
                self.settings_group_uuid(
                    RftMap.Settings.FORMATION_GRAPH_SELECTIONS,
                    FormationsGraphSelections.Elements.FORMATIONS_DATE,
                ),
                "value",
            ),
            Input(
                self.settings_group_uuid(
                    RftMap.Settings.FORMATION_GRAPH_SELECTIONS,
                    FormationsGraphSelections.Elements.FORMATIONS_ENSEMBLE,
                ),
                "value",
            ),
            Input(
                self.formations_graph_view_element.setting_group_uuid(
                    FormationsGraphViewElement.Settings.FORMATION_GRAPH_SETTINGS,
                    FormationsGraphViewElementsSettings.Elements.FORMATIONS_LINETYPE,
                ),
                "value",
            ),
            Input(
                self.formations_graph_view_element.setting_group_uuid(
                    FormationsGraphViewElement.Settings.FORMATION_GRAPH_SETTINGS,
                    FormationsGraphViewElementsSettings.Elements.FORMATIONS_DEPTHOPTION,
                ),
                "value",
            ),
        )
        def _update_formation_plot(
            well: str, date: str, ensembles: List[str], linetype: str, depth_option: str
        ) -> Union[str, Dict[str, Any]]:
            if not ensembles:
                return "No ensembles selected"

            if date not in self._data_model.date_in_well(well):
                raise PreventUpdate

            figure = FormationFigure(
                well=well,
                ertdf=self._data_model.ertdatadf,
                enscolors=self._data_model.enscolors,
                depth_option=depth_option,
                date=date,
                ensembles=ensembles,
                simdf=self._data_model.simdf,
                obsdf=self._data_model.obsdatadf,
            )
            if figure.ertdf.empty:
                return "No data matching the given filter criteria."

            if self._data_model.formations is not None:
                figure.add_formation(self._data_model.formationdf)

            figure.add_simulated_lines(linetype)
            figure.add_additional_observations()
            figure.add_ert_observed()

            return figure.figure

        @app.callback(
            Output(
                self.settings_group_uuid(
                    RftMap.Settings.FORMATION_GRAPH_SELECTIONS,
                    FormationsGraphSelections.Elements.FORMATIONS_WELL,
                ),
                "value",
            ),
            Input(
                self.view_element_uuid(
                    self.ViewElements.MAP_PLOT_ROW_ELEMENT,
                    MapPlotViewElement.Elements.MAP_PLOT,
                ),
                "clickData",
            ),
            State(
                self.settings_group_uuid(
                    RftMap.Settings.FORMATION_GRAPH_SELECTIONS,
                    FormationsGraphSelections.Elements.FORMATIONS_WELL,
                ),
                "value",
            ),
        )
        def _get_clicked_well(
            click_data: Dict[str, List[Dict[str, Any]]], well: str
        ) -> str:
            if not click_data:
                return well
            for layer in click_data["points"]:
                try:
                    return layer["customdata"]
                except KeyError:
                    pass
            raise PreventUpdate

        @app.callback(
            Output(
                self.formations_graph_view_element.setting_group_uuid(
                    FormationsGraphViewElement.Settings.FORMATION_GRAPH_SETTINGS,
                    FormationsGraphViewElementsSettings.Elements.FORMATIONS_LINETYPE,
                ),
                "options",
            ),
            Output(
                self.formations_graph_view_element.setting_group_uuid(
                    FormationsGraphViewElement.Settings.FORMATION_GRAPH_SETTINGS,
                    FormationsGraphViewElementsSettings.Elements.FORMATIONS_LINETYPE,
                ),
                "value",
            ),
            Input(
                self.formations_graph_view_element.setting_group_uuid(
                    FormationsGraphViewElement.Settings.FORMATION_GRAPH_SETTINGS,
                    FormationsGraphViewElementsSettings.Elements.FORMATIONS_DEPTHOPTION,
                ),
                "value",
            ),
            State(
                self.formations_graph_view_element.setting_group_uuid(
                    FormationsGraphViewElement.Settings.FORMATION_GRAPH_SETTINGS,
                    FormationsGraphViewElementsSettings.Elements.FORMATIONS_LINETYPE,
                ),
                "value",
            ),
            State(
                self.settings_group_uuid(
                    RftMap.Settings.FORMATION_GRAPH_SELECTIONS,
                    FormationsGraphSelections.Elements.FORMATIONS_WELL,
                ),
                "value",
            ),
            State(
                self.settings_group_uuid(
                    RftMap.Settings.FORMATION_GRAPH_SELECTIONS,
                    FormationsGraphSelections.Elements.FORMATIONS_DATE,
                ),
                "value",
            ),
        )
        def _update_linetype(
            depth_option: str,
            current_linetype: str,
            current_well: str,
            current_date: str,
        ) -> Tuple[List[Dict[str, str]], str]:
            if self._data_model.simdf is not None:
                df = filter_frame(
                    self._data_model.simdf,
                    {"WELL": current_well, "DATE": current_date},
                )
                if depth_option == "TVD" or (
                    depth_option == "MD"
                    and "CONMD" in self._data_model.simdf
                    and len(df["CONMD"].unique()) == len(df["DEPTH"].unique())
                ):

                    return [
                        {
                            "label": "Realization lines",
                            "value": "realization",
                        },
                        {
                            "label": "Statistical fanchart",
                            "value": "fanchart",
                        },
                    ], current_linetype

            return [
                {
                    "label": "Realization lines",
                    "value": "realization",
                },
            ], "realization"

        @app.callback(
            Output(
                self.settings_group_uuid(
                    RftMap.Settings.FORMATION_GRAPH_SELECTIONS,
                    FormationsGraphSelections.Elements.FORMATIONS_DATE,
                ),
                "options",
            ),
            Output(
                self.settings_group_uuid(
                    RftMap.Settings.FORMATION_GRAPH_SELECTIONS,
                    FormationsGraphSelections.Elements.FORMATIONS_DATE,
                ),
                "value",
            ),
            Input(
                self.settings_group_uuid(
                    RftMap.Settings.FORMATION_GRAPH_SELECTIONS,
                    FormationsGraphSelections.Elements.FORMATIONS_WELL,
                ),
                "value",
            ),
            State(
                self.settings_group_uuid(
                    RftMap.Settings.FORMATION_GRAPH_SELECTIONS,
                    FormationsGraphSelections.Elements.FORMATIONS_DATE,
                ),
                "value",
            ),
        )
        def _update_date(
            well: str, current_date: str
        ) -> Tuple[List[Dict[str, str]], str]:
            dates = self._data_model.date_in_well(well)
            available_dates = [{"label": date, "value": date} for date in dates]
            date = current_date if current_date in dates else dates[0]
            return available_dates, date
