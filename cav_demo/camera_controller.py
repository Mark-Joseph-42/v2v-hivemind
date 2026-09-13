"""
3D Chase Camera Controller with Interactive Agent Cycling.
Final Year Project - RSET
Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs

Provides smooth cycling of the 3D chase camera across all active CAV agents
using LEFT / RIGHT arrow keys or bracket keys, with debounce protection.
"""

import time
from typing import Any, List, Optional
from cav_demo.config import CameraConfig
from cav_demo.utils import format_agent_name


class CameraController:
    """
    Manages 3D camera tracking across multi-agent CAV fleet in MetaDrive.
    """

    def __init__(self, config: Optional[CameraConfig] = None):
        self.config = config or CameraConfig()
        self.current_agent_id: Optional[str] = None
        self.last_switch_time: float = 0.0
        self._registered_keys: bool = False

    def setup_panda3d_listeners(self, env: Any):
        """Register keyboard event listeners directly into Panda3D's event manager."""
        if self._registered_keys:
            return

        engine = getattr(env, "engine", None)
        if engine is not None and hasattr(engine, "accept"):
            try:
                engine.accept("arrow_left", self.previous_agent, [env])
                engine.accept("arrow_right", self.next_agent, [env])
                engine.accept("[", self.previous_agent, [env])
                engine.accept("]", self.next_agent, [env])
                self._registered_keys = True
            except Exception as e:
                # If engine is headless or event manager not ready
                pass

    def get_focused_agent_id(self, env: Any) -> str:
        """Return the currently focused agent ID."""
        agents = self._get_agent_keys(env)
        if not agents:
            return "agent0"

        if self.current_agent_id not in agents:
            self.current_agent_id = agents[0]
            self._apply_tracking(env, self.current_agent_id)

        return self.current_agent_id

    def get_focused_display_name(self, env: Any) -> str:
        """Return the presentation name (e.g. CAV_02) for the focused agent."""
        return format_agent_name(self.get_focused_agent_id(env))

    def next_agent(self, env: Any):
        """Cycle camera forward to the next vehicle."""
        self._cycle_agent(env, direction=+1)

    def previous_agent(self, env: Any):
        """Cycle camera backward to the previous vehicle."""
        self._cycle_agent(env, direction=-1)

    def _get_agent_keys(self, env: Any) -> List[str]:
        """Return sorted list of active agent keys."""
        if hasattr(env, "agents") and isinstance(env.agents, dict) and env.agents:
            return sorted(list(env.agents.keys()))
        elif hasattr(env, "agent_manager") and hasattr(env.agent_manager, "active_agents"):
            return sorted(list(env.agent_manager.active_agents.keys()))
        return []

    def _cycle_agent(self, env: Any, direction: int = 1):
        """Switch camera target with debounce protection."""
        now = time.time()
        if now - self.last_switch_time < self.config.switch_cooldown_s:
            return

        agents = self._get_agent_keys(env)
        if not agents:
            return

        current = self.get_focused_agent_id(env)
        try:
            curr_idx = agents.index(current)
        except ValueError:
            curr_idx = 0

        next_idx = (curr_idx + direction) % len(agents)
        self.current_agent_id = agents[next_idx]
        self.last_switch_time = now

        self._apply_tracking(env, self.current_agent_id)

    def _apply_tracking(self, env: Any, agent_id: str):
        """Instruct MetaDrive's 3D engine to track the specified vehicle."""
        engine = getattr(env, "engine", None)
        agents_dict = getattr(env, "agents", None)

        if not agents_dict or agent_id not in agents_dict:
            return

        target_vehicle = agents_dict[agent_id]

        try:
            if hasattr(env, "current_track_agent"):
                env.current_track_agent = target_vehicle
            if engine is not None:
                # Patch property fallback on engine if needed
                engine._custom_target_vehicle = target_vehicle
                if not hasattr(type(engine), "_patched_track_getter"):
                    orig_fget = type(engine).current_track_agent.fget
                    def safe_track_getter(eng):
                        if getattr(eng, "main_camera", None) is not None:
                            return eng.main_camera.current_track_agent
                        return getattr(eng, "_custom_target_vehicle", None) or (eng.agents.get("default_agent") if hasattr(eng, "agents") else None)
                    type(engine).current_track_agent = property(safe_track_getter)
                    type(engine)._patched_track_getter = True

                # Use MetaDrive MainCamera.track API
                if getattr(engine, "main_camera", None) is not None:
                    engine.main_camera.track(target_vehicle)

                if hasattr(engine, "agent_manager") and hasattr(engine.agent_manager, "set_current_agent"):
                    engine.agent_manager.set_current_agent(agent_id)
        except Exception:
            pass
