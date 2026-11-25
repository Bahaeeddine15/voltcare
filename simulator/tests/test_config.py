from datetime import date

from config import BORNES, VILLES, mois_avant, validate_configuration

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


def test_commissioning_dates_match_demo_data():
    # donnees-demo.apex : 10, 14, 18, 22, 26 mois pour les bornes 001 a 005
    for borne in BORNES:
        number = int(borne.code[-3:])
        assert borne.date_mise_en_service == mois_avant(6 + number * 4)
        assert borne.date_mise_en_service < date.today()


def test_mois_avant_handles_year_and_month_end():
    assert mois_avant(2, date(2026, 1, 15)) == date(2025, 11, 15)
    assert mois_avant(1, date(2026, 3, 31)) == date(2026, 2, 28)
