from typing import Dict, Optional, Literal
from pathlib import Path
import os
import hashlib
import json
from enum import Enum
import logging

import pandas as pd
from fmu.ensemble import ScratchEnsemble

from webviz_config.webviz_factory_registry import WEBVIZ_FACTORY_REGISTRY
from webviz_config.webviz_factory import WebvizFactory
from webviz_config.webviz_instance_info import WebvizRunMode

from .ensemble_summary_provider import EnsembleSummaryProvider
from .ensemble_summary_provider_set import EnsembleSummaryProviderSet
from .ensemble_summary_provider_impl_arrow import EnsembleSummaryProviderImplArrow
from .ensemble_summary_provider_impl_parquet import EnsembleSummaryProviderImplParquet
from .ensemble_summary_provider_impl_inmem_parquet import (
    EnsembleSummaryProviderImplInMemParquet,
)
from .._utils.perf_timer import PerfTimer

from .ensemble_summary_provider_experiments import (
    load_per_realization_smry_tables_using_smry2arrow,
    resample_per_real_tables,
    Frequency,
)
from .ensemble_summary_provider_impl_LAZY_arrow import (
    EnsembleSummaryProviderImplLAZYArrow,
)


class BackingType(Enum):
    ARROW = 1
    PARQUET = 2
    INMEM_PARQUET = 3


LOGGER = logging.getLogger(__name__)


# =============================================================================
class EnsembleSummaryProviderFactory(WebvizFactory):

    # -------------------------------------------------------------------------
    def __init__(self, root_storage_folder: Path, pref_df_backing: BackingType) -> None:
        self._storage_dir = Path(root_storage_folder) / __name__
        self._pref_df_backing: BackingType = pref_df_backing
        self._allow_storage_writes = True

        LOGGER.info(
            f"EnsembleSummaryProviderFactory init: storage_dir={self._storage_dir}"
        )
        LOGGER.info(
            f"EnsembleSummaryProviderFactory init: pref_df_backing={repr(self._pref_df_backing)}"
        )

        if self._allow_storage_writes:
            os.makedirs(self._storage_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    @staticmethod
    def instance() -> "EnsembleSummaryProviderFactory":
        factory = WEBVIZ_FACTORY_REGISTRY.get_factory(EnsembleSummaryProviderFactory)
        if not factory:
            app_instance_info = WEBVIZ_FACTORY_REGISTRY.app_instance_info
            storage_folder = app_instance_info.storage_folder

            factory = EnsembleSummaryProviderFactory(storage_folder, BackingType.ARROW)

            # Store the factory object in the registry
            WEBVIZ_FACTORY_REGISTRY.set_factory(EnsembleSummaryProviderFactory, factory)

        return factory

    # -------------------------------------------------------------------------
    def create_provider_set_from_aggregated_csv_file(
        self,
        aggr_csv_file: Path,
    ) -> EnsembleSummaryProviderSet:

        LOGGER.info(
            f"create_provider_set_from_aggregated_csv_file() starting - {aggr_csv_file}"
        )
        timer = PerfTimer()

        main_storage_key = f"aggr_csv__{_make_hash_string(str(aggr_csv_file))}"

        # Since our only input is the file name of a single aggregated CSV file, we rely
        # on reading the dict which maps from ensemble names to the keys that need to
        # be loaded from a JSON file on disk.
        storage_keys_to_load: Dict[str, str] = {}
        json_filename = self._storage_dir / (main_storage_key + ".json")
        try:
            with open(json_filename, "r") as file:
                storage_keys_to_load = json.load(file)
        except FileNotFoundError:
            # No dict found on disk. We can only recover from this if we're allowed to
            # write to storage. In that case we'll import the CSV file and write the
            # resulting dict to JSON further down
            if not self._allow_storage_writes:
                raise

        # Possibly do import of CSV and writing of provider data to backing store
        if not storage_keys_to_load and self._allow_storage_writes:
            aggregated_df = pd.read_csv(aggr_csv_file)
            ensemble_names = aggregated_df["ENSEMBLE"].unique()

            LOGGER.info(
                f"Saving {len(ensemble_names)} "
                f"summary providers from aggregated CSV to backing store"
            )

            for ens_name in ensemble_names:
                storage_key = main_storage_key + "__" + ens_name
                ensemble_df = aggregated_df[aggregated_df["ENSEMBLE"] == ens_name]
                self._write_df_to_pref_df_backing(storage_key, ensemble_df.copy())
                storage_keys_to_load[ens_name] = storage_key

            with open(json_filename, "w") as file:
                json.dump(storage_keys_to_load, file)

        created_providers: Dict[str, EnsembleSummaryProvider] = {}
        for ens_name, storage_key in storage_keys_to_load.items():
            provider = self._create_provider_instance_from_pref_df_backing(storage_key)
            if provider:
                created_providers[ens_name] = provider

        num_missing_models = len(storage_keys_to_load) - len(created_providers)
        if num_missing_models > 0:
            raise ValueError(f"Failed to load data for {num_missing_models} ensembles")

        LOGGER.info(f"Loaded {len(created_providers)} providers from backing store")

        LOGGER.info(
            f"create_provider_set_from_aggregated_csv_file() finished "
            f"- total time: {timer.elapsed_s():.2f}s"
        )

        return EnsembleSummaryProviderSet(created_providers)

    # -------------------------------------------------------------------------
    def create_provider_set_from_per_realization_csv_file(
        self, ensembles: Dict[str, str], csv_file_rel_path: str
    ) -> EnsembleSummaryProviderSet:

        LOGGER.info(
            f"create_provider_set_from_per_realization_csv_file() starting - {csv_file_rel_path}"
        )
        timer = PerfTimer()

        created_providers: Dict[str, EnsembleSummaryProvider] = {}
        missing_storage_keys: Dict[str, str] = {}

        # Try and create/load providers from backing store
        for ens_name, ens_path in ensembles.items():
            storage_key = f"ens_csv__{_make_hash_string(ens_path + csv_file_rel_path)}"
            provider = self._create_provider_instance_from_pref_df_backing(storage_key)
            if provider:
                created_providers[ens_name] = provider
                LOGGER.info(
                    f"Loaded summary provider for {ens_name} from backing store"
                )
            else:
                missing_storage_keys[ens_name] = storage_key

        # If there are remaining keys AND we're allowed to write to storage, we'll load
        # the CSV/SMRY data, write data to storage and then try and load again
        if missing_storage_keys and self._allow_storage_writes:
            for ens_name, storage_key in dict(missing_storage_keys).items():
                LOGGER.info(
                    f"Importing/saving CSV summary data for ensemble: {ens_name}"
                )
                timer.lap_s()

                ens_path = ensembles[ens_name]
                scratch_ensemble = ScratchEnsemble(
                    ens_name, ens_path, autodiscovery=True
                )
                et_create_scratch_ens_s = timer.lap_s()

                ensemble_df = scratch_ensemble.load_csv(csv_file_rel_path)
                et_load_csv_s = timer.lap_s()

                self._write_df_to_pref_df_backing(storage_key, ensemble_df)
                et_write_s = timer.lap_s()

                provider = self._create_provider_instance_from_pref_df_backing(
                    storage_key
                )
                if provider:
                    created_providers[ens_name] = provider
                    del missing_storage_keys[ens_name]
                    LOGGER.info(
                        f"Saved summary provider for {ens_name} to backing store ("
                        f"create_scratch_ens={et_create_scratch_ens_s:.2f}s, "
                        f"load_csv={et_load_csv_s:.2f}s, "
                        f"write={et_write_s:.2f}s)"
                    )

        if missing_storage_keys:
            raise ValueError(
                f"Failed to load/create provider(s) for {len(missing_storage_keys)} ensembles"
            )

        LOGGER.info(
            f"create_provider_set_from_per_realization_csv_file() finished "
            f"- total time: {timer.elapsed_s():.2f}s"
        )

        return EnsembleSummaryProviderSet(created_providers)

    # -------------------------------------------------------------------------
    def create_provider_set_from_ensemble_smry_fmu(
        self, ensembles: Dict[str, str], time_index: str
    ) -> EnsembleSummaryProviderSet:

        LOGGER.info("create_provider_set_from_ensemble_smry_fmu() starting...")
        timer = PerfTimer()

        created_providers: Dict[str, EnsembleSummaryProvider] = {}
        missing_storage_keys: Dict[str, str] = {}

        # Try and create/load from backing store
        for ens_name, ens_path in ensembles.items():
            ens_storage_key = f"ens_smry__{_make_hash_string(ens_path)}__{time_index}"
            provider = self._create_provider_instance_from_pref_df_backing(
                ens_storage_key
            )
            if provider:
                created_providers[ens_name] = provider
                LOGGER.info(
                    f"Loaded summary provider for {ens_name} from backing store"
                )
            else:
                missing_storage_keys[ens_name] = ens_storage_key

        # If there are remaining keys to create, we'll load the smry data using
        # FMU, write the data to storage and then try and load again
        if missing_storage_keys and self._allow_storage_writes:
            for ens_name, ens_storage_key in dict(missing_storage_keys).items():
                LOGGER.info(f"Importing/saving summary data for ensemble: {ens_name}")
                timer.lap_s()

                ens_path = ensembles[ens_name]
                ensemble_df = _load_ensemble_smry_dataframe_using_fmu(
                    ens_path, time_index
                )
                et_import_smry_s = timer.lap_s()

                self._write_df_to_pref_df_backing(ens_storage_key, ensemble_df)
                et_write_s = timer.lap_s()

                provider = self._create_provider_instance_from_pref_df_backing(
                    ens_storage_key
                )
                if provider:
                    created_providers[ens_name] = provider
                    del missing_storage_keys[ens_name]
                    LOGGER.info(
                        f"Saved summary provider for {ens_name} to backing store ("
                        f"import_smry={et_import_smry_s:.2f}s, write={et_write_s:.2f}s)"
                    )

        # Should not be any keys missing
        if missing_storage_keys:
            raise ValueError(
                f"Failed to load/create provider(s) for {len(missing_storage_keys)} ensembles"
            )

        LOGGER.info(
            f"create_provider_set_from_ensemble_smry_fmu() finished "
            f"- total time: {timer.elapsed_s():.2f}s"
        )

        return EnsembleSummaryProviderSet(created_providers)

    # -------------------------------------------------------------------------
    def create_provider_set_PRESAMPLED_from_FAKE_per_realization_arrow_file(
        self,
        ensembles: Dict[str, str],
        sampling_frequency_str: Literal["daily", "weekly", "monthly", "yearly", "raw"],
    ) -> EnsembleSummaryProviderSet:

        LOGGER.info(
            "create_provider_set_PRESAMPLED_from_FAKE_per_realization_arrow_file() starting..."
        )
        timer = PerfTimer()

        frequency_enum: Optional[Frequency] = None
        if sampling_frequency_str is not "raw":
            frequency_enum = Frequency(sampling_frequency_str)

        created_providers: Dict[str, EnsembleSummaryProvider] = {}
        missing_storage_keys: Dict[str, str] = {}

        for ens_name, ens_path in ensembles.items():
            ens_storage_key = f"ens_concat_PRESAMPLED_{sampling_frequency_str}__{_make_hash_string(ens_path)}"
            provider = EnsembleSummaryProviderImplArrow.from_backing_store(
                self._storage_dir, ens_storage_key
            )
            if provider:
                created_providers[ens_name] = provider
                LOGGER.info(
                    f"Loaded summary provider for {ens_name} from backing store"
                )
            else:
                missing_storage_keys[ens_name] = ens_storage_key

        if missing_storage_keys and self._allow_storage_writes:
            for ens_name, ens_storage_key in dict(missing_storage_keys).items():
                LOGGER.info(f"Importing/saving summary data for ensemble: {ens_name}")
                timer.lap_s()

                ens_path = ensembles[ens_name]
                per_real_tables = load_per_realization_smry_tables_using_smry2arrow(
                    ens_path
                )
                et_import_smry_s = timer.lap_s()

                if frequency_enum is not None:
                    per_real_tables = resample_per_real_tables(
                        per_real_tables, frequency_enum
                    )
                et_resample_s = timer.lap_s()

                EnsembleSummaryProviderImplArrow.write_backing_store_from_per_realization_tables(
                    self._storage_dir, ens_storage_key, per_real_tables
                )
                et_write_s = timer.lap_s()

                provider = EnsembleSummaryProviderImplArrow.from_backing_store(
                    self._storage_dir, ens_storage_key
                )

                if provider:
                    created_providers[ens_name] = provider
                    del missing_storage_keys[ens_name]
                    LOGGER.info(
                        f"Saved summary provider for {ens_name} to backing store ("
                        f"import_smry={et_import_smry_s:.2f}s, resample={et_resample_s:.2f}s, write={et_write_s:.2f}s)"
                    )

        # Should not be any keys missing
        if missing_storage_keys:
            raise ValueError(
                f"Failed to load/create provider(s) for {len(missing_storage_keys)} ensembles"
            )

        LOGGER.info(
            f"create_provider_set_PRESAMPLED_from_FAKE_per_realization_arrow_file() finished "
            f"- total time: {timer.elapsed_s():.2f}s"
        )

        return EnsembleSummaryProviderSet(created_providers)

    # -------------------------------------------------------------------------
    def create_provider_set_LAZY_from_FAKE_per_realization_arrow_file(
        self,
        ensembles: Dict[str, str],
        report_frequency_str: Literal["daily", "weekly", "monthly", "yearly", "raw"],
    ) -> EnsembleSummaryProviderSet:

        LOGGER.info(
            "create_provider_set_LAZY_from_FAKE_per_realization_arrow_file() starting..."
        )
        timer = PerfTimer()

        frequency_enum: Optional[Frequency] = None
        if report_frequency_str is not "raw":
            frequency_enum = Frequency(report_frequency_str)

        created_providers: Dict[str, EnsembleSummaryProvider] = {}
        missing_storage_keys: Dict[str, str] = {}

        for ens_name, ens_path in ensembles.items():
            ens_storage_key = f"ens_concat_LAZY__{_make_hash_string(ens_path)}"
            provider = EnsembleSummaryProviderImplLAZYArrow.from_backing_store(
                self._storage_dir, ens_storage_key, frequency_enum
            )
            if provider:
                created_providers[ens_name] = provider
                LOGGER.info(
                    f"Loaded summary provider for {ens_name} from backing store"
                )
            else:
                missing_storage_keys[ens_name] = ens_storage_key

        if missing_storage_keys and self._allow_storage_writes:
            for ens_name, ens_storage_key in dict(missing_storage_keys).items():
                LOGGER.info(f"Importing/saving summary data for ensemble: {ens_name}")
                timer.lap_s()

                ens_path = ensembles[ens_name]
                per_real_tables = load_per_realization_smry_tables_using_smry2arrow(
                    ens_path
                )
                et_import_smry_s = timer.lap_s()

                EnsembleSummaryProviderImplLAZYArrow.write_backing_store_from_per_realization_tables(
                    self._storage_dir, ens_storage_key, per_real_tables
                )
                et_write_s = timer.lap_s()

                provider = EnsembleSummaryProviderImplLAZYArrow.from_backing_store(
                    self._storage_dir, ens_storage_key, frequency_enum
                )

                if provider:
                    created_providers[ens_name] = provider
                    del missing_storage_keys[ens_name]
                    LOGGER.info(
                        f"Saved summary provider for {ens_name} to backing store ("
                        f"import_smry={et_import_smry_s:.2f}s, write={et_write_s:.2f}s)"
                    )

        # Should not be any keys missing
        if missing_storage_keys:
            raise ValueError(
                f"Failed to load/create provider(s) for {len(missing_storage_keys)} ensembles"
            )

        LOGGER.info(
            f"create_provider_set_LAZY_from_FAKE_per_realization_arrow_file() finished "
            f"- total time: {timer.elapsed_s():.2f}s"
        )

        return EnsembleSummaryProviderSet(created_providers)

    # -------------------------------------------------------------------------
    # Simple solution for creating EnsembleSummaryProvider instances from backing store
    # based on the configured backing type.
    def _create_provider_instance_from_pref_df_backing(
        self, storage_key: str
    ) -> Optional[EnsembleSummaryProvider]:
        if self._pref_df_backing is BackingType.ARROW:
            return EnsembleSummaryProviderImplArrow.from_backing_store(
                self._storage_dir, storage_key
            )

        if self._pref_df_backing is BackingType.PARQUET:
            return EnsembleSummaryProviderImplParquet.from_backing_store(
                self._storage_dir, storage_key
            )

        if self._pref_df_backing is BackingType.INMEM_PARQUET:
            return EnsembleSummaryProviderImplInMemParquet.from_backing_store(
                self._storage_dir, storage_key
            )

        raise NotImplementedError("Unhandled preferred df backing type")

    # -------------------------------------------------------------------------
    # Simple solution for writing data to backing store according to the backing
    # type that is configured for the factory
    def _write_df_to_pref_df_backing(
        self, storage_key: str, ensemble_df: pd.DataFrame
    ) -> None:
        if self._pref_df_backing is BackingType.ARROW:
            EnsembleSummaryProviderImplArrow.write_backing_store_from_ensemble_dataframe(
                self._storage_dir, storage_key, ensemble_df
            )

        elif self._pref_df_backing is BackingType.PARQUET:
            EnsembleSummaryProviderImplParquet.write_backing_store_from_ensemble_dataframe(
                self._storage_dir, storage_key, ensemble_df
            )

        elif self._pref_df_backing is BackingType.INMEM_PARQUET:
            EnsembleSummaryProviderImplInMemParquet.write_backing_store_from_ensemble_dataframe(
                self._storage_dir, storage_key, ensemble_df
            )

        else:
            raise NotImplementedError("Unhandled preferred df backing type")


# -------------------------------------------------------------------------
def _load_ensemble_smry_dataframe_using_fmu(
    ens_path: str, time_index: str
) -> pd.DataFrame:

    LOGGER.debug(f"_load_ensemble_smry_dataframe_using_fmu() starting - {ens_path}")
    timer = PerfTimer()

    scratch_ensemble = ScratchEnsemble("tempEnsName", paths=ens_path)
    et_create_scratch_ens_s = timer.lap_s()

    ensemble_df = scratch_ensemble.load_smry(time_index=time_index)
    et_load_smry_s = timer.lap_s()

    LOGGER.debug(
        f"_load_ensemble_smry_dataframe_using_fmu() "
        f"finished in: {timer.elapsed_s():.2f}s ("
        f"create_scratch_ens={et_create_scratch_ens_s:.2f}s "
        f"load_smry={et_load_smry_s:.2f}s)"
    )

    return ensemble_df


# -------------------------------------------------------------------------
def _make_hash_string(string_to_hash: str) -> str:
    # There is no security risk here and chances of collision should be very slim
    return hashlib.md5(string_to_hash.encode()).hexdigest()  # nosec
