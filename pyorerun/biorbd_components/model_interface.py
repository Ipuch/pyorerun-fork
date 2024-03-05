import biorbd
import numpy as np
from biorbd import GeneralizedCoordinates


class BiorbdModel:
    """
    A class to handle a biorbd model and its transformations
    """

    def __init__(self, path):
        self.path = path
        self.model = biorbd.Model(path)

    @property
    def name(self):
        return self.path.split("/")[-1].split(".")[0]

    @property
    def marker_names(self) -> tuple[str, ...]:
        return tuple([s.to_string() for s in self.model.markerNames()])

    @property
    def nb_markers(self) -> int:
        return self.model.nbMarkers()

    @property
    def segment_names(self) -> tuple[str, ...]:
        return tuple([s.name().to_string() for s in self.model.segments()])

    @property
    def nb_segments(self) -> int:
        return self.model.nbSegment()

    @property
    def segments(self) -> tuple[biorbd.Segment, ...]:
        return self.model.segments()

    @property
    def segments_with_mesh(self) -> tuple[biorbd.Segment, ...]:
        return tuple([s for s in self.model.segments() if s.characteristics().mesh().hasMesh()])

    @property
    def mesh_paths(self) -> list[str]:
        return [
            s.characteristics().mesh().path().absolutePath().to_string()
            for s in self.model.segments()
            if s.characteristics().mesh().hasMesh()
        ]

    def segment_homogeneous_matrices_in_global(self, q: np.ndarray, segment_index: int) -> np.ndarray:
        """
        Returns a biorbd object containing the roto-translation matrix of the segment in the global reference frame.
        This is useful if you want to interact with biorbd directly later on.
        """
        rt_matrix = self.model.globalJCS(GeneralizedCoordinates(q), segment_index)
        return rt_matrix.to_array()

    def markers(self, q: np.ndarray) -> np.ndarray:
        """
        Returns a Nmarkersx3 array containing the position of each marker in the global reference frame
        """
        return np.array(
            [self.model.markers(GeneralizedCoordinates(q))[i].to_array() for i in range(self.model.nbMarkers())]
        )

    def center_of_mass(self, q: np.ndarray) -> np.ndarray:
        """
        Returns the position of the center of mass in the global reference frame
        """
        return self.model.CoM(GeneralizedCoordinates(q)).to_array()
