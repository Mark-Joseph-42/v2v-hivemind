"""
Generate an Ultra-Clean, Simple, and Intuitive Design Diagrams Image
for Slide 7/8 of the B.Tech Presentation at RSET.
Features:
1. UML Class Architecture (Left Panel) - zero overlap, perfect spacing
2. Cooperative Braking FSM (Top Right Panel)
3. Step Execution Sequence (Bottom Right Panel)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_design_diagrams(output_path="design_diagrams.png"):
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    ax.set_xlim(0, 160)
    ax.set_ylim(0, 92)
    ax.axis('off')

    # Background
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    # Header / Title
    ax.text(80, 88.5, "SYSTEM DESIGN & BEHAVIORAL DIAGRAMS",
            ha='center', va='center', fontsize=17, weight='bold', color='#0F172A', fontfamily='sans-serif')
    ax.text(80, 85.5, "UML Class Relationships  •  Cooperative Braking FSM  •  Runtime Execution Sequence",
            ha='center', va='center', fontsize=10.5, color='#64748B', fontfamily='sans-serif')

    # Color Palette
    c_blue = {'border': '#2563EB', 'bg': '#EFF6FF', 'badge': '#1D4ED8', 'title': '#1E40AF'}
    c_green = {'border': '#059669', 'bg': '#ECFDF5', 'badge': '#047857', 'title': '#065F46'}
    c_purple = {'border': '#7C3AED', 'bg': '#FAF5FF', 'badge': '#6D28D9', 'title': '#5B21B6'}

    # Helper: Outer Section Card
    def draw_section_card(x, y, w, h, title, pal):
        shadow = patches.FancyBboxPatch((x+0.3, y-0.3), w, h, boxstyle="round,pad=0.2,rounding_size=1.2",
                                        facecolor='#E2E8F0', edgecolor='none', zorder=1)
        ax.add_patch(shadow)
        card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=1.2",
                                      facecolor=pal['bg'], edgecolor=pal['border'], linewidth=1.6, zorder=2)
        ax.add_patch(card)
        badge = patches.FancyBboxPatch((x + 2, y + h - 3.8), w - 4, 3.0, boxstyle="round,pad=0.1,rounding_size=0.6",
                                       facecolor=pal['badge'], edgecolor='none', zorder=3)
        ax.add_patch(badge)
        ax.text(x + w/2, y + h - 2.3, title, ha='center', va='center', fontsize=9.5,
                weight='bold', color='#FFFFFF', zorder=4, fontfamily='sans-serif')

    # =========================================================================
    # LEFT PANEL: SIMPLIFIED UML CLASS DIAGRAM (x: 6 to 79, y: 6 to 82)
    # =========================================================================
    draw_section_card(6, 6, 73, 76, "1. CORE UML CLASS ARCHITECTURE", c_blue)

    def draw_class_box(x, y, w, h, class_name, fields, methods, border='#2563EB', fill='#FFFFFF'):
        b = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=0.7",
                                   facecolor=fill, edgecolor=border, linewidth=1.4, zorder=5)
        ax.add_patch(b)
        header = patches.FancyBboxPatch((x, y + h - 2.8), w, 2.8, boxstyle="round,pad=0.0,rounding_size=0.5",
                                        facecolor='#DBEAFE', edgecolor=border, linewidth=1.0, zorder=6)
        ax.add_patch(header)
        ax.text(x + w/2, y + h - 1.4, f"<<class>> {class_name}", ha='center', va='center',
                fontsize=8.5, weight='bold', color='#1E40AF', zorder=7, fontfamily='sans-serif')

        # Dividing line between fields and methods
        sep_y = y + h - 2.8 - (len(fields) * 1.5 + 0.6)
        ax.plot([x, x+w], [sep_y, sep_y], color='#CBD5E1', lw=0.9, zorder=7)

        # Fields
        curr_y = y + h - 4.2
        for f in fields:
            ax.text(x + 1.2, curr_y, f, ha='left', va='center', fontsize=7.1,
                    color='#334155', fontfamily='monospace', zorder=7)
            curr_y -= 1.5

        # Methods
        curr_y = sep_y - 1.4
        for m in methods:
            ax.text(x + 1.2, curr_y, m, ha='left', va='center', fontsize=7.1,
                    color='#0F172A', fontfamily='monospace', weight='bold', zorder=7)
            curr_y -= 1.5

    # Class 1: V2VNetworkMesh (Top Left) - x: 8 to 39
    draw_class_box(8.5, 45, 31, 26, "V2VNetworkMesh",
                   ["- comm_radius: 80.0m",
                    "- channel_jitter: 12ms",
                    "- packet_drop: 2%",
                    "- packet_buffer: dict"],
                   ["+ extract_kinematics()",
                    "+ broadcast_step()",
                    "+ get_brake_warnings()",
                    "+ get_metrics()"])

    # Class 2: CollaborativePerceptionEngine (Top Right) - x: 46.5 to 77.5
    draw_class_box(46.5, 45, 31, 26, "CollabPerceptionEngine",
                   ["- sensing_radius: 80m",
                    "- ray_count: 72 rays",
                    "- occluded_list: list",
                    "- unmasked_count: int"],
                   ["+ update(env, mesh)",
                    "+ is_line_blocked()",
                    "+ unmask_obstacles()",
                    "+ render_beacons()"])

    # Class 3: V2VPacket (Bottom Left) - x: 8.5 to 39.5
    draw_class_box(8.5, 10, 31, 23, "V2VPacket",
                   ["+ sender_id: str",
                    "+ position: (x, y)",
                    "+ speed_kmh: float",
                    "+ is_braking: bool",
                    "+ state_vector: 11D",
                    "+ latency_ms: float"],
                   ["+ is_valid(): bool",
                    "+ to_dict(): dict"])

    # Class 4: IDMFleetController (Bottom Right) - x: 46.5 to 77.5
    draw_class_box(46.5, 10, 31, 23, "IDMFleetController",
                   ["- enable_coop_brake: bool",
                    "- coop_step_count: dict",
                    "- coop_cooldown: dict",
                    "- alert_threshold: 25m"],
                   ["+ get_actions(fleet, mesh)",
                    "+ is_coop_braking(): bool",
                    "+ apply_fsm_decel()",
                    "+ reset()"])

    # Relationships:
    # 1. Composition: Mesh manages Packets (Vertical Drop)
    con1 = patches.ConnectionPatch(xyA=(24, 45), xyB=(24, 33), coordsA="data", coordsB="data",
                                   arrowstyle='-|>', color='#2563EB', linewidth=1.6, zorder=8)
    ax.add_artist(con1)
    ax.text(25, 39, "1  manages  *", ha='left', va='center', fontsize=7.5,
            weight='bold', color='#1E40AF', backgroundcolor='#FFFFFF', zorder=9,
            bbox=dict(boxstyle="round,pad=0.15", facecolor='#FFFFFF', edgecolor='#CBD5E1', lw=0.8))

    # 2. Dependency: CollabEngine queries Mesh (Horizontal with clean offset text)
    con2 = patches.ConnectionPatch(xyA=(39.5, 58), xyB=(46.5, 58), coordsA="data", coordsB="data",
                                   arrowstyle='-|>', color='#2563EB', linewidth=1.5, linestyle='dashed', zorder=8)
    ax.add_artist(con2)
    ax.text(43.0, 61.2, "queries\npackets", ha='center', va='center', fontsize=6.8, color='#1E40AF',
            weight='bold', backgroundcolor='#FFFFFF', zorder=9,
            bbox=dict(boxstyle="round,pad=0.15", facecolor='#FFFFFF', edgecolor='#CBD5E1', lw=0.8))

    # 3. Dependency: FleetController queries Mesh for brake alerts
    con3 = patches.ConnectionPatch(xyA=(39.5, 48), xyB=(46.5, 30), coordsA="data", coordsB="data",
                                   arrowstyle='-|>', color='#2563EB', linewidth=1.5, linestyle='dashed', zorder=8)
    ax.add_artist(con3)
    ax.text(42.5, 38.5, "queries\nbrake alerts", ha='center', va='center', fontsize=6.8, color='#1E40AF',
            weight='bold', backgroundcolor='#FFFFFF', zorder=9,
            bbox=dict(boxstyle="round,pad=0.15", facecolor='#FFFFFF', edgecolor='#CBD5E1', lw=0.8))


    # =========================================================================
    # TOP-RIGHT PANEL: COOPERATIVE BRAKING FSM (x: 81 to 154, y: 47 to 82)
    # =========================================================================
    draw_section_card(81, 47, 73, 35, "2. COOPERATIVE BRAKING FSM (STATE MACHINE)", c_green)

    def draw_fsm_state(x, y, w, h, state_name, desc, pal_color, is_start=False):
        s = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=1.2",
                                   facecolor=pal_color['bg'], edgecolor=pal_color['border'], linewidth=1.6, zorder=6)
        ax.add_patch(s)
        ax.text(x + w/2, y + h - 1.8, state_name, ha='center', va='center', fontsize=8.5,
                weight='bold', color=pal_color['title'], zorder=7, fontfamily='sans-serif')
        ax.text(x + w/2, y + h - 3.8, desc, ha='center', va='center', fontsize=7.2,
                color='#334155', zorder=7, fontfamily='sans-serif')
        if is_start:
            ax.plot([x - 3.5, x], [y + h/2, y + h/2], color='#047857', lw=1.8, zorder=8)
            ax.plot(x - 3.5, y + h/2, marker='o', color='#047857', markersize=4, zorder=8)

    # 3 FSM States
    s_normal = {'bg': '#FFFFFF', 'border': '#059669', 'title': '#065F46'}
    s_brake  = {'bg': '#FEE2E2', 'border': '#DC2626', 'title': '#991B1B'}
    s_cool   = {'bg': '#FEF3C7', 'border': '#D97706', 'title': '#92400E'}

    draw_fsm_state(84, 63.5, 28, 6.8, "NORMAL_FOLLOWING", "Standard IDM Headway", s_normal, is_start=True)
    draw_fsm_state(123, 63.5, 28, 6.8, "COOPERATIVE_BRAKING", "V2V Proportional Decel", s_brake)
    draw_fsm_state(103.5, 49.5, 29, 6.8, "COOLDOWN_HYSTERESIS", "Anti-Deadlock (12 Steps)", s_cool)

    # FSM Transitions
    # Normal -> Braking (Top arrow)
    con_fsm1 = patches.ConnectionPatch(xyA=(112, 68.0), xyB=(123, 68.0), coordsA="data", coordsB="data",
                                       arrowstyle='-|>', color='#DC2626', linewidth=1.6, zorder=8)
    ax.add_artist(con_fsm1)
    ax.text(117.5, 71.2, "Hazard Alert Ahead\n(Dist < 25m)", ha='center', va='center',
            fontsize=6.8, weight='bold', color='#DC2626', zorder=9,
            bbox=dict(boxstyle="round,pad=0.15", facecolor='#FFFFFF', edgecolor='#FCA5A5', lw=0.8))

    # Braking -> Cooldown (Down arrow)
    con_fsm2 = patches.ConnectionPatch(xyA=(137, 63.5), xyB=(126, 56.3), coordsA="data", coordsB="data",
                                       arrowstyle='-|>', color='#D97706', linewidth=1.6, zorder=8)
    ax.add_artist(con_fsm2)
    ax.text(138.5, 59.5, "Step Count >= 15\nor Hazard Cleared", ha='left', va='center',
            fontsize=6.8, color='#B45309', weight='bold', zorder=9,
            bbox=dict(boxstyle="round,pad=0.15", facecolor='#FFFFFF', edgecolor='#FDE68A', lw=0.8))

    # Cooldown -> Normal (Up-left arrow)
    con_fsm3 = patches.ConnectionPatch(xyA=(103.5, 54.0), xyB=(98, 63.5), coordsA="data", coordsB="data",
                                       arrowstyle='-|>', color='#059669', linewidth=1.6, zorder=8)
    ax.add_artist(con_fsm3)
    ax.text(94.5, 57.5, "Cooldown == 0\n(Safe Headway)", ha='right', va='center',
            fontsize=6.8, color='#047857', weight='bold', zorder=9,
            bbox=dict(boxstyle="round,pad=0.15", facecolor='#FFFFFF', edgecolor='#A7F3D0', lw=0.8))


    # =========================================================================
    # BOTTOM-RIGHT PANEL: EXECUTION SEQUENCE FLOW (x: 81 to 154, y: 6 to 43)
    # =========================================================================
    draw_section_card(81, 6, 73, 37, "3. STEP RUNTIME EXECUTION SEQUENCE (50 Hz)", c_purple)

    seq_steps = [
        ("Step 1: Kinematic Extraction", "Extract 11D continuous state tensor from all active vehicles", "#EDE9FE", "#6D28D9"),
        ("Step 2: V2V Mesh Broadcast", "Filter pairwise range (R<=80m) + Inject latency jitter & drop", "#FFFFFF", "#7C3AED"),
        ("Step 3: Multi-Agent Arbitration", "FSM checks emergency alerts; modulates throttle & IDM headway", "#EDE9FE", "#6D28D9"),
        ("Step 4: Actuation & Visualization", "Step Bullet Physics world (0.02s) & update 20 Hz Onscreen HUD", "#FFFFFF", "#7C3AED")
    ]

    curr_sy = 33.5
    for idx, (s_title, s_desc, bg_color, b_color) in enumerate(seq_steps):
        s_box = patches.FancyBboxPatch((84, curr_sy), 67, 5.2, boxstyle="round,pad=0.1,rounding_size=0.6",
                                       facecolor=bg_color, edgecolor=b_color, linewidth=1.2, zorder=5)
        ax.add_patch(s_box)

        # Number badge
        num_circ = patches.Circle((87.5, curr_sy + 2.6), 1.6, facecolor=b_color, edgecolor='none', zorder=6)
        ax.add_patch(num_circ)
        ax.text(87.5, curr_sy + 2.6, str(idx + 1), ha='center', va='center', fontsize=8,
                weight='bold', color='#FFFFFF', zorder=7)

        ax.text(91, curr_sy + 3.6, s_title, ha='left', va='center', fontsize=8,
                weight='bold', color='#0F172A', zorder=6, fontfamily='sans-serif')
        ax.text(91, curr_sy + 1.6, s_desc, ha='left', va='center', fontsize=7.0,
                color='#475569', zorder=6, fontfamily='sans-serif')

        # Arrow down to next step
        if idx < len(seq_steps) - 1:
            con_seq = patches.ConnectionPatch(xyA=(117.5, curr_sy), xyB=(117.5, curr_sy - 2.0),
                                              coordsA="data", coordsB="data",
                                              arrowstyle='-|>', color='#7C3AED', linewidth=1.4, zorder=8)
            ax.add_artist(con_seq)

        curr_sy -= 7.2

    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Perfect Design Diagrams image generated at: {output_path}")

if __name__ == "__main__":
    generate_design_diagrams("/home/mark-joseph/Desktop/main project/design_diagrams.png")
