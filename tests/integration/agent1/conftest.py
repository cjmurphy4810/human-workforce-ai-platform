import sys
from pathlib import Path

_AGENT1 = Path(__file__).parent.parent.parent.parent / "agent1-research"
if str(_AGENT1) not in sys.path:
    sys.path.insert(0, str(_AGENT1))
