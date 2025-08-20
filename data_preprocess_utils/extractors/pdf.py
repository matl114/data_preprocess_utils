from .base import BaseExtractor
import pypdfium2 
from ..document_utils import flatten_raw_texts, transform_ocr_results, filter_ocr_contents, flatten_ocr_block, visualize_ocr_results, collect_ocr_page_info
from typing import *
import base64
import requests
from ..core.data_models import OCRContent, OCRTextBlock
from pathlib import Path
import json
import os
import traceback

class PdfExtractor(BaseExtractor) :
    @override
    def extract(self, 
                filepath : str, 
                line_splitter = None,
                use_ocr : bool = False, 
                no_ocr_cache : bool = False, 
                min_len_per_page : int = 10,
                min_len : int = 50,
                ocr_servce_url : str = None, 
                ** kwargs) -> Iterable[str]:

        try:
            if not use_ocr:
                try:
                    pdf_reader = pypdfium2.PdfDocument(filepath, autoclose=True)
                    def stream_pdf(pdf_reader : pypdfium2.PdfDocument):
                        for page_number, page in enumerate(pdf_reader):
                            text_page = page.get_textpage()
                            content = text_page.get_text_bounded()
                            text_page.close()
                            page.close()
                            yield content
                    ls_cleaned = list(flatten_raw_texts(stream_pdf(pdf_reader)))
                    if self.check_valid_pdf(ls_cleaned, min_len_per_page, min_len):
                        return ls_cleaned
                    else:
                        self.logger.error("Invalid Pdf content readed by PyPdfium")
                finally:
                    pdf_reader.close()
            self.logger.error("Using OCR server...")
            return self.extract_via_ocr_server(
                filepath, 
                no_cache= no_ocr_cache,
                ocr_servce_url= ocr_servce_url, 
                line_splitter= line_splitter,
                ** kwargs
            )
        except Exception as e:
            self.logger.error(f"Error loading pdf file {filepath} : {str(e)}")
            traceback.print_exc()
            return None
            
    def extract_via_ocr_server(self, path, no_cache, ocr_servce_url, line_splitter,  ** kwargs) -> Iterable[str]:
        if ocr_servce_url is not None:
            try:
                ocr : OCRContent = None
                # cached_file_path = Path( str(Path(path).with_suffix("")) + "_ocr_result_cache.json_cache")
                cached_tmp_path =  Path( str(Path(path).with_suffix("")) + "_ocr_result_cache.json_cache")
                # use cache first
                # if not no_cache:
                #     if os.path.exists(cached_file_path):
                #         try:
                #             with open(cached_file_path, mode= "r", encoding= "utf-8") as fp :
                #                 data = json.load(fp)
                #                 ocr = OCRContent.model_validate(data)
                #         except Exception as e:
                #             self.logger.error("Corrupted ocr result cache file! Generating new cache...")
                #             self.logger.error(e)
                #             os.remove(cached_file_path)
                # # if cache invalid, request for ocr
                if not no_cache and os.path.exists(cached_tmp_path):
                    with open(cached_tmp_path, mode="r", encoding= "utf-8")as fp:
                        result = json.load(fp)
                else:
                    with open(path, "rb") as fp:
                        byte = fp.read()
                    b64 = base64.b64encode(byte)
                    response = requests.post(ocr_servce_url, json = {"file": str(b64, encoding= "utf-8"), "fileType": 0})
                    response.raise_for_status()
                    result = response.json()["result"]
               
                    if not no_cache:
                        compressed_result = {
                            "ocrResults" :  [{"prunedResult" : res["prunedResult"]} for res in result["ocrResults"]]
                        }
                    # only keep prunedResult
                        with open(cached_tmp_path, mode= "w", encoding="utf-8") as fp:
                            json.dump(compressed_result, fp)
                
                ocr_result = result["ocrResults"]
                ocr_pages : list[list[OCRTextBlock]] = []
                for i, ocr_page_result in enumerate(ocr_result):
                    ocrtextblock = list(transform_ocr_results(ocr_page_result["prunedResult"]))
                    # pageinfo = collect_ocr_page_info(ocrtextblock)
                    # if i == 7:
                    #     print(ocrtextblock)
                    # visualize_ocr_results(ocrtextblock, pagesize= pageinfo, output_path = f"./test_result/pdf/page_{i}.png")
                    results = list(filter_ocr_contents(ocrtextblock))
                    # visualize_ocr_results(results, pagesize= pageinfo, output_path=f"./test_result/pdf/page_filtered_{i}.png")
                    ocr_pages.append(results)
                ocr = OCRContent(type= "pdf", pages = ocr_pages)
                assert ocr is not None
                return list(flatten_raw_texts(sum([list(flatten_ocr_block(ocr_page, splitter = line_splitter)) for ocr_page in ocr.pages], [])))
            except Exception as e:
                self.logger.error(f"Error loading pdf file {path}: {str(e)}")
                traceback.print_exc()
        else:
            self.logger.error("OCR Server config absent!")
            return None
    
    def check_valid_pdf(self, cleaned : Iterable[str], minimal_in_page : int, minimal_all_unique : int) -> bool:
        cnt = 0
        all_set = set()
        for cl in cleaned :
            if len(cl) < minimal_in_page:
                # 最多首末
                cnt += 1
                if cnt > 2 :
                    return False
            else:
                all_set.add(cl)
        all_len = sum(map(len, all_set))
        return all_len > minimal_all_unique
                
                
