"""
Intelligent Driver Model (IDM) Fleet Policy with V2V Cooperative Braking.
Final Year Project - RSET
Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs

Wraps MetaDrive's IDMPolicy and enhances it with decentralized V2V hazard awareness:
- Autonomous lane-keeping and car-following via IDM
- Cooperative braking when nearby CAVs broadcast emergency deceleration
- Smooth steering and throttle limits
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from cav_demo.v2v_network import V2VNetworkMesh


class IDMFleetController:
    """
    Manages autonomous driving policies for all CAV fleet vehicles.
    Instantiates an IDMPolicy for each agent and applies cooperative V2V adjustments.
    """

    def __init__(self, enable_coop_braking: bool = True):
        self.enable_coop_braking = enable_coop_braking
        self.policies: Dict[str, Any] = {}
        self.cooperative_brake_active: Dict[str, bool] = {}
        self.coop_step_count: Dict[str, int] = {}
        self.coop_cooldown: Dict[str, int] = {}

    def _get_or_create_policy(self, agent_id: str, vehicle: Any) -> Any:
        """Lazily initialize or refresh IDMPolicy for a vehicle."""
        existing = self.policies.get(agent_id)
        if existing is not None and getattr(existing, "control_object", None) is vehicle:
            return existing

        try:
            from metadrive.policy.idm_policy import IDMPolicy
            self.policies[agent_id] = IDMPolicy(vehicle, 42)
        except Exception:
            # Fallback simple cruise policy if IDM fails instantiation
            self.policies[agent_id] = None
        return self.policies.get(agent_id)

    def get_actions(
        self,
        agents_dict: Dict[str, Any],
        v2v_mesh: Optional[V2VNetworkMesh] = None,
        manual_agents: Optional[List[str]] = None
    ) -> Dict[str, List[float]]:
        """
        Compute control actions [steering, throttle] for all active fleet agents.
        
        Args:
            agents_dict: Current active agents dictionary
            v2v_mesh: Optional V2V network mesh for cooperative hazard sharing
            manual_agents: List of agent IDs controlled manually (e.g. ['agent0'])
        """
        actions = {}
        manual_set = set(manual_agents or [])

        for agent_id, vehicle in agents_dict.items():
            if agent_id in manual_set:
                # In MetaDrive, manual agents obtain actions from environment's ManualControlPolicy
                continue

            policy = self._get_or_create_policy(agent_id, vehicle)
            
            if policy is not None:
                try:
                    action = policy.act()
                    # Ensure action format is [steer, throttle]
                    if isinstance(action, (np.ndarray, list, tuple)):
                        steer = float(action[0])
                        throttle = float(action[1])
                    else:
                        steer, throttle = 0.0, 0.4
                except Exception:
                    steer, throttle = 0.0, 0.4
            else:
                steer, throttle = 0.0, 0.4

            # Cooperative V2V Braking Logic with Hysteresis & Proportional Control
            self.cooperative_brake_active[agent_id] = False
            cooldown = self.coop_cooldown.get(agent_id, 0)
            if cooldown > 0:
                self.coop_cooldown[agent_id] = cooldown - 1

            if self.enable_coop_braking and v2v_mesh is not None and cooldown == 0:
                warnings = v2v_mesh.get_emergency_brake_warnings(agent_id, max_distance=30.0, only_in_front=True)
                ego_speed_kmh = float(vehicle.speed_km_h) if hasattr(vehicle, "speed_km_h") and vehicle.speed_km_h is not None else 20.0

                # Only react if ego vehicle is in motion (> 5 km/h) to prevent permanent fleet freeze
                if warnings and ego_speed_kmh > 5.0:
                    closest_sender, dist, other_speed = warnings[0]
                    active_count = self.coop_step_count.get(agent_id, 0)

                    if active_count < 15:  # Maximum 15 steps (~0.75s) consecutive cooperative braking
                        if dist < 12.0:
                            # Close proximity emergency deceleration
                            throttle = min(throttle, -0.50)
                        elif dist < 25.0:
                            # Medium distance: defensive coasting / gentle deceleration
                            throttle = min(throttle, -0.15)
                        else:
                            # Gentle speed matching
                            throttle = min(throttle, 0.05)

                        self.cooperative_brake_active[agent_id] = True
                        self.coop_step_count[agent_id] = active_count + 1
                    else:
                        # Exceeded continuous braking limit; enter cooldown to let vehicle resume flow
                        self.coop_step_count[agent_id] = 0
                        self.coop_cooldown[agent_id] = 12
                else:
                    self.coop_step_count[agent_id] = 0

            # Safe action clamping to valid [-1.0, 1.0] domain
            steer = float(np.clip(steer, -1.0, 1.0))
            throttle = float(np.clip(throttle, -1.0, 1.0))
            actions[agent_id] = [steer, throttle]

        return actions

    def is_coop_braking(self, agent_id: str) -> bool:
        """Query if an agent is currently executing cooperative defensive braking."""
        return self.cooperative_brake_active.get(agent_id, False)

    def reset(self):
        """Reset policy cache and cooperative state upon episode restart."""
        self.policies.clear()
        self.cooperative_brake_active.clear()
        self.coop_step_count.clear()
        self.coop_cooldown.clear()
