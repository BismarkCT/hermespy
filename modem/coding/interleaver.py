from typing import List
from parameters_parser.parameters_block_interleaver import ParametersBlockInterleaver
from modem.coding.encoder import Encoder

import numpy as np


class BlockInterleaver(Encoder):

    def __init__(self, params: ParametersBlockInterleaver, bits_in_frame: int) -> None:
        self.params = params
        self.bits_in_frame = bits_in_frame

    def encode(self, data_bits: List[np.array]) -> List[np.array]:
        encoded_bits: List[np.array] = []

        for block in data_bits:
            while block.size > 0:
                encoded_block = np.reshape(
                    block[:self.params.data_bits_k],
                    (self.params.M, self.params.N)
                )
                encoded_block = np.ravel(encoded_block.T)
                encoded_bits.append(encoded_block)
                block = block[self.params.data_bits_k:]

        encoded_bits.append(np.zeros(
            self.bits_in_frame
            - self.code_blocks * self.params.encoded_bits_n
        ))
        return encoded_bits

    def decode(self, encoded_bits: List[np.array]) -> List[np.array]:
        if encoded_bits[-1].size < self.params.encoded_bits_n:
            del encoded_bits[-1]

        decoded_bits = [
            np.ravel(
                np.reshape(
                    block,
                    (self.params.N, self.params.M)
                ).T
            ) for block in encoded_bits
        ]
        return decoded_bits

    @property
    def encoded_bits_n(self) -> int:
        """int: Number of encoded bits that the encoding of k data bits result in."""
        return self.params.encoded_bits_n

    @property
    def data_bits_k(self) -> int:
        """int: Number of bits that are to be encoded into n bits."""
        return self.params.data_bits_k

    @property
    def code_blocks(self) -> int:
        """int: Number of code blocks which are to encoded."""
        return int(np.floor(self.bits_in_frame / self.encoded_bits_n))

    @property
    def source_bits(self) -> int:
        """int: Number of bits to be generated by the source given n/k."""
        return int(self.code_blocks * self.data_bits_k)