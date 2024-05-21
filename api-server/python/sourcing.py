import csv
import os
import json
import boto3
import sys
import time
import requests
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from threading import Lock
from urllib.parse import urlparse, unquote
from boto3.s3.transfer import TransferConfig

lock = Lock()

script_dir = os.path.dirname(os.path.abspath(__file__))

# options = Options()
# options.add_argument("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(
    api_key=OPENAI_API_KEY
)

# AWS S3 설정
s3 = boto3.client('s3', region_name='ap-northeast-2', aws_access_key_id=os.environ.get("S3_ACCESS_KEY_ID"), aws_secret_access_key=os.environ.get("S3_SECRET_ACCESS_KEY"))
bucket_name = "idwhat-cdn"
cloudfront_url = "https://d2cbw0xqrrkdri.cloudfront.net"
aws_detail_urls = []
aws_thumbnail_urls = []

def brandnameChanger(query):
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo-0125",
    messages = [
            {"role": "system", "content": "제공된 상품 이름의 단어들을 상점에서 사용되는 동의어로 교체하고, 마지막 두세 단어의 순서를 재배열합니다. 변환된 결과는 모두 한국어로 반환되며, 욕설이나 특수 문자가 포함되지 않아야 합니다."},
            {"role": "user", "content": query}
        ]
    )
    
    return completion.choices[0].message.content
    
def getCategoryCode(driver):
    csv_file_path = os.path.join(os.path.dirname(__file__), 'categories.csv')  # 현재 스크립트와 같은 디렉토리에 있는 categories.csv 파일 경로
    
    try:
        WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "._1_FPHJbv10"))
            ).text
        
        temp_categoryname = driver.find_elements(By.CSS_SELECTOR, "._1_FPHJbv10")
        categoryname = [element.text for element in temp_categoryname]
    except Exception as e:
        print("카테고리 코드를 찾는데 필요한 요소가 시간 내에 로드되지 않았습니다.", e)
        return None
    
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # 공백이 아닌 값들만 필터링하여 리스트를 생성
            filtered_row = [item for item in row[:-1] if item.strip()]
            
            # 주어진 category_list도 동일한 방식으로 공백을 제거
            filtered_category_list = [item for item in categoryname if item.strip()]
            
            # 이제 두 리스트를 문자열로 변환하여 비교
            if ','.join(filtered_row) == ','.join(filtered_category_list):
                return row[-1]  # 일치하는 경우, 마지막 열의 카테고리 코드 반환

    return None  # 일치하는 카테고리가 없으면 None 반환

def getPrice(driver):
    temp_price = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "strong ._1LY7DqCnwR"))
        ).text
        
    price = int(temp_price.replace(',', '')) - 500
    return price
    
def is_video_url(url):
    # URL에서 쿼리 스트링을 제거하고 순수한 파일 이름만 추출합니다.
    parsed_url = urlparse(url)
    path = unquote(parsed_url.path)  # URL 디코딩을 통해 인코딩된 문자 처리
    return path.endswith(('.mp4', '.webm'))

def getThumbnails(driver):
    thumb_arr = []
    try:
        # 썸네일 목록 요소를 찾습니다.
        thumbnail_li = WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".bd_2YVUb li"))
        )
    except Exception as e:
        thumbnail_li = []
        
    if not thumbnail_li:
        try:
            # 썸네일 이미지 요소를 직접 찾습니다.
            thumbnail_img = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".bd_2DO68"))
            )
            thumbnail_src = thumbnail_img.get_attribute("src")
            thumb_arr.append(thumbnail_src)
        except Exception as e:
            print("썸네일 이미지를 가져오는 도중 오류가 발생했습니다.", e)
    else:
        for element in thumbnail_li:
            element.click()  # 각 썸네일을 클릭합니다.
            try:
                # 변경된 썸네일 이미지를 가져옵니다.
                thumbnail_img = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".bd_2DO68"))
                )
                thumbnail_src = thumbnail_img.get_attribute("src")
                thumb_arr.append(thumbnail_src)
            except Exception as e:
                # 비디오 소스 처리
                try:
                    video_src = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".bd_22GJN video"))
                    ).get_attribute("src")
                    thumb_arr.append(video_src)
                except Exception as e:
                    print("비디오 소스를 가져오는 도중 오류가 발생했습니다.", e)
    
    return thumb_arr
        
def getOptions(driver):
    option_type = "[옵션타입]\n"

    # 옵션 버튼 찾기 및 클릭
    option_btn = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".bd_1fhc9"))
    )
    option_btn.click()

    # 옵션 리스트 요소들 찾기
    option_li = WebDriverWait(driver, 3).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".bd_zxkRR li"))
    )

    # 각 옵션에 대한 정보 추출
    for option in option_li:
        text = option.text
        index_of_plus = text.find("(+")

        if index_of_plus != -1:
            s = text.find("(+") + 2
            e = text.find("원")
            sub_text = text[:index_of_plus].strip()
            plus_charge = text[s:e]
            option_text = f"{sub_text}=={plus_charge}"
            option_type += f"{option_text}==999=0=0=0=\n"
        else:
            option_type += f"{text.strip()}==0==999=0=0=0=\n"

    return option_type
        
def getOptionImgAndText(driver):
    option_imgs = []
    option_texts = []
    try:
        # Collect option images
        optionImgs = WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "._3osy73V_eD tbody tr img"))
        )
        
        # Collect option texts
        optionTexts = WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "._3osy73V_eD tbody tr + tr td"))
        )
        
        for img in optionImgs:
            imgSrc = img.get_attribute('data-src')
            option_imgs.append(imgSrc)
        
        # Collecting and filtering non-empty text
        all_texts = [text.get_attribute("textContent").strip() for text in optionTexts]
        option_texts = [text for text in all_texts if text]  # Filters out empty strings

    except Exception as e:
        print("Error fetching option images and texts:", str(e))

    return option_imgs, option_texts
        
def getDetailImg(driver, exclude_imgs):
    detail_imgs_src = []
    try:
        detailImgs = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "._3osy73V_eD ._9F9CWn02VE img"))
        )
        
        # 첫 번째와 마지막 이미지를 제외하기 위해 리스트 슬라이싱 사용
        if len(detailImgs) > 2:  # 첫 번째와 마지막 이미지를 제외할 수 있을 때만 실행
            detailImgs = detailImgs[1:-1]  # 리스트의 첫 번째와 마지막 요소 제외
        
        for img in detailImgs:
            src = img.get_attribute('data-src') or img.get_attribute('src')
            
            if src and (src not in exclude_imgs):
                detail_imgs_src.append(src)

        if not detail_imgs_src:
            print("No valid detail images were found.")
    except Exception as e:
        print(f"Error while fetching detail images: {e}")

    return detail_imgs_src



def download_image(url):
    try:
        time.sleep(1)  # 요청 사이에 간격을 두어 서버 부하를 방지
        response = requests.get(url)
        response.raise_for_status()  # HTTP 요청 실패 시 예외 발생
        image = Image.open(BytesIO(response.content))
        return image
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except IOError as e:
        print(f"Cannot open image: {e}")
    return None


def apply_watermark(image, watermark_url):
    """이미지에 워터마크를 추가합니다."""
    response = requests.get(watermark_url)
    watermark = Image.open(BytesIO(response.content))
    watermark = watermark.convert("RGBA")  # 워터마크를 RGBA로 변환하여 투명도 유지

    # 워터마크의 크기를 이미지 높이의 10분의 1로 조정
    watermark_scale_height = image.height // 10
    scale_factor = watermark_scale_height / watermark.height
    watermark = watermark.resize((int(watermark.width * scale_factor), int(watermark.height * scale_factor)), Image.Resampling.LANCZOS)

    # 워터마크 투명도 설정 (50%)
    new_data = []
    for item in watermark.getdata():
        new_data.append((item[0], item[1], item[2], int(item[3] * 0.5)))  # 투명도를 50%로 조정
    watermark.putdata(new_data)

    # 워터마크 위치 계산 (이미지의 정 중앙)
    watermark_position = ((image.width - watermark.width) // 2, (image.height - watermark.height) // 2)

    # 원본 이미지가 RGBA 포맷이 아니면 RGBA로 변환
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    combined = Image.alpha_composite(image, Image.new('RGBA', image.size, (0, 0, 0, 0)))
    combined.paste(watermark, watermark_position, watermark)  # 워터마크를 결합

    return combined.convert('RGB')  # 최종 이미지를 RGB로 변환하여 반환

def upload_to_s3(image, bucket, key):
    """이미지 객체를 S3 버킷에 업로드"""
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    s3.upload_fileobj(BytesIO(img_byte_arr), bucket, key, ExtraArgs={'ContentType': 'image/jpeg'})
        
def create_html(aws_option_urls, aws_detail_urls, option_texts):
    # 옵션 이미지와 텍스트를 사용하여 HTML 구성
    option_inner_html = ""
    for i, url in enumerate(aws_option_urls):
        option_inner_html += f'<div style="display: inline-table; width: 50%; border: 1px solid #aaa; margin: 30px 0 0 0; box-sizing: border-box;"><img src="{url}" width="390"/><div style="display: block; border-top: 1px solid #aaa; padding: 15px; font-size: 15pt; box-sizing: border-box;">{option_texts[i]}</div></div>'

    # 상세 이미지를 사용하여 HTML 구성
    detail_inner_html = ""
    for url in aws_detail_urls:
        detail_inner_html += f'<div><img src="{url}" /></div>'

    # 전체 HTML 구성
    if aws_option_urls:
        detail_html = f'<div style="margin: 0 auto; width: 100%; text-align: center"><img src="https://dfua3zgxja7ca.cloudfront.net/common/option.jpg" /><div style="display: block; align-items: center; width: 100%; font-size: 0">{option_inner_html}</div><div style="text-align: center; margin-top: 30px">{detail_inner_html}</div></div>'
    else:
        detail_html = f'<div style="margin: 0 auto; width: 100%; text-align: center"><div style="text-align: center; margin-top: 30px">{detail_inner_html}</div></div>'

    return detail_html

def process_and_upload_images(thumbnails, optionUrls, detailUrls, watermark_url, bucket, user_id, cloudfront_url, aws_option_urls, aws_detail_urls):
    # 각 URL 종류별로 처리
    url_sets = {
        "Thumbnails": thumbnails,
        "Option URLs": optionUrls,
        "Detail URLs": detailUrls
    }

    for name, urls in url_sets.items():
        if not urls:
            print(f"No URLs to process in {name}")
            continue
        
        for url in urls:
            # 이미지 파일 처리 로직
            image = download_image(url)
            if image is None:
                print(f"Skipping {url} due to download or open error.")
                continue
            
            if name != "Thumbnails":
                if image.mode == 'RGBA':
                    image = image.convert('RGB')  # RGBA를 RGB로 변환
                image = apply_watermark(image, watermark_url)
            
            key = f'{user_id}/{datetime.now().strftime("%Y%m%d%H%M%S%f")}.jpg'
            upload_to_s3(image, bucket, key)  # 여기에서 image 객체를 전달
            
            # 결과 URL을 적절한 리스트에 추가
            if name == "Option URLs":
                aws_option_urls.append(f"{cloudfront_url}/{key}")
            elif name == "Detail URLs":
                aws_detail_urls.append(f"{cloudfront_url}/{key}")
            else:
                aws_thumbnail_urls.append(f"{cloudfront_url}/{key}")


    print(f"Completed processing with results - Options: {aws_option_urls}, Details: {aws_detail_urls}, Thumbnails: {aws_thumbnail_urls}")

def collect_data(driver, url):
    user_info = json.loads(sys.argv[1])
    
    try:
        driver.get(url)
        data = {}
        data['업체상품코드'] = "__AUTO__"
        
        temp_modelname = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "fieldset > div h3"))
        ).text
        
        modelname = brandnameChanger(temp_modelname) # 동의어 변환
        
        data['모델명'] = modelname
        data['브랜드'] = user_info["brandname"] + " 협력사"
        data['제조사'] = user_info["brandname"] + " 협력사"
        data['원산지'] = "해외=아시아=중국"
        data['상품명'] = modelname
        data['요약상품명'] = modelname
        data['카테고리코드'] = getCategoryCode(driver)
        data['시중가'] = 0
        data['원가'] = 0
        data['표준공급가'] = 0
        data['판매가'] = getPrice(driver)
        data['배송방법'] = "무료"
        data['배송비'] = 0
        data['과세여부'] = "Y"
        data['판매수량'] = 999
        thumbnails = getThumbnails(driver)
            
        data['옵션구분'] = "SM"
        data['선택옵션'] = getOptions(driver)
        
        
        userid = user_info["userid"]
        usermobile = user_info["mobile"]
        watermark_url = f'{cloudfront_url}/{userid}/common/watermark.png'
        option_imgs, option_texts =  getOptionImgAndText(driver)
        aws_option_urls = []
        image_urls = getDetailImg(driver,option_imgs)
            
        process_and_upload_images(thumbnails, option_imgs, image_urls, watermark_url, bucket_name, userid, cloudfront_url, aws_option_urls, aws_detail_urls)
        html_content = create_html(aws_option_urls, aws_detail_urls, option_texts)
        
        # 비디오 URL을 저장할 변수
        video_url = None
        # 이미지 URL만 저장하고, 비디오 URL이 있으면 따로 저장
        for i in range(min(4, len(aws_thumbnail_urls))):  # 최대 5개의 썸네일을 처리
            if is_video_url(aws_thumbnail_urls[i]):
                video_url = aws_thumbnail_urls[i]  # 비디오 URL을 저장
            else:
                data[f'이미지{i+1}URL'] = aws_thumbnail_urls[i]

        # 비디오 URL이 있다면 데이터 딕셔너리의 마지막에 추가
        if video_url:
            data[f'이미지{min(4, len(aws_thumbnail_urls))+1}URL'] = video_url
            
        data['인증구분'] = "B"
        data['상품무게'] = 0
        data['포장방법'] = "봉투"
        data['상품상세코드'] = 35
        data['상품상세1'] = "상세설명참조"
        data['상품상세2'] = "상세설명참조"
        data['상품상세3'] = "해당사항 없음"
        data['상품상세4'] = "중국"
        data['상품상세5'] = "상세설명참조"
        data['상품상세6'] = "Y"
        data['상품상세7'] = "상세설명참조"
        data['상품상세8'] = usermobile
        data['상세설명'] = html_content
        
        # print(data)
        return data
    finally:
        print(f"{url} 완료")

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    return driver

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
    driver = setup_driver()
    
    try:
        for url in urls:
            result = collect_data(driver, url)
            results.append(result)
    finally:
        driver.quit()  # 모든 작업이 완료된 후 드라이버 종료
        
    save_to_csv(results, 'temp')

if __name__ == '__main__':
    # URL 데이터를 읽고 처리
    # urls = ["https://smartstore.naver.com/ttokalmall/products/9657042387"]
    urls = sys.stdin.read().strip().split('\n')
    main(urls)


