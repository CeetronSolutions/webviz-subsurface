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

from fmu.sumo.explorer import Explorer  # type: ignore

LOGGER = logging.getLogger(__name__)

REL_STAT_CACHE_DIR = "stat_cache"

# pylint: disable=too-few-public-methods
class Col:
    ATTRIBUTE = "attribute"
    NAME = "name"
    DATESTR = "datestr"


class ProviderImplSumo(EnsembleSurfaceProvider):
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
        self._stat_surf_cache = StatSurfCache(self._provider_dir / REL_STAT_CACHE_DIR)

        sumo = Explorer(env="dev", interactive=True)
        case = sumo.get_case_by_id(self._case_sumo_id)
        print(json.dumps(case.meta_data, indent=2, sort_keys=True))

        timer = PerfTimer()

        self._realization_ids = list(case.get_realizations(iteration_id))

        attribute_arr: List[str] = []
        name_arr: List[str] = []
        datestr_arr: List[str] = []

        attrib_names = case.get_object_property_values(
            "tag_name", "surface", iteration_ids=[iteration_id]
        )
        for attrib_name in attrib_names:
            surf_names = case.get_object_property_values(
                "object_name",
                "surface",
                iteration_ids=[iteration_id],
                tag_names=[attrib_name],
            )

            for surf_name in surf_names:
                time_intervals = case.get_object_property_values(
                    "time_interval",
                    "surface",
                    object_names=[surf_name],
                    iteration_ids=[iteration_id],
                    tag_names=[attrib_name],
                )

                for interval_str in time_intervals:
                    print(f"{attrib_name} -- {surf_name} -- {interval_str}")
                    attribute_arr.append(attrib_name)
                    name_arr.append(surf_name)
                    datestr_arr.append(interval_str if interval_str != "NULL" else "")

        LOGGER.debug(f"Sumo discovery of surfaces took: {timer.elapsed_s():.2f}s")

        self._inventory_df = pd.DataFrame(
            {
                Col.ATTRIBUTE: attribute_arr,
                Col.NAME: name_arr,
                Col.DATESTR: datestr_arr,
            }
        )

    @staticmethod
    def from_sumo(
        storage_dir: Path,
        storage_key: str,
        field_name: str,
        case_name: str,
        iteration_id: str,
    ) -> Optional["ProviderImplSumo"]:

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
        return ProviderImplSumo(provider_dir, sumo_id_of_case, case_name, iteration_id)

    def provider_id(self) -> str:
        return self._provider_id

    def attributes(self) -> List[str]:
        return sorted(list(self._inventory_df[Col.ATTRIBUTE].unique()))

    def surface_names_for_attribute(self, surface_attribute: str) -> List[str]:
        return sorted(
            list(
                self._inventory_df.loc[
                    self._inventory_df[Col.ATTRIBUTE] == surface_attribute
                ][Col.NAME].unique()
            )
        )

    def surface_dates_for_attribute(
        self, surface_attribute: str
    ) -> Optional[List[str]]:
        dates = sorted(
            list(
                self._inventory_df.loc[
                    self._inventory_df[Col.ATTRIBUTE] == surface_attribute
                ][Col.DATESTR].unique()
            )
        )
        if len(dates) == 1 and not bool(dates[0]):
            return None

        return dates

    def realizations(self) -> List[int]:
        return sorted(self._realization_ids)

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

    def _get_simulated_surface(
        self, address: SimulatedSurfaceAddress
    ) -> Optional[xtgeo.RegularSurface]:
        """Returns a Xtgeo surface instance of a single realization surface"""

        timer = PerfTimer()

        lookup_datestr = address.datestr if address.datestr is not None else ""
        time_intervals_list = [address.datestr] if address.datestr is not None else []

        df = self._inventory_df
        df = df.loc[
            (df[Col.ATTRIBUTE] == address.attribute)
            & (df[Col.NAME] == address.name)
            & (df[Col.DATESTR] == lookup_datestr)
        ]

        num_inventory_matches = df.shape[0]
        if num_inventory_matches == 0:
            LOGGER.warning(f"No simulated surface in inventory for: {address}")
            return None

        sumo = Explorer(env="dev", interactive=True)
        case = sumo.get_case_by_id(self._case_sumo_id)

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

        lookup_datestr = address.datestr if address.datestr is not None else ""
        time_intervals_list = [address.datestr] if address.datestr is not None else []

        df = self._inventory_df
        df = df.loc[
            (df[Col.ATTRIBUTE] == address.attribute)
            & (df[Col.NAME] == address.name)
            & (df[Col.DATESTR] == lookup_datestr)
        ]

        num_inventory_matches = df.shape[0]
        if num_inventory_matches == 0:
            LOGGER.warning(f"No simulated surface in inventory for: {address}")
            return None

        sumo = Explorer(env="dev", interactive=True)
        case = sumo.get_case_by_id(self._case_sumo_id)

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
