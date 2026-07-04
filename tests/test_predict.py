# Configuration pour petits script
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
###################################

from ml.predict import classify_trend


def test_classify_trend_hausse():
    assert classify_trend(1.0) == "hausse"


def test_classify_trend_baisse():
    assert classify_trend(-1.0) == "baisse"


def test_classify_trend_stagnation():
    assert classify_trend(0.1) == "stagnation"