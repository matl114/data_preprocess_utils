from enum import Enum, auto
from .extractors.base import BaseExtractor
from typing import *
from .document_utils import has_cache, read_cache, save_to_cache, is_cache_file

class FileType(Enum):
    PDF = auto()
    WORD = auto()
    TXT = auto()
    TABLE = auto()
    UNKNOWN = auto()
    @classmethod
    def guess_file_type(cls, path : str):
        if path.endswith(".pfdf"):
            return cls.PDF
        elif path.endswith(".docx") or path.endswith(".doc"):
            return cls.WORD 
        elif path.endswith(".txt") :
            return cls.TXT
        elif path.endswith(".xlsx") or path.endswith(".csv") :
            return cls.TABLE
        else:
            return cls.UNKNOWN
        
class Extractor:
    @classmethod
    def extract(cls, filepath : str, filetype : FileType = FileType.UNKNOWN, **kwargs) -> Iterable[str] | None:
        extractor : BaseExtractor = None
        if filetype == FileType.PDF:
            from .extractors.pdf import PdfExtractor
            extractor = PdfExtractor()
        elif filetype == FileType.WORD:
            from .extractors.word import WordExtractor
            extractor = WordExtractor()
        elif filetype == FileType.TXT:
            from .extractors.txt import TxtExtractor
            extractor = TxtExtractor()
        elif filetype == FileType.TABLE:
            from .extractors.table import TableExtractor
            extractor = TableExtractor()
        else:
            from .extractors.txt import TxtExtractor
            extractor = TxtExtractor()
        return extractor.extract(filepath, **kwargs)
    
    @classmethod
    def extract_with_cache(cls, filepath : str, filetype : FileType = FileType.UNKNOWN, **kwargs) -> Iterable[str] | None:
        assert not is_cache_file(filepath)
        if has_cache(filepath):
            return read_cache(filepath)
        else:
            result = cls.extract(filepath, filetype, ** kwargs)
            save_to_cache(filepath, result)
            return result