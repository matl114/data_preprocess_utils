import re
from typing import *

def segment_as_sentence(target : str, window_size : int = 32, max_window_size : int = 64, duplicating_length : int = 8) -> Generator[str, None, None]:
    assert window_size != 0 and max_window_size != 0
    assert window_size < max_window_size
    assert duplicating_length >= 0
    segments = re.split(r'(?<=[，。！？,.!?])', target)
    segments = [seg.strip() for seg in segments if seg is not None and seg.strip()]
    current_seg = ""
    for seg in segments:
        if len(current_seg) + len(seg) <= window_size:
            current_seg = current_seg + seg 
        elif len(current_seg) > window_size:
            yield current_seg
            current_seg = (current_seg[- duplicating_length :] if duplicating_length != 0 else "") + seg 
        else:
            current_seg = current_seg + seg 
            max_window = current_seg[: max_window_size]
            yield max_window
            current_seg = (max_window[- duplicating_length :] if duplicating_length != 0 else "") + current_seg[max_window_size :]
        while len(current_seg) > max_window_size:
            max_window = current_seg[: max_window_size]
            yield max_window
            current_seg = (max_window[- duplicating_length :] if duplicating_length != 0 else "") + current_seg[max_window_size :]