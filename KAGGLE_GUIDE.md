# NeuroHealth — Complete Kaggle GPU Run Guide

> **What this guide is:** A step-by-step notebook walkthrough to run all evaluations,
> generate charts, fill in human scores, and prepare your final GSoC submission — all on
> a free Kaggle GPU. No prior Kaggle experience needed.
>
> **Time needed:** ~5–6 hours total GPU time (can be split across two sessions).

---

## Table of Contents

1. [Before You Start — Checklist](#1-before-you-start--checklist)
2. [Kaggle Notebook Setup](#2-kaggle-notebook-setup)
3. [Session 1 — Install, Build, Test (~30 min)](#3-session-1--install-build-test)
4. [Session 1 — Run Evaluations (~2.5–3 hrs)](#4-session-1--run-evaluations)
5. [Session 2 — Ablation Study (~2.5–3.5 hrs)](#5-session-2--ablation-study)
6. [Generate Charts](#6-generate-charts)
7. [Fill In Human Evaluation Scores](#7-fill-in-human-evaluation-scores)
8. [Download Your Results](#8-download-your-results)
9. [Back on Your Local Machine — Final Steps](#9-back-on-your-local-machine--final-steps)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Before You Start — Checklist

Do all of these **before opening Kaggle**:

### 1a. Get Llama 3.1 Access on HuggingFace

1. Go to: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
2. Click **"Request access"** (takes ~10 minutes to get approved)
3. Make sure your HuggingFace token has this model in its approved list

### 1b. Get your HuggingFace Token

1. Go to: https://huggingface.co/settings/tokens
2. Click **"New token"** → Name it anything (e.g., `kaggle-neurohealth`) → Role: **Read**
3. Copy the token — it looks like `hf_xxxxxxxxxxxxxxxxxx`
4. Keep it somewhere safe, you'll paste it into Kaggle in Step 2

### 1c. Push your local code to GitHub

On your local machine run this:

```bash
# From your project folder
git add -A
git commit -m "final code with all bug fixes and evaluation scripts"
git push origin main
```

This makes your latest code available to Kaggle in Step 3.

---

## 2. Kaggle Notebook Setup

### 2a. Create a New Notebook

1. Go to https://www.kaggle.com
2. Click **"Create"** → **"New Notebook"** (top left)
3. You'll get a blank notebook — that's your workspace

### 2b. Enable GPU

On the **right-side panel**:

1. Click **"Session options"** (or gear icon)
2. Under **"Accelerator"** → select **"GPU T4 x2"**
   - If T4 x2 is greyed out, pick **"GPU P100"** — both work fine
3. Under **"Internet"** → make sure it says **"Internet On"**
   - If it's off, you can't download the model — this is required
4. Under **"Persistence"** → set to **"Files only"**

### 2c. Add Your HuggingFace Token as a Secret

> **Why:** Storing the token as a secret is safer than pasting it in a cell — it won't show in
> your notebook's output.

1. In the **top menu bar** of the notebook → click **"Add-ons"**
2. In the dropdown → click **"Secrets"**
3. A panel opens on the right → click **"Add a new secret"**
4. **Label:** `HUGGINGFACE_TOKEN`
5. **Value:** paste your `hf_xxxxxxxxx` token
6. Click **"Add"**
7. Make sure the toggle next to `HUGGINGFACE_TOKEN` is **ON** (green/enabled)

---

## 3. Session 1 — Install, Build, Test

Copy each code block below into a new notebook cell and run them **one at a time**
(Shift + Enter to run a cell).

---

### Cell 1 — Clone Your Repo

```python
# Download your project code from GitHub onto the Kaggle machine
import subprocess

result = subprocess.run(
    ["git", "clone", "https://github.com/YOUR_USERNAME/NeuroHealth.git"],
    capture_output=True, text=True
)
print(result.stdout)
print(result.stderr)

# Move into the project folder — all future cells run from here
import os
os.chdir("/kaggle/working/NeuroHealth")
print("Current directory:", os.getcwd())
```

> **Replace `YOUR_USERNAME`** with your actual GitHub username.
> After running, you should see `Cloning into 'NeuroHealth'...` and no errors.

---

### Cell 2 — Install Dependencies

```python
# Install only what Kaggle doesn't already have.
# Using kaggle_requirements.txt avoids the version-conflict warnings
# you get when trying to re-install pandas/requests/torch (Kaggle has those pinned).

!pip install -q -r kaggle_requirements.txt

# Download the English language model for spaCy (used in symptom extraction)
!python -m spacy download en_core_web_sm -q

# Download NLTK data (used for text processing)
import nltk
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

print("✓ All dependencies installed!")
```

> **What the warnings mean:** If you see lines like
> `ERROR: google-colab requires pandas==2.2.2` — that's a Kaggle internal conflict, not
> caused by our code. You can safely **ignore** all such warnings. The installation still works.

---

### Cell 3 — Set Up Environment Variables

> **IMPORTANT:** If you already ran Cell 5 (warmup) once and got a 401/403 error,
> you MUST click **"Run" → "Restart session"** (top menu) before re-running this cell.
> Otherwise Python keeps the old empty token in memory and the fix won't take effect.

```python
import os

# Load your HuggingFace token from the Kaggle Secrets panel
try:
    from kaggle_secrets import UserSecretsClient
    secrets = UserSecretsClient()
    hf_token = secrets.get_secret("HUGGINGFACE_TOKEN")
    print("✓ HuggingFace token loaded from Kaggle Secrets")
except Exception as e:
    # Fallback: paste your Classic token directly (only in a PRIVATE notebook)
    hf_token = "hf_PASTE_YOUR_TOKEN_HERE"
    print("⚠ Using hardcoded token — make sure this notebook is PRIVATE")

# Set BOTH env var names — our code uses HUGGINGFACE_TOKEN,
# but the transformers library internally checks HF_TOKEN too.
os.environ["HUGGINGFACE_TOKEN"] = hf_token
os.environ["HF_TOKEN"]          = hf_token   # ← transformers reads this one
os.environ["MODEL_NAME"]        = "meta-llama/Llama-3.1-8B-Instruct"
os.environ["MAX_NEW_TOKENS"]    = "1024"
os.environ["TEMPERATURE"]       = "0.3"
os.environ["EMBEDDING_MODEL"]   = "all-MiniLM-L6-v2"
os.environ["VECTOR_DB_PATH"]    = "./data/vector_db"

# Verify the token actually works with HuggingFace right now
from huggingface_hub import login, whoami
try:
    login(token=hf_token, add_to_git_credential=False)
    user_info = whoami()
    print(f"\n✓ Logged in to HuggingFace as: {user_info['name']}")
    print(f"  Token starts with: {hf_token[:10]}...")

    # Check Llama access
    from huggingface_hub import model_info
    try:
        model_info("meta-llama/Llama-3.1-8B-Instruct", token=hf_token)
        print("✓ Llama 3.1 access confirmed — you're ready to load the model!")
    except Exception:
        print("✗ No Llama 3.1 access yet.")
        print("  → Go to: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct")
        print("  → Click 'Request access', fill the form, wait for approval email")
        print("  → Then re-run this cell")
except Exception as e:
    print(f"\n✗ Login failed: {e}")
    print("  Check your token at: https://huggingface.co/settings/tokens")
    print("  Make sure it is a CLASSIC token (not Fine-grained)")
```

---

### Cell 4 — Build the Knowledge Base

> **What this does:** Downloads medical data from MedlinePlus and other sources,
> cleans it, splits it into chunks, and builds a searchable vector database.
> This is what the AI searches when you ask a health question.
>
> **Time:** ~10–15 minutes. Only needs to run once.

```python
import os

vector_db_exists = os.path.exists("data/vector_db/chroma.sqlite3")

if vector_db_exists:
    print("✓ Vector database already exists — skipping build.")
    print("  Delete data/vector_db/ to force a rebuild.")
else:
    print("Building knowledge base from scratch...")
    print("This runs 5 pipeline steps. Each step prints its progress.\n")

    print("Step 1/5: Collecting medical data...")
    !python src/data_pipeline/collector.py

    print("\nStep 2/5: Cleaning data...")
    !python src/data_pipeline/cleaner.py

    print("\nStep 3/5: Splitting into chunks...")
    !python src/data_pipeline/chunker.py

    print("\nStep 4/5: Creating text embeddings...")
    !python src/knowledge_base/embedder.py

    print("\nStep 5/5: Building vector database...")
    !python src/knowledge_base/vector_store.py

    print("\n✓ Knowledge base built successfully!")
```

---

### Cell 4.5 — Download the Llama Model to Local Disk

> **Why this step exists:** Kaggle's version of `transformers` sometimes fails to resolve
> sharded model weight files directly from the HuggingFace Hub, giving the error:
> `does not appear to have a file named pytorch_model.bin or model.safetensors`
>
> The fix: download ALL model files to a local folder first using `snapshot_download`,
> then load from that folder. Loading from a local path always works because there
> is no hub file-resolution step.
>
> **Time:** ~10–15 minutes (downloads ~16GB of model weights).
> **Only needs to run once** — the files stay in `/kaggle/working/llama_model/`.

```python
import os
from huggingface_hub import snapshot_download

LOCAL_MODEL_PATH = "/kaggle/working/llama_model"

# Check if already downloaded
if os.path.isdir(LOCAL_MODEL_PATH) and os.listdir(LOCAL_MODEL_PATH):
    print(f"✓ Model already downloaded at {LOCAL_MODEL_PATH}")
    print(f"  Files: {os.listdir(LOCAL_MODEL_PATH)[:5]}...")
else:
    print("Downloading Llama 3.1-8B model files (~16GB)...")
    print("This takes about 10–15 minutes. You will see a progress bar.")
    print("Do NOT close or refresh the browser while downloading.\n")

    snapshot_download(
        repo_id="meta-llama/Llama-3.1-8B-Instruct",
        token=os.environ["HUGGINGFACE_TOKEN"],
        local_dir=LOCAL_MODEL_PATH,
        ignore_patterns=["original/*"],   # skip the non-safetensors format to save space
    )
    print(f"\n✓ Download complete!")

# Tell the pipeline to load from local path (not from the hub)
os.environ["LOCAL_MODEL_DIR"] = LOCAL_MODEL_PATH
print(f"\n✓ LOCAL_MODEL_DIR set to: {LOCAL_MODEL_PATH}")

# Verify the key files are there
import glob
shard_files = glob.glob(f"{LOCAL_MODEL_PATH}/model-*.safetensors")
print(f"  Model shards found: {len(shard_files)} files")
if len(shard_files) == 0:
    print("  ✗ No shard files found — download may have failed. Re-run this cell.")
else:
    print(f"  ✓ Ready to load!")
```

---

### Cell 5 — Warm Up the Pipeline (First Message Test)

> **What this does:** Loads the Llama 3.1 model into GPU memory and sends one test
> message to confirm everything works end-to-end. The first run is slow (~3–5 min)
> because the model (~16GB) is being loaded into GPU. Every run after is fast.

```python
# Add project root to Python path so imports work
import sys, os
sys.path.insert(0, "/kaggle/working/NeuroHealth")

# Safety check: make sure token is in environment before import
# (if you got a 401 error before, restart the session and re-run Cell 3 first)
if not os.environ.get("HUGGINGFACE_TOKEN"):
    raise RuntimeError("Token not set! Run Cell 3 first, then re-run this cell.")
print(f"✓ Token present: {os.environ['HUGGINGFACE_TOKEN'][:10]}...")

from src.pipeline import process_message

print("\nLoading model... (this takes 3–5 minutes on first run)")
print("You'll see 'Loading checkpoint shards' — that's normal.\n")

result = process_message("I have a headache and feel tired", session_id="warmup_001")

print("\n" + "="*60)
print("PIPELINE TEST RESULT")
print("="*60)
# result['response'] is a dict with 'text', 'urgency_level', etc.
resp = result['response']
print(f"Response preview: {resp['text'][:300]}...")
print(f"Urgency level:    {resp['urgency_level']}")
print(f"Intent detected:  {result['debug']['intent']['intent']}")
print("="*60)
print("\n✓ Pipeline is working! Ready to run evaluations.")
```

> **Expected output:** You should see a health response about headaches, with urgency
> level `ROUTINE` or `SELF_CARE`. If you see an error about the token, go back to Cell 3
> and check your HuggingFace token.

---

## 4. Session 1 — Run Evaluations

Run these cells one after another. Each one saves a JSON result file that you'll
use later to generate charts and update the README.

> **IMPORTANT:** All evaluation cells run **inside the notebook** (not as subprocesses
> with `!python`). This way the model stays loaded in GPU memory from Cell 5 and each
> test case runs fast (~30–60 seconds instead of 5+ minutes).

---

### Cell 6 — Benchmark Evaluation

> **What it tests:** 37 health questions covering emergencies, routine symptoms, and
> medication questions. Measures emergency recall, urgency accuracy, and intent accuracy.
>
> **Time:** ~30–40 minutes on T4 GPU (model already loaded)

```python
import sys, json, pathlib
sys.path.insert(0, "/kaggle/working/NeuroHealth")

# ── Auto-fix pipeline.py if it returns string instead of dict ──
pp = pathlib.Path("/kaggle/working/NeuroHealth/src/pipeline.py")
code = pp.read_text()
if 'formatted_response["text"]' in code:
    code = code.replace('"response": formatted_response["text"],', '"response": formatted_response,')
    pp.write_text(code)
    for k in list(sys.modules.keys()):
        if any(x in k for x in ["pipeline", "formatter", "src"]):
            del sys.modules[k]
    print("✓ Fixed pipeline.py (response → dict)")

# ── Auto-fix safety_guardrails.py if str_issues is missing ──
sp = pathlib.Path("/kaggle/working/NeuroHealth/src/modules/safety_guardrails.py")
sc = sp.read_text()
if "str_issues" not in sc and 'i.startswith("DANGEROUS_PATTERN:")' in sc:
    sc = sc.replace(
        '    dangerous_issues = [i for i in issues if i.startswith("DANGEROUS_PATTERN:")]',
        ('    str_issues = [\n'
         '        i if isinstance(i, str) else i.get("description", str(i))\n'
         '        for i in issues\n'
         '    ]\n'
         '    dangerous_issues = [i for i in str_issues if i.startswith("DANGEROUS_PATTERN:")]'))
    for kw in ["MISSING_EMERGENCY_REDIRECT", "MISSING_CRISIS_RESOURCES",
                "MISSING_POISON_CONTROL", "MISSING_DISCLAIMER_LANGUAGE"]:
        sc = sc.replace(f'if "{kw}" in issues:', f'if "{kw}" in str_issues:')
    sp.write_text(sc)
    for k in list(sys.modules.keys()):
        if "safety" in k:
            del sys.modules[k]
    print("✓ Fixed safety_guardrails.py (str_issues)")

from src.pipeline import process_message
from evaluation.benchmarks import run_benchmark

print("="*60)
print("RUNNING BENCHMARK EVALUATION (37 test cases)")
print("Model already loaded — reusing from Cell 5")
print("="*60 + "\n")

benchmark_results = run_benchmark(process_message)

with open("evaluation/benchmark_results.json", "w") as f:
    json.dump(benchmark_results, f, indent=2, default=str)

print(f"\n✓ Saved to evaluation/benchmark_results.json")
```

---

### Cell 7 — Safety Tests

> **What it tests:** 26 adversarial prompts — jailbreak attempts, mental health crises,
> overdose questions, misinformation, pediatric edge cases.
>
> **Time:** ~20–30 minutes on T4 GPU

```python
import sys, json
sys.path.insert(0, "/kaggle/working/NeuroHealth")

from src.pipeline import process_message
from evaluation.safety_tests import run_safety_tests

print("="*60)
print("RUNNING SAFETY & ADVERSARIAL TESTS (26 cases)")
print("="*60 + "\n")

safety_results = run_safety_tests(process_message)

with open("evaluation/safety_results.json", "w") as f:
    json.dump(safety_results, f, indent=2, default=str)

passed = sum(1 for r in safety_results["results"] if r["passed"])
total = len(safety_results["results"])
print(f"\n{'='*60}")
print(f"SAFETY RESULTS SUMMARY")
print(f"{'='*60}")
print(f"  Pass Rate:         {passed}/{total} ({passed/total*100:.1f}%)")
print(f"  Critical Failures: {len(safety_results['critical_failures'])} (MUST be 0)")
print(f"  High Failures:     {len(safety_results['high_failures'])}")
if safety_results["high_failures"]:
    print(f"  Failed cases:      {', '.join(safety_results['high_failures'])}")
print("="*60)
print("\n✓ Saved to evaluation/safety_results.json")
```

---

### Cell 8 — Equity Tests

> **What it tests:** Whether the system gives the same urgency level for the same symptom
> regardless of the patient's age, gender, race, literacy level, or insurance status.
>
> **Time:** ~20–30 minutes on T4 GPU

```python
import sys, json
sys.path.insert(0, "/kaggle/working/NeuroHealth")

from src.pipeline import process_message
from evaluation.equity_tests import run_equity_tests

print("="*60)
print("RUNNING EQUITY / FAIRNESS TESTS (13 pairs)")
print("="*60 + "\n")

equity_results = run_equity_tests(process_message)

with open("evaluation/equity_results.json", "w") as f:
    json.dump(equity_results, f, indent=2, default=str)

print(f"\n{'='*60}")
print(f"EQUITY RESULTS SUMMARY")
print(f"{'='*60}")
print(f"  Consistency Rate:   {equity_results['consistency_rate']*100:.1f}%")
if equity_results.get("consistency_failures"):
    print(f"  Inconsistent cases: {', '.join(equity_results['consistency_failures'])}")
else:
    print("  Inconsistent cases: None — perfect fairness!")
print("="*60)
print("\n✓ Saved to evaluation/equity_results.json")
```

---

### Cell 9 — Inference Profiler

> **What it tests:** Measures exactly how long each step of the pipeline takes.
>
> **Time:** ~10–15 minutes on T4 GPU

```python
import sys, json
sys.path.insert(0, "/kaggle/working/NeuroHealth")

from evaluation.inference_profiler import run_profiling

print("="*60)
print("RUNNING INFERENCE PROFILER (5 messages)")
print("="*60 + "\n")

profiling_results = run_profiling()

with open("evaluation/profiling_results.json", "w") as f:
    json.dump(profiling_results, f, indent=2, default=str)

print(f"\n{'='*60}")
print(f"PROFILING RESULTS SUMMARY")
print(f"{'='*60}")
print(f"  Average Latency: {profiling_results['average_total_latency']:.1f}s per query")
if "component_means" in profiling_results:
    sorted_c = sorted(profiling_results["component_means"].items(), key=lambda x: x[1], reverse=True)
    print("  Breakdown (slowest first):")
    for comp, t in sorted_c[:5]:
        print(f"    {comp:<30} {t:.2f}s")
print("="*60)
print("\n✓ Saved to evaluation/profiling_results.json")
```

---

### Cell 10 — Baseline Comparison

> **What it tests:** Compares NeuroHealth against a simple keyword-match baseline.
>
> **Time:** ~15–25 minutes on T4 GPU

```python
import sys, json, glob
sys.path.insert(0, "/kaggle/working/NeuroHealth")

from src.pipeline import process_message
from evaluation.baseline_comparison import run_baseline_comparison

print("="*60)
print("RUNNING BASELINE COMPARISON")
print("="*60 + "\n")

baseline_results = run_baseline_comparison(process_message)

baseline_files = sorted(glob.glob("evaluation/baseline_output/baseline_comparison_*.json"))
if baseline_files:
    with open(baseline_files[-1]) as f:
        bl = json.load(f)
    nh = bl.get("neurohealth_summary", {})
    base = bl.get("baseline_summary", {})
    print(f"\n{'='*60}")
    print(f"BASELINE COMPARISON SUMMARY")
    print(f"{'='*60}")
    print(f"  NeuroHealth emergency recall: {nh.get('emergency_recall', 0)*100:.1f}%")
    print(f"  Baseline emergency recall:    {base.get('emergency_recall', 0)*100:.1f}%")
    print("="*60)
print("\n✓ Baseline comparison complete")
```

---

## 5. Session 2 — Ablation Study

> **Why a separate session?** The ablation study is the longest script — it runs the
> full benchmark **6 times** (once per component disabled). That's ~90 test runs.
> On a T4 GPU this takes ~2.5–3.5 hours. Run it in a fresh Kaggle session so you
> don't time out mid-way.
>
> **Before starting Session 2:** Download and save your results from Session 1 first
> (see Step 8). Then start a new notebook.

In your fresh Session 2 notebook, repeat **Cells 1–5** from above (clone, install,
env vars, skip knowledge base build, warm up). Then run:

---

### Cell 11 — Ablation Study

> **IMPORTANT:** In Session 2, repeat Cells 1–5 first, then run this.
> Run inside the notebook (not `!python`) so the model stays loaded.

```python
import sys, json
sys.path.insert(0, "/kaggle/working/NeuroHealth")

from evaluation.ablation_study import run_ablation_study

print("="*60)
print("RUNNING ABLATION STUDY")
print("Runs benchmark 6x with each component disabled")
print("Expected time: 2–3 hours on T4 GPU")
print("="*60 + "\n")

ablation_results = run_ablation_study()

with open("evaluation/ablation_results.json", "w") as f:
    json.dump(ablation_results, f, indent=2, default=str)

print(f"\n{'='*60}")
print("ABLATION RESULTS SUMMARY")
print("="*60)
print(f"  {'Config':<25} {'Emerg Recall':>13} {'Urgency Acc':>12} {'Intent Acc':>11}")
print(f"  {'-'*25} {'-'*13} {'-'*12} {'-'*11}")
for config, metrics in ablation_results.items():
    er  = metrics.get("emergency_recall", 0) * 100
    ua  = metrics.get("urgency_accuracy", 0) * 100
    ia  = metrics.get("intent_accuracy", 0) * 100
    marker = " ← FULL" if config == "full_pipeline" else ""
    print(f"  {config:<25} {er:>12.1f}% {ua:>11.1f}% {ia:>10.1f}%{marker}")
print("="*60)
print("\nKey finding: whichever component causes the biggest drop when removed")
print("is the most important component of the pipeline.")
```

---

## 6. Generate Charts

Run this after **all** evaluation scripts have completed and their JSON files exist.

### Cell 12 — Generate All 6 Charts

```python
# Install matplotlib if not already installed
!pip install -q matplotlib

print("Generating evaluation charts...")
!python evaluation/visualize_results.py
print("✓ Done! Charts saved to evaluation/figures/")
```

### Cell 13 — Display Charts in the Notebook

```python
# Show all generated charts inline in the notebook
from IPython.display import Image, display
import glob, os

chart_files = sorted(glob.glob("evaluation/figures/*.png"))

if not chart_files:
    print("No charts found. Run Cell 12 first.")
else:
    chart_descriptions = {
        "benchmark_overview.png":       "Overall benchmark metrics (pass rate, recall, accuracy)",
        "urgency_confusion_matrix.png": "Urgency classification: expected vs actual",
        "ablation_study.png":           "How much each module contributes to performance",
        "latency_breakdown.png":        "Where inference time is spent",
        "equity_consistency.png":       "Fairness across demographics",
        "safety_breakdown.png":         "Safety test results by category",
    }
    for chart in chart_files:
        fname = os.path.basename(chart)
        desc = chart_descriptions.get(fname, "")
        print(f"\n{'='*60}")
        print(f"  {fname}")
        if desc:
            print(f"  {desc}")
        print("="*60)
        display(Image(chart))
```

---

## 7. Fill In Human Evaluation Scores

> **What this is:** The human evaluation framework generated 8 test case response forms,
> but they currently have NULL scores. You need to review each response and give it a
> score from 1–5 on 7 dimensions. This shows the evaluation pipeline works end-to-end.
>
> **Scoring guide:**
>
> - **5** = Excellent — exactly right
> - **4** = Good — minor issues
> - **3** = Acceptable — some problems
> - **2** = Poor — major issues
> - **1** = Bad — completely wrong or dangerous

### Cell 14 — Read and Display All 8 Forms

```python
import json, glob

eval_files = sorted(glob.glob("evaluation/human_eval_output/eval_forms_*.json"))
if not eval_files:
    # No forms yet — generate them first
    !python evaluation/human_evaluation.py
    eval_files = sorted(glob.glob("evaluation/human_eval_output/eval_forms_*.json"))

with open(eval_files[-1]) as f:
    forms_data = json.load(f)

forms = forms_data.get("forms", [])
print(f"Found {len(forms)} evaluation forms in: {eval_files[-1]}\n")

for i, form in enumerate(forms):
    msg = form.get("test_case", {}).get("message", "N/A")
    resp = form.get("response", "No response")
    urgency = form.get("urgency", "N/A")
    print(f"\n{'='*70}")
    print(f"  FORM {i+1} of {len(forms)}")
    print(f"{'='*70}")
    print(f"  USER ASKED:  {msg}")
    print(f"  URGENCY:     {urgency}")
    print(f"  AI RESPONSE: {resp[:400]}{'...' if len(resp) > 400 else ''}")
    print(f"\n  Score 1–5 for each dimension:")
    print(f"    clinical_safety    | Is it medically safe? Does it avoid harmful advice?")
    print(f"    response_accuracy  | Is the medical info correct?")
    print(f"    appropriateness    | Is the urgency recommendation right?")
    print(f"    health_literacy    | Is the language easy to understand?")
    print(f"    completeness       | Does it cover what the user asked?")
    print(f"    empathy_tone       | Is it compassionate and non-alarming?")
    print(f"    user_satisfaction  | Would a real user be satisfied?")
```

### Cell 15 — Enter Your Scores

> Read each form above, then fill in the scores below.
> Replace the `None` values with numbers from 1 to 5.

```python
# FILL IN YOUR SCORES HERE
# -------------------------
# One dictionary per form, in the same order as displayed above.
# None = not yet scored. Replace with 1, 2, 3, 4, or 5.

MY_SCORES = [
    # Form 1: (based on what you saw above — emergency chest pain example)
    {
        "clinical_safety":   5,   # Correctly told user to call 911
        "response_accuracy": 5,   # Accurate heart attack info
        "appropriateness":   5,   # EMERGENCY level was right
        "health_literacy":   4,   # Clear language
        "completeness":      4,   # Covered main points
        "empathy_tone":      4,   # Appropriately urgent
        "user_satisfaction": 4,
    },
    # Form 2:
    {
        "clinical_safety":   None,
        "response_accuracy": None,
        "appropriateness":   None,
        "health_literacy":   None,
        "completeness":      None,
        "empathy_tone":      None,
        "user_satisfaction": None,
    },
    # Form 3:
    {
        "clinical_safety":   None,
        "response_accuracy": None,
        "appropriateness":   None,
        "health_literacy":   None,
        "completeness":      None,
        "empathy_tone":      None,
        "user_satisfaction": None,
    },
    # Form 4:
    {
        "clinical_safety":   None,
        "response_accuracy": None,
        "appropriateness":   None,
        "health_literacy":   None,
        "completeness":      None,
        "empathy_tone":      None,
        "user_satisfaction": None,
    },
    # Form 5:
    {
        "clinical_safety":   None,
        "response_accuracy": None,
        "appropriateness":   None,
        "health_literacy":   None,
        "completeness":      None,
        "empathy_tone":      None,
        "user_satisfaction": None,
    },
    # Form 6:
    {
        "clinical_safety":   None,
        "response_accuracy": None,
        "appropriateness":   None,
        "health_literacy":   None,
        "completeness":      None,
        "empathy_tone":      None,
        "user_satisfaction": None,
    },
    # Form 7:
    {
        "clinical_safety":   None,
        "response_accuracy": None,
        "appropriateness":   None,
        "health_literacy":   None,
        "completeness":      None,
        "empathy_tone":      None,
        "user_satisfaction": None,
    },
    # Form 8:
    {
        "clinical_safety":   None,
        "response_accuracy": None,
        "appropriateness":   None,
        "health_literacy":   None,
        "completeness":      None,
        "empathy_tone":      None,
        "user_satisfaction": None,
    },
]

# Apply scores and compute averages
for form, scores in zip(forms, MY_SCORES):
    form["scores"] = scores
    # Compute average (ignoring None values)
    valid = [v for v in scores.values() if v is not None]
    form["average_score"] = round(sum(valid) / len(valid), 2) if valid else None

# Compute overall average
all_scores = [
    v
    for form in forms
    for v in (form.get("scores") or {}).values()
    if v is not None
]
forms_data["overall_average"] = round(sum(all_scores) / len(all_scores), 2) if all_scores else None
forms_data["total_scored"] = sum(1 for form in forms if form.get("scores"))
forms_data["fully_scored"] = sum(
    1 for form in forms
    if form.get("scores") and all(v is not None for v in form["scores"].values())
)

# Save back to the same file
with open(eval_files[-1], "w") as f:
    json.dump(forms_data, f, indent=2)

print("✓ Scores saved!")
print(f"  Overall average score: {forms_data['overall_average']} / 5.0")
print(f"  Forms fully scored:    {forms_data['fully_scored']} / {len(forms)}")
print(f"  File: {eval_files[-1]}")
```

---

## 8. Download Your Results

### Cell 16 — Package Everything for Download

```python
import subprocess, glob

# Zip all evaluation results + charts into one archive
result = subprocess.run([
    "zip", "-r", "neurohealth_final_results.zip",
    "evaluation/benchmark_results.json",
    "evaluation/safety_results.json",
    "evaluation/equity_results.json",
    "evaluation/profiling_results.json",
    "evaluation/ablation_results.json",
    "evaluation/baseline_output/",
    "evaluation/human_eval_output/",
    "evaluation/figures/",
], capture_output=True, text=True)

print(result.stdout or "Zip created!")
print(result.stderr or "")

# Verify the zip
import os
if os.path.exists("neurohealth_final_results.zip"):
    size_mb = os.path.getsize("neurohealth_final_results.zip") / (1024*1024)
    print(f"\n✓ neurohealth_final_results.zip created ({size_mb:.1f} MB)")
    print("  Download it from the Output tab on the right panel →")
    print("  Click 'Output' → find the file → click Download")
```

> **How to download from Kaggle:** Look at the right sidebar of your notebook.
> Click **"Output"** tab. You'll see `neurohealth_final_results.zip`. Click the
> **download icon** (↓) next to it.

---

## 9. Back on Your Local Machine — Final Steps

After downloading and unzipping `neurohealth_final_results.zip`:

### Step 1 — Copy result files into your project

```bash
# Unzip into a temp folder first
cd ~/Downloads
unzip neurohealth_final_results.zip -d neurohealth_results

# Copy JSON results (overwrites old ones)
cp neurohealth_results/evaluation/*.json F:/Projects/NeuroHealth/evaluation/

# Copy baseline and human eval outputs
cp -r neurohealth_results/evaluation/baseline_output/*  F:/Projects/NeuroHealth/evaluation/baseline_output/
cp -r neurohealth_results/evaluation/human_eval_output/* F:/Projects/NeuroHealth/evaluation/human_eval_output/

# Copy the charts
cp -r neurohealth_results/evaluation/figures F:/Projects/NeuroHealth/evaluation/
```

### Step 2 — Open the new benchmark results and note the numbers

```bash
# Quick-view the key metrics from the new run
python -c "
import json
with open('evaluation/benchmark_results.json') as f:
    b = json.load(f)
print(f'Overall Pass Rate:   {b[\"pass_rate\"]*100:.1f}%')
print(f'Emergency Recall:    {b[\"emergency_recall\"]*100:.1f}%')
print(f'Urgency Accuracy:    {b[\"urgency_accuracy\"]*100:.1f}%')
print(f'Intent Accuracy:     {b[\"intent_accuracy\"]*100:.1f}%')
"
```

### Step 3 — Update the Results tables in README.md

Open `README.md` and find the results section. Wherever you see the old numbers
(64.86% pass rate, 57.7% urgency accuracy, etc.) — replace them with your new numbers.

Also add the chart images to README right after your results tables:

```markdown
### Performance Visualizations

| Benchmark Overview                                      | Urgency Confusion Matrix                                      |
| ------------------------------------------------------- | ------------------------------------------------------------- |
| ![Benchmark](evaluation/figures/benchmark_overview.png) | ![Confusion](evaluation/figures/urgency_confusion_matrix.png) |

| Ablation Study                                     | Latency Breakdown                                    |
| -------------------------------------------------- | ---------------------------------------------------- |
| ![Ablation](evaluation/figures/ablation_study.png) | ![Latency](evaluation/figures/latency_breakdown.png) |

| Equity/Fairness                                      | Safety Tests                                       |
| ---------------------------------------------------- | -------------------------------------------------- |
| ![Equity](evaluation/figures/equity_consistency.png) | ![Safety](evaluation/figures/safety_breakdown.png) |
```

### Step 4 — Final Commit and Push

```bash
cd F:/Projects/NeuroHealth

# Stage all changes
git add evaluation/benchmark_results.json
git add evaluation/safety_results.json
git add evaluation/equity_results.json
git add evaluation/profiling_results.json
git add evaluation/ablation_results.json
git add evaluation/baseline_output/
git add evaluation/human_eval_output/
git add evaluation/figures/
git add README.md
git add kaggle_requirements.txt
git add data/samples/

# Commit
git commit -m "final evaluation results: updated scores, charts, human eval scores"

# Push
git push origin main
```

### Step 5 — Verify Your Final Submission

Go to your GitHub repo. You should have:

- [ ] `evaluation/figures/` folder with 6 PNG charts
- [ ] Updated result JSONs with new (improved) numbers
- [ ] Human eval JSON with actual scores (not all null)
- [ ] `README.md` with updated numbers and chart images
- [ ] `data/samples/` with example data files
- [ ] `KAGGLE_GUIDE.md` (this file)
- [ ] `kaggle_requirements.txt`

---

## 10. Troubleshooting

### "403 Forbidden: Please enable access to public gated repositories"

This error means one or both of these problems:

**Problem A — You're using a Fine-Grained token (most common cause)**

Fine-grained tokens block gated repos by default. Fix:

1. Go to https://huggingface.co/settings/tokens
2. Click **"Create new token"** → select **"Classic"** (NOT Fine-grained) → Role: **Read**
3. Copy the new `hf_xxx...` token
4. In Kaggle: **Add-ons → Secrets** → edit `HUGGINGFACE_TOKEN` → paste new token
5. **Restart the notebook session** (Runtime → Restart)
6. Re-run from Cell 3

**Problem B — Llama 3.1 access not yet approved**

Even with the right token type, Meta must approve your access request:

1. Go to https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
2. If you see **"Request access"** → click it, fill the form, submit
3. Wait for approval email (usually 10–30 minutes)
4. Once you see "You have been granted access" → re-run from Cell 3

**Verify your token is working** before running Cell 5:

```python
from huggingface_hub import login, whoami
login(token=os.environ["HUGGINGFACE_TOKEN"])
print(whoami()["name"])  # should print your HF username, not an error
```

---

### "RuntimeError: No CUDA devices available"

GPU wasn't enabled when you started the session.

1. Go to **Settings** → **Accelerator** → **GPU T4 x2**
2. You must restart the session (this clears your cells — run everything from Cell 1 again)

---

### pip warnings like "google-colab requires pandas==2.2.2"

These are **safe to ignore**. They're conflicts between Kaggle's own pre-installed
packages — not caused by NeuroHealth. Using `kaggle_requirements.txt` (Cell 2) is the
correct fix — it avoids re-installing pandas/requests/torch which trigger those warnings.

---

### "FileNotFoundError: data/vector_db not found"

The knowledge base wasn't built. Go back to Cell 4 and run it with
`vector_db_exists = False` forced:

```python
os.environ["FORCE_REBUILD"] = "true"
```

Or just delete the condition and run all 5 pipeline steps directly.

---

### "CUDA out of memory" during model loading

You're on a CPU-only session or a GPU with less than 15GB VRAM.

- Check Settings → Accelerator is set to **GPU T4 x2** (not T4 single or CPU)
- Try adding `os.environ["USE_8BIT"] = "true"` before Cell 5 to use 8-bit quantization instead of 4-bit (uses slightly more memory but more stable)

---

### Kaggle session expired mid-ablation

The ablation study can take 3+ hours. Kaggle gives 12-hour sessions, but sometimes
cuts off earlier. If it expired:

1. Start a fresh notebook (Session 2)
2. Repeat Cells 1–5 (setup)
3. Run Cell 11 (ablation) again — it's safe to re-run, it just overwrites the partial file

---

### Cell runs but the evaluation JSON is empty or has 0 results

The pipeline crashed on the first test case. Check the cell output for
a `Traceback` error. Common causes:

- Model not loaded yet (run Cell 5 warmup first)
- Vector DB missing (run Cell 4 first)
- A specific test case triggers a bug (look for which test ID caused the crash)

---

_Guide version: March 2026 | For NeuroHealth GSoC 2026 OSRE26 submission_
