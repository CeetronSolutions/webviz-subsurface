import datetime
import os
from pathlib import Path

import pandas as pd
from fmu.ensemble import ScratchEnsemble

from webviz_subsurface._providers import EnsembleSummaryProviderFactory, Frequency


# Helper function for generating per-realization CSV files based on aggregated CSV file
def _split_aggr_csv_into_per_real(aggr_csvfile: str, output_folder: str) -> None:
    df = pd.read_csv(aggr_csvfile)
    df = df[df["ENSEMBLE"] == "iter-0"]
    df = df.drop(columns="ENSEMBLE")

    for real in range(0, 10):
        real_df = df[df["REAL"] == real]
        real_df = real_df.drop(columns="REAL")
        os.makedirs(f"{output_folder}/realization-{real}/iter-0/", exist_ok=True)
        real_df.to_csv(
            f"{output_folder}/realization-{real}/iter-0/smry.csv", index=False
        )


# Helper function dumping values obtained via fmu to CSV file.
# Used to find the expected values in "arrow" tests
def _dump_smry_to_csv_using_fmu(
    ens_path: str, time_index: str, output_csv_file: str
) -> None:
    scratch_ensemble = ScratchEnsemble("tempEnsName", paths=ens_path)
    df = scratch_ensemble.load_smry(time_index=time_index)
    df.sort_values(["DATE", "REAL"], inplace=True)

    print("Dataframe shape::", df.shape)

    unique_dates = df["DATE"].unique()
    print("Num unique dates:", len(unique_dates))
    print(unique_dates)

    unique_reals = df["REAL"].unique()
    print("Num unique reals:", len(unique_reals))
    print(unique_reals)

    df.to_csv(output_csv_file, index=False)


def test_create_from_arrow_unsmry_lazy(testdata_folder: Path, tmp_path: Path) -> None:

    ensemble_path = str(testdata_folder / "01_drogon_ahm/realization-*/iter-0")

    # Used to generate test results
    # _dump_smry_to_csv_using_fmu(ensemble_path, "monthly", "expected_smry.csv")

    factory = EnsembleSummaryProviderFactory(tmp_path, allow_storage_writes=True)
    provider = factory.create_from_arrow_unsmry_lazy(ensemble_path)

    assert provider.supports_resampling()

    assert provider.vector_metadata("FOPT") is not None

    vecnames = provider.vector_names()
    assert len(vecnames) == 931

    dates = provider.dates(Frequency.MONTHLY)
    assert len(dates) == 31
    assert isinstance(dates[0], datetime.datetime)
    assert dates[0] == datetime.datetime.fromisoformat("2018-01-01")
    assert dates[-1] == datetime.datetime.fromisoformat("2020-07-01")

    realizations = provider.realizations()
    assert len(realizations) == 100
    assert realizations[0] == 0
    assert realizations[-1] == 99

    vecdf = provider.get_vectors_df(["FOPR"], Frequency.MONTHLY)
    assert vecdf.shape == (3100, 3)
    assert vecdf.columns.tolist() == ["DATE", "REAL", "FOPR"]
    assert vecdf["DATE"].nunique() == 31
    assert vecdf["REAL"].nunique() == 100
    sampleddate = vecdf["DATE"][0]
    assert isinstance(sampleddate, datetime.datetime)

    vecdf = provider.get_vectors_df(["FOPR"], Frequency.MONTHLY, [5])
    assert vecdf.shape == (31, 3)
    assert vecdf.columns.tolist() == ["DATE", "REAL", "FOPR"]
    assert vecdf["DATE"].nunique() == 31
    assert vecdf["REAL"].nunique() == 1
    assert vecdf["REAL"][0] == 5


def test_create_from_arrow_unsmry_presampled_monthly(
    testdata_folder: Path, tmp_path: Path
) -> None:

    ensemble_path = testdata_folder / "01_drogon_ahm/realization-*/iter-0"

    factory = EnsembleSummaryProviderFactory(tmp_path, allow_storage_writes=True)
    provider = factory.create_from_arrow_unsmry_presampled(
        str(ensemble_path), Frequency.MONTHLY
    )

    assert not provider.supports_resampling()

    assert provider.vector_metadata("FOPT") is not None

    vecnames = provider.vector_names()
    assert len(vecnames) == 931

    dates = provider.dates(None)
    assert len(dates) == 31
    assert isinstance(dates[0], datetime.datetime)
    assert dates[0] == datetime.datetime.fromisoformat("2018-01-01")
    assert dates[-1] == datetime.datetime.fromisoformat("2020-07-01")

    realizations = provider.realizations()
    assert len(realizations) == 100
    assert realizations[0] == 0
    assert realizations[-1] == 99

    vecdf = provider.get_vectors_df(["FOPR"], None)
    assert vecdf.shape == (3100, 3)
    assert vecdf.columns.tolist() == ["DATE", "REAL", "FOPR"]
    assert vecdf["DATE"].nunique() == 31
    assert vecdf["REAL"].nunique() == 100
    sampleddate = vecdf["DATE"][0]
    assert isinstance(sampleddate, datetime.datetime)


def test_create_from_per_realization_csv_file(
    testdata_folder: Path, tmp_path: Path
) -> None:

    _split_aggr_csv_into_per_real(
        str(testdata_folder / "reek_test_data/aggregated_data/smry.csv"),
        str(tmp_path / "fake_data"),
    )

    factory = EnsembleSummaryProviderFactory(tmp_path, allow_storage_writes=True)

    ens_path = tmp_path / "fake_data/realization-*/iter-0"
    csvfile = "smry.csv"
    provider = factory.create_from_per_realization_csv_file(str(ens_path), csvfile)

    vecnames = provider.vector_names()
    assert len(vecnames) == 16
    assert vecnames[0] == "FGIP"
    assert vecnames[15] == "YEARS"

    realizations = provider.realizations()
    assert len(realizations) == 10

    vecdf = provider.get_vectors_df(["FOPR"], None)
    assert vecdf.shape == (380, 3)
    assert vecdf.columns.tolist() == ["DATE", "REAL", "FOPR"]
    assert vecdf["REAL"].nunique() == 10
    sampleddate = vecdf["DATE"][0]
    assert isinstance(sampleddate, datetime.datetime)

    vecdf = provider.get_vectors_df(["FOPR"], None, [1])
    assert vecdf.shape == (38, 3)
    assert vecdf.columns.tolist() == ["DATE", "REAL", "FOPR"]
    assert vecdf["REAL"].nunique() == 1


def test_create_from_ensemble_csv(testdata_folder: Path, tmp_path: Path) -> None:

    factory = EnsembleSummaryProviderFactory(tmp_path, allow_storage_writes=True)

    csv_filename = (
        testdata_folder / "reek_test_data" / "aggregated_data" / "smry_hm.csv"
    )
    provider = factory.create_from_ensemble_csv_file(csv_filename, "iter-0")

    vecnames = provider.vector_names()
    assert len(vecnames) == 473
    assert vecnames[0] == "BPR:15,28,1"
    assert vecnames[472] == "YEARS"

    realizations = provider.realizations()
    assert len(realizations) == 10

    dates = provider.dates(None)
    assert len(dates) == 38
    assert isinstance(dates[0], datetime.datetime)
    assert dates[0] == datetime.datetime.fromisoformat("2000-01-01")
    assert dates[-1] == datetime.datetime.fromisoformat("2003-02-01")

    vecdf = provider.get_vectors_df(["FOPR"], None)
    assert vecdf.shape == (380, 3)
    assert vecdf.columns.tolist() == ["DATE", "REAL", "FOPR"]
    assert vecdf["REAL"].nunique() == 10
    sampleddate = vecdf["DATE"][0]
    assert isinstance(sampleddate, datetime.datetime)

    vecdf = provider.get_vectors_df(["FOPR"], None, [1])
    assert vecdf.shape == (38, 3)
    assert vecdf.columns.tolist() == ["DATE", "REAL", "FOPR"]
    assert vecdf["REAL"].nunique() == 1