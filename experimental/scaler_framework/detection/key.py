"""
Key / scale estimation using the Krumhansl-Schmuckler algorithm.

Correlates a pitch-class histogram against perceptual key profiles
from Krumhansl & Kessler (1982).
"""

import numpy as np

from scaler_framework.theory.scale import KeyEstimate


class KeyEstimator:
    """
    Estimates key from a 12-element pitch class histogram.

    Usage:
        estimator = KeyEstimator()
        keys = estimator.estimate(histogram, top_n=5)
        print(keys[0])  # "C major (92%)"
    """

    # Krumhansl-Kessler profiles
    MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                               2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                               2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    def estimate(self, pitch_histogram: np.ndarray, top_n: int = 5) -> list[KeyEstimate]:
        """
        Correlate observed pitch histogram against all 24 major/minor keys.

        Args:
            pitch_histogram: 12-element array of pitch class weights.
            top_n: Number of top key estimates to return.

        Returns:
            Sorted list of KeyEstimate (best first).
        """
        results = []

        for root in range(12):
            rotated = np.roll(pitch_histogram, -root)

            for scale_type, profile in [("major", self.MAJOR_PROFILE),
                                         ("natural_minor", self.MINOR_PROFILE)]:
                corr = np.corrcoef(rotated, profile)[0, 1]
                results.append(KeyEstimate(
                    root=root,
                    scale_type=scale_type,
                    confidence=max(0.0, float(corr)),
                ))

        results.sort(key=lambda k: k.confidence, reverse=True)
        return results[:top_n]
