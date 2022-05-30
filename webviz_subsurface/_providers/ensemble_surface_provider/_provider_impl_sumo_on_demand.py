import logging
import shutil
import warnings
from enum import Enum
from pathlib import Path
from typing import List, Optional, Set
import json
from io import BytesIO

import numpy as np
import pandas as pd
import xtgeo

from webviz_subsurface._utils.perf_timer import PerfTimer

from ._stat_surf_cache import StatSurfCache
from ._surface_discovery import SurfaceFileInfo
from .ensemble_surface_provider import (
    EnsembleSurfaceProvider,
    ObservedSurfaceAddress,
    SimulatedSurfaceAddress,
    StatisticalSurfaceAddress,
    SurfaceAddress,
    SurfaceStatistic,
)

from webviz_config.webviz_instance_info import WEBVIZ_INSTANCE_INFO

from fmu.sumo.explorer import Explorer  # type: ignore
from fmu.sumo.explorer import Case  # type: ignore

LOGGER = logging.getLogger(__name__)

REL_STAT_CACHE_DIR = "stat_cache"

import redislite

# import redislite.patch
# redislite.patch.patch_redis("./myRedisLite.db")


import flask_caching


class ProviderImplSumoOnDemand(EnsembleSurfaceProvider):
    def __init__(
        self,
        provider_dir: Path,
        sumo_id_of_case: str,
        case_name: str,
        iteration_id: str,
    ) -> None:
        self._provider_dir = provider_dir
        self._provider_id = f"{case_name}__{iteration_id}__{sumo_id_of_case}"
        self._case_sumo_id = sumo_id_of_case
        self._case_name = case_name
        self._iteration_id = iteration_id

        # self._metadata_cache = flask_caching.Cache(
        #     config={
        #         "CACHE_TYPE": "FileSystemCache",
        #         "CACHE_DIR": self._provider_dir / "metadata_cache",
        #         "CACHE_DEFAULT_TIMEOUT": 30,
        #         # "CACHE_DEFAULT_TIMEOUT": 30,
        #         # "CACHE_THRESHOLD": 5,
        #     }
        # )

        self._provider_dir.mkdir(parents=True, exist_ok=True)
        my_redis = redislite.Redis(self._provider_dir / "myRedisLite.db")
        self._metadata_cache = flask_caching.Cache(
            config={"CACHE_TYPE": "RedisCache", "CACHE_REDIS_HOST": my_redis}
        )

        self._metadata_cache.init_app(WEBVIZ_INSTANCE_INFO.dash_app.server)

        self._stat_surf_cache = StatSurfCache(self._provider_dir / REL_STAT_CACHE_DIR)

    @staticmethod
    def from_sumo(
        storage_dir: Path,
        storage_key: str,
        field_name: str,
        case_name: str,
        iteration_id: str,
    ) -> Optional["ProviderImplSumoOnDemand"]:

        sumo = Explorer(env="dev", interactive=True)
        case_collection = sumo.get_cases(fields=[field_name])
        sumo_id_of_case = None
        for case in case_collection:
            if case.case_name == case_name:
                sumo_id_of_case = case.sumo_id
                break

        if not sumo_id_of_case:
            raise ValueError(
                f"Could not find or access field={field_name}, case={case_name}"
            )

        provider_dir = storage_dir / storage_key
        return ProviderImplSumoOnDemand(
            provider_dir, sumo_id_of_case, case_name, iteration_id
        )

    def provider_id(self) -> str:
        return self._provider_id

    def attributes(self) -> List[str]:
        timer = PerfTimer()

        cache_key = "attributes"
        cached_arr = self._metadata_cache.get(cache_key)
        if cached_arr is not None:
            LOGGER.debug(f"attributes() from cache in: {timer.elapsed_s():.2f}s")
            return cached_arr

        case = self._get_my_sumo_case()
        attrib_names = case.get_object_property_values(
            "tag_name", "surface", iteration_ids=[self._iteration_id]
        )
        attrib_names = sorted(attrib_names)

        self._metadata_cache.set(cache_key, attrib_names)

        LOGGER.debug(f"attributes() completed using Sumo in: {timer.elapsed_s():.2f}s")

        return attrib_names

    def surface_names_for_attribute(self, surface_attribute: str) -> List[str]:
        timer = PerfTimer()

        cache_key = f"surface_names_for_attribute_{surface_attribute}"
        cached_arr = self._metadata_cache.get(cache_key)
        if cached_arr is not None:
            LOGGER.debug(
                f"surface_names_for_attribute({surface_attribute}) from cache in: {timer.elapsed_s():.2f}s"
            )
            return cached_arr

        case = self._get_my_sumo_case()
        surf_names = case.get_object_property_values(
            "object_name",
            "surface",
            iteration_ids=[self._iteration_id],
            tag_names=[surface_attribute],
        )
        surf_names = sorted(surf_names)

        self._metadata_cache.set(cache_key, surf_names)

        LOGGER.debug(
            f"surface_names_for_attribute({surface_attribute}) completed using Sumo in: {timer.elapsed_s():.2f}s"
        )

        return surf_names

    def surface_dates_for_attribute(
        self, surface_attribute: str
    ) -> Optional[List[str]]:
        timer = PerfTimer()

        cache_key = f"surface_dates_for_attribute_{surface_attribute}"
        cached_arr = self._metadata_cache.get(cache_key)
        if cached_arr is not None:
            LOGGER.debug(
                f"surface_dates_for_attribute({surface_attribute}) from cache in: {timer.elapsed_s():.2f}s"
            )
            if len(cached_arr) == 1 and not bool(cached_arr[0]):
                return None
            return cached_arr

        case = self._get_my_sumo_case()
        time_intervals = case.get_object_property_values(
            "time_interval",
            "surface",
            iteration_ids=[self._iteration_id],
            tag_names=[surface_attribute],
        )

        datestr_arr: List[str] = []
        for interval_str in time_intervals:
            datestr_arr.append(interval_str if interval_str != "NULL" else "")

        datestr_arr = sorted(datestr_arr)

        self._metadata_cache.set(cache_key, datestr_arr)

        LOGGER.debug(
            f"surface_dates_for_attribute({surface_attribute}) completed using Sumo in: {timer.elapsed_s():.2f}s"
        )

        if len(datestr_arr) == 1 and not bool(datestr_arr[0]):
            return None

        return datestr_arr

    def realizations(self) -> List[int]:
        timer = PerfTimer()

        cache_key = "realizations"
        cached_arr = self._metadata_cache.get(cache_key)
        if cached_arr is not None:
            LOGGER.debug(f"realizations() from cache in: {timer.elapsed_s():.2f}s")
            return cached_arr

        case = self._get_my_sumo_case()
        realization_ids = case.get_object_property_values("realization_id", "surface")
        realization_ids = sorted(realization_ids)

        self._metadata_cache.set(cache_key, realization_ids)

        LOGGER.debug(
            f"realizations() completed using Sumo in: {timer.elapsed_s():.2f}s"
        )

        return realization_ids

    def get_surface(
        self,
        address: SurfaceAddress,
    ) -> Optional[xtgeo.RegularSurface]:
        if isinstance(address, StatisticalSurfaceAddress):
            return self._get_statistical_surface(address)
        if isinstance(address, SimulatedSurfaceAddress):
            return self._get_simulated_surface(address)
        if isinstance(address, ObservedSurfaceAddress):
            return None

        raise TypeError("Unknown type of surface address")

    def _get_my_sumo_case(self) -> Case:
        timer = PerfTimer()

        sumo = Explorer(env="dev", interactive=True)
        case = sumo.get_case_by_id(self._case_sumo_id)

        LOGGER.debug(f"_get_my_sumo_case() took: {timer.elapsed_s():.2f}s")

        return case

    def _get_simulated_surface(
        self, address: SimulatedSurfaceAddress
    ) -> Optional[xtgeo.RegularSurface]:
        """Returns a Xtgeo surface instance of a single realization surface"""

        timer = PerfTimer()

        case = self._get_my_sumo_case()

        time_intervals_list = [address.datestr] if address.datestr is not None else []

        surface_collection = case.get_objects(
            "surface",
            iteration_ids=[self._iteration_id],
            realization_ids=[address.realization],
            tag_names=[address.attribute],
            object_names=[address.name],
            time_intervals=time_intervals_list,
        )

        num_surfaces = len(surface_collection)
        if num_surfaces == 0:
            LOGGER.warning(f"No simulated surface found in Sumo for {address}")
            return None
        if num_surfaces > 1:
            LOGGER.warning(
                f"Multiple simulated surfaces found in Sumo for: {address}"
                "Returning first surface."
            )

        surf = surface_collection[0]
        blob_bytes: bytes = surf.blob
        byte_stream = BytesIO(blob_bytes)
        xtgeo_surf = xtgeo.surface_from_file(byte_stream)

        LOGGER.debug(f"Loaded simulated surface from Sumo in: {timer.elapsed_s():.2f}s")

        return xtgeo_surf

    def _get_statistical_surface(
        self, address: StatisticalSurfaceAddress
    ) -> Optional[xtgeo.RegularSurface]:

        timer = PerfTimer()

        case = self._get_my_sumo_case()

        time_intervals_list = [address.datestr] if address.datestr is not None else []

        surface_collection = case.get_objects(
            "surface",
            iteration_ids=[self._iteration_id],
            realization_ids=address.realizations,
            tag_names=[address.attribute],
            object_names=[address.name],
            time_intervals=time_intervals_list,
        )

        surf_count = len(surface_collection)
        if surf_count == 0:
            LOGGER.warning(f"No simulated surfaces found in Sumo for {address}")
            return None

        surfstat_to_sumostatstr_map = {
            SurfaceStatistic.MEAN: "MEAN",
            SurfaceStatistic.STDDEV: "STD",
            SurfaceStatistic.MINIMUM: "MIN",
            SurfaceStatistic.MAXIMUM: "MAX",
            SurfaceStatistic.P10: "P10",
            SurfaceStatistic.P90: "P90",
        }
        sumo_aggr_str = surfstat_to_sumostatstr_map[address.statistic]

        agg_surf_bytes: bytes = surface_collection.aggregate(sumo_aggr_str)
        byte_stream = BytesIO(agg_surf_bytes)
        xtgeo_surf = xtgeo.surface_from_file(byte_stream)

        LOGGER.debug(
            f"Calculated statistical surface using Sumo in: {timer.elapsed_s():.2f}s ("
            f"[#surfaces={surf_count}, stat={address.statistic}, "
            f"attr={address.attribute}, name={address.name}, date={address.datestr}]"
        )

        return xtgeo_surf
