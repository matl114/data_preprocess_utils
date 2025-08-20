from typing import * 
import re
from pathlib import Path
import os
from .logging_utils import logger
from .core.data_models import OCRTextBlock, PageSize
import math
import numpy as np
import base64
import io

def flatten_raw_texts(texts: Iterable[str]) -> Generator[str, None , None]:
    for s in texts:
        for splited in s.split("\n"):
            val2 = clean_document_text(splited)
            if val2 is not None and val2:
                yield val2

def clean_document_text(text: str) -> str:
    if not text or len(text) <= 1:
        return None
    
    # Chinese to English punctuation mapping
    punctuation_map = {
        '，': ',', '。': '.', '、': ',', '；': ';', '：': ':',
        '？': '?', '！': '!', '「': '"', '」': '"', '『': '"', 
        '』': '"', '（': '(', '）': ')', '【': '[', '】': ']',
        '《': '<', '》': '>', '～': '~', '—': '-', '…': '...',
        '·': '.', '‘': "'", '’': "'", '“': '"', '”': '"'
    }
    
    # Step 1: Convert Chinese punctuation to English
    for cn_punc, en_punc in punctuation_map.items():
        text = text.replace(cn_punc, en_punc)
    
    # Step 2: Only keep Chinese characters, English letters, and ASCII characters
    # Chinese Unicode range: \u4e00-\u9fff
    # Basic ASCII range: \x20-\x7e (printable characters)
    text = re.sub(
        r'[^\u4e00-\u9fffa-zA-Z\x20-\x7e]',
        '',
        text
    )
    
    # Original cleaning operations:
    # Replace special whitespace characters
    text = text.replace('\u3000', ' ')  # Chinese full-width space
    text = text.replace('\xa0', ' ')    # Non-breaking space
    
    # Remove control characters (ASCII 0-31 and 127)
    text = re.sub(r'[\x00-\x1f\x7f]', '', text)
    
    # Remove other illegal Unicode characters (keep common printable characters)
    text = re.sub(
        r'[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]', 
        '', 
        text
    )
    
    # Normalize whitespace (merge consecutive whitespace)
    text = re.sub(r'[ \t\r\n\u2002-\u200f]+', ' ', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'[\r\n]+', '\n', text)
    
    return text.strip()

TAN_10 = math.tan(math.radians(10))  # ≈ 0.2679
TAN_80 = math.tan(math.radians(80))

def transform_ocr_results(ocr_data : dict) -> Generator[OCRTextBlock, None, None]:
    texts = ocr_data["rec_texts"]
    boxes = ocr_data["rec_boxes"]
    polys = ocr_data["rec_polys"]
    scores = ocr_data["rec_scores"]
    for txt, box, poly, score in zip(texts, boxes, polys, scores):
        yield OCRTextBlock(
            text = txt, 
            score = score, 
            box = list(map(int, box)), 
            poly = list(list(map(int, poly0)) for poly0 in poly)
        )
        
def collect_ocr_page_info(texts : Iterable[OCRTextBlock]) -> PageSize: 
    page_width = max((text.box[2] for text in texts)) if texts else 0
    page_height = max((text.box[3] for text in texts)) if texts else 0
    
    return PageSize(width= page_width, height= page_height)

def clean_ocr_blocks(texts : Iterable[OCRTextBlock]) -> Iterable[OCRTextBlock]:
    def score_filter(txt : OCRTextBlock):
        return txt.score > 0.9
    
    def poly_filter(txt : OCRTextBlock):
        line_generator = ((txt.poly[i], txt.poly[(i + 1)%len(txt.poly)]) for i in range(len(txt.poly)))
        def line_tan_in_10_80_range(pair):
            pointx, pointy = pair
            if abs( pointx[0] - pointy[0]) < 1e-6:
                return False
            else:
                tan  = abs( (pointx[1] - pointy[1]) / ( pointx[0] - pointy[0]))
                return TAN_10 <= tan and TAN_80 >= tan
        return not any(map(line_tan_in_10_80_range, line_generator))
    
    return list(filter(poly_filter, filter(score_filter, texts)))
    
def manage_ocr_blocks(texts : Iterable[OCRTextBlock], pageinfo: PageSize) -> Iterable[OCRTextBlock]:
    #
    # USE PAGE CONTENT BEFORE FILTER
    if not any(True for _ in texts):
        return []
    
    def maybe_a_titlemark(text : OCRTextBlock):
        return text.box[0] > 1/3 * pageinfo.width and text.box[3] < 1/ 10 * pageinfo.height or text.box[1] > 9/10 * pageinfo.height
    may_a_titlemark = []
    not_a_title_mark_index = set()
    for i, txt in enumerate( texts):
        if maybe_a_titlemark(txt):
            may_a_titlemark.append(txt)
        else: 
            not_a_title_mark_index.add(i)
    def should_not_be_considered_as_a_titlemark(text_and_idx : tuple[int, OCRTextBlock]):
        idx, text = text_and_idx
        if idx in not_a_title_mark_index:
            return True
        def check_in_range(txt_idx : int):
            txt = texts[txt_idx]
            return txt.box[3] > text.box[1] and txt.box[1] < text.box[3]
        return any(True for _ in filter(check_in_range, not_a_title_mark_index))        
    return list(y for _, y in filter(should_not_be_considered_as_a_titlemark, enumerate(texts)))

def filter_ocr_contents(texts : Iterable[OCRTextBlock]) -> Iterable[OCRTextBlock]:
    size = collect_ocr_page_info(texts)
    return manage_ocr_blocks(clean_ocr_blocks(texts), size)
        # manage_ocr_blocks(
            
        # )

TABLE_SPLITTER = "| "
PERCENTAGE_ONE_LINE = 0.5

def flatten_ocr_block(texts : Iterable[OCRTextBlock], splitter = TABLE_SPLITTER) -> Generator[str, None, None]:
    if splitter is None:
        splitter = TABLE_SPLITTER
    if not any(True for _ in texts):
        return 
    textsList = list(texts) 
    textsList.sort(key = lambda x : x.box[1])
    # print(list((x.box[0], x.box[1]) for x in textsList))
    # print(list(x.text for x in textsList))
    if len(textsList) == 0:
        return []
    current_text = None 
    line = ""
    for text in texts:
        if current_text is None:
            current_text = text 
            line += text.text
        elif text.box[1] < (PERCENTAGE_ONE_LINE * current_text.box[3] + (1 - PERCENTAGE_ONE_LINE) * current_text.box[1]):
            line += splitter + text.text
        else:
            yield line
            # 新的一行 嗯
            current_text = text
            line = current_text.text  
    if line:
        yield line

def visualize_ocr_results(ocr_data : Iterable[OCRTextBlock], pagesize : PageSize, image_path = None, output_path = None, font_path = None):
    from PIL import Image, ImageDraw, ImageFont
    # TODO FIXME ocr_data = []
    if len(ocr_data) < 1:
        logger.info("OCR结果为空")
        return
    if image_path:
        img = Image.open(image_path).convert("RGB")
        img_width, img_height = img.size
    else:
        img_width = pagesize.width
        img_height = pagesize.height
        img = Image.new("RGB", (img_width, img_height), (255, 255, 255))

    draw = ImageDraw.Draw(img)

    for i, ocr in enumerate(ocr_data):
        poly = ocr.poly
        score = ocr.score
        poly_int = [(int(x), int(y)) for x, y in poly]
        draw.polygon(poly_int, outline=(0, 200, 0) if score > 0.9 else (255, 0, 0))
        box = ocr.box 
        box_int = [(box[0], box[1]), (box[0], box[3]), (box[2], box[3]), (box[2], box[1])]
        draw.polygon(box_int, outline=(0, 0, 200) if score > 0.9 else (255, 0, 0))
        
        # 在框上方绘制文字和置信度
        # 计算文字框的左上角位置
        min_x = min([p[0] for p in poly])
        min_y = min([p[1] for p in poly])
        text_pos = (min_x, min_y - 25)

        display_text = f"{i}th block: {ocr.text[: 10]} ({score:.2f})"

        text_bbox = draw.textbbox(text_pos, display_text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        if text_pos[1] < 0:
            text_pos = (text_pos[0], min_y + 5)
        
        # 绘制文字背景
        bg_box = [
            text_pos[0] - 2, text_pos[1] - 2,
            text_pos[0] + text_width + 2, text_pos[1] + text_height + 2
        ]
        draw.rectangle(bg_box, fill=(255, 255, 200))

        draw.text(text_pos, display_text, fill=(0, 0, 0))
    
    if output_path is not None:
        img.save(output_path)
        logger.info(f"可视化结果已保存至: {output_path}")
    return img

def visualize_base64_img(b64: str, output_path : str = None):
    try:
        from PIL import Image, ImageDraw, ImageFont
        if b64.startswith('data:image/'):
            b64 = b64.split(',', 1)[1]
        image_data = base64.b64decode(b64)
        img = Image.open(io.BytesIO(image_data))
        if output_path is not None:
            img.save(output_path)
            logger.info(f"图像已保存至: {output_path}")
        return img
    except Exception as e:
        logger.error(f"Error while visualizing Base64 Image: {str(e)}")
        

CACHE_SUFFIX = ".cache"

def save_to_cache(originPath : str, texts : Iterable[str]):
    path = Path(originPath).with_suffix(CACHE_SUFFIX)
    if not os.path.isdir( path.parent):
        os.makedirs(path.parent, exist_ok= True)
    with open(path, "w", encoding= "utf-8") as fp:
        fp.write("\n".join(texts))
        
def is_cache_file(originPath : str):
    return originPath.endswith(CACHE_SUFFIX)
        
def has_cache(orginPath) -> bool :
    return os.path.isfile(Path(orginPath).with_suffix(CACHE_SUFFIX))

def read_cache(originPath : str):
    assert has_cache(originPath)
    with open(Path(originPath).with_suffix(CACHE_SUFFIX), "r", encoding = "utf-8") as fp:
        return fp.readlines()

def remove_cache(originPath : str):
    if has_cache(originPath):
        try:
            os.remove(Path(originPath).with_suffix(CACHE_SUFFIX))
        except Exception as e:
            logger.error(f"Error while removing cache for path {originPath}: {str(e)}")
            
def remove_all_cache(rootpath : str):
    for root, _, files in os.walk(rootpath):
        for file in files: 
            if is_cache_file(file):
                remove_cache(os.path.join(root, file))
    
def remove_cache_of_type(rootpath : str, prefix : str) :
    for root, _, files in os.walk(rootpath):
        for file in files :
            if file.endswith(prefix):
                path = os.path.join(root, file)
                try:
                    os.remove(path)
                except Exception as e:
                    logger.error(f"Error while removing file for path {path}: {str(e)}")