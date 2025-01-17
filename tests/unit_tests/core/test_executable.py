# -*- coding: utf-8 -*-
"""Test HermesPy base executable."""

import unittest
import tempfile
from contextlib import _GeneratorContextManager
from typing import Type
from unittest.mock import Mock, patch

from ruamel.yaml import SafeRepresenter, Node, ScalarNode

from hermespy.core import Executable, Verbosity
from hermespy.core.factory import Serializable

__author__ = "Jan Adler"
__copyright__ = "Copyright 2022, Barkhausen Institut gGmbH"
__credits__ = ["Jan Adler"]
__license__ = "AGPLv3"
__version__ = "0.2.5"
__maintainer__ = "Jan Adler"
__email__ = "jan.adler@barkhauseninstitut.org"
__status__ = "Prototype"


class ExecutableStub(Executable):
    """Testing instantiation of the abstract Executable prototype, mock implementing all abstract functions."""

    def __init__(self, *args) -> None:
        Executable.__init__(self, *args)

    def run(self) -> None:
        pass

    @classmethod
    def to_yaml(cls: Type[Serializable],
                representer: SafeRepresenter,
                node: Serializable) -> Node:

        return ScalarNode('ExecutableStub', None)


class TestExecutable(unittest.TestCase):
    """Test the base executable prototype, the base class for hermes operations."""

    def setUp(self) -> None:

        self.verbosity = Verbosity.NONE

        with tempfile.TemporaryDirectory() as tempdir:
            self.executable = ExecutableStub(tempdir, self.verbosity)

    def test_init(self) -> None:
        """Executable initialization parameters should be properly stored."""

        self.assertEqual(self.verbosity, self.executable.verbosity)

    def test_execute(self) -> None:
        """Executing the executable should call the run routine."""

        with patch.object(self.executable, 'run') as run:

            self.executable.execute()
            self.assertTrue(run.called)

    def test_results_dir_setget(self) -> None:
        """Results directory property getter should return setter argument."""

        with tempfile.TemporaryDirectory() as dirname:

            self.executable.results_dir = dirname
            self.assertEqual(dirname, self.executable.results_dir)

    def test_results_dir_validation(self) -> None:
        """Results directory property setter should throw ValueError on invalid arguments."""

        with tempfile.NamedTemporaryFile() as file:
            with self.assertRaises(ValueError):
                self.executable.results_dir = file.name

        with self.assertRaises(ValueError):
            self.executable.results_dir = "ad213ijt0923h1o2i3hnjqnda"

    def test_verbosity_setget(self) -> None:
        """Verbosity property getter should return setter argument."""

        for verbosity_option in Verbosity:

            self.executable.verbosity = verbosity_option
            self.assertEqual(verbosity_option, self.executable.verbosity)

    def test_verbosity_setget_str(self) -> None:
        """Verbosity property getter should return setter argument for strings."""

        for verbosity_option in Verbosity:

            self.executable.verbosity = verbosity_option.name
            self.assertEqual(verbosity_option, self.executable.verbosity)

    def test_style_setget(self) -> None:
        """Style property getter should return setter argument."""

        style = 'light'
        self.executable.style = style

        self.assertEqual(style, self.executable.style)

    def test_style_validation(self) -> None:
        """Style property setter should raise ValueError on invalid styles."""

        with self.assertRaises(ValueError):
            self.executable.style = "131241251"

    def test_style_context(self) -> None:
        """Style context should return PyPlot style context."""

        self.assertTrue(isinstance(self.executable.style_context(), _GeneratorContextManager))
