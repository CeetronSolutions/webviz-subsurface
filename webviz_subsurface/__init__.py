import glob
import pathlib

from pkg_resources import get_distribution, DistributionNotFound
import webviz_config


try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass


@webviz_config.SHARED_SETTINGS_SUBSCRIPTIONS.subscribe("scratch_ensembles")
def subscribe(
    scratch_ensembles: dict, config_folder: pathlib.Path, portable: bool
) -> dict:
    if scratch_ensembles is not None:
        for ensemble_name, ensemble_path in scratch_ensembles.items():
            if not pathlib.Path(ensemble_path).is_absolute():
                scratch_ensembles[ensemble_name] = str(config_folder / ensemble_path)

            if not portable and not glob.glob(
                str(pathlib.Path(scratch_ensembles[ensemble_name]) / "OK")
            ):
                if not glob.glob(scratch_ensembles[ensemble_name]):
                    raise ValueError(
                        f"Ensemble {ensemble_name} is said to be located at {ensemble_path},"
                        " but that wildcard path does not give any matches."
                    )
                raise ValueError(
                    f"No realizations with a valid target file ('OK') found for ensemble "
                    f"{ensemble_name} located at {ensemble_path}. This can occur when running "
                    "ERT if no simulations are finished, or all simulations have failed."
                )

    return scratch_ensembles
