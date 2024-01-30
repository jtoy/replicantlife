import sys
import time
import signal
import argparse

from concurrent.futures import ThreadPoolExecutor
from src.matrix import Matrix
from utils.utils import *
from save_report import save_report #TODO refactor


matrix = None

def main():
    global matrix
    #Base.metadata.create_all(engine)
    # Parse Args
    parser = argparse.ArgumentParser(description='Matrix Simulation')
    #parser.add_argument('--agents', kind=str, default='configs/def_environment.json', help='Path to the env file')
    #parser.add_argument('--world', kind=str, default='configs/def_environment.json', help='Path to the env file')
    parser.add_argument('--scenario', type=str, default='configs/def.json', help='Path to the scenario file')
    parser.add_argument('--environment', type=str, default='configs/largev2.tmj', help='Path to the env file')
    parser.add_argument('--id', type=str, default='', help='Custom Simulation ID')
    args = parser.parse_args()

    #matrix_data = {"agents_file":args.agents, "world_file":args.world}
    #matrix = Matrix(matrix_data)
    if args.id != '':
        matrix = Matrix({ "scenario": args.scenario, "environment": args.environment, "id": args.id })
    else:
        matrix = Matrix({ "scenario": args.scenario, "environment": args.environment })
    # matrix.send_matrix_to_redis()

    pd(f"model:#{MODEL}")
    pd("Initial Agents Positions:")
    redis_connection.set(f"{matrix.id}:matrix_state", json.dumps(matrix.get_arr_2D()))

    # Clear convos
    matrix.clear_redis()

    # Run
    start_time = datetime.now()

    #matrix.run()
    matrix.run_singlethread()
    end_time = datetime.now()
    matrix.run_interviews()

    # Log Runtime
    matrix.simulation_runtime = end_time - start_time
    matrix.send_matrix_to_redis()

    # Save the environment state to a file for inspection
    if matrix.id is not None and matrix.id != '' and RUN_REPORTS != 0:
        save_report(matrix)
    #session.commit()

def signal_handler(signum, frame):
    global matrix,last_interrupt_time, ctrl_c_count
    current_time = time.time()
    #TODO on first control-c, run interview questions then quit, we need to pause the simulation
    if current_time - last_interrupt_time < 2:
        ctrl_c_count += 1
        if ctrl_c_count > 1 :
            pd("Exiting...")
            exit(0)
        else:
            pass

    else:
        ctrl_c_count = 1
        pd("stopping matrix, please wait for current step to finish")
        pd("*"*50)
        matrix.status = "stop"
        matrix.send_matrix_to_redis()
    last_interrupt_time = current_time

ctrl_c_count = 0
last_interrupt_time = time.time()
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    main()

