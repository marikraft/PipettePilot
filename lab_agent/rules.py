"""
Lab practice rules used by the validator and the executor.

These are rules of thumb, not physical limits, and they vary between labs and protocols,
so they live here as parameters rather than buried in the validation code.
"""

# Fraction of a well's current volume that can't be reliably aspirated
# (10% is a common guideline: from 100 uL, expect to recover about 90 uL).
DEAD_VOLUME_FRACTION = 0.10

# Typical working range for a 360 uL well is roughly 100-300 uL.
# Filling above this risks splashing and cross-contamination when the plate moves.
WORKING_MAX_FILL_UL = 300

# Accuracy drops below roughly 10% of a tip's nominal volume.
TIP_MIN_FRACTION = 0.10

# Tip sizes on the deck, smallest first.
TIP_SIZES_UL = [50, 300, 1000]


def select_tip(volume_ul: float) -> int | None:
    """Smallest tip that can hold the volume and still pipette it accurately."""
    for size in TIP_SIZES_UL:
        if TIP_MIN_FRACTION * size <= volume_ul <= size:
            return size
    return None
