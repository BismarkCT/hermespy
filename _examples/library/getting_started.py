"""
    This example is to make a simple simulation of transmitter device
"""

import matplotlib.pyplot as plt

# Import required HermesPy modules
from hermespy.simulation import SimulatedDevice
from hermespy.modem import Modem, WaveformGeneratorPskQam

# Configure devive operator
operator = Modem()
operator.waveform_generator = WaveformGeneratorPskQam(oversampling_factor=8)
operator.device = SimulatedDevice()

# Launch simulation to take transmit signal
signal, _, _ = operator.transmit()

# Visualize results of transmit signal
signal.plot()
plt.show()
