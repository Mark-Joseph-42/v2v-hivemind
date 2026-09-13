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
from cav_demo.utils import format_agent_name


def is_line_blocked(
    p_from: Tuple[float, float],
    p_to: Tuple[float, float],
    obstacles: List[Tuple[float, float]],
    vehicle_width: float = 2.4
) -> bool:
    """Return True if the line segment from p_from to p_to is blocked by any intervening obstacle."""
    x1, y1 = p_from
    x2, y2 = p_to
    dx = x2 - x1
    dy = y2 - y1
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq < 1e-4:
        return False

    for ox, oy in obstacles:
        vx = ox - x1
        vy = oy - y1
        t = (vx * dx + vy * dy) / seg_len_sq
        # Obstacle must lie strictly between p_from and p_to (with buffer)
        if 0.08 < t < 0.92:
            nx = x1 + t * dx
            ny = y1 + t * dy
            dist_to_ray = math.hypot(ox - nx, oy - ny)
            if dist_to_ray < (vehicle_width * 0.85):
                return True
    return False


class CollaborativePerceptionEngine:
    """
    Computes and visualizes collaborative beyond-line-of-sight perception.
    Fills in the ego vehicle's LiDAR occlusion shadow with radiant green markers
    using observations transmitted by neighboring CAVs over the V2V wireless mesh.
    """

    def __init__(self, circle_radius: float = 2.6, circle_segments: int = 24):
        self.circle_radius = circle_radius
        self.circle_segments = circle_segments
        self._np: Any = None

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

        # 1. Retrieve ego coordinates & elevation
        ego_pos = (float(ego_veh.position[0]), float(ego_veh.position[1]))
        if hasattr(ego_veh, "origin") and hasattr(ego_veh.origin, "getPos"):
            try:
                ego_z = float(ego_veh.origin.getPos()[2]) + 0.12
            except Exception:
                ego_z = 0.85
        else:
            ego_z = 0.85

        # 2. Collect all active peer CAVs within V2V communication range (80m)
        peer_cavs: List[Tuple[str, Tuple[float, float], float, Any]] = []
        for aid, veh in agents_dict.items():
            if aid == ego_agent_id:
                continue
            try:
                pos = (float(veh.position[0]), float(veh.position[1]))
                dist = math.hypot(pos[0] - ego_pos[0], pos[1] - ego_pos[1])
                if dist <= 80.0:
                    if hasattr(veh, "origin") and hasattr(veh.origin, "getPos"):
                        try:
                            vz = float(veh.origin.getPos()[2]) + 0.12
                        except Exception:
                            vz = 0.85
                    else:
                        vz = 0.85
                    peer_cavs.append((aid, pos, vz, veh))
            except Exception:
                pass

        # 3. Retrieve observation objects from MetaDrive
        obss: Dict[str, Any] = {}
        if hasattr(env, "agent_manager") and hasattr(env.agent_manager, "get_observations"):
            try:
                obss = env.agent_manager.get_observations()
            except Exception:
                obss = {}

        ego_obs = obss.get(ego_agent_id)
        ego_detected_ids: Set[int] = set()
        if ego_obs is not None and hasattr(ego_obs, "detected_objects") and ego_obs.detected_objects:
            ego_detected_ids = {id(obj) for obj in ego_obs.detected_objects}

        # 4. Collect all obstacle candidates (traffic vehicles + peer CAVs)
        all_obstacles: List[Tuple[str, Tuple[float, float], float, Any]] = []
        if hasattr(env, "engine") and hasattr(env.engine, "traffic_manager") and env.engine.traffic_manager:
            for tv in getattr(env.engine.traffic_manager, "vehicles", []):
                try:
                    tpos = (float(tv.position[0]), float(tv.position[1]))
                    tz = float(tv.origin.getPos()[2]) + 0.14 if hasattr(tv, "origin") else 0.85
                    all_obstacles.append(("traffic", tpos, tz, tv))
                except Exception:
                    pass

        for aid, pos, vz, veh in peer_cavs:
            all_obstacles.append((aid, pos, vz, veh))

        obs_positions = [pos for _, pos, _, _ in all_obstacles]

        # 5. Detect occluded targets (in LiDAR shadow or revealed by peer observation)
        collaborative_targets: List[Tuple[float, float, float, str, Optional[Tuple[float, float]]]] = []
        min_dist_found = 50.0
        revealing_partner = "NONE"
        processed_target_keys: Set[str] = set()

        # A. Sensor observation based unmasking (ETSI CPM standard)
        for peer_id, peer_pos, peer_z, _ in peer_cavs:
            p_obs = obss.get(peer_id)
            if p_obs is None or not hasattr(p_obs, "detected_objects") or not p_obs.detected_objects:
                continue

            sender_name = format_agent_name(peer_id)
            for target_obj in p_obs.detected_objects:
                # Do not treat ego vehicle as an occluded target to itself
                if target_obj is ego_veh or id(target_obj) == id(ego_veh):
                    continue

                if id(target_obj) not in ego_detected_ids and hasattr(target_obj, "position"):
                    t_pos = (float(target_obj.position[0]), float(target_obj.position[1]))
                    t_dist = math.hypot(t_pos[0] - ego_pos[0], t_pos[1] - ego_pos[1])
                    if 2.5 <= t_dist <= 60.0:
                        tz = float(target_obj.origin.getPos()[2]) + 0.14 if hasattr(target_obj, "origin") else 0.85
                        t_key = f"{t_pos[0]:.1f}_{t_pos[1]:.1f}"
                        if t_key not in processed_target_keys:
                            processed_target_keys.add(t_key)
                            collaborative_targets.append((t_pos[0], t_pos[1], tz, sender_name, peer_pos))
                            if t_dist < min_dist_found:
                                min_dist_found = t_dist
                                revealing_partner = sender_name

        # B. Geometric LiDAR shadow ray occlusion detection
        for tag, pos, tz, obj in all_obstacles:
            t_key = f"{pos[0]:.1f}_{pos[1]:.1f}"
            if t_key in processed_target_keys:
                continue

            t_dist = math.hypot(pos[0] - ego_pos[0], pos[1] - ego_pos[1])
            if t_dist > 60.0 or t_dist < 3.0:
                continue

            # Other obstacles that could block line-of-sight between ego and target
            intervening = [p for p in obs_positions if p != pos]
            if is_line_blocked(ego_pos, pos, intervening):
                # Find the best peer CAV that has unblocked line-of-sight to reveal target
                best_revealer = "NONE"
                best_revealer_pos: Optional[Tuple[float, float]] = None
                best_peer_dist = 999.0

                for peer_id, peer_pos, _, _ in peer_cavs:
                    if not is_line_blocked(peer_pos, pos, intervening):
                        p_dist = math.hypot(peer_pos[0] - pos[0], peer_pos[1] - pos[1])
                        if p_dist < best_peer_dist:
                            best_peer_dist = p_dist
                            best_revealer = format_agent_name(peer_id)
                            best_revealer_pos = peer_pos

                if best_revealer == "NONE" and peer_cavs:
                    # Fallback to nearest peer CAV within V2V mesh
                    sorted_peers = sorted(peer_cavs, key=lambda p: math.hypot(p[1][0] - pos[0], p[1][1] - pos[1]))
                    best_revealer = format_agent_name(sorted_peers[0][0])
                    best_revealer_pos = sorted_peers[0][1]

                if best_revealer != "NONE":
                    processed_target_keys.add(t_key)
                    collaborative_targets.append((pos[0], pos[1], tz, best_revealer, best_revealer_pos))
                    if t_dist < min_dist_found:
                        min_dist_found = t_dist
                        revealing_partner = best_revealer

        self.resolved_occlusions_count = len(collaborative_targets)
        if self.resolved_occlusions_count == 0:
            self.closest_collaborative_dist = 50.0
            self.revealing_partner_name = "NONE"
        else:
            self.closest_collaborative_dist = min_dist_found
            self.revealing_partner_name = revealing_partner

        # 6. Render 3D fluorescent green circles, mesh links, and cyan ego ring in Panda3D
        self._render_collaborative_scene(
            env=env,
            ego_pos=ego_pos,
            ego_z=ego_z,
            peer_cavs=peer_cavs,
            collaborative_targets=collaborative_targets
        )

        return self.get_summary()

    def _render_collaborative_scene(
        self,
        env: Any,
        ego_pos: Tuple[float, float],
        ego_z: float,
        peer_cavs: List[Tuple[str, Tuple[float, float], float, Any]],
        collaborative_targets: List[Tuple[float, float, float, str, Optional[Tuple[float, float]]]]
    ):
        """Render 3D fluorescent green beacon rings and V2V wireless mesh links in Panda3D."""
        engine = getattr(env, "engine", None)
        if engine is None or not hasattr(engine, "render") or engine.render is None:
            return

        # Clear previous frame's geometry
        self.clear_visualization()

        try:
            from panda3d.core import LineSegs

            ls = LineSegs("v2v_collaborative_perception")
            ls.setThickness(3.2)

            # 1. Draw Electric Cyan Ring around focused ego vehicle
            ls.setColor(0.15, 0.85, 1.0, 1.0)
            for i in range(self.circle_segments + 1):
                theta = i * 2.0 * math.pi / self.circle_segments
                px = ego_pos[0] + self.circle_radius * math.cos(theta)
                py = ego_pos[1] + self.circle_radius * math.sin(theta)
                if i == 0:
                    ls.moveTo(px, py, ego_z)
                else:
                    ls.drawTo(px, py, ego_z)

            # 2. Draw Radiant Green Rings & V2V Wireless Links on all peer CAVs
            ls.setColor(0.0, 1.0, 0.25, 1.0)
            for aid, peer_pos, peer_z, _ in peer_cavs:
                # Outer ring
                for i in range(self.circle_segments + 1):
                    theta = i * 2.0 * math.pi / self.circle_segments
                    px = peer_pos[0] + (self.circle_radius * 1.15) * math.cos(theta)
                    py = peer_pos[1] + (self.circle_radius * 1.15) * math.sin(theta)
                    if i == 0:
                        ls.moveTo(px, py, peer_z)
                    else:
                        ls.drawTo(px, py, peer_z)

                # Inner ring
                inner_r = self.circle_radius * 0.58
                for i in range(self.circle_segments + 1):
                    theta = i * 2.0 * math.pi / self.circle_segments
                    px = peer_pos[0] + inner_r * math.cos(theta)
                    py = peer_pos[1] + inner_r * math.sin(theta)
                    if i == 0:
                        ls.moveTo(px, py, peer_z)
                    else:
                        ls.drawTo(px, py, peer_z)

                # Crosshairs
                ch_len = self.circle_radius * 1.45
                ls.moveTo(peer_pos[0] - ch_len, peer_pos[1], peer_z)
                ls.drawTo(peer_pos[0] + ch_len, peer_pos[1], peer_z)
                ls.moveTo(peer_pos[0], peer_pos[1] - ch_len, peer_z)
                ls.drawTo(peer_pos[0], peer_pos[1] + ch_len, peer_z)

                # V2V Wireless Mesh Link Beam connecting ego to peer
                ls.moveTo(ego_pos[0], ego_pos[1], ego_z)
                ls.drawTo(peer_pos[0], peer_pos[1], peer_z)

            # 3. Draw High-Intensity Green Beacon Rings on occluded targets in shadow
            ls.setColor(0.05, 1.0, 0.20, 1.0)
            for tx, ty, tz, revealer_name, revealer_pos in collaborative_targets:
                # Concentric multi-tier beacon rings
                for r in [self.circle_radius * 1.35, self.circle_radius * 0.90, self.circle_radius * 0.45]:
                    for i in range(self.circle_segments + 1):
                        theta = i * 2.0 * math.pi / self.circle_segments
                        px = tx + r * math.cos(theta)
                        py = ty + r * math.sin(theta)
                        if i == 0:
                            ls.moveTo(px, py, tz)
                        else:
                            ls.drawTo(px, py, tz)

                # Prominent crosshairs
                ch_len = self.circle_radius * 1.70
                ls.moveTo(tx - ch_len, ty, tz)
                ls.drawTo(tx + ch_len, ty, tz)
                ls.moveTo(tx, ty - ch_len, tz)
                ls.drawTo(tx, ty + ch_len, tz)

                # Cooperative unmasking beam from revealing partner to target
                if revealer_pos is not None:
                    ls.moveTo(revealer_pos[0], revealer_pos[1], tz)
                    ls.drawTo(tx, ty, tz)

            geom_node = ls.create()
            self._np = engine.render.attachNewNode(geom_node)
            # Critical Panda3D render flags to guarantee vibrant visibility
            self._np.setLightOff()
            self._np.setShaderOff()
            self._np.setDepthTest(False)
            self._np.setBin("transparent", 100)
        except Exception:
            pass

    def clear_visualization(self):
        """Remove previously drawn green circles and mesh links."""
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
