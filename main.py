from data_preprocess_utils.test.test_simularity import test_embedding_simularity, DATA_0, QUERY_0, DATA_1, QUERY_1
from data_preprocess_utils.test.test_ocr import test_ocr_pdf_extractor
from data_preprocess_utils.document_utils import visualize_base64_img
import json

if __name__ == "__main__":
    print("start")
    test_embedding_simularity("http://127.0.0.1:11434", DATA_0, QUERY_0)
    test_embedding_simularity("http://127.0.0.1:11434", DATA_1, QUERY_1)
    #test_ocr_pdf_extractor("./test_data/test_watermark.pdf", ocr_server= "http://127.0.0.1:8083/ocr", no_cache= False)
   