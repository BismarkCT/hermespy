from __future__ import annotations
from typing import Type
from ruamel.yaml import SafeConstructor, SafeRepresenter, Node
import numpy as np

from coding.encoder import Encoder


class RepetitionEncoder(Encoder):
    """Exemplary implementation of a repetition channel encoder.

    This shows how a new encoder is to implemented. It's a three-step process:
    """

    yaml_tag = 'Repetition'
    __bit_block_size: int
    __repetitions: int
    __code_block_size: int

    def __init__(self,
                 bit_block_size: int = 32,
                 repetitions: int = 2,
                 code_block_size: int = 70) -> None:
        """Object initialization.

        Args:
            bit_block_size (int, optional): The number of input bits per data block.
            repetitions (int, optional): The number of times the input bit block is repeated.
            code_block_size (int, optional): The number of output bits per encoded data block.

        Raises:
            ValueError: If `bit_block_size` times `repetitions` is smaller than `code_block_size`.
        """

        # Default parameters
        Encoder.__init__(self)
        self.bit_block_size = bit_block_size
        self.repetitions = repetitions
        self.code_block_size = code_block_size

        if self.bit_block_size * repetitions > self.code_block_size:
            raise ValueError("The number of generated bits must be smaller or equal to the configured code block size")

    def encode(self, bits: np.array) -> np.array:
        """Encodes a single block of bits.

        Args:
            bits (np.array): A block of bits to be encoded by this `Encoder`.

        Returns:
            np.array: The encoded `bits` block.
        """

        num_code_bits = self.bit_block_size * self.repetitions
        num_padding_bits = self.code_block_size - num_code_bits

        code = np.empty(self.code_block_size)
        code[:num_code_bits] = np.repeat(bits, self.repetitions)
        code[-num_padding_bits:] = np.zeros(num_padding_bits, dtype=int)

        return code

    def decode(self, encoded_bits: np.array) -> np.array:
        """Decodes a single block of encoded bits.

        Args:
            encoded_bits (np.array): An encoded block of bits.

        Returns:
            np.array: A decoded block of bits.
        """

        code = encoded_bits[(self.bit_block_size * self.repetitions):].reshape((self.repetitions, self.bit_block_size))
        bits = (np.sum(code, axis=0) / self.repetitions) >= 0.5

        return bits.astype(int)

    @property
    def bit_block_size(self) -> int:
        """The number of resulting bits after decoding / the number of bits required before encoding.

        Returns:
            int: The number of bits.
        """

        return self.__bit_block_size

    @bit_block_size.setter
    def bit_block_size(self, num_bits: int) -> None:
        """Configure the number of resulting bits after decoding / the number of bits required before encoding.

        Args:
            num_bits (int): The number of bits.

        Raises:
            ValueError: If `num_bits` is smaller than one.
        """

        if num_bits < 1:
            raise ValueError("Number data bits must be greater or equal to one")

        self.__bit_block_size = num_bits

    @property
    def code_block_size(self) -> int:
        """The number of resulting bits after encoding / the number of bits required before decoding.

        Returns:
            int: The number of bits.
        """

        return self.__code_block_size

    @code_block_size.setter
    def code_block_size(self, num_bits: int) -> None:
        """Configure the number of resulting bits after encoding / the number of bits required before decoding.

        Args:
            num_bits (int): The number of bits.

        Raises:
            ValueError: If `num_bits` is smaller than one.
        """

        if num_bits < 1:
            raise ValueError("Number data bits must be greater or equal to one")

        self.__code_block_size = num_bits

    @property
    def repetitions(self) -> int:
        """The number of bit repetitions during coding.

        Returns:
            int: The number of bits.
        """

        return self.__repetitions

    @repetitions.setter
    def repetitions(self, num: int) -> None:
        """Configure the number of bit repetitions during coding.

        Args:
            num (int): The number of repetitions.

        Raises:
            ValueError: If `num` is smaller than one.
        """

        if num < 1:
            raise ValueError("The number of data bit repetitions must be at least one")

        self.__repetitions = num

    @classmethod
    def to_yaml(cls: Type[RepetitionEncoder], representer: SafeRepresenter, node: RepetitionEncoder) -> Node:
        """Serialize a `RepetitionEncoder` to YAML.

        Args:
            representer (SafeRepresenter):
                A handle to a representer used to generate valid YAML code.
                The representer gets passed down the serialization tree to each node.

            node (RepetitionEncoder):
                The `RepetitionEncoder` instance to be serialized.

        Returns:
            Node:
                The serialized YAML node.
        """

        state = {
            "bit_block_size": node.bit_block_size,
            "repetitions": node.repetitions,
            "code_block_size": node.code_block_size,
        }

        return representer.represent_mapping(cls.yaml_tag, state)

    @classmethod
    def from_yaml(cls: Type[RepetitionEncoder], constructor: SafeConstructor, node: Node) -> RepetitionEncoder:
        """Recall a new `RepetitionEncoder` from YAML.

        Args:
            constructor (SafeConstructor):
                A handle to the constructor extracting the YAML information.

            node (Node):
                YAML node representing the `RepetitionEncoder` serialization.

        Returns:
            RepetitionEncoder:
                Newly created `RepetitionEncoder` instance.

        Note that the created instance is floating by default.
        """

        state = constructor.construct_mapping(node)
        return cls(**state)