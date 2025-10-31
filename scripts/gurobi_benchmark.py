#!/usr/bin/env python3

import os
import csv
from pathlib import Path
import gurobipy as gp
from gurobipy import GRB

def solve_mps_with_gurobi(mps_file_path, time_limit=600):
    """
    Solve a single MPS file using Gurobi for LP relaxation.

    Args:
        mps_file_path (str): Path to the MPS file
        time_limit (int): Time limit in seconds

    Returns:
        dict: Results containing model_name, solve_time, status, objective
    """
    model_name = Path(mps_file_path).stem
    result = {
        'model_name': model_name,
        'solve_time': None,
        'status': None,
        'objective': None,
        'error': None
    }

    try:
        # Read the model
        model = gp.read(mps_file_path)

        # Configure for LP relaxation - convert integer variables to continuous
        for v in model.getVars():
            if v.vType != GRB.CONTINUOUS:
                v.vType = GRB.CONTINUOUS
        model.update()

        # Set solver parameters to match cuOpt benchmark
        model.setParam('TimeLimit', time_limit)
        model.setParam('Presolve', 1)  # Enable presolve like cuOpt
        model.setParam('OutputFlag', 0)  # Suppress verbose output
        model.setParam('Method', -1)  # Automatic method selection

        # Optimize the model
        model.optimize()

        # Extract results using Gurobi's built-in timing
        result['solve_time'] = model.Runtime
        result['status'] = model.Status

        if model.Status == GRB.OPTIMAL:
            result['objective'] = model.ObjVal
        elif model.Status == GRB.TIME_LIMIT:
            result['objective'] = model.ObjVal if model.ObjVal is not None else "N/A"
        else:
            result['objective'] = "N/A"

    except Exception as e:
        result['error'] = str(e)
        result['status'] = "ERROR"

    return result

def main():
    """Main benchmark function."""
    # Configuration
    mps_data_dir = "/benchmarks/miplib_data"
    results_dir = "/gurobi_results"
    csv_file = "/gurobi_results.csv"
    time_limit = 600  # 10 minutes like cuOpt benchmark

    # Create results directory if it doesn't exist
    os.makedirs(results_dir, exist_ok=True)

    # Find all MPS files
    mps_files = list(Path(mps_data_dir).glob("*.mps"))

    if not mps_files:
        print(f"No MPS files found in {mps_data_dir}")
        return

    print(f"Found {len(mps_files)} MPS files to process")
    print(f"Time limit: {time_limit} seconds per problem")
    print(f"Results will be saved to: {csv_file}")
    print("-" * 60)

    # Prepare CSV file
    csv_headers = ['model_name', 'solve_time', 'status', 'objective', 'error']
    results = []

    # Process each MPS file
    for i, mps_file in enumerate(mps_files, 1):
        print(f"[{i}/{len(mps_files)}] Processing: {mps_file.name}")

        # Solve the model
        result = solve_mps_with_gurobi(str(mps_file), time_limit)
        results.append(result)

        # Display progress
        status_desc = {
            GRB.OPTIMAL: "Optimal",
            GRB.TIME_LIMIT: "Time Limit",
            GRB.INFEASIBLE: "Infeasible",
            GRB.UNBOUNDED: "Unbounded",
            GRB.Error: "Error"
        }.get(result['status'], f"Status_{result['status']}")

        time_str = f"{result['solve_time']:.3f}s" if result['solve_time'] is not None else "N/A"
        obj_str = f"{result['objective']:.6e}" if isinstance(result['objective'], (int, float)) else str(result['objective'])

        print(f"  Status: {status_desc}, Time: {time_str}, Objective: {obj_str}")

        if result['error']:
            print(f"  Error: {result['error']}")

        # Save individual log file
        log_content = f"""Model: {result['model_name']}
Status: {status_desc} ({result['status']})
Solve Time: {time_str}
Objective: {obj_str}
"""
        if result['error']:
            log_content += f"Error: {result['error']}\n"

        log_file = os.path.join(results_dir, f"{result['model_name']}.log")
        with open(log_file, 'w') as f:
            f.write(log_content)

    # Save summary CSV
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(results)

    print("-" * 60)
    print(f"Benchmark completed!")
    print(f"Results saved to: {csv_file}")
    print(f"Individual logs saved to: {results_dir}")

    # Summary statistics
    successful_solves = sum(1 for r in results if r['status'] == GRB.OPTIMAL)
    time_limited = sum(1 for r in results if r['status'] == GRB.TIME_LIMIT)
    errors = sum(1 for r in results if r['status'] == "ERROR")

    print(f"\nSummary:")
    print(f"  Total problems: {len(results)}")
    print(f"  Optimal solutions: {successful_solves}")
    print(f"  Time limit reached: {time_limited}")
    print(f"  Errors: {errors}")

    if successful_solves > 0:
        avg_time = sum(r['solve_time'] for r in results if r['solve_time'] is not None) / len([r for r in results if r['solve_time'] is not None])
        print(f"  Average solve time: {avg_time:.3f}s")

if __name__ == "__main__":
    main()