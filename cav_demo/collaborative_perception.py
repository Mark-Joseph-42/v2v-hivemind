"""
V2V Collaborative Perception & Occlusion Shadow Filling.
Final Year Project - RSET
Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs

Implements Beyond-Line-of-Sight (BLOS) Cooperative Perception (ETSI TR 103 562 / SAE J3186):
- Detects obstacles hidden within the ego vehicle's local LiDAR occlusion shadow (blue shadow)
- Fuses neighboring CAV point clouds & detected objects transmitted over the V2V mesh
- Renders real-time GREEN CIRCLES & augmented beacon rings at occluded obstacle coordinates
"""

import math
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np


class CollaborativePerceptionEngine:
    """
    Computes and visualizes collaborative beyond-line-of-sight perception.
    Fills in the ego vehicle's LiDAR occlusion shadow with green markers
    using observations transmitted by neighboring CAVs over the V2V mesh.
    """

    def __init__(self, circle_radius: float = 2.4, circle_segments: int = 24):
        self.circle_radius = circle_radius
        self.circle_segments = circle_segments
        self._line_node: Any = None
        self._np: Any = None
        self._initialized: bool = False
        
        # Telemetry metrics
        self.resolved_occlusions_count: int = 0
        self.closest_collaborative_dist: float = 50.0
        self.revealing_partner_name: str = "NONE"

    def update(
        self,
        env: Any,
        ego_agent_id: str,
        v2v_mesh: Any
    ) -> Dict[str, Any]:
        """
        Compute occluded targets and render green collaborative circles in Panda3D.
        Returns telemetry summary for on-screen HUD.
        """
        agents_dict = getattr(env, "agents", {})
        ego_veh = agents_dict.get(ego_agent_id)
        if ego_veh is None:
            self.clear_visualization()
            return self.get_summary()

        # 1. Retrieve observation objects from MetaDrive
        obss = {}
        if hasattr(env, "agent_manager") and hasattr(env.agent_manager, "get_observations"):
            try:
                obss = env.agent_manager.get_observations()
            except Exception:
                obss = {}

        ego_obs = obss.get(ego_agent_id)
        ego_pos = (float(ego_veh.position[0]), float(ego_veh.position[1]))

        # Objects directly detected by ego vehicle
        ego_detected_ids: Set[int] = set()
        if ego_obs is not None and hasattr(ego_obs, "detected_objects") and ego_obs.detected_objects:
            ego_detected_ids = {id(obj) for obj in ego_obs.detected_objects}

        # 2. Find objects detected by neighboring CAVs that are occluded from ego
        collaborative_targets: List[Tuple[float, float, str]] = []
        min_dist_found = 50.0
        revealing_partner = "NONE"

        for neighbor_id, neighbor_veh in agents_dict.items():
            if neighbor_id == ego_agent_id:
                continue

            # Check if neighbor is within V2V communication range
            n_pos = (float(neighbor_veh.position[0]), float(neighbor_veh.position[1]))
            dist_to_neighbor = math.hypot(n_pos[0] - ego_pos[0], n_pos[1] - ego_pos[1])
            if dist_to_neighbor > 80.0:
                continue

            n_obs = obss.get(neighbor_id)
            if n_obs is None or not hasattr(n_obs, "detected_objects") or not n_obs.detected_objects:
                continue

            for target_obj in n_obs.detected_objects:
                # If target is NOT directly visible to ego, it lies in ego's occlusion shadow!
                if id(target_obj) not in ego_detected_ids and hasattr(target_obj, "position"):
                    t_pos = (float(target_obj.position[0]), float(target_obj.position[1]))
                    t_dist = math.hypot(t_pos[0] - ego_pos[0], t_pos[1] - ego_pos[1])

                    # Only highlight targets within a realistic collaborative radius (e.g. 50m)
                    if t_dist <= 50.0:
                        from cav_demo.utils import format_agent_name
                        sender_name = format_agent_name(neighbor_id)
                        collaborative_targets.append((t_pos[0], t_pos[1], sender_name))
                        if t_dist < min_dist_found:
                            min_dist_found = t_dist
                            revealing_partner = sender_name

        self.resolved_occlusions_count = len(collaborative_targets)
        self.closest_collaborative_dist = min_dist_found
        self.revealing_partner_name = revealing_partner

        # 3. Draw green collaborative circles in Panda3D viewport
        self._render_green_circles(env, collaborative_targets, ego_pos)

        return self.get_summary()

    def _render_green_circles(
        self,
        env: Any,
        targets: List[Tuple[float, float, str]],
        ego_pos: Tuple[float, float]
    ):
        """Render 3D green beacon circles at all collaborative target locations."""
        engine = getattr(env, "engine", None)
        if engine is None or not hasattr(engine, "render") or engine.render is None:
            return

        # Clear previous frame's geometry
        self.clear_visualization()

        if not targets:
            return

        try:
            from panda3d.core import LineSegs, NodePath

            ls = LineSegs("v2v_collaborative_perception")
            # Bright fluorescent green for V2V augmentation
            ls.setColor(0.05, 1.0, 0.25, 1.0)
            ls.setThickness(2.8)

            z_height = 0.45  # Hover slightly above road asphalt to prevent z-fighting

            for tx, ty, sender_name in targets:
                # Draw outer green beacon circle
                for i in range(self.circle_segments + 1):
                    theta = i * 2.0 * math.pi / self.circle_segments
                    px = tx + self.circle_radius * math.cos(theta)
                    py = ty + self.circle_radius * math.sin(theta)
                    if i == 0:
                        ls.moveTo(px, py, z_height)
                    else:
                        ls.drawTo(px, py, z_height)

                # Draw inner concentric ring
                inner_r = self.circle_radius * 0.55
                for i in range(self.circle_segments + 1):
                    theta = i * 2.0 * math.pi / self.circle_segments
                    px = tx + inner_r * math.cos(theta)
                    py = ty + inner_r * math.sin(theta)
                    if i == 0:
                        ls.moveTo(px, py, z_height)
                    else:
                        ls.drawTo(px, py, z_height)

                # Draw crosshairs
                ls.moveTo(tx - self.circle_radius * 1.3, ty, z_height)
                ls.drawTo(tx + self.circle_radius * 1.3, ty, z_height)
                ls.moveTo(tx, ty - self.circle_radius * 1.3, z_height)
                ls.drawTo(tx, ty + self.circle_radius * 1.3, z_height)

            geom_node = ls.create()
            self._np = engine.render.attachNewNode(geom_node)
        except Exception:
            pass

    def clear_visualization(self):
        """Remove previously drawn green circles."""
        if self._np is not None:
            try:
                self._np.removeNode()
            except Exception:
                pass
            self._np = None

    def get_summary(self) -> Dict[str, Any]:
        """Return real-time collaborative perception statistics for HUD overlay."""
        return {
            "resolved_count": self.resolved_occlusions_count,
            "closest_dist": self.closest_collaborative_dist,
            "revealing_partner": self.revealing_partner_name,
            "active": self.resolved_occlusions_count > 0
        }

    def destroy(self):
        """Clean up all Panda3D resources upon shutdown."""
        self.clear_visualization()
