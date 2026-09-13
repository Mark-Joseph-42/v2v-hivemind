"""
Main Entry Point for MetaDrive Multi-Agent CAV Telemetry & Control Demo.
Final Year Project - RSET
Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs

Usage:
    # Fleet Observation Mode (All autonomous CAVs, arrow key camera cycling)
    python main.py --mode fleet --agents 4 --map 5

    # Human-in-the-Loop Mode (Agent_0 keyboard driving, AI fleet cooperative defense)
    python main.py --mode human --agents 4 --map 5
"""

import argparse
import os
import sys
import time
from typing import Dict, Any

# Ensure project root is on sys.path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from cav_demo.config import SimulationConfig, V2VConfig, CameraConfig, HUDConfig, MinimapConfig
from cav_demo.env_setup import create_env, get_active_agents_dict
from cav_demo.v2v_network import V2VNetworkMesh
from cav_demo.camera_controller import CameraController
from cav_demo.telemetry_overlay import TelemetryHUD
from cav_demo.minimap_renderer import MinimapRenderer
from cav_demo.idm_fleet_policy import IDMFleetController
from cav_demo.human_mode import HumanInTheLoopManager
from cav_demo.logger import TelemetryLogger
from cav_demo.utils import print_banner, Colors, format_agent_name


def parse_args():
    parser = argparse.ArgumentParser(
        description="RSET CAV Multi-Agent Telemetry & Orchestration Demonstration"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["fleet", "human"],
        default="fleet",
        help="Operating mode: 'fleet' (autonomous fleet observation) or 'human' (interactive human driving)"
    )
    parser.add_argument(
        "--agents",
        type=int,
        default=4,
        help="Number of CAV agents in the simulation (default: 4)"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        choices=["corridor", "roundabout", "intersection", "bottleneck", "tollgate", "parking"],
        default="corridor",
        help="Multi-Agent traffic environment scenario: 'corridor' (default highway), 'roundabout', 'intersection', 'bottleneck', 'tollgate', or 'parking'"
    )
    parser.add_argument(
        "--map",
        type=int,
        default=5,
        help="Procedural highway map complexity in blocks (default: 5)"
    )
    parser.add_argument(
        "--traffic",
        type=float,
        default=0.08,
        help="NPC civilian traffic density (default: 0.08)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without 3D window (for automated testing and benchmarking)"
    )
    parser.add_argument(
        "--hide-lidar",
        action="store_true",
        help="Hide real-time 3D laser scan rays in viewport"
    )
    parser.add_argument(
        "--disable-coop",
        action="store_true",
        help="Disable V2V cooperative braking (to demonstrate single-agent vs cooperative comparison)"
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Record telemetry data to CSV in logs/ for plotting evaluation figures"
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Maximum simulation steps to run before exiting (default: unlimited)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Print RSET Demonstration Banner
    print_banner(mode=args.mode, num_agents=args.agents)

    # 2. Build Configurations
    sim_cfg = SimulationConfig(
        num_agents=args.agents,
        map_blocks=args.map,
        scenario=args.scenario,
        traffic_density=args.traffic,
        use_render=not args.headless,
        manual_control=(args.mode == "human"),
        show_lidar=not args.hide_lidar
    )
    v2v_cfg = V2VConfig()
    cam_cfg = CameraConfig()
    hud_cfg = HUDConfig()
    mini_cfg = MinimapConfig(enabled=not args.headless)

    # 3. Create Environment
    print(f"{Colors.BLUE}[MetaDrive]{Colors.ENDC} Initializing PGMA Multi-Agent Environment ({args.agents} CAVs)...")
    env = create_env(config=sim_cfg, mode=args.mode, headless=args.headless)

    # 4. Instantiate Subsystems
    v2v_mesh = V2VNetworkMesh(config=v2v_cfg)
    cam_ctrl = CameraController(config=cam_cfg)
    telemetry_hud = TelemetryHUD(config=hud_cfg)
    minimap = MinimapRenderer(config=mini_cfg)

    enable_coop = not args.disable_coop
    fleet_controller = IDMFleetController(enable_coop_braking=enable_coop)
    human_manager = HumanInTheLoopManager(human_agent_id="agent0")
    logger = TelemetryLogger(enabled=args.log)

    try:
        # 5. Reset Environment
        print(f"{Colors.BLUE}[MetaDrive]{Colors.ENDC} Resetting scene and establishing V2V wireless mesh...")
        reset_res = env.reset()
        if isinstance(reset_res, tuple):
            obs, info = reset_res
        else:
            obs, info = reset_res, {}

        # Set up Panda3D arrow key camera switching and initialize focus
        cam_ctrl.setup_panda3d_listeners(env)
        initial_focus = cam_ctrl.get_focused_agent_id(env)

        print(f"{Colors.GREEN}[Ready]{Colors.ENDC} Live demo running! Press Left/Right arrow keys to cycle camera.")
        if args.mode == "human":
            print(f"{Colors.YELLOW}[Interactive]{Colors.ENDC} Use W/A/S/D to drive CAV_01. Slam 'S' to broadcast emergency brake!")

        step = 0
        running = True
        actions_last = {}

        while running:
            step += 1

            # A. Retrieve active agents
            agents = get_active_agents_dict(env)
            if not agents:
                # No active agents, reset
                env.reset()
                continue

            # B. Generate Actions
            if args.mode == "human":
                actions = human_manager.get_fleet_actions(env, agents, v2v_mesh)
            else:
                actions = fleet_controller.get_actions(agents, v2v_mesh)

            actions_last = actions

            # C. Step Physics Simulation
            step_res = env.step(actions)
            if len(step_res) == 5:
                obs, rewards, dones, truncs, infos = step_res
            else:
                obs, rewards, dones, infos = step_res
                truncs = {}

            # D. Execute V2V Wireless Mesh Broadcast
            v2v_mesh.broadcast_step(agents, step=step, actions_dict=actions)

            # E. Camera & Telemetry HUD Update
            focused_id = cam_ctrl.get_focused_agent_id(env)
            is_coop = False
            if args.mode == "human":
                is_coop = human_manager.is_coop_braking(focused_id)
            else:
                is_coop = fleet_controller.is_coop_braking(focused_id)

            telemetry_hud.update(
                env=env,
                focused_agent_id=focused_id,
                v2v_mesh=v2v_mesh,
                actions_dict=actions,
                mode=args.mode,
                is_coop_braking=is_coop
            )

            # F. Minimap PiP Update
            minimap.update(env, focused_id)

            # G. Telemetry Logging (if enabled)
            if args.log:
                coop_dict = {
                    aid: (human_manager.is_coop_braking(aid) if args.mode == "human" else fleet_controller.is_coop_braking(aid))
                    for aid in agents
                }
                logger.log_step(step, agents, v2v_mesh, actions, coop_dict)

            # H. Terminal Heartbeat (every 100 steps)
            if step % 100 == 0:
                stats = v2v_mesh.get_aggregate_stats()
                print(
                    f"{Colors.DIM}[Step {step:05d}]{Colors.ENDC} "
                    f"Tracking: {Colors.BOLD}{format_agent_name(focused_id)}{Colors.ENDC} | "
                    f"Active CAVs: {len(agents)} | "
                    f"V2V Avg Latency: {stats['avg_latency_ms']:.1f}ms | "
                    f"Packets Dropped: {stats['drop_rate_pct']:.1f}%"
                )

            # I. Check Termination / Episode Reset
            all_done = dones.get("__all__", False) if isinstance(dones, dict) else False
            if all_done:
                print(f"{Colors.YELLOW}[Episode End]{Colors.ENDC} Horizon reached. Resetting fleet positions...")
                env.reset()
                fleet_controller.reset()
                human_manager.reset()
                v2v_mesh.reset()

            if args.max_steps is not None and step >= args.max_steps:
                print(f"\nReached target limit of {args.max_steps} steps. Exiting demonstration.")
                break

    except KeyboardInterrupt:
        print("\n\nDemonstration paused by user (KeyboardInterrupt). Exiting cleanly...")
    finally:
        telemetry_hud.destroy()
        minimap.destroy()
        logger.close()
        try:
            env.close()
        except Exception:
            pass
        print(f"{Colors.GREEN}[Shutdown]{Colors.ENDC} Simulation closed successfully. Thank you!")


if __name__ == "__main__":
    main()
