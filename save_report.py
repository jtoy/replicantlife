"""
This module saves simulation reports which includes
logs for agent goals, conversations, reflections, etc.
"""

import re
import traceback
from utils.utils import *


def save_report(matrix_instance, filename=None):
    """
    This function saves all types of logs of the simulation.
    """

    if filename is None:
        filename = f"report-{matrix_instance.id}.txt"
    try:
        total_reflections = 0
        total_metas = 0
        for a in matrix_instance.agents:
            for m in a.memory:
                if m.kind == "reflect":
                    total_reflections += 1
                if m.kind == "meta":
                    total_metas += 1

        with open(f"logs/report-{filename}", "w", encoding="utf-8") as file:
            for k, v in matrix_instance.all_env_vars().items():
                file.write(f"{k}: {v}\n")
            if llm.call_times:
                file.write(
                    f"Average_time_per_call: {sum(llm.call_times) / len(llm.call_times)} seconds\n"
                )
            else:
                file.write("No LLM calls recorded.\n")

            file.write("Scenario: \n")
            file.write(f"{matrix_instance.background}\n")

            file.write("Goals Log:\n")
            for agent in matrix_instance.agents:
                file.write(f"{agent.name}'s goal: {agent.goal}\n")

            file.write("\nInterview Question Results:\n")
            for agent_name, results in matrix_instance.interview_results.items():
                for i in results:
                    file.write(f"Question: {i['question']}\n")
                    file.write(f"{i['answer']}\n")

            for agent in matrix_instance.agents:
                current_location = (
                    matrix_instance.environment.get_location_from_coordinates(
                        agent.x, agent.y
                    )
                )
                current_area = matrix_instance.environment.get_area_from_coordinates(
                    agent.x, agent.y
                )

                file.write(
                    f"{agent.name} is currently at "
                    f"{'' if current_area is None else current_area.name} "
                    f"{current_location.name}\n"
                )

            file.write("==========================================\n")
            for agent in matrix_instance.agents:
                file.write(f"{agent.name}'s goal: {agent.goal}\n")

            file.write("\n\nConversations Log:\n")
            for agent in matrix_instance.agents:
                file.write("==========================================")
                file.write(f"Conversation logs for {agent}\n")
                for conversation in agent.conversations:
                    conversation_strings = "\n".join(conversation.messages)
                    file.write("Start +++++++++++++++++++++++++++++++++++++++\n")
                    file.write(f"{conversation_strings}\n")
                file.write("End +++++++++++++++++++++++++++++++++++++++\n")

            file.write("\n\nReflection Log:\n")
            for agent in matrix_instance.agents:
                file.write("==========================================")
                file.write(f"Reflection logs for {agent}\n")
                memory_strings = "Start +++++++++++++++++++++++++++++++++++++++\n"
                for memory in agent.memory:
                    if memory.kind in ["reflect", "meta"]:
                        memory_strings += f"** {memory.content}\n"
                file.write(memory_strings)
                file.write("End +++++++++++++++++++++++++++++++++++++++\n")

            file.write("\n\nMeta Cognition Log:\n")
            for agent in matrix_instance.agents:
                file.write("==========================================")
                file.write(f"Meta logs for {agent}\n")
                memory_strings = "Start +++++++++++++++++++++++++++++++++++++++\n"
                for memory in agent.memory:
                    if memory.kind == "meta":
                        memory_strings += f"** {memory.content}\n"
                file.write(memory_strings)
                file.write("End +++++++++++++++++++++++++++++++++++++++\n")

        with open(f"logs/eval-{filename}", "w", encoding="utf-8") as file:
            file.write("\n\nAUTO EVALUATIONS\n")
            for agent in matrix_instance.agents:
                if agent.kind == "human":
                    file.write(
                        f"==========================================Scores for {agent}\n"
                    )

                    conversation_part = f"++++ {agent.name}'s Conversations ++++\n"
                    for conversation in agent.conversations:
                        conversation_part += "==== start ====\n"
                        conversation_part += "\n- ".join(conversation.messages)

                    reflect_part = f"++++ {agent.name}'s Reflections ++++\n"
                    for memory in agent.memory:
                        if memory.kind in ["reflect", "meta"]:
                            reflect_part += f"{memory.content}\n"

                    interview_part = []
                    for item in matrix_instance.interview_results[agent.name]:
                        interview_part.append(
                            {"Question": item["question"], "Answer": item["answer"]}
                        )

                    variables = {
                        "background": matrix_instance.background,
                        "agent": agent.name,
                        "conversation_part": conversation_part,
                        "reflect_part": reflect_part,
                        "interview_part": interview_part,
                    }
                    generated_correctly = False
                    while not generated_correctly:
                        try:
                            agent_eval = llm.prompt("eval", variables)
                            scores_part = re.compile(
                                r"(Progressive Understanding|Adaptive Communication|"
                                r"Reflective Depth|Knowledge Application|"
                                r"Cognitive Flexibility): (\d+)"
                            ).findall(agent_eval)

                            progressive_understanding_score = int(scores_part[0][1])
                            adaptive_communication_score = int(scores_part[1][1])
                            reflective_depth_score = int(scores_part[2][1])
                            knowledge_application_score = int(scores_part[3][1])
                            cognitive_flexibility_score = int(scores_part[4][1])

                            generated_correctly = True
                            file.write(agent_eval)
                            file.write("\n")

                        except Exception as e: # pylint: disable=broad-except
                            print(
                                f"Wrong evaluation format response error: {e}, retrying..."
                            )
                        # Performance Calculation
            numerator = matrix_instance.performance_evals["numerator"]
            denominator = matrix_instance.performance_evals["denominator"]
            all_env_vars = matrix_instance.all_env_vars()

            if numerator not in all_env_vars:
                numerator_value = matrix_instance.performance_metrics[numerator]
            else:
                numerator_value = all_env_vars[numerator]

            if denominator not in all_env_vars:
                denominator_value = matrix_instance.performance_metrics[denominator]
            else:
                denominator_value = all_env_vars[denominator]

            if denominator_value < 0:
                performance_score = 0
            else:
                performance_score = (numerator_value / denominator_value) * 10

            file.write(f"\n\n++++ Performance Score: {performance_score}")

    except Exception as e: # pylint: disable=broad-except
        print(f"Error: {e}")

        traceback.print_exc()
