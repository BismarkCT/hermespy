"""
    This example is to make a simple Monte Carlo simulation of device
"""

import matplotlib.pyplot as plt

# Import required HermesPy modules
from hermespy.simulation import Simulation
from hermespy.modem import Modem, WaveformGeneratorPskQam, BitErrorEvaluator

# Create a new HermesPy simulation scenario
simulation = Simulation()

# Create a new simulated device
device = simulation.scenario.new_device()

# Add a modem at the simulated device
operator = Modem()
operator.waveform_generator = WaveformGeneratorPskQam(oversampling_factor=8)
operator.device = device

# Configure Monte Carlo simulation
simulation.add_evaluator(BitErrorEvaluator(operator, operator))
simulation.new_dimension('snr', [10, 4, 2, 1, 0.5])
simulation.num_samples = 1000

# Launch simulation campaign
result = simulation.run()

# Visualize results
result.plot()
plt.show()
