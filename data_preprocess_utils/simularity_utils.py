import numpy as np
import re
from .segment_utils import segment_as_sentence

def lcs_match_ratio(target, query):
    import pylcs
    return pylcs.lcs2(target, query) /len(query)

def embedding_match_ratio(context, target, query):
    from .embedding.text_embedding import CachedEmbeddingInvocation
    
    context : CachedEmbeddingInvocation = context    
    # step = max(len(query) + 4, 16)
    # window_size =  2 * step
    # max_window_size = 2 * window_size
    tobetest = list(segment_as_sentence(target = target, window_size = 32, max_window_size= 64, duplicating_length= 8))
    embeddings = context.invoke_embedding(tobetest + [query])
    target_embedding = np.array(embeddings[: -1]) # (M, N)
    query_embedding = np.array( embeddings[-1]) #  (N,) 
    target_embedding_norm = target_embedding / np.linalg.norm(target_embedding, axis=1, keepdims=True) # (M, N)
    query_embedding_norm = query_embedding / np.linalg.norm(query_embedding)
    simularities : np.ndarray = target_embedding_norm @ query_embedding_norm
    return simularities.max(), tobetest[simularities.argmax()]