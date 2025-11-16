#!/bin/bash

# Test script for comparison query with logging
# This script will help debug the business context issue

echo "========================================="
echo "Comparison Query Test Script"
echo "========================================="
echo ""

# Check if backend is running
echo "Checking if backend is running..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✓ Backend is running"
else
    echo "✗ Backend is not running"
    echo "Please start the backend first:"
    echo "  docker-compose up -d backend"
    echo "  or"
    echo "  python -m app.api.main"
    exit 1
fi

# Check if frontend is running
echo "Checking if frontend is running..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✓ Frontend is running"
else
    echo "✗ Frontend is not running"
    echo "Please start the frontend first:"
    echo "  cd frontend && npm run dev"
    exit 1
fi

echo ""
echo "========================================="
echo "INSTRUCTIONS"
echo "========================================="
echo ""
echo "This test will:"
echo "1. Submit the query: 'compare apple and microsoft revenue'"
echo "2. Wait for the response (about 30 seconds)"
echo "3. Capture screenshots"
echo "4. Generate a report"
echo ""
echo "IMPORTANT: Watch your backend terminal for these logs:"
echo ""
echo "  🔍 RAW LLM RESPONSE ANALYSIS"
echo "  📄 Answer sections count: X"
echo "  🏢 Companies in parsed_result: ['AAPL', 'MSFT']"
echo "    AAPL: business_context=✓ or ✗"
echo "    MSFT: business_context=✓ or ✗"
echo "  📊 Comparison data: True/False"
echo ""
echo "  📤 SENDING TO FRONTEND"
echo "  📦 Sections being sent: X"
echo "  📊 Metadata.companies: ['AAPL', 'MSFT']"
echo "    AAPL: business_context=✓ or ✗"
echo "    MSFT: business_context=✓ or ✗"
echo ""
echo "These logs will tell us exactly where the business_context is getting lost!"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

echo ""
echo "Starting test..."
echo ""

# Note: The actual Playwright test would be run here
# For now, this is a manual test guide
echo "Manual Test Steps:"
echo "1. Go to http://localhost:3000"
echo "2. Type: compare apple and microsoft revenue"
echo "3. Press Enter"
echo "4. Watch the backend logs for the debug output above"
echo "5. Check the UI for:"
echo "   - Paragraph section"
echo "   - Table section"
echo "   - Comparison summary section"
echo "   - Business context for AAPL (should appear)"
echo "   - Business context for MSFT (should appear)"
echo ""
echo "========================================="
echo "EXPECTED LOGS (if working correctly)"
echo "========================================="
echo ""
cat << 'EOF'
🔍 RAW LLM RESPONSE ANALYSIS
================================================================================
📄 Answer sections count: 3
  Section 0: type='paragraph', has_content=True
  Section 1: type='table', has_content=True
  Section 2: type='comparison_summary', has_content=True
🏢 Companies in parsed_result: ['AAPL', 'MSFT']
  AAPL: business_context=✓
    - growth_drivers: True
    - headwinds: True
    - explanation: True
  MSFT: business_context=✓
    - growth_drivers: True
    - headwinds: True
    - explanation: True
📊 Comparison data: True
  - summary: True
  - winner: MSFT
  - metric: revenue_growth
================================================================================

📤 SENDING TO FRONTEND
================================================================================
📦 Sections being sent: 3
  Section 0: component='Paragraph'
  Section 1: component='Table'
  Section 2: component='ComparisonSummary'
📊 Metadata.companies: ['AAPL', 'MSFT']
  AAPL: business_context=✓
  MSFT: business_context=✓
📈 Metadata.comparison: ✓
================================================================================
EOF

echo ""
echo "========================================="
echo "TROUBLESHOOTING"
echo "========================================="
echo ""
echo "If business_context=✗ in RAW LLM RESPONSE:"
echo "  → LLM is not generating business_context"
echo "  → Solution: Restart backend to reload prompt"
echo "  → Command: docker-compose restart backend"
echo ""
echo "If business_context=✓ in RAW but ✗ in SENDING TO FRONTEND:"
echo "  → Backend parsing issue in format_answer_for_ui()"
echo "  → Check the code in filing_qa_tool.py"
echo ""
echo "If business_context=✓ in SENDING but not visible in UI:"
echo "  → Frontend rendering issue in ChatMessage.jsx"
echo "  → Check browser console for errors"
echo ""
echo "========================================="
