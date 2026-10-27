"""
Deck setup and a plain-data snapshot of its state.

The snapshot is what the validator (and later the LLM) gets to see. The LLM never
reads the robot directly; it only sees what this module chooses to report.
"""
from dataclasses import dataclass

from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import LiquidHandlerChatterboxBackend
from pylabrobot.resources import (
    STARLetDeck,
    TIP_CAR_480_A00,
    PLT_CAR_L5AC_A00,
    hamilton_96_tiprack_1000uL,
    cor_96_wellplate_360uL_Fb,
    set_volume_tracking,
    set_tip_tracking,
)

TIP_MAX_UL = 1000  # nominal tip volume; the labware definition allows a little more for air gaps


@dataclass
class Lab:
    lh: LiquidHandler
    tips: object
    plates: dict  # plate name -> plate resource


async def build_lab(initial_volumes: dict[str, dict[str, float]] | None = None) -> Lab:
    """Set up a simulated STARlet with one tip rack and two 96-well plates.

    initial_volumes example: {"source": {"A1": 300, "A2": 300}}
    """
    set_volume_tracking(True)
    set_tip_tracking(True)

    lh = LiquidHandler(backend=LiquidHandlerChatterboxBackend(), deck=STARLetDeck())
    await lh.setup()

    tip_carrier = TIP_CAR_480_A00(name="tip_carrier")
    tip_carrier[0] = tips = hamilton_96_tiprack_1000uL(name="tips")
    lh.deck.assign_child_resource(tip_carrier, rails=3)

    plate_carrier = PLT_CAR_L5AC_A00(name="plate_carrier")
    plate_carrier[0] = source = cor_96_wellplate_360uL_Fb(name="source")
    plate_carrier[1] = target = cor_96_wellplate_360uL_Fb(name="target")
    lh.deck.assign_child_resource(plate_carrier, rails=9)

    plates = {"source": source, "target": target}
    for plate_name, wells in (initial_volumes or {}).items():
        for well, volume in wells.items():
            plates[plate_name].get_well(well).tracker.set_volume(volume)

    return Lab(lh=lh, tips=tips, plates=plates)


def next_tip(lab: Lab):
    """First tip spot that still holds a tip, or None if the rack is empty."""
    for spot in lab.tips.get_all_items():
        if spot.has_tip():
            return spot
    return None


def snapshot(lab: Lab) -> dict:
    """Current deck state as plain data: only non-empty wells, to keep it short."""
    plates = {}
    for name, plate in lab.plates.items():
        well = plate.get_well("A1")
        plates[name] = {
            "wells": 96,
            "max_volume_ul": well.max_volume,
            "filled_wells": {
                w.name.split("_")[-1]: w.tracker.get_used_volume()
                for w in plate.get_all_items()
                if w.tracker.get_used_volume() > 0
            },
        }
    tips_left = sum(1 for spot in lab.tips.get_all_items() if spot.has_tip())
    return {"plates": plates, "tips_left": tips_left, "tip_max_ul": TIP_MAX_UL}
