"""
    Send a numpy array roundtrip to Octave using an m-file.
"""

# Import required oct2py modules
from xml.etree.ElementTree import indent
from oct2py import octave
import numpy as np

# Add path to oct2py look for files
octave.addpath('./_examples/resources')

# Define array
x = np.array([[1, 2], [3, 4]], dtype=float)

#use nout='max_nout' to automatically choose max possible nout
out, oclass = octave.roundtrip(x ,nout=2)

# Visualize results
print(x, "\n")
print(x.dtype, "<- x type\n")
print(out, "<- out\n")
print(out.dtype, "<- out type\n")
print(oclass, "<- out class")