# from typing import List, Type, Union

# from dash.development.base_component import Component  # type: ignore
# from dash import html

# import webviz_core_components as wcc

# from webviz_config.webviz_plugin_subclasses._views import ViewABC, ViewElementABC
# from webviz_config.webviz_plugin_subclasses._settings_group_abc import SettingsGroupABC

# from .._business_logic import RftPlotterDataModel


# class ParameterResponseSelections(SettingsGroupABC):
#     def __init__(
#         self,
#         ensembles: List[str],
#         well_names: List[str],
#         parameters: List[str],
#     ) -> None:
#         super().__init__("Selections")

#     @property
#     def layout(self) -> Type[Component]:
#         return html.Div


# class ParameterResponseOptions(SettingsGroupABC):
#     def __init__(self) -> None:
#         super().__init__("Options")

#     @property
#     def layout(self) -> Type[Component]:
#         return html.Div(
#             children=[
#                 wcc.Checklist(
#                     id=self.register_component_uuid(
#                         RftMapViewElements.DISPLAY_PARAM_FILTER
#                     ),
#                     options=[{"label": "Show parameter filter", "value": "Show"}],
#                     value=[],
#                 ),
#                 wcc.RadioItems(
#                     label="Correlation options",
#                     id=self.register_component_uuid(
#                         RftMapViewElements.PARAMRESP_CORRTYPE
#                     ),
#                     options=[
#                         {
#                             "label": "Simulated vs parameters",
#                             "value": "sim_vs_param",
#                         },
#                         {
#                             "label": "Parameter vs simulated",
#                             "value": "param_vs_sim",
#                         },
#                     ],
#                     value="sim_vs_param",
#                 ),
#                 wcc.RadioItems(
#                     label="Depth option",
#                     id=self.register_component_uuid(
#                         RftMapViewElements.PARAMRESP_DEPTHOPTION
#                     ),
#                     options=[
#                         {
#                             "label": "TVD",
#                             "value": "TVD",
#                         },
#                         {
#                             "label": "MD",
#                             "value": "MD",
#                         },
#                     ],
#                     value="TVD",
#                 ),
#             ]
#         )


# class RftParameterResponse(ViewABC):
#     def __init__(self, data_model: RftPlotterDataModel) -> None:
#         super().__init__("RFT arameter Response")
