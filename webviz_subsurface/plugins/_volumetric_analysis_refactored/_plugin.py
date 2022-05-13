from typing import List, Optional
from pathlib import Path

import pandas as pd
from tables import Filters
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
from .shared_settings import Filters
from .views.inplace_distributions.shared_settings import (
    PlotControls,
    Settings as InplaceDistributionsSettings,
)
from .views.tornado_plots.shared_settings import (
    TornadoControls,
    Settings as TornadoSettings,
)

from .views import (
    InplaceDistributionsCustomPlotting,
    InplaceDistributionsPlotsPerZoneRegion,
    InplaceDistributionsConvergencePlot,
    Tables,
    TornadoPlotsCustom,
    TornadoPlotsBulk,
)

from .views.comparison import (
    DiffTableMultipleResponses,
    DiffTableSelectedResponse,
    QCPlots,
)

from .views.fip_file import (
    FipFileQCPlots
)

from .views.comparison.shared_settings import Controls, Settings as ComparisonSettings

from ._layout_elements import ElementIds
from .business_logic.volume_validator_and_combinator import VolumeValidatorAndCombinator

from ._callbacks import set_plugin_callbacks


class VolumetricAnalysisRefactored(WebvizPluginABC):
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-statements
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

        self.add_store(ElementIds.Stores.FILTERS, WebvizPluginABC.StorageType.SESSION)
        self.add_store(
            ElementIds.Stores.INPLACE_DISTRIBUTIONS, WebvizPluginABC.StorageType.SESSION
        )
        self.add_store(ElementIds.Stores.TABLES, WebvizPluginABC.StorageType.SESSION)
        self.add_store(
            ElementIds.Stores.TORNADO_PLOTS, WebvizPluginABC.StorageType.SESSION
        )

        # Inplace distributions views

        self.add_view(
            InplaceDistributionsCustomPlotting(self.volumes_model),
            ElementIds.InplaceDistributions.CustomPlotting.ID,
            ElementIds.InplaceDistributions.NAME,
        )

        self.add_view(
            InplaceDistributionsPlotsPerZoneRegion(self.volumes_model),
            ElementIds.InplaceDistributions.PlotsPerZoneRegion.ID,
            ElementIds.InplaceDistributions.NAME,
        )

        self.add_view(
            InplaceDistributionsConvergencePlot(self.volumes_model),
            ElementIds.InplaceDistributions.ConvergencePlot.ID,
            ElementIds.InplaceDistributions.NAME,
        )

        self.add_shared_settings_group(
            Filters(self.volumes_model, self.disjoint_set_df),
            ElementIds.SharedSettings.Filters.ID,
        )

        self.add_shared_settings_group(
            PlotControls(self.volumes_model),
            ElementIds.InplaceDistributions.Settings.PlotControls.ID,
            visible_in_views=[
                self.view(ElementIds.InplaceDistributions.CustomPlotting.ID)
                .get_unique_id()
                .to_string(),
                self.view(ElementIds.InplaceDistributions.PlotsPerZoneRegion.ID)
                .get_unique_id()
                .to_string(),
                self.view(ElementIds.InplaceDistributions.ConvergencePlot.ID)
                .get_unique_id()
                .to_string(),
            ],
        )

        self.add_shared_settings_group(
            InplaceDistributionsSettings(self.volumes_model, self.theme),
            ElementIds.InplaceDistributions.Settings.Settings.ID,
            visible_in_views=[
                self.view(ElementIds.InplaceDistributions.CustomPlotting.ID)
                .get_unique_id()
                .to_string(),
                self.view(ElementIds.InplaceDistributions.PlotsPerZoneRegion.ID)
                .get_unique_id()
                .to_string(),
                self.view(ElementIds.InplaceDistributions.ConvergencePlot.ID)
                .get_unique_id()
                .to_string(),
            ],
        )

        self.add_view(Tables(self.volumes_model), ElementIds.Tables.ID)

        if self.volumes_model.sensrun:
            self.add_view(
                TornadoPlotsCustom(volumes_model=self.volumes_model, theme=self.theme),
                ElementIds.TornadoPlots.Custom.ID,
                ElementIds.TornadoPlots.NAME,
            )
            self.add_view(
                TornadoPlotsBulk(self.volumes_model, self.theme),
                ElementIds.TornadoPlots.BulkVsStoiipGiip.ID,
                ElementIds.TornadoPlots.NAME,
            )

            self.add_shared_settings_group(
                TornadoControls(self.volumes_model),
                ElementIds.TornadoPlots.Settings.TornadoControls.ID,
                visible_in_views=[
                    self.view(ElementIds.TornadoPlots.Custom.ID)
                    .get_unique_id()
                    .to_string(),
                    self.view(ElementIds.TornadoPlots.BulkVsStoiipGiip.ID)
                    .get_unique_id()
                    .to_string(),
                ],
            )

            self.add_shared_settings_group(
                TornadoSettings(self.volumes_model),
                ElementIds.TornadoPlots.Settings.Settings.ID,
                visible_in_views=[
                    self.view(ElementIds.TornadoPlots.Custom.ID)
                    .get_unique_id()
                    .to_string(),
                    self.view(ElementIds.TornadoPlots.BulkVsStoiipGiip.ID)
                    .get_unique_id()
                    .to_string(),
                ],
            )

        if len(self.volumes_model.sources) > 1:
            self.add_store(
                ElementIds.Comparison.SourceComparison.ID,
                WebvizPluginABC.StorageType.SESSION,
            )

            self.add_view(
                QCPlots(compare_on="Source", volumes_model=self.volumes_model),
                f"{ElementIds.Comparison.SourceComparison.ID}-{ElementIds.Comparison.QCPlots.ID}",
                ElementIds.Comparison.SourceComparison.NAME,
            )
            self.add_view(
                DiffTableSelectedResponse(
                    compare_on="Source", volumes_model=self.volumes_model
                ),
                f"{ElementIds.Comparison.SourceComparison.ID}"
                f"-{ElementIds.Comparison.DiffTableSelectedResponse.ID}",
                ElementIds.Comparison.SourceComparison.NAME,
            )
            self.add_view(
                DiffTableMultipleResponses(
                    compare_on="Source", volumes_model=self.volumes_model
                ),
                f"{ElementIds.Comparison.SourceComparison.ID}"
                f"-{ElementIds.Comparison.DiffTableMultipleResponses.ID}",
                ElementIds.Comparison.SourceComparison.NAME,
            )

            self.add_shared_settings_group(
                Controls(compare_on="Source", volumes_model=self.volumes_model),
                f"{ElementIds.Comparison.SourceComparison.ID}"
                f"-{ElementIds.Comparison.Settings.Controls.ID}",
                visible_in_views=[
                    self.view(
                        f"{ElementIds.Comparison.SourceComparison.ID}"
                        f"-{ElementIds.Comparison.QCPlots.ID}"
                    )
                    .get_unique_id()
                    .to_string(),
                    self.view(
                        f"{ElementIds.Comparison.SourceComparison.ID}"
                        f"-{ElementIds.Comparison.DiffTableSelectedResponse.ID}"
                    )
                    .get_unique_id()
                    .to_string(),
                    self.view(
                        f"{ElementIds.Comparison.SourceComparison.ID}"
                        f"-{ElementIds.Comparison.DiffTableMultipleResponses.ID}"
                    )
                    .get_unique_id()
                    .to_string(),
                ],
            )

            self.add_shared_settings_group(
                ComparisonSettings(),
                f"{ElementIds.Comparison.SourceComparison.ID}"
                f"-{ElementIds.Comparison.Settings.Settings.ID}",
                visible_in_views=[
                    self.view(
                        f"{ElementIds.Comparison.SourceComparison.ID}"
                        f"-{ElementIds.Comparison.QCPlots.ID}"
                    )
                    .get_unique_id()
                    .to_string(),
                    self.view(
                        f"{ElementIds.Comparison.SourceComparison.ID}"
                        f"-{ElementIds.Comparison.DiffTableSelectedResponse.ID}"
                    )
                    .get_unique_id()
                    .to_string(),
                    self.view(
                        f"{ElementIds.Comparison.SourceComparison.ID}"
                        f"-{ElementIds.Comparison.DiffTableMultipleResponses.ID}"
                    )
                    .get_unique_id()
                    .to_string(),
                ],
            )

        if len(self.volumes_model.ensembles) > 1 or self.volumes_model.sensrun:
            if len(self.volumes_model.ensembles) > 1:
                self.add_store(
                    ElementIds.Comparison.EnsembleComparison.ID,
                    WebvizPluginABC.StorageType.SESSION,
                )

                self.add_view(
                    QCPlots(compare_on="Ensemble", volumes_model=self.volumes_model),
                    f"{ElementIds.Comparison.EnsembleComparison.ID}"
                    f"-{ElementIds.Comparison.QCPlots.ID}",
                    ElementIds.Comparison.EnsembleComparison.NAME,
                )
                self.add_view(
                    DiffTableSelectedResponse(
                        compare_on="Ensemble", volumes_model=self.volumes_model
                    ),
                    f"{ElementIds.Comparison.EnsembleComparison.ID}"
                    f"-{ElementIds.Comparison.DiffTableSelectedResponse.ID}",
                    ElementIds.Comparison.EnsembleComparison.NAME,
                )
                self.add_view(
                    DiffTableMultipleResponses(
                        compare_on="Ensemble", volumes_model=self.volumes_model
                    ),
                    f"{ElementIds.Comparison.EnsembleComparison.ID}"
                    f"-{ElementIds.Comparison.DiffTableMultipleResponses.ID}",
                    ElementIds.Comparison.EnsembleComparison.NAME,
                )

                self.add_shared_settings_group(
                    Controls(compare_on="Ensemble", volumes_model=self.volumes_model),
                    f"{ElementIds.Comparison.EnsembleComparison.ID}"
                    f"-{ElementIds.Comparison.Settings.Controls.ID}",
                    visible_in_views=[
                        self.view(
                            f"{ElementIds.Comparison.EnsembleComparison.ID}"
                            f"-{ElementIds.Comparison.QCPlots.ID}"
                        )
                        .get_unique_id()
                        .to_string(),
                        self.view(
                            f"{ElementIds.Comparison.EnsembleComparison.ID}"
                            f"-{ElementIds.Comparison.DiffTableSelectedResponse.ID}"
                        )
                        .get_unique_id()
                        .to_string(),
                        self.view(
                            f"{ElementIds.Comparison.EnsembleComparison.ID}"
                            f"-{ElementIds.Comparison.DiffTableMultipleResponses.ID}"
                        )
                        .get_unique_id()
                        .to_string(),
                    ],
                )

                self.add_shared_settings_group(
                    ComparisonSettings(),
                    f"{ElementIds.Comparison.EnsembleComparison.ID}"
                    f"-{ElementIds.Comparison.Settings.Settings.ID}",
                    visible_in_views=[
                        self.view(
                            f"{ElementIds.Comparison.EnsembleComparison.ID}"
                            f"-{ElementIds.Comparison.QCPlots.ID}"
                        )
                        .get_unique_id()
                        .to_string(),
                        self.view(
                            f"{ElementIds.Comparison.EnsembleComparison.ID}"
                            f"-{ElementIds.Comparison.DiffTableSelectedResponse.ID}"
                        )
                        .get_unique_id()
                        .to_string(),
                        self.view(
                            f"{ElementIds.Comparison.EnsembleComparison.ID}"
                            f"-{ElementIds.Comparison.DiffTableMultipleResponses.ID}"
                        )
                        .get_unique_id()
                        .to_string(),
                    ],
                )
            else:
                self.add_store(
                    ElementIds.Comparison.SensitivityComparison.ID,
                    WebvizPluginABC.StorageType.SESSION,
                )

                self.add_view(
                    QCPlots(compare_on="Sensitivity", volumes_model=self.volumes_model),
                    f"{ElementIds.Comparison.SensitivityComparison.ID}"
                    f"-{ElementIds.Comparison.QCPlots.ID}",
                    ElementIds.Comparison.SensitivityComparison.NAME,
                )
                self.add_view(
                    DiffTableSelectedResponse(
                        compare_on="Sensitivity", volumes_model=self.volumes_model
                    ),
                    f"{ElementIds.Comparison.SensitivityComparison.ID}"
                    f"-{ElementIds.Comparison.DiffTableSelectedResponse.ID}",
                    ElementIds.Comparison.SensitivityComparison.NAME,
                )
                self.add_view(
                    DiffTableMultipleResponses(
                        compare_on="Sensitivity", volumes_model=self.volumes_model
                    ),
                    f"{ElementIds.Comparison.SensitivityComparison.ID}"
                    f"-{ElementIds.Comparison.DiffTableMultipleResponses.ID}",
                    ElementIds.Comparison.SensitivityComparison.NAME,
                )

                self.add_shared_settings_group(
                    Controls(
                        compare_on="Sensitivity", volumes_model=self.volumes_model
                    ),
                    f"{ElementIds.Comparison.SensitivityComparison.ID}"
                    f"-{ElementIds.Comparison.Settings.Controls.ID}",
                    visible_in_views=[
                        self.view(
                            f"{ElementIds.Comparison.SensitivityComparison.ID}"
                            f"-{ElementIds.Comparison.QCPlots.ID}"
                        )
                        .get_unique_id()
                        .to_string(),
                        self.view(
                            f"{ElementIds.Comparison.SensitivityComparison.ID}"
                            f"-{ElementIds.Comparison.DiffTableSelectedResponse.ID}"
                        )
                        .get_unique_id()
                        .to_string(),
                        self.view(
                            f"{ElementIds.Comparison.SensitivityComparison.ID}"
                            f"-{ElementIds.Comparison.DiffTableMultipleResponses.ID}"
                        )
                        .get_unique_id()
                        .to_string(),
                    ],
                )

                self.add_shared_settings_group(
                    ComparisonSettings(),
                    f"{ElementIds.Comparison.SensitivityComparison.ID}"
                    f"-{ElementIds.Comparison.Settings.Settings.ID}",
                    visible_in_views=[
                        self.view(
                            f"{ElementIds.Comparison.SensitivityComparison.ID}"
                            f"-{ElementIds.Comparison.QCPlots.ID}"
                        )
                        .get_unique_id()
                        .to_string(),
                        self.view(
                            f"{ElementIds.Comparison.SensitivityComparison.ID}"
                            f"-{ElementIds.Comparison.DiffTableSelectedResponse.ID}"
                        )
                        .get_unique_id()
                        .to_string(),
                        self.view(
                            f"{ElementIds.Comparison.SensitivityComparison.ID}"
                            f"-{ElementIds.Comparison.DiffTableMultipleResponses.ID}"
                        )
                        .get_unique_id()
                        .to_string(),
                    ],
                )

        if self.disjoint_set_df is not None:
            self.add_view(FipFileQCPlots(self.disjoint_set_df), ElementIds.FipFile.QCPlots.ID, ElementIds.FipFile.NAME)

    def _set_callbacks(self) -> None:
        set_plugin_callbacks(self, self.volumes_model)


@CACHE.memoize(timeout=CACHE.TIMEOUT)
@webvizstore
def read_csv(csv_file: Path) -> pd.DataFrame:
    return pd.read_csv(csv_file)


@webvizstore
def get_path(path: Path) -> Path:
    return Path(path)
