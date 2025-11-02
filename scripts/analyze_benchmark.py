#!/usr/bin/env python3
"""
Quick analysis script for benchmark results.

Usage:
    python scripts/analyze_benchmark.py benchmark_results/full_benchmark_*.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

def analyze_results(results_file: Path):
    """Analyze benchmark results and print recommendations."""
    
    with open(results_file) as f:
        all_results = json.load(f)
    
    print("\n" + "="*80)
    print("BENCHMARK ANALYSIS")
    print("="*80 + "\n")
    
    # Summary table
    print("📊 SUMMARY TABLE\n")
    print(f"{'Configuration':<40} {'Avg Time':<12} {'Accuracy':<12} {'Success':<10}")
    print("-" * 80)
    
    for result in all_results:
        if 'aggregate_metrics' in result:
            metrics = result['aggregate_metrics']
            config_name = result['config_name'][:38]
            print(f"{config_name:<40} "
                  f"{metrics['avg_response_time']:>8.1f}s    "
                  f"{metrics['avg_accuracy_score']:>8.1%}    "
                  f"{metrics['successful_queries']}/{metrics['total_queries']}")
    
    print("\n" + "="*80 + "\n")
    
    # Find best configurations
    valid_results = [r for r in all_results if 'aggregate_metrics' in r]
    
    if not valid_results:
        print("❌ No valid results found!")
        return
    
    # Fastest
    fastest = min(valid_results, key=lambda x: x['aggregate_metrics']['avg_response_time'])
    print("🏃 FASTEST CONFIGURATION")
    print(f"   {fastest['config_name']}")
    print(f"   Average Time: {fastest['aggregate_metrics']['avg_response_time']:.1f}s")
    print(f"   Accuracy: {fastest['aggregate_metrics']['avg_accuracy_score']:.1%}")
    print()
    
    # Most accurate
    most_accurate = max(valid_results, key=lambda x: x['aggregate_metrics']['avg_accuracy_score'])
    print("🎯 MOST ACCURATE CONFIGURATION")
    print(f"   {most_accurate['config_name']}")
    print(f"   Accuracy: {most_accurate['aggregate_metrics']['avg_accuracy_score']:.1%}")
    print(f"   Average Time: {most_accurate['aggregate_metrics']['avg_response_time']:.1f}s")
    print()
    
    # Best balance (speed × accuracy)
    for result in valid_results:
        metrics = result['aggregate_metrics']
        speed_score = 1 / metrics['avg_response_time']
        accuracy_score = metrics['avg_accuracy_score']
        result['balance_score'] = speed_score * accuracy_score
    
    best_balance = max(valid_results, key=lambda x: x['balance_score'])
    print("⚖️  BEST BALANCE (Speed × Accuracy)")
    print(f"   {best_balance['config_name']}")
    print(f"   Average Time: {best_balance['aggregate_metrics']['avg_response_time']:.1f}s")
    print(f"   Accuracy: {best_balance['aggregate_metrics']['avg_accuracy_score']:.1%}")
    print(f"   Balance Score: {best_balance['balance_score']:.3f}")
    print()
    
    # Recommendations
    print("="*80)
    print("💡 RECOMMENDATIONS")
    print("="*80 + "\n")
    
    # Speed priority
    if fastest['aggregate_metrics']['avg_response_time'] < 15:
        print("✅ For SPEED priority:")
        print(f"   Use: {fastest['config_name']}")
        print(f"   Expected: ~{fastest['aggregate_metrics']['avg_response_time']:.0f}s response time")
        print()
    
    # Quality priority
    if most_accurate['aggregate_metrics']['avg_accuracy_score'] > 0.80:
        print("✅ For QUALITY priority:")
        print(f"   Use: {most_accurate['config_name']}")
        print(f"   Expected: ~{most_accurate['aggregate_metrics']['avg_accuracy_score']:.0%} accuracy")
        print()
    
    # Balanced
    print("✅ For BALANCED approach:")
    print(f"   Use: {best_balance['config_name']}")
    print(f"   Expected: ~{best_balance['aggregate_metrics']['avg_response_time']:.0f}s, "
          f"~{best_balance['aggregate_metrics']['avg_accuracy_score']:.0%} accuracy")
    print()
    
    # Configuration commands
    print("="*80)
    print("🔧 DEPLOYMENT COMMANDS")
    print("="*80 + "\n")
    
    print("To deploy the recommended configuration, update your .env:\n")
    
    recommended = best_balance
    print(f"# Recommended: {recommended['config_name']}")
    print(f"SUPERVISOR_MODEL={recommended['models']['supervisor']}")
    print(f"PLANNER_MODEL={recommended['models']['planner']}")
    print(f"SYNTHESIZER_MODEL={recommended['models']['synthesizer']}")
    print()
    
    print("Then restart backend:")
    print("docker-compose -f docker-compose.prod.yml restart backend")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_benchmark.py <results.json>")
        sys.exit(1)
    
    results_file = Path(sys.argv[1])
    if not results_file.exists():
        print(f"Error: File not found: {results_file}")
        sys.exit(1)
    
    analyze_results(results_file)
