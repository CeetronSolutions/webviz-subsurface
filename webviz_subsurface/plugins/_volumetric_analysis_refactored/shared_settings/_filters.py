from typing import List, Optional, Union

import pandas as pd

from webviz_config.webviz_plugin_subclasses import (
    SettingsGroupABC,
)
from dash.development.base_component import Component

from dash import html
import webviz_core_components as wcc

from webviz_subsurface._models.inplace_volumes_model import InplaceVolumesModel


class Filters(SettingsGroupABC):
    def __init__(
        self,
        volumes_model: InplaceVolumesModel,
        disjoint_set_df: Optional[pd.DataFrame],
    ) -> None:
        super().__init__("Filters")
        self.volumes_model = volumes_model
        self.disjoint_set_df = disjoint_set_df
        self.selectors = ["ZONE", "REGION", "FACIES", "FIPNUM", "SET"]

    def layout(self) -> List[Component]:
        return [
            self.filter_dropdowns(),
            self.realization_filters(),
            self.fip_filter_dropdowns(),
        ]

    def filter_dropdowns(
        self,
    ) -> html.Div:
        """Makes dropdowns for each selector"""
        dropdowns_layout: List[Union[html.Div, html.Span]] = []
        hide_selectors = ["SENSNAME", "SENSTYPE", "SENSCASE"]

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
            id={
                "id": self.get_unique_id().to_string(),
                "wrapper": selector,
                "type": filter_type,
            },
            style={"display": "inline" if len(elements) > 1 and not hide else "none"},
            children=wcc.SelectWithLabel(
                label=selector.lower().capitalize(),
                id={
                    "id": self.get_unique_id().to_string(),
                    "selector": selector,
                    "type": filter_type,
                },
                options=[{"label": i, "value": i} for i in elements],
                value=elements,
                multi=True,
                size=min(15, len(elements)),
            ),
        )

    def fipnum_vs_zone_region_switch(self) -> wcc.RadioItems:
        return wcc.RadioItems(
            id={
                "id": self.get_unique_id().to_string(),
                "element": "region-selector",
                "wrapper": "region-selector",
            },
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
            id={
                "id": self.get_unique_id().to_string(),
                "wrapper": "REAL",
                "type": "REAL",
            },
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
                            id={
                                "id": self.get_unique_id().to_string(),
                                "element": "real_text",
                            },
                            style={"margin-left": "10px"},
                            children=f"{min(reals)}-{max(reals)}",
                        ),
                    ],
                ),
                wcc.RadioItems(
                    id={
                        "id": self.get_unique_id().to_string(),
                        "element": "real-selector-option",
                    },
                    options=[
                        {"label": "Range", "value": "range"},
                        {"label": "Select", "value": "select"},
                    ],
                    value="range",
                    vertical=False,
                ),
                wcc.RangeSlider(
                    wrapper_id={
                        "id": self.get_unique_id().to_string(),
                        "element": "real-slider-wrapper",
                    },
                    id={
                        "id": self.get_unique_id().to_string(),
                        "component_type": "range",
                    },
                    value=[min(reals), max(reals)],
                    min=min(reals),
                    max=max(reals),
                    marks={str(i): {"label": str(i)} for i in [min(reals), max(reals)]},
                ),
                html.Div(
                    style={"display": "none"},
                    children=wcc.Select(
                        id={
                            "id": self.get_unique_id().to_string(),
                            "selector": "REAL",
                            "type": "REAL",
                        },
                        options=[{"label": i, "value": i} for i in reals],
                        value=reals,
                    ),
                ),
            ],
        )

    def fip_filter_dropdowns(self) -> html.Div:
        dropdowns: List[html.Div] = []
        if self.disjoint_set_df is not None:
            for selector in ["FIPNUM", "SET"]:
                elements = list(self.disjoint_set_df[selector].unique())
                if selector == "FIPNUM":
                    elements = sorted(elements, key=int)
                dropdowns.append(
                    html.Div(
                        id={
                            "id": self.get_unique_id().to_string(),
                            "wrapper": selector,
                            "type": "undef",
                        },
                        children=wcc.SelectWithLabel(
                            label=selector.lower().capitalize(),
                            id={
                                "id": self.get_unique_id().to_string(),
                                "selector": selector,
                                "type": "undef",
                            },
                            options=[{"label": i, "value": i} for i in elements],
                            value=elements,
                            multi=True,
                            size=min(15, len(elements)),
                        ),
                    )
                )
        return html.Div(dropdowns)
