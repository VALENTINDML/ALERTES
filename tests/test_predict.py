# Configuration pour petits script
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
###################################

from ml.predict import classify_trend


def test_classify_trend_hausse():
    """
    Vérifie qu'une variation positive est classée en hausse.
    """
    assert classify_trend(1.0) == "hausse"


def test_classify_trend_baisse():
    """
    Vérifie qu'une variation négative est classée en baisse.
    """
    assert classify_trend(-1.0) == "baisse"


def test_classify_trend_stagnation():
    """
    Vérifie qu'une faible variation est classée en stagnation.
    """
    assert classify_trend(0.1) == "stagnation"