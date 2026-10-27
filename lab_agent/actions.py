"""
The actions the system knows how to perform, as plain data.

Actions describe what should happen; they don't touch the robot. Keeping planning and
execution apart means a whole plan can be checked before the first movement.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Transfer:
    volume_ul: float
    source_plate: str
    source_well: str
    dest_plate: str
    dest_well: str

    def describe(self) -> str:
        return (f"Transfer {self.volume_ul:g} uL from {self.source_plate} {self.source_well} "
                f"to {self.dest_plate} {self.dest_well}")


def transfer(volume_ul, source_plate, source_well, dest_plate, dest_well) -> list[Transfer]:
    return [Transfer(volume_ul, source_plate, source_well.upper(), dest_plate, dest_well.upper())]


def distribute(volume_ul, source_plate, source_well, dest_plate, dest_wells) -> list[Transfer]:
    """Same volume from one well into several. One transfer (and one fresh tip) per destination."""
    return [Transfer(volume_ul, source_plate, source_well.upper(), dest_plate, w.upper())
            for w in dest_wells]
