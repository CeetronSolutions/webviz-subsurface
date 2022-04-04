from typing import List, Type

from dash.development.base_component import Component
from dash import html

import webviz_core_components as wcc

from webviz_config.webviz_plugin_subclasses._settings_group_abc import SettingsGroupABC


class ViewFilters(SettingsGroupABC):
    """Shared settings across views in plugin, placed in Settings Drawer"""

    class Elements:
        # pylint: disable=too-few-public-methods
        FILTER_ENSEMBLES = "ensembles"
        FILTER_WELLS = "well"
        FILTER_ZONES = "zones"
        FILTER_DATES = "dates"

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
                        ViewFilters.Elements.FILTER_ENSEMBLES
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
                    id=self.register_component_uuid(ViewFilters.Elements.FILTER_WELLS),
                    options=[
                        {"label": name, "value": name} for name in self._well_names
                    ],
                    value=self._well_names,
                    multi=True,
                ),
                wcc.SelectWithLabel(
                    label="Zones",
                    size=min(10, len(self._zone_names)),
                    id=self.register_component_uuid(ViewFilters.Elements.FILTER_ZONES),
                    options=[
                        {"label": name, "value": name} for name in self._zone_names
                    ],
                    value=self._zone_names,
                    multi=True,
                ),
                wcc.SelectWithLabel(
                    label="Dates",
                    size=min(10, len(self._dates)),
                    id=self.register_component_uuid(ViewFilters.Elements.FILTER_DATES),
                    options=[{"label": name, "value": name} for name in self._dates],
                    value=self._dates,
                    multi=True,
                ),
            ]
        )
