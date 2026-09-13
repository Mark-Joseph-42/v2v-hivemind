"""
Human-in-the-Loop Mixed-Autonomy Controller.
Final Year Project - RSET
Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs

Enables interactive human driving for Agent_0 (via W/A/S/D) while autonomous CAVs
react dynamically via IDM + V2V collaborative defense.
"""

from typing import Any, Dict, List, Optional, Tuple
from cav_demo.idm_fleet_policy import IDMFleetController
from cav_demo.v2v_network import V2VNetworkMesh


class HumanInTheLoopManager:
    """
    Coordinates mixed-autonomy execution:
    - Agent_0: Human driver (Keyboard W/A/S/D)
    - Agent_1..N: Autonomous CAV Fleet (IDM + V2V cooperative policy)
    """

    def __init__(self, human_agent_id: str = "agent0"):
        self.human_agent_id = human_agent_id
        self.fleet_controller = IDMFleetController(enable_coop_braking=True)
        self.manual_override_active = True

    def get_fleet_actions(
        self,
        env: Any,
        agents_dict: Dict[str, Any],
        v2v_mesh: V2VNetworkMesh
    ) -> Dict[str, List[float]]:
        """
        Generate actions for all vehicles in mixed-autonomy mode:
        Autonomous vehicles get actions from IDMFleetController;
        Human vehicle action is handled via MetaDrive ManualControlPolicy or keyboard passthrough.
        """
        # Dynamically resolve human agent id from active agents
        target_human_id = self.human_agent_id
        if target_human_id not in agents_dict:
            if "agent0" in agents_dict:
                target_human_id = "agent0"
            elif "agent_0" in agents_dict:
                target_human_id = "agent_0"
            elif agents_dict:
                target_human_id = sorted(list(agents_dict.keys()))[0]
            self.human_agent_id = target_human_id

        # Autonomous fleet actions for all non-human agents
        actions = self.fleet_controller.get_actions(
            agents_dict=agents_dict,
            v2v_mesh=v2v_mesh,
            manual_agents=[target_human_id]
        )

        # In MetaDrive multi-agent, provide neutral action for manual agent so env reads keyboard
        if target_human_id in agents_dict:
            actions[target_human_id] = [0.0, 0.0]

        return actions

    def is_coop_braking(self, agent_id: str) -> bool:
        """Check if autonomous vehicle is currently braking cooperatively."""
        return self.fleet_controller.is_coop_braking(agent_id)

    def reset(self):
        """Reset internal fleet controller upon episode restart."""
        self.fleet_controller.reset()

