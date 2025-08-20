import os
from pathlib import Path
from typing import *

def walk_while_precessing_files(path : str, function : Callable[[str], None], predicate : Callable[[str], bool] = None) -> None:
    for root ,_, files in os.walk(path):
        for file in files:
            path = os.path.join(root, file)
            if predicate is None or predicate(path):
                function(path)
            
def walk_while_mapping_files_to(path : str, mapping_path,  function : Callable[[str, str], None] , predicate : Callable[[str], bool] = None, filename_mapper : Callable[[str], str] = lambda x: x) -> None:
    for root, _ , files in os.walk(path):
        outpath = Path(mapping_path) / Path(root).relative_to(path)
        os.makedirs(outpath, exist_ok=True)
        for file in files :
            path = str( os.path.join(root, file))
            if predicate is None or predicate(path):
                output_path = str( outpath / filename_mapper(file) )
                input_path = path
                function(input_path, output_path)
                
def write_lines(path : str, lists : list[str], splitter : str = "\n", mode : Literal["w", "a", "x"] = "w") -> None:
    os.makedirs(Path(path).parent, exist_ok= True)
    with open(path, mode, encoding= "utf-8") as fp:
        fp.write(splitter.join(lists))
                
def read_lines(path : str, strip_lines : bool = False) -> list[str] | None:
    if os.path.isfile(path):
        with open(path, "r", encoding= "utf-8") as fp:
            lst = fp.readlines()
            if strip_lines:
                lst = [ls.strip()  for ls in lst]
            return lst
    else:
        return None