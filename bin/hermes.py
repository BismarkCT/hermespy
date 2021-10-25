#!/usr/bin/env python

"""This function calls the simulator main function.

It loads and checks all input parameters, creates results directories, initializes random numbers seeds, adds the
simulation paths, generates, saves and plots the statistics.

It can be called as follows:

Example:
    $ python hermes.py

    uses default parameter (../_settings) and output directories (_results_yyyy-mm-dd_iii)

    $ python hermes.py -o <output_dir> -p <parameter_dir>

    uses user-defined parameter and output directories

    $python hermes.py -h

    help on usage


@authors: Andre Noll Barreto (andre.nollbarreto@barkhauseninstitut.org)
Copyright (C) 2019 Barkhausen Institut gGmbH
Released under the Gnu Public License Version 3

"""
import os
import shutil
import datetime
import sys
import argparse
from typing import List, Optional
from ruamel.yaml.constructor import ConstructorError

from simulator_core.random_streams import RandomStreams
from simulator_core import Factory, Executable
from simulator_core.drop_loop import DropLoop


def hermes(args: Optional[List[str]] = None) -> None:
    """HermesPy command line routine.

    Args:
        args ([List[str], optional): Command line arguments.
    """

    # Recover command line arguments from system if none are provided
    if args is None:
        args = sys.argv[1:]

    print("Welcome to HermesPy")
    parser = argparse.ArgumentParser(
        description="usage: hermes.py -p <settings_dir> -o <output_dir>")
    parser.add_argument("-p", help="Settings directory.")
    parser.add_argument("-o", help="Output directory.")
    arguments = parser.parse_args(args)
    input_parameters_dir = arguments.p
    results_dir = arguments.o

    # validate commandline parameters
    if not input_parameters_dir:
        input_parameters_dir = os.path.join(os.getcwd(), '_settings')

    elif not(os.path.isabs(input_parameters_dir)):
        input_parameters_dir = os.path.join(os.getcwd(), input_parameters_dir)

    print('Parameters will be read from ' + input_parameters_dir)

    ##################
    # Import executable from YAML config dump
    factory = Factory()

    try:

        # Create executable
        executable: Executable = factory.load(input_parameters_dir)

    except ConstructorError as error:

        print("\nYAML import failed during parsing of line {} in file '{}':\n\t{}".format(error.problem_mark.line,
                                                                                          error.problem_mark.name,
                                                                                          error.problem,
                                                                                          file=sys.stderr))
        exit(-1)

    # Inform about the results directory
    print("Results will be saved in '{}'".format(executable.results_dir))

    # Dump current configuration to results directory
    shutil.copytree(input_parameters_dir, executable.results_dir, dirs_exist_ok=True)

    ##################
    # run simulation
    executable.run()

    ###########
    # Goodbye :)
    print('Configuration executed. Goodbye.')


if __name__ == "__main__":

    ################################################################
    # read command line parameters and initialize simulation folders
    hermes()
