"""
    This example is to show the estimated mean and confidence across the number of samples 
"""

# Imports the necessary libraries
import numpy as np
import numpy.random as rnd
from math import exp, sqrt
from scipy.constants import pi
from scipy.stats import norm

# Allowed difference between true and estimated RV mean
tolerance = .1

# Probability that the tolerance was achieved
confidence = .1

# Minimum numbers of samples
min_num_samples = 50

# Define variables
samples = np.empty(0, dtype=float)
sample_mean = np.nan
confidence_estimate = np.nan
required_num_samples = min_num_samples

# Berry-Esseen constants
C_0 = .4785
C_1 = 30.2338

# Funtion responsable to return a smallest item between C_0 and C_1 x (1 + |x|)^(-3)


def cbe(x):
    return min(C_0, C_1 * (1 + abs(x)) ** -3)


for n in range(1, 1000000):

    samples = np.append(samples, rnd.standard_normal())

    if n < required_num_samples:
        continue

    # Compute moments
    sample_mean = np.mean(samples)
    unbiased_samples = samples - sample_mean
    sigma_moment = sqrt(np.sum(unbiased_samples ** 2) / n)
    beta_bar_moment = np.sum(np.abs(unbiased_samples)
                             ** 3) / (n * sigma_moment ** 3)
    beta_hat_moment = np.sum(unbiased_samples ** 3) / (n * sigma_moment ** 3)
    kappa_moment = np.sum(unbiased_samples ** 4) / (n * sigma_moment ** 4) - 3

    # Estimate the confidence
    sample_sqrt = sqrt(n)
    sigma_tolerance = sample_sqrt * tolerance / sigma_moment
    sigma_tolerance_squared = sigma_tolerance ** 2
    kappa_term = 4 * (2 / (n - 1) + kappa_moment / n)

    confidence_bound = 2 * (1 - norm.cdf(sigma_tolerance)) \
        + 2 * cbe(sigma_tolerance) * beta_bar_moment / sample_sqrt * min(1, kappa_term) \
        + abs(sigma_tolerance_squared - 1) * abs(beta_hat_moment) / (exp(.5 * sigma_tolerance_squared)
                                                                     * 3 * sqrt(2 * pi * n) * sigma_moment ** 3) \
        * max(1 - kappa_term, 0)

    if confidence_bound < confidence:
        break

    else:
        required_num_samples = 2 * n
        print(required_num_samples)

# Show the results
print(f"Required {required_num_samples} samples to estimate the mean to {sample_mean} with a confidence of {confidence_estimate}")
