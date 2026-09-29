"""
Generate an Ultra-Clean, Professional, and Highly Intuitive System Architecture
Diagram for Slide 5 of the B.Tech Final Year Evaluation at RSET.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_clean_architecture(output_path="overall_system_architecture.png"):
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    ax.set_xlim(0, 160)
    ax.set_ylim(0, 92)
    ax.axis('off')

    # Clean off-white canvas
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    # Slide Diagram Title
    ax.text(80, 88.5, "SYSTEM ARCHITECTURE OVERVIEW",
            ha='center', va='center', fontsize=17, weight='bold', color='#0F172A', fontfamily='sans-serif')
    ax.text(80, 85.5, "Decentralized Cyber-Physical Architecture for Connected Autonomous Vehicles",
            ha='center', va='center', fontsize=10.5, color='#64748B', fontfamily='sans-serif')

    # Color definitions
    palettes = {
        'sim':    {'border': '#2563EB', 'bg': '#F1F5FD', 'badge': '#1D4ED8', 'title': '#1E40AF', 'sub_bg': '#FFFFFF', 'accent_bg': '#DBEAFE'},
        'v2v':    {'border': '#059669', 'bg': '#F0FDF4', 'badge': '#047857', 'title': '#065F46', 'sub_bg': '#FFFFFF', 'accent_bg': '#D1FAE5'},
        'plan':   {'border': '#7C3AED', 'bg': '#FAF5FF', 'badge': '#6D28D9', 'title': '#5B21B6', 'sub_bg': '#FFFFFF', 'accent_bg': '#EDE9FE'},
        'ui':     {'border': '#D97706', 'bg': '#FFFBEB', 'badge': '#B45309', 'title': '#92400E', 'sub_bg': '#FFFFFF', 'accent_bg': '#FEF3C7'}
    }

    # Helper: draw layer container
    def draw_layer(x, y, w, h, title, subtitle, member_tag, pal):
        # Card shadow
        shadow = patches.FancyBboxPatch((x+0.3, y-0.3), w, h, boxstyle="round,pad=0.2,rounding_size=1.2",
                                        facecolor='#E2E8F0', edgecolor='none', zorder=1)
        ax.add_patch(shadow)
        # Main card
        card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=1.2",
                                      facecolor=pal['bg'], edgecolor=pal['border'], linewidth=1.6, zorder=2)
        ax.add_patch(card)
        # Title text
        ax.text(x + 2.5, y + h - 2.5, title, ha='left', va='center', fontsize=10.5,
                weight='bold', color=pal['title'], zorder=3, fontfamily='sans-serif')
        ax.text(x + 2.5, y + h - 4.5, subtitle, ha='left', va='center', fontsize=7.5,
                color='#64748B', zorder=3, fontfamily='sans-serif')
        # Member Badge
        tag = patches.FancyBboxPatch((x + w - 34, y + h - 3.8), 32, 2.6, boxstyle="round,pad=0.1,rounding_size=0.8",
                                     facecolor=pal['badge'], edgecolor='none', zorder=3)
        ax.add_patch(tag)
        ax.text(x + w - 18, y + h - 2.5, member_tag, ha='center', va='center', fontsize=8,
                weight='bold', color='#FFFFFF', zorder=4, fontfamily='sans-serif')

    # Helper: draw module box
    def draw_box(x, y, w, h, title, items, fill='#FFFFFF', border='#CBD5E1', title_color='#0F172A'):
        b = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=0.7",
                                   facecolor=fill, edgecolor=border, linewidth=1.2, zorder=5)
        ax.add_patch(b)
        ax.text(x + w/2, y + h - 1.8, title, ha='center', va='center', fontsize=9,
                weight='bold', color=title_color, zorder=6, fontfamily='sans-serif')
        y_text = y + h - 3.8
        for it in items:
            ax.text(x + w/2, y_text, it, ha='center', va='center', fontsize=7.6,
                    color='#334155', zorder=6, fontfamily='sans-serif')
            y_text -= 1.6

    # =========================================================================
    # 4 HORIZONTAL ARCHITECTURE LAYERS (Bottom to Top)
    # =========================================================================

    # LAYER 1: PHYSICAL SIMULATION LAYER
    y_l1 = 6.5
    h_l1 = 16.5
    draw_layer(8, y_l1, 134, h_l1,
               "1. PHYSICAL SIMULATION & ENVIRONMENT LAYER",
               "Real-Time 3D Physics Engine (50 Hz Bullet) & Multi-Agent Road Dynamics",
               "Mark Joseph — Lead", palettes['sim'])
    draw_box(11, y_l1 + 1.5, 30, 9.5, "MetaDrive Simulator",
             ["Procedural Road Topologies", "Frictional Tire-Road Physics"],
             fill=palettes['sim']['sub_bg'], border=palettes['sim']['border'])
    draw_box(44, y_l1 + 1.5, 30, 9.5, "Connected Fleet (CAVs)",
             ["Autonomous CAV_01 - CAV_04", "360° LiDAR Scans (72 Rays)"],
             fill=palettes['sim']['accent_bg'], border=palettes['sim']['border'], title_color='#1E40AF')
    draw_box(77, y_l1 + 1.5, 30, 9.5, "Human Vehicle (Agent_0)",
             ["Manual Keyboard (W/A/S/D)", "Injected Sudden Braking"],
             fill='#FEF3C7', border='#D97706', title_color='#B45309')
    draw_box(110, y_l1 + 1.5, 29, 9.5, "Civilian Traffic (NPCs)",
             ["Rule-Based Background Cars", "Natural Multi-Lane Flow"],
             fill=palettes['sim']['sub_bg'], border='#94A3B8')

    # LAYER 2: V2V COMMUNICATION & PERCEPTION LAYER
    y_l2 = 26.0
    h_l2 = 16.5
    draw_layer(8, y_l2, 134, h_l2,
               "2. CYBER-PHYSICAL V2V & PERCEPTION LAYER",
               "Ad-Hoc Wireless Mesh (80m Radius) & Beyond-Line-of-Sight (BLOS) Sensing",
               "Neha & Sanjana", palettes['v2v'])
    draw_box(11, y_l2 + 1.5, 30, 9.5, "Kinematic Extractor",
             ["11D Continuous State Vector", "Speed, Heading, Yaw Rate"],
             fill=palettes['v2v']['sub_bg'], border=palettes['v2v']['border'])
    draw_box(44, y_l2 + 1.5, 30, 9.5, "V2V Wireless Mesh",
             ["80m Ad-Hoc Geometric Broadcast", "Peer-to-Peer Packet Protocol"],
             fill=palettes['v2v']['accent_bg'], border=palettes['v2v']['border'], title_color='#065F46')
    draw_box(77, y_l2 + 1.5, 30, 9.5, "Channel Noise Emulation",
             ["Gaussian Jitter (μ=12ms)", "Bernoulli Packet Loss (2%)"],
             fill=palettes['v2v']['sub_bg'], border=palettes['v2v']['border'])
    draw_box(110, y_l2 + 1.5, 29, 9.5, "BLOS Perception Engine",
             ["Ray-Casting Blind Spot Unmasking", "Shared Cooperative Hazard Map"],
             fill=palettes['v2v']['accent_bg'], border=palettes['v2v']['border'], title_color='#065F46')

    # LAYER 3: MULTI-AGENT DECISION & PLANNING LAYER
    y_l3 = 45.5
    h_l3 = 16.5
    draw_layer(8, y_l3, 134, h_l3,
               "3. MULTI-AGENT DECISION & TRAJECTORY PLANNING LAYER",
               "Intent Forecasting, Diffusion Sampling & Centralized Training / Decentralized Execution (CTDE)",
               "Ritu & Neha", palettes['plan'])
    draw_box(11, y_l3 + 1.5, 30, 9.5, "Spatial-Temporal Transformer",
             ["Human Trajectory Forecasting", "Attention on Naturalistic Flow"],
             fill=palettes['plan']['accent_bg'], border=palettes['plan']['border'], title_color='#5B21B6')
    draw_box(44, y_l3 + 1.5, 30, 9.5, "Trajectory Diffusion Model",
             ["Denoising Candidate Path Generation", "Kinematically Feasible Waypoints"],
             fill=palettes['plan']['sub_bg'], border=palettes['plan']['border'])
    draw_box(77, y_l3 + 1.5, 30, 9.5, "Cooperative Braking FSM",
             ["Early V2V Hazard Deceleration", "Anti-Deadlock Cooldown Guard"],
             fill=palettes['plan']['accent_bg'], border=palettes['plan']['border'], title_color='#5B21B6')
    draw_box(110, y_l3 + 1.5, 29, 9.5, "IDM / CTDE MASAC Policy",
             ["Headway Spacing & Acceleration", "Decentralized Execution on CAVs"],
             fill=palettes['plan']['sub_bg'], border=palettes['plan']['border'])

    # LAYER 4: TELEMETRY & USER INTERFACE LAYER
    y_l4 = 65.0
    h_l4 = 16.5
    draw_layer(8, y_l4, 134, h_l4,
               "4. TELEMETRY, HUD & VISUALIZATION INTERFACE",
               "Interactive 3D Panda3D Viewport, Real-Time HUD Overlay & Metric Logging",
               "Sanjana & Mark", palettes['ui'])
    draw_box(11, y_l4 + 1.5, 30, 9.5, "3D Chase Camera Rig",
             ["Left/Right Arrow Vehicle Cycling", "Smooth Chase & Overhead Orbit"],
             fill=palettes['ui']['sub_bg'], border=palettes['ui']['border'])
    draw_box(44, y_l4 + 1.5, 30, 9.5, "Live Telemetry Sidebar HUD",
             ["20 Hz Real-Time Diagnostics", "6-Sector LiDAR Proximity Bars"],
             fill=palettes['ui']['accent_bg'], border=palettes['ui']['border'], title_color='#92400E')
    draw_box(77, y_l4 + 1.5, 30, 9.5, "2D Top-Down Minimap (PiP)",
             ["Bird's Eye Track Texture", "Global Multi-Agent Coordinates"],
             fill=palettes['ui']['sub_bg'], border=palettes['ui']['border'])
    draw_box(110, y_l4 + 1.5, 29, 9.5, "Streaming CSV Logger",
             ["High-Frequency Metrics to Disk", "Jerk, Headway & TTC Analysis"],
             fill=palettes['ui']['accent_bg'], border=palettes['ui']['border'], title_color='#92400E')

    # =========================================================================
    # CLEAN, NON-OVERLAPPING FLOW ARROWS
    # =========================================================================

    def draw_arrow(x1, y1, x2, y2, label="", color='#475569', lw=1.8, style='-|>', offset_y=0):
        con = patches.ConnectionPatch(xyA=(x1, y1), xyB=(x2, y2), coordsA="data", coordsB="data",
                                      arrowstyle=style, color=color, linewidth=lw, mutation_scale=14, zorder=8)
        ax.add_artist(con)
        if label:
            mx, my = (x1 + x2)/2, (y1 + y2)/2 + offset_y
            ax.text(mx, my, label, ha='center', va='center', fontsize=7.8, weight='bold',
                    color='#0F172A', backgroundcolor='#FFFFFF', zorder=9,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='#FFFFFF', edgecolor='#CBD5E1', lw=0.9))

    # 1. State Extraction: L1 -> L2 (Left side)
    draw_arrow(26, y_l1 + h_l1, 26, y_l2, "11D Kinematic Tensors & LiDAR", color='#2563EB')

    # 2. Perception & V2V to Planning: L2 -> L3 (Left side)
    draw_arrow(26, y_l2 + h_l2, 26, y_l3, "Filtered V2V Packets & BLOS Map", color='#059669')

    # 3. Telemetry Stream: L2/L3 to L4 (Middle)
    draw_arrow(59, y_l3 + h_l3, 59, y_l4, "20 Hz Telemetry Stream", color='#D97706')

    # 4. Closed-Loop Actuation Feedback: L3 down to L1 (Right side bypass loop)
    # Using an elegant outer curved arc on the right margin so it never overlaps any box!
    con_loop = patches.ConnectionPatch(xyA=(142, y_l3 + 5), xyB=(142, y_l1 + 8),
                                       coordsA="data", coordsB="data",
                                       arrowstyle='-|>', color='#DC2626', linewidth=2.2,
                                       connectionstyle="arc3,rad=-0.4", mutation_scale=16, zorder=8)
    ax.add_artist(con_loop)

    # Actuation Loop Badge
    ax.text(152, (y_l3 + y_l1)/2 + 4, "Actuation Feedback\n[Throttle, Steering, Brake]",
            ha='center', va='center', fontsize=7.8, weight='bold', color='#DC2626',
            bbox=dict(boxstyle="round,pad=0.3", facecolor='#FFF1F2', edgecolor='#DC2626', lw=1.2), zorder=9)

    # Summary footer bar
    footer_box = patches.FancyBboxPatch((8, 1.2), 134, 3.2, boxstyle="round,pad=0.1,rounding_size=0.6",
                                        facecolor='#FFFFFF', edgecolor='#E2E8F0', linewidth=1.0, zorder=2)
    ax.add_patch(footer_box)
    ax.text(75, 2.8, "Closed-Loop Data Flow: Environment Sensing (50 Hz)  ⟶  V2V Mesh Broadcast (80m)  ⟶  Planning & FSM  ⟶  Decentralized Vehicle Actuation",
            ha='center', va='center', fontsize=8.2, weight='bold', color='#475569', fontfamily='sans-serif')

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Clean, professional diagram generated at {output_path}")

if __name__ == "__main__":
    generate_clean_architecture("/home/mark-joseph/Desktop/main project/overall_system_architecture.png")
