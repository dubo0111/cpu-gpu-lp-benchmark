#!/usr/bin/env python3

import csv
import pandas as pd
from pathlib import Path

def load_results():
    """Load both cuOpt and Gurobi results from CSV files."""
    cuopt_file = "/cuopt_results.csv"
    gurobi_file = "/gurobi_results.csv"

    # Load cuOpt results
    cuopt_df = pd.read_csv(cuopt_file)
    cuopt_df['solver'] = 'cuOpt'

    # Load Gurobi results
    gurobi_df = pd.read_csv(gurobi_file)
    gurobi_df['solver'] = 'Gurobi'

    return cuopt_df, gurobi_df

def analyze_comparison():
    """Compare cuOpt and Gurobi results and identify specific issues."""
    cuopt_df, gurobi_df = pd.read_csv("/cuopt_results.csv"), pd.read_csv("/gurobi_results.csv")

    print("=" * 80)
    print("CPU vs GPU LP Benchmark Comparison")
    print("=" * 80)

    # Basic statistics
    print(f"\n📊 Basic Statistics:")
    print(f"  cuOpt results: {len(cuopt_df)} problems")
    print(f"  Gurobi results: {len(gurobi_df)} problems")

    # Status analysis
    print(f"\n📈 Status Analysis:")

    # cuOpt status analysis - convert to numeric first
    cuopt_df['status_num'] = pd.to_numeric(cuopt_df['status'], errors='coerce')
    cuopt_optimal = (cuopt_df['status_num'] == 2).sum()
    cuopt_errors = (cuopt_df['status'].str.contains('ERROR')).sum()
    cuopt_other = len(cuopt_df) - cuopt_optimal - cuopt_errors

    print(f"  cuOpt:")
    print(f"    Optimal: {cuopt_optimal} ({cuopt_optimal/len(cuopt_df)*100:.1f}%)")
    print(f"    Errors: {cuopt_errors} ({cuopt_errors/len(cuopt_df)*100:.1f}%)")
    print(f"    Other: {cuopt_other} ({cuopt_other/len(cuopt_df)*100:.1f}%)")

    # Gurobi status analysis - convert to numeric first
    gurobi_df['status_num'] = pd.to_numeric(gurobi_df['status'], errors='coerce')
    gurobi_optimal = (gurobi_df['status_num'] == 2).sum()
    gurobi_time_limit = (gurobi_df['status_num'] == 9).sum()
    gurobi_errors = (gurobi_df['status'].str.contains('ERROR')).sum()
    gurobi_other = len(gurobi_df) - gurobi_optimal - gurobi_time_limit - gurobi_errors

    print(f"  Gurobi:")
    print(f"    Optimal: {gurobi_optimal} ({gurobi_optimal/len(gurobi_df)*100:.1f}%)")
    print(f"    Time Limit: {gurobi_time_limit} ({gurobi_time_limit/len(gurobi_df)*100:.1f}%)")
    print(f"    Errors: {gurobi_errors} ({gurobi_errors/len(gurobi_df)*100:.1f}%)")
    print(f"    Other: {gurobi_other} ({gurobi_other/len(gurobi_df)*100:.1f}%)")

    # Performance comparison for common problems
    common_models = set(cuopt_df['model_name']) & set(gurobi_df['model_name'])
    print(f"\n🔄 Performance Comparison (Common Problems: {len(common_models)}):")

    # Merge dataframes for comparison
    merged_df = pd.merge(
        cuopt_df[['model_name', 'solve_time', 'status', 'objective']],
        gurobi_df[['model_name', 'solve_time', 'status', 'objective']],
        on='model_name',
        suffixes=('_cuopt', '_gurobi')
    )

    # Filter to problems where both solved optimally
    both_optimal = merged_df[
        (merged_df['status_cuopt'] == 2) & (merged_df['status_gurobi'] == 2)
    ]

    if len(both_optimal) > 0:
        # Calculate speedup
        both_optimal['speedup'] = both_optimal['solve_time_gurobi'] / both_optimal['solve_time_cuopt']

        print(f"  Both solved optimally: {len(both_optimal)} problems")
        print(f"  Average cuOpt time: {both_optimal['solve_time_cuopt'].mean():.3f}s")
        print(f"  Average Gurobi time: {both_optimal['solve_time_gurobi'].mean():.3f}s")
        print(f"  Average speedup (Gurobi/cuOpt): {both_optimal['speedup'].mean():.2f}x")
        print(f"  cuOpt faster in: {(both_optimal['speedup'] > 1).sum()} problems")
        print(f"  Gurobi faster in: {(both_optimal['speedup'] < 1).sum()} problems")

    # Specific issue analysis
    print(f"\n🚨 Specific Issues Analysis:")

    # 1. Gurobi time limit issues (status = 9)
    gurobi_time_limit_problems = gurobi_df[gurobi_df['status'] == 9]
    if len(gurobi_time_limit_problems) > 0:
        print(f"\n  ⏰ Gurobi Time Limit Issues ({len(gurobi_time_limit_problems)} problems):")
        for _, row in gurobi_time_limit_problems.iterrows():
            cuopt_status = cuopt_df[cuopt_df['model_name'] == row['model_name']]['status'].iloc[0] if row['model_name'] in cuopt_df['model_name'].values else "N/A"
            cuopt_time = cuopt_df[cuopt_df['model_name'] == row['model_name']]['solve_time'].iloc[0] if row['model_name'] in cuopt_df['model_name'].values else "N/A"
            print(f"    {row['model_name']}: Gurobi hit time limit, cuOpt status={cuopt_status}, time={cuopt_time}s")

    # 2. cuOpt error issues (marked as OOM)
    cuopt_error_problems = cuopt_df[cuopt_df['status'] == 'ERROR']
    if len(cuopt_error_problems) > 0:
        print(f"\n  💾 cuOpt Error Issues ({len(cuopt_error_problems)} problems):")
        for _, row in cuopt_error_problems.iterrows():
            gurobi_status = gurobi_df[gurobi_df['model_name'] == row['model_name']]['status'].iloc[0] if row['model_name'] in gurobi_df['model_name'].values else "N/A"
            gurobi_time = gurobi_df[gurobi_df['model_name'] == row['model_name']]['solve_time'].iloc[0] if row['model_name'] in gurobi_df['model_name'].values else "N/A"
            print(f"    {row['model_name']}: cuOpt error ({row['error']}), Gurobi status={gurobi_status}, time={gurobi_time}s")

    # 3. Problems where one solver succeeded and the other failed
    print(f"\n  🔄 Solver Success Comparison:")

    # cuOpt succeeded, Gurobi failed/time limited
    cuopt_success_gurobi_fail = []
    for model in common_models:
        cuopt_row = cuopt_df[cuopt_df['model_name'] == model].iloc[0]
        gurobi_row = gurobi_df[gurobi_df['model_name'] == model].iloc[0]

        if cuopt_row['status_num'] == 2 and gurobi_row['status_num'] != 2:
            cuopt_success_gurobi_fail.append((model, cuopt_row, gurobi_row))

    if cuopt_success_gurobi_fail:
        print(f"    cuOpt succeeded, Gurobi failed/time limited ({len(cuopt_success_gurobi_fail)} problems):")
        for model, cuopt_row, gurobi_row in cuopt_success_gurobi_fail:
            gurobi_status_desc = {
                2: "Optimal", 9: "Time Limit", 3: "Infeasible", 5: "Unbounded", "ERROR": "Error"
            }.get(gurobi_row['status_num'], f"Status_{gurobi_row['status_num']}")
            print(f"      {model}: cuOpt {cuopt_row['solve_time']:.3f}s, Gurobi {gurobi_status_desc}")

    # Gurobi succeeded, cuOpt failed
    gurobi_success_cuopt_fail = []
    for model in common_models:
        cuopt_row = cuopt_df[cuopt_df['model_name'] == model].iloc[0]
        gurobi_row = gurobi_df[gurobi_df['model_name'] == model].iloc[0]

        if gurobi_row['status_num'] == 2 and cuopt_row['status_num'] != 2:
            gurobi_success_cuopt_fail.append((model, cuopt_row, gurobi_row))

    if gurobi_success_cuopt_fail:
        print(f"    Gurobi succeeded, cuOpt failed ({len(gurobi_success_cuopt_fail)} problems):")
        for model, cuopt_row, gurobi_row in gurobi_success_cuopt_fail:
            print(f"      {model}: Gurobi {gurobi_row['solve_time']:.3f}s, cuOpt error ({cuopt_row['error']})")

    # Create detailed comparison CSV
    print(f"\n💾 Creating detailed comparison file...")

    # Prepare comparison data
    comparison_data = []
    for model in common_models:
        cuopt_row = cuopt_df[cuopt_df['model_name'] == model].iloc[0]
        gurobi_row = gurobi_df[gurobi_df['model_name'] == model].iloc[0]

        comparison_data.append({
            'model_name': model,
            'cuopt_solve_time': cuopt_row['solve_time'] if cuopt_row['solve_time'] is not None else None,
            'cuopt_status': cuopt_row['status'],
            'cuopt_objective': cuopt_row['objective'],
            'cuopt_error': cuopt_row['error'],
            'gurobi_solve_time': gurobi_row['solve_time'] if gurobi_row['solve_time'] is not None else None,
            'gurobi_status': gurobi_row['status'],
            'gurobi_objective': gurobi_row['objective'],
            'gurobi_error': gurobi_row['error'],
            'speedup': gurobi_row['solve_time'] / cuopt_row['solve_time'] if (cuopt_row['solve_time'] is not None and gurobi_row['solve_time'] is not None and cuopt_row['solve_time'] > 0) else None,
            'winner': 'cuOpt' if (cuopt_row['solve_time'] is not None and gurobi_row['solve_time'] is not None and cuopt_row['solve_time'] < gurobi_row['solve_time']) else 'Gurobi' if (cuopt_row['solve_time'] is not None and gurobi_row['solve_time'] is not None and gurobi_row['solve_time'] < cuopt_row['solve_time']) else 'Tie' if (cuopt_row['solve_time'] is not None and gurobi_row['solve_time'] is not None) else 'N/A'
        })

    # Save comparison CSV
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df.to_csv("/home/dubo/Projects/cpu-gpu-lp-benchmark/comparison_results.csv", index=False)

    print(f"  Detailed comparison saved to: comparison_results.csv")

    # Summary of key findings
    print(f"\n🎯 Key Findings:")
    if len(both_optimal) > 0:
        faster_cuopt = (both_optimal['speedup'] > 1).sum()
        faster_gurobi = (both_optimal['speedup'] < 1).sum()
        print(f"  • Performance: cuOpt faster in {faster_cuopt} problems, Gurobi faster in {faster_gurobi} problems")
        print(f"  • Average speedup: {both_optimal['speedup'].mean():.2f}x (Gurobi/cuOpt)")

    print(f"  • Reliability: cuOpt solved {cuopt_optimal}/{len(cuopt_df)} problems, Gurobi solved {gurobi_optimal}/{len(gurobi_df)} problems")
    print(f"  • Time limits: Gurobi hit time limit in {gurobi_time_limit} problems")
    print(f"  • Errors: cuOpt had {cuopt_errors} errors, Gurobi had {gurobi_errors} errors")

if __name__ == "__main__":
    try:
        analyze_comparison()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Make sure both cuopt_results.csv and gurobi_results.csv exist before running this comparison.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")