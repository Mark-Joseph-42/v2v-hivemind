"""
Utility functions, formatting, and mathematical helpers for CAV Telemetry Demo.
"""

import math
import numpy as np
from typing import Tuple, List, Dict, Any


class Colors:
    """Terminal ANSI colors for rich console reporting."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'


def format_agent_name(agent_id: str) -> str:
    """Standardize agent identifier into a clean presentation string (e.g., CAV_01)."""
    # Extract digits if any
    digits = ''.join(c for c in str(agent_id) if c.isdigit())
    if digits:
        return f"CAV_{int(digits) + 1:02d}"
    return f"CAV_{str(agent_id).upper()}"


def mps_to_kmh(speed_mps: float) -> float:
    """Convert speed from meters per second to kilometers per hour."""
    return float(speed_mps * 3.6)


def rad_to_deg(angle_rad: float) -> float:
    """Convert angle in radians to degrees normalized in [-180, 180]."""
    deg = math.degrees(angle_rad) % 360.0
    if deg > 180.0:
        deg -= 360.0
    return deg


def euclidean_distance(pos_a: Tuple[float, float], pos_b: Tuple[float, float]) -> float:
    """2D Euclidean distance between two positions."""
    return math.hypot(pos_a[0] - pos_b[0], pos_a[1] - pos_b[1])


def print_banner(mode: str, num_agents: int):
    """Print an eye-catching presentation banner for RSET project demonstration."""
    print(f"""{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║              RAJAGIRI SCHOOL OF ENGINEERING & TECHNOLOGY (RSET)              ║
║         FINAL YEAR B.TECH PROJECT - 30% MILESTONE DEMONSTRATION             ║
║                                                                              ║
║  Title: Collaborative Trajectory Planning and Multi-Agent Orchestration      ║
║         for Connected Autonomous Vehicles in Mixed-Autonomy Environments     ║
║  Team : Mark Joseph | Sanjana | Neha | Ritu                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.ENDC}
{Colors.GREEN}● Operating Mode     :{Colors.ENDC} {Colors.BOLD}{mode.upper()}{Colors.ENDC}
{Colors.GREEN}● Active CAV Fleet   :{Colors.ENDC} {num_agents} Vehicles
{Colors.GREEN}● Communication Mesh :{Colors.ENDC} V2V Cooperative Telemetry Enabled (80m Radius)
{Colors.GREEN}● Interactive Keys   :{Colors.ENDC}
    {Colors.YELLOW}[◄ / ►]{Colors.ENDC} Cycle Chase Camera Across Active CAVs
    {Colors.YELLOW}[W/A/S/D]{Colors.ENDC} Control CAV_01 Directly (in Human Mode)
    {Colors.YELLOW}[T]{Colors.ENDC}       Toggle CAV_01 Manual/Autonomous in Human Mode
    {Colors.YELLOW}[H / Esc]{Colors.ENDC} Toggle On-Screen Help / Exit Simulation
══════════════════════════════════════════════════════════════════════════════
""")
