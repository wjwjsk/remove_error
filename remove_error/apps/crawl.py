from pathlib import Path
import openai
import requests, subprocess, re, datetime, time, concurrent.futures, json
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import psycopg2

# from datetime import datetime


crl_page = 1


BASE_DIR = Path(__file__).resolve().parent.parent
with open("c:/Users/Park/Desktop/oreumi/project/remove_error/remove_error/config.json") as f:
    json_object = json.load(f)


# PostgreSQL 데이터베이스에 연결
conn = psycopg2.connect(
    dbname=json_object["DATABASES"]["NAME"],
    user=json_object["DATABASES"]["USER"],
    password=json_object["DATABASES"]["PASSWORD"],
    host=json_object["DATABASES"]["HOST"],
    port=5432,
)

cursor = conn.cursor()

#     # OpenAI API 키 설정
openai.api_key = json_object["OPENAI_API_KEY"]


# HTML 페이지 soup에 담기
def insert_soup(url):
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    return soup


def txt_write(url):
    soup = insert_soup(url)
    with open("page_html.txt", "w", encoding="utf-8") as file:
        file.write(soup.prettify())
    subprocess.run(["start", "page_html.txt"], shell=True)  # Windows


def json_write(data):
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    with open("page_data.json", "w", encoding="utf-8") as file:
        file.write(json_data)
    subprocess.run(["start", "page_data.json"], shell=True)  # Windows
    # subprocess.run(["open", "page_data.json"])  # macOS


# fmkorea(aws요청거부)
# 10페이지
def fm_crawling_function():
    home = "https://www.fmkorea.com"
    datas = [[] for _ in range(crl_page)]
    for page in range(0, crl_page):
        soup = insert_soup(home + "/index?mid=hotdeal&page=" + str(page + 1))
        list_tags = soup.select("div.fm_best_widget > ul > li")
        # 게시판 링크+제목+금액+배송비+시간
        for link in list_tags:
            href = link.select_one(".li h3 a")["href"]
            bf_title = "".join(
                link.select_one(".li h3 a").find_all(string=True, recursive=False)
            ).strip()
            title = re.sub(r"[\xa0\t]", "", bf_title)
            info_texts = [a.text for a in link.select(".hotdeal_info span a")[1:3]]
            category = link.select_one("div .category a").text
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            # 게시글 내부 이미지
            in_soup = insert_soup("https://www.fmkorea.com" + href)
            shop_url = in_soup.select_one("tr td .xe_content a").text

            desc_div = in_soup.select_one("div article div")
            image_src_str = ""
            div_a_tags = desc_div.select("div > img, p > img")
            for tag in div_a_tags:
                src = tag["src"]
                image_src_str += src + "<br>"

            if "hotdeal_var8Y" in link.select_one(".li h3 a")["class"]:
                is_end_deal = True
            else:
                is_end_deal = False

            datas[page].append(
                {
                    "board_url": home + href,
                    "item_name": title,
                    "end_url": shop_url,
                    "clr_update_time": formatted_time,
                    "board_price": info_texts[0],
                    "board_description": image_src_str,
                    "delivery_price": info_texts[1],
                    "is_end_deal": is_end_deal,
                    "category": category,
                }
            )

        time.sleep(0.5)

    return datas


# ppomppu(selenium)
# 미사용
def pp_crawling_function():
    home = "https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu"
    datas = [[] for _ in range(crl_page)]

    def process_page(page):
        soup = insert_soup(home + "&page=" + str(page + 1))
        list_tags = soup.select("tr.common-list0, tr.common-list1")[:20]  # 리스트 개수 = 20
        # 게시판 링크+제목+금액+배송비+시간
        for link in list_tags:
            bf_board_id = link.select_one("td").text
            board_id = "".join(re.findall(r"\d+", bf_board_id))
            href = "&no=" + board_id

            # Selenium으로 웹 페이지 열기
            options = Options()
            options.add_argument("--headless")  # 브라우저를 표시하지 않고 백그라운드에서 실행
            driver = webdriver.Chrome(options=options)
            driver.get(home + href)

            # Selenium으로 스크립트 로드될 때까지 대기
            wait = WebDriverWait(driver, 3)
            try:
                element = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".board-contents"))
                )
                # 요소가 표시된 후에 수행할 작업
            except TimeoutException:
                # 대기 시간 초과 예외 처리
                print(f"대기 시간 초과: {board_id}가 표시되지 않았습니다.")
                # 적절한 조치를 취하거나 예외를 다시 발생시킬 수 있음
            except Exception as e:
                # 다른 예외 처리
                print("오류 발생:", str(e))
                # 적절한 조치를 취하거나 예외를 다시 발생시킬 수 있음

            # 스크립트 로드된 후의 HTML 가져오기
            html = driver.page_source

            in_soup = BeautifulSoup(html, "html.parser")
            bf_title = "".join(
                in_soup.select_one(".view_title2").find_all(string=True, recursive=False)
            ).strip()
            title = re.sub(r"(DCM_TITLE\s*|/DCM_TITLE)", "", bf_title)  # 제목
            # title = re.sub(r'[\xa0\t]', '', bf_title)
            # info_texts = [a.text for a in link.select('.hotdeal_info span a')[1:3]] # 금액+배송비
            shop_url = in_soup.select_one("div .wordfix a").text
            category = in_soup.select_one("div .view_cate").text
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            # 게시글 내부 이미지
            desc_div = in_soup.select_one("tr .board-contents")
            image_src_str = ""
            div_a_tags = desc_div.select("p img")
            filtered_tags = [
                tag
                for tag in div_a_tags
                if len(tag["src"]) <= 450 and "clickWideIcon" not in tag.get("class", [])
            ]
            for tag in filtered_tags:
                src = tag["src"]
                image_src_str += src + "<br>"

            div_tags = in_soup.select("div")
            has_top_cmt = any(tag for tag in div_tags if "top_cmt" in tag.get("class", []))

            if has_top_cmt:
                is_end_deal = True
            else:
                is_end_deal = False

            datas[page].append(
                {
                    "board_url": home + href,
                    "item_name": title,
                    "end_url": shop_url,
                    "clr_update_time": formatted_time,
                    "board_description": image_src_str,
                    "is_end_deal": is_end_deal,
                    "category": category,
                }
            )
        # 한페이지 마다 Selenium 세션 종료
        driver.quit()

    # 병렬 처리를 위해 ThreadPoolExecutor 사용
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(process_page, range(0, crl_page))

    return datas


# quasarzone
# 5페이지 이하만 사용(aws 요청시 페이지당 3초 이상 소요)
def qz_crawling_function():
    home = "https://quasarzone.com"
    datas = [[] for _ in range(int(crl_page / 2))]
    for page in range(0, int(crl_page / 2)):
        soup = insert_soup(home + "/bbs/qb_saleinfo?page=" + str(page + 1))
        list_tags = soup.select("table tbody tr")
        # 게시판 링크+제목+금액+배송비+시간
        for link in list_tags:
            fa_lock = link.select_one(".fa-lock")
            if fa_lock is None or fa_lock.text not in "블라인드":
                href = link.select_one(".market-info-list p a")["href"]
                time.sleep(3)
                in_soup = insert_soup(home + href)
                temp = in_soup.select_one("dl dt .title")
                if temp is not None:
                    bf_title = "".join(temp.text).strip()
                    title = re.sub(r"^[^\[]*(\[[^\]]+\]\s*)", "", bf_title, count=1)
                    shop_url = in_soup.select_one(".market-info-view-table tr td a").text
                    board_price = in_soup.select_one(".market-info-view-table tr td span").text
                    tr = in_soup.find("th", string=re.compile("배송비"))
                    delivery_price = tr.find_next_sibling("td").get_text()
                    category = "".join(
                        in_soup.select_one(".left .ca_name").find_all(string=True, recursive=False)
                    ).strip()
                    bf_find_item_time = in_soup.select_one(".right .date").text
                    find_item_time = re.sub(
                        r"(\d{4})[.-](\d{2})[.-](\d{2}) (\d{2}):(\d{2}):(\d{2})",
                        r"\1-\2-\3 \4:\5",
                        bf_find_item_time,
                    ).replace(".", "-")
                    current_time = datetime.datetime.now()
                    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                    # 게시글 이미지

                    image_src_str = link.select_one(".market-info-list .maxImg")["src"]

                    if "label done" in in_soup.select_one("div .title span")["class"]:
                        is_end_deal = True
                    else:
                        is_end_deal = False
            else:
                is_end_deal = True
                href = link.select_one(".market-info-list p a")["href"]
                title = "블라인드 게시글"
                shop_url = "블라인드 게시글"
                formatted_time = "블라인드 게시글"
                current_time = datetime.datetime.now()
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                find_item_time = "블라인드 게시글"
                board_price = "블라인드 게시글"
                image_src_str = "블라인드 게시글"
                delivery_price = "블라인드 게시글"
                category = "블라인드 게시글"

            datas[page].append(
                {
                    "board_url": home + href,
                    "item_name": title,
                    "end_url": shop_url,
                    "clr_update_time": formatted_time,
                    "find_item_time": find_item_time,
                    "board_price": board_price,
                    "board_description": image_src_str,
                    "delivery_price": delivery_price,
                    "is_end_deal": is_end_deal,
                    "category": category,
                }
            )

    return datas


# arcalive
# 10페이지
def al_crawling_function():
    home = "https://arca.live"
    datas = [[] for _ in range(crl_page)]
    for page in range(0, crl_page):
        soup = insert_soup(home + "/b/hotdeal?p=" + str(page + 1))
        list_tags = soup.select(".article-list .list-table.hybrid .vrow.hybrid")
        # 게시판 링크+제목+금액+배송비+시간
        for link in list_tags:
            href = link.select_one(".title.hybrid-title")["href"]
            in_soup = insert_soup(home + href)
            category = in_soup.select_one(".badge.badge-success.category-badge").text
            shop_url = in_soup.select_one("table tbody > tr:nth-child(1) > td:nth-child(2) a").text
            bf_title = in_soup.select_one(
                "table tbody > tr:nth-child(3) > td:nth-child(2) span"
            ).text
            title = re.sub(r"\[[^\]]+\]\s*", "", bf_title.strip(), count=1)
            bf_find_item_time = in_soup.select_one(".info-row .date time").text
            find_item_time = re.sub(
                r"(\d{4})[.-](\d{2})[.-](\d{2}) (\d{2}):(\d{2}):(\d{2})",
                r"\1-\2-\3 \4:\5",
                bf_find_item_time,
            ).replace(".", "-")
            board_price = in_soup.select_one(
                "table tbody > tr:nth-child(4) > td:nth-child(2) span"
            ).text.strip()
            delivery_price = in_soup.select_one(
                "table tbody > tr:nth-child(5) > td:nth-child(2) span"
            ).text.strip()
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            # 게시글 이미지
            image_src_str = ""
            div_src_str = in_soup.select(".fr-view.article-content p img")
            for tag in div_src_str:
                src = tag["src"]
                image_src_str += src + "<br>"

            if "close-deal" in in_soup.select_one(".title-row .title")["class"]:
                is_end_deal = True
            else:
                is_end_deal = False

            datas[page].append(
                {
                    "board_url": home + href,
                    "item_name": title,
                    "end_url": shop_url,
                    "clr_update_time": formatted_time,
                    "find_item_time": find_item_time,
                    "board_price": board_price,
                    "board_description": image_src_str,
                    "delivery_price": delivery_price,
                    "is_end_deal": is_end_deal,
                    "category": category,
                }
            )

        time.sleep(0.5)

    return datas


# coolenjoy
# 10페이지
def ce_crawling_function():
    home = "https://coolenjoy.net"
    datas = [[] for _ in range(crl_page)]
    for page in range(0, crl_page):
        soup = insert_soup(home + "/bbs/jirum?page=" + str(page + 1))
        list_tags = soup.select(".na-table.d-md-table.w-100 li")
        # 게시판 링크+제목+금액+배송비+시간
        for link in list_tags:
            blind = link.select_one(".na-item a")
            if (
                blind is None or not any(filter(lambda word: word == "블라인드", blind.text.split()))
            ) and link.select_one(".fa-lock") is None:
                href = link.select_one(".na-subject")["href"]
                category = link.select_one("#abcd").text
                board_price = link.select_one("div:nth-child(3) font").text
                in_soup = insert_soup(href)
                bf_shop_url = re.findall(
                    r"(https?://[^\s]+)",
                    in_soup.select_one(".d-flex.my-1 > .pl-3.flex-grow-1.text-break-all a").text,
                )
                shop_url = bf_shop_url[0]

                bf_title = in_soup.select_one("h1#bo_v_title").text.split()
                title = " ".join(bf_title[4:])
                bf_find_item_time = in_soup.select_one(".d-flex.align-items-center li time").text
                find_item_time = re.sub(
                    r"(\d{4})[.-](\d{2})[.-](\d{2}) (\d{2}):(\d{2}):(\d{2})",
                    r"\1-\2-\3 \4:\5",
                    bf_find_item_time,
                ).replace(".", "-")
                current_time = datetime.datetime.now()
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                # 게시글 이미지
                image_src_str = ""
                div_src_str = in_soup.select(
                    ".view-content.fr-view p img, .view-content.fr-view a img"
                )
                for tag in div_src_str:
                    src = tag["src"]
                    image_src_str += src + "<br>"

                if "종료된" in in_soup.select_one("#bo_v_atc b").text.split():
                    is_end_deal = True
                else:
                    is_end_deal = False
            else:
                is_end_deal = True
                href = link.select_one(".na-subject")["href"]
                title = "블라인드 게시글"
                shop_url = "블라인드 게시글"
                find_item_time = "블라인드 게시글"
                current_time = datetime.datetime.now()
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                board_price = "블라인드 게시글"
                image_src_str = "블라인드 게시글"
                category = "블라인드 게시글"

            datas[page].append(
                {
                    "board_url": href,
                    "item_name": title,
                    "end_url": shop_url,
                    "clr_update_time": formatted_time,
                    "find_item_time": find_item_time,
                    "board_price": board_price,
                    "board_description": image_src_str,
                    "delivery_price": "본문참조",
                    "is_end_deal": is_end_deal,
                    "category": category,
                }
            )

            time.sleep(0.5)

    return datas


# clien
# 해외 제외 2페이지만
def cl_crawling_function():
    home = "https://www.clien.net"
    crl_page = 2
    datas = [[] for _ in range(crl_page)]

    for page in range(0, crl_page):
        soup = insert_soup(f"{home}/service/board/jirum?&od=T31&category=1000236&po={page}")
        list_tags = soup.select("div.contents_jirum .list_item.symph_row")
        for link in list_tags:
            subject_tag = link.select_one(".list_title span a")
            href = subject_tag["href"]
            title = subject_tag.text.strip()
            if link.select_one(".icon_info"):
                is_end_deal = True
            else:
                is_end_deal = False
            in_soup = insert_soup(home + href)
            bf_find_item_time = in_soup.select_one(".post_view .post_author span").text.rsplit("수정일 : ")[-1]
            find_item_time = re.sub(
                r"(\d{4})[.-](\d{2})[.-](\d{2}) (\d{2}):(\d{2}):(\d{2})",
                r"\1-\2-\3 \4:\5",
                bf_find_item_time,
            ).strip().replace(".", "-")
            outlink = in_soup.select_one(".outlink .url")
            if outlink is not None and outlink.text:
                shop_url = in_soup.select_one(".outlink .url").text
            else:
                shop_url = ""
                is_end_deal = True
            image_src_str = ""
            img_tag = in_soup.select(".post_article p img")
            for tag in img_tag:
                src = tag["src"]
                if src.split("?")[-1] == "w=230&h=150":
                    src = src.split("?")[0] + "?scale=width[740],options[limit]"
                    image_src_str += src + "<br>"
                else:
                    image_src_str += src + "<br>"
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

            datas[page].append(
                {
                    "board_url": home + href,
                    "item_name": title,
                    "end_url": shop_url,
                    "find_item_time": find_item_time,
                    "clr_update_time": formatted_time,
                    "board_price": "본문참조",
                    "board_description": image_src_str,
                    "delivery_price": "본문참조",
                    "is_end_deal": is_end_deal,
                    "category": "기타",
                }
            )

    return datas


## 해당url html 확인
# url = "https://www.clien.net/service/board/jirum/18377759?od=T31&po=0&category=1000236&groupCd="
# txt_write(url)


## 크롤링 데이터확인
# json_write(pp_crawling_function())

# response = requests.get("https://m.fmkorea.com")
# print(response)


def categorize_deals(category, item_name):
    if category in [
        "PC제품",
        "가전제품",
        "컴퓨터",
        "디지털",
        "PC/하드웨어",
        "노트북/모바일",
        "가전/TV",
        "전자제품",
        "PC관련",
        "가전",
    ]:
        return 6

    elif category in ["의류", "의류/잡화", "패션/의류", "의류잡화"]:
        return 7

    elif category in ["먹거리", "식품/건강", "생활/식품", "식품"]:
        return 8

    elif category in ["생활용품", "가전/가구"]:
        return 9

    elif category in [
        "패키지/이용권",
        "상품권",
        "세일정보",
        "모바일/상품권",
        "상품권/쿠폰",
        "이벤트",
        "쿠폰",
    ]:
        return 10

    elif category in ["화장품"]:
        return 11

    elif category in ["SW/게임", "등산/캠핑", "게임/SW", "게임"]:
        return 12

    elif category in ["기타", "해외핫딜", "인터넷", "모바일"]:
        product_title = item_name

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": f"이 상품의 주요 카테고리는 무엇인가요? 전자제품 및 가전제품, 의류 및 패션 ,식품 및 식료품,홈 및 가든,할인 및 상품권,뷰티 및 화장품,스포츠 및 액티비티,기타 중 하나를 정확하고 최대한 짧게 카테고리 자체만 대답하세요. {product_title}은(는) ",
                },
            ],
        )

        category_ai = response["choices"][0]["message"]["content"].strip()
        # 사전에 정의된 카테고리 목록
        predefined_categories = [
            "전자제품 및 가전제품",
            "의류 및 패션",
            "식품 및 식료품",
            "홈 및 가든",
            "할인 및 상품권",
            "뷰티 및 화장품",
            "스포츠 및 액티비티",
        ]

        category_id_mapping = {
            "전자제품 및 가전제품": 6,
            "의류 및 패션": 7,
            "식품 및 식료품": 8,
            "홈 및 가든": 9,
            "할인 및 상품권": 10,
            "뷰티 및 화장품": 11,
            "스포츠 및 액티비티": 12,
        }

        for cate in predefined_categories:
            if cate.strip() in category_ai.strip() or category_ai.strip() in cate.strip():
                return category_id_mapping[cate]

        # 미리 정의된 카테고리 목록 또는 category_ai에 없는 경우 "기타" 카테고리 반환
        time.sleep(1)
        return 13

    return 13


def insert_data(result):
    # 크롤링 수행 및 추가된 레코드 수 카운트
    current_time = datetime.datetime.now()

    count = 0
    mod_count = 0
    transposed_result = list(zip(*result))
    for column in transposed_result:
        for data in column:
            board_url = data.get("board_url", "")
            end_url = data.get("end_url", "")

            # 추가된 부분: 길이 검사
            if len(board_url) > 500 or len(end_url) > 500:
                continue  # 500자가 넘으면 저장하지 않음

            sql_data = {"item_name": data["item_name"], "end_url": data["end_url"]}
            # SQL 쿼리문
            sql_query = """
            SELECT 1 
            FROM "Items" 
            WHERE item_name = %(item_name)s OR end_url = %(end_url)s
            """

            # 쿼리 실행
            cursor.execute(sql_query, sql_data)
            result = cursor.fetchone()

            if not result:
                if data["is_end_deal"] == False:
                    # 첫 번째 단어 추출
                    first_word = data["item_name"].split()[0]

                    # 링크에서 "//"와 "/" 사이 부분 추출
                    link_part = re.search(r"\/\/(.*?)\/", data["end_url"])
                    if link_part:
                        extracted_url = link_part.group(1)
                    else:
                        extracted_url = data["end_url"]

                    sql_data = {
                        "first_word": first_word,
                        "extracted_url": extracted_url,
                        "board_price": data["board_price"],
                    }

                    # SQL 쿼리문
                    sql_query = """
                    SELECT 1 
                    FROM "Items" 
                    WHERE 
                        item_name LIKE '%%' || %(first_word)s || '%%'
                        AND end_url LIKE '%%' || %(extracted_url)s || '%%'
                        AND board_price = %(board_price)s
                    """
                    # 쿼리 실행
                    cursor.execute(sql_query, sql_data)
                    query_result = cursor.fetchone()

                    if not query_result:
                        sql_data = {
                            "item_name": data["item_name"],
                            "end_url": data["end_url"],
                            "board_url": data["board_url"],
                            "clr_update_time": current_time,
                            "find_item_time": data["find_item_time"],
                            "board_price": data["board_price"][:30],
                            "board_description": data["board_description"],
                            "delivery_price": data["delivery_price"][:30],
                            "is_end_deal": data["is_end_deal"],
                            "category": categorize_deals(data["category"], data["item_name"]),
                            "find_item_time": current_time,
                            "first_price": "",
                        }

                        # SQL 쿼리문
                        sql_query = """
                        INSERT INTO "Items" (item_name, end_url, board_url, clr_update_time, find_item_time, board_price, board_description, delivery_price, is_end_deal, category_id, first_price)
                        VALUES (%(item_name)s, %(end_url)s, %(board_url)s, %(clr_update_time)s, %(find_item_time)s ,%(board_price)s, %(board_description)s, %(delivery_price)s, %(is_end_deal)s, %(category)s, %(first_price)s)
                        """

                        # 쿼리 실행
                        cursor.execute(sql_query, sql_data)
                        count += 1

            else:
                # SQL 쿼리문
                sql_update_query = """
                    UPDATE "Items" 
                    SET board_url = %(board_url)s,
                        clr_update_time = %(clr_update_time)s,
                        find_item_time = %(find_item_time)s,
                        board_price = %(board_price)s,
                        board_description = %(board_description)s,
                        delivery_price = %(delivery_price)s,
                        is_end_deal = %(is_end_deal)s
                    WHERE item_name = %(item_name)s OR end_url = %(end_url)s
                """

                # SQL 쿼리에 사용될 데이터
                sql_update_data = {
                    "board_url": data["board_url"],
                    "clr_update_time": current_time,
                    "find_item_time": data["find_item_time"],
                    "board_price": data["board_price"][:30],
                    "board_description": data["board_description"],
                    "delivery_price": data["delivery_price"][:30],
                    "is_end_deal": data["is_end_deal"],
                    "item_name": data["item_name"],
                    "end_url": data["end_url"],
                }

                # 쿼리 실행
                cursor.execute(sql_update_query, sql_update_data)
                # 변경 사항 커밋
                conn.commit()
                mod_count += 1

    print(f" 새로운 데이터 : {count}")
    print(f" 업데이트 데이터 : {mod_count}")


def crawling():
    # print("fm 시작")
    # start_time_fm = time.time()  # fm 작업 시작 시간 기록
    # insert_data(fm_crawling_function())
    # end_time_fm = time.time()  # fm 작업 종료 시간 기록
    # elapsed_time_fm = end_time_fm - start_time_fm  # fm 작업 소요 시간 계산
    # print(f"fm 작업 완료. 소요 시간: {elapsed_time_fm:.2f} 초")

    # print("qz 시작")
    # start_time_qz = time.time()  # qz 작업 시작 시간 기록
    # insert_data(qz_crawling_function())
    # end_time_qz = time.time()  # qz 작업 종료 시간 기록
    # elapsed_time_qz = end_time_qz - start_time_qz  # qz 작업 소요 시간 계산
    # print(f"qz 작업 완료. 소요 시간: {elapsed_time_qz:.2f} 초")

    print("al 시작")
    start_time_al = time.time()  # al 작업 시작 시간 기록
    insert_data(al_crawling_function())
    end_time_al = time.time()  # al 작업 종료 시간 기록
    elapsed_time_al = end_time_al - start_time_al  # al 작업 소요 시간 계산
    print(f"al 작업 완료. 소요 시간: {elapsed_time_al:.2f} 초")

    # print("ce 시작")
    # start_time_ce = time.time()  # ce 작업 시작 시간 기록
    # insert_data(ce_crawling_function())
    # end_time_ce = time.time()  # ce 작업 종료 시간 기록
    # elapsed_time_ce = end_time_ce - start_time_ce  # ce 작업 소요 시간 계산
    # print(f"ce 작업 완료. 소요 시간: {elapsed_time_ce:.2f} 초")

    # print("cl 시작")
    # start_time_cl = time.time()  # cl 작업 시작 시간 기록
    # insert_data(cl_crawling_function())
    # end_time_cl = time.time()  # cl 작업 종료 시간 기록
    # elapsed_time_cl = end_time_cl - start_time_cl  # cl 작업 소요 시간 계산
    # print(f"cl 작업 완료. 소요 시간: {elapsed_time_cl:.2f} 초")


crawling()
# 연결 닫기
cursor.close()
conn.close()
