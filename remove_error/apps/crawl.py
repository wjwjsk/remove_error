import requests, subprocess, re, datetime, time, concurrent.futures, json
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

crl_page = 10


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


# fmkorea
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
# 10페이지
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
# 5페이지 이하만 사용(페이지 자체 로드 느림)
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
                in_soup = insert_soup(home + href)
                bf_title = "".join(
                    in_soup.select_one("dl dt .title").find_all(string=True, recursive=False)
                ).strip()
                title = re.sub(r"\[[^\]]+\]\s*", "", bf_title, count=1)
                shop_url = in_soup.select_one(".market-info-view-table tr td a").text
                board_price = in_soup.select_one(".market-info-view-table tr td span").text
                tr = in_soup.find("th", string=re.compile("배송비"))
                delivery_price = tr.find_next_sibling("td").get_text()
                category = "".join(
                    in_soup.select_one(".left .ca_name").find_all(string=True, recursive=False)
                ).strip()
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
                    "board_price": board_price,
                    "board_description": image_src_str,
                    "delivery_price": delivery_price,
                    "is_end_deal": is_end_deal,
                    "category": category,
                }
            )

            time.sleep(0.5)

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
            if blind is None or not any(filter(lambda word: word == "블라인드", blind.text.split())):
                href = link.select_one(".na-subject")["href"]
                category = link.select_one("#abcd").text
                board_price = link.select_one("div:nth-child(3) font").text
                in_soup = insert_soup(href)
                bf_shop_url = re.findall(r'(https?://[^\s]+)', in_soup.select_one(
                    ".d-flex.my-1 > .pl-3.flex-grow-1.text-break-all a").text)
                shop_url = bf_shop_url[0]

                bf_title = in_soup.select_one("h1#bo_v_title").text.split()
                title = ' '.join(bf_title[4:])
                current_time = datetime.datetime.now()
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                # 게시글 이미지
                image_src_str = ""
                div_src_str = in_soup.select(".view-content.fr-view p img, .view-content.fr-view a img")
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
                formatted_time = "블라인드 게시글"
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
                image_src_str += src + "<br>"            
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")                

            datas[page].append({
                'board_url': home + href,
                'item_name': title,
                "end_url": shop_url,
                'clr_update_time': formatted_time,
                "board_price": "본문참조",
                "board_description": image_src_str,
                "delivery_price": "본문참조",
                "is_end_deal": is_end_deal,
                "category": "기타",
            })

    return datas



## 해당url html 확인
# url = "https://www.clien.net/service/board/jirum/18383201?od=T31&po=0&category=1000236&groupCd="
# txt_write(url)


## 크롤링 데이터확인
# json_write(cl_crawling_function())
