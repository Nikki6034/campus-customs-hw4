"""Size guidance for Campus Customs unisex tops.

The catalogue uses alpha sizes XS–XXL. This module holds a standard unisex
size chart (body chest, in inches and cm, with US and UK labels) and a simple
recommendation from a shopper's height and weight. It is a general fit guide,
not a measurement of any specific garment, and says so.

Standards used: chest measured around the fullest part of the chest; 1 in =
2.54 cm; 1 lb = 0.453592 kg. For these unisex letter-sized tops, US and UK
letter sizes coincide — the chest measurement is the real determinant.
"""

from dataclasses import dataclass

SIZES = ["XS", "S", "M", "L", "XL", "XXL"]


@dataclass(frozen=True)
class SizeRow:
    size: str
    us: str
    uk: str
    chest_in: str
    chest_cm: str
    # Upper weight bound (kg) for the base recommendation; None = open-ended.
    weight_max_kg: float | None


# Standard unisex top chart. Chest is the body measurement, not the garment.
SIZE_CHART: list[SizeRow] = [
    SizeRow("XS", "XS", "XS", "32–34", "81–86", 57),
    SizeRow("S", "S", "S", "35–37", "89–94", 68),
    SizeRow("M", "M", "M", "38–40", "97–102", 79),
    SizeRow("L", "L", "L", "41–43", "104–109", 91),
    SizeRow("XL", "XL", "XL", "44–46", "112–117", 105),
    SizeRow("XXL", "XXL", "XXL", "47–49", "119–124", None),
]

_BY_SIZE = {row.size: row for row in SIZE_CHART}

IN_PER_CM = 1 / 2.54
KG_PER_LB = 0.453592


def chart() -> list[dict]:
    """The full size chart as plain dicts."""
    return [
        {
            "size": r.size,
            "us": r.us,
            "uk": r.uk,
            "chest_in": r.chest_in,
            "chest_cm": r.chest_cm,
        }
        for r in SIZE_CHART
    ]


def _to_metric(height: float, weight: float, units: str) -> tuple[float, float]:
    """Return (height_cm, weight_kg) from metric or imperial inputs."""
    if units == "imperial":
        # height in inches, weight in pounds
        return height / IN_PER_CM, weight * KG_PER_LB
    return height, weight


def recommend(height: float, weight: float, units: str = "metric") -> dict:
    """Recommend a size from height and weight.

    units: "metric" (height cm, weight kg) or "imperial" (height in, weight lb).
    Weight sets a base size; height nudges it (tall → up, short → down). This is
    a general estimate — the response says to confirm with the chest measurement.
    """
    units = units if units in ("metric", "imperial") else "metric"
    height_cm, weight_kg = _to_metric(height, weight, units)

    # Base size from weight.
    base_index = len(SIZES) - 1
    for i, row in enumerate(SIZE_CHART):
        if row.weight_max_kg is not None and weight_kg <= row.weight_max_kg:
            base_index = i
            break

    # Height nudge: noticeably tall sizes up, noticeably short sizes down.
    if height_cm >= 188:
        base_index += 1
    elif height_cm <= 163:
        base_index -= 1
    base_index = max(0, min(base_index, len(SIZES) - 1))

    row = _BY_SIZE[SIZES[base_index]]
    rationale = (
        f"Based on roughly {height_cm:.0f} cm and {weight_kg:.0f} kg, a {row.size} "
        f"is the best regular-fit starting point."
    )
    note = (
        f"This is a general unisex guide — confirm with your chest measurement "
        f"({row.chest_in} in / {row.chest_cm} cm for {row.size}). For an oversized "
        f"look, size up. US and UK letter sizes are the same for these tops."
    )
    return {
        "recommended_size": row.size,
        "us": row.us,
        "uk": row.uk,
        "chest_in": row.chest_in,
        "chest_cm": row.chest_cm,
        "rationale": rationale,
        "note": note,
    }
