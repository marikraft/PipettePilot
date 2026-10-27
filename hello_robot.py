"""
Day 0 sanity check: a simulated liquid handler doing one transfer, written by hand.
No AI yet. If this runs, your environment is ready.
"""
import asyncio

from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import LiquidHandlerChatterboxBackend
from pylabrobot.resources import (
    STARLetDeck,
    TIP_CAR_480_A00,
    PLT_CAR_L5AC_A00,
    hamilton_96_tiprack_1000uL,
    set_volume_tracking,
    cor_96_wellplate_360uL_Fb,
)


async def main():
    # Tell the simulator to keep track of how much liquid is in each well.
    set_volume_tracking(True)

    # 1. A simulated robot: it prints every command instead of moving hardware.
    lh = LiquidHandler(backend=LiquidHandlerChatterboxBackend(), deck=STARLetDeck())
    await lh.setup()

    # 2. Put labware on the deck: one tip rack and two 96-well plates.
    tip_carrier = TIP_CAR_480_A00(name="tip_carrier")
    tip_carrier[0] = tips = hamilton_96_tiprack_1000uL(name="tips")
    lh.deck.assign_child_resource(tip_carrier, rails=3)

    plate_carrier = PLT_CAR_L5AC_A00(name="plate_carrier")
    plate_carrier[0] = source = cor_96_wellplate_360uL_Fb(name="source")
    plate_carrier[1] = target = cor_96_wellplate_360uL_Fb(name="target")
    lh.deck.assign_child_resource(plate_carrier, rails=9)

    # 3. Fill the source well A1 with 200 uL of liquid (in the simulation's memory).
    source.get_well("A1").tracker.set_volume(200)

    # 4. One transfer: 50 uL from source A1 to target B1.
    await lh.pick_up_tips(tips["A1"])
    await lh.aspirate(source["A1"], vols=[50])
    await lh.dispense(target["B1"], vols=[50])
    await lh.drop_tips(tips["A1"])

    print("\nSource A1 now holds:", source.get_well("A1").tracker.get_used_volume(), "uL")
    print("Target B1 now holds:", target.get_well("B1").tracker.get_used_volume(), "uL")

    await lh.stop()


if __name__ == "__main__":
    asyncio.run(main())
