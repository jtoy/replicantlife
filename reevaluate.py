"""
This module handles the evaluation of simulations.
"""

import os
import json
import re
import argparse
import requests
from configs.configs import *
from utils.utils import *


def call_gpt(prompt):
    """
    This function uses the gpt service for evaluations.
    """

    data = {
        "model": "gpt-3.5-turbo-16k",
        "messages": [{"role": "user", "content": prompt}],
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json",
    }

    timeout = 60

    response = requests.post(
        "https://api.openai.com/v1/chat/completions", json=data, headers=headers, timeout=timeout
    )

    if response.status_code == 200:
        msg = response.json()["choices"][0]["message"]["content"]
    else:
        print(response.json())
        msg = "Error"

    return msg


parser = argparse.ArgumentParser(description="Evaluate with GPT")
parser.add_argument("--report", type=str, help="Report file to evaluate")
args = parser.parse_args()

if os.path.exists(args.report):
    with open(args.report, encoding="utf-8") as file:
        input_string = file.read()

    env_vars = {
        "total_agents": int(re.search(r"total_agents: (\d+)", input_string).group(1)),
        "total_dead": int(re.search(r"total_dead: (\d+)", input_string).group(1)),
        "total_alive": int(re.search(r"total_alive: (\d+)", input_string).group(1)),
    }
    interview_part = (
        re.search(
            r"Interview Question Results:(.*?)(Conversation Log:|\Z)",
            input_string,
            re.DOTALL,
        )
        .group(1)
        .strip()
    )
    scenario_part = (
        re.search(r"Scenario:(.*?)(Goals Log:|\Z)", input_string, re.DOTALL)
        .group(1)
        .strip()
    )
    goals_part = (
        re.search(
            r"Goals Log:(.*?)(Interview Question Results:|\Z)", input_string, re.DOTALL
        )
        .group(1)
        .strip()
    )
    conversation_part = (
        re.search(
            r"Conversations Log:(.*?)(Reflection Log:|\Z)", input_string, re.DOTALL
        )
        .group(1)
        .strip()
    )
    reflection_part = (
        re.search(
            r"Reflection Log:(.*?)(Meta Cognition Log:|\Z)", input_string, re.DOTALL
        )
        .group(1)
        .strip()
    )
    metacognition_part = (
        re.search(r"Meta Cognition Log:(.*?)(\Z)", input_string, re.DOTALL)
        .group(1)
        .strip()
    )

    conversation_matches = re.compile(
        r"={42}Conversation logs for (.+?)\n(.*?)(?=\n={42}|$)", re.DOTALL
    ).findall(conversation_part)
    parsed_data = {}
    for name, logs in conversation_matches:
        if name not in parsed_data:
            parsed_data[name.strip()] = []

        parsed_data[name.strip()] = logs.strip()
    conversation_matches = parsed_data

    reflection_matches = re.compile(
        r"={42}Reflection logs for (.+?)\n(.*?)(?=\n={42}|$)", re.DOTALL
    ).findall(reflection_part)
    parsed_data = {}
    for name, logs in reflection_matches:
        if name not in parsed_data:
            parsed_data[name.strip()] = []

        parsed_data[name.strip()] = logs.strip()
    reflection_matches = parsed_data

    interview_matches = re.compile(
        r"Question: (.+?)\n(.*?)(?:\n\[.*?\])?(?=\nQuestion:|$|\n={10,})", re.DOTALL
    ).findall(interview_part)
    parsed_data = {}
    for question, block in interview_matches:
        answer_match = re.match(r"(\w+):(.+)", block)
        if answer_match:
            name = answer_match.group(1).strip()
            answer = answer_match.group(2).strip()

            if name not in parsed_data:
                parsed_data[name] = []

            parsed_data[name].append({"Question": question.strip(), "Answer": answer})

        else:
            special_case_pattern = re.compile(r"(\w+): (\d)\n(.*)", re.DOTALL)
            special_case_match = special_case_pattern.search(block)
            if special_case_match:
                name = special_case_match.group(1)
                answer = special_case_match.group(2)

                if name not in parsed_data:
                    parsed_data[name] = []

                parsed_data[name].append(
                    {"Question": question.strip(), "Answer": answer}
                )

    interview_matches = parsed_data

    progressive_understanding_scores = []
    adaptive_communication_scores = []
    reflective_depth_scores = []
    knowledge_application_scores = []
    cognitive_flexibility_scores = []
    performance_scores = []

    # Write to re-eval file
    reeval_filename = args.report.replace("report", "reeval")
    with open(reeval_filename, "w", encoding="utf-8") as file:
        file.write("\n\nauto evaluations\n")

    for i in conversation_matches:
        if "Zombie" in i:
            continue

        variables = {
            "background": scenario_part,
            "agent": i,
            "conversation_part": conversation_matches[i],
            "reflect_part": reflection_matches[i],
            "interview_part": interview_matches[i],
        }

        # pylint: disable=invalid-name
        generated_correctly = False
        # pylint: enable=invalid-name

        while not generated_correctly:
            try:
                agent_eval = llm.prompt("eval", variables)

                scores_part = re.compile(
                    r"(Progressive Understanding|Adaptive Communication|Reflective Depth|"
                    r"Knowledge Application|Cognitive Flexibility): (\d+)"
                ).findall(agent_eval)

                progressive_understanding_scores.append(int(scores_part[0][1]))
                adaptive_communication_scores.append(int(scores_part[1][1]))
                reflective_depth_scores.append(int(scores_part[2][1]))
                knowledge_application_scores.append(int(scores_part[3][1]))
                cognitive_flexibility_scores.append(int(scores_part[4][1]))

                # pylint: disable=invalid-name
                generated_correctly = True
                # pylint: enable=invalid-name

                with open(reeval_filename, "a", encoding="utf-8") as file:
                    file.write(
                        f"==========================================Scores for {i}\n"
                    )
                    file.write(agent_eval)
                    file.write("\n")

                if "xmas_" in args.report:
                    CONFIG_FILENAME = "configs/christmas_party_situation.json"
                elif "ss_" in args.report:
                    CONFIG_FILENAME = "configs/secret_santa_situation.json"
                elif "z_" in args.report:
                    CONFIG_FILENAME = "configs/zombie_situation.json"
                elif "m_" in args.report:
                    CONFIG_FILENAME = "configs/murder_situation.json"
                else:
                    CONFIG_FILENAME = "configs/def.json"

                with open(CONFIG_FILENAME, "r", encoding="utf-8") as config_file:
                    configs_json = json.load(config_file)
                    questions = configs_json.get("questions", [])
                    performance = configs_json.get("performance", {})

                    numerator_key = performance.get("numerator", None)
                    denominator_key = performance.get("denominator", None)

                    for q in questions:
                        metric = q.get("metric", None)
                        if metric:
                            # pylint: disable=invalid-name
                            answer = 0
                            # pylint: enable=invalid-name

                            for interview in interview_matches[i]:
                                if q["question"] == interview["Question"]:
                                    answer = llm.generate(
                                        f"Based on the excerpt:\n"
                                        f"{interview['Question']}\n{interview['Answer']}\n\n"
                                        f"Did the character achieve the question? "
                                        f"1 for yes, 0 for no.\n"
                                        f"Format your answer like this:\n\nExplanation: <string>\n"
                                        f"Answer: <0 or 1 only>"
                                    )
                                    answer = (
                                        int(
                                            re.search(r"Answer: (\d+)", answer).group(1)
                                        )
                                        * 10
                                    )

                        else:
                            answer = (
                                env_vars.get(numerator_key, 0)
                                / env_vars.get(denominator_key, 1)
                            ) * 10

                    performance_scores.append(answer)

            except Exception as e: # pylint: disable=broad-except
                print(f"Wrong evaluation format response error: {e}, retrying...")

    adaptive_communication_scores = [i for i in adaptive_communication_scores if i != 0]

    pu = sum(progressive_understanding_scores) / len(progressive_understanding_scores)
    ac = sum(adaptive_communication_scores) / len(adaptive_communication_scores)
    rd = sum(reflective_depth_scores) / len(reflective_depth_scores)
    ka = sum(knowledge_application_scores) / len(knowledge_application_scores)
    cf = sum(cognitive_flexibility_scores) / len(cognitive_flexibility_scores)
    ps = sum(performance_scores) / len(performance_scores)
    with open(reeval_filename, "a", encoding="utf-8") as file:
        file.write(f"\n\n++++ Performance Score: {ps}\n")
    score_data = {
        "file": args.report,
        "progressive_understanding": pu,
        "adaptive_communication": ac,
        "reflective_depth": rd,
        "knowledge_application": ka,
        "cognitive_flexibility": cf,
        "performance": ps,
        "overall": pu + ac + rd + ka + cf + ps,
    }
    print(score_data)
else:
    print("report file {args.report} does not exist")
