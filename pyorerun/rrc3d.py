from pathlib import Path
from typing import Any

import ezc3d
import numpy as np
import rerun as rr
from pyomeca import Markers as PyoMarkers

from .phase_rerun import PhaseRerun


def rrc3d(
    c3d_file: str,
    show_floor: bool = True,
    show_force_plates: bool = True,
    show_forces: bool = True,
    marker_trajectories: bool = False,
) -> None:
    """
    Display a c3d file in rerun.

    Parameters
    ----------
    cd3_file: str
        The c3d file to display.
    show_floor: bool
        If True, show the floor.
    show_force_plates: bool
        If True, show the force plates.
    show_forces: bool
        If True, show the forces.
    show_camera: bool
        If True, show the camera.
    marker_trajectories: bool
        If True, show the marker trajectories.
    """

    # Load a c3d file
    pyomarkers = PyoMarkers.from_c3d(c3d_file)
    units = pyomarkers.units
    pyomarkers = adjust_position_unit_to_meters(pyomarkers, pyomarkers.units)
    t_span = pyomarkers.time.to_numpy()
    filename = Path(c3d_file).name

    force_plates_corners = get_force_plates(c3d_file, units=units)
    lowest_corner = get_lowest_corner(c3d_file, units=units)

    phase_rerun = PhaseRerun(t_span)
    phase_rerun.add_xp_markers(filename, pyomarkers)

    if show_force_plates:
        for i, corners in enumerate(force_plates_corners):
            phase_rerun.add_force_plate(f"force_plate_{i}", corners["corners"])

    if show_forces:
        force_data = get_force_vector(c3d_file)
        for i, force in enumerate(force_data):
            ratio = force["force"].shape[1] / t_span.shape[0]
            down_sampled_slice = slice(0, force["center_of_pressure"].shape[1], int(ratio))
            down_sampled_center_of_pressure = adjust_position_unit_to_meters(
                force["center_of_pressure"][:, down_sampled_slice], unit=units
            )
            down_sampled_force = force["force"][:, down_sampled_slice]
            phase_rerun.add_force_data(
                num=i, force_origin=down_sampled_center_of_pressure, force_vector=down_sampled_force
            )

    if show_floor:
        square_width = max_xy_coordinate_span_by_markers(pyomarkers)
        phase_rerun.add_floor(square_width, height_offset=lowest_corner)

    phase_rerun.rerun(filename)

    if marker_trajectories:
        # todo: find a better way to display curves but hacky way ok for now
        for frame, t in enumerate(t_span):
            rr.set_time_seconds("stable_time", t)
            phase_rerun.xp_data.xp_data[0].to_rerun_curve(frame)


def max_xy_coordinate_span_by_markers(pyomarkers: PyoMarkers) -> float:
    """Return the max span of the x and y coordinates of the markers."""
    min_pyomarkers = np.min(np.min(pyomarkers.to_numpy(), axis=2), axis=1)
    max_pyomarkers = np.max(np.max(pyomarkers.to_numpy(), axis=2), axis=1)
    x_absolute_max = np.max(np.abs([min_pyomarkers[0], max_pyomarkers[0]]))
    y_absolute_max = np.max(np.abs([min_pyomarkers[1], max_pyomarkers[1]]))

    return np.max([x_absolute_max, y_absolute_max])


def c3d_file_format(cd3_file) -> ezc3d.c3d:
    """Return the c3d file in the format of ezc3d.c3d if it is a string path."""
    if isinstance(cd3_file, str):
        return ezc3d.c3d(cd3_file, extract_forceplat_data=True)

    return cd3_file


def adjust_pyomarkers_unit_to_meters(pyomarkers: PyoMarkers, unit: str) -> PyoMarkers:
    """Adjust the positions to meters for displaying purposes."""
    pyomarkers = adjust_position_unit_to_meters(pyomarkers, unit)
    pyomarkers.attrs["units"] = "m"
    return pyomarkers


def adjust_position_unit_to_meters(array: Any, unit: str) -> Any:
    conversion_factors = {"mm": 1000, "cm": 100, "m": 1}
    for u, factor in conversion_factors.items():
        if u in unit:
            array /= factor
            break
    else:
        raise ValueError("The unit of the c3d file is not in meters, mm or cm.")
    return array


def get_force_plates(c3d_file, units) -> list[dict[str, np.ndarray]]:
    c3d_file = c3d_file_format(c3d_file)
    force_plates = []
    nb_force_plates = c3d_file["parameters"]["FORCE_PLATFORM"]["USED"]["value"][0]
    for i in range(nb_force_plates):
        force_plates.append(
            {
                "corners": adjust_position_unit_to_meters(
                    c3d_file["parameters"]["FORCE_PLATFORM"]["CORNERS"]["value"][:, :, i],
                    unit=units,
                ),
            }
        )

    return force_plates


def get_lowest_corner(c3d_file, units) -> float:
    c3d_file = c3d_file_format(c3d_file)
    corners = c3d_file["parameters"]["FORCE_PLATFORM"]["CORNERS"]["value"][2, :, :]

    if corners.shape[1] == 0:
        return 0

    return np.min(
        adjust_position_unit_to_meters(
            c3d_file["parameters"]["FORCE_PLATFORM"]["CORNERS"]["value"][2, :, :],
            unit=units,
        )
    )


def get_force_vector(c3d_file) -> list[dict[str, np.ndarray]]:
    c3d_file = c3d_file_format(c3d_file)
    return c3d_file["data"]["platform"]
