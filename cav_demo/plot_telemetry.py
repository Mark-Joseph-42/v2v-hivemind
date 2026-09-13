"""
Plotting Utility for CAV Telemetry Logs.
Final Year Project - RSET
Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs

Generates publication-quality figures from recorded CSV logs for presentation slides:
1. Vehicle Speed Profiles over Time
2. V2V Communication Latency
3. Cooperative Braking Event Markers
"""

import os
import glob
import sys
import pandas as pd
import matplotlib.pyplot as plt


def plot_latest_log(log_dir: str = "logs", output_fig: str = "cav_evaluation_plot.png"):
    files = sorted(glob.glob(os.path.join(log_dir, "*.csv")), key=os.path.getmtime, reverse=True)
    if not files:
        print(f"No CSV logs found in '{log_dir}/'. Run a simulation with --log first.")
        return

    latest_file = files[0]
    print(f"Reading telemetry from: {latest_file}")
    df = pd.read_csv(latest_file)

    agents = df["agent_id"].unique()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # 1. Speed Profile Plot
    for aid in sorted(agents):
        sub = df[df["agent_id"] == aid]
        ax1.plot(sub["step"], sub["speed_kmh"], label=f"{aid.upper()} Speed (km/h)", linewidth=1.8)
        
        # Mark cooperative braking activations
        coop_events = sub[sub["coop_braking_active"] == 1]
        if not coop_events.empty:
            ax1.scatter(coop_events["step"], coop_events["speed_kmh"], color="red", s=30, zorder=5, label=f"{aid.upper()} V2V Brake Event" if aid == agents[0] else "")

    ax1.set_title("CAV Fleet Velocity Profiles & V2V Defensive Braking", fontsize=13, fontweight="bold")
    ax1.set_ylabel("Speed (km/h)", fontsize=11)
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="upper right")

    # 2. V2V Latency Plot
    sub0 = df[df["agent_id"] == agents[0]]
    ax2.plot(sub0["step"], sub0["v2v_avg_latency_ms"], color="darkgreen", label="Average V2V Latency (ms)", linewidth=1.5)
    ax2.axhline(12.0, color="gray", linestyle=":", label="Baseline Latency (12ms)")
    ax2.set_title("Simulated V2V Wireless Transmission Latency", fontsize=13, fontweight="bold")
    ax2.set_xlabel("Simulation Step", fontsize=11)
    ax2.set_ylabel("Latency (ms)", fontsize=11)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(output_fig, dpi=300)
    print(f"[Success] Evaluation plot saved to: {output_fig}")


if __name__ == "__main__":
    plot_latest_log()
