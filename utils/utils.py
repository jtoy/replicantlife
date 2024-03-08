"""
This module defines helper functions used throughout the system,
and defines LLM functions as well.
"""

# TODO remove this
import time
import os
import difflib
import random
import json
from datetime import datetime
import nltk
import redis
import requests

from nltk.corpus import brown
from jinja2 import Template
from sqlalchemy import (
    create_engine,
    # Column,
    # Float,
    # DateTime,
    # Integer,
    # String,
    # PickleType,
    # ForeignKey,
    # JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from configs.configs import *

nltk.download("brown")

# Modify accordingly for requests.post() calls
TIMEOUT = 60


try:
    from vllm import LLM, SamplingParams
except ImportError:
    print("vllm Module not found. Skipping...")

"""
Print Debug Function
"""


def pd(msg, tag=None):
    if DEBUG == "1":
        if (tag and DEBUG_TAGS and tag in DEBUG_TAGS) or tag is None:
            print(f"{msg}")
    # url = "https://discord.com/api/webhooks/1179589082540675113/o8NLAfbISn82hZ9SmGyJ3GAJavIc7OIDS8Qbjl8OoO-jWOBSVLuQ6kgv-_UDju1yWf8M"
    # data = {"content": msg}
    # headers = {"Content-Type": "application/json"}
    # try:
    # response = requests.post(url, json=data, headers=headers)


def unix_to_strftime(unix_time):
    return datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")


def random_common_word():
    # TODO store the array in memory
    common_words = [
        word.lower() for word in brown.words() if len(word) > 2 and word.isalpha()
    ]
    random_common_word = random.choice(common_words)
    return random_common_word


"""
Llm class wrapper

Required to have a running ollama server on machine
"""

SUPPORTED_GPT_MODELS = [
    "gpt-4",
    "gpt-4-1106-preview",
    "gpt-4-vision-preview",
    "gpt-4-32k",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-1106",
]
VLLM_MODELS = ["mistralai/Mistral-7B-Instruct-v0.1"]
OLLAMA_MODELS = ["llama2", "mistral", "orca-mini"]


class Llm:
    def __init__(self, model=MODEL, url=LLAMA_URL, key=OPENAI_KEY):
        self.model = model
        self.urls = url.split(",")
        # self.url = url
        self.openai_api_key = key
        self.call_counter = 0
        self.call_times = []
        self.vllm = None
        self.sampling_params = None

        # Pre-warm Llm
        # if self.model != "off":
        #    self.generate("41+1=?")

    def generate(self, prompt, fallback="Llm Error"):
        # Truncate more than 1400 words
        # lines = prompt.splitlines()
        # truncated_lines = []

        # total_words = 0
        # for line in lines:
        #    words = line.split()
        #    if total_words + len(words) <= 1400:
        #        truncated_lines.append(line)
        #        total_words += len(words)
        #    else:
        #        remaining_words = 1400 - total_words
        #        truncated_words = words[:remaining_words]
        #        truncated_line = ' '.join(truncated_words)
        #        truncated_lines.append(truncated_line)
        #        break

        # prompt = '\n'.join(truncated_lines)
        if self.model == "off":
            return fallback
        start_time = time.time()
        if self.model in SUPPORTED_GPT_MODELS:
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            }

            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                f"https://api.openai.com/v1/chat/completions",
                json=data,
                headers=headers,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                msg = response.json()["choices"][0]["message"]["content"]
                self.call_counter += 1
            else:
                pd(response.text)
                msg = fallback

        elif self.model in VLLM_MODELS:
            if self.vllm is None:
                self.vllm = LLM(model=self.model)
                self.sampling_params = SamplingParams(max_tokens=10000)
            try:
                outputs = self.vllm.generate(prompt, self.sampling_params)
                msg = ""
                for output in outputs:
                    cur_out = output.outputs
                    for o in cur_out:
                        msg = msg + o.text

            except Exception as e: # pylint: disable=broad-except
                print(e)
                msg = fallback
        else:
            data = {"model": self.model, "prompt": prompt, "stream": False}
            # "temperature": 0.4,
            # print(data)
            current_url = self.urls[self.call_counter % len(self.urls)]
            try:
                if self.model == "powerinf":
                    data = {"prompt": prompt, "n_predict": 128}
                    response = requests.post(
                        f"{POWERINF_URL}/completion", json=data, timeout=LLAMA_TIMEOUT
                    )
                    if response.status_code == 200:
                        msg = response.json()["content"]
                        self.call_counter += 1
                    else:
                        msg = fallback
                else:
                    response = requests.post(
                        f"{current_url}/generate", json=data, timeout=LLAMA_TIMEOUT
                    )

                    if response.status_code == 200:
                        msg = response.json()["response"]
                        self.call_counter += 1
                    else:
                        msg = fallback + ": " + response.text

            except Exception: # pylint: disable=broad-except
                msg = fallback

        end_time = time.time()
        self.log_calls(prompt, msg, end_time - start_time)
        self.call_times.append(end_time - start_time)
        if len(self.urls) > 1:
            pd(f"current url {current_url}")
        pd(f"INPUT:\n {prompt}")
        pd(f"OUTPUT:\n {msg}")
        pd(f"runtime: {end_time - start_time}")
        return msg

    def embeddings(self, prompt, fallback=[0.5, 0.5, 0.5]):
        if self.model == "off":
            return fallback

        start_time = time.time()
        if self.model in SUPPORTED_GPT_MODELS:
            data = {
                "input": prompt,
                "model": "text-embedding-ada-002",
                "encoding_format": "float",
            }

            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                f"https://api.openai.com/v1/embeddings", json=data, headers=headers, timeout=TIMEOUT
            )

            if response.status_code == 200:
                msg = response.json()["data"][0]["embedding"]
                self.call_counter += 1
            else:
                msg = fallback
        else:
            data = {
                "model": self.model,
                "prompt": prompt,
            }
            current_url = self.urls[self.call_counter % len(self.urls)]
            if self.model == "powerinf":
                data = {"content": prompt}
                response = requests.post(f"{POWERINF_URL}/embedding", json=data, timeout=TIMEOUT)
            else:
                response = requests.post(f"{current_url}/embeddings", json=data, timeout=TIMEOUT)

            if response.status_code == 200:
                msg = response.json()["embedding"]
                self.call_counter += 1
            else:
                msg = fallback

        end_time = time.time()
        pd(f"embed conversion for: {prompt}")
        pd(f"runtime: {end_time - start_time}")
        self.log_calls(prompt, msg, end_time - start_time)
        self.call_times.append(end_time - start_time)
        return msg

    def log_calls(self, prompt, output, time):
        with open("storage/llm_logs.tsv", "a", encoding="utf-8") as file:
            file.write(f"{prompt}\t{output}\t{time}\n")

    def prompt(self, prompt_name, variables=None, fallback="Llm Error"):
        if self.model == "off":
            return ""

        current_path = os.getcwd()
        file_path = os.path.join(
            current_path, "prompts", self.model, prompt_name + ".txt"
        )

        if not os.path.exists(file_path):
            default_folder_path = os.path.join(
                current_path, "prompts", "general", prompt_name + ".txt"
            )
            if not os.path.exists(default_folder_path):
                raise FileNotFoundError(
                    f"Couldnt find {file_path} or {default_folder_path}."
                )
            else:
                file_path = default_folder_path
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # new_prompt = content.format(**variables)
        template = Template(content)
        new_prompt = template.render(**variables)

        output = self.generate(new_prompt, fallback)
        return output


llm = Llm()
"""
REDIS
"""
# TODO get rid of globals
if "REDIS_URL" in globals():
    REDIS_CONNECTION = redis.Redis.from_url(REDIS_URL)
else:
    print("REDIS_URL environment variable is not set.")
    REDIS_CONNECTION = None


def print_and_log(content, key):
    return
    redis_log(content, key)
    print(content)


def redis_log(content, key):
    if LOG_TO_REDIS == 1:
        REDIS_CONNECTION.rpush(key, json.dumps(content))


def find_most_similar(inp, arr):
    most_similar = difflib.get_close_matches(inp, arr, n=1, cutoff=0.8)

    if most_similar:
        return most_similar[0]

    return arr[0]


"""
DATABASE
"""
Base = declarative_base()
engine = create_engine("sqlite:///storage/matrix.db")
Session = sessionmaker(bind=engine)
session = Session()
