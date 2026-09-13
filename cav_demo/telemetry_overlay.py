"""
Live Telemetry & V2V Communication HUD Overlay using Panda3D OnScreenText.
Final Year Project - RSET
Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs

Renders a sleek, real-time telemetry sidebar on the right side of the 3D window,
displaying live kinematic readings, V2V packet transfers, and emergency alerts.
"""

import math
import time
from typing import Any, Dict, List, Optional
from cav_demo.config import HUDConfig
from cav_demo.v2v_network import V2VNetworkMesh, V2VPacket
from cav_demo.utils import format_agent_name, rad_to_deg, mps_to_kmh


class TelemetryHUD:
    """
    On-screen dashboard overlay for Panda3D rendering window.
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

            # Sidebar Text Node (Right side of screen)
            self._onscreen_text = OnscreenText(
                text="INITIALIZING V2V TELEMETRY...",
                pos=(self.config.sidebar_x, self.config.sidebar_top_y),
                scale=self.config.font_size,
                fg=self.config.normal_color,
                align=TextNode.ALeft,
                mayChange=True,
                shadow=(0, 0, 0, 0.8),
                shadowOffset=(0.04, 0.04)
            )

            # Bottom Controls & Status Banner
            self._bottom_banner = OnscreenText(
                text="[Left/Right Arrow] Cycle Camera | [W/A/S/D] Drive | [Esc] Exit",
                pos=(0.0, -0.95),
                scale=0.042,
                fg=(1.0, 0.9, 0.3, 1.0),
                align=TextNode.ACenter,
                mayChange=True,
                shadow=(0, 0, 0, 0.9),
                shadowOffset=(0.04, 0.04)
            )

            self._initialized = True
        except Exception as e:
            # Fallback if running headless or Panda3D GUI unavailable
            self._initialized = False

    def update(
        self,
        env: Any,
        focused_agent_id: str,
        v2v_mesh: V2VNetworkMesh,
        actions_dict: Optional[Dict[str, Any]] = None,
        mode: str = "fleet",
        is_coop_braking: bool = False
    ):
        """
        Update the on-screen telemetry feed with the latest vehicle states and V2V packets.
        """
        now = time.time()
        if now - self.last_update_time < self.config.update_interval_s:
            return
        self.last_update_time = now

        if not self._initialized:
            self.init_hud(env)

        # 1. Format the telemetry string
        text_content, banner_content, banner_fg = self._generate_hud_strings(
            env=env,
            focused_agent_id=focused_agent_id,
            v2v_mesh=v2v_mesh,
            actions_dict=actions_dict,
            mode=mode,
            is_coop_braking=is_coop_braking
        )

        # 2. Update Panda3D text nodes if active
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

    def _generate_hud_strings(
        self,
        env: Any,
        focused_agent_id: str,
        v2v_mesh: V2VNetworkMesh,
        actions_dict: Optional[Dict[str, Any]],
        mode: str,
        is_coop_braking: bool
    ) -> (str, str, tuple):
        """Construct formatted telemetry text blocks."""
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

        # Build Sidebar Dashboard Text
        lines = [
            "+-----------------------------------+",
            "|    FLEET TELEMETRY DASHBOARD      |",
            "|   RSET Final Year B.Tech CAV Demo |",
            "+-----------------------------------+",
            f"| Active View:  {focused_name} ({mode.upper()})",
            "| ---------------------------------",
            f"| Speed       : {speed_kmh:5.1f} km/h",
            f"| Heading     : {heading_deg:5.1f} deg",
            f"| Steering    : {steer:+5.2f} rad",
            f"| Throttle    : {throttle:+5.2f}",
            f"| Lane Index  : {lane}",
            "+-----------------------------------+",
            "|    V2V WIRELESS MESH STATUS       |",
            "+-----------------------------------+",
            f"| Active Links: {links} connected",
            f"| Avg Latency : {avg_lat:4.1f} ms",
            f"| Packet Loss : {drop_pct:4.1f} %",
            "| ---------------------------------",
            "| INCOMING V2V TELEMETRY STREAM:    "
        ]

        # Show incoming packets from neighbors
        rx_packets = v2v_mesh.received_packets.get(focused_agent_id, [])
        if rx_packets:
            seen_senders = set()
            count = 0
            for pkt in rx_packets:
                if pkt.sender_id not in seen_senders and count < 4:
                    seen_senders.add(pkt.sender_id)
                    count += 1
                    status_flag = " [BRAKE!]" if pkt.is_braking else ""
                    lines.append(f"| [{pkt.sender_display}] {pkt.speed_kmh:4.1f}kph {pkt.latency_ms:3.0f}ms{status_flag}")
        else:
            lines.append("| (Listening for neighbor broadcasts...)")

        lines.append("+-----------------------------------+")
        lines.append("| FLEET STATUS:                     ")
        for aid in sorted(agents_dict.keys()):
            aname = format_agent_name(aid)
            tag = " [FOCUS]" if aid == focused_agent_id else " [AUTO]"
            if mode == "human" and aid in ("agent0", "agent_0"):
                tag = " [HUMAN]"
            st = v2v_mesh.latest_states.get(aid)
            spd_str = f"{st.speed_kmh:4.0f}kph" if st else " --"
            brk_str = " *BRAKE*" if (st and st.is_braking) else ""
            lines.append(f"|  * {aname}{tag:8s} {spd_str}{brk_str}")

        lines.append("+-----------------------------------+")

        # Bottom banner logic
        if is_coop_braking or warnings:
            banner_text = f"[!] V2V COLLISION AVOIDANCE ACTIVE: Emergency brake signal received! [Tracking: {focused_name}]"
            banner_fg = (1.0, 0.2, 0.2, 1.0)
        else:
            banner_text = f"[Left/Right Arrow] Cycle Focus | Tracking: {focused_name} | Mode: {mode.upper()}"
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
