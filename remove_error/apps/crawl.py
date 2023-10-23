import requests, subprocess, re, datetime, time, concurrent.futures ,json
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

crl_page = 10


def json_write(data):
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    with open("page_data.json", "w", encoding="utf-8") as file:
        file.write(json_data)
    subprocess.run(["start", "page_data.json"], shell=True)  # Windows
    # subprocess.run(["open", "page_html.txt"])  # macOS


# HTML 페이지 soup에 담기
def insert_soup(url):
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    return soup


# fmkorea
def fm_crawling_function():
    home = "https://www.fmkorea.com"
    datas = [[] for _ in range(crl_page)]
    for page in range(0, crl_page):
        if page == 0:
            soup = insert_soup("https://www.fmkorea.com/hotdeal")
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

        else:
            # 2페이지 부터
            soup = insert_soup("https://www.fmkorea.com/hotdeal?page=" + str(page + 1))
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


# ppomppu
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
            div_a_tags = desc_div.select("p > img")
            filtered_tags = [tag for tag in div_a_tags if len(tag["src"]) <= 450]
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


# pp_crawling_function()
# json_write(fm_crawling_function())