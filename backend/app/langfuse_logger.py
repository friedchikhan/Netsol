import os
from langfuse import Langfuse

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

def log_system_prompt(prompt: str, name: str = "SystemPrompt"):
    span = langfuse.start_span(
        name=name,
        input={"prompt": prompt}
    )
    span.end()
    langfuse.flush()