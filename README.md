# About


replicantlife is a simulation engine for generative agents  that can be used in a simulation engine or standalone.
Agents are powered with metacognition modules that allow that to learn and adjust their strategy over time.

Read the paper: https://arxiv.org/abs/5336760

Learn more about the project: https://replicantlife.com

Join discord here: https://discord.com/invite/DNBwbKT3Ns

# Goal

Our goal is to build the most powerful generative AI agent and simulation framework.
We are looking for help on this project. If you know python or know how to use chatgpt, you can contribute :)

# Paper

Metacognition is all you need?  Using Introspection in Generative Agents to Improve Goal-directed Behavior

Recent advances in Large Language Models (LLMs) have shown impressive capabilities in various applications, yet LLMs face challenges such as limited context windows and difficulties in generalization. In this paper, we introduce a metacognition module for generative agents, enabling them to observe their own thought processes and actions. This metacognitive approach, designed to emulate System 1 and System 2 cognitive processes, allows agents to significantly enhance their performance by modifying their strategy. We tested the metacognition module on a variety of scenarios, including a situation where generative agents must survive a zombie apocalypse, and observe that our system outperform others, while agents adapt and improve their strategies to complete tasks over time.

![Flow diagram of metacognition](images/flow-diag.jpg?raw=true )




# Run Simulation

`python engine.py`


## Simulation flags

```
- DEBUG # For print debugs (default = 1)
- LLAMA_URL # For accessing ollama endpoint (default="http://localhost:11434/api/generate")
- REDIS_URL # For accessing redis endpoint (default="redis://localhost:6379")
- MODEL # For setting ollama model (default="mistral" | "off" to disable llm)
- MATRIX_SIZE # Size of map (default="15")
- SIMULATION_STEPS # Simulation steps to run (default="5")
- PERCEPTION_RANGE # Block ranges of agent vision (default="2")
- NUM_AGENTS # Num of agents in simulation (default="0")
- NUM_ZOMBIES # Num of zombies in simulation (default="0")
- MAX_WORKERS # Num of thread workers for running the simulation (default="1")
```

### Usage

`MODEL=off python engine.py`

This will run the simulation without LLM

You can also choose to add these params to `.env` file.

### Connecting to Live Production Redis

Just pass in `REDIS_URL=<redis url>` as param for running simulation.

### Changing Environment

We can create our own environment and agents by adding a `.json` file in `configs/`.
Just follow the format of `def_environment.json`, run the engine with
`--scenario` and `--env` flag indicating the scenario and environment simulation you want.

## Test Simulations

![Zombie scenario](images/zombie.jpeg?raw=true)

### Spyfall

`python engine.py --scenario configs/spyfall_situation.json  --env configs/largev2.tmj`

### Christmas Party

`python engine.py --scenario configs/christmas_party_situation.json --env configs/largev2.tmj`

### Secret Santa Game

`python engine.py --scenario configs/secret_santa_situation.json --world configs/largev2.tmj`



### Murder
Someone is killing people

`python engine.py --scenario configs/murder_situation.json --world configs/largev2.tmj`

### Zombie
There are zombies killing people
`NUM_ZOMBIES=5 python engine.py --scenario configs/zombie_situation.json --world configs/largev2.tmj`


## Adding New Tilemap Assets

1. Create Tilemap in tilemap editor. Make sure to add proper collisions. Take note of the width/height you used.

2. From the tilemap json file, get the layer of the collisions. Modify `utils/convert_to_2d.py`. Instructions are inside the file.

3. Create the `environment.json` file inside `configs/` directory. You can copy `def_environment.json` as a starting point for now.

    * Run `python utils/convert_to_2d.py` and paste the result in the `environment.json` under `"collision"`.

    * Manually add the x, y coordinates from tilemap to the json file. If you are referencing from inside the tilemap editor, we flip the x,y coordinates for our usecase.

    * Add the `"width"` and `"height"` to the json file.

4. Inside `static` directory, create a unique folder to reference the new assets that you made. It should contain:

    * `matrix.png` which is the map png file.

    * `characters/` directory which will contain the png files for the characters. THEY SHOULD BE THE SAME NAME with what you declared inside the json file, + .png

5. Run server and simulation.

6. Go to `http://127.0.0.1:5000/?assets=<name of folder you made earlier>` to see the new map.


## Unit Tests

`python test.py`

## Simulation Report
python run_all_sims.py

MODEL=off python run_all_sims.py

# options


  1. `--id` For passing custom simulation id (mostly for redis integration)

  2. `--scenario` For passing a scenario json. (defaults to configs/def.json).

      * For crafting agents init data, we can literally pass no params and it will randomize Agent data.

      * Refer to agents.py to see all available params. Some examples are "name", "description", "goals", etc.

      * In scenario file, this is where we define the simulation params that are customizable. Refer to `configs/secret_santa_situation.json` for more customized sample.

  3. `--environment` For passing in the environment file. (defaults to configs/largev2.tmj)

      * This requires a correctly formatted map file from tiledmap editor. I'll teach Adrian how to make one, it's just custom layer naming and grouping then our program will automatically parse it.

  4. `MODEL=model_name` For choosing custom ollama or gpt models (or turning it off by passing `off`)

  5. `ALLOW_PLAN=<1 or 0>` to turn planning on or off (for speed)

  6. `ALLOW_REFLECT=<1 or 0>` to turn reflection on or off (for speed)

  7. `LLM_ACTION=<1 or 0>` to turn on llm-powered decision making.

  8. `SHORT_MEMORY_CAPACITY=<1 or 0>` to indicate how many memories needs to be stored on short term memory before reflecting and summarizing them.



## Running Cognitive Test Graph

* `python cognitive_test.py --generate --steps <num_of_steps, default 100>` to generate the result files.

* `python cognitive_test.py --generate --overwrite --steps <num_of_steps, default 100>` flag to generate and overwrite the previous result files.

* `python cognitive_test.py --graph` to generate the graph.

# Run frontend.py

(this is not working right now)

`python frontend.py`

This should start a basic webserver that would allow us to view the game state at `http://localhost:5000`

## Creating Maps

1. Layer Hierarchy:

    * Collisions `represents tiles that cannot be traversed`

    * Location_name/ `group folder that contains rooms for that current location`

        * Bounds `represents tiles occupied by current location`

        * Room_name/ `group folder that contains objects for current room`

            * Bounds `represents tiles occupied by current room`

            * Object_name `represents an object inside the current room`

2. Save as JSON map format. Move to `configs/<your_map_name>.tmj`

3. Pass in to `engine.py` with `--environment` flag.
