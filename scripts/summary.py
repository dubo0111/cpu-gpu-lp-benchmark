#!/usr/bin/env python3

import pandas as pd

def main():
    """Generate a final summary of the benchmark comparison."""
    print("🔍 CPU vs GPU LP Benchmark - Final Summary")
    print("=" * 60)

    # Load results
    cuopt_df = pd.read_csv("../cuopt_results.csv")
    gurobi_df = pd.read_csv("../gurobi_results.csv")
    comparison_df = pd.read_csv("../comparison_results.csv")

    print(f"\n📊 Dataset Overview:")
    print(f"  Total MIPLIB problems: 240")
    print(f"  cuOpt results: {len(cuopt_df)} problems")
    print(f"  Gurobi results: {len(gurobi_df)} problems")

    # Success rates
    cuopt_success_rate = (cuopt_df['status'] == 2).sum() / len(cuopt_df) * 100
    gurobi_success_rate = (gurobi_df['status'] == 2).sum() / len(gurobi_df) * 100

    print(f"\n✅ Success Rates:")
    print(f"  cuOpt (GPU): {cuopt_success_rate:.1f}% success rate")
    print(f"  Gurobi (CPU): {gurobi_success_rate:.1f}% success rate")

    # Performance comparison for common solved problems
    both_solved = comparison_df[
        (comparison_df['winner'] == 'cuOpt') | (comparison_df['winner'] == 'Gurobi')
    ]

    if len(both_solved) > 0:
        cuopt_faster = (both_solved['winner'] == 'cuOpt').sum()
        gurobi_faster = (both_solved['winner'] == 'Gurobi').sum()
        ties = (both_solved['winner'] == 'Tie').sum()

        avg_speedup = both_solved['speedup'].mean()
        median_speedup = both_solved['speedup'].median()

        print(f"\n⚡ Performance Comparison ({len(both_solved)} common solved problems):")
        print(f"  cuOpt faster: {cuopt_faster} problems ({cuopt_faster/len(both_solved)*100:.1f}%)")
        print(f"  Gurobi faster: {gurobi_faster} problems ({gurobi_faster/len(both_solved)*100:.1f}%)")
        print(f"  Same performance: {ties} problems ({ties/len(both_solved)*100:.1f}%)")
        print(f"  Average speedup (Gurobi/cuOpt): {avg_speedup:.2f}x")
        print(f"  Median speedup (Gurobi/cuOpt): {median_speedup:.2f}x")

    # Key insights
    print(f"\n💡 Key Insights:")

    # Overall winner
    if 'winner' in comparison_df.columns:
        winner_counts = comparison_df['winner'].value_counts()
        if len(winner_counts) > 0:
            overall_winner = winner_counts.index[0] if winner_counts.iloc[0] > 0 else None
            if overall_winner:
                print(f"  🏆 Overall winner: {overall_winner}")
                print(f"     Won {winner_counts[overall_winner]} out of {len(winner_counts)} compared problems")

    # Specific issues
    print(f"\n⚠️  Specific Issues to Investigate:")

    # cuOpt memory issues
    cuopt_memory_issues = cuopt_df[cuopt_df['status'].str.contains('ERROR', na=False)]
    if len(cuopt_memory_issues) > 0:
        print(f"  💾 cuOpt memory/out-of-memory issues: {len(cuopt_memory_issues)} problems")
        for _, row in cuopt_memory_issues.iterrows():
            print(f"     - {row['model_name']}: {row['error']}")

    # Gurobi time limit issues (if any)
    gurobi_time_issues = gurobi_df[gurobi_df['status'] == 9]
    if len(gurobi_time_issues) > 0:
        print(f"  ⏰ Gurobi time limit issues: {len(gurobi_time_issues)} Problems")
        for _, row in gurobi_time_issues.iterrows():
            print(f"     - {row['model_name']}: hit 600s limit")

    # Performance extremes
    if 'speedup' in comparison_df.columns:
        extreme_cases = comparison_df.nlargest(5, 'speedup')
        print(f"\n📈 Most Extreme Performance Differences:")
        for _, row in extreme_cases.iterrows():
            faster = "Gurobi" if row['speedup'] < 1 else "cuOpt"
            print(f"  {row['model_name']}: {row['speedup']:.1f}x faster ({faster})")

    print(f"\n📁 Files Generated:")
    print(f"  • cuopt_results.csv - Parsed cuOpt (GPU) results")
    print(f"  • gurobi_results.csv - Gurobi (CPU) benchmark results")
    print(f"  • comparison_results.csv - Detailed performance comparison")

    # Load CSV
    df = pd.read_csv("../comparison_results.csv")
    df = df [["model_name", "cuopt_solve_time", "cuopt_objective", "gurobi_solve_time", "gurobi_objective", "winner", "speedup"]]
    # Convert to Markdown
    print(df.to_markdown(index=False))

if __name__ == "__main__":
    main()