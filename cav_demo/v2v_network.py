"""
Vehicle-to-Vehicle (V2V) Communication Network Simulation.
Final Year Project - RSET
Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs

Simulates a real-time decentralized V2V ad-hoc mesh network:
- 11-dimensional kinematic state vector extraction
- Wireless range-limited broadcast (80m)
- Stochastic latency and wireless packet loss simulation
- Distributed hazard & emergency brake event propagation
"""

import math
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from cav_demo.config import V2VConfig
from cav_demo.utils import euclidean_distance, mps_to_kmh, format_agent_name


@dataclass
class V2VPacket:
    """A single V2V broadcast packet containing standard 11D kinematic telemetry."""
    sender_id: str
    sender_display: str
    step: int
    pos: Tuple[float, float]
    velocity: Tuple[float, float]
    speed_kmh: float
    heading_rad: float
    yaw_rate: float
    steering: float
    throttle: float
    is_braking: bool
    lane_index: int
    kinematic_vector: np.ndarray
    latency_ms: float
    dropped: bool = False

    def summary_line(self) -> str:
        """One-line formatted readout for UI telemetry feeds."""
        brake_str = " [BRAKE!]" if self.is_braking else ""
        return (f"[{self.sender_display}] Spd:{self.speed_kmh:4.1f}km/h "
                f"Pos:({self.pos[0]:5.1f},{self.pos[1]:5.1f}) Lat:{self.latency_ms:4.1f}ms{brake_str}")


class V2VNetworkMesh:
    """
    Simulates a localized V2V wireless communication mesh among active CAV agents.
    """

    def __init__(self, config: Optional[V2VConfig] = None):
        self.config = config or V2VConfig()
        
        # Per-agent received packet history: agent_id -> deque of V2VPacket
        self.received_packets: Dict[str, deque] = {}
        
        # Latest known state per agent: agent_id -> V2VPacket
        self.latest_states: Dict[str, V2VPacket] = {}
        
        # Aggregate statistics
        self.total_broadcasts = 0
        self.total_delivered = 0
        self.total_dropped = 0
        self.active_links_count = 0
        self.rolling_latencies = deque(maxlen=100)

    def extract_kinematics(self, agent_id: str, vehicle: Any, step: int, last_action: Optional[List[float]] = None) -> V2VPacket:
        """
        Extract the standard 11-dimensional kinematic state vector from a MetaDrive vehicle.
        Vector: [pos_x, pos_y, vel_x, vel_y, heading_rad, yaw_rate, speed_kmh, steer, throttle, brake_flag, lane_idx]
        """
        pos = vehicle.position
        pos_x, pos_y = float(pos[0]), float(pos[1])
        
        vel = vehicle.velocity if hasattr(vehicle, "velocity") else (0.0, 0.0)
        vel_x, vel_y = float(vel[0]), float(vel[1])
        
        if hasattr(vehicle, "speed_km_h") and vehicle.speed_km_h is not None:
            speed_kmh = float(vehicle.speed_km_h)
        elif hasattr(vehicle, "speed") and vehicle.speed is not None:
            speed_kmh = mps_to_kmh(float(vehicle.speed))
        else:
            speed_kmh = mps_to_kmh(math.hypot(vel_x, vel_y))
        
        heading_rad = float(vehicle.heading_theta) if hasattr(vehicle, "heading_theta") else 0.0
        
        # Extract yaw rate from Bullet physics chassis or fallback
        yaw_rate = 0.0
        try:
            if hasattr(vehicle, "chassis") and hasattr(vehicle.chassis, "node"):
                ang_vel = vehicle.chassis.node().getAngularVelocity()
                yaw_rate = float(ang_vel[2])
            elif hasattr(vehicle, "angular_velocity") and vehicle.angular_velocity is not None:
                yaw_rate = float(vehicle.angular_velocity[2])
        except Exception:
            yaw_rate = 0.0
        
        steering = float(last_action[0]) if (last_action is not None and len(last_action) > 0) else 0.0
        throttle = float(last_action[1]) if (last_action is not None and len(last_action) > 1) else 0.0
        
        # Genuine emergency braking: heavy decel while in motion (speed > 8 km/h)
        is_braking = (throttle < self.config.brake_warning_threshold) and (speed_kmh > 8.0)
        
        lane_index = 0
        if hasattr(vehicle, "lane_index") and vehicle.lane_index is not None:
            try:
                lane_index = int(vehicle.lane_index[-1]) if isinstance(vehicle.lane_index, tuple) else int(vehicle.lane_index)
            except Exception:
                lane_index = 0

        # Construct 11D array
        kinematic_vector = np.array([
            pos_x,
            pos_y,
            vel_x,
            vel_y,
            heading_rad,
            yaw_rate,
            speed_kmh,
            steering,
            throttle,
            1.0 if is_braking else 0.0,
            float(lane_index)
        ], dtype=np.float32)

        # Simulate latency with standard wireless propagation + jitter
        latency = max(2.0, random.gauss(self.config.base_latency_ms, self.config.latency_jitter_ms))
        
        # Packet drop determination
        dropped = (random.random() < self.config.packet_drop_rate)

        return V2VPacket(
            sender_id=agent_id,
            sender_display=format_agent_name(agent_id),
            step=step,
            pos=(pos_x, pos_y),
            velocity=(vel_x, vel_y),
            speed_kmh=speed_kmh,
            heading_rad=heading_rad,
            yaw_rate=yaw_rate,
            steering=steering,
            throttle=throttle,
            is_braking=is_braking,
            lane_index=lane_index,
            kinematic_vector=kinematic_vector,
            latency_ms=latency,
            dropped=dropped
        )

    def broadcast_step(self, agents_dict: Dict[str, Any], step: int, actions_dict: Optional[Dict[str, Any]] = None) -> Dict[str, List[V2VPacket]]:
        """
        Execute one complete round of V2V broadcast across all active agents.
        Returns mapping: receiver_agent_id -> list of successfully received V2VPackets.
        """
        actions = actions_dict or {}
        active_agents = list(agents_dict.keys())
        
        # Initialize queues if newly joined
        for aid in active_agents:
            if aid not in self.received_packets:
                self.received_packets[aid] = deque(maxlen=self.config.packet_history_len)

        # 1. Extract packets from all transmitters
        packets: Dict[str, V2VPacket] = {}
        for aid, veh in agents_dict.items():
            pkt = self.extract_kinematics(aid, veh, step, actions.get(aid))
            packets[aid] = pkt
            if not pkt.dropped:
                self.latest_states[aid] = pkt

        # 2. Simulate range-limited mesh exchange
        received_this_step: Dict[str, List[V2VPacket]] = {aid: [] for aid in active_agents}
        active_links = 0

        for sender_id, pkt in packets.items():
            self.total_broadcasts += 1
            if pkt.dropped:
                self.total_dropped += 1
                continue

            self.total_delivered += 1
            self.rolling_latencies.append(pkt.latency_ms)

            # Check neighbors within communication radius
            for receiver_id in active_agents:
                if receiver_id == sender_id:
                    continue

                rx_pos = agents_dict[receiver_id].position
                dist = euclidean_distance(pkt.pos, (float(rx_pos[0]), float(rx_pos[1])))

                if dist <= self.config.comm_radius_m:
                    active_links += 1
                    received_this_step[receiver_id].append(pkt)
                    self.received_packets[receiver_id].appendleft(pkt)

        self.active_links_count = active_links
        return received_this_step

    def get_emergency_brake_warnings(
        self,
        receiver_id: str,
        max_distance: Optional[float] = None,
        only_in_front: bool = True
    ) -> List[Tuple[str, float, float]]:
        """
        Check for any nearby agents broadcasting emergency braking within warning radius.
        Filters hazards using spatial vector projection to ensure hazard is ahead of receiver.
        Returns list of tuples: (sender_display, distance_m, speed_kmh)
        """
        dist_threshold = max_distance or self.config.coop_brake_radius_m
        if receiver_id not in self.latest_states:
            return []

        rx_state = self.latest_states[receiver_id]
        warnings = []

        for sender_id, state in self.latest_states.items():
            if sender_id == receiver_id:
                continue
            # Must be actively braking and moving
            if state.is_braking and state.speed_kmh > 5.0:
                d = euclidean_distance(rx_state.pos, state.pos)
                if d <= dist_threshold:
                    if only_in_front:
                        # Vector from receiver to sender
                        dx = state.pos[0] - rx_state.pos[0]
                        dy = state.pos[1] - rx_state.pos[1]
                        # Longitudinal distance along receiver heading
                        long_dist = dx * math.cos(rx_state.heading_rad) + dy * math.sin(rx_state.heading_rad)
                        # Only warn if sender is ahead of receiver (tolerance -2.0m)
                        if long_dist < -2.0:
                            continue
                    warnings.append((state.sender_display, d, state.speed_kmh))

        return sorted(warnings, key=lambda x: x[1])

    def get_aggregate_stats(self) -> Dict[str, Any]:
        """Summary metrics for the live telemetry panel."""
        avg_lat = float(np.mean(self.rolling_latencies)) if self.rolling_latencies else self.config.base_latency_ms
        drop_rate_pct = (self.total_dropped / max(1, self.total_broadcasts)) * 100.0
        return {
            "avg_latency_ms": avg_lat,
            "drop_rate_pct": drop_rate_pct,
            "total_broadcasts": self.total_broadcasts,
            "total_delivered": self.total_delivered,
            "active_links": self.active_links_count,
            "monitored_vehicles": len(self.latest_states)
        }

    def reset(self):
        """Reset network history upon episode restart."""
        self.received_packets.clear()
        self.latest_states.clear()
        self.active_links_count = 0
        self.rolling_latencies.clear()
        self.total_broadcasts = 0
        self.total_delivered = 0
        self.total_dropped = 0

