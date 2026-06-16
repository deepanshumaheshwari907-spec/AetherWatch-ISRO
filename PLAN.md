# AetherWatch-ISRO: Next-Step Plan

## Current status
- Streamlit app is running successfully on http://localhost:8501
- Baseline tests are passing: 4 passed in 1.03s

## Phase 1: Stabilize and verify
1. Keep the current virtual environment and add a small README/usage checklist.
2. Add a simple CI smoke check (pytest) for every change.
3. Pin dependency versions in requirements.txt for reproducibility.

## Phase 2: Improve core functionality
1. Validate the satellite-data fetch path and fallback behavior.
2. Test the AI/cloud-cluster logic on demo and runtime data.
3. Add error handling for missing or corrupt HDF5 files.

## Phase 3: Improve app experience
1. Add loading states, warnings, and better user feedback in the UI.
2. Show more actionable threat summaries (risk trend, region, confidence).
3. Improve map legends and metrics for disaster-response use.

## Phase 4: Prepare for real use
1. Add logging and model-performance tracking.
2. Optionally deploy the app to a cloud host.
3. Collect user feedback and refine the alert flow.

## Suggested first 3 tasks for this week
1. Add pytest to the project workflow and keep it as a required check.
2. Improve fallback handling for missing satellite files.
3. Add one more UI/analytics feature based on the threat summary.
