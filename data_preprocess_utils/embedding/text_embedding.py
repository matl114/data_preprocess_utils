from ..core.models import AbstractAIModel, EmbeddingInvocation, ModelType
# from langchain_community.llms.ollama import Ollama
from langchain_ollama import OllamaEmbeddings
from typing import *

class OllamaEmbeddingModel(AbstractAIModel):
    model_type : ModelType = ModelType.TEXT_EMBEDDING
    url : str = "http://127.0.0.1:11434"
    model : str 
    def invoke_embedding(self, texts: list[str]) -> list[list[float]]:
        embeddings = OllamaEmbeddings(base_url= self.url, model = self.model)
        result = embeddings.embed_documents(texts)
        return result



class CachedEmbeddingInvocation(EmbeddingInvocation):
    cache_map : dict[str, list[float]] = {}
    def invoke_embedding(self, texts: list[str]) -> list[list[float]]:
        texts_not_in_cache =set( (txt for txt in texts if txt not in self.cache_map.keys()))
        if len(texts_not_in_cache) > 0:
            result = self.model_instance.invoke_embedding(list(texts_not_in_cache))
            for key, val in zip(texts_not_in_cache, result):
                self.cache_map[key] = val
        return [self.cache_map.get(tl) for tl in texts]
    
class ImmutableEmbeddingInvocation(EmbeddingInvocation):
    cache_map : dict[str, list[float]]
    def invoke_embedding(self, texts: list[str]) -> list[list[float]]:
        lst = []
        for txt in texts:
            if txt in self.cache_map.keys():
                lst.append(txt)
            else:
                # Abort 
                raise KeyError(f"\"{txt}\" not in the cache map")
        return lst 