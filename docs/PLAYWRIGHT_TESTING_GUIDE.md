# Playwright Testing Guide

## Overview
Playwright is a browser automation framework that we use for end-to-end UI testing. It allows us to interact with the application just like a real user would, verifying that the entire stack (backend + frontend) works correctly together.

## Why Playwright?

### Traditional Testing Limitations
- **Unit tests**: Test individual functions in isolation
- **Integration tests**: Test API endpoints but not the UI
- **Manual testing**: Time-consuming, error-prone, not repeatable

### Playwright Advantages
1. **Real Browser Testing**: Tests run in actual Chromium/Firefox/WebKit browsers
2. **Full Stack Validation**: Verifies backend → frontend → UI rendering pipeline
3. **Interactive Debugging**: Can see exactly what the browser sees
4. **Async/Await Support**: Natural handling of loading states and API calls
5. **Rich Assertions**: Can verify text content, component rendering, element states
6. **Screenshot/Video Capture**: Visual proof of test execution

## Our Use Case: Comparison Summary Bug

### The Problem
- Comparison summary section was rendering empty for multi-company queries
- Manual testing was time-consuming (start servers, navigate UI, check each section)
- Hard to verify all sections consistently

### How Playwright Helped

#### 1. **Automated UI Verification**
```javascript
// Navigate to app
await page.goto('http://localhost:3000');

// Type query and submit
await page.getByRole('textbox').fill('Compare Apple and Microsoft revenue');
await page.getByRole('textbox').press('Enter');

// Wait for processing
await page.waitForTimeout(50000);

// Verify comparison summary exists and has content
const summary = await page.getByText(/Microsoft's.*revenue growth/);
expect(summary).toBeTruthy();
```

#### 2. **Snapshot Inspection**
Playwright's `browser_snapshot` tool provides a structured view of the page:
```yaml
- generic [ref=e333]:
  - generic [ref=e334]:
    - img [ref=e335]
    - heading "Summary" [level=4] [ref=e337]
  - paragraph [ref=e338]: Microsoft's 16% revenue growth significantly 
    outpaced Apple's 2% due to strong cloud services expansion.
```

This revealed:
- ✅ Component was rendering (heading "Summary" present)
- ❌ Paragraph content was empty (the bug!)

#### 3. **Comprehensive Section Validation**
We verified ALL sections in one test run:
- ✅ Comparison table with data
- ✅ Comparison summary with text
- ✅ Business context for AAPL
- ✅ Business context for MSFT
- ✅ SEC filing links (clickable and working)
- ✅ Sources panel (10 sources with excerpts)

#### 4. **Regression Prevention**
After fixing the bug, we re-ran the same test to verify:
- Single-company query: NO comparison summary (correct)
- Multi-company query: Comparison summary WITH content (fixed!)

## How to Use Playwright in This Project

### Setup (Already Configured via MCP)
Playwright is available through the Model Context Protocol (MCP) server. No additional installation needed.

### Available Tools

#### 1. **browser_navigate**
Navigate to a URL:
```javascript
await page.goto('http://localhost:3000');
```

#### 2. **browser_snapshot**
Get structured page content (better than screenshot for verification):
```javascript
await page.snapshot();
// Returns YAML structure of all elements
```

#### 3. **browser_type**
Type into input fields:
```javascript
await page.getByRole('textbox').fill('What is Apple revenue?');
await page.getByRole('textbox').press('Enter');
```

#### 4. **browser_click**
Click buttons/links:
```javascript
await page.getByRole('button', { name: 'New Chat' }).click();
```

#### 5. **browser_wait_for**
Wait for content or time:
```javascript
await page.waitForTimeout(45000);  // Wait 45s for LLM response
await page.waitForText('Summary');  // Wait for specific text
```

#### 6. **browser_take_screenshot**
Capture visual proof:
```javascript
await page.screenshot({ path: 'comparison-result.png' });
```

### Testing Workflow

#### Step 1: Start Services
```bash
# Terminal 1: Backend
cd /Users/harpreet/financeagent
source venv/bin/activate
python -m app.main

# Terminal 2: Frontend
cd frontend
npm run dev
```

#### Step 2: Run Playwright Test
Use Cascade AI with Playwright MCP tools:
```
"Navigate to http://localhost:3000 and test the comparison query 
'Compare Apple and Microsoft revenue'. Verify all sections render correctly."
```

#### Step 3: Verify Results
Check the snapshot output for:
- Component types (Paragraph, Table, ComparisonSummary, BusinessContext)
- Content presence (not empty)
- Interactive elements (buttons, links)

### Example Test Cases

#### Test 1: Single-Company Query
```
Query: "What is Apple's revenue?"
Expected:
- ✅ Paragraph with revenue data
- ✅ Key findings
- ✅ Business context for AAPL only
- ✅ SEC filing link
- ❌ NO comparison summary
```

#### Test 2: Multi-Company Query
```
Query: "Compare Apple and Microsoft revenue"
Expected:
- ✅ Comparison table
- ✅ Comparison summary with text
- ✅ Business context for both companies
- ✅ SEC filing links for both
- ✅ Sources from both companies
```

#### Test 3: Link Verification
```
Action: Click on "AAPL 10-K (FY 2025)" link
Expected:
- ✅ Opens SEC.gov in new tab
- ✅ Correct filing URL
```

## Best Practices

### 1. **Use Semantic Selectors**
```javascript
// ✅ Good: Role-based selectors
await page.getByRole('button', { name: 'New Chat' });
await page.getByRole('textbox');

// ❌ Bad: CSS selectors (brittle)
await page.locator('.btn-primary');
```

### 2. **Wait for Dynamic Content**
```javascript
// LLM responses take time
await page.waitForTimeout(45000);  // 45s for synthesis

// Or wait for specific content
await page.waitForText('Processing Complete');
```

### 3. **Use Snapshots Over Screenshots**
```javascript
// ✅ Better: Structured data for assertions
const snapshot = await page.snapshot();
// Can verify text content, element hierarchy

// ❌ Less useful: Visual only
await page.screenshot();
```

### 4. **Test Both Success and Edge Cases**
- ✅ Valid queries (Apple, Microsoft)
- ✅ Invalid queries (unsupported companies)
- ✅ Malformed queries
- ✅ Empty results

### 5. **Document Test Results**
Create markdown reports with:
- Test date and environment
- Queries tested
- Expected vs actual results
- Screenshots/snapshots as evidence

## Debugging Failed Tests

### Issue: Element Not Found
```
Error: Element not found: button "View sources"
```

**Solutions:**
1. Check if element loaded: `await page.waitForTimeout(5000)`
2. Verify selector: Use `browser_snapshot` to see actual elements
3. Check if behind authentication or different state

### Issue: Timeout
```
Error: Timeout waiting for element
```

**Solutions:**
1. Increase wait time for LLM responses (45-60s)
2. Check backend logs for errors
3. Verify services are running

### Issue: Content Mismatch
```
Expected: "Summary with content"
Actual: Empty paragraph
```

**Solutions:**
1. Use `browser_snapshot` to inspect actual DOM
2. Check browser console for JS errors
3. Verify backend is sending correct data (check Network tab)

## Integration with CI/CD

### Future: Automated Testing
```yaml
# .github/workflows/test.yml
- name: Run Playwright Tests
  run: |
    docker-compose up -d
    npm run test:playwright
    docker-compose down
```

### Current: Manual Testing
1. Developer makes UI changes
2. Run Playwright test via Cascade AI
3. Verify all sections render correctly
4. Document results in test report
5. Commit changes if tests pass

## Real-World Impact

### Bug Discovery
- **Found**: Comparison summary rendering but empty
- **Root Cause**: Backend sent `props.summary`, frontend expected `props.text`
- **Fix Time**: 1 line change
- **Verification**: Playwright test confirmed fix in 2 minutes

### Time Savings
- **Manual Testing**: ~5 minutes per test (start app, navigate, check sections)
- **Playwright Testing**: ~2 minutes automated + instant verification
- **Regression Testing**: Free (just re-run the test)

### Confidence
- Before: "I think it works, let me check manually..."
- After: "Playwright verified all 6 sections render correctly ✅"

## Resources

- **Playwright Docs**: https://playwright.dev/
- **MCP Playwright Server**: https://github.com/executeautomation/mcp-playwright
- **Our Test Reports**: `/docs/PLAYWRIGHT_TEST_REPORT_FINAL.md`

## Next Steps

1. **Expand Test Coverage**
   - Test all supported companies (AAPL, MSFT, PFE, HOOD, AMZN)
   - Test error states (unsupported companies, network errors)
   - Test conversation history (multi-turn queries)

2. **Automate Test Runs**
   - Add to pre-commit hooks
   - Run on CI/CD pipeline
   - Generate test reports automatically

3. **Performance Testing**
   - Measure LLM response times
   - Track token usage
   - Monitor UI rendering performance

4. **Visual Regression Testing**
   - Capture screenshots of key states
   - Compare against baseline images
   - Detect unintended UI changes
