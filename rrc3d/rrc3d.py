import rerun as rr  # NOTE: `rerun`, not `rerun-sdk`!
import numpy as np
import ezc3d

def rrc3d(cd3_file: ezc3d.c3d | str) -> None:


    # Load a c3d file
    c3d_file = c3d_file_format(cd3_file)
    positions = c3d_file["data"]["points"]

    filename = cd3_file if isinstance(cd3_file, str) else "c3d file"

    nb_markers = positions.shape[1]
    nb_frames = positions.shape[2]

    frequency = c3d_file["header"]["points"]["frame_rate"]
    first_frame = c3d_file["header"]["points"]["first_frame"]
    initial_time = first_frame / frequency
    unit = c3d_file["parameters"]["POINT"]["UNITS"]["value"]

    labels = c3d_file["parameters"]["POINT"]["LABELS"]["value"]

    COLORS = np.ones((nb_markers, 3))

    if unit == "mm":
        positions /= 1000

    time = initial_time

    rr.init(filename, spawn=True)

    for i in range(nb_frames):
        # put first frame in shape (n_mark, 3)
        positions_f = positions[:3, :, i].T

        rr.log(
            "my markers",
            rr.Points3D(positions_f, colors=COLORS, radii=10, labels=labels)
        )

        time += 1 / frequency
        rr.set_time_seconds("stable_time", time)


def c3d_file_format(cd3_file) -> ezc3d.c3d:
    if isinstance(cd3_file, str):
        return ezc3d.c3d(cd3_file)

    return cd3_file
