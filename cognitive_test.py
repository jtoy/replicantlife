from engine import Matrix
import re
from utils.utils import *
import json
import argparse
import subprocess
import os
import sys
from contextlib import contextmanager
import numpy as np
import matplotlib.pyplot as plt
from save_report import save_report

parser = argparse.ArgumentParser(description='Cognitive Test')
parser.add_argument('--generate', action='store_true', help='Run tests to generate auto eval')
parser.add_argument('--overwrite', action='store_true', help='Overwrite eval files')
parser.add_argument('--reeval', action='store_true', help='Run reevaluate')
parser.add_argument('--graph', action='store_true', help='Read eval files to generate graph')
parser.add_argument('--steps', type=int, default=100, help='Steps for Generating')
args = parser.parse_args()

variations = [
        { "steps": args.steps, "allow_plan": 1, "allow_reflect": 1, "allow_observance": 1, "allow_meta": 1, "llm_action": 1, "llm_importance": 0 }, #Full Architecture With Meta
        { "steps": args.steps, "allow_plan": 1, "allow_reflect": 1, "allow_observance": 1, "allow_meta": 0, "llm_action": 1, "llm_importance": 0 }, #Full Architecture Without Meta
        { "steps": args.steps, "allow_plan": 0, "allow_reflect": 0, "allow_observance": 1, "allow_meta": 1, "llm_action": 1, "llm_importance": 0 }, #Architecture With Meta Only
        { "steps": args.steps, "allow_plan": 0, "allow_reflect": 1, "allow_observance": 1, "allow_meta": 0, "llm_action": 1, "llm_importance": 0 }, #Architecture With Reflect Only
        { "steps": args.steps, "allow_plan": 0, "allow_reflect": 0, "allow_observance": 0, "allow_meta": 0, "llm_action": 1, "llm_importance": 0 } #Reflect and Meta Off
]

scenarios = [
    "configs/christmas_party_situation.json",
    "configs/secret_santa_situation.json",
    "configs/zombie_situation.json",
    "configs/murder_situation.json"
]

ids = [
    "xmas_p1_r1_o1_m1",
    "ss_p1_r1_o1_m1",
    "z_p1_r1_o1_m1",
    "m_p1_r1_o1_m1",

    "xmas_p1_r1_o1_m0",
    "ss_p1_r1_o1_m0",
    "z_p1_r1_o1_m0",
    "m_p1_r1_o1_m0",

    "xmas_p0_r0_o1_m1",
    "ss_p0_r0_o1_m1",
    "z_p0_r0_o1_m1",
    "m_p0_r0_o1_m1",

    "xmas_p0_r1_o1_m0",
    "ss_p0_r1_o1_m0",
    "z_p0_r1_o1_m0",
    "m_p0_r1_o1_m0",

    "xmas_p0_r0_o0_m0",
    "ss_p0_r0_o0_m0",
    "z_p0_r0_o0_m0",
    "m_p0_r0_o0_m0"
]

variation_labels = [
    "Full Architecture",
    "Full Architecture Without Meta",
    "Architecture With Meta Only",
    "Architecture With Reflect Only",
    "Architecture With Reflect, Meta, and Conversation Off"
]

@contextmanager
def tee_stdout(log_file):
    original_stdout = sys.stdout
    try:
        # Open the log file in append mode
        with open(log_file, 'a') as log:
            sys.stdout = Tee(sys.stdout, log)
            yield sys.stdout
    finally:
        sys.stdout = original_stdout

class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)

    def flush(self):
        for stream in self.streams:
            if hasattr(stream, 'flush'):
                stream.flush()

def parse_score(eval_result):
    score = 0
    try:
        cleaned = re.search(r"Score:\s*(\d+)", eval_result)
        if cleaned:
            score = int(cleaned.group(1))
        else:
            cleaned = re.search(r"\b\d+\b", eval_result)
            score = int(cleaned.group(1))

        return score
    except Exception as e:
        return 0

if args.generate:
    for var_index in range(len(variations)):
        for scene_index in range(len(scenarios)):
            log_file_name = f"fulllogs-{ids[(var_index * len(scenarios)) + scene_index]}_s{args.steps}.txt"
            report_file_name = f"report-{ids[(var_index * len(scenarios)) + scene_index]}_s{args.steps}.txt"
            eval_file_name = f"eval-{ids[(var_index * len(scenarios)) + scene_index]}_s{args.steps}.txt"

            if os.path.exists(f"logs/{log_file_name}"):
                if args.overwrite:
                    os.remove(f"logs/{log_file_name}")
                else:
                    print("Logs already exists")
                    continue

            if os.path.exists(f"logs/{report_file_name}"):
                if args.overwrite:
                    os.remove(f"logs/{report_file_name}")
                else:
                    print("Logs already exists")
                    continue

            if os.path.exists(f"logs/{eval_file_name}"):
                if args.overwrite:
                    os.remove(f"logs/{eval_file_name}")
                else:
                    print("Logs already exists")
                    continue

            with tee_stdout(os.path.join("logs", log_file_name)):
                params = { **variations[var_index], "scenario": scenarios[scene_index], "id": f"{ids[(var_index * len(scenarios)) + scene_index]}_s{args.steps}" }
                matrix = Matrix(params)

                matrix.run_singlethread()
                matrix.run_interviews()
                save_report(matrix, f"{ids[(var_index * len(scenarios)) + scene_index]}_s{args.steps}.txt")

if args.reeval:
    for i in range(len(ids)):
        if os.path.exists(f"logs/report-{ids[i]}_s{args.steps}.txt"):
            command = f"python reevaluate.py --report logs/report-{ids[i]}_s{args.steps}.txt"

            process = subprocess.Popen(command, shell=True)
            process.wait()

            if process.returncode == 0:
                print(f"Successfully reevaluated for logs/report-{ids[i]}_s{args.steps}.txt")
            else:
                print(f"Error: Reevaluation failed for logs/report-{ids[i]}_s{args.steps}.txt")

results = []
grouped_data = {label: [] for label in variation_labels}
if args.graph:
    for i in range(len(ids)):
        if os.path.exists(f"logs/eval-{ids[i]}_s{args.steps}.txt"):
            if args.reeval:
                eval_file = f"logs/reeval-{ids[i]}_s{args.steps}.txt"
            else:
                eval_file = f"logs/eval-{ids[i]}_s{args.steps}.txt"
            with open(eval_file) as file:
                input_string = file.read()

            score_matches = re.compile(r"={42}Scores for (.+?)\n(.*?)(?=\n={42}|$)", re.DOTALL).findall(input_string)
            progressive_understanding_scores = []
            adaptive_communication_scores = []
            reflective_depth_scores = []
            knowledge_application_scores = []
            cognitive_flexibility_scores = []
            for name, block in score_matches:
                scores_part = re.compile(r"(Progressive Understanding|Adaptive Communication|Reflective Depth|Knowledge Application|Cognitive Flexibility): (\d+)").findall(block)

                progressive_understanding_scores.append(int(scores_part[0][1]))
                adaptive_communication_scores.append(int(scores_part[1][1]))
                reflective_depth_scores.append(int(scores_part[2][1]))
                knowledge_application_scores.append(int(scores_part[3][1]))
                cognitive_flexibility_scores.append(int(scores_part[4][1]))

            adaptive_communication_scores = [i for i in adaptive_communication_scores if i != 0]

            pu = sum(progressive_understanding_scores) / len(progressive_understanding_scores)
            ac = sum(adaptive_communication_scores) / len(adaptive_communication_scores)
            rd = sum(reflective_depth_scores) / len(reflective_depth_scores)
            ka = sum(knowledge_application_scores) / len(knowledge_application_scores)
            cf = sum(cognitive_flexibility_scores) / len(cognitive_flexibility_scores)

            grouped_data[variation_labels[i // len(scenarios)]].append({
                "progressive_understanding": pu,
                "adaptive_communication": ac,
                "reflective_depth": rd,
                "knowledge_application": ka,
                "cognitive_flexibility": cf,
                "overall": pu + ac + rd + ka + cf
            })
        else:
            grouped_data[variation_labels[i // len(scenarios)]].append({
                "progressive_understanding": 0,
                "adaptive_communication": 0,
                "reflective_depth": 0,
                "knowledge_application": 0,
                "cognitive_flexibility": 0,
                "overall": 0
            })

    means = [np.mean([item.get('overall', 0) for item in grouped_data[label]]) for label in variation_labels]
    std_devs = [np.std([item.get('overall', 0) for item in grouped_data[label]]) for label in variation_labels]

    fig, ax = plt.subplots()
    x = np.arange(len(variation_labels))

    bars = ax.bar(x, means, yerr=std_devs, align='center', alpha=0.7, ecolor='black', capsize=10)

    ax.set_xticks(x)
    ax.set_xticklabels(variation_labels, rotation=45, ha="right")
    ax.set_ylabel('Overall Score')
    ax.set_title('Overall Score by Variation with Standard Deviation')
    ax.legend()

    for bar, mean, std_dev in zip(bars, means, std_devs):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 0.1, f'{mean:.2f} ± {std_dev:.2f}', ha='center', va='bottom')

    print("Final Data")
    for i in range(len(ids)):
        label = variation_labels[i % len(scenarios)]
        print(f"ID: {ids[i]} | {grouped_data[label][i % len(scenarios)]}")

    plt.tight_layout()
    plt.savefig(f"logs/cognitive_graph_{args.steps}.png")
    plt.show()


