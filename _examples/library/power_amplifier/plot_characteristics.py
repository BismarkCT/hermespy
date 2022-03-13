"""
    This example is to make a simple comparison between multiples power amplifiers
"""

import matplotlib.pyplot as plt

# Import required HermesPy modules
from hermespy.simulation.rf_chain.power_amplifier import PowerAmplifier, SalehPowerAmplifier, RappPowerAmplifier, ClippingPowerAmplifier

# Configure the saturation amplitude of the powered amplifiers
saturation_amplitude = 1.0

# Create a new simple power amplifier
power_amplifier = PowerAmplifier(saturation_amplitude=saturation_amplitude)

# Create a new rapp power amplifier, witch is a clipping power amplifier with smoothness factor
rapp_power_amplifier = RappPowerAmplifier(saturation_amplitude=saturation_amplitude,
                                          smoothness_factor=0.5)

# Create a new clipping power amplifier
clipping_power_amplifier = ClippingPowerAmplifier(
    saturation_amplitude=saturation_amplitude)

# Create a new saleh power amplifier
saleh_power_amplifier = SalehPowerAmplifier(saturation_amplitude=saturation_amplitude,
                                            amplitude_alpha=1.9638,
                                            amplitude_beta=0.9945,
                                            phase_alpha=2.5293,
                                            phase_beta=2.8168)

# Visualize results
power_amplifier.plot()
rapp_power_amplifier.plot()
clipping_power_amplifier.plot()
saleh_power_amplifier.plot()
plt.show()
