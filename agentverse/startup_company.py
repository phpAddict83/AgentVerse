import copy
import asyncio
import logging
from typing import List

# from agentverse.agents import Agent
from agentverse.agents.simulation_agent.conversation import BaseAgent
from agentverse.environments import HierarchicalEnvironment
from agentverse.initialization import (
    load_agent,
    load_environment,
    prepare_structure_config,
)
from agentverse.environments.tasksolving_env.basic import BasicEnvironment
from agentverse.utils import AGENT_TYPES
import os

openai_logger = logging.getLogger("openai")
openai_logger.setLevel(logging.WARNING)


class StartupCompany:
    def __init__(self, agents: List[BaseAgent], environment: HierarchicalEnvironment):
        self.agents = agents
        self.environment = environment

    @classmethod
    def from_task(cls, task: str, tasks_dir: str):
        """Build an AgentVerse from a task name.
        The task name should correspond to a directory in `tasks` directory.
        Then this method will load the configuration from the yaml file in that directory.
        """
        # Prepare the config of the task
        task_config = prepare_structure_config(task, tasks_dir)

        # Build the environment
        env_config = task_config["environment"]

        # Build agents for all pipeline (task)
        # agents = {}
        # for i, agent_config in enumerate(task_config["agents"]):
        #     if agent_config.get("agent_type", "") == "critic":
        #         agent = load_agent(agent_config)
        #         agents[AGENT_TYPES.CRITIC] = [
        #             copy.deepcopy(agent)
        #             for _ in range(task_config.get("cnt_agents", 1) - 1)
        #         ]
        #     else:
        #         agent_type = AGENT_TYPES.from_string(agent_config.get("agent_type", ""))
        #         agents[agent_type] = load_agent(agent_config)

        # env_config["agents"] = agents

        env_config["task_description"] = task_config.get("task_description", "")
        env_config["max_rounds"] = task_config.get("max_rounds", 3)

        environment = HierarchicalEnvironment(
            complex_task=task_config.get("task_description", ""),
            structure_path=os.path.join(tasks_dir, task, "structure.json"),
        )

        return cls(environment=environment, task=task)

    def run(self):
        """Run the environment from scratch until it is done."""
        self.environment.reset()
        while not self.environment.is_done():
            asyncio.run(self.environment.step())
        self.environment.report_metrics()

    def reset(self):
        self.environment.reset()
        for agent in self.agents:
            agent.reset()

    def next(self, *args, **kwargs):
        """Run the environment for one step and return the return message."""
        return_message = asyncio.run(self.environment.step(*args, **kwargs))
        return return_message

    def update_state(self, *args, **kwargs):
        """Run the environment for one step and return the return message."""
        self.environment.update_state(*args, **kwargs)


def run_company(task, tasks_dir):
    company = StartupCompany.from_task(task, tasks_dir)
    company.run()
    return


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="company")
    parser.add_argument(
        "--tasks_dir",
        type=str,
        default="agentverse\tasks\startup\data_analysis\config.yaml",
    )
    args = parser.parse_args()
    run_company(args.task, args.tasks_dir)