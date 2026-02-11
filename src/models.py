"""
LLM model configuration for the FTR Accelerator Agent.
"""

from strands.models.ollama import OllamaModel
from .config import OLLAMA_HOST, OLLAMA_MODEL


def create_ollama_model() -> OllamaModel:
    """
    Create and return a configured Ollama model instance.
    
    Returns:
        OllamaModel: Configured local LLM model
    """
    return OllamaModel(
        host=OLLAMA_HOST,
        model_id=OLLAMA_MODEL,
        temperature=0.7,
        top_p=0.9,
        # max_tokens=4096,           # uncomment & adjust if needed
        # keep_alive="5m",           # keeps model loaded longer
    )


# Pre-configured model instance for convenience
# local_model = create_ollama_model()

# ──────────────────────────────────────────────────────────────────────────────
# Bedrock Configuration (Optional)
# ──────────────────────────────────────────────────────────────────────────────
from strands.models.bedrock import BedrockModel
from .config import (
    BEDROCK_AWS_PROFILE, 
    BEDROCK_AWS_ACCESS_KEY_ID, 
    BEDROCK_AWS_SECRET_ACCESS_KEY, 
    BEDROCK_AWS_SESSION_TOKEN,
    BEDROCK_AWS_REGION,
    BEDROCK_MODEL_ID
)
import os
import boto3

def create_bedrock_model(model_id: str = BEDROCK_MODEL_ID) -> BedrockModel:
    """Create a Bedrock model instance.
    
    NOTE: BedrockModel does not accept a session object. 
    We must set standard AWS env vars for it to pick up the right credentials.
    Since APN tools use explicit sessions/keys, this won't conflict with them.
    """
    
    # Priority 1: Explicit Keys (if provided)
    if BEDROCK_AWS_ACCESS_KEY_ID and BEDROCK_AWS_SECRET_ACCESS_KEY:
        # Set global env vars for BedrockModel to pick up
        os.environ["AWS_ACCESS_KEY_ID"] = BEDROCK_AWS_ACCESS_KEY_ID
        os.environ["AWS_SECRET_ACCESS_KEY"] = BEDROCK_AWS_SECRET_ACCESS_KEY
        if BEDROCK_AWS_SESSION_TOKEN:
            os.environ["AWS_SESSION_TOKEN"] = BEDROCK_AWS_SESSION_TOKEN
        if BEDROCK_AWS_REGION:
            os.environ["AWS_DEFAULT_REGION"] = BEDROCK_AWS_REGION
            os.environ["AWS_REGION"] = BEDROCK_AWS_REGION
            
        return BedrockModel(model_id=model_id)

    # Priority 2: Named Profile (if provided)
    # Priority 2: Named Profile (if provided)
    elif BEDROCK_AWS_PROFILE:
        # CRITICAL: Unset any explicit keys that might be polluting the env
        # (e.g. if they were loaded from .env but now we want to use a profile)
        for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"]:
            if key in os.environ:
                del os.environ[key]

        # Set profile env var
        os.environ["AWS_PROFILE"] = BEDROCK_AWS_PROFILE
        if BEDROCK_AWS_REGION:
           os.environ["AWS_DEFAULT_REGION"] = BEDROCK_AWS_REGION
           os.environ["AWS_REGION"] = BEDROCK_AWS_REGION
            
        return BedrockModel(model_id=model_id)
    
    # Priority 3: Default Environment/Chain
    else:
        return BedrockModel(model_id=model_id)

# Default to Bedrock (Sonnet 4) as requested
local_model = create_bedrock_model()
# local_model = create_ollama_model() # Uncomment to switch back to Ollama
