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
    Supports:
    - Interactive agent cycling with LEFT / RIGHT arrow keys
    - Toggle between 3D Chase Camera and Top-Down BEV Perception Mode with [P] key
    """

    def __init__(self, config: Optional[CameraConfig] = None, initial_view: Optional[str] = None):
        self.config = config or CameraConfig()
        self.current_agent_id: Optional[str] = None
        self.view_mode: str = initial_view or getattr(self.config, "initial_view", "chase")
        self.is_paused: bool = False
        self.last_switch_time: float = 0.0
        self.last_toggle_time: float = 0.0
        self.last_pause_time: float = 0.0
        self._registered_keys: bool = False

    def setup_panda3d_listeners(self, env: Any):
        """Register keyboard event listeners directly into Panda3D's event manager."""
        if self._registered_keys:
            return

        engine = getattr(env, "engine", None)
        if engine is not None and hasattr(engine, "accept"):
            try:
                # Unbind MetaDrive base_env built-in keys that conflict with demo controls
                # In particular: "p" paused the simulation (self.stop), and "b"/"q" manipulated camera
                for conflicting_key in ("p", "P", "b", "B", "q", "Q", "[", "]"):
                    try:
                        engine.ignore(conflicting_key)
                    except Exception:
                        pass

                # Agent cycling
                engine.accept("arrow_left", self.previous_agent, [env])
                engine.accept("arrow_right", self.next_agent, [env])
                engine.accept("[", self.previous_agent, [env])
                engine.accept("]", self.next_agent, [env])

                # [Space] and [Pause] keys toggle simulation pause/resume
                engine.accept("space", self.toggle_pause, [env])
                engine.accept("pause", self.toggle_pause, [env])

                # [P] and [V] keys toggle between 3D Chase view and Top-Down BEV Perception
                engine.accept("p", self.toggle_view_mode, [env])
                engine.accept("P", self.toggle_view_mode, [env])
                engine.accept("v", self.toggle_view_mode, [env])
                engine.accept("V", self.toggle_view_mode, [env])
                self._registered_keys = True
            except Exception:
                pass

    def toggle_pause(self, env: Any = None, force: bool = False) -> bool:
        """Toggle simulation pause state with debounce protection."""
        now = time.time()
        if not force and (now - self.last_pause_time < 0.30):
            return self.is_paused
        self.last_pause_time = now
        self.is_paused = not self.is_paused

        # Ensure MetaDrive in_stop flag doesn't interfere
        if env is not None and hasattr(env, "in_stop"):
            env.in_stop = False

        status = "PAUSED ⏸" if self.is_paused else "RESUMED ▶"
        print(f"\n[Simulation {status}] Press [Space] to {'resume' if self.is_paused else 'pause'}.")
        return self.is_paused

    def toggle_view_mode(self, env: Any, force: bool = False):
        """Toggle between 3D Chase Camera and Top-Down Bird's-Eye-View (BEV)."""
        now = time.time()
        if not force and (now - self.last_toggle_time < 0.35):
            return
        self.last_toggle_time = now

        # Ensure MetaDrive in_stop pause flag is never stuck
        if hasattr(env, "in_stop"):
            env.in_stop = False

        self.view_mode = "bev" if self.view_mode == "chase" else "chase"
        self._apply_tracking(env, self.get_focused_agent_id(env))

    def update_frame(self, env: Any):
        """Per-step camera update: hardware button polling and BEV position tracking."""
        engine = getattr(env, "engine", None)
        if engine is None:
            return

        # Safeguard: prevent MetaDrive from freezing if in_stop was somehow toggled
        if getattr(env, "in_stop", False):
            env.in_stop = False

        # Direct hardware polling for Space, P/V, and arrow keys via Panda3D mouseWatcherNode
        mwn = getattr(engine, "mouseWatcherNode", None)
        if mwn is not None:
            try:
                from panda3d.core import KeyboardButton

                # Spacebar or Pause key polling for Pause/Resume
                is_space_down = (
                    mwn.is_button_down(KeyboardButton.space()) or
                    mwn.is_button_down(KeyboardButton.pause())
                )
                if is_space_down:
                    now = time.time()
                    if now - self.last_pause_time > 0.35:
                        self.toggle_pause(env)

                # P or V key polling for View Mode toggle
                is_p_down = (
                    mwn.is_button_down(KeyboardButton.ascii_key(b"p")) or
                    mwn.is_button_down(KeyboardButton.ascii_key(b"P")) or
                    mwn.is_button_down(KeyboardButton.ascii_key(b"v")) or
                    mwn.is_button_down(KeyboardButton.ascii_key(b"V"))
                )
                if is_p_down:
                    now = time.time()
                    if now - self.last_toggle_time > 0.40:
                        self.toggle_view_mode(env)

                # Left / Right arrow keys polling for vehicle cycling (works even when paused)
                if mwn.is_button_down(KeyboardButton.left()):
                    self.previous_agent(env)
                elif mwn.is_button_down(KeyboardButton.right()):
                    self.next_agent(env)
            except Exception:
                pass

        # If in BEV, position camera overhead looking directly down at focused CAV
        if self.view_mode == "bev":
            agents_dict = getattr(env, "agents", {})
            focused_veh = agents_dict.get(self.current_agent_id)
            if getattr(engine, "main_camera", None) is not None and focused_veh is not None:
                try:
                    pos = focused_veh.position
                    engine.main_camera.camera.setPos(pos[0], pos[1], 75.0)
                    engine.main_camera.camera.lookAt(pos[0], pos[1], 0.0)
                except Exception:
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
        """Instruct MetaDrive's 3D engine to track the specified vehicle in Chase or BEV mode."""
        engine = getattr(env, "engine", None)
        agents_dict = getattr(env, "agents", None)

        if not agents_dict or agent_id not in agents_dict:
            return

        target_vehicle = agents_dict[agent_id]

        try:
            if hasattr(env, "current_track_agent"):
                env.current_track_agent = target_vehicle
            if engine is not None:
                engine._custom_target_vehicle = target_vehicle
                if not hasattr(type(engine), "_patched_track_getter"):
                    orig_fget = type(engine).current_track_agent.fget
                    def safe_track_getter(eng):
                        if getattr(eng, "main_camera", None) is not None:
                            return eng.main_camera.current_track_agent
                        return getattr(eng, "_custom_target_vehicle", None) or (eng.agents.get("default_agent") if hasattr(eng, "agents") else None)
                    type(engine).current_track_agent = property(safe_track_getter)
                    type(engine)._patched_track_getter = True

                if getattr(engine, "main_camera", None) is not None:
                    mc = engine.main_camera
                    if self.view_mode == "bev":
                        # Overhead Top-Down BEV view: cancel chase task and position camera
                        if engine.task_manager.hasTaskNamed(mc.CHASE_TASK_NAME):
                            engine.task_manager.remove(mc.CHASE_TASK_NAME)
                        if engine.task_manager.hasTaskNamed(mc.TOP_DOWN_TASK_NAME):
                            engine.task_manager.remove(mc.TOP_DOWN_TASK_NAME)
                        pos = target_vehicle.position
                        mc.camera.setPos(pos[0], pos[1], 75.0)
                        mc.camera.lookAt(pos[0], pos[1], 0.0)
                    else:
                        # 3D Chase Camera: cancel top down and re-track target vehicle
                        if engine.task_manager.hasTaskNamed(mc.TOP_DOWN_TASK_NAME):
                            engine.task_manager.remove(mc.TOP_DOWN_TASK_NAME)
                        mc.track(target_vehicle)

                if hasattr(engine, "agent_manager") and hasattr(engine.agent_manager, "set_current_agent"):
                    engine.agent_manager.set_current_agent(agent_id)
        except Exception:
            pass
