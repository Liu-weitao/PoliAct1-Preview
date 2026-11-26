"""LADDER entry: scripts/eval.sh --task lite --agent /path/your_client.py:YourClass"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ladder_remote_agent import PoliAct1PreviewRemoteAgent

class YourClass(PoliAct1PreviewRemoteAgent):
    pass
