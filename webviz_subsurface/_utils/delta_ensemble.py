from typing import List, Optional, Sequence
import numpy as np
import pandas as pd

# class DeltaEnsemble(EnsembleSummaryProvider):
class DeltaEnsemble:
    """
    Delta ensemble object, based on EnsembleSummaryProvider implementation
    made by Sigurd.

    Thereby new object will be: class DeltaEnsemble(EnsembleSummaryProvider)
     - Where ensemble_a and ensemble_b will be instances EnsembleSummaryProviders
     when new interface is taken in use.

    """

    def __init__(self, ensemble_a: str, ensemble_b: str, smry: pd.DataFrame) -> None:
        """
        When new EnsembleSummaryProvider is in place, the attributes will change:

        - self._a str will be replaced with EnsembleSummaryProvider for ensemble A
        - self._b str will be replaced with EnsembleSummaryProvider for ensemble B
        - self._smry will be removed, as providers a and b are given as attributes
        """
        self._a: str = ensemble_a
        self._b: str = ensemble_b
        self._smry: pd.DataFrame = smry

    def vector_names(self) -> List[str]:
        return [
            col
            for col in list(self._smry.columns)
            if col not in ["DATE", "REAL", "ENSEMBLE"]
        ]

    def vector_names_filtered_by_value(
        self,
        exclude_all_values_zero: bool = False,
        exclude_constant_values: bool = False,
    ) -> List[str]:
        ret_vec_names: List[str] = []
        for vec_name in self.vector_names():
            nparray = self.get_vectors_df(vec_name).values
            minval = np.nanmin(nparray)
            maxval = np.nanmax(nparray)

            if minval == maxval:
                if exclude_constant_values:
                    continue

                if exclude_all_values_zero and minval == 0:
                    continue

            ret_vec_names.append(vec_name)
        return ret_vec_names

    def realizations(self) -> List[int]:
        return self._smry["REAL"].unique().tolist()

    def get_vectors_df(
        self, vector_names: Sequence[str], realizations: Optional[Sequence[int]] = None
    ) -> pd.DataFrame:
        columns_to_get = ["DATE", "REAL"]
        columns_to_get.extend(vector_names)

        # Get vectors for specified ensemble
        ensemble_a_df = self._smry.loc[
            self._smry["ENSEMBLE"] == self._a, self._smry.columns.isin(columns_to_get)
        ]
        ensemble_b_df = self._smry.loc[
            self._smry["ENSEMBLE"] == self._b, self._smry.columns.isin(columns_to_get)
        ]

        # Filter realizations
        if realizations:
            ensemble_a_df = ensemble_a_df[ensemble_a_df["REAL"].isin(realizations)]
            ensemble_b_df = ensemble_b_df[ensemble_b_df["REAL"].isin(realizations)]

        # TODO: Sort rows by realization integer and thereafter date to ensure correct subtraction?

        ensemble_a_df = ensemble_a_df.set_index(["DATE", "REAL"])
        ensemble_b_df = ensemble_b_df.set_index(["DATE", "REAL"])
        delta_df = ensemble_a_df.sub(ensemble_b_df).reset_index()
        delta_df["ENSEMBLE"] = f"({self._a}) - ({self._b})"

        return delta_df.dropna(axis=0, how="any")
