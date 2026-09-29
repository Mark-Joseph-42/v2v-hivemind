#!/usr/bin/env bash
# ==============================================================================
# Rajagiri School of Engineering & Technology (RSET)
# Final Year B.Tech Project - 30% Milestone Demo Launcher
# Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs
# Team: Mark Joseph | Sanjana | Neha | Ritu
# ==============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "[Error] Virtual environment .venv not found!"
    echo "Please run: uv venv .venv --python 3.11 && uv pip install -r cav_demo/requirements.txt"
    exit 1
fi

PYTHON_EXEC=".venv/bin/python"

# Export project root to PYTHONPATH
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Prefer NVIDIA RTX 5060 Max-Q GPU over integrated Radeon 780M if available
if command -v nvidia-smi &> /dev/null; then
    export __NV_PRIME_RENDER_OFFLOAD=1
    export __GLX_VENDOR_LIBRARY_NAME=nvidia
    export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json
fi

# If arguments were passed directly, forward them to main.py
if [ $# -gt 0 ]; then
    exec "$PYTHON_EXEC" cav_demo/main.py "$@"
fi

# Otherwise, present an interactive presentation menu
clear
echo "=================================================================="
echo "    RAJAGIRI SCHOOL OF ENGINEERING & TECHNOLOGY (RSET)"
echo "      FINAL YEAR B.TECH PROJECT - 30% MILESTONE DEMO"
echo "  Collaborative Trajectory Planning & Multi-Agent Orchestration"
echo "=================================================================="
echo ""
echo "Select Demonstration Mode for the Evaluation Panel:"
echo ""
echo "  [1] REAL VIEW       - 3D Chase Camera (Realistic Highway Driving & Telemetry)"
echo "  [2] PERCEPTION VIEW - Top-Down BEV (360° LiDAR Rays + V2V Green Occlusion Rings)"
echo "  [3] HUMAN MODE      - Interactive W/A/S/D Driving + Fleet Cooperative Defense"
echo "  [4] SCENARIO        - Multi-Lane Roundabout Coordination"
echo "  [5] SCENARIO        - 4-Way Cross Intersection Navigation"
echo "  [6] ABLATION        - Fleet Mode WITHOUT V2V Cooperative Defense"
echo "  [7] HEADLESS        - Automated Verification Test (100 steps)"
echo "  [8] TESTS           - Run Pytest Unit Test Suite"
echo "  [q] Quit"
echo ""
echo "Keybindings inside 3D Window:"
echo "  * [◄ / ►]  Cycle Camera Across Active CAVs"
echo "  * [Space]  Pause / Resume Simulation"
echo "  * [P / V]  Toggle between 3D Real View and Overhead BEV Perception"
echo "  * [W/A/S/D] Drive CAV_01 directly (in Human Mode)"
echo ""
read -p "Enter choice [1-8 or q]: " choice

case "$choice" in
    1)
        echo "Launching Real View Mode (3D Chase Camera, Highway Corridor)..."
        exec "$PYTHON_EXEC" cav_demo/main.py --mode fleet --view chase --scenario corridor --agents 4 --map 5
        ;;
    2)
        echo "Launching Perception View Mode (Overhead BEV + 360 LiDAR + V2V Green Rings)..."
        exec "$PYTHON_EXEC" cav_demo/main.py --mode perception --view bev --scenario corridor --agents 4 --map 5
        ;;
    3)
        echo "Launching Human-in-the-Loop Interactive Mode..."
        exec "$PYTHON_EXEC" cav_demo/main.py --mode human --scenario corridor --agents 4 --map 5
        ;;
    4)
        echo "Launching Multi-Lane Roundabout Coordination Scenario..."
        exec "$PYTHON_EXEC" cav_demo/main.py --mode fleet --scenario roundabout --agents 4
        ;;
    5)
        echo "Launching 4-Way Cross Intersection Scenario..."
        exec "$PYTHON_EXEC" cav_demo/main.py --mode fleet --scenario intersection --agents 4
        ;;
    6)
        echo "Launching Fleet Mode WITHOUT V2V cooperative defense..."
        exec "$PYTHON_EXEC" cav_demo/main.py --mode fleet --scenario corridor --agents 4 --map 5 --disable-coop
        ;;
    7)
        echo "Running Headless Verification Test (100 steps)..."
        exec "$PYTHON_EXEC" cav_demo/main.py --mode fleet --agents 4 --headless --max-steps 100
        ;;
    8)
        echo "Running Unit Tests..."
        exec "$PYTHON_EXEC" -m pytest tests/ -v
        ;;
    q|Q)
        echo "Exiting."
        exit 0
        ;;
    *)
        echo "Invalid selection. Launching Real View Mode..."
        exec "$PYTHON_EXEC" cav_demo/main.py --mode fleet --agents 4
        ;;
esac
