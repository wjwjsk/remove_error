from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def clien_crawling_function():
    webdriver_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=webdriver_service)
    
    driver.get("https://www.clien.net/service/board/jirum")

    time.sleep(2)  # 페이지 로딩 대기

    posts = driver.find_elements(By.CSS_SELECTOR, ".list_item.symph_row")

    data_list = []
    
    for post in posts:
        title_element = post.find_element(By.CSS_SELECTOR, ".list_subject a")
        title = title_element.text
        link = title_element.get_attribute('href')
        
        data_list.append({'title': title, 'link': link})
    
    driver.quit()
    
    return data_list


if __name__ == "__main__":
   result_data = clien_crawling_function()
   for data in result_data:
       print(f"Title: {data['title']}, Link: {data['link']}")
