from pydantic import BaseModel
from dataclasses import dataclass
                
class OCRTextBlock(BaseModel):
    text: str 
    score: float 
    box : list[int]
    poly : list[list[int]]

class OCRContent(BaseModel):
    type : str
    pages : list[list[OCRTextBlock]]
    
@dataclass
class PageSize:
    width : int 
    height : int
    