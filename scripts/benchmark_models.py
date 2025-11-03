#!/usr/bin/env python3
"""
Model Benchmarking Script for Production

Tests different model combinations across multiple queries to measure:
- Response time (speed)
- Answer quality (accuracy)
- Memory usage

Usage:
    python scripts/benchmark_models.py --output results.json
"""

import asyncio
import json
import time
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.supervisor import SupervisorAgent
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Test Configuration
# ============================================================================

# Models to test
MODELS_TO_TEST = [
    {
        "name": "Current (llama3.1:8b)",
        "supervisor": "llama3.1",
        "planner": "llama3.1",
        "synthesizer": "llama3.1"
    },
    {
        "name": "Qwen2.5:72b (All)",
        "supervisor": "qwen2.5:72b",
        "planner": "qwen2.5:72b",
        "synthesizer": "qwen2.5:72b"
    },
    {
        "name": "Qwen2.5:32b (All)",
        "supervisor": "qwen2.5:32b",
        "planner": "qwen2.5:32b",
        "synthesizer": "qwen2.5:32b"
    },
    {
        "name": "Mixtral:8x7b (All)",
        "supervisor": "mixtral:8x7b",
        "planner": "mixtral:8x7b",
        "synthesizer": "mixtral:8x7b"
    },
    {
        "name": "Specialized (Qwen72b + Mixtral + Llama8b)",
        "supervisor": "qwen2.5:72b",
        "planner": "mixtral:8x7b",
        "synthesizer": "llama3.1"
    },
    {
        "name": "Fast (Qwen32b + Llama8b)",
        "supervisor": "qwen2.5:32b",
        "planner": "qwen2.5:32b",
        "synthesizer": "llama3.1"
    }
]

# Test queries covering different complexity levels
TEST_QUERIES = [
    {
        "query": "Who is the CFO of Apple?",
        "category": "simple_factual",
        "expected_keywords": ["Kevan Parekh", "Chief Financial Officer", "CFO"],
        "difficulty": "easy"
    },
    {
        "query": "What were Apple's total revenues last fiscal year?",
        "category": "numerical_extraction",
        "expected_keywords": ["revenue", "416", "billion"],
        "difficulty": "easy"
    },
    {
        "query": "What are the main risk factors for investing in Amazon?",
        "category": "complex_analysis",
        "expected_keywords": ["risk", "competition", "regulatory", "operational"],
        "difficulty": "medium"
    },
    {
        "query": "How much did Microsoft spend on research and development last year?",
        "category": "numerical_extraction",
        "expected_keywords": ["research", "development", "R&D", "billion"],
        "difficulty": "easy"
    },
    {
        "query": "What is Microsoft's business strategy for cloud computing?",
        "category": "strategic_analysis",
        "expected_keywords": ["cloud", "Azure", "strategy", "growth"],
        "difficulty": "medium"
    },
    {
        "query": "Compare Apple's gross margin to Microsoft's gross margin",
        "category": "comparative_analysis",
        "expected_keywords": ["gross margin", "Apple", "Microsoft", "percent", "%"],
        "difficulty": "hard"
    },
    {
        "query": "What were the key highlights from Pfizer's latest 10-K?",
        "category": "summarization",
        "expected_keywords": ["revenue", "product", "pipeline", "clinical"],
        "difficulty": "medium"
    },
    {
        "query": "Who are the members of Apple's board of directors?",
        "category": "list_extraction",
        "expected_keywords": ["director", "board", "Tim Cook"],
        "difficulty": "easy"
    },
    {
        "query": "What is Amazon's policy on stock-based compensation?",
        "category": "policy_extraction",
        "expected_keywords": ["stock", "compensation", "equity", "RSU"],
        "difficulty": "medium"
    },
    {
        "query": "Explain Amazon's revenue recognition policy for AWS services",
        "category": "technical_accounting",
        "expected_keywords": ["revenue recognition", "AWS", "services", "accounting"],
        "difficulty": "hard"
    }
]

# ============================================================================
# Benchmarking Functions
# ============================================================================

async def test_model_configuration(
    config: Dict,
    queries: List[Dict],
    run_id: str
) -> Dict:
    """
    Test a specific model configuration across all queries.
    
    Args:
        config: Model configuration dict
        queries: List of test queries
        run_id: Unique identifier for this test run
        
    Returns:
        Results dict with timing and response data
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing Configuration: {config['name']}")
    logger.info(f"{'='*80}")
    
    # Temporarily override settings
    original_supervisor = settings.supervisor_model
    original_planner = settings.planner_model
    original_synthesizer = settings.synthesizer_model
    
    try:
        # Set new models
        settings.supervisor_model = config['supervisor']
        settings.planner_model = config['planner']
        settings.synthesizer_model = config['synthesizer']
        
        logger.info(f"Models: Supervisor={config['supervisor']}, "
                   f"Planner={config['planner']}, "
                   f"Synthesizer={config['synthesizer']}")
        
        # Initialize supervisor with new config
        supervisor = SupervisorAgent()
        
        results = {
            "config_name": config['name'],
            "models": {
                "supervisor": config['supervisor'],
                "planner": config['planner'],
                "synthesizer": config['synthesizer']
            },
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "queries": []
        }
        
        # Test each query
        for idx, test_case in enumerate(queries, 1):
            logger.info(f"\n[{idx}/{len(queries)}] Testing: {test_case['query'][:60]}...")
            
            try:
                # Measure response time
                start_time = time.time()
                result = await supervisor.ainvoke(test_case['query'])
                end_time = time.time()
                
                response_time = end_time - start_time
                answer = result.get('answer', '')
                
                # Calculate accuracy score (keyword matching)
                accuracy_score = calculate_accuracy(
                    answer,
                    test_case.get('expected_keywords', [])
                )
                
                query_result = {
                    "query": test_case['query'],
                    "category": test_case['category'],
                    "difficulty": test_case['difficulty'],
                    "response_time_seconds": round(response_time, 2),
                    "answer_length_chars": len(answer),
                    "answer_preview": answer[:200] + "..." if len(answer) > 200 else answer,
                    "full_answer": answer,
                    "accuracy_score": accuracy_score,
                    "expected_keywords": test_case.get('expected_keywords', []),
                    "found_keywords": find_keywords(answer, test_case.get('expected_keywords', [])),
                    "success": True
                }
                
                logger.info(f"  ✓ Response time: {response_time:.2f}s")
                logger.info(f"  ✓ Accuracy score: {accuracy_score:.1%}")
                logger.info(f"  ✓ Answer length: {len(answer)} chars")
                
            except Exception as e:
                logger.error(f"  ✗ Error: {str(e)}")
                query_result = {
                    "query": test_case['query'],
                    "category": test_case['category'],
                    "difficulty": test_case['difficulty'],
                    "error": str(e),
                    "success": False
                }
            
            results['queries'].append(query_result)
            
            # Small delay between queries to avoid overwhelming the system
            await asyncio.sleep(2)
        
        # Calculate aggregate metrics
        successful_queries = [q for q in results['queries'] if q.get('success')]
        if successful_queries:
            results['aggregate_metrics'] = {
                "total_queries": len(queries),
                "successful_queries": len(successful_queries),
                "failed_queries": len(queries) - len(successful_queries),
                "avg_response_time": round(
                    sum(q['response_time_seconds'] for q in successful_queries) / len(successful_queries),
                    2
                ),
                "min_response_time": round(
                    min(q['response_time_seconds'] for q in successful_queries),
                    2
                ),
                "max_response_time": round(
                    max(q['response_time_seconds'] for q in successful_queries),
                    2
                ),
                "avg_accuracy_score": round(
                    sum(q['accuracy_score'] for q in successful_queries) / len(successful_queries),
                    3
                ),
                "avg_answer_length": round(
                    sum(q['answer_length_chars'] for q in successful_queries) / len(successful_queries),
                    0
                )
            }
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Configuration Summary: {config['name']}")
            logger.info(f"{'='*80}")
            logger.info(f"Successful: {len(successful_queries)}/{len(queries)}")
            logger.info(f"Avg Response Time: {results['aggregate_metrics']['avg_response_time']}s")
            logger.info(f"Avg Accuracy: {results['aggregate_metrics']['avg_accuracy_score']:.1%}")
            logger.info(f"{'='*80}")
        
        return results
        
    finally:
        # Restore original settings
        settings.supervisor_model = original_supervisor
        settings.planner_model = original_planner
        settings.synthesizer_model = original_synthesizer


def calculate_accuracy(answer: str, expected_keywords: List[str]) -> float:
    """
    Calculate accuracy score based on keyword presence.
    
    Args:
        answer: The generated answer
        expected_keywords: List of keywords that should appear
        
    Returns:
        Accuracy score between 0 and 1
    """
    if not expected_keywords:
        return 1.0
    
    answer_lower = answer.lower()
    found_count = sum(1 for keyword in expected_keywords if keyword.lower() in answer_lower)
    return found_count / len(expected_keywords)


def find_keywords(answer: str, keywords: List[str]) -> List[str]:
    """Find which keywords are present in the answer."""
    answer_lower = answer.lower()
    return [kw for kw in keywords if kw.lower() in answer_lower]


def generate_report(all_results: List[Dict], output_file: Path):
    """
    Generate a comprehensive report from all test results.
    
    Args:
        all_results: List of results from all configurations
        output_file: Path to save the report
    """
    logger.info(f"\n{'='*80}")
    logger.info("GENERATING COMPREHENSIVE REPORT")
    logger.info(f"{'='*80}")
    
    # Save raw JSON results
    json_file = output_file.with_suffix('.json')
    with open(json_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"✓ Raw results saved to: {json_file}")
    
    # Generate markdown report
    md_file = output_file.with_suffix('.md')
    with open(md_file, 'w') as f:
        f.write("# Model Benchmark Results\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Configurations Tested**: {len(all_results)}\n\n")
        
        # Summary table
        f.write("## Summary Comparison\n\n")
        f.write("| Configuration | Avg Time (s) | Avg Accuracy | Success Rate | Avg Length |\n")
        f.write("|--------------|-------------|--------------|--------------|------------|\n")
        
        for result in all_results:
            if 'aggregate_metrics' in result:
                metrics = result['aggregate_metrics']
                f.write(f"| {result['config_name']} | "
                       f"{metrics['avg_response_time']} | "
                       f"{metrics['avg_accuracy_score']:.1%} | "
                       f"{metrics['successful_queries']}/{metrics['total_queries']} | "
                       f"{int(metrics['avg_answer_length'])} |\n")
        
        # Detailed results per configuration
        f.write("\n## Detailed Results\n\n")
        for result in all_results:
            f.write(f"### {result['config_name']}\n\n")
            f.write(f"**Models**:\n")
            f.write(f"- Supervisor: `{result['models']['supervisor']}`\n")
            f.write(f"- Planner: `{result['models']['planner']}`\n")
            f.write(f"- Synthesizer: `{result['models']['synthesizer']}`\n\n")
            
            if 'aggregate_metrics' in result:
                metrics = result['aggregate_metrics']
                f.write(f"**Aggregate Metrics**:\n")
                f.write(f"- Average Response Time: {metrics['avg_response_time']}s\n")
                f.write(f"- Min/Max Response Time: {metrics['min_response_time']}s / {metrics['max_response_time']}s\n")
                f.write(f"- Average Accuracy: {metrics['avg_accuracy_score']:.1%}\n")
                f.write(f"- Success Rate: {metrics['successful_queries']}/{metrics['total_queries']}\n\n")
            
            # Query-by-query results
            f.write("**Query Results**:\n\n")
            f.write("| Query | Time (s) | Accuracy | Status |\n")
            f.write("|-------|----------|----------|--------|\n")
            
            for query_result in result['queries']:
                status = "✓" if query_result.get('success') else "✗"
                time_str = f"{query_result.get('response_time_seconds', 0):.1f}" if query_result.get('success') else "N/A"
                acc_str = f"{query_result.get('accuracy_score', 0):.1%}" if query_result.get('success') else "N/A"
                query_preview = query_result['query'][:50] + "..." if len(query_result['query']) > 50 else query_result['query']
                f.write(f"| {query_preview} | {time_str} | {acc_str} | {status} |\n")
            
            f.write("\n---\n\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        f.write("### Fastest Configuration\n")
        fastest = min(all_results, key=lambda x: x.get('aggregate_metrics', {}).get('avg_response_time', float('inf')))
        if 'aggregate_metrics' in fastest:
            f.write(f"**{fastest['config_name']}** - {fastest['aggregate_metrics']['avg_response_time']}s average\n\n")
        
        f.write("### Most Accurate Configuration\n")
        most_accurate = max(all_results, key=lambda x: x.get('aggregate_metrics', {}).get('avg_accuracy_score', 0))
        if 'aggregate_metrics' in most_accurate:
            f.write(f"**{most_accurate['config_name']}** - {most_accurate['aggregate_metrics']['avg_accuracy_score']:.1%} accuracy\n\n")
        
        f.write("### Best Balance (Speed × Accuracy)\n")
        # Calculate balance score (higher is better)
        for result in all_results:
            if 'aggregate_metrics' in result:
                metrics = result['aggregate_metrics']
                # Normalize: faster time = higher score, higher accuracy = higher score
                speed_score = 1 / metrics['avg_response_time'] if metrics['avg_response_time'] > 0 else 0
                accuracy_score = metrics['avg_accuracy_score']
                result['balance_score'] = speed_score * accuracy_score
        
        best_balance = max(all_results, key=lambda x: x.get('balance_score', 0))
        if 'aggregate_metrics' in best_balance:
            f.write(f"**{best_balance['config_name']}** - "
                   f"{best_balance['aggregate_metrics']['avg_response_time']}s, "
                   f"{best_balance['aggregate_metrics']['avg_accuracy_score']:.1%} accuracy\n\n")
    
    logger.info(f"✓ Markdown report saved to: {md_file}")
    logger.info(f"\n{'='*80}")
    logger.info("BENCHMARK COMPLETE!")
    logger.info(f"{'='*80}")
    logger.info(f"View results: cat {md_file}")


# ============================================================================
# Main Execution
# ============================================================================

async def main():
    """Main benchmark execution."""
    parser = argparse.ArgumentParser(description='Benchmark different model configurations')
    parser.add_argument(
        '--output',
        type=str,
        default='benchmark_results',
        help='Output file prefix (without extension)'
    )
    parser.add_argument(
        '--configs',
        type=str,
        nargs='+',
        help='Specific config names to test (default: all)'
    )
    parser.add_argument(
        '--queries',
        type=int,
        help='Number of queries to test (default: all 10)'
    )
    
    args = parser.parse_args()
    
    # Filter configurations if specified
    configs_to_test = MODELS_TO_TEST
    if args.configs:
        configs_to_test = [c for c in MODELS_TO_TEST if c['name'] in args.configs]
        if not configs_to_test:
            logger.error(f"No matching configurations found for: {args.configs}")
            return
    
    # Filter queries if specified
    queries_to_test = TEST_QUERIES[:args.queries] if args.queries else TEST_QUERIES
    
    logger.info(f"\n{'='*80}")
    logger.info("MODEL BENCHMARK STARTING")
    logger.info(f"{'='*80}")
    logger.info(f"Configurations to test: {len(configs_to_test)}")
    logger.info(f"Queries per configuration: {len(queries_to_test)}")
    logger.info(f"Total tests: {len(configs_to_test) * len(queries_to_test)}")
    logger.info(f"Output file: {args.output}")
    logger.info(f"{'='*80}\n")
    
    # Run benchmarks
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    all_results = []
    
    for config in configs_to_test:
        try:
            result = await test_model_configuration(config, queries_to_test, run_id)
            all_results.append(result)
        except Exception as e:
            logger.error(f"Failed to test configuration {config['name']}: {e}")
            continue
    
    # Generate report
    output_path = Path(args.output)
    generate_report(all_results, output_path)


if __name__ == "__main__":
    asyncio.run(main())
