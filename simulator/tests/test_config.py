from config import BORNES, VILLES, validate_configuration

def test_total_chargers():
    assert len(BORNES) == 15


def test_unique_codes():
    codes = [borne.code for borne in BORNES]
    assert len(codes) == len(set(codes))


def test_five_chargers_per_city():
    for ville in VILLES:
        assert sum(b.ville == ville for b in BORNES) == 5


def test_station_assignments():
    for borne in BORNES:
        number = int(borne.code[-3:])
        expected = (
            f"ST-{borne.ville}-01"
            if number <= 3
            else f"ST-{borne.ville}-02"
        )
        assert borne.station_code == expected


def test_configuration_validation():
    validate_configuration()