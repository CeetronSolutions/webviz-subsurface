from typing import List, Type, Union

from dash.development.base_component import Component  # type: ignore
from dash import html, Dash, Input, Output

import webviz_core_components as wcc

from webviz_config.webviz_plugin_subclasses._views import ViewABC, ViewElementABC

from .._business_logic import RftPlotterDataModel, filter_frame
from .._figures._misfit_figure import update_misfit_plot
from .._shared_settings import ViewFilters


# class MisfitPlotSelections(SettingsGroupABC):
#     """Settings for misfit plot in Settings Drawer"""

#     # TODO: Move to shared settings when shared settings for selection of views is supported

#     class Elements:
#         # pylint: disable=too-few-public-methods
#         FILTER_ENSEMBLES = "ensembles-misfit"
#         FILTER_WELLS = "well-misfit"
#         FILTER_ZONES = "zones-misfit"
#         FILTER_DATES = "dates-misfit"

#     def __init__(
#         self,
#         ensembles: List[str],
#         well_names: List[str],
#         zone_names: List[str],
#         dates: List[str],
#     ) -> None:
#         super().__init__("Filters")

#         self._ensembles = ensembles
#         self._well_names = well_names
#         self._zone_names = zone_names
#         self._dates = dates

#     def layout(self) -> Type[Component]:
#         return html.Div(
#             children=[
#                 wcc.SelectWithLabel(
#                     label="Ensembles",
#                     size=min(4, len(self._ensembles)),
#                     id=self.register_component_uuid(
#                         MisfitPlotSelections.Elements.FILTER_ENSEMBLES
#                     ),
#                     options=[
#                         {"label": name, "value": name} for name in self._ensembles
#                     ],
#                     value=self._ensembles,
#                     multi=True,
#                 ),
#                 wcc.SelectWithLabel(
#                     label="Wells",
#                     size=min(20, len(self._well_names)),
#                     id=self.register_component_uuid(
#                         MisfitPlotSelections.Elements.FILTER_WELLS
#                     ),
#                     options=[
#                         {"label": name, "value": name} for name in self._well_names
#                     ],
#                     value=self._well_names,
#                     multi=True,
#                 ),
#                 wcc.SelectWithLabel(
#                     label="Zones",
#                     size=min(10, len(self._zone_names)),
#                     id=self.register_component_uuid(
#                         MisfitPlotSelections.Elements.FILTER_ZONES
#                     ),
#                     options=[
#                         {"label": name, "value": name} for name in self._zone_names
#                     ],
#                     value=self._zone_names,
#                     multi=True,
#                 ),
#                 wcc.SelectWithLabel(
#                     label="Dates",
#                     size=min(10, len(self._dates)),
#                     id=self.register_component_uuid(
#                         MisfitPlotSelections.Elements.FILTER_DATES
#                     ),
#                     options=[{"label": name, "value": name} for name in self._dates],
#                     value=self._dates,
#                     multi=True,
#                 ),
#             ]
#         )


class MisfitPlotViewElement(ViewElementABC):
    class Elements:
        # pylint: disable=too-few-public-methods
        MISFIT_GRAPHS_CONTAINER = "misfit_graphs_container"

    def layout(self) -> Union[str, Type[Component]]:
        return html.Div(
            id=self.register_component_uuid(
                MisfitPlotViewElement.Elements.MISFIT_GRAPHS_CONTAINER
            ),
            children=[],
        )


class RftMisfitPerReal(ViewABC):
    class ViewElements:
        # pylint: disable=too-few-public-methods
        MISFIT_PLOT_VIEW_ELEMENT = "misfit_plot_view_element"

    class Settings:
        # pylint: disable=too-few-public-methods
        MISFIT_PLOT_SELECTIONS = "misfit_plot_selections"

    def __init__(
        self,
        data_model: RftPlotterDataModel,
        shared_filters_id: str,
    ) -> None:
        super().__init__("RFT Misfit Per Real")

        self._data_model = data_model
        self._misfit_plot_view_element = MisfitPlotViewElement()
        self.add_view_element(
            self._misfit_plot_view_element, self.ViewElements.MISFIT_PLOT_VIEW_ELEMENT
        )
        self._shared_filters_id = shared_filters_id

    def _set_callbacks(self, app: Dash) -> None:
        if not self.shared_settings_group(self._shared_filters_id):
            return

        @app.callback(
            Output(
                self.view_element_uuid(
                    self.ViewElements.MISFIT_PLOT_VIEW_ELEMENT,
                    MisfitPlotViewElement.Elements.MISFIT_GRAPHS_CONTAINER,
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
        def _misfit_plot(
            wells: List[str], zones: List[str], dates: List[str], ensembles: List[str]
        ) -> Union[str, List[wcc.Graph]]:
            df = filter_frame(
                self._data_model.ertdatadf,
                {"WELL": wells, "ZONE": zones, "DATE": dates, "ENSEMBLE": ensembles},
            )
            if df.empty:
                return "No data matching the given filter criteria"

            return update_misfit_plot(df, self._data_model.enscolors)

        # @app.callback(
        #     Output(
        #         self.view_element_uuid(
        #             self.ViewElements.MISFIT_PLOT_VIEW_ELEMENT,
        #             MisfitPlotViewElement.Elements.MISFIT_GRAPHS_CONTAINER,
        #         ),
        #         "children",
        #     ),
        #     Input(
        #         self.settings_group_uuid(
        #             self.Settings.MISFIT_PLOT_SELECTIONS,
        #             MisfitPlotSelections.Elements.FILTER_WELLS,
        #         ),
        #         "value",
        #     ),
        #     Input(
        #         self.settings_group_uuid(
        #             self.Settings.MISFIT_PLOT_SELECTIONS,
        #             MisfitPlotSelections.Elements.FILTER_ZONES,
        #         ),
        #         "value",
        #     ),
        #     Input(
        #         self.settings_group_uuid(
        #             self.Settings.MISFIT_PLOT_SELECTIONS,
        #             MisfitPlotSelections.Elements.FILTER_DATES,
        #         ),
        #         "value",
        #     ),
        #     Input(
        #         self.settings_group_uuid(
        #             self.Settings.MISFIT_PLOT_SELECTIONS,
        #             MisfitPlotSelections.Elements.FILTER_ENSEMBLES,
        #         ),
        #         "value",
        #     ),
        # )
        # def _misfit_plot(
        #     wells: List[str], zones: List[str], dates: List[str], ensembles: List[str]
        # ) -> Union[str, List[wcc.Graph]]:
        #     df = filter_frame(
        #         self._data_model.ertdatadf,
        #         {"WELL": wells, "ZONE": zones, "DATE": dates, "ENSEMBLE": ensembles},
        #     )
        #     if df.empty:
        #         return "No data matching the given filter criteria"

        #     return update_misfit_plot(df, self._data_model.enscolors)
