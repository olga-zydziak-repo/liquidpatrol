"""r03/kont_config.py — konfiguracja nogi KONT (PRE_KONT §2.2, PROMPT_KONT_S1 §1.3). r03/config.py FROZEN, nietknięty.
Wejście: parametry preflight + assert-on-entry z echem do manifestu. Odcięcie GNSS w locie: KONT_CUT (jak K2)."""

KONT_PARAM_PREFLIGHT = {
    "EKF2_OF_CTRL": 1,
    "EKF2_RNG_CTRL": 1,
    "EKF2_HGT_REF": 0,
    "EKF2_GPS_CTRL": 7,
}
KONT_CUT = ("EKF2_GPS_CTRL", 0)


async def apply_and_assert(param):
    """param = mavsdk System.param. Ustawia, czyta z powrotem, rzuca przy rozjeździe. Zwraca echo {nazwa: {przed, po}}."""
    echo = {}
    for name, want in KONT_PARAM_PREFLIGHT.items():
        before = await param.get_param_int(name)
        await param.set_param_int(name, want)
        after = await param.get_param_int(name)
        if after != want:
            raise RuntimeError(f"assert-on-entry {name}: {after} != {want}")
        echo[name] = {"przed": before, "po": after}
    return echo
