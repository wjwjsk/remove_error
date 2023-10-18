import requests
from bs4 import BeautifulSoup

home_link = "https://www.fmkorea.com"
board_url_list = []


for page in range(1,11):
    if(page == 1):
        url = "https://www.fmkorea.com/hotdeal"
        response = requests.get(url)
        # HTML 페이지 내용 가져오기
        html = response.text

        soup = BeautifulSoup(html, 'html.parser')

        # 중복 항목을 제거할 빈 세트(set)를 만듭니다.
        unique_links = set()

        div_element = soup.find('div', class_='fm_best_widget')

        if div_element:
            # div 태그 내부에서 ul > li > a 요소를 선택하고 중복된 것을 제거하고 a 태그의 링크를 가져옵니다.
            for link in div_element.select('ul > li > div > a'):
                href = link['href']
                if href not in unique_links:
                    unique_links.add(href)
                    board_url_list.append(home_link + href)

    else:
        url = "https://www.fmkorea.com/hotdeal?page=" + str(page)
        response = requests.get(url)
        # HTML 페이지 내용 가져오기
        html = response.text

        soup = BeautifulSoup(html, 'html.parser')

        # 중복 항목을 제거할 빈 세트(set)를 만듭니다.
        unique_links = set()

        div_element = soup.find('div', class_='fm_best_widget')

        if div_element:
            # div 태그 내부에서 ul > li > a 요소를 선택하고 중복된 것을 제거하고 a 태그의 링크를 가져옵니다.
            for link in div_element.select('ul > li > div > a'):
                href = link['href']
                if href not in unique_links:
                    unique_links.add(href)
                    board_url_list.append(home_link + href)


print(board_url_list)
            
