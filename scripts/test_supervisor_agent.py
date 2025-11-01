#!/usr/bin/env python3
"""
Test script for the new SupervisorAgent.

This script validates the new Supervisor/Specialist architecture by invoking
the Supervisor agent with a sample query.
"""

import sys
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.agents.supervisor import SupervisorAgent

def run_supervisor_test():
    print("\n" + "#"*80)
    print("Testing Supervisor Agent Architecture")
    print("#"*80)

    # The query for the test
    query = "what are the risks investing in pfizer"

    print(f"QUERY: {query}")
    print("#"*80)

    # Instantiate the supervisor
    supervisor = SupervisorAgent()

    # Invoke the supervisor
    start_time = time.time()
    result = supervisor.invoke(query)
    total_time = time.time() - start_time

    # Print the results
    print("\n" + "="*80)
    print("SUPERVISOR AGENT TEST COMPLETE")
    print("="*80)
    print(f"Total Time: {total_time:.1f}s")
    print("\n📝 FINAL ANSWER:")
    print(result['answer'])
    print("="*80 + "\n")

if __name__ == "__main__":
    run_supervisor_test()
