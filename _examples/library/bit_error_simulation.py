"""
    This example is to do a simple simulation of the device to catch the errors
"""

import matplotlib.pyplot as plt

# Import required HermesPy modules
from hermespy.simulation.simulation import Simulation
from hermespy.modem import Modem, WaveformGeneratorPskQam
from hermespy.modem.evaluators import BitErrorEvaluator, BlockErrorEvaluator, FrameErrorEvaluator

# Create a new HermesPy simulation scenario
simulation = Simulation()

# Create a new simulated device
device = simulation.scenario.new_device()

# Add a modem at the simulated device
modem = Modem()
modem.waveform_generator = WaveformGeneratorPskQam()
modem.device = device

# Configure simulation evaluators
simulation.add_evaluator(BitErrorEvaluator(modem, modem))
simulation.add_evaluator(BlockErrorEvaluator(modem, modem))
simulation.add_evaluator(FrameErrorEvaluator(modem, modem))

# Configure simulation sweep dimension
simulation.new_dimension('snr', [0.5, 1, 2, 4, 8, 16])

# Launch simulation campaign
simulation.num_samples = 1000
result = simulation.run()

# Visualize results
result.plot()
plt.show()
