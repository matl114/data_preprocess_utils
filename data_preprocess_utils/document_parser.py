from typing import * 
import re


class DocumentNode:
    # pattern : str
    # title : Optional[str] = None 
    # contents : list[str] = []
    # subnodes : list = []
    
    def __init__(self, pattern, ** kwargs):
        self.pattern = pattern
        self.title = kwargs.get("title", None)
        self.contents = kwargs.get("contents", [])
        self.subnodes = kwargs.get("subnodes", [])
    
    def flatten_json(self):
        return {
            "title" : self.title,
            "content": "\n".join(self.contents),
            "subnodes" : [
                val.flatten_json() for val in self.subnodes
            ]
        }
        
        
class DocumentParser:
    digit_title_pattern = r'^(\d+(?:\.\d+)*)'
    chinese_digit_title_pattern = r'^(第\s*[零一二三四五六七八九十百千\d]+\s*[\u4e00-\u9fa5])'
    any_title_pattern = r'((\d+(?:\.\d+)*)|(第\s*[零一二三四五六七八九十百千\d]+\s*[\u4e00-\u9fa5]))'
    chinese_digit = r"\s*[零一二三四五六七八九十百千\d]+\s*"
    digit = r"\s*\d+\s*"
    # TODO should we add (一) （二） ...
    @classmethod
    def match_title_to_pattern(cls, title : str) -> str :
        if re.match(cls.chinese_digit_title_pattern, title):
            title = re.sub(cls.chinese_digit, "▢▨▨▢", title)
            title = title.replace("▢▨▨▢", "[零一二三四五六七八九十百千d]+")
        elif re.match(cls.digit_title_pattern, title):
            title = re.sub(cls.digit, "d+", title)
        else :
            return None
        return title
    
    def __init__(self):
        self.root = DocumentNode(title= "root", pattern= "root")
        self.current_node_stack = [self.root]
        self.current = self.root
        self.level_to_depth = {"root" : 0}
        self.current_depth = 0
        
    def acceptline(self, text : str) -> Self:
        for t in text.split("\n"):
            self._acceptline(t)
        return self
        
    def _acceptline(self, text : str) -> Self:
        text = text.strip()
        if not text:
            return
        iter = re.finditer(DocumentParser.any_title_pattern, text)
        first_index = 0
        
        for val in iter :
            # 截取一段 加入current
            if val.start() != 0:
                # fix: 不要将文中的数字匹配成标题
                break
            content = text[first_index: val.start()].strip()
            if content:
                self.current.contents.append(content)
            first_index = val.end()
            next_title = val.group(0)
            generated_pattern = DocumentParser.match_title_to_pattern(next_title)
            assert generated_pattern is not None
            current = self.change_level_by_pattern(generated_pattern)
            current.title = next_title
        content = text[first_index: ].strip()
        if content:
            self.current.contents.append(content)
        return self
    
    def acceptlines(self, texts : list[str]) -> Self:
        for text in texts :
            self.acceptline(text)
        return self
        
    def build(self) -> DocumentNode:
        return self.root
    
    def buildInfo(self) -> dict:
        return {
            "root" : self.root.flatten_json()
        }
            
    def change_level_by_pattern(self, pattern : str) -> DocumentNode:
        predicted_depth = 0
        for key, val in self.level_to_depth.items():
            if key == pattern :
                predicted_depth = val
                break
        else:
            if pattern.startswith("第") :
                predicted_depth = self.current_depth + 1
            else :
                predicted_depth = pattern.count(".") + 1
            self.level_to_depth[pattern] = predicted_depth      
        old_depth = self.current_depth
        self.current_depth = predicted_depth
        if predicted_depth > old_depth :
            #go deeper
            new_node = DocumentNode(pattern= pattern)
            self.current.subnodes.append(new_node)
            self.current_node_stack.append(new_node)
            self.current = new_node
        else:
            # roll back
        
            while len(self.current_node_stack) > 0:
                self.current_node_stack.pop()
                depth = self.level_to_depth[self.current_node_stack[-1].pattern]
                if depth < predicted_depth:
                    break
            assert len(self.current_node_stack) > 0
            node = self.current_node_stack[-1]
            new_node = DocumentNode(pattern= pattern)
            node.subnodes.append(new_node)
            self.current_node_stack.append(new_node)
            self.current = new_node
        return self.current



