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

crl_page = 1

BASE_DIR = Path(__file__).resolve().parent.parent
with open("remove_error/config.json") as f:
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
