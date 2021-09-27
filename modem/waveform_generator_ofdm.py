from typing import List, Tuple
from enum import IntEnum
import numpy as np
from scipy import signal

from modem import Modem
from modem.waveform_generator import WaveformGenerator
from modem.tools.psk_qam_mapping import PskQamMapping
from modem.tools.mimo import Mimo


class WaveformGeneratorOfdm(WaveformGenerator):
    """This module provides a class for a generic OFDM modem, with a flexible frame configuration.

    The following features are supported:
    - The modem can transmit or receive custom-defined frames. (see class ParametersOfdm). The frame may contain UL/DL data
    symbols, null carriers, pilot subcarriers, reference signals and guard intervals.
    - SC-FDMA can also be implemented with a precoder.
    - Subcarriers can be modulated with BPSK/QPSK/16-/64-/256-QAM.
    - cyclic-prefix OFDM are supported.

    This implementation has currently the following limitations:
    - all subcarriers use the same modulation scheme
    - reference is a random
    - ideal channel estimation assumed
    - pilot not implemented
    """
    
    # YAML tag
    yaml_tag = "OFDM"

    # Modulation parameters
    __subcarrier_spacing: float
    __fft_size: int
    __numb_occupied_subcarriers: int
    __cp_ratio: np.array
    __precoding: str
    __bits_in_frame: int
    __dc_suppression: bool

    # Receiver parameters
    __channel_estimation: str
    __equalization: str

    # Frame parameters
    __frame_guard_interval: float
    __frame_structure: List[FrameElement]
    __ofdm_symbol_resources_mapping: List[List[ResourcePattern]]
    __ofdm_symbol_configs: List[OfdmSymbolConfig]

    def __init__(self,
                 modem: Modem = None,
                 sampling_rate: float = None,
                 oversampling_factor: float = None) -> None:
        """Object initialization."""

        WaveformGenerator.__init__(self,
                                   modem=modem,
                                   sampling_rate=sampling_rate,
                                   oversampling_factor=oversampling_factor)

        # Default parameters
        self.__subcarrier_spacing = 0.0
        self.__fft_size = 1
        self.__num_occupied_subcarriers = 1
        self.__cp_ratio = np.array([])
        self.__precoding = ""
        self.__bits_in_frame = 0
        self.__dc_suppression = True
        self.__channel_estimation = ""
        self.__equalization = ""
        self.__frame_guard_interval = 0.0
        self.__frame_structure = []
        self.__ofdm_symbol_resources_mapping = []
        self.__ofdm_symbol_configs = []

        self._samples_in_frame_no_oversampling = 0

        self._mapping = PskQamMapping(self.param.modulation_order)


        self._mimo = Mimo(mimo_method=self.param.mimo_scheme,
                          number_tx_antennas=self.param.number_tx_antennas,
                          number_of_streams=self.param.number_streams)
        self._resource_element_mapping: np.array = self._calculate_resource_element_mapping()
        self._samples_in_frame_no_oversampling, self._cyclic_prefix_overhead = (
            self._calculate_samples_in_frame()
        )

    def _calculate_samples_in_frame(self) -> Tuple[int, float]:
        samples_in_frame_no_oversampling = 0
        number_cyclic_prefix_samples = 0
        number_of_data_samples = 0

        for frame_element in self.param.frame_structure:
            if isinstance(frame_element, GuardInterval):
                samples_in_frame_no_oversampling += frame_element.no_samples
            else:
                samples_in_frame_no_oversampling += frame_element.cyclic_prefix_samples
                number_cyclic_prefix_samples += frame_element.cyclic_prefix_samples

                samples_in_frame_no_oversampling += frame_element.no_samples
                number_of_data_samples += frame_element.no_samples

        cyclic_prefix_overhead = (number_of_data_samples + number_cyclic_prefix_samples) / number_of_data_samples

        return samples_in_frame_no_oversampling, cyclic_prefix_overhead

    def _calculate_resource_element_mapping(self) -> np.array:
        initial_index = self.param.fft_size - \
            int(np.ceil(self.param.number_occupied_subcarriers / 2))
        resource_element_mapping: np.array = np.arange(
            initial_index, self.param.fft_size)
        final_index = int(np.floor(self.param.number_occupied_subcarriers / 2))
        resource_element_mapping = np.append(
            resource_element_mapping, np.arange(
                self.param.dc_suppression, final_index + self.param.dc_suppression))
        return resource_element_mapping

    @property
    def subcarrier_spacing(self) -> float:
        """Spacing between individual subcarriers.

        Returns:
            float:
                Subcarrier spacing in Hz."""

        return self.__subcarrier_spacing

    @subcarrier_spacing.setter
    def subcarrier_spacing(self, spacing: float) -> None:
        """Modify spacing between individual subcarriers.

        Args:
            spacing (float): The new subcarrier spacing in Hz.

        Raises:
            ValueError: If the `spacing` is less than zero.
        """

        if spacing < 0.0:
            raise ValueError("Subcarrier spacing must be greater or equal to zero")

        self.__subcarrier_spacing = spacing

    @property
    def fft_size(self) -> int:
        """Number of fft windows?

        return:
            int: Number of FFT windows.
        """

        return self.__fft_size

    @fft_size.setter
    def fft_size(self, size: int) -> None:
        """Modify number of FFT windows.

        Args:
             size (int): New Number of FFT windows.

        Raises:
            ValueError: If `size` is smaller than one.
        """

        if size < 0:
            raise ValueError("FFT size must be greater than zero.")

        if size > self.__number_occupied_subcarriers:
            raise ValueError("FFT size may not be larger than number of occupied subcarriers")

        self.__fft_size = size

    @property
    def num_occupied_subcarriers(self) -> int:
        """Number of occupied subcarriers.

        return:
            int: Number of occupied subcarriers.
        """

        return self.__num_occupied_subcarriers

    @num_occupied_subcarriers.setter
    def num_occupied_subcarriers(self, num: int) -> None:
        """Modify the number of occupied subcarriers.

        Args:
             num (int): New number of occupied subcarriers.

        Raises:
            ValueError: If `num` is larger than the `fft_size`.
        """

        if self.fft_size < num:
            raise ValueError("Number of occupied subcarriers may not be larger than the FFT size")

        self.__num_occupied_subcarriers = num



    @property
    def samples_in_frame(self) -> int:
        """int: Returns read-only samples_in_frame"""
        return self._samples_in_frame_no_oversampling * self.param.oversampling_factor

    @property
    def bits_in_frame(self) -> int:
        """int: Returns read-only bits_in_frame"""
        return self.param.bits_in_frame

    @property
    def cyclic_prefix_overhead(self) -> float:
        """int: Returns read-only cyclic_prefix_overhead"""
        return self._cyclic_prefix_overhead

    # property definitions END
    #############################################

    def create_frame(self, timestamp: int, data_bits: np.array) -> Tuple[np.ndarray, int, int]:
        """Creates a modulated complex baseband signal for a whole transmit frame.

        The signal will be modulated based on the bits generated by "self.source".

        Args:
            timestamp(int): timestamp (in samples) of initial sample in frame
            data_bits (np.array):
                Flattened blocks, whose bits are supposed to fit into this frame.

        Returns:
            (np.ndarray, int, int):
            
            `output_signal(numpy.ndarray)`: 2D array containing the transmitted signal with
            (self.param.number_tx_antennas x self.samples_in_frame) elements

            `timestamp(int)`: current timestamp (in samples) of the following frame

            `initial_sample_num(int)`: sample in which this frame starts (equal to initial timestamp)
        """
        output_signal: np.ndarray = np.zeros(
            (self.param.number_tx_antennas, self._samples_in_frame_no_oversampling),
            dtype=complex)

        data_symbols_in_frame = self._mapping.get_symbols(data_bits)

        sample_index = 0
        for frame_element in self.param.frame_structure:
            if isinstance(frame_element, GuardInterval):
                sample_index += frame_element.no_samples
            else:
                resource_elements, data_symbols_in_frame = self.map_resources(
                    frame_element.resource_types, data_symbols_in_frame)

                sample_index, output_signal = self.create_ofdm_symbol_time_domain(
                    sample_index, resource_elements, frame_element, output_signal)

        initial_sample_num = timestamp
        timestamp += self.samples_in_frame

        if self.param.oversampling_factor > 1:
            output_signal = signal.resample_poly(
                output_signal, self.param.oversampling_factor, 1, axis=1)
        return output_signal, timestamp, initial_sample_num

    def create_ofdm_symbol_time_domain(self,
                                       first_sample_idx: int,
                                       resource_elements: np.array,
                                       ofdm_symbol_config: OfdmSymbolConfig,
                                       output_signal: np.ndarray) -> Tuple[int, np.ndarray]:
        """Creates one ofdm symbol in time domain.

        Args:
            first_sample_idx (int): first sample index of frame
            resource_elements (np.array): resource elements already mapped to subcarriers.
            ofdm_symbol_config (OfdmSymbolConfig): Configuration of ofdm symbol to create.
            output_signal (np.ndarray): frame signal of shape `N_tx_antennas x samples`.

        Returns:
            (int, np.ndarray):
                `int`: updated sampleindex
                `np.ndarray`: updated output signal
        """
        sample_index = first_sample_idx
        freq_domain: np.ndarray = np.zeros(
            (self.param.number_tx_antennas, self.param.fft_size),
            dtype=complex)

        freq_domain[:, self._resource_element_mapping] = resource_elements

        ofdm_symbol: np.ndarray = np.fft.ifft(freq_domain, norm='ortho')

        # prepend cyclic prefix if necessary
        if ofdm_symbol_config.cyclic_prefix_samples:
            ofdm_symbol = np.hstack(
                (ofdm_symbol[:, -ofdm_symbol_config.cyclic_prefix_samples:], ofdm_symbol))

        # update samples
        no_samples_ofdm_symbol = ofdm_symbol.shape[1]
        output_signal[:, sample_index:sample_index + no_samples_ofdm_symbol] = ofdm_symbol
        sample_index += no_samples_ofdm_symbol

        return sample_index, output_signal

    def map_resources(self,
                      res_mapping: List[ResourcePattern],
                      data_symbols_in_frame: np.array) -> Tuple[np.ndarray, np.array]:
        """Maps data symbols to subcarriers.

        Args:
            res_mapping(List(ResourcePattern)): Describes which sc are data, reference and null.
            data_symbols_in_frame(np.array): Data symbols to distribute.

        Returns:
            (np.ndarray, np.ndarray):
                `np.ndarray`: Resources in current ofdm symbol in f domain, rows denote tx ant.
                `np.ndarray`: Remaining data symbols.
        """
        resource_elements = np.zeros(
            (self.param.number_tx_antennas, self.param.number_occupied_subcarriers),
            dtype=complex
        )

        #############################################################################
        # calculate indices for data and pilot resource elements in this OFDM symbol
        subcarrier_idx = 0
        data_idxs: np.array = np.array([], dtype=int)
        ref_idxs: np.array = np.array([], dtype=int)
        null_idxs: np.array = np.array([], dtype=int)

        for res_pattern in res_mapping:
            for pattern_el_idx in range(res_pattern.number):
                for res in res_pattern.MultipleRes:
                    if res.ResourceType == ResourceType.DATA:
                        data_idxs = np.append(data_idxs, np.arange(subcarrier_idx, subcarrier_idx + res.number))
                    elif res.ResourceType == ResourceType.REFERENCE:
                        ref_idxs = np.append(ref_idxs, np.arange(subcarrier_idx, subcarrier_idx + res.number))
                    elif res.ResourceType == ResourceType.NULL:
                        null_idxs = np.append(null_idxs, np.arange(subcarrier_idx, subcarrier_idx + res.number))

                    subcarrier_idx += res.number

        ######################################
        # fill out resource elements with data
        number_data_res_el = data_idxs.size
        number_data_symbols = number_data_res_el * self.param.number_streams

        data_symbols: np.array = data_symbols_in_frame[:number_data_symbols]
        data_symbols_in_frame = data_symbols_in_frame[number_data_symbols:]

        data_symbols = self._mimo.encode(data_symbols)
        if self.param.precoding == "DFT":
            resource_elements[:, data_idxs] = np.fft.fft(data_symbols, norm='ortho')
        else:
            resource_elements[:, data_idxs] = data_symbols

        #######################################################
        # fill out resource elements with random pilot symbols
        size = (self.param.number_tx_antennas, ref_idxs.size)
        resource_elements[:, ref_idxs] = (
            (self._rand.standard_normal(size) + 1j * self._rand.standard_normal(size))
            / np.sqrt(2) / np.sqrt(self.param.number_tx_antennas)
        )

        # fill out resource elements with null carriers
        resource_elements[:, null_idxs] = 0

        return resource_elements, data_symbols_in_frame

    def receive_frame(self,
                      rx_signal: np.ndarray,
                      timestamp_in_samples: int,
                      noise_var: float) -> Tuple[List[np.ndarray], np.ndarray]:
        """Demodulates the signal for a whole received frame.

        This method extracts a signal frame from 'rx_signal' and demodulates it according to
        the frame and modulation parameters.

        Args:
            rx_signal(numpy.ndarray):
                N x S array containg the received signal, with N the number of receive antennas
                and S the number of samples left in the drop.
            timestamp_in_samples(int):
                timestamp of initial sample in received signal, relative to the first sample in
                the simulation drop.
            noise_var (float): noise variance (for equalization).

        Returns:
            (list[np.ndarray], np.ndarray):
                `list[numpy.ndarray]`: 
                    list of detected blocks of bits.
                `numpy.ndarray`:
                    N x S' array containing the remaining part of the signal, after this frame was
                    demodulated.  S' = S - self.samples_in_frame
        """
        if rx_signal.shape[1] < self.samples_in_frame:
            bits = None
            rx_signal = np.array([])
        else:
            bits = np.array([])
            frame_signal = rx_signal[:, :self.samples_in_frame]
            channel_estimation = self.channel_estimation(
                rx_signal, timestamp_in_samples)

            rx_signal = rx_signal[:, self.samples_in_frame:]
            if self.param.oversampling_factor > 1:
                frame_signal = signal.decimate(
                    frame_signal, self.param.oversampling_factor)

            for frame_element_def in self.param.frame_structure:
                frame_element_samples = frame_element_def.no_samples
                if isinstance(frame_element_def, OfdmSymbolConfig):
                    # get channel estimation for this symbol
                    channel_in_freq_domain = channel_estimation[:, :, :, 0]

                    if channel_in_freq_domain.size:
                        channel_estimation = channel_estimation[:, :, :, 1:]

                    frame_element_samples += frame_element_def.cyclic_prefix_samples

                    bits_in_ofdm_symbol = self.get_bits_from_ofdm_symbol(
                        frame_element_def,
                        frame_signal[:, frame_element_def.cyclic_prefix_samples:],
                        channel_in_freq_domain,
                        noise_var
                    )
                    bits = np.append(bits, bits_in_ofdm_symbol)

                frame_signal = frame_signal[:,
                                            frame_element_samples:]
                timestamp_in_samples += frame_element_samples * \
                    self.param.oversampling_factor
        return list([bits]), rx_signal

    def get_bits_from_ofdm_symbol(
            self,
            ofdm_symbol_config: OfdmSymbolConfig,
            frame_signal: np.ndarray,
            channel_in_freq_domain: np.ndarray,
            noise_var: float) -> np.ndarray:
        """Detects the bits that are contained in an ofdm symbol in time domain.

        Args:
            ofdm_symbol_config(OfdmSymbolConfig): Configuration of current ofdm symbol.
            frame_signal(numpy.ndarray): array with the received signal in the whole remaining frame
            channel_in_freq_domain(np.ndarray):
                channel frequency response estimation. It should be a np.ndarray of shape
                fft_size x #rx_antennas x #tx_antennas
            noise_var(float): noise variance.

        Returns:
            Vector containing the detected bits for this particular symbol.
        """
        ofdm_symbol_resources: np.ndarray = frame_signal[:, :self.param.fft_size]
        symbols, noise_var = self.demodulate_ofdm_symbol(
            ofdm_symbol_config,
            ofdm_symbol_resources,
            channel_in_freq_domain,
            noise_var
        )

        symbols = symbols.flatten('F')
        bits_in_ofdm_symbol = self._mapping.detect_bits(symbols)

        return bits_in_ofdm_symbol

    def demodulate_ofdm_symbol(self, ofdm_symbol_config: OfdmSymbolConfig, ofdm_symbol_resources: np.ndarray,
                               channel_in_freq_domain: np.ndarray, noise_var: float) -> np.ndarray:
        """Demodulates  a single OFDM symbol

        This method performs the FFT of the time-domain signal and equalizes it with knowledge of the channel frequency
        response.

        Args:
            ofdm_symbol_config(OfdmSymbolConfig): Config of ofdm symbol to demodulate.
            ofdm_symbol_resources(numpy.ndarray):
                contains information the received OFDM symbol in time domain of shape
                #rx_antennas x #fft_size
            channel_in_freq_domain(numpy.ndarray):
                channel estimate in the frequency domain of shape
                fft_size x #rx_antennas x #tx_antennas
            noise_var(float): noise variance.

        Returns:
            (numpy.ndarray, numpy.ndarray)
                'data_symbols(numpy.ndarray)': estimate of the frequency-domain symbols at the data subcarriers
                'noise_var(numpy.ndarray)': noise variance of demodulated symbols

        """
        channel_in_freq_domain = np.moveaxis(channel_in_freq_domain, 0, -1)

        ofdm_symbol_resources_f = np.fft.fft(ofdm_symbol_resources, norm='ortho')
        data_symbols = ofdm_symbol_resources_f[:, self._resource_element_mapping]
        channel_in_freq_domain = channel_in_freq_domain[:, :, self._resource_element_mapping]

        data_symbols = self.discard_reference_symbols(ofdm_symbol_config, data_symbols)

        channel_in_freq_domain_reduced = np.zeros(
            (
                self.param.number_rx_antennas,
                self.param.number_tx_antennas,
                data_symbols.shape[1],
            ),
            dtype=complex
        )

        for rx_antenna_idx in range(self.param.number_rx_antennas):
            channel_in_freq_domain_reduced[rx_antenna_idx, :, :] = self.discard_reference_symbols(
                ofdm_symbol_config,
                channel_in_freq_domain[rx_antenna_idx, :, :],
            )

        channel_in_freq_domain = channel_in_freq_domain_reduced
        data_symbols, channel_in_freq_domain, noise_var = \
            self._mimo.decode(data_symbols, channel_in_freq_domain, noise_var)

        if self.param.equalization == "MMSE":
            SNR = (channel_in_freq_domain *
                   np.conj(channel_in_freq_domain))**2 / noise_var
            equalizer = 1 / channel_in_freq_domain * (SNR / (SNR + 1))
        else:
            # ZF equalization considering perfect channel state information
            # (SISO only)
            equalizer = 1 / channel_in_freq_domain

        noise_var = noise_var * np.abs(equalizer) ** 2
        data_symbols = data_symbols * equalizer

        if self.param.precoding == "DFT":
            data_symbols = np.fft.ifft(data_symbols, norm='ortho')

            dftmtx = np.fft.fft(np.eye(data_symbols.size), norm='ortho')
            noise_var = dftmtx @ np.diag(noise_var.flatten()) @ dftmtx.T.conj()

        return data_symbols, noise_var

    def discard_reference_symbols(self,
                                  ofdm_symbol_config: OfdmSymbolConfig,
                                  ofdm_symbol_resources: np.ndarray) -> np.ndarray:
        """Discards symbols except data symbols in ofdm symbol.

        Args:
            ofdm_symbol_config(OfdmSymbolConfig): Config that defines the resource element mapping.
            ofdm_symbol_resources(np.ndarray): subcarriers of the frame.

        Returns:
            np.ndarray: Data subcarriers
        """

        data_resources_indices: np.array = np.array([], dtype=int)
        symbol_idx = 0
        for pattern in ofdm_symbol_config.resource_types:
            for pattern_el_idx in range(pattern.number):
                for res in pattern.MultipleRes:
                    if res.ResourceType == ResourceType.DATA:
                        data_resources_indices = np.append(
                            data_resources_indices,
                            np.arange(symbol_idx, symbol_idx + res.number))
                    symbol_idx += res.number
        return ofdm_symbol_resources[:, data_resources_indices]

    def channel_estimation(self, rx_signal: np.ndarray,
                           timestamp_in_samples: int) -> np.ndarray:
        """Performs channel estimation

        This methods estimates the frequency response of the channel for all OFDM symbols in a frame. The estimation
        algorithm is defined in the parameter variable `self.param`.
        Currently only ideal channel estimation is available, either considering the channel state information (CSI)
        only at the beginning/middle/end of the frame (estimation_type='IDEAL_PREAMBLE'/'IDEAL_MIDAMBLE'/
        'IDEAL_POSTAMBLE'), or at every OFDM symbol ('IDEAL').
        Ideal channel estimation extracts the CSI directly from the channel,a and does not use the received signal.

        Args:
            rx_signal(numpy.ndarray): time-domain samples of the received signal over the whole frame
            timestamp_in_samples(int): sample index inside the drop of the first sample in frame

        Returns:
            numpy.ndarray:
                channel estimate in the frequency domain. It is a N x R x T x K array, with N
                the FFT size and K the number of data OFDM symbols in the frame.
                R denotes the number of receiving antennas and T of the transmitting
                antennas.
        """

        if self.param.channel_estimation == 'IDEAL':  # ideal channel estimation at each transmitted OFDM symbol
            channel_in_freq_domain = np.empty(
                (self.param.fft_size,
                 self._channel.number_rx_antennas,
                 self._channel.number_tx_antennas,
                 0),
                dtype=complex
            )
            for frame_element in self.param.frame_structure:

                if isinstance(frame_element, OfdmSymbolConfig):
                    # get channel estimation in frequency domain
                    channel_timestamp = np.array(
                        timestamp_in_samples / self.param.sampling_rate)
                    channel_in_freq_domain = np.concatenate(
                        (channel_in_freq_domain,
                         self.get_ideal_channel_estimation(channel_timestamp)),
                        axis=3)
                    samples_in_element = frame_element.no_samples + frame_element.cyclic_prefix_samples
                else:
                    samples_in_element = frame_element.no_samples

                timestamp_in_samples += samples_in_element * self.param.oversampling_factor

        else:  # self.param == 'IDEAL_PREAMBLE', 'IDEAL_MIDAMBLE', 'IDEAL_POSTAMBLE':
            # ideal estimation at a single instant at each frame
            number_of_data_symbols = sum(isinstance(frame_element, OfdmSymbolConfig)
                                         for frame_element in self.param.frame_structure)

            if self.param.channel_estimation == 'IDEAL_PREAMBLE':
                channel_timestamp = np.array(
                    timestamp_in_samples / self.param.sampling_rate)
            elif self.param.channel_estimation == 'IDEAL_MIDAMBLE':
                channel_timestamp = np.array(
                    (timestamp_in_samples + self.samples_in_frame / 2) / self.param.sampling_rate)
            elif self.param.channel_estimation == 'IDEAL_POSTAMBLE':
                channel_timestamp = np.array(
                    (timestamp_in_samples + self.samples_in_frame) / self.param.sampling_rate)
            else:
                raise ValueError('invalid channel estimation type')
            channel_in_freq_domain = np.tile(
                self.get_ideal_channel_estimation(channel_timestamp),
                number_of_data_symbols)

        return channel_in_freq_domain

    def get_ideal_channel_estimation(
            self, channel_timestamp: np.array) -> np.ndarray:
        """returns ideal channel estimation

        This method extracts the frequency-domain response from a known channel impulse response. The channel is the one
        from `self.channel`.

        Args:
            channel_timestamp(np.array): timestamp (in seconds) at which the channel impulse response should be
                measured

        Returns:
            np.ndarray:
                channel in freqence domain in shape `FFT_SIZE x #rx_antennas x #tx_antennas
        """

        channel_in_freq_domain_MIMO = np.zeros(
            (self.param.fft_size * self.param.oversampling_factor,
             self._channel.number_rx_antennas,
             self._channel.number_tx_antennas,
             1),
            dtype=complex
        )
        cir = self._channel.get_impulse_response(channel_timestamp)

        for rx_antenna_idx in range(self._channel.number_rx_antennas):
            for tx_antenna_idx in range(self._channel.number_tx_antennas):
                channel_in_freq_domain_MIMO[:, rx_antenna_idx, tx_antenna_idx, 0] = (
                    np.fft.fft(
                        cir[:, rx_antenna_idx, tx_antenna_idx].ravel(),
                        n=self.param.fft_size * self.param.oversampling_factor
                    )
                )

        if self.param.oversampling_factor > 1:
            channel_in_freq_domain_MIMO = np.delete(
                channel_in_freq_domain_MIMO,
                slice(int(self.param.fft_size / 2), -int(self.param.fft_size / 2)),
                axis=0
            )

        return channel_in_freq_domain_MIMO

    def get_bit_energy(self) -> float:
        """returns the theoretical (discrete) bit energy.

        Returns:
            float:
                raw bit energy. For the OFDM signal, the average bit energy of all data symbols, including
                the cyclic prefix overhead, is considered.
        """

        return self.param.oversampling_factor / \
            self._mapping.bits_per_symbol * self._cyclic_prefix_overhead

    def get_symbol_energy(self) -> float:
        """returns the theoretical symbol energy.

        Returns:
            float:
                raw symbol energy. For the OFDM signal, the average energy of a data resource element,
                including the cyclic prefix overhead, is considered.
        """

        return self.param.oversampling_factor * self._cyclic_prefix_overhead

    def get_power(self) -> float:
        return self.param.number_occupied_subcarriers / self.param.fft_size
