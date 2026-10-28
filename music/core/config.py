import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_CONFIG = {
    "bpm": 84,
    "key": "F#m",
    "time_sig": (4, 4),
    "sections": {
        "intro": 4,
        "verse": 8,
        "chorus": 8,
        "outro": 4,
    },
    "swing": 0.0,          # 0=直排，>0 微 swing
    "velocity_base": 80,
}