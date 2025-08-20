from .base import BaseExtractor
from typing import *
from ..document_utils import flatten_raw_texts

class TxtExtractor(BaseExtractor) :
    def extract(self, filepath : str, ** kwargs) -> Iterable[str]:
        with open(filepath, "r", encoding= "utf-8") as fp:
            contents = fp.readlines()
        return list(flatten_raw_texts(contents))
    