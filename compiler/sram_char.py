#!/usr/bin/env python3
# See LICENSE for licensing information.
#
# Copyright (c) 2016-2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
"""
This script will characterize an SRAM previously generated by OpenRAM given a
configuration file. Configuration option "use_pex" determines whether extracted
or generated spice is used and option "analytical_delay" determines whether
an analytical model or spice simulation is used for characterization.
"""

import sys
import datetime
from globals import *
try:
    import openram
except:
    # If openram library isn't found as a python package,
    # import it from the $OPENRAM_HOME path.
    import importlib.util
    OPENRAM_HOME = os.getenv("OPENRAM_HOME")
    # Import using spec since the directory can be named something
    # other than "openram".
    spec = importlib.util.spec_from_file_location("openram", "{}/../__init__.py".format(OPENRAM_HOME))
    module = importlib.util.module_from_spec(spec)
    sys.modules["openram"] = module
    spec.loader.exec_module(module)
    import openram

(OPTS, args) = openram.parse_args()

# Override the usage
USAGE = "Usage: {} [options] <config file> <spice netlist>\nUse -h for help.\n".format(__file__)

# Check that we are left with a single configuration file as argument.
if len(args) != 2:
    print(USAGE)
    sys.exit(2)

OPTS.top_process = 'memchar'

# These depend on arguments, so don't load them until now.
from openram import debug

# Parse config file and set up all the options
openram.init_openram(config_file=args[0], is_unit_test=False)

openram.print_banner()

# Configure the SRAM organization (duplicated from openram.py)
from openram.characterizer import fake_sram
s = fake_sram(name=OPTS.output_name,
              word_size=OPTS.word_size,
              num_words=OPTS.num_words,
              write_size=OPTS.write_size,
              num_banks=OPTS.num_banks,
              words_per_row=OPTS.words_per_row,
              num_spare_rows=OPTS.num_spare_rows,
              num_spare_cols=OPTS.num_spare_cols)

debug.check(os.path.exists(args[1]), "Spice netlist file {} not found.".format(args[1]))
sp_file = args[1]
s.generate_pins()
s.setup_multiport_constants()

OPTS.netlist_only = True
OPTS.check_lvsdrc = False
OPTS.nomimal_corner_only = True

# TODO: remove this after adding trimmed netlist gen to sram run
OPTS.trim_netlist = False

# Characterize the design
start_time = datetime.datetime.now()
from openram.characterizer import lib
debug.print_raw("LIB: Characterizing... ")
lib(out_dir=OPTS.output_path, sram=s, sp_file=sp_file, use_model=False)
print_time("Characterization", datetime.datetime.now(), start_time)

# Output info about this run
print("Output files are:\n{0}*.lib".format(OPTS.output_path))
#report_status() #could modify this function to provide relevant info

# Delete temp files, remove the dir, etc.
openram.end_openram()