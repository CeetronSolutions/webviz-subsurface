from typing import Callable, Dict, List, Optional, Tuple
from pathlib import Path

import pandas as pd
from tables import Filters
from dash import ALL, Input, Output, State, callback, callback_context, no_update
from dash.exceptions import PreventUpdate
from webviz_config import WebvizPluginABC, WebvizSettings
from webviz_config.common_cache import CACHE
from webviz_config.webviz_assets import WEBVIZ_ASSETS
from webviz_config.webviz_store import webvizstore

import webviz_subsurface
from webviz_subsurface._models import (
    EnsembleSetModel,
    InplaceVolumesModel,
    caching_ensemble_set_model_factory,
)
from webviz_subsurface._models.inplace_volumes_model import extract_volumes
from .shared_settings import PlotControls, Filters, Settings

from .views import (
    InplaceDistributionsCustomPlotting,
    InplaceDistributionsPlotsPerZoneRegion,
    InplaceDistributionsConvergencePlot,
    Tables,
    TornadoPlotsCustom,
    TornadoPlotsBulk,
    SensitivityComparison,
    SourceComparison,
    EnsembleComparison,
    FipFile,
)

from ._layout_elements import ElementIds
from .business_logic.volume_validator_and_combinator import VolumeValidatorAndCombinator


class VolumetricAnalysisRefactored(WebvizPluginABC):
    def __init__(
        self,
        webviz_settings: WebvizSettings,
        csv_file_volumes: Path = None,
        csv_file_parameters: Path = None,
        ensembles: list = None,
        volumes_files: dict = None,
        volumes_folder: str = "share/results/volumes",
        non_net_facies: Optional[List[str]] = None,
        fip_file: Path = None,
    ):
        super().__init__(stretch=True)

        WEBVIZ_ASSETS.add(
            Path(webviz_subsurface.__file__).parent
            / "_assets"
            / "css"
            / "inplace_volumes.css"
        )

        self.csvfile_vol = csv_file_volumes
        self.csvfile_parameters = csv_file_parameters
        self.fip_file = fip_file

        if csv_file_volumes:
            volumes_table = read_csv(csv_file_volumes)
            parameters: Optional[pd.DataFrame] = (
                read_csv(csv_file_parameters) if csv_file_parameters else None
            )

        elif ensembles and volumes_files:
            ensemble_paths = {
                ens: webviz_settings.shared_settings["scratch_ensembles"][ens]
                for ens in ensembles
            }
            self.emodel: EnsembleSetModel = (
                caching_ensemble_set_model_factory.get_or_create_model(
                    ensemble_paths=ensemble_paths,
                )
            )
            parameters = self.emodel.load_parameters()
            volumes_table = extract_volumes(self.emodel, volumes_folder, volumes_files)

        else:
            raise ValueError(
                'Incorrent arguments. Either provide a "csvfile_vol" or "ensembles" and "volfiles"'
            )

        vcomb = VolumeValidatorAndCombinator(
            volumes_table=volumes_table,
            fipfile=get_path(self.fip_file) if self.fip_file else None,
        )
        self.disjoint_set_df = vcomb.disjoint_set_df
        self.volumes_model = InplaceVolumesModel(
            volumes_table=vcomb.dframe,
            parameter_table=parameters,
            non_net_facies=non_net_facies,
            volume_type=vcomb.volume_type,
        )
        self.theme = webviz_settings.theme

        # Stores

        self.add_store("selections", WebvizPluginABC.StorageType.SESSION)
        self.add_store("initial-load-info", WebvizPluginABC.StorageType.MEMORY)

        # Inplace distributions views

        self.add_view(
            InplaceDistributionsCustomPlotting(self.volumes_model),
            ElementIds.InplaceDistributions.CustomPlotting.ID,
            "Inplace distributions",
        )

        self.add_view(
            InplaceDistributionsPlotsPerZoneRegion(self.volumes_model),
            ElementIds.InplaceDistributions.PlotsPerZoneRegion.ID,
            "Inplace distributions",
        )

        self.add_view(
            InplaceDistributionsConvergencePlot(self.volumes_model),
            ElementIds.InplaceDistributions.ConvergencePlot.ID,
            "Inplace distributions",
        )

        self.add_shared_settings_group(
            PlotControls(self.volumes_model),
            ElementIds.InplaceDistributions.Settings.PlotControls.ID,
            visible_in_views=[
                self.view(ElementIds.InplaceDistributions.CustomPlotting.ID)
                .get_uuid()
                .to_string(),
                self.view(ElementIds.InplaceDistributions.PlotsPerZoneRegion.ID)
                .get_uuid()
                .to_string(),
                self.view(ElementIds.InplaceDistributions.ConvergencePlot.ID)
                .get_uuid()
                .to_string(),
            ],
        )

        self.add_shared_settings_group(
            Settings(self.volumes_model, self.theme),
            ElementIds.InplaceDistributions.Settings.Settings.ID,
            visible_in_views=[
                self.view(ElementIds.InplaceDistributions.CustomPlotting.ID)
                .get_uuid()
                .to_string(),
                self.view(ElementIds.InplaceDistributions.PlotsPerZoneRegion.ID)
                .get_uuid()
                .to_string(),
                self.view(ElementIds.InplaceDistributions.ConvergencePlot.ID)
                .get_uuid()
                .to_string(),
            ],
        )

        self.add_shared_settings_group(
            Filters(self.volumes_model),
            ElementIds.InplaceDistributions.Settings.Filters.ID,
        )

        self.add_view(Tables(self.volumes_model), ElementIds.Tables.ID)

        if self.volumes_model.sensrun:
            self.add_view(
                TornadoPlotsCustom(), ElementIds.TornadoPlots.Custom.ID, "Tornadoplots"
            )

        if self.volumes_model.sensrun:
            self.add_view(
                TornadoPlotsBulk(),
                ElementIds.TornadoPlots.BulkVsStoiipGiip.ID,
                "Tornadoplots",
            )

        if len(self.volumes_model.sources) > 1:
            self.add_view(SourceComparison(), "SourceComparison")

        if len(self.volumes_model.ensembles) > 1 or self.volumes_model.sensrun:
            if len(self.volumes_model.ensembles) > 1:
                self.add_view(EnsembleComparison(), "EnsembleComparison")
            else:
                self.add_view(SensitivityComparison(), "SensitivityComparison")

        if self.disjoint_set_df:
            self.add_view(FipFile(), "FipFile")

    def _set_callbacks(self) -> None:
        @callback(
            Output(self.get_store_uuid("selections"), "data"),
            Input(
                {
                    "id": self.shared_settings_group(
                        ElementIds.InplaceDistributions.Settings.PlotControls.ID
                    )
                    .get_uuid()
                    .to_string(),
                    "selector": ALL,
                },
                "value",
            ),
            Input(
                {
                    "id": self.shared_settings_group(
                        ElementIds.InplaceDistributions.Settings.Settings.ID
                    )
                    .get_uuid()
                    .to_string(),
                    "selector": ALL,
                },
                "value",
            ),
            Input(
                {
                    "id": self.shared_settings_group(
                        ElementIds.InplaceDistributions.Settings.Filters.ID
                    )
                    .get_uuid()
                    .to_string(),
                    "selector": ALL,
                    "type": ALL,
                },
                "value",
            ),
            Input(
                {
                    "id": self.shared_settings_group(
                        ElementIds.InplaceDistributions.Settings.Settings.ID
                    )
                    .get_uuid()
                    .to_string(),
                    "settings": "Colorscale",
                },
                "colorscale",
            ),
            Input(self.get_store_uuid("initial-load-info"), "data"),
            Input("webviz-content-manager", "activeViewId"),
            State(self.get_store_uuid("selections"), "data"),
            State(
                {
                    "id": self.shared_settings_group(
                        ElementIds.InplaceDistributions.Settings.PlotControls.ID
                    )
                    .get_uuid()
                    .to_string(),
                    "selector": ALL,
                },
                "id",
            ),
            State(
                {
                    "id": self.shared_settings_group(
                        ElementIds.InplaceDistributions.Settings.Settings.ID
                    )
                    .get_uuid()
                    .to_string(),
                    "selector": ALL,
                },
                "id",
            ),
            State(
                {
                    "id": self.shared_settings_group(
                        ElementIds.InplaceDistributions.Settings.Filters.ID
                    )
                    .get_uuid()
                    .to_string(),
                    "selector": ALL,
                    "type": ALL,
                },
                "id",
            ),
        )
        def _update_selections(
            selectors: list,
            settings: list,
            filters: list,
            colorscale: str,
            initial_load: dict,
            selected_view: str,
            previous_selection: dict,
            selector_ids: list,
            settings_ids: list,
            filter_ids: list,
        ) -> dict:
            ctx = callback_context.triggered[0]
            if ctx["prop_id"] == ".":
                raise PreventUpdate

            if previous_selection is None:
                previous_selection = {}

            page_selections = {
                id_value["selector"]: values
                for id_value, values in zip(
                    selector_ids + settings_ids, selectors + settings
                )
            }
            page_selections["filters"] = {
                id_value["selector"]: values
                for id_value, values in zip(filter_ids, filters)
            }

            page_selections.update(Colorscale=colorscale if colorscale else None)
            page_selections.update(ctx_clicked=ctx["prop_id"])

            # check if a page needs to be updated due to page refresh or
            # change in selections/filters
            if initial_load[selected_view] or len(previous_selection) == 0:
                page_selections.update(update=True)
            else:
                equal_list = []
                for selector, values in page_selections.items():
                    if selector != "ctx_clicked":
                        equal_list.append(values == previous_selection[selector])
                page_selections.update(update=not all(equal_list))

            previous_selection = page_selections
            return previous_selection

        @callback(
            Output(self.get_store_uuid("initial-load-info"), "data"),
            Input("webviz-content-manager", "activeViewId"),
            Input(
                {
                    "id": self.shared_settings_group(
                        ElementIds.InplaceDistributions.Settings.PlotControls.ID
                    )
                    .get_uuid()
                    .to_string(),
                    "selector": ALL,
                },
                "value",
            ),
            Input(
                {
                    "id": self.shared_settings_group(
                        ElementIds.InplaceDistributions.Settings.Settings.ID
                    )
                    .get_uuid()
                    .to_string(),
                    "selector": ALL,
                },
                "value",
            ),
            Input(
                {
                    "id": self.shared_settings_group(
                        ElementIds.InplaceDistributions.Settings.Filters.ID
                    )
                    .get_uuid()
                    .to_string(),
                    "selector": ALL,
                    "type": ALL,
                },
                "value",
            ),
            State(self.get_store_uuid("initial-load-info"), "data"),
        )
        def _store_initial_load_info(
            page_selected: str,
            _selectors_changed: list,
            _settings_changed: list,
            _filters_changed: list,
            initial_load: dict,
        ) -> Dict[str, bool]:
            """
            Store info (True/False) reagarding if a page is initally loaded.
            Updating filters or selectors will set the value to False
            """
            if initial_load is None:
                initial_load = {}
            initial_load[page_selected] = page_selected not in initial_load
            return initial_load


@CACHE.memoize(timeout=CACHE.TIMEOUT)
@webvizstore
def read_csv(csv_file: Path) -> pd.DataFrame:
    return pd.read_csv(csv_file)


@webvizstore
def get_path(path: Path) -> Path:
    return Path(path)
