from typing import List, Optional, Type
from xml.dom.minidom import Element
from webviz_config.webviz_plugin_subclasses import (
    SettingsGroupABC,
)
from dash.development.base_component import Component

from dash import Input, Output, State, callback, html
import webviz_core_components as wcc

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel

from .._layout_elements import ElementIds


class Filters(SettingsGroupABC):
    def __init__(self, volumes_model: InplaceVolumesModel) -> None:
        super().__init__("Filters")
        self.volumes_model = volumes_model
        self.selectors = ["ZONE", "REGION", "FACIES", "FIPNUM", "SET"]

    def layout(self) -> List[Component]:
        return [
            self.filter_dropdowns(),
            self.realization_filters(),
        ]

    def filter_dropdowns(
        self,
        hide_selectors: Optional[list] = None,
    ) -> html.Div:
        """Makes dropdowns for each selector"""
        dropdowns_layout: List[html.Div] = []
        hide_selectors = ["SENSNAME", "SENSTYPE", "SENSCASE"] + (
            hide_selectors if hide_selectors is not None else []
        )
        selectors = [
            x
            for x in self.volumes_model.selectors
            if x not in self.volumes_model.region_selectors + ["REAL"]
        ]
        for selector in selectors:
            dropdowns_layout.append(
                self.create_filter_select(
                    selector,
                    elements=list(self.volumes_model.dataframe[selector].unique()),
                    filter_type="undef",
                    hide=selector in hide_selectors,
                )
            )
        # Make region filters
        dropdowns_layout.append(
            html.Span("Region filters: ", style={"font-weight": "bold"})
        )
        if all(
            x in self.volumes_model.region_selectors
            for x in ["FIPNUM", "ZONE", "REGION"]
        ):
            dropdowns_layout.append(self.fipnum_vs_zone_region_switch())

        for selector in self.volumes_model.region_selectors:
            dropdowns_layout.append(
                self.create_filter_select(
                    selector,
                    elements=list(self.volumes_model.dataframe[selector].unique()),
                    filter_type="region",
                    hide=selector == "FIPNUM"
                    and len(self.volumes_model.region_selectors) > 1,
                )
            )
        return html.Div(dropdowns_layout)

    def create_filter_select(
        self,
        selector: str,
        elements: list,
        filter_type: str,
        hide: bool,
    ) -> html.Div:
        return html.Div(
            id=self.register_component_uuid(f"{selector}-{filter_type}"),
            style={"display": "inline" if len(elements) > 1 and not hide else "none"},
            children=wcc.SelectWithLabel(
                label=selector.lower().capitalize(),
                id=self.register_component_uuid(f"{selector}-select-{filter_type}"),
                options=[{"label": i, "value": i} for i in elements],
                value=elements,
                multi=True,
                size=min(15, len(elements)),
            ),
        )

    def fipnum_vs_zone_region_switch(self) -> wcc.RadioItems:
        return wcc.RadioItems(
            id=self.register_component_uuid("region-selector"),
            options=[
                {"label": "Region∕Zone", "value": "regzone"},
                {"label": "Fipnum", "value": "fipnum"},
            ],
            value="regzone",
            vertical=False,
        )

    def realization_filters(self) -> html.Div:
        reals = self.volumes_model.realizations
        return html.Div(
            style={"margin-top": "15px"},
            children=[
                html.Div(
                    style={"display": "inline-flex"},
                    children=[
                        html.Span(
                            "Realizations: ",
                            style={"font-weight": "bold"},
                        ),
                        html.Span(
                            id=self.register_component_uuid("real_text"),
                            style={"margin-left": "10px"},
                            children=f"{min(reals)}-{max(reals)}",
                        ),
                    ],
                ),
                wcc.RadioItems(
                    id=self.register_component_uuid("real-selector-option"),
                    options=[
                        {"label": "Range", "value": "range"},
                        {"label": "Select", "value": "select"},
                    ],
                    value="range",
                    vertical=False,
                ),
                wcc.RangeSlider(
                    wrapper_id=self.register_component_uuid("real-slider-wrapper"),
                    id=self.register_component_uuid("range"),
                    value=[min(reals), max(reals)],
                    min=min(reals),
                    max=max(reals),
                    marks={str(i): {"label": str(i)} for i in [min(reals), max(reals)]},
                ),
                html.Div(
                    style={"display": "none"},
                    children=wcc.Select(
                        id=self.register_component_uuid("REAL"),
                        options=[{"label": i, "value": i} for i in reals],
                        value=reals,
                    ),
                ),
            ],
        )
