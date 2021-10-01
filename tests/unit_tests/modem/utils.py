from typing import List

import numpy as np


def flatten_blocks(bits: List[np.array]) -> np.array:
    flattened_blocks = np.array([])
    for block in bits:
        flattened_blocks = np.append(
            flattened_blocks,
            block
        )
    return flattened_blocks

def assert_frame_equality(
        data_bits: List[np.array], encoded_bits: List[np.array]) -> None:
    for data_block, encoded_block in zip(data_bits, encoded_bits):
        np.testing.assert_array_equal(data_block, encoded_block)
