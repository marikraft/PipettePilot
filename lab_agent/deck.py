"""
Deck setup and a plain-data snapshot of its state.

The snapshot is what the validator (and the LLM) gets to see. The LLM never reads the
robot directly; it only sees what this module chooses to report.
"""
from dataclasses import dataclass

from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import LiquidHandlerChatterboxBackend
from pylabrobot.resources import (
    STARLetDeck,
    TIP_CAR_480_A00,
    PLT_CAR_L5AC_A00,
    hamilton_96_tiprack_50uL,
    hamilton_96_tiprack_300uL,
    hamilton_96_tiprack_1000uL,
    cor_96_wellplate_360uL_Fb,
    set_volume_tracking,
    set_tip_tracking,
)


@dataclass
class Lab:
    lh: LiquidHandler
    tip_racks: dict  # nominal tip volume (uL) -> tip rack
    plates: dict     # plate name -> plate resource


async def build_lab(initial_volumes: dict[str, dict[str, float]] | None = None) -> Lab:
    """Simulated STARlet with three tip sizes and two 96-well plates.

    initial_volumes example: {"source": {"A1": 300, "A2": 300}}
    """
    set_volume_tracking(True)
    set_tip_tracking(True)

    lh = LiquidHandler(backend=LiquidHandlerChatterboxBackend(), deck=STARLetDeck())
    await lh.setup()

    tip_carrier = TIP_CAR_480_A00(name="tip_carrier")
    tip_carrier[0] = tips_50 = hamilton_96_tiprack_50uL(name="tips_50uL")
    tip_carrier[1] = tips_300 = hamilton_96_tiprack_300uL(name="tips_300uL")
    tip_carrier[2] = tips_1000 = hamilton_96_tiprack_1000uL(name="tips_1000uL")
    lh.deck.assign_child_resource(tip_carrier, rails=3)

    plate_carrier = PLT_CAR_L5AC_A00(name="plate_carrier")
    plate_carrier[0] = source = cor_96_wellplate_360uL_Fb(name="source")
    plate_carrier[1] = target = cor_96_wellplate_360uL_Fb(name="target")
    lh.deck.assign_child_resource(plate_carrier, rails=9)

    plates = {"source": source, "target": target}
    for plate_name, wells in (initial_volumes or {}).items():
        for well, volume in wells.items():
            plates[plate_name].get_well(well).tracker.set_volume(volume)

    return Lab(lh=lh, tip_racks={50: tips_50, 300: tips_300, 1000: tips_1000}, plates=plates)


def next_tip(lab: Lab, size_ul: int):
    """First spot in the rack of this size that still holds a tip, or None."""
    for spot in lab.tip_racks[size_ul].get_all_items():
        if spot.has_tip():
            return spot
    return None


def snapshot(lab: Lab) -> dict:
    """Current deck state as plain data. Only non-empty wells are listed, to keep it short."""
    plates = {}
    for name, plate in lab.plates.items():
        plates[name] = {
            "rows": "A-H",
            "columns": "1-12",
            "max_volume_ul": plate.get_well("A1").max_volume,
            "filled_wells": {
                w.name.split("_")[-1]: w.tracker.get_used_volume()
                for w in plate.get_all_items()
                if w.tracker.get_used_volume() > 0
            },
        }
    tips_left = {
        f"{size}uL": sum(1 for spot in rack.get_all_items() if spot.has_tip())
        for size, rack in lab.tip_racks.items()
    }
    return {"plates": plates, "tips_left": tips_left}
