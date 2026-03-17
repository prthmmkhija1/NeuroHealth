# src/llm_utils.py

"""
LLM Utility Module (Local Llama)
---------------------------------
Shared utility that loads the local Llama model ONCE and provides
a generate() function for all modules.

WHY THIS EXISTS:
The original guide uses OpenAI API calls (gpt-4o-mini) in every module.
Since we're running zero-cost with local Llama on the A100, this module
replaces ALL those API calls with local inference.

USAGE:
    from src.llm_utils import generate_response
    result = generate_response(system_prompt, user_message)
"""

import os
import torch
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "1024"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))

# NOTE: HF_TOKEN is intentionally NOT read here at module-import time.
# It is read inside _load_model() so that setting os.environ["HUGGINGFACE_TOKEN"]
# in a notebook cell AFTER import still works correctly.

# ── Singleton model holder ─────────────────────────────────────────────
_model = None
_tokenizer = None


def _load_model():
    """
    Loads the Llama model and tokenizer exactly once (singleton pattern).
    Uses 4-bit quantization on GPU to fit in memory efficiently.
    On CPU (HP-INT), loads in float32 for testing (very slow but works).
    """
    global _model, _tokenizer

    if _model is not None:
        return _model, _tokenizer

    # Read token at call time so notebook cells that set os.environ AFTER
    # import still work correctly (avoids the "captured at import time" trap).
    hf_token = os.getenv("HUGGINGFACE_TOKEN", "")

    if not hf_token or hf_token.startswith("hf_YOUR"):
        raise EnvironmentError(
            "HUGGINGFACE_TOKEN is not set in .env. "
            "Add your real token before running LLM-dependent code."
        )

    # Support pre-downloading the model to a local directory.
    # On Kaggle, hub file-resolution for sharded models can fail — downloading
    # first via snapshot_download and loading from a local path is always reliable.
    # Set LOCAL_MODEL_DIR env var to the downloaded path to use it.
    local_dir = os.getenv("LOCAL_MODEL_DIR", "")
    load_path = local_dir if local_dir and os.path.isdir(local_dir) else MODEL_NAME

    print(f"Loading model from: {load_path}")
    print("This may take a few minutes on first load...")

    from transformers import AutoModelForCausalLM, AutoTokenizer

    # Load tokenizer
    _tokenizer = AutoTokenizer.from_pretrained(
        load_path,
        token=hf_token,
        trust_remote_code=True,
    )
    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token

    # Check if GPU is available
    if torch.cuda.is_available():
        print(f"GPU detected: {torch.cuda.get_device_name(0)}")
        print("Loading with 4-bit quantization for efficiency...")

        from transformers import BitsAndBytesConfig

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )

        _model = AutoModelForCausalLM.from_pretrained(
            load_path,
            token=hf_token,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True,
        )
    else:
        print("No GPU detected. Loading on CPU (slow, for testing only)...")
        _model = AutoModelForCausalLM.from_pretrained(
            load_path,
            token=hf_token,
            torch_dtype=torch.float32,
            device_map="cpu",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )

    print("Model loaded successfully!")
    return _model, _tokenizer


def generate_response(
    system_prompt: str,
    user_message: str,
    max_new_tokens: int = None,
    temperature: float = None,
    json_mode: bool = False,
) -> str:
    """
    Generate a response from the local Llama model.

    This is the DROP-IN REPLACEMENT for every OpenAI API call in the guide.
    Instead of:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": msg}]
        )
    
    Just do:
        from src.llm_utils import generate_response
        response = generate_response(system_prompt=sys, user_message=msg)

    Args:
        system_prompt: Instructions for the model (e.g., "You are a medical assistant...")
        user_message: The user's actual input
        max_new_tokens: Maximum tokens to generate (default from .env)
        temperature: Randomness (0.0=deterministic, 1.0=creative)
        json_mode: If True, instructs the model to output valid JSON

    Returns:
        The model's text response as a string
    """
    model, tokenizer = _load_model()

    if max_new_tokens is None:
        max_new_tokens = MAX_NEW_TOKENS
    if temperature is None:
        temperature = TEMPERATURE

    # If JSON mode requested, append instruction to system prompt
    effective_system = system_prompt
    if json_mode:
        effective_system += "\n\nIMPORTANT: You MUST respond with valid JSON only. No other text."

    # Build messages in Llama's chat format
    messages = [
        {"role": "system", "content": effective_system},
        {"role": "user", "content": user_message},
    ]

    # Apply chat template
    input_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(input_text, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature if temperature > 0 else None,
            do_sample=temperature > 0,
            top_p=0.9 if temperature > 0 else None,
            pad_token_id=tokenizer.pad_token_id,
        )

    # Decode only the NEW tokens (skip the input)
    new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    return response


def generate_with_history(
    system_prompt: str,
    conversation_history: list,
    max_new_tokens: int = None,
    temperature: float = None,
) -> str:
    """
    Generate a response given a full conversation history.
    Used by conversation_manager for multi-turn chats.

    Args:
        system_prompt: The system instructions
        conversation_history: List of {"role": "user"|"assistant", "content": "..."}
        max_new_tokens: Max tokens to generate
        temperature: Randomness

    Returns:
        The model's text response
    """
    model, tokenizer = _load_model()

    if max_new_tokens is None:
        max_new_tokens = MAX_NEW_TOKENS
    if temperature is None:
        temperature = TEMPERATURE

    # Build full message list
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)

    # Apply chat template
    input_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(input_text, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature if temperature > 0 else None,
            do_sample=temperature > 0,
            top_p=0.9 if temperature > 0 else None,
            pad_token_id=tokenizer.pad_token_id,
        )

    new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    return response


# ── Quick test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing LLM utility...")
    result = generate_response(
        system_prompt="You are a helpful medical assistant. Be concise.",
        user_message="What are common symptoms of the flu?",
    )
    print(f"\nResponse:\n{result}")
