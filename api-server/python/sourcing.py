import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import sys

def collect_data(url):
    driver = webdriver.Chrome()
    try:
        driver.get(url)
        data = {}
        data['업체상품코드'] = "__AUTO__"
        data['모델명'] = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "fieldset > div h3"))
        ).text
        data['브랜드'] = ""
        # 필요한 추가 데이터 수집
        return data
    finally:
        driver.quit()

def save_to_csv(datas, folder_path):
    current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{folder_path}/product_data_{current_time}.csv"
    fieldnames = [
        '업체상품코드', '모델명', '브랜드', '제조사', '원산지', '상품명', '홍보문구', '요약상품명', 
        '표준산업코드', '카테고리코드', '사용자분류명', '한줄메모', '시중가', '원가', '표준공급가', 
        '판매가', '배송방법', '배송비', '과세여부', '판매수량', '이미지1URL', '이미지2URL', '이미지3URL', 
        '이미지4URL', 'GIF생성', '이미지6URL', '이미지7URL', '이미지8URL', '이미지9URL', '이미지10URL', 
        '추가정보 입력사항', '옵션구분', '선택옵션', '입력형옵션', '추가구매옵션', '상세설명', '추가상세설명', 
        '광고/홍보', '제조일자', '유효일자', '사은품내용', '키워드', '인증구분', '인증정보', '거래처', 
        '영어상품명', '중국어상품명', '일본어상품명', '영어상세설명', '중국어상세설명', '일본어상세설명', 
        '상품무게', '영어키워드', '중국어키워드', '일본어키워드', '생산지국가', '전세계배송코드', '사이즈', 
        '포장방법', '개별카테고리', '상품상세코드', '상품상세1', '상품상세2', '상품상세3', '상품상세4', 
        '상품상세5', '상품상세6', '상품상세7', '상품상세8', '상품상세9', '상품상세10', '상품상세11', 
        '상품상세12', '상품상세13', '상품상세14', '상품상세15', '상품상세16', '상품상세17', '상품상세18', 
        '상품상세19', '상품상세20', '상품상세21', '상품상세22', '상품상세23', '상품상세24', '상품상세25', 
    ]
    # 폴더가 존재하는지 확인하고, 없으면 생성
    os.makedirs(folder_path, exist_ok=True)
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in datas:
            writer.writerow(data)

def main(urls):
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(collect_data, urls))
        print(results)
    save_to_csv(results, 'temp')

if __name__ == '__main__':
    # URL 데이터를 읽고 처리
    urls = sys.stdin.read().strip().split('\n')
    main(urls)


