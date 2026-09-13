"""
MetaDrive PGMA (Procedural Generation Multi-Agent) Environment Factory.
Final Year Project - RSET
Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs
"""

import sys
from typing import Any, Dict, Optional
from cav_demo.config import SimulationConfig


def create_env(config: Optional[SimulationConfig] = None, mode: str = "fleet", headless: bool = False) -> Any:
    """
    Construct and return a configured MultiAgentMetaDrive environment.
    
    Args:
        config: SimulationConfig parameters dataclass
        mode: "fleet" (all autonomous) or "human" (Agent_0 keyboard control)
        headless: If True, disables 3D window rendering (useful for testing/benchmarking)
    """
    try:
        from metadrive import MultiAgentMetaDrive
        from metadrive.engine.base_engine import BaseEngine

        # Ensure multi-agent environments never raise AttributeError in ManualControlPolicy
        if not hasattr(BaseEngine, "_safe_current_track_agent_patched"):
            def _safe_current_track_agent(engine_self):
                if getattr(engine_self, "main_camera", None) is not None and engine_self.main_camera.current_track_agent is not None:
                    return engine_self.main_camera.current_track_agent
                if hasattr(engine_self, "_custom_track_agent") and engine_self._custom_track_agent is not None:
                    return engine_self._custom_track_agent
                if hasattr(engine_self, "agents") and engine_self.agents:
                    if "default_agent" in engine_self.agents:
                        return engine_self.agents["default_agent"]
                    first_key = sorted(list(engine_self.agents.keys()))[0]
                    return engine_self.agents[first_key]
                return None

            BaseEngine.current_track_agent = property(_safe_current_track_agent)
            BaseEngine._safe_current_track_agent_patched = True

    except ImportError as e:
        print(f"[Error] Failed to import MetaDrive: {e}")
        print("Please ensure metadrive-simulator is installed in the active virtual environment.")
        sys.exit(1)

    cfg = config or SimulationConfig()
    
    # In human mode, enable MetaDrive's manual_control on agent0
    is_manual = (mode == "human")

    env_config: Dict[str, Any] = {
        "use_render": not headless and cfg.use_render,
        "num_agents": cfg.num_agents,
        "map": cfg.map_blocks,
        "traffic_density": cfg.traffic_density,
        "allow_respawn": cfg.allow_respawn,
        "crash_done": cfg.crash_done,
        "out_of_road_done": cfg.out_of_road_done,
        "crash_vehicle_done": cfg.crash_vehicle_done,
        "horizon": cfg.horizon,
        "decision_repeat": cfg.decision_repeat,
        "physics_world_step_size": cfg.physics_world_step_size,
        "manual_control": is_manual,
        "vehicle_config": {
            "lidar": {
                "num_lasers": cfg.lidar_num_lasers,
                "distance": cfg.lidar_distance,
                "gaussian_noise": 0.0,
                "dropout_prob": 0.0,
            },
            "show_lidar": cfg.show_lidar and not headless,
            "show_navi_mark": False,
            "show_dest_mark": False,
        },
        "window_size": cfg.window_size,
    }

    # Scenario Selection (PGMA Corridor, Roundabout, Intersection, Bottleneck, Tollgate)
    scenario = (cfg.scenario or "corridor").strip().lower()
    if scenario in ("roundabout", "marl_roundabout"):
        from metadrive.envs.marl_envs import MultiAgentRoundaboutEnv
        env = MultiAgentRoundaboutEnv(env_config)
    elif scenario in ("intersection", "marl_intersection"):
        from metadrive.envs.marl_envs import MultiAgentIntersectionEnv
        env = MultiAgentIntersectionEnv(env_config)
    elif scenario in ("bottleneck", "marl_bottleneck"):
        from metadrive.envs.marl_envs import MultiAgentBottleneckEnv
        env = MultiAgentBottleneckEnv(env_config)
    elif scenario in ("tollgate", "marl_tollgate"):
        from metadrive.envs.marl_envs import MultiAgentTollgateEnv
        env = MultiAgentTollgateEnv(env_config)
    elif scenario in ("parking", "marl_parking"):
        from metadrive.envs.marl_envs import MultiAgentParkingLotEnv
        env = MultiAgentParkingLotEnv(env_config)
    else:
        # Default procedural PGMA highway corridor
        env = MultiAgentMetaDrive(env_config)

    return env


def get_active_agents_dict(env: Any) -> Dict[str, Any]:
    """Retrieve the dictionary of all currently active agent vehicles."""
    if hasattr(env, "agents") and isinstance(env.agents, dict):
        return env.agents
    elif hasattr(env, "agent_manager") and hasattr(env.agent_manager, "active_agents"):
        return env.agent_manager.active_agents
    return {}
