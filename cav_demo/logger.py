"""
Telemetry Data Logger for Experimental Analysis and Report Generation.
Final Year Project - RSET
Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs

Records kinematic states and V2V packet exchanges to CSV for easy plotting
of velocity profiles, inter-vehicle distances, and network latency in report slides.
"""

import csv
import os
import time
from typing import Dict, List, Optional, Any


class TelemetryLogger:
    """
    Logs step-by-step CAV fleet telemetry into a CSV file for report graphing.
    """

    def __init__(self, log_dir: str = "logs", enabled: bool = True):
        self.enabled = enabled
        self.log_dir = log_dir
        self.csv_file = None
        self.writer = None
        self.filepath = ""

        if self.enabled:
            os.makedirs(self.log_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.filepath = os.path.join(self.log_dir, f"cav_telemetry_{timestamp}.csv")
            self.csv_file = open(self.filepath, mode="w", newline="", buffering=1)
            self.writer = csv.writer(self.csv_file)
            # CSV Header
            self.writer.writerow([
                "step",
                "timestamp_epoch",
                "agent_id",
                "pos_x",
                "pos_y",
                "speed_kmh",
                "heading_deg",
                "steering",
                "throttle",
                "is_braking",
                "coop_braking_active",
                "v2v_active_links",
                "v2v_avg_latency_ms"
            ])

    def log_step(
        self,
        step: int,
        agents_dict: Dict[str, Any],
        v2v_mesh: Any,
        actions_dict: Optional[Dict[str, Any]] = None,
        coop_status_dict: Optional[Dict[str, bool]] = None
    ):
        """Log the state of all agents at the current simulation step."""
        if not self.enabled or self.writer is None:
            return

        now = time.time()
        actions = actions_dict or {}
        coop_status = coop_status_dict or {}
        stats = v2v_mesh.get_aggregate_stats() if v2v_mesh else {}

        for aid, veh in agents_dict.items():
            state = v2v_mesh.latest_states.get(aid) if v2v_mesh else None
            act = actions.get(aid, [0.0, 0.0])

            pos_x = state.pos[0] if state else 0.0
            pos_y = state.pos[1] if state else 0.0
            speed_kmh = state.speed_kmh if state else 0.0
            heading_deg = state.heading_rad * 57.2958 if state else 0.0
            steer = float(act[0])
            throttle = float(act[1])
            is_braking = 1 if (state and state.is_braking) else 0
            is_coop = 1 if coop_status.get(aid, False) else 0

            self.writer.writerow([
                step,
                round(now, 3),
                aid,
                round(pos_x, 2),
                round(pos_y, 2),
                round(speed_kmh, 2),
                round(heading_deg, 2),
                round(steer, 3),
                round(throttle, 3),
                is_braking,
                is_coop,
                stats.get("active_links", 0),
                round(stats.get("avg_latency_ms", 0.0), 2)
            ])

    def close(self):
        """Close log file upon simulation termination."""
        if self.csv_file is not None and not self.csv_file.closed:
            self.csv_file.flush()
            self.csv_file.close()
            print(f"[Telemetry Logger] Data saved to {self.filepath}")
