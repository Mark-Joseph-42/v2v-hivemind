"""
Centralized Configuration for MetaDrive Multi-Agent CAV Telemetry System
Final Year Project - RSET
Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Tuple


@dataclass
class SimulationConfig:
    """Core simulator configuration settings."""
    num_agents: int = 4
    map_blocks: int = 5
    scenario: str = "corridor"           # "corridor", "roundabout", "intersection", "bottleneck", "tollgate"
    traffic_density: float = 0.08
    allow_respawn: bool = False
    crash_done: bool = False
    out_of_road_done: bool = False
    crash_vehicle_done: bool = False
    horizon: int = 4000
    decision_repeat: int = 5
    physics_world_step_size: float = 0.02
    use_render: bool = True
    manual_control: bool = False
    show_lidar: bool = True              # Draw real 3D laser beams in the viewport
    lidar_num_lasers: int = 72           # 360-degree laser count
    lidar_distance: float = 50.0         # LiDAR maximum detection range in meters
    window_size: Tuple[int, int] = (1280, 720)


@dataclass
class V2VConfig:
    """Vehicle-to-Vehicle (V2V) Communication Mesh parameters."""
    comm_radius_m: float = 80.0          # Max broadcast radius in meters
    base_latency_ms: float = 12.0        # Average wireless transmission latency
    latency_jitter_ms: float = 6.0       # Latency standard deviation / jitter
    packet_drop_rate: float = 0.02       # 2% packet loss rate
    packet_history_len: int = 25         # Rolling history per agent
    brake_warning_threshold: float = -0.35 # Deceleration / brake threshold for warning
    coop_brake_radius_m: float = 45.0    # Distance for cooperative fleet emergency reaction


@dataclass
class CameraConfig:
    """3D Chase Camera & switching configuration."""
    switch_cooldown_s: float = 0.25      # Debounce period for switching agents
    fov: float = 65.0
    chase_dist: float = 8.5
    chase_height: float = 2.8


@dataclass
class HUDConfig:
    """On-screen telemetry HUD layout configuration."""
    update_interval_s: float = 0.05      # 20 Hz update rate
    sidebar_x: float = 0.58              # Right side position (Panda3D aspect2d coords)
    sidebar_top_y: float = 0.95          # Aligned to top-right
    font_size: float = 0.030             # Scaled for multi-panel telemetry layout
    header_color: Tuple[float, float, float, float] = (0.3, 0.8, 1.0, 1.0)
    normal_color: Tuple[float, float, float, float] = (0.9, 0.9, 0.9, 1.0)
    highlight_color: Tuple[float, float, float, float] = (0.2, 1.0, 0.4, 1.0)
    warning_color: Tuple[float, float, float, float] = (1.0, 0.25, 0.25, 1.0)
    caution_color: Tuple[float, float, float, float] = (1.0, 0.85, 0.2, 1.0)


@dataclass
class MinimapConfig:
    """Top-down Picture-in-Picture minimap configuration."""
    enabled: bool = True
    size: Tuple[int, int] = (260, 260)
    update_interval_frames: int = 3      # Update every 3rd step to maximize 3D FPS
    screen_pos: Tuple[float, float] = (-1.08, -0.68) # Bottom-left in Panda3D aspect2d
    scaling: float = 1.6
