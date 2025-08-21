from pydantic import BaseModel, Field
from enum import Enum
from typing import *

class ModelType(Enum):
    """
    Enum class for model type.
    """

    LLM = "llm"
    TEXT_EMBEDDING = "text-embedding"
    RERANK = "rerank"
    SPEECH2TEXT = "speech2text"
    MODERATION = "moderation"
    TTS = "tts"

class AbstractAIModel(BaseModel):
    model_type: ModelType = Field(description="Model type")
    
    def invoke_embedding(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("abstract")
    
class AbstractModelInvocation(BaseModel):
    model_instance : Optional[AbstractAIModel] = Field(description= "Model invocation")
    
class EmbeddingInvocation(AbstractModelInvocation):
    def invoke_embedding(self, texts: list[str]) -> list[list[float]]:
        pass 

