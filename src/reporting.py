from dotenv import load_dotenv
import subprocess
from utils.utils import *

class Reporting:
    def get_server_info(self):
        try:
            # Run 'uname -a' command
            uname_output = subprocess.check_output(['uname', '-a']).decode('utf-8').strip()
            return uname_output
        except Exception as e:
            # Handle any exceptions that may occur
            return f"Error getting server info: {str(e)}"

    def all_env_vars(self):
        if self.sim_start_time is None:
            self.sim_start_time = datetime.now()

        if self.simulation_runtime is None:
            self.simulation_runtime = datetime.now() - self.sim_start_time

        total_reflections = 0
        total_metas = 0
        for a in self.agents:
            for m in a.memory:
                if m.kind == "reflect":
                    total_reflections += 1
                if m.kind == "meta":
                    total_metas += 1

        total_seconds = self.simulation_runtime.total_seconds()

        # Calculate minutes and seconds
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)

        # Create a human-readable string
        runtime_string = f"{minutes} minute(s) and {seconds} second(s)"

        return {
            "id": self.id,
            "map": self.environment_file,
            "agents": self.scenario_file,
            "date": self.sim_start_time.isoformat(),
            "width": self.environment.width,
            "height": self.environment.width,
            "status": self.status,
            "runtime": runtime_string, # Include the string representation
            "server_info": self.get_server_info(),
            "created_at": self.sim_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": self.model,
            "total_steps": self.steps,
            "meta_flag": self.allow_meta_flag,
            "reflect_flag": self.allow_reflect_flag,
            "conversation_counter": self.conversation_counter,
            "total_meta_memories": total_metas,
            "total_reflect_memories": total_reflections,
            "total_agents": sum(1 for agent in self.agents if agent.kind != 'zombie'),
            "total_zombies": sum(1 for agent in self.agents if agent.kind == 'zombie'),
            "total_dead": sum(1 for agent in self.agents if agent.status == 'dead'),
            "total_alive": sum(1 for agent in self.agents if agent.status != 'dead'),
            "llm_call_counter": llm.call_counter,
            "avg_llm_calls_per_step": llm.call_counter / self.steps,
            "avg_runtime_per_step": total_seconds / self.steps,
        }
    def run_interviews(self):
        if self.interview_questions:
            dead_agents = [agent for agent in self.agents if (agent.status == "dead" and agent.kind != "zombie")]
            living_agents = [agent for agent in self.agents if (agent.status != "dead" and agent.kind != "zombie")]

            for agent in dead_agents + living_agents:
                results = []
                for question in self.interview_questions:
                    metric = question.get("metric", None)
                    #if agent.status == "dead":
                    #    pd(f"{agent} dead, can't ask questions")
                    #    results.append("Agent is dead, cannot answer questions")
                    #elif question["who"] == "all" or question["who"] == agent.name:
                    answer = agent.answer(question["question"])
                    if metric:
                        match = re.search(r"Answer: (\d)", answer)
                        if match:
                            score = int(match.group(0))
                        else:
                            score = 0
                        self.performance_metrics[metric] += score
                    answer_data = {
                        "question": question["question"],
                        "answer": answer
                    }
                    results.append(answer_data)
                self.interview_results[agent.name] = results

    def print_agent_memories(self):
        for agent in self.agents:
            print(f"\nMemories for {agent}:")
            for memory in agent.memory:
                print(memory)

    def print_matrix(self):
        cell_width = 15  # Adjust this value based on your needs
        matrix = [[" " * cell_width for _ in range(self.environment.width)] for _ in range(self.environment.height)]

        # Print agents
        for agent in self.agents:
            matrix[agent.x][agent.y] = "{:<{width}}".format(f"{agent.direction} * {agent.name}", width=cell_width)

        #sys.stdout.write("\033[H")
        print("\n\n")
        for row in matrix:
            print("|".join(row))
            print("-" * (cell_width * self.n - 1))
