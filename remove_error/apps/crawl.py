import requests, subprocess, re, datetime, time
from bs4 import BeautifulSoup
from django.utils import timezone



fm_home = "https://www.fmkorea.com"
fm_datas = [[] for _ in range(10)]


def txt_write(soup):
    data = str(soup)
    with open("page_html.txt", "w" ,encoding="utf-8") as file:
        file.write(data)
    subprocess.run(["start", "page_html.txt"], shell=True)  # Windows
    # subprocess.run(["open", "page_html.txt"])  # macOS

# HTML 페이지 soup에 담기
def insert_soup(url):
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def fm_crawling_function():
    for page in range(0, 10):
        if(page == 0):
            soup = insert_soup("https://www.fmkorea.com/hotdeal")
            li_tags = soup.select('div.fm_best_widget > ul > li')
            # 게시판 링크+제목+금액+배송비+시간
            for link in li_tags:
                href = link.select_one('.li h3 a')['href']
                bf_title = ''.join(link.select_one('.li h3 a').find_all(string=True, recursive=False)).strip()
                title = re.sub(r'[\xa0\t]', '', bf_title)
                info_texts = [a.text for a in link.select('.hotdeal_info span a')[1:3]]
                category = link.select_one('div .category a').text
                current_time = datetime.datetime.now()
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                # 게시글 내부 설명+url
                in_soup = insert_soup("https://www.fmkorea.com"+ href)
                shop_url = in_soup.select_one('tr td .xe_content a').text
                
                desc_div = in_soup.select_one('div article div')
                desc_p = desc_div.find_all('p')
                #설명 p태그마다 가져오기
                description = ""
                for i in range(1, len(desc_p)):
                    p = desc_p[i]
                    description += str(p)                   
                                
                if 'hotdeal_var8Y' in link.select_one('.li h3 a')['class']:
                    fm_datas[page].append({'board_url' : fm_home + href, 'item_name' : title, 'end_url' : shop_url, 'clr_update_time': formatted_time, 
                                'board_price': info_texts[0], 'board_description': description , 'delivery_price': info_texts[1],'is_end_deal' : True, 'category' : category})
                else:
                    fm_datas[page].append({'board_url' : fm_home + href, 'item_name' : title, 'end_url' : shop_url, 'clr_update_time': formatted_time, 
                                'board_price': info_texts[0], 'board_description': description ,'delivery_price': info_texts[1],'is_end_deal' : False, 'category' : category})
                    
            time.sleep(1)
            
        else:
            # 2페이지 부터
            soup = insert_soup("https://www.fmkorea.com/hotdeal?page=" + str(page+1))
            li_tags = soup.select('div.fm_best_widget > ul > li')
            # 게시판 링크+제목
            for link in li_tags:
                href = link.select_one('.li h3 a')['href']
                bf_title = ''.join(link.select_one('.li h3 a').find_all(string=True, recursive=False)).strip()
                title = re.sub(r'[\xa0\t]', '', bf_title)
                info_texts = [a.text for a in link.select('.hotdeal_info span a')[1:3]]
                current_time = datetime.datetime.now()
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                # 게시글 내부 설명+url
                in_soup = insert_soup("https://www.fmkorea.com"+ href)
                shop_url = in_soup.select_one('tr td .xe_content a').text
                
                desc_div = in_soup.select_one('div article div')
                desc_p = desc_div.find_all('p')
                #설명 p태그마다 가져오기
                description = ""
                for i in range(1, len(desc_p)):
                    p = desc_p[i]
                    description += str(p)                   
                                
                if 'hotdeal_var8Y' in link.select_one('.li h3 a')['class']:
                    fm_datas[page].append({'board_url' : fm_home + href, 'item_name' : title, 'end_url' : shop_url, 'clr_update_time': formatted_time, 
                                'board_price': info_texts[0], 'board_description': description , 'delivery_price': info_texts[1],'is_end_deal' : True, 'category' : category})
                else:
                    fm_datas[page].append({'board_url' : fm_home + href, 'item_name' : title, 'end_url' : shop_url, 'clr_update_time': formatted_time, 
                                'board_price': info_texts[0], 'board_description': description ,'delivery_price': info_texts[1],'is_end_deal' : False, 'category' : category})
            time.sleep(1)
            
            
    return fm_datas
        

# txt_write(fm_crawling_function())

            
