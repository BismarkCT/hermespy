# -*- coding: utf-8 -*-
"""Test Multipath Fading Channel Model."""

import unittest
import numpy as np
import numpy.random as rand
from numpy import dtype, exp
import numpy.testing as npt
import scipy
from scipy import stats
from scipy.constants import pi
import copy
from unittest.mock import Mock
from typing import Any, Dict

from scipy.constants.codata import unit

from hermespy.channel import MultipathFadingChannel
from hermespy.scenario import Scenario

__author__ = "Tobias Kronauer"
__copyright__ = "Copyright 2021, Barkhausen Institut gGmbH"
__credits__ = ["Tobias Kronauer", "Jan Adler"]
__license__ = "AGPLv3"
__version__ = "0.1.0"
__maintainer__ = "Tobias Kronauer"
__email__ = "tobias.kronaue@barkhauseninstitut.org"
__status__ = "Prototype"


class TestMultipathFadingChannel(unittest.TestCase):
    """Test the multipath fading channel implementation."""

    def setUp(self) -> None:

        np.random.seed(42)

        self.active = True
        self.gain = 1.0

        self.delays = np.zeros(1, dtype=float)
        self.power_profile = np.ones(1, dtype=float)
        self.rice_factors = np.zeros(1, dtype=float)

        self.sampling_rate = 1e6
        self.transmit_frequency = pi * self.sampling_rate
        self.num_sinusoids = 8
        self.doppler_frequency = 0.0

        self.transmitter = Mock()
        self.receiver = Mock()
        self.transmitter.sampling_rate = self.sampling_rate
        self.receiver.sampling_rate = self.sampling_rate
        self.transmitter.num_antennas = 1
        self.receiver.num_antennas = 1
        self.sync_offset_low = 1
        self.sync_offset_high = 3

        self.channel_params = {
            'delays': self.delays,
            'power_profile': self.power_profile,
            'rice_factors': self.rice_factors,
            'active': self.active,
            'transmitter': self.transmitter,
            'receiver': self.receiver,
            'gain': self.gain,
            'doppler_frequency': self.doppler_frequency,
            'num_sinusoids': 8,
            'sync_offset_low': self.sync_offset_low,
            'sync_offset_high': self.sync_offset_high
        }

        self.num_samples = 100

        self.min_number_samples = 1000
        self.max_number_samples = 500000
        self.max_doppler_frequency = 100
        self.max_number_paths = 20
        self.max_delay_in_samples = 30

    def test_init(self) -> None:
        """The object initialization should properly store all parameters."""

        channel = MultipathFadingChannel(**self.channel_params)

        self.assertIs(self.transmitter, channel.transmitter, "Unexpected transmitter parameter initialization")
        self.assertIs(self.receiver, channel.receiver, "Unexpected receiver parameter initialization")
        self.assertEqual(self.active, channel.active, "Unexpected active parameter initialization")
        self.assertEqual(self.gain, channel.gain, "Unexpected gain parameter initialization")
        self.assertEqual(self.num_sinusoids, channel.num_sinusoids)
        self.assertEqual(self.doppler_frequency, channel.doppler_frequency)
        self.assertEqual(self.sync_offset_low, channel.sync_offset_low)
        self.assertEqual(self.sync_offset_high, channel.sync_offset_high)

    def test_init_validation(self) -> None:
        """Object initialization should raise ValueError on invalid arguments."""

        with self.assertRaises(ValueError):
            params = copy.deepcopy(self.channel_params)
            params['delays'] = np.array([1, 2])
            _ = MultipathFadingChannel(**params)

        with self.assertRaises(ValueError):
            params = copy.deepcopy(self.channel_params)
            params['power_profile'] = np.array([1, 2])
            _ = MultipathFadingChannel(**params)

        with self.assertRaises(ValueError):
            params = copy.deepcopy(self.channel_params)
            params['rice_factors'] = np.array([1, 2])
            _ = MultipathFadingChannel(**params)

        with self.assertRaises(ValueError):
            params = copy.deepcopy(self.channel_params)
            params['delays'] = np.array([-1.0])
            _ = MultipathFadingChannel(**params)

        with self.assertRaises(ValueError):
            params = copy.deepcopy(self.channel_params)
            params['power_profile'] = np.array([-1.0])
            _ = MultipathFadingChannel(**params)

        with self.assertRaises(ValueError):
            params = copy.deepcopy(self.channel_params)
            params['rice_factors'] = np.array([-1.0])
            _ = MultipathFadingChannel(**params)

    def test_delays_get(self) -> None:
        """Delays getter should return init param."""

        channel = MultipathFadingChannel(**self.channel_params)
        np.testing.assert_array_almost_equal(self.delays, channel.delays)

    def test_power_profiles_get(self) -> None:
        """Power profiles getter should return init param."""

        channel = MultipathFadingChannel(**self.channel_params)
        np.testing.assert_array_almost_equal(self.power_profile, channel.power_profile)

    def test_rice_factors_get(self) -> None:
        """Rice factors getter should return init param."""

        channel = MultipathFadingChannel(**self.channel_params)
        np.testing.assert_array_almost_equal(self.rice_factors, channel.rice_factors)

    def test_doppler_frequency_setget(self) -> None:
        """Doppler frequency property getter should return setter argument."""

        channel = MultipathFadingChannel(**self.channel_params)

        doppler_frequency = 5
        channel.doppler_frequency = doppler_frequency

        self.assertEqual(doppler_frequency, channel.doppler_frequency)

    def test_los_doppler_frequency_setget(self) -> None:
        """Line-of-Sight Doppler frequency property getter should return setter argument,
        alternatively the global Doppler."""

        channel = MultipathFadingChannel(**self.channel_params)

        los_doppler_frequency = 5
        channel.los_doppler_frequency = los_doppler_frequency
        self.assertEqual(los_doppler_frequency, channel.los_doppler_frequency)

        doppler_frequency = 4
        channel.doppler_frequency = doppler_frequency
        channel.los_doppler_frequency = None
        self.assertEqual(doppler_frequency, channel.los_doppler_frequency)

    def test_transmit_precoding_setget(self) -> None:
        """Transmit precoding property getter should return setter argument."""

        channel = MultipathFadingChannel(**self.channel_params)

        precoding = np.identity(5)
        channel.transmit_precoding = precoding
        npt.assert_array_equal(precoding, channel.transmit_precoding)

        channel.transmit_precoding = None
        self.assertEqual(None, channel.transmit_precoding)

    def test_transmit_precoding_validation(self) -> None:
        """Doppler frequency setter should raise ValueError on invalid arguments."""

        channel = MultipathFadingChannel(**self.channel_params)

        with self.assertRaises(ValueError):
            precoding = np.array([1])
            channel.transmit_precoding = precoding

        with self.assertRaises(ValueError):
            precoding = np.array([[1, 0], [1, 1]])
            channel.transmit_precoding = precoding

        with self.assertRaises(ValueError):
            precoding = np.ones((2, 2))
            channel.transmit_precoding = precoding
            
    def test_receive_postcoding_setget(self) -> None:
        """Transmit postcoding property getter should return setter argument."""

        channel = MultipathFadingChannel(**self.channel_params)

        postcoding = np.identity(5)
        channel.receive_postcoding = postcoding
        npt.assert_array_equal(postcoding, channel.receive_postcoding)

        channel.receive_postcoding = None
        self.assertEqual(None, channel.receive_postcoding)

    def test_receive_postcoding_validation(self) -> None:
        """Doppler frequency setter should raise ValueError on invalid arguments."""

        channel = MultipathFadingChannel(**self.channel_params)

        with self.assertRaises(ValueError):
            postcoding = np.array([1])
            channel.receive_postcoding = postcoding

        with self.assertRaises(ValueError):
            postcoding = np.array([[1, 0], [1, 1]])
            channel.receive_postcoding = postcoding

        with self.assertRaises(ValueError):
            postcoding = np.ones((2, 2))
            channel.receive_postcoding = postcoding

    def test_max_delay_get(self) -> None:
        """Max delay property should return maximum of delays."""

        self.channel_params['delays'] = np.array([1, 2, 3])
        self.channel_params['power_profile'] = np.zeros(3)
        self.channel_params['rice_factors'] = np.ones(3)

        channel = MultipathFadingChannel(**self.channel_params)
        self.assertEqual(max(self.channel_params['delays']), channel.max_delay)

    def test_num_sequences_get(self) -> None:
        """Number of fading sequences property should return core parameter lengths."""

        self.channel_params['delays'] = np.array([1, 2, 3])
        self.channel_params['power_profile'] = np.zeros(3)
        self.channel_params['rice_factors'] = np.ones(3)

        channel = MultipathFadingChannel(**self.channel_params)
        self.assertEqual(len(self.channel_params['delays']), channel.num_resolvable_paths)

    def test_num_sinusoids_setget(self) -> None:
        """Number of sinusoids property getter should return setter argument."""

        channel = MultipathFadingChannel(**self.channel_params)

        num_sinusoids = 100
        channel.num_sinusoids = num_sinusoids

        self.assertEqual(num_sinusoids, channel.num_sinusoids)

    def test_num_sinusoids_validation(self) -> None:
        """Number of sinusoids property setter should raise ValueError on invalid arguments."""

        channel = MultipathFadingChannel(**self.channel_params)

        with self.assertRaises(ValueError):
            channel.num_sinusoids = -1

    def test_los_angle_setget(self) -> None:
        """Line of sight angle property getter should return setter argument."""

        channel = MultipathFadingChannel(**self.channel_params)

        los_angle = 15
        channel.los_angle = los_angle
        self.assertEqual(los_angle, channel.los_angle)

        channel.los_angle = None
        self.assertEqual(None, channel.los_angle)

    def test_max_delay_in_samples_get(self) -> None:
        """Max delay in samples should be the transmitter sampling rate times the max delay."""

        self.channel_params['delays'] = np.array([1, 2, 3])
        self.channel_params['power_profile'] = np.zeros(3)
        self.channel_params['rice_factors'] = np.ones(3)
        channel = MultipathFadingChannel(**self.channel_params)

        expected_max_delay = int(max(self.channel_params['delays']) * self.transmitter.sampling_rate)
        self.assertEqual(expected_max_delay, channel.max_delay_in_samples)

    def test_antenna_correlation(self) -> None:
        """Test the antenna correlation"""

        NO_ANTENNAS = 2

        self.transmitter.num_antennas = NO_ANTENNAS
        self.receiver.num_antennas = NO_ANTENNAS

        transmit_precoding = scipy.linalg.sqrtm(np.identity(NO_ANTENNAS) * 4)
        receive_postcoding = scipy.linalg.sqrtm(np.identity(NO_ANTENNAS) * 8)
        self.channel_params['transmit_precoding'] = transmit_precoding
        self.channel_params['receive_postcoding'] = receive_postcoding

        correlated_channel = MultipathFadingChannel(**self.channel_params)

        self.channel_params.pop('transmit_precoding')
        self.channel_params.pop('receive_postcoding')
        uncorrelated_channel = MultipathFadingChannel(**self.channel_params)

        tx_signal = np.exp(2j * pi * np.arange(NO_ANTENNAS * self.num_samples) *
                           self.transmit_frequency / self.sampling_rate).reshape((NO_ANTENNAS, self.num_samples))

        np.random.seed(22)
        rx_signal_correlated_channel = correlated_channel.propagate(tx_signal)
        np.random.seed(22)
        rx_signal_uncorrelated_channel = uncorrelated_channel.propagate(tx_signal)

        expected_rx_signal_correlated_channel = (transmit_precoding  @
                                                 receive_postcoding @
                                                 rx_signal_uncorrelated_channel)
        np.testing.assert_array_almost_equal(expected_rx_signal_correlated_channel, rx_signal_correlated_channel)

    def test_propagation_siso_no_fading(self) -> None:
        """
        Test the propagation through a SISO multipath channel model without fading
        Check if the output sizes are consistent
        Check the output of a SISO multipath channel model without fading (K factor of Rice distribution = inf)
        """

        self.rice_factors[0] = float('inf')
        self.delays[0] = 10 / self.sampling_rate
        channel = MultipathFadingChannel(**self.channel_params)

        timestamps = np.arange(self.num_samples) / self.sampling_rate
        transmission = exp(1j * timestamps * self.transmit_frequency).reshape(1, self.num_samples)
        output = channel.propagate(transmission)

        self.assertEqual(10, output.shape[1] - transmission.shape[1],
                         "Propagation impulse response has unexpected length")

    def test_propagation_fading(self) -> None:
        """
        Test the propagation through a SISO multipath channel with fading.
        """

        test_delays = np.array([1., 2., 3., 4.]) / self.sampling_rate

        reference_params = self.channel_params.copy()
        delayed_params = self.channel_params.copy()

        reference_params['delays'] = np.array([0.0])
        reference_channel = MultipathFadingChannel(**reference_params)

        timestamps = np.arange(self.num_samples) / self.sampling_rate
        transmit_signal = np.exp(2j * pi * timestamps * self.transmit_frequency).reshape((1, self.num_samples))

        for d in range(len(test_delays)):
            delayed_params['delays'] = reference_params['delays'] + test_delays[d]
            delayed_channel = MultipathFadingChannel(**delayed_params)

            np.random.seed(d)
            reference_propagation = reference_channel.propagate(transmit_signal)

            np.random.seed(d)
            delayed_propagation = delayed_channel.propagate(transmit_signal)

            zero_pads = int(test_delays[d] * self.sampling_rate)
            npt.assert_array_almost_equal(reference_propagation, delayed_propagation[:, zero_pads:])

    def test_propagation_fading_interpolation(self) -> None:
        """Test the propagation when path delays do not match sampling instants.
        The delayed signals are expected to be zero-padded and slightly phase shifted.
        """

        test_delays = np.array([.5, .75, 1.25, 15]) / self.sampling_rate

        reference_params = self.channel_params.copy()
        delayed_params = self.channel_params.copy()

        reference_params['delays'] = np.array([0.0])
        reference_channel = MultipathFadingChannel(**reference_params)

        timestamps = np.arange(self.num_samples) / self.sampling_rate
        transmit_signal = np.exp(2j * pi * timestamps * self.transmit_frequency).reshape((1, self.num_samples))

        for d in range(len(test_delays)):

            delayed_params['delays'] = reference_params['delays'] + test_delays[d]
            delayed_channel = MultipathFadingChannel(**delayed_params)

            np.random.seed(d)
            reference_propagation = reference_channel.propagate(transmit_signal)

            np.random.seed(d)
            delayed_propagation = delayed_channel.propagate(transmit_signal)

            zero_pads = int(test_delays[d] * self.sampling_rate)
            npt.assert_array_almost_equal(abs(reference_propagation), abs(delayed_propagation[:, zero_pads:]))

    def test_rayleigh(self) -> None:
        """
        Test if the amplitude of a path is Rayleigh distributed.
        Verify that both real and imaginary components are zero-mean normal random variables with the right variance and
        uncorrelated.
        """
        max_number_of_drops = 200
        samples_per_drop = 1000
        self.doppler_frequency = 200

        self.channel_params['delays'][0] = 0.
        self.channel_params['power_profile'][0] = 1.
        self.channel_params['rice_factors'][0] = 0.
        self.channel_params['doppler_frequency'] = self.doppler_frequency
        channel = MultipathFadingChannel(**self.channel_params)

        time_interval = 1 / self.doppler_frequency  # get uncorrelated samples
        timestamps = np.arange(samples_per_drop) * time_interval

        samples = np.array([])

        is_rayleigh = False
        alpha = .05
        max_corr = 0.05

        number_of_drops = 0
        while not is_rayleigh and number_of_drops < max_number_of_drops:

            channel_gains = channel.siso_impulse_response(timestamps)
            samples = np.append(samples, channel_gains.ravel())

            _, p_real = stats.kstest(np.real(samples), 'norm', args=(0, 1 / np.sqrt(2)))
            _, p_imag = stats.kstest(np.real(samples), 'norm', args=(0, 1 / np.sqrt(2)))

            corr = np.corrcoef(np.real(samples), np.imag(samples))
            corr = corr[0, 1]

            if p_real > alpha and p_imag > alpha and np.abs(corr) < max_corr:
                is_rayleigh = True

            number_of_drops += 1

        self.assertTrue(is_rayleigh)

    def test_rice(self) -> None:
        """
        Test if the amplitude of a path is Ricean distributed.
        """
        max_number_of_drops = 100
        doppler_frequency = 200
        samples_per_drop = 1000

        self.channel_params['delays'][0] = 0.
        self.channel_params['power_profile'][0] = 1.
        self.channel_params['rice_factors'][0] = 1.
        self.channel_params['doppler_frequency'] = doppler_frequency
        channel = MultipathFadingChannel(**self.channel_params)

        time_interval = 1 / doppler_frequency  # get uncorrelated samples
        timestamps = np.arange(samples_per_drop) * time_interval

        samples = np.array([])

        is_rice = False
        alpha = .05

        number_of_drops = 0
        while not is_rice and number_of_drops < max_number_of_drops:

            channel_gains = channel.siso_impulse_response(timestamps)
            samples = np.append(samples, channel_gains.ravel())

            dummy, p_real = stats.kstest(np.abs(samples), 'rice', args=(np.sqrt(2), 0, 1 / 2))

            if p_real > alpha:
                is_rice = True

            number_of_drops += 1

        self.assertTrue(is_rice)

    def test_power_delay_profile(self) -> None:
        """
        Test if the resulting power delay profile matches with the one specified in the parameters.
        Test also an interpolated channel (should have the same rms delay spread)
        """
        max_number_of_drops = 100
        samples_per_drop = 1000
        max_delay_spread_dev = self.sampling_rate / 10  # TODO: This does not make any sense to me?

        self.doppler_frequency = 50
        self.channel_params['doppler_frequency'] = self.doppler_frequency
        self.channel_params['delays'] = np.zeros(5)
        self.channel_params['power_profile'] = np.ones(5)
        self.channel_params['rice_factors'] = np.zeros(5)
        channel = MultipathFadingChannel(**self.channel_params)

        self.channel_params['delays'] = np.array([0, 3, 6, 7, 8]) / self.sampling_rate
        mean_delay = np.mean(self.channel_params['delays'])
        delayed_channel = MultipathFadingChannel(**self.channel_params)

        timestamps = np.arange(samples_per_drop) / self.transmitter.sampling_rate

        for s in range(max_number_of_drops):

            np.random.seed(s+10)
            immediate_response = channel.siso_impulse_response(timestamps)

            np.random.seed(s+10)
            delayed_response = delayed_channel.siso_impulse_response(timestamps)

            immediate_power = np.mean(np.abs(immediate_response) ** 2, axis=0)
            delayed_power = np.mean(np.abs(delayed_response) ** 2, axis=0)

            immediate_time = np.arange(len(immediate_response)) / self.transmitter.sampling_rate
            delayed_time = np.arange(len(delayed_response)) / self.transmitter.sampling_rate

            immediate_spread = np.sqrt(np.mean(immediate_time**2 * abs(immediate_response)**2)
                                       / immediate_power)
            delayed_spread = np.sqrt(np.mean((delayed_time - mean_delay) ** 2 * abs(delayed_response) ** 2)
                                     / delayed_power)

            spread_delta = abs(immediate_spread - delayed_spread)
            self.assertTrue(spread_delta < max_delay_spread_dev)

    def test_channel_gain(self) -> None:
        """
        Test if channel gain is applied correctly on both propagation and channel impulse response
        """
        gain = 10

        doppler_frequency = 200
        sampling_rate = 1e6
        signal_length = 1000

        self.channel_params['delays'][0] = 0.
        self.channel_params['power_profile'][0] = 1.
        self.channel_params['rice_factors'][0] = 0.
        self.channel_params['doppler_frequency'] = doppler_frequency

        channel_no_gain = MultipathFadingChannel(**self.channel_params)

        self.channel_params['gain'] = gain
        channel_gain = MultipathFadingChannel(**self.channel_params)

        frame_size = (1, signal_length)
        tx_signal = rand.normal(size=frame_size) + 1j * rand.normal(size=frame_size)

        np.random.seed(42)  # Reset random number generator
        signal_out_no_gain = channel_no_gain.propagate(tx_signal)

        np.random.seed(42)  # Reset random number generator
        signal_out_gain = channel_gain.propagate(tx_signal)

        npt.assert_array_almost_equal(signal_out_gain, signal_out_no_gain * gain)

        timestamps = np.asarray([0, 100, 500]) / sampling_rate

        np.random.seed(50)  # Reset random number generator
        channel_state_info_no_gain = channel_no_gain.siso_impulse_response(timestamps)

        np.random.seed(50)  # Reset random number generator
        channel_state_info_gain = channel_gain.siso_impulse_response(timestamps)

        npt.assert_array_almost_equal(channel_state_info_gain, channel_state_info_no_gain * gain)

    def test_to_yaml(self) -> None:
        """Test YAML serialization dump validity."""
        pass

    def test_from_yaml(self) -> None:
        """Test YAML serialization recall validity."""
        pass

    def test_mimo(self) -> None:
        """
        Test the MIMO channel
        The following tests are performed

        1 - check output sizes
        2 - test MIMO output with known channel
        3 - check the channel impulse response
        4 - test antenna correlation
        :return:
        """
        pass

from tests.unit_tests.channel.test_channel import TestSyncOffset


class TestSyncoffsetNoInterpolationFilter(TestSyncOffset):

    def create_channel(self, sync_low: float, sync_high: float, seed: int = 42) -> None:
        sampling_rate = 1e3
        transmitter = Mock()
        receiver = Mock()
        transmitter.sampling_rate = sampling_rate
        receiver.sampling_rate = sampling_rate
        transmitter.num_antennas = 1
        receiver.num_antennas = 1

        channel_params = {
            'delays': np.zeros(1, dtype=float),
            'power_profile': np.ones(1, dtype=float),
            'scenario': Scenario(sampling_rate=1e3),
            'rice_factors': np.zeros(1, dtype=float),
            'active': True,
            'transmitter': transmitter,
            'receiver': receiver,
            'gain': 1.0,
            'doppler_frequency': 0.0,
            'num_sinusoids': 1,
            'sync_offset_low': sync_low,
            'sync_offset_high': sync_high,
            'random_generator': np.random.default_rng(seed=seed),
            'impulse_response_interpolation': False
        }

        ch = MultipathFadingChannel(**channel_params)
        return ch