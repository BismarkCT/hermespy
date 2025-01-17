# -*- coding: utf-8 -*-
"""Octave interface to the Quadriga channel model."""

from __future__ import annotations
from typing import Optional, List, Any, Type

import numpy as np
from oct2py import Oct2Py, Oct2PyError, Struct

from .quadriga_interface import QuadrigaInterface

__author__ = "Tobias Kronauer"
__copyright__ = "Copyright 2021, Barkhausen Institut gGmbH"
__credits__ = ["Tobias Kronauer", "Jan Adler"]
__license__ = "AGPLv3"
__version__ = "0.2.7"
__maintainer__ = "Tobias Kronauer"
__email__ = "tobias.kronaue@barkhauseninstitut.org"
__status__ = "Prototype"


class QuadrigaOctaveInterface(QuadrigaInterface):
    """Quadriga Octave Interface."""

    __octave: Oct2Py

    def __init__(self,
                 path_quadriga_src: Optional[str] = None,
                 antenna_kind: Optional[str] = None,
                 scenario_label: Optional[str] = None,
                 octave_bin: Optional[str] = None) -> None:
        """Quadriga Octave interface object initialization.

        Args:
            path_quadriga_src (str, optional): Path to the Quadriga Matlab source files.
            antenna_kind (str, optional): Type of antenna considered.
            scenario_label (str, optional): Scenario label.
            octave_bin (str, optional): Path to the octave cli executable.
        """

        # Init base class
        QuadrigaInterface.__init__(self, path_quadriga_src, antenna_kind, scenario_label)

        # Init octave session
        self.__octave = Oct2Py()  # executable=octave_bin)

        # Add quadriga source folder to octave lookup paths
        self.__octave.addpath(self.path_quadriga_src)

    def _run_quadriga(self, **parameters) -> List[Any]:

        # Push parameters to quadriga
        for key, value in parameters.items():

            # Convert numpy arrays to lists
            if isinstance(value, np.ndarray):
                value = value.tolist()

            self.__octave.push(key, value)

        # Launch octave
        try:
            self.__octave.eval("hermespy/resources/matlab/launch_quadriga_script")

        except Oct2PyError as error:
            raise RuntimeError(error)

        # Pull & return results
        cirs = self.__octave.pull("cirs")

        if isinstance(cirs, Struct):
            cirs = np.array([[cirs]])

        return cirs
