from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from dash.development.base_component import Component
from dash import html, Dash, Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd

import webviz_core_components as wcc

from webviz_config.webviz_plugin_subclasses._views import ViewABC, ViewElementABC
from webviz_config.webviz_plugin_subclasses._settings_group_abc import SettingsGroupABC

from ..utils.parameter_filter import ParameterFilter

from ...._figures import BarChart, ScatterPlot
from .._business_logic import RftPlotterDataModel, correlate
from .._figures._formation_figure import FormationFigure


class ParameterResponseSelections(SettingsGroupABC):
    """Settings for parameter response in Settings Drawer"""

    @dataclass(frozen=True)
    class Elements:
        ENSEMBLE_DROPDOWN = "ensemble_dropdown"
        WELL_DROPDOWN = "well_dropdown"
        DATE_DROPDOWN = "date_dropdown"
        ZONE_DROPDOWN = "zone_dropdown"
        DATE_DROPDOWN_CONTAINER = "date_dropdown_container"
        ZONE_DROPDOWN_CONTAINER = "zone_dropdown_container"
        PARAMETER_DROPDOWN = "parameter_dropdown"

        PARAMETER_FILTER_OPEN_BUTTON = "parameter_filter_open_button"
        PARAMETER_FILTER_DIALOG = "parameter_filter_dialog"
        PARAMETER_FILTER = "parameter_filter"

    def __init__(
        self,
        ensembles: List[str],
        well_names: List[str],
        parameters: List[str],
        df_parameter_model: pd.DataFrame,
        parameter_model_mc_ensembles: List[str],
    ) -> None:
        super().__init__("Selections")

        self._ensembles = ensembles
        self._well_names = well_names
        self._parameters = parameters

        self._df_parameter_model = df_parameter_model
        self._parameter_model_mc_ensembles = parameter_model_mc_ensembles
        self._parameter_filter = ParameterFilter(
            parameter_filter_id=self.Elements.PARAMETER_FILTER,
            dframe=self._df_parameter_model[
                self._df_parameter_model["ENSEMBLE"].isin(
                    self._parameter_model_mc_ensembles
                )
            ].copy(),
            component_uuid=self.component_uuid,
            register_component_uuid=self.register_component_uuid,
            reset_on_ensemble_update=True,
        )

    def layout(self) -> Type[Component]:
        return html.Div(
            children=[
                wcc.Dropdown(
                    label="Ensemble",
                    id=self.register_component_uuid(self.Elements.ENSEMBLE_DROPDOWN),
                    options=[{"label": ens, "value": ens} for ens in self._ensembles],
                    value=self._ensembles[0] if self._ensembles else None,
                    clearable=False,
                ),
                wcc.Dropdown(
                    label="Well",
                    id=self.register_component_uuid(self.Elements.WELL_DROPDOWN),
                    options=[
                        {"label": well, "value": well} for well in self._well_names
                    ],
                    value=self._well_names[0] if self._well_names else None,
                    clearable=False,
                ),
                html.Div(
                    id=self.register_component_uuid(
                        self.Elements.DATE_DROPDOWN_CONTAINER
                    ),
                    children=[
                        wcc.Dropdown(
                            label="Date",
                            id=self.register_component_uuid(
                                self.Elements.DATE_DROPDOWN
                            ),
                            options=[],
                            value=None,
                            clearable=False,
                        )
                    ],
                ),
                html.Div(
                    id=self.register_component_uuid(
                        self.Elements.ZONE_DROPDOWN_CONTAINER
                    ),
                    children=[
                        wcc.Dropdown(
                            label="Zone",
                            id=self.register_component_uuid(
                                self.Elements.ZONE_DROPDOWN
                            ),
                            options=[],
                            clearable=False,
                            value=None,
                        )
                    ],
                ),
                wcc.Dropdown(
                    label="Parameter",
                    id=self.register_component_uuid(self.Elements.PARAMETER_DROPDOWN),
                    options=[
                        {"label": param, "value": param} for param in self._parameters
                    ],
                    clearable=False,
                    value=None,
                ),
                html.Button(
                    "Parameter Filter",
                    id=self.register_component_uuid(
                        self.Elements.PARAMETER_FILTER_OPEN_BUTTON
                    ),
                    style={
                        "margin-top": "10px",
                        "margin-bottom": "10px",
                    },
                ),
                wcc.Dialog(
                    title="Parameter Filter",
                    id=self.register_component_uuid(
                        self.Elements.PARAMETER_FILTER_DIALOG
                    ),
                    draggable=True,
                    max_width="lg",
                    children=html.Div(
                        style={"height": "70vh", "width": "30vw"},
                        children=self._parameter_filter.layout,
                    ),
                ),
            ]
        )

    def _set_callbacks(self, __app: Dash) -> None:
        self._parameter_filter.set_callbacks()


class BarchartViewElementSettings(SettingsGroupABC):
    @dataclass(frozen=True)
    class Elements:
        CORRELATION_TYPE = "barchart_correlation_type"

    def __init__(self) -> None:
        super().__init__("Barchart Options")

    def layout(self) -> Type[Component]:
        return wcc.RadioItems(
            label="Correlation options",
            id=self.register_component_uuid(self.Elements.CORRELATION_TYPE),
            options=[
                {
                    "label": "Simulated vs parameters",
                    "value": "sim_vs_param",
                },
                {
                    "label": "Parameter vs simulated",
                    "value": "param_vs_sim",
                },
            ],
            value="sim_vs_param",
        )


class FormationsViewElementSettings(SettingsGroupABC):
    @dataclass(frozen=True)
    class Elements:
        DEPTH_OPTION = "formations_depth_option"

    def __init__(self) -> None:
        super().__init__("Formations options")

    def layout(self) -> Type[Component]:
        return wcc.RadioItems(
            label="Depth option",
            id=self.register_component_uuid(self.Elements.DEPTH_OPTION),
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
        )


class BarchartViewElement(ViewElementABC):
    @dataclass(frozen=True)
    class Elements:
        BARCHART_GRAPH = "barchart_graph"

    @dataclass(frozen=True)
    class Settings:
        BARCHART_SETTINGS = "barchart_settings"

    def __init__(
        self, flex_grow: int = 1, screenshot_filename: str = "webviz-screenshot.png"
    ) -> None:
        super().__init__(
            flex_grow, screenshot_filename, ViewElementABC.LoadingMask.Graph
        )

        self.add_settings_group(
            BarchartViewElementSettings(), self.Settings.BARCHART_SETTINGS
        )

    def layout(self) -> Union[str, Type[Component]]:
        return wcc.Graph(
            style={"displayModeBar": False},
            id=self.register_component_uuid(self.Elements.BARCHART_GRAPH),
        )


class ScatterplotViewElement(ViewElementABC):
    @dataclass(frozen=True)
    class Elements:
        SCATTERPLOT_GRAPH = "scatterplot_graph"

    def __init__(
        self, flex_grow: int = 1, screenshot_filename: str = "webviz-screenshot.png"
    ) -> None:
        super().__init__(
            flex_grow, screenshot_filename, ViewElementABC.LoadingMask.Graph
        )

    def layout(self) -> Union[str, Type[Component]]:
        return wcc.Graph(
            style={"displayModeBar": False},
            id=self.register_component_uuid(self.Elements.SCATTERPLOT_GRAPH),
        )


class FormationsViewElement(ViewElementABC):
    @dataclass(frozen=True)
    class Elements:
        FORMATIONS_GRAPH = "formations_graph"

    @dataclass(frozen=True)
    class Settings:
        FORMATIONS_SETTINGS = "formations_settings"

    def __init__(
        self, flex_grow: int = 1, screenshot_filename: str = "webviz-screenshot.png"
    ) -> None:
        super().__init__(
            flex_grow, screenshot_filename, ViewElementABC.LoadingMask.Graph
        )

        self.add_settings_group(
            FormationsViewElementSettings(), self.Settings.FORMATIONS_SETTINGS
        )

    def layout(self) -> Union[str, Type[Component]]:
        return wcc.Graph(
            style={"height": "87vh"},
            id=self.register_component_uuid(self.Elements.FORMATIONS_GRAPH),
        )


class RftParameterResponse(ViewABC):
    @dataclass(frozen=True)
    class ViewElements:
        BARCHART_VIEW_ELEMENT = "barchart_view_element"
        SCATTERPLOT_VIEW_ELEMENT = "scatterplot_view_element"
        FORMATIONS_VIEW_ELEMENT = "formations_view_element"

    @dataclass(frozen=True)
    class Settings:
        SELECTIONS = "selections"

    def __init__(self, data_model: RftPlotterDataModel) -> None:
        super().__init__("RFT Parameter Response")

        self._data_model = data_model

        self._barchart_view_element = BarchartViewElement()
        self._scatterplot_view_element = ScatterplotViewElement()
        self._formations_view_element = FormationsViewElement()

        first_column = self.add_column()
        first_column_first_row = first_column.make_row()
        first_column_first_row.add_view_element(
            self._barchart_view_element, self.ViewElements.BARCHART_VIEW_ELEMENT
        )
        first_column_second_row = first_column.make_row()
        first_column_second_row.add_view_element(
            self._scatterplot_view_element, self.ViewElements.SCATTERPLOT_VIEW_ELEMENT
        )

        second_column = self.add_column()
        second_column.add_view_element(
            self._formations_view_element, self.ViewElements.FORMATIONS_VIEW_ELEMENT
        )

        self.add_settings_group(
            ParameterResponseSelections(
                ensembles=self._data_model.ensembles,
                well_names=self._data_model.well_names,
                parameters=self._data_model.parameters,
                df_parameter_model=self._data_model.param_model.dataframe,
                parameter_model_mc_ensembles=self._data_model.param_model.mc_ensembles,
            ),
            self.Settings.SELECTIONS,
        )

    def _set_callbacks(self, app: Dash) -> None:
        @app.callback(
            Output(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.PARAMETER_DROPDOWN,
                ),
                "value",
            ),
            Input(
                self._barchart_view_element.component_uuid(
                    BarchartViewElement.Elements.BARCHART_GRAPH
                ).to_string(),
                "clickData",
            ),
            State(
                self._barchart_view_element.setting_group_uuid(
                    BarchartViewElement.Settings.BARCHART_SETTINGS,
                    BarchartViewElementSettings.Elements.CORRELATION_TYPE,
                ),
                "value",
            ),
            prevent_initial_call=True,
        )
        def _update_param_from_clickdata(
            corr_vector_clickdata: Union[None, dict],
            corrtype: str,
        ) -> str:
            """Update the selected parameter from clickdata"""
            if corr_vector_clickdata is None or corrtype == "param_vs_sim":
                raise PreventUpdate
            return corr_vector_clickdata.get("points", [{}])[0].get("y")

        @app.callback(
            Output(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.WELL_DROPDOWN,
                ),
                "value",
            ),
            Output(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.DATE_DROPDOWN_CONTAINER,
                ),
                "children",
            ),
            Output(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.ZONE_DROPDOWN_CONTAINER,
                ),
                "children",
            ),
            Input(
                self._barchart_view_element.component_uuid(
                    BarchartViewElement.Elements.BARCHART_GRAPH
                ).to_string(),
                "clickData",
            ),
            State(
                self._barchart_view_element.setting_group_uuid(
                    BarchartViewElement.Settings.BARCHART_SETTINGS,
                    BarchartViewElementSettings.Elements.CORRELATION_TYPE,
                ),
                "value",
            ),
            State(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.WELL_DROPDOWN,
                ),
                "value",
            ),
            prevent_initial_call=True,
        )
        def _update_selections_from_clickdata(
            corr_vector_clickdata: Union[None, dict],
            corrtype: str,
            well: str,
        ) -> Tuple[str, wcc.Dropdown, wcc.Dropdown]:
            # Update well, date and zone from clickdata
            if corr_vector_clickdata is None or corrtype == "sim_vs_param":
                raise PreventUpdate

            clickdata = corr_vector_clickdata.get("points", [{}])[0].get("y")
            ls_clickdata = clickdata.split()

            dates_in_well, zones_in_well = self._data_model.well_dates_and_zones(well)
            dates_dropdown = wcc.Dropdown(
                label="Date",
                id=self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.DATE_DROPDOWN,
                ),
                options=[{"label": date, "value": date} for date in dates_in_well],
                value=ls_clickdata[1],
                clearable=False,
            )
            zones_dropdown = wcc.Dropdown(
                label="Zone",
                id=self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.ZONE_DROPDOWN,
                ),
                options=[{"label": zone, "value": zone} for zone in zones_in_well],
                value=ls_clickdata[2],
                clearable=False,
            )

            return ls_clickdata[0], dates_dropdown, zones_dropdown

        @app.callback(
            Output(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.DATE_DROPDOWN,
                ),
                "options",
            ),
            Output(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.DATE_DROPDOWN,
                ),
                "value",
            ),
            Output(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.ZONE_DROPDOWN,
                ),
                "options",
            ),
            Output(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.ZONE_DROPDOWN,
                ),
                "value",
            ),
            Input(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.WELL_DROPDOWN,
                ),
                "value",
            ),
            State(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.ZONE_DROPDOWN,
                ),
                "value",
            ),
        )
        def _update_date_and_zone(
            well: str, zone_state: str
        ) -> Tuple[List[Dict[str, str]], str, List[Dict[str, str]], str]:
            """Update dates and zones when selecting well. If the current
            selected zone is also present in the new well it will be kept as value.
            """
            dates_in_well, zones_in_well = self._data_model.well_dates_and_zones(well)
            return (
                [{"label": date, "value": date} for date in dates_in_well],
                dates_in_well[0],
                [{"label": zone, "value": zone} for zone in zones_in_well],
                zone_state if zone_state in zones_in_well else zones_in_well[0],
            )

        # @app.callback(
        #     Output(
        #         self.settings_group_uuid(
        #             self.Settings.SELECTIONS,
        #             ParameterResponseSelections.Elements.WELL_DROPDOWN,
        #         ),
        #         "value",
        #     ),
        #     Output(
        #         self.settings_group_uuid(
        #             self.Settings.SELECTIONS,
        #             ParameterResponseSelections.Elements.DATE_DROPDOWN,
        #         ),
        #         "options",
        #     ),
        #     Output(
        #         self.settings_group_uuid(
        #             self.Settings.SELECTIONS,
        #             ParameterResponseSelections.Elements.DATE_DROPDOWN,
        #         ),
        #         "value",
        #     ),
        #     Output(
        #         self.settings_group_uuid(
        #             self.Settings.SELECTIONS,
        #             ParameterResponseSelections.Elements.ZONE_DROPDOWN,
        #         ),
        #         "options",
        #     ),
        #     Output(
        #         self.settings_group_uuid(
        #             self.Settings.SELECTIONS,
        #             ParameterResponseSelections.Elements.ZONE_DROPDOWN,
        #         ),
        #         "value",
        #     ),
        #     Input(
        #         self.settings_group_uuid(
        #             self.Settings.SELECTIONS,
        #             ParameterResponseSelections.Elements.WELL_DROPDOWN,
        #         ),
        #         "value",
        #     ),
        #     Input(
        #         self._barchart_view_element.component_uuid(
        #             BarchartViewElement.Elements.BARCHART_GRAPH
        #         ),
        #         "clickData",
        #     ),
        #     State(
        #         self._barchart_view_element.setting_group_uuid(
        #             BarchartViewElement.Settings.BARCHART_SETTINGS,
        #             BarchartViewElementSettings.Elements.CORRELATION_TYPE,
        #         ),
        #         "value",
        #     ),
        #     State(
        #         self.settings_group_uuid(
        #             self.Settings.SELECTIONS,
        #             ParameterResponseSelections.Elements.ZONE_DROPDOWN,
        #         ),
        #         "value",
        #     ),
        # )
        # def _update_from_barchart_clickdata_and_well_selection(
        #     corr_vector_clickdata: Union[None, dict],
        #     well: str,
        #     corrtype: str,
        #     zone_state: str,
        #     # ) -> Tuple[str, wcc.Dropdown, wcc.Dropdown]:
        # ) -> Tuple[str, List[Dict[str, str]], str, List[Dict[str, str]], str]:
        #     """
        #     Merged original _update_selections_from_clickdata and _update_date_and_zone
        #     into one callback. Removed original html.Div around dropdowns
        #     """
        #     raise PreventUpdate
        #     ctx = dash.callback_context.triggered
        #     trigger_id = ctx[0]["prop_id"].split(".")[0]

        #     if trigger_id == self._barchart_view_element.component_uuid(
        #         BarchartViewElement.Elements.BARCHART_GRAPH
        #     ):
        #         # Update well, date and zone from clickdata
        #         if corr_vector_clickdata is None or corrtype == "sim_vs_param":
        #             raise PreventUpdate

        #         clickdata = corr_vector_clickdata.get("points", [{}])[0].get("y")
        #         ls_clickdata = clickdata.split()

        #         dates_in_well, zones_in_well = self._data_model.well_dates_and_zones(
        #             well
        #         )

        #         date_dropdown_options = [
        #             {"label": date, "value": date} for date in dates_in_well
        #         ]
        #         date_dropdown_value = str(ls_clickdata[1])

        #         zone_dropdown_options = [
        #             {"label": zone, "value": zone} for zone in zones_in_well
        #         ]
        #         zone_dropdown_value = str(ls_clickdata[2])
        #         # dates_dropdown = wcc.Dropdown(
        #         #     label="Date",
        #         #     id=get_uuid(LayoutElements.PARAMRESP_DATE),
        #         #     options=[{"label": date, "value": date} for date in dates_in_well],
        #         #     value=ls_clickdata[1],
        #         #     clearable=False,
        #         # )
        #         # zones_dropdown = wcc.Dropdown(
        #         #     label="Zone",
        #         #     id=get_uuid(LayoutElements.PARAMRESP_ZONE),
        #         #     options=[{"label": zone, "value": zone} for zone in zones_in_well],
        #         #     value=ls_clickdata[2],
        #         #     clearable=False,
        #         # )

        #         # return ls_clickdata[0], dates_dropdown, zones_dropdown

        #         return (
        #             ls_clickdata[0],
        #             date_dropdown_options,
        #             date_dropdown_value,
        #             zone_dropdown_options,
        #             zone_dropdown_value,
        #         )

        #     # Otherwise:
        #     dates_in_well, zones_in_well = self._data_model.well_dates_and_zones(well)
        #     return (
        #         dash.no_update,
        #         [{"label": date, "value": date} for date in dates_in_well],
        #         dates_in_well[0],
        #         [{"label": zone, "value": zone} for zone in zones_in_well],
        #         zone_state if zone_state in zones_in_well else zones_in_well[0],
        #     )

        @app.callback(
            Output(
                self._barchart_view_element.component_uuid(
                    BarchartViewElement.Elements.BARCHART_GRAPH
                ).to_string(),
                "figure",
            ),
            Output(
                self._scatterplot_view_element.component_uuid(
                    ScatterplotViewElement.Elements.SCATTERPLOT_GRAPH
                ).to_string(),
                "figure",
            ),
            Output(
                self._formations_view_element.component_uuid(
                    FormationsViewElement.Elements.FORMATIONS_GRAPH
                ).to_string(),
                "figure",
            ),
            Input(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.ENSEMBLE_DROPDOWN,
                ),
                "value",
            ),
            Input(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.WELL_DROPDOWN,
                ),
                "value",
            ),
            Input(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.DATE_DROPDOWN,
                ),
                "value",
            ),
            Input(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.ZONE_DROPDOWN,
                ),
                "value",
            ),
            Input(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.PARAMETER_DROPDOWN,
                ),
                "value",
            ),
            Input(
                self._barchart_view_element.setting_group_uuid(
                    BarchartViewElement.Settings.BARCHART_SETTINGS,
                    BarchartViewElementSettings.Elements.CORRELATION_TYPE,
                ),
                "value",
            ),
            Input(
                self._formations_view_element.setting_group_uuid(
                    FormationsViewElement.Settings.FORMATIONS_SETTINGS,
                    FormationsViewElementSettings.Elements.DEPTH_OPTION,
                ),
                "value",
            ),
            Input(
                {
                    "id": self.settings_group_uuid(
                        self.Settings.SELECTIONS,
                        ParameterResponseSelections.Elements.PARAMETER_FILTER,
                    ),
                    "type": "data-store",
                },
                "data",
            ),
        )
        # pylint: disable=too-many-locals
        def _update_paramresp_graphs(
            ensemble: str,
            well: str,
            date: str,
            zone: str,
            param: Optional[str],
            corrtype: str,
            depth_option: str,
            real_filter: Dict[str, List[int]],
        ) -> List[Optional[Any]]:
            """Main callback to update the graphs:

            * ranked correlations bar chart
            * response vs param scatter plot
            * formations chart RFT pressure vs depth, colored by parameter value
            """
            (
                df,
                obs,
                obs_err,
                ens_params,
                ens_rfts,
            ) = self._data_model.create_rft_and_param_pivot_table(
                ensemble=ensemble,
                well=well,
                date=date,
                zone=zone,
                reals=real_filter[ensemble],
                keep_all_rfts=(corrtype == "param_vs_sim"),
            )
            current_key = f"{well} {date} {zone}"

            if df is None:
                # This happens if the filtering criterias returns no data
                # Could f.ex happen when there are ensembles with different well names
                return ["No data matching the given filter criterias."] * 3
            if param is not None and param not in ens_params:
                # This happens if the selected parameter does not exist in the
                # selected ensemble
                return ["The selected parameter not valid for selected ensemble."] * 3
            if not ens_params:
                # This happens if there are multiple ensembles and one of the ensembles
                # doesn't have non-constant parameters.
                return ["The selected ensemble has no non-constant parameters."] * 3

            if corrtype == "sim_vs_param" or param is None:
                corrseries = correlate(df[ens_params + [current_key]], current_key)
                param = param if param is not None else corrseries.abs().idxmax()
                corr_title = f"{current_key} vs parameters"
                scatter_x, scatter_y, highlight_bar = param, current_key, param

            if corrtype == "param_vs_sim":
                corrseries = correlate(df[ens_rfts + [param]], param)
                corr_title = f"{param} vs simulated RFTs"
                scatter_x, scatter_y, highlight_bar = param, current_key, current_key

            # Correlation bar chart
            corrfig = BarChart(corrseries, n_rows=15, title=corr_title, orientation="h")
            corrfig.color_bars(highlight_bar, "#007079", 0.5)

            # Scatter plot
            scatterplot = ScatterPlot(
                df, scatter_y, scatter_x, "#007079", f"{current_key} vs {param}"
            )
            scatterplot.add_vertical_line_with_error(
                obs,
                obs_err,
                df[param].min(),
                df[param].max(),
            )

            # Formations plot
            formations_figure = FormationFigure(
                well=well,
                ertdf=self._data_model.ertdatadf,
                enscolors=self._data_model.enscolors,
                depth_option=depth_option,
                date=date,
                ensembles=[ensemble],
                reals=real_filter[ensemble],
                simdf=self._data_model.simdf,
                obsdf=self._data_model.obsdatadf,
            )

            if formations_figure.use_ertdf:
                return [
                    corrfig.figure,
                    scatterplot.figure,
                    f"Realization lines not available for depth option {depth_option}",
                ]

            if self._data_model.formations is not None:
                formations_figure.add_formation(
                    self._data_model.formationdf, fill_color=False
                )

            formations_figure.add_simulated_lines("realization")
            formations_figure.add_additional_observations()
            formations_figure.add_ert_observed()

            df_value_norm = self._data_model.get_param_real_and_value_df(
                ensemble, parameter=param, normalize=True
            )
            formations_figure.color_by_param_value(df_value_norm, param)

            return [
                corrfig.figure,
                scatterplot.figure,
                formations_figure.figure,
            ]

        @app.callback(
            Output(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.PARAMETER_FILTER_DIALOG,
                ),
                "open",
            ),
            [
                Input(
                    self.settings_group_uuid(
                        self.Settings.SELECTIONS,
                        ParameterResponseSelections.Elements.PARAMETER_FILTER_OPEN_BUTTON,
                    ),
                    "n_clicks",
                ),
            ],
            [
                State(
                    self.settings_group_uuid(
                        self.Settings.SELECTIONS,
                        ParameterResponseSelections.Elements.PARAMETER_FILTER_DIALOG,
                    ),
                    "open",
                )
            ],
        )
        def _toggle_parameter_filter_dialog_open(
            n_open_clicks: int, is_open: bool
        ) -> bool:
            if n_open_clicks:
                return not is_open
            raise PreventUpdate

        @app.callback(
            Output(
                {
                    "id": self.settings_group_uuid(
                        self.Settings.SELECTIONS,
                        ParameterResponseSelections.Elements.PARAMETER_FILTER,
                    ),
                    "type": "ensemble-update",
                },
                "data",
            ),
            Input(
                self.settings_group_uuid(
                    self.Settings.SELECTIONS,
                    ParameterResponseSelections.Elements.ENSEMBLE_DROPDOWN,
                ),
                "value",
            ),
        )
        def _update_parameter_filter_selection(ensemble: str) -> List[str]:
            """Update ensemble in parameter filter"""
            return [ensemble]
