"""
    This example is to make a simulation of exchanging information between devices with image data
"""

import os
import matplotlib.pyplot as plt
import numpy as np

# Import required HermesPy modules
from hermespy.modem import Modem, WaveformGeneratorPskQam
from hermespy.modem.waveform_generator_psk_qam import PskQamCorrelationSynchronization, \
    PskQamLeastSquaresChannelEstimation, PskQamZeroForcingChannelEqualization
from hermespy.modem.waveform_generator_chirp_fsk import WaveformGeneratorChirpFsk, ChirpFskCorrelationSynchronization
from hermespy.core.scenario import Scenario
from hermespy.simulation import SimulatedDevice
from hermespy.modem.bits_source import StreamBitsSource


# Create a new HermesPy simulation scenario
scenario = Scenario[SimulatedDevice]()

# Create a new simulated device
device = SimulatedDevice()
scenario.add_device(device)

# # Configure simulation waveform generator chirp fsk
# waveform_generator = WaveformGeneratorChirpFsk(oversampling_factor=8)
# waveform_generator.num_pilot_chirps = 20
# waveform_generator.num_data_chirps = 80
# waveform_generator.synchronization = ChirpFskCorrelationSynchronization()

# Configure simulation waveform generator psk qam
waveform_generator = WaveformGeneratorPskQam(oversampling_factor=8)
waveform_generator.num_preamble_symbols = 128
waveform_generator.num_data_symbols = 1024
waveform_generator.modulation_order = 4
waveform_generator.synchronization = PskQamCorrelationSynchronization()
waveform_generator.channel_estimation = PskQamLeastSquaresChannelEstimation()
waveform_generator.channel_equalization = PskQamZeroForcingChannelEqualization()

# Configure simulation waveform generator sampling rate
device.sampling_rate = waveform_generator.sampling_rate

# Configure the path to image example
source = StreamBitsSource(os.path.join(
    os.path.dirname(__file__), '../resources/leena.raw'))

# Configure image bit numbers
leena_num_bits = 512 * 512 * 8

# Configure image buffering
image_buffer = np.zeros((512, 512), dtype=np.uint8)
image_buffer[0, 0] = 255

# Add a modem at the simulated device
modem = Modem()
modem.device = device
modem.bits_source = source
modem.waveform_generator = waveform_generator

# Compute number of required frames
bits_per_frame = modem.num_data_bits_per_frame
byte_per_frame = int(bits_per_frame / 8)
num_frames = int(leena_num_bits / bits_per_frame)

# Launch simulation campaign
plt.ion()
fig, axes = plt.subplots()
image = axes.imshow(image_buffer)

for f in range(num_frames):
    # Simulates exchanging information between devices
    tx_signal, tx_symbols, tx_bits = modem.transmit()
    device_transmissions = device.transmit(clear_cache=True)
    device.receive_signal(device_transmissions[0])
    rx_signal, rx_symbols, data_bits = modem.receive()

    # # Simulates exchanging information between devices with snr
    # tx_signal, tx_symbols, tx_bits = modem.transmit()
    # device_transmissions = device.transmit(clear_cache=True)
    # device.receive_signal(device_transmissions[0], snr=8.)
    # rx_signal, rx_symbols, data_bits = modem.receive()

    if len(data_bits) > 0:
        image_buffer.flat[f*byte_per_frame:(f+1)
                          * byte_per_frame] = np.packbits(data_bits)

    # Write the data to the image buffer
    image.set_data(image_buffer)

    # Flush the image buffer
    fig.canvas.flush_events()

# Waiting for input to close the program
input("Press Enter to close...")
plt.close()
