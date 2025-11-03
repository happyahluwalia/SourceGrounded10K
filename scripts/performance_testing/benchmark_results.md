# Model Benchmark Results

**Date**: 2025-11-03 08:17:52

**Total Configurations Tested**: 6

## Summary Comparison

| Configuration | Avg Time (s) | Avg Accuracy | Success Rate | Avg Length |
|--------------|-------------|--------------|--------------|------------|
| Current (llama3.1:8b) | 30.23 | 72.5% | 10/10 | 1201 |
| Qwen2.5:72b (All) | 692.92 | 50.8% | 10/10 | 1024 |
| Qwen2.5:32b (All) | 197.92 | 51.7% | 10/10 | 766 |
| Specialized (Qwen72b + Mixtral + Llama8b) | 210.49 | 34.2% | 10/10 | 735 |
| Fast (Qwen32b + Llama8b) | 105.51 | 53.3% | 10/10 | 883 |

## Detailed Results

### Current (llama3.1:8b)

**Models**:
- Supervisor: `llama3.1`
- Planner: `llama3.1`
- Synthesizer: `llama3.1`

**Aggregate Metrics**:
- Average Response Time: 30.23s
- Min/Max Response Time: 16.87s / 46.51s
- Average Accuracy: 72.5%
- Success Rate: 10/10

**Query Results**:

| Query | Time (s) | Accuracy | Status |
|-------|----------|----------|--------|
| Who is the CFO of Apple? | 22.8 | 66.7% | ✓ |
| What were Apple's total revenues last fiscal year? | 40.0 | 66.7% | ✓ |
| What are the main risk factors for investing in Am... | 28.6 | 100.0% | ✓ |
| How much did Microsoft spend on research and devel... | 16.9 | 50.0% | ✓ |
| What is Microsoft's business strategy for cloud co... | 28.4 | 75.0% | ✓ |
| Compare Apple's gross margin to Microsoft's gross ... | 46.5 | 100.0% | ✓ |
| What were the key highlights from Pfizer's latest ... | 33.4 | 25.0% | ✓ |
| Who are the members of Apple's board of directors? | 26.3 | 66.7% | ✓ |
| What is Amazon's policy on stock-based compensatio... | 33.9 | 100.0% | ✓ |
| Explain Amazon's revenue recognition policy for AW... | 25.4 | 75.0% | ✓ |

---

### Qwen2.5:72b (All)

**Models**:
- Supervisor: `qwen2.5:72b`
- Planner: `qwen2.5:72b`
- Synthesizer: `qwen2.5:72b`

**Aggregate Metrics**:
- Average Response Time: 692.92s
- Min/Max Response Time: 399.26s / 1176.01s
- Average Accuracy: 50.8%
- Success Rate: 10/10

**Query Results**:

| Query | Time (s) | Accuracy | Status |
|-------|----------|----------|--------|
| Who is the CFO of Apple? | 424.8 | 33.3% | ✓ |
| What were Apple's total revenues last fiscal year? | 408.1 | 33.3% | ✓ |
| What are the main risk factors for investing in Am... | 717.3 | 25.0% | ✓ |
| How much did Microsoft spend on research and devel... | 399.3 | 50.0% | ✓ |
| What is Microsoft's business strategy for cloud co... | 633.3 | 50.0% | ✓ |
| Compare Apple's gross margin to Microsoft's gross ... | 765.4 | 100.0% | ✓ |
| What were the key highlights from Pfizer's latest ... | 1108.8 | 0.0% | ✓ |
| Who are the members of Apple's board of directors? | 601.3 | 66.7% | ✓ |
| What is Amazon's policy on stock-based compensatio... | 1176.0 | 75.0% | ✓ |
| Explain Amazon's revenue recognition policy for AW... | 695.0 | 75.0% | ✓ |

---

### Qwen2.5:32b (All)

**Models**:
- Supervisor: `qwen2.5:32b`
- Planner: `qwen2.5:32b`
- Synthesizer: `qwen2.5:32b`

**Aggregate Metrics**:
- Average Response Time: 197.92s
- Min/Max Response Time: 68.99s / 319.47s
- Average Accuracy: 51.7%
- Success Rate: 10/10

**Query Results**:

| Query | Time (s) | Accuracy | Status |
|-------|----------|----------|--------|
| Who is the CFO of Apple? | 141.3 | 33.3% | ✓ |
| What were Apple's total revenues last fiscal year? | 172.0 | 33.3% | ✓ |
| What are the main risk factors for investing in Am... | 193.4 | 50.0% | ✓ |
| How much did Microsoft spend on research and devel... | 127.6 | 50.0% | ✓ |
| What is Microsoft's business strategy for cloud co... | 210.7 | 50.0% | ✓ |
| Compare Apple's gross margin to Microsoft's gross ... | 239.9 | 100.0% | ✓ |
| What were the key highlights from Pfizer's latest ... | 319.5 | 25.0% | ✓ |
| Who are the members of Apple's board of directors? | 69.0 | 0.0% | ✓ |
| What is Amazon's policy on stock-based compensatio... | 296.8 | 100.0% | ✓ |
| Explain Amazon's revenue recognition policy for AW... | 209.1 | 75.0% | ✓ |

---

### Mixtral:8x7b (All)

**Models**:
- Supervisor: `mixtral:8x7b`
- Planner: `mixtral:8x7b`
- Synthesizer: `mixtral:8x7b`

**Query Results**:

| Query | Time (s) | Accuracy | Status |
|-------|----------|----------|--------|
| Who is the CFO of Apple? | N/A | N/A | ✗ |
| What were Apple's total revenues last fiscal year? | N/A | N/A | ✗ |
| What are the main risk factors for investing in Am... | N/A | N/A | ✗ |
| How much did Microsoft spend on research and devel... | N/A | N/A | ✗ |
| What is Microsoft's business strategy for cloud co... | N/A | N/A | ✗ |
| Compare Apple's gross margin to Microsoft's gross ... | N/A | N/A | ✗ |
| What were the key highlights from Pfizer's latest ... | N/A | N/A | ✗ |
| Who are the members of Apple's board of directors? | N/A | N/A | ✗ |
| What is Amazon's policy on stock-based compensatio... | N/A | N/A | ✗ |
| Explain Amazon's revenue recognition policy for AW... | N/A | N/A | ✗ |

---

### Specialized (Qwen72b + Mixtral + Llama8b)

**Models**:
- Supervisor: `qwen2.5:72b`
- Planner: `mixtral:8x7b`
- Synthesizer: `llama3.1`

**Aggregate Metrics**:
- Average Response Time: 210.49s
- Min/Max Response Time: 172.32s / 275.2s
- Average Accuracy: 34.2%
- Success Rate: 10/10

**Query Results**:

| Query | Time (s) | Accuracy | Status |
|-------|----------|----------|--------|
| Who is the CFO of Apple? | 172.3 | 0.0% | ✓ |
| What were Apple's total revenues last fiscal year? | 234.8 | 66.7% | ✓ |
| What are the main risk factors for investing in Am... | 202.4 | 25.0% | ✓ |
| How much did Microsoft spend on research and devel... | 194.9 | 75.0% | ✓ |
| What is Microsoft's business strategy for cloud co... | 172.4 | 0.0% | ✓ |
| Compare Apple's gross margin to Microsoft's gross ... | 267.9 | 100.0% | ✓ |
| What were the key highlights from Pfizer's latest ... | 216.6 | 0.0% | ✓ |
| Who are the members of Apple's board of directors? | 275.2 | 0.0% | ✓ |
| What is Amazon's policy on stock-based compensatio... | 177.3 | 0.0% | ✓ |
| Explain Amazon's revenue recognition policy for AW... | 191.1 | 75.0% | ✓ |

---

### Fast (Qwen32b + Llama8b)

**Models**:
- Supervisor: `qwen2.5:32b`
- Planner: `qwen2.5:32b`
- Synthesizer: `llama3.1`

**Aggregate Metrics**:
- Average Response Time: 105.51s
- Min/Max Response Time: 76.13s / 139.56s
- Average Accuracy: 53.3%
- Success Rate: 10/10

**Query Results**:

| Query | Time (s) | Accuracy | Status |
|-------|----------|----------|--------|
| Who is the CFO of Apple? | 113.5 | 66.7% | ✓ |
| What were Apple's total revenues last fiscal year? | 106.1 | 66.7% | ✓ |
| What are the main risk factors for investing in Am... | 104.0 | 25.0% | ✓ |
| How much did Microsoft spend on research and devel... | 100.2 | 75.0% | ✓ |
| What is Microsoft's business strategy for cloud co... | 101.3 | 50.0% | ✓ |
| Compare Apple's gross margin to Microsoft's gross ... | 139.6 | 100.0% | ✓ |
| What were the key highlights from Pfizer's latest ... | 117.9 | 25.0% | ✓ |
| Who are the members of Apple's board of directors? | 76.1 | 0.0% | ✓ |
| What is Amazon's policy on stock-based compensatio... | 96.7 | 75.0% | ✓ |
| Explain Amazon's revenue recognition policy for AW... | 99.7 | 50.0% | ✓ |

---

## Recommendations

### Fastest Configuration
**Current (llama3.1:8b)** - 30.23s average

### Most Accurate Configuration
**Current (llama3.1:8b)** - 72.5% accuracy

### Best Balance (Speed × Accuracy)
**Current (llama3.1:8b)** - 30.23s, 72.5% accuracy