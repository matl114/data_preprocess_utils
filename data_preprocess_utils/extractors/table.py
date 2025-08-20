from .base import BaseExtractor
import pandas as pd
from typing import *
from ..document_utils import flatten_raw_texts


class TableExtractor(BaseExtractor):
    def extract(self, filepath : str, ** kwargs) -> Iterable[str]:
        # avoid uname0 col
        index_col = kwargs.get("index_col", 0)
        df = pd.read_table(
            filepath, 
            index_col= index_col
            )
        return flatten_raw_texts(df.apply(lambda g : ", ".join(f'"{k}": "{v}"' for k, v in g.items() if pd.notna(v) and v), axis = 1).values)