"""
Unit tests for V2V communication network and kinematic packet processing.
"""

import math
from unittest.mock import MagicMock
import numpy as np
import pytest

from cav_demo.config import V2VConfig
from cav_demo.v2v_network import V2VNetworkMesh, V2VPacket
from cav_demo.utils import format_agent_name, mps_to_kmh


class MockVehicle:
    """Mock MetaDrive vehicle object for isolated unit testing."""
    def __init__(self, x=0.0, y=0.0, vx=10.0, vy=0.0, heading=0.0, yaw_rate=0.0, lane_index=1):
        self.position = [x, y]
        self.velocity = [vx, vy]
        self.speed = math.hypot(vx, vy)
        self.heading_theta = heading
        self.angular_velocity = [0.0, 0.0, yaw_rate]
        self.lane_index = ("road_0", "road_1", lane_index)


def test_agent_name_formatting():
    assert format_agent_name("agent0") == "CAV_01"
    assert format_agent_name("agent_1") == "CAV_02"
    assert format_agent_name("cav_3") == "CAV_04"


def test_speed_conversion():
    assert pytest.approx(mps_to_kmh(10.0), 0.01) == 36.0
    assert pytest.approx(mps_to_kmh(0.0), 0.01) == 0.0


def test_v2v_packet_extraction():
    config = V2VConfig(base_latency_ms=10.0, latency_jitter_ms=0.0, packet_drop_rate=0.0)
    mesh = V2VNetworkMesh(config)
    mock_veh = MockVehicle(x=25.0, y=50.0, vx=15.0, vy=0.0, heading=0.5, yaw_rate=0.1, lane_index=2)

    # Normal cruise action [steer=0.0, throttle=0.6]
    pkt = mesh.extract_kinematics("agent_0", mock_veh, step=1, last_action=[0.0, 0.6])

    assert pkt.sender_id == "agent_0"
    assert pkt.sender_display == "CAV_01"
    assert pkt.pos == (25.0, 50.0)
    assert pytest.approx(pkt.speed_kmh, 0.01) == 54.0
    assert not pkt.is_braking
    assert pkt.lane_index == 2
    assert len(pkt.kinematic_vector) == 11
    assert pkt.kinematic_vector[0] == 25.0
    assert pkt.kinematic_vector[1] == 50.0
    assert pkt.kinematic_vector[6] == 54.0
    assert pkt.kinematic_vector[9] == 0.0  # brake flag 0


def test_v2v_brake_warning_trigger():
    config = V2VConfig(brake_warning_threshold=-0.3)
    mesh = V2VNetworkMesh(config)
    mock_veh = MockVehicle(x=10.0, y=10.0)

    # Hard brake action: throttle = -0.8
    pkt = mesh.extract_kinematics("agent_0", mock_veh, step=2, last_action=[0.0, -0.8])
    assert pkt.is_braking
    assert pkt.kinematic_vector[9] == 1.0


def test_v2v_mesh_broadcast_range():
    # Set comm radius to 50m, 0% drop rate
    config = V2VConfig(comm_radius_m=50.0, packet_drop_rate=0.0)
    mesh = V2VNetworkMesh(config)

    # 3 vehicles:
    # A at (0, 0)
    # B at (30, 0) -> distance 30m (< 50m, in range)
    # C at (90, 0) -> distance 90m (> 50m, out of range of A)
    agents = {
        "agent_0": MockVehicle(x=0.0, y=0.0),
        "agent_1": MockVehicle(x=30.0, y=0.0),
        "agent_2": MockVehicle(x=90.0, y=0.0),
    }

    received = mesh.broadcast_step(agents, step=1)

    # Agent_0 should receive from Agent_1 (30m away) but NOT from Agent_2 (90m away)
    a0_senders = [p.sender_id for p in received["agent_0"]]
    assert "agent_1" in a0_senders
    assert "agent_2" not in a0_senders

    # Agent_1 at 30 should receive from Agent_0 (30m away) and from Agent_2 (60m away is > 50m)
    a1_senders = [p.sender_id for p in received["agent_1"]]
    assert "agent_0" in a1_senders
    assert "agent_2" not in a1_senders

    # Check aggregate stats
    stats = mesh.get_aggregate_stats()
    assert stats["total_broadcasts"] == 3
    assert stats["drop_rate_pct"] == 0.0


def test_directional_brake_warning():
    """Verify that only braking vehicles ahead trigger defensive warnings, not vehicles behind."""
    config = V2VConfig(comm_radius_m=50.0, packet_drop_rate=0.0)
    mesh = V2VNetworkMesh(config)

    # Ego vehicle at (10, 0) heading along +x (heading_theta = 0)
    # Front vehicle at (25, 0) (ahead by 15m)
    # Rear vehicle at (0, 0) (behind by 10m)
    agents = {
        "agent0": MockVehicle(x=10.0, y=0.0, vx=15.0, heading=0.0),
        "agent1_front": MockVehicle(x=25.0, y=0.0, vx=15.0, heading=0.0),
        "agent2_rear": MockVehicle(x=0.0, y=0.0, vx=15.0, heading=0.0),
    }

    actions = {
        "agent0": [0.0, 0.5],
        "agent1_front": [0.0, -0.8],  # Hard brake ahead
        "agent2_rear": [0.0, -0.8],   # Hard brake behind
    }
    mesh.broadcast_step(agents, step=1, actions_dict=actions)

    warnings = mesh.get_emergency_brake_warnings("agent0", max_distance=30.0, only_in_front=True)
    warn_senders = [w[0] for w in warnings]

    # Front vehicle must trigger warning
    assert format_agent_name("agent1_front") in warn_senders
    # Rear vehicle must NOT trigger warning for vehicle ahead
    assert format_agent_name("agent2_rear") not in warn_senders

