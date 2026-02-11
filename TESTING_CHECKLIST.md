# Quick Testing Checklist

**Print this and check off as you go!**

---

## ☑️ **Pre-Flight Checks**

- [ ] Docker Desktop running
- [ ] Terminal opened
- [ ] In project directory: `C:\Users\MohitTripathi(Quadra\Downloads\Manus\computer_use_codebase`
- [ ] `.env` file has API key
- [ ] Postman installed

---

## ☑️ **Phase 1: Start Services**

- [ ] Docker containers running (`docker ps`)
- [ ] Computer-use container healthy (port 8080)
- [ ] API server started (`python api_server.py`)
- [ ] See "AGENT INITIALIZED SUCCESSFULLY" in terminal
- [ ] See "S3 Skills Loaded: True"
- [ ] See "Uvicorn running on http://0.0.0.0:8003"

---

## ☑️ **Phase 2: Postman Setup**

- [ ] Postman opened
- [ ] Collection imported (`postman_collection.json`)
- [ ] See 18 test requests in 7 categories
- [ ] URL base is `http://localhost:8003`

---

## ☑️ **Phase 3: Run Tests**

### Test 1: Health Check (5 sec)
- [ ] Request sent
- [ ] Status 200
- [ ] Response: `"status": "healthy"`
- [ ] **PASS** ✅

### Test 2: System Status (5 sec)
- [ ] Request sent
- [ ] Status 200
- [ ] S3 skills enabled: true
- [ ] Total tools: 11
- [ ] Terminal shows status check logs
- [ ] **PASS** ✅

### Test 3: S3 Skill Discovery (20 sec)
- [ ] Request sent
- [ ] Success: true
- [ ] Response mentions "pdf_report_generator"
- [ ] Turns: 1-3
- [ ] Terminal shows multi-turn execution
- [ ] **PASS** ✅

### Test 4: Retail Data Query (60 sec)
- [ ] Request sent
- [ ] Success: true
- [ ] Turns: 5-10
- [ ] Tools used: retail tools
- [ ] Terminal shows tool calls
- [ ] Response has data analysis
- [ ] **PASS** ✅

### Test 5: Bash Commands (60 sec)
- [ ] Request sent
- [ ] Success: true
- [ ] Turns: 8-12
- [ ] Tools used: bash
- [ ] Terminal shows bash execution
- [ ] Files listed and analyzed
- [ ] **PASS** ✅

### Test 6: Complex Workflow (5 min)
- [ ] Request sent
- [ ] Success: true
- [ ] Turns: 20-25
- [ ] Multiple tools used
- [ ] Terminal shows complete pipeline
- [ ] Completes without critical errors
- [ ] **PASS** ✅

---

## ☑️ **Phase 4: Verification**

### Terminal Logs Show:
- [ ] Turn-by-turn execution (TURN 1/X, TURN 2/X, etc.)
- [ ] Tool calls with inputs
- [ ] Success confirmations (✅)
- [ ] Final responses
- [ ] Execution times

### Postman Responses Have:
- [ ] `success: true` field
- [ ] `response` with Claude's answer
- [ ] `turns` field
- [ ] `tools_used` array
- [ ] `s3_skills_loaded: ["pdf_report_generator"]`
- [ ] Reasonable execution times (<60s for simple tests)

---

## ☑️ **Final Score**

**Tests Passed:** ___ / 6

**Status:**
- [ ] 6/6 - Excellent! Everything working perfectly 🎉
- [ ] 5/6 - Very Good! Minor issues only ✅
- [ ] 4/6 - Good! Core functionality working ✓
- [ ] 3/6 - Partial! Needs investigation ⚠️
- [ ] <3/6 - Issues! Check logs ❌

---

## ☑️ **Key Findings**

### What Worked:
- _______________________________________
- _______________________________________
- _______________________________________

### What Failed:
- _______________________________________
- _______________________________________

### Recommendations:
- _______________________________________
- _______________________________________

---

## ☑️ **Cleanup**

- [ ] API server stopped (Ctrl+C)
- [ ] Docker containers stopped (optional)
- [ ] Test results saved
- [ ] Screenshots captured (optional)

---

**Date:** _______________
**Tester:** _______________
**Duration:** _______________

