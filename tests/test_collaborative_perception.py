"""
Unit tests for V2V Collaborative Perception & BEV Camera Controller.
Final Year Project - RSET
"""

import math
from unittest.mock import MagicMock
import pytest

from cav_demo.collaborative_perception import CollaborativePerceptionEngine
from cav_demo.camera_controller import CameraController
from cav_demo.config import CameraConfig


class MockObs:
    def __init__(self, detected_objects=None):
        self.detected_objects = detected_objects or []


class MockTarget:
    def __init__(self, x=0.0, y=0.0):
        self.position = [x, y]


class MockVehicle:
    def __init__(self, x=0.0, y=0.0):
        self.position = [x, y]


class MockAgentManager:
    def __init__(self, obss):
        self._obss = obss

    def get_observations(self):
        return self._obss


class MockEnv:
    def __init__(self, agents, obss):
        self.agents = agents
        self.agent_manager = MockAgentManager(obss)
        self.engine = MagicMock()


def test_collaborative_perception_occlusion_detection():
    engine = CollaborativePerceptionEngine()

    # Ego vehicle at (0, 0)
    # Neighbor CAV at (10, 0)
    # Target 1 (Visible to both): at (5, 0)
    # Target 2 (Occluded from ego, visible ONLY to neighbor): at (15, 0)
    target_shared = MockTarget(5.0, 0.0)
    target_hidden = MockTarget(15.0, 0.0)

    ego_veh = MockVehicle(0.0, 0.0)
    neighbor_veh = MockVehicle(10.0, 0.0)

    agents = {
        "agent0": ego_veh,
        "agent1": neighbor_veh,
    }

    obss = {
        "agent0": MockObs(detected_objects=[target_shared]),
        "agent1": MockObs(detected_objects=[target_shared, target_hidden]),
    }

    env = MockEnv(agents, obss)
    v2v_mesh = MagicMock()

    summary = engine.update(env, "agent0", v2v_mesh)

    assert summary["active"] is True
    assert summary["resolved_count"] == 1
    assert pytest.approx(summary["closest_dist"], 0.1) == 15.0
    assert summary["revealing_partner"] == "CAV_02"


def test_camera_controller_bev_toggle():
    cam = CameraController(CameraConfig())
    assert cam.view_mode == "chase"

    mock_env = MagicMock()
    cam.toggle_view_mode(mock_env, force=True)
    assert cam.view_mode == "bev"

    cam.toggle_view_mode(mock_env, force=True)
    assert cam.view_mode == "chase"
