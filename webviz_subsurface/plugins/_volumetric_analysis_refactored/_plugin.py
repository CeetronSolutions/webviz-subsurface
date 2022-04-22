from typing import Callable, List, Optional, Tuple
from pathlib import Path

import pandas as pd
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

from .views import InplaceDistributions, Tables, TornadoPlots, SensitivityComparison, SourceComparison, EnsembleComparison, FipFile
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
        super().__init__()

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

        self.add_view(InplaceDistributions(), "InplaceDistributions")
        self.add_view(Tables(), "Tables")

        if self.volumes_model.sensrun:
            self.add_view(TornadoPlots(), "TornadoPlots")

        if len(self.volumes_model.sources) > 1:
            self.add_view(SourceComparison(), "SourceComparison")

        if len(self.volumes_model.ensembles) > 1 or self.volumes_model.sensrun:
            if len(self.volumes_model.ensembles) > 1:
                self.add_view(EnsembleComparison(), "EnsembleComparison")
            else:
                self.add_view(SensitivityComparison(), "SensitivityComparison")

        if self.disjoint_set_df:
            self.add_view(FipFile(), "FipFile")

@CACHE.memoize(timeout=CACHE.TIMEOUT)
@webvizstore
def read_csv(csv_file: Path) -> pd.DataFrame:
    return pd.read_csv(csv_file)

@webvizstore
def get_path(path: Path) -> Path:
    return Path(path)



