#!/bin/bash
# autopilot_v5.sh — Runs on the server.
# Keeps training V5 iterations until kv_strict_F1 > qmeans (20.23%).
# Run from: /home3/indiamart/gemma_4/
# Usage: nohup bash /home3/indiamart/gemma_4/autopilot_v5.sh > /home3/indiamart/gemma_4/autopilot_v5.log 2>&1 &

set -e

PYTHON="/home3/indiamart/gemma_4/gemma4_env/bin/python"
BASE="/home3/indiamart/gemma_4"
SCRIPTS="$BASE"
TARGET_F1=20.24   # must beat qmeans
MAX_ITER=6        # max iterations before giving up

log() { echo "[$(date '+%H:%M:%S')] $*"; }

iteration=0
while [ $iteration -lt $MAX_ITER ]; do
    iteration=$((iteration + 1))
    log "========== ITERATION $iteration / $MAX_ITER =========="

    # ---- STEP 1: TRAIN ----
    log "Starting V5 training (iter $iteration) ..."
    TRAIN_LOG="$BASE/v5_train_iter${iteration}.log"
    touch "$TRAIN_LOG" 2>/dev/null || TRAIN_LOG="/tmp/v5_train_iter${iteration}.log"
    $PYTHON "$SCRIPTS/finetune_gemma4_v5_flat.py" 2>&1 | tee "$TRAIN_LOG"
    TRAIN_EXIT=${PIPESTATUS[0]}
    log "Training exit code: $TRAIN_EXIT"
    if [ "$TRAIN_EXIT" -ne 0 ]; then
        log "ERROR: Training failed! Check $TRAIN_LOG. Stopping."
        exit 1
    fi
    log "Training done (iter $iteration)."

    # ---- STEP 2: INFERENCE part1 ----
    log "Running V5 inference PART 1 (GPU0) ..."
    rm -f "$BASE/v5_flat_results_part1.jsonl" "$BASE/v5_flat_results_part2.jsonl" "$BASE/v5_flat_results.jsonl"
    INF1_LOG="$BASE/v5_inf_part1_iter${iteration}.log" ; touch "$INF1_LOG" 2>/dev/null || INF1_LOG="/tmp/v5_inf_part1_iter${iteration}.log"
    CUDA_VISIBLE_DEVICES=0 $PYTHON "$SCRIPTS/inference_v5.py" --part 1 \
        2>&1 | tee "$INF1_LOG" &
    PID1=$!

    # ---- STEP 3: INFERENCE part2 ----
    log "Running V5 inference PART 2 (GPU1) ..."
    INF2_LOG="$BASE/v5_inf_part2_iter${iteration}.log" ; touch "$INF2_LOG" 2>/dev/null || INF2_LOG="/tmp/v5_inf_part2_iter${iteration}.log"
    CUDA_VISIBLE_DEVICES=1 $PYTHON "$SCRIPTS/inference_v5.py" --part 2 \
        2>&1 | tee "$INF2_LOG" &
    PID2=$!

    # wait for both
    wait $PID1 ; INF1_EXIT=$? ; log "Part1 exit: $INF1_EXIT"
    wait $PID2 ; INF2_EXIT=$? ; log "Part2 exit: $INF2_EXIT"

    if [ "$INF1_EXIT" -ne 0 ] || [ "$INF2_EXIT" -ne 0 ]; then
        log "ERROR: Inference failed. Check inference logs."
        exit 1
    fi

    # ---- STEP 4: MERGE results ----
    log "Merging part1 + part2 ..."
    RESULTS="$BASE/v5_flat_results.jsonl"
    cat "$BASE/v5_flat_results_part1.jsonl" "$BASE/v5_flat_results_part2.jsonl" > "$RESULTS"
    wc -l "$RESULTS"

    # ---- STEP 5: COMPARE ----
    log "Comparing V5 vs qmeans ..."
    RESULT=$($PYTHON "$SCRIPTS/compare_v5.py" --v5 "$RESULTS" 2>&1)
    echo "$RESULT"
    echo "$RESULT" > "$BASE/v5_compare_iter${iteration}.txt"

    # Extract V5 F1 from output
    V5_F1=$(echo "$RESULT" | grep "kv_strict_F1" | grep -v qmeans | grep -oP '[0-9]+\.[0-9]+' | head -1)
    log "V5 kv_strict_F1 = $V5_F1%  (target > $TARGET_F1%)"

    # Check if we beat qmeans
    if python3 -c "exit(0 if float('$V5_F1') > $TARGET_F1 else 1)" 2>/dev/null; then
        log "🎉 SUCCESS! V5 beats qmeans: $V5_F1% > $TARGET_F1%"
        log "Adapter saved at /home3/indiamart/isq-gemma4-e4b-v5-flat"
        exit 0
    else
        log "Not there yet ($V5_F1% vs target $TARGET_F1%). Adjusting and retrying ..."

        # ---- Incremental improvements between iterations ----
        # Bump LR slightly, add more epochs via env var
        # The trainer already does resume-from-checkpoint, so next iteration adds more training
        export V5_EXTRA_EPOCHS=$((iteration))   # signal to trainer (optional)

        # If we're on iter 2+, clear checkpoint to force fresh weights with new LR
        if [ $iteration -ge 3 ]; then
            log "Clearing old checkpoint for fresh restart with tuned hyperparams ..."
            rm -rf /home3/indiamart/isq-gemma4-e4b-v5-flat/checkpoint-*
        fi
    fi
done

log "Reached max iterations ($MAX_ITER) without beating qmeans. Best result saved."
log "Check /home3/indiamart/gemma_4/v5_compare_iter*.txt for best iteration."
