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
echo "  [1] FLEET MODE (Autonomous Fleet + Arrow-Key 3D Camera Switching)"
echo "  [2] HUMAN MODE (Drive Agent_0 with W/A/S/D + Live Fleet Defense)"
echo "  [3] ABLATION DEMO (Fleet Mode WITHOUT V2V Cooperative Braking)"
echo "  [4] HEADLESS VERIFICATION TEST (Automated 100-step smoke test)"
echo "  [5] RUN UNIT TESTS (Pytest for V2V networking & packet integrity)"
echo "  [q] Quit"
echo ""
read -p "Enter choice [1-5 or q]: " choice

case "$choice" in
    1)
        echo "Launching Fleet Observation Mode..."
        exec "$PYTHON_EXEC" cav_demo/main.py --mode fleet --agents 4 --map 5
        ;;
    2)
        echo "Launching Human-in-the-Loop Interactive Mode..."
        exec "$PYTHON_EXEC" cav_demo/main.py --mode human --agents 4 --map 5
        ;;
    3)
        echo "Launching Fleet Mode WITHOUT V2V cooperative defense..."
        exec "$PYTHON_EXEC" cav_demo/main.py --mode fleet --agents 4 --map 5 --disable-coop
        ;;
    4)
        echo "Running Headless Verification Test (100 steps)..."
        exec "$PYTHON_EXEC" cav_demo/main.py --mode fleet --agents 4 --headless --max-steps 100
        ;;
    5)
        echo "Running Unit Tests..."
        exec "$PYTHON_EXEC" -m pytest tests/ -v
        ;;
    q|Q)
        echo "Exiting."
        exit 0
        ;;
    *)
        echo "Invalid selection. Launching default Fleet Mode..."
        exec "$PYTHON_EXEC" cav_demo/main.py --mode fleet --agents 4
        ;;
esac
