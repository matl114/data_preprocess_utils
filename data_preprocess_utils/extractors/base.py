from abc import abstractmethod
import logging
from typing import *

class BaseExtractor :
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    # method returned must not be a Generator
    # method returned must goes throught document_parser.flatten_raw_text which cleans the texts
    @abstractmethod
    def extract(self, filepath : str, ** kwargs) -> Iterable[str]:
        ...
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        