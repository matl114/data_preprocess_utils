from ..document_extractor import Extractor, FileType



def test_ocr_pdf_extractor(file_path : str, ocr_server : str, no_cache : bool):
    content = Extractor().extract(
        filepath = file_path,
        filetype= FileType.PDF,
        use_ocr= True,
        ocr_servce_url= ocr_server,
        no_ocr_cache= no_cache
    )
    print(content)
    with open("./test_result/pdf/text.txt" , encoding="utf-8", mode= "w") as fp:
        fp.write('\n'.join(content))