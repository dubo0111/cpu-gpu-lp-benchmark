#!/usr/bin/env python3

import os
import re
import csv
from pathlib import Path

def parse_cuopt_log(log_file_path):
    """
    Parse a single cuOpt log file to extract key information.

    Args:
        log_file_path (str): Path to cuOpt log file

    Returns:
        dict: Results containing model_name, solve_time, status, objective
    """
    model_name = Path(log_file_path).stem
    result = {
        'model_name': model_name,
        'solve_time': None,
        'status': None,
        'objective': None,
        'error': None
    }

    try:
        with open(log_file_path, 'r') as f:
            content = f.read()

        # First, find concurrent line which contains the actual solve time
        # Pattern: Concurrent time: 0.479s, total time 0.522s
        concurrent_pattern = r'Concurrent time:\s*([\d,\.]+s),\s*total time\s*([\d,\.]+s)'
        concurrent_match = re.search(concurrent_pattern, content)

        # Then find status line for status and objective
        # Pattern: Status: Optimal   Objective: 2.87906569e+03  Iterations: 277
        status_pattern = r'Status:\s*(\w+)\s+Objective:\s*(\S+)\s+Iterations:\s*\d+'
        status_match = re.search(status_pattern, content)

        if concurrent_match and status_match:
            # Extract solve time from concurrent line (total time)
            total_time_str = concurrent_match.group(2)
            if total_time_str.endswith('s'):
                total_time_str = total_time_str[:-1]
            total_time_clean = total_time_str.replace(',', '')
            result['solve_time'] = float(total_time_clean)

            # Extract status and objective from status line
            status = status_match.group(1)
            objective = status_match.group(2)

            # Convert status to numeric for consistency with Gurobi
            status_map = {
                'Optimal': 2,  # GRB.OPTIMAL
                'Time': 9,     # GRB.TIME_LIMIT (if it says "Time Limit")
                'Infeasible': 3,  # GRB.INFEASIBLE
                'Unbounded': 5,   # GRB.UNBOUNDED
                'Unknown': 11     # Other status
            }

            # Handle "Time Limit" vs just "Time"
            if 'Limit' in status:
                status = 'Time Limit'

            result['status'] = status_map.get(status, 11)
            result['objective'] = objective
        else:
            # If no required lines found, it might be an error or incomplete log
            result['status'] = 'ERROR'
            result['error'] = 'No concurrent and status lines found in log'

    except Exception as e:
        result['status'] = 'ERROR'
        result['error'] = str(e)

    return result

def main():
    """Main function to parse all cuOpt logs and create CSV."""
    # Configuration
    cuopt_results_dir = "/benchmarks/miplib_result"
    csv_file = "/cuopt_results.csv"

    # Find all log files
    log_files = list(Path(cuopt_results_dir).glob("*.log"))

    if not log_files:
        print(f"No log files found in {cuopt_results_dir}")
        return

    print(f"Found {len(log_files)} cuOpt log files to parse")
    print(f"Results will be saved to: {csv_file}")
    print("-" * 60)

    # Prepare CSV file
    csv_headers = ['model_name', 'solve_time', 'status', 'objective', 'error']
    results = []

    # Process each log file
    for i, log_file in enumerate(log_files, 1):
        print(f"[{i}/{len(log_files)}] Parsing: {log_file.name}")

        result = parse_cuopt_log(str(log_file))
        results.append(result)

        # Display progress
        if result['status'] == 'ERROR':
            print(f"  Status: ERROR, Time: N/A, Objective: N/A")
            if result['error']:
                print(f"  Error: {result['error']}")
        else:
            status_desc = {
                2: "Optimal",
                9: "Time Limit",
                3: "Infeasible",
                5: "Unbounded",
                11: "Unknown"
            }.get(result['status'], f"Status_{result['status']}")

            time_str = f"{result['solve_time']:.3f}s" if result['solve_time'] is not None else "N/A"
            obj_str = str(result['objective']) if result['objective'] is not None else "N/A"

            print(f"  Status: {status_desc}, Time: {time_str}, Objective: {obj_str}")

    # Save CSV
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(results)

    print("-" * 60)
    print(f"Parsing completed!")
    print(f"Results saved to: {csv_file}")

    # Summary statistics
    optimal_solves = sum(1 for r in results if r['status'] == 2)
    time_limited = sum(1 for r in results if r['status'] == 9)
    errors = sum(1 for r in results if r['status'] == 'ERROR')

    print(f"\nSummary:")
    print(f"  Total problems: {len(results)}")
    print(f"  Optimal solutions: {optimal_solves}")
    print(f"  Time limit reached: {time_limited}")
    print(f"  Errors: {errors}")

    if optimal_solves > 0:
        valid_times = [r['solve_time'] for r in results if r['solve_time'] is not None]
        if valid_times:
            avg_time = sum(valid_times) / len(valid_times)
            print(f"  Average solve time: {avg_time:.3f}s")

if __name__ == "__main__":
    main()