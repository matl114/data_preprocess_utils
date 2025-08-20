

def lcs_match_ratio(target, query):
    import pylcs
    return pylcs.lcs2(target, query) /len(query)

def embedding_match_ratio(context, target, query):
    from .embedding.text_embedding import CachedEmbeddingInvocation
    import numpy as np
    import re
    context : CachedEmbeddingInvocation = context    
    step = max(len(query) + 4, 16)
    window_size =  2 * step
    max_window_size = 2 * window_size
    tobetest = []
    segments = re.split(r'(?<=[，。！？,.!?])', target)
    segments = [seg.strip() for seg in segments if seg is not None and seg.strip()]
    current_seg = ""
    for seg in segments:
        if len(current_seg) + len(seg) <= window_size:
            current_seg = current_seg + seg 
        elif len(current_seg) > window_size:
            tobetest.append(current_seg)
            current_seg = current_seg[- len(current_seg) //2 :] + seg 
        else:
            current_seg = current_seg + seg 
            max_window = current_seg[: max_window_size]
            tobetest.append(max_window)
            current_seg = max_window[-len(max_window) //2 :] + current_seg[max_window_size :]
        while len(current_seg) > max_window_size:
            max_window = current_seg[: max_window_size]
            tobetest.append(max_window)
            current_seg = max_window[-len(max_window) //2 :] + current_seg[max_window_size :]
    embeddings = context.invoke_embedding(tobetest + [query])
    target_embedding = np.array(embeddings[: -1]) # (M, N)
    query_embedding = np.array( embeddings[-1]) #  (N,) 
    target_embedding_norm = target_embedding / np.linalg.norm(target_embedding, axis=1, keepdims=True) # (M, N)
    query_embedding_norm = query_embedding / np.linalg.norm(query_embedding)
    simularities : np.ndarray = target_embedding_norm @ query_embedding_norm
    return simularities.max(), tobetest[simularities.argmax()]