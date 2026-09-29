"""
Live Telemetry & V2V Communication HUD Overlay using Panda3D OnScreenText.
Final Year Project - RSET
Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs

Renders a sleek, real-time telemetry sidebar on the right side of the 3D window,
displaying live kinematic readings, V2V packet transfers, and emergency alerts.
"""

import math
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from cav_demo.config import HUDConfig
from cav_demo.v2v_network import V2VNetworkMesh, V2VPacket
from cav_demo.utils import format_agent_name, rad_to_deg, mps_to_kmh


class TelemetryHUD:
    """
    On-screen dashboard overlay for Panda3D rendering window.
    Organized into:
    - Top Right: MetaDrive Vehicle Telemetry (Speed, Heading, Lane, Steer, Throttle, V2V mesh)
    - Right Side: 360° LiDAR Perception Sensor (72 laser rays, sector clearances, radar compass)
    - Lower Right: Fleet Status overview
    """

    def __init__(self, config: Optional[HUDConfig] = None):
        self.config = config or HUDConfig()
        self.last_update_time: float = 0.0
        self._onscreen_text: Any = None
        self._bottom_banner: Any = None
        self._initialized: bool = False

    def init_hud(self, env: Any):
        """Initialize Panda3D OnscreenText nodes if rendering is enabled."""
        if self._initialized:
            return

        engine = getattr(env, "engine", None)
        if engine is None:
            return

        try:
            from direct.gui.OnscreenText import OnscreenText
            from panda3d.core import TextNode

            # Unified Multi-Panel Sidebar (Bottom-Right Vehicle Telemetry & LiDAR Perception)
            self._onscreen_text = OnscreenText(
                text="INITIALIZING V2V & LIDAR TELEMETRY...",
                pos=(self.config.sidebar_x, self.config.sidebar_top_y),
                scale=self.config.font_size,
                fg=self.config.normal_color,
                bg=getattr(self.config, "card_bg_color", (0.02, 0.04, 0.08, 0.78)),
                align=TextNode.ALeft,
                mayChange=True,
                shadow=(0, 0, 0, 0.95),
                shadowOffset=(0.04, 0.04)
            )

            # Bottom Controls & Status Banner
            self._bottom_banner = OnscreenText(
                text="[Left/Right Arrow] Cycle Camera | [P / V] Toggle BEV View | [W/A/S/D] Drive | [Esc] Exit",
                pos=(0.0, -0.95),
                scale=0.040,
                fg=(1.0, 0.9, 0.3, 1.0),
                align=TextNode.ACenter,
                mayChange=True,
                shadow=(0, 0, 0, 0.95),
                shadowOffset=(0.04, 0.04)
            )

            self._initialized = True
        except Exception:
            self._initialized = False

    def update(
        self,
        env: Any,
        focused_agent_id: str,
        v2v_mesh: V2VNetworkMesh,
        actions_dict: Optional[Dict[str, Any]] = None,
        mode: str = "fleet",
        is_coop_braking: bool = False,
        collab_summary: Optional[Dict[str, Any]] = None,
        view_mode: str = "chase",
        is_paused: bool = False
    ):
        """
        Update the on-screen telemetry feed with the latest vehicle states, LiDAR rays, and V2V packets.
        """
        now = time.time()
        if now - self.last_update_time < self.config.update_interval_s:
            return
        self.last_update_time = now

        if not self._initialized:
            self.init_hud(env)

        text_content, banner_content, banner_fg = self._generate_hud_strings(
            env=env,
            focused_agent_id=focused_agent_id,
            v2v_mesh=v2v_mesh,
            actions_dict=actions_dict,
            mode=mode,
            is_coop_braking=is_coop_braking,
            collab_summary=collab_summary,
            view_mode=view_mode,
            is_paused=is_paused
        )

        if self._onscreen_text is not None:
            try:
                self._onscreen_text.setText(text_content)
            except Exception:
                pass

        if self._bottom_banner is not None:
            try:
                self._bottom_banner.setText(banner_content)
                self._bottom_banner.setFg(banner_fg)
            except Exception:
                pass

    def _extract_lidar(self, env: Any, agent_id: str) -> Dict[str, Any]:
        """Extract 360-degree LiDAR cloud points and compute sector clearances."""
        max_dist = 50.0
        try:
            if hasattr(env, "agent_manager") and hasattr(env.agent_manager, "get_observations"):
                obs_dict = env.agent_manager.get_observations()
                obs_obj = obs_dict.get(agent_id)
                if obs_obj is not None and hasattr(obs_obj, "cloud_points") and obs_obj.cloud_points is not None:
                    pts = np.array(obs_obj.cloud_points, dtype=float)
                    num_pts = len(pts)
                    if num_pts > 0:
                        dists = pts * max_dist
                        
                        f_idx = np.concatenate([np.arange(0, 4), np.arange(num_pts - 4, num_pts)])
                        fr_idx = np.arange(4, 15)
                        r_idx = np.arange(15, 22)
                        rear_idx = np.arange(32, 41)
                        l_idx = np.arange(51, 58)
                        fl_idx = np.arange(58, num_pts - 4)

                        f_dist = float(np.min(dists[f_idx]))
                        fr_dist = float(np.min(dists[fr_idx]))
                        r_dist = float(np.min(dists[r_idx]))
                        rear_dist = float(np.min(dists[rear_idx]))
                        l_dist = float(np.min(dists[l_idx]))
                        fl_dist = float(np.min(dists[fl_idx]))
                        min_dist = float(np.min(dists))

                        sector_map = [
                            ("FRONT", f_dist),
                            ("F-RIGHT", fr_dist),
                            ("RIGHT", r_dist),
                            ("REAR", rear_dist),
                            ("LEFT", l_dist),
                            ("F-LEFT", fl_dist)
                        ]
                        closest_name = min(sector_map, key=lambda x: x[1])[0]

                        return {
                            "active": True,
                            "min_dist": min_dist,
                            "closest_sector": closest_name,
                            "front": f_dist,
                            "front_left": fl_dist,
                            "front_right": fr_dist,
                            "left": l_dist,
                            "right": r_dist,
                            "rear": rear_dist,
                            "num_lasers": num_pts
                        }
        except Exception:
            pass

        return {
            "active": False,
            "min_dist": max_dist,
            "closest_sector": "CLEAR",
            "front": max_dist,
            "front_left": max_dist,
            "front_right": max_dist,
            "left": max_dist,
            "right": max_dist,
            "rear": max_dist,
            "num_lasers": 72
        }

    @staticmethod
    def _format_bar(dist: float, max_range: float = 50.0, width: int = 8) -> str:
        """Create a visual clearance bar with distance and status label."""
        ratio = min(1.0, max(0.0, dist / max_range))
        filled = int(round(ratio * width))
        bar = "=" * filled + " " * (width - filled)
        if dist > 25.0:
            status = "CLEAR"
        elif dist > 12.0:
            status = "WARN "
        else:
            status = "ALERT"
        return f"[{bar}] {dist:4.1f}m {status}"

    def _generate_hud_strings(
        self,
        env: Any,
        focused_agent_id: str,
        v2v_mesh: V2VNetworkMesh,
        actions_dict: Optional[Dict[str, Any]],
        mode: str,
        is_coop_braking: bool,
        collab_summary: Optional[Dict[str, Any]] = None,
        view_mode: str = "chase",
        is_paused: bool = False
    ) -> Tuple[str, str, tuple]:
        """Construct formatted multi-panel telemetry and LiDAR text."""
        focused_name = format_agent_name(focused_agent_id)
        agents_dict = getattr(env, "agents", {})
        veh = agents_dict.get(focused_agent_id)

        speed_kmh = 0.0
        heading_deg = 0.0
        steer = 0.0
        throttle = 0.0
        lane = 0

        if veh is not None:
            try:
                vel = veh.velocity if hasattr(veh, "velocity") else (0.0, 0.0)
                speed_kmh = mps_to_kmh(math.hypot(vel[0], vel[1]))
                if hasattr(veh, "heading_theta"):
                    heading_deg = rad_to_deg(veh.heading_theta)
                if hasattr(veh, "lane_index") and veh.lane_index:
                    lane = veh.lane_index[-1] if isinstance(veh.lane_index, tuple) else veh.lane_index
            except Exception:
                pass

        if actions_dict and focused_agent_id in actions_dict:
            act = actions_dict[focused_agent_id]
            steer = float(act[0])
            throttle = float(act[1])

        # V2V network metrics
        stats = v2v_mesh.get_aggregate_stats()
        links = stats["active_links"]
        avg_lat = stats["avg_latency_ms"]
        drop_pct = stats["drop_rate_pct"]

        # Warnings
        warnings = v2v_mesh.get_emergency_brake_warnings(focused_agent_id)

        # Extract LiDAR readings for focused vehicle
        lidar = self._extract_lidar(env, focused_agent_id)

        # -------------------------------------------------------------
        # 1. BOTTOM-RIGHT: CAV FLEET & VEHICLE TELEMETRY
        # -------------------------------------------------------------
        view_tag = "BEV" if view_mode == "bev" else "3D"
        status_tag = "⏸ PAUSED" if is_paused else "RUNNING"
        lines = [
            "+-- CAV FLEET TELEMETRY ------------+",
            f"| Status   : {status_tag:<10s} [{view_tag} View]",
            f"| Focused  : {focused_name} ({mode.upper()})",
            f"| Speed    : {speed_kmh:5.1f} km/h | Lane: {lane}",
            f"| Heading  : {heading_deg:5.1f} deg | Steer: {steer:+4.2f}",
            f"| V2V Mesh : {links} links | Lat: {avg_lat:4.1f}ms ({drop_pct:.1f}%)",
            "+-----------------------------------+",
        ]

        # -------------------------------------------------------------
        # 2. 360° LIDAR PERCEPTION SENSOR
        # -------------------------------------------------------------
        obs_tag = f"{lidar['min_dist']:4.1f}m [{lidar['closest_sector']}]" if lidar['min_dist'] < 48.0 else "CLEAR (>48m)"
        lines.extend([
            "+-- 360 LIDAR PERCEPTION SENSOR ----+",
            f"| Hazard : {obs_tag:18s} ({lidar['num_lasers']} Lasers)",
            f"| FRONT  : {self._format_bar(lidar['front'])}",
            f"| F-LEFT : {self._format_bar(lidar['front_left'])}",
            f"| F-RGHT : {self._format_bar(lidar['front_right'])}",
            f"| LEFT   : {self._format_bar(lidar['left'])}",
            f"| RIGHT  : {self._format_bar(lidar['right'])}",
            f"| REAR   : {self._format_bar(lidar['rear'])}",
            "+-----------------------------------+",
        ])

        # -------------------------------------------------------------
        # 2b. V2V COLLABORATIVE PERCEPTION (BLOS AUGMENTATION)
        # -------------------------------------------------------------
        if collab_summary and collab_summary.get("active", False):
            c_cnt = collab_summary.get("resolved_count", 0)
            c_dist = collab_summary.get("closest_dist", 50.0)
            c_partner = collab_summary.get("revealing_partner", "NONE")
            collab_lines = [
                "+-- V2V COLLABORATIVE PERCEPTION ---+",
                f"| BLOS Status : ACTIVE [UNMASKED]",
                f"| Occluded    : {c_cnt} targets (via {c_partner})",
                f"| Closest BLOS: {c_dist:4.1f}m [GREEN BEACON]",
                "+-----------------------------------+",
            ]
        else:
            collab_lines = [
                "+-- V2V COLLABORATIVE PERCEPTION ---+",
                f"| BLOS Status : STANDBY (Receiving CPM)",
                f"| Markers     : Ready for Blind-Spots",
                "+-----------------------------------+",
            ]
        lines.extend(collab_lines)

        # -------------------------------------------------------------
        # 3. ACTIVE CAV FLEET STATUS
        # -------------------------------------------------------------
        lines.append("+-- ACTIVE CAV FLEET STATUS --------+")
        for aid in sorted(agents_dict.keys()):
            aname = format_agent_name(aid)
            tag = " [FOCUS]" if aid == focused_agent_id else " [AUTO]"
            if mode == "human" and aid in ("agent0", "agent_0"):
                tag = " [HUMAN]"
            st = v2v_mesh.latest_states.get(aid)
            spd_str = f"{st.speed_kmh:4.0f}kph" if st else " --"
            brk_str = " *BRK*" if (st and st.is_braking) else ""
            lines.append(f"|  * {aname}{tag:8s} {spd_str}{brk_str}")

        lines.append("+-----------------------------------+")

        # Bottom banner logic
        if is_paused:
            view_label = "3D View" if view_mode == "bev" else "BEV View"
            banner_text = f"⏸ SIMULATION PAUSED | [Space] Resume | [◄ / ►] Cycle CAV | [P / V] Switch to {view_label} | Tracking: {focused_name}"
            banner_fg = (1.0, 0.85, 0.1, 1.0)
        elif is_coop_braking or warnings:
            banner_text = f"[!] V2V COLLISION AVOIDANCE ACTIVE: Emergency brake signal received! [Tracking: {focused_name}]"
            banner_fg = (1.0, 0.2, 0.2, 1.0)
        elif collab_summary and collab_summary.get("active", False):
            c_partner = collab_summary.get("revealing_partner", "PEER")
            banner_text = f"[+] V2V COLLABORATIVE PERCEPTION ACTIVE: Hidden obstacle revealed by {c_partner}! | [P / V] Toggle View"
            banner_fg = (0.2, 1.0, 0.3, 1.0)
        else:
            view_label = "3D View" if view_mode == "bev" else "BEV View"
            banner_text = f"[◄ / ►] Cycle CAV | [Space] Pause | [P / V] Switch to {view_label} | Tracking: {focused_name} | Mode: {mode.upper()}"
            banner_fg = (0.2, 1.0, 0.4, 1.0)

        return "\n".join(lines), banner_text, banner_fg

    def destroy(self):
        """Clean up GUI elements upon shutdown."""
        if self._onscreen_text is not None:
            try:
                self._onscreen_text.destroy()
            except Exception:
                pass
        if self._bottom_banner is not None:
            try:
                self._bottom_banner.destroy()
            except Exception:
                pass
