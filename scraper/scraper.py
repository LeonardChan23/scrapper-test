import requests
import time
import argparse
import re
import cloudscraper
from datetime import datetime
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
# import tensorflow
# from transformers import pipeline
from pymongo import MongoClient


# 连接到 MongoDB
client = MongoClient('mongodb://localhost:27017/')  
db = client['scraper_post']  
# 创建集合
collection = db['scraper_post'] 

def fetch_protocol_posts(url, site):
    try:
        #查询数据中最新的时间
        driver = webdriver.Chrome()
        max_time_doc = collection.find_one(
            {'source': 'protocol.ai'},  # 查询条件
            sort=[('time', -1)]  # 按 time 字段降序排序
        )
        # 发送 GET 请求
        response = requests.get(url+site)
        response.raise_for_status()  # 检查请求是否成功
        #print(response)
        responseContent = response.text.encode('utf-8')
        # 解析 HTML 页面
        soup = BeautifulSoup(responseContent, 'html.parser')

        # 找到所有博客文章的标题和内容
        posts = soup.find_all('article') 

        # 打开目标网页
        driver.get(url+site) 

        scroll_pause_time = 2  # 每次滚动的暂停时间

        # 获取窗口的高度
        window_height = driver.execute_script("return window.innerHeight")

        time.sleep(scroll_pause_time)

        while True:
            time_elements = driver.find_elements(By.CSS_SELECTOR, 'time')
            visible_time_elements = []

            for time_element in time_elements:
                is_visible = driver.execute_script(
                    "var elem = arguments[0];"
                    "var box = elem.getBoundingClientRect();"
                    "return (box.top >= 0 && box.left >= 0 && box.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&"
                    " box.right <= (window.innerWidth || document.documentElement.clientWidth));",
                    time_element
                )

                if is_visible:
                    visible_time_elements.append(time_element)
                    time_value = time_element.get_attribute('datetime')  # 获取 datetime 属性值
                    
            if time_value:
                # 转换为日期格式
                timeFormat = '%Y-%m-%d'  # 指定格式
                dateObj = datetime.strptime(time_value, timeFormat)
                print(dateObj)
            if max_time_doc:
                max_time = max_time_doc['time']  # 提取最大 time 值
                if max_time >= dateObj:
                    break

            # 向下滚动一个窗口的高度
            driver.execute_script(f"window.scrollBy(0, {window_height});")
            
            # 等待一段时间
            time.sleep(scroll_pause_time)
            
            # 获取当前滚动位置
            current_scroll_position = driver.execute_script("return window.scrollY")
            
            # 获取新的滚动高度
            new_scroll_height = driver.execute_script("return document.body.scrollHeight")
            
            # 检查滚动位置和总高度
            if current_scroll_position + window_height >= new_scroll_height:
                break  # 如果已经到达底部，退出循环

        # 查找 article 内的所有 img 标签
        articleImages = driver.find_elements(By.CSS_SELECTOR, 'article img')

        # 创建列表来保存图片链接
        imageLinks = []

        # 遍历找到的图片并保存链接
        for img in articleImages:
            imgUrl = img.get_attribute('src')
            if imgUrl:  # 确保 URL 存在
                imageLinks.append(imgUrl)
            else:
                imageLinks.append('No Image')
        driver.close()

        imageCount = 0        
        for post in posts:
            # 查询 time 字段的最大值，限定 source 为 'protocol.ai'  

            title = post.find('h1').text  # 标题在 <h1> 标签中
            title = title.replace("\\n", "").replace("\\t", "").replace("\\\\", "").strip()
            
            content = post.find('p', class_='type-p1-serif')  # 简介在该 class 中 但是可能不存在简介
            
            linkElement = post.find('a')
            link = linkElement['href'] if linkElement and 'href' in linkElement.attrs else "No Link"
            
            timePosted = post.find('time').text #时间在 <time> 标签中
            timePosted = timePosted.replace("\\n", "").replace("\\t", "").replace("\\\\", "").strip()
            
            # 转换为 datetime 对象
            timeFormat = '%b %d, %Y'  # 指定格式
            timePostedObj = datetime.strptime(timePosted, timeFormat)

            if max_time_doc:
                max_time = max_time_doc['time']  # 提取最大 time 值
                if max_time >= timePostedObj:
                    break

            author =''.join(post.find(attrs={'itemprop':'name'}).stripped_strings)
            if content != None:
                content = content.text
            # 拼接成绝对链接
            absolute_link = urljoin(url, link)
            #减少访问频率 防止访问过密被block 在NLP模型预测较快时会显著增加第一次爬取需要的时间
            time.sleep(0.5)
            #访问详细信息获取内容
            responsePost = requests.get(absolute_link)
            responsePost.raise_for_status()  # 检查请求是否成功
            #print(response)

            # 解析 HTML 页面
            soupPost = BeautifulSoup(responsePost.text, 'html.parser')
            singlePost = soupPost.find('article')
            div = singlePost.find(attrs={'itemprop': 'articleBody'})
            postInfo = {
                'title':title,
                'author':author,
                'time': timePostedObj,
                'link': absolute_link,
                'image': imageLinks[imageCount],
                'source': 'protocol.ai'
            }
            # 获取所有文本元素并拼接
            for span in div.find_all('span'):
                span.decompose()
            article_content = div.get_text(separator=' ', strip=True)  # 使用 stripped_strings 去掉多余空白
            article_content = article_content.encode('latin1').decode('UTF-8')
            #print(all_text)
            postInfo['summary'] = get_blog_summary(article_content)
            #postInfo['summary'] = article_content
            print(postInfo)
            collection.insert_one(postInfo)
            imageCount += 1
            #测试专用 只爬十篇文章
            if imageCount == 10 and args.test:
                break
            

    except requests.exceptions.RequestException as e:
        print(f'Error fetching the blog posts: {e}')

def fetch_ethereum_posts(url):
    max_time_doc = collection.find_one(
        {'source': 'Ethereum'},  # 查询条件
        sort=[('time', -1)]  # 按 time 字段降序排序
    )

    sitemapUrl = 'https://blog.ethereum.org/sitemap-0.xml'
    XmlResponse = requests.get(sitemapUrl)
    XmlResponse.raise_for_status() 
    siteXml = XmlResponse.text
    root = ET.fromstring(siteXml)
    namespaces = {}
    for elem in root.findall('.//*'):
        if '}' in elem.tag:
            ns = elem.tag.split('}')[0].strip('{')
            namespaces[ns] = ns  # 将命名空间添加到字典中
    loc_links = []
    # 查找 loc 元素，使用提取的命名空间
    for blogUrl in root.findall('.//{*}loc'):
        loc_text = blogUrl.text
        if loc_text and loc_text.startswith('https://blog.ethereum.org/'):
            parts = loc_text.split('/')
            if len(parts) > 3:  # 确保有足够的部分
                year_str = parts[3]  # 获取紧跟在基础 URL 后的部分
                if len(year_str) == 4 and year_str.isdigit():  # 检查是否为年份
                    loc_links.append(loc_text)
    loc_links.sort(reverse=True)
    # with open ('output.txt','w') as f:
    #     for item in loc_links:
    #         f.write(item+'\n')
    count = 0
    for link in loc_links:
        responsePost = requests.get(link)
        responsePost.raise_for_status()  # 检查请求是否成功
        # print(responsePost.text)
        # with open ('output.txt','w') as f:
        #     f.write(responsePost.text)

        # 解析 HTML 页面
        soupPost = BeautifulSoup(responsePost.text, 'html.parser')
        singlePost = soupPost.find('main')

        title = singlePost.find('h1').text  # 标题在 <h1> 标签中
        title = title.replace("\\n", "").replace("\\t", "").replace("\\\\", "").strip()
        
        timeAndAuthor = singlePost.find ('h2', class_="chakra-text").text #作者和时间在 <h2> 标签中
        timeAndAuthor = timeAndAuthor.replace("\\n", "").replace("\\t", "").replace("\\\\", "").strip()
        pattern = r"Posted by (.+?) on ([A-Za-z]+ \d{1,2}, \d{4})"

        # 使用正则表达式搜索
        match = re.search(pattern, timeAndAuthor)
        
        if match:
            author = match.group(1)  # 提取作者
            date =  datetime.strptime(match.group(2),"%B %d, %Y")     # 提取日期
        else:
            author = "No Author"
            date = None
        
        if max_time_doc:
                max_time = max_time_doc['time']  # 提取最大 time 值
                if max_time >= date:
                    break

        image = singlePost.find('img', attrs={'data-nimg':'intrinsic'})['src']
        image = urljoin(url,image)

        category = singlePost.find(attrs={'id':'category'}).text

        content = singlePost.find('article').get_text(separator=' ')

        postInfo = {
            'title':title,
            'author':author,
            'time': date,
            'link': link,
            'category': category,
            'image': image,
            'source': 'Ethereum'
        }
        postInfo['summary'] = get_blog_summary(content) 
        collection.insert_one(postInfo)
        print(postInfo)
        #测试专用 只爬十篇文章
        count += 1
        if count == 10 and args.test:
            break

def fetch_coinbase_posts(url):
    max_time_doc = collection.find_one(
        {'source': 'Coinbase'},  # 查询条件
        sort=[('time', -1)]  # 按 time 字段降序排序
    )

    chrome_options = Options()
    chrome_options.add_argument("--lang=en")  # 设置语言为英语
    # chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # 创建 WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    # 访问页面
    driver.get(url)

    time.sleep(3)

    span_element = driver.find_element(By.XPATH, "//span[text()='Show more']")
    button_element = span_element
    for _ in range(3):  # 向上查找两次
        button_element = button_element.find_element(By.XPATH, "..")
    count = 0
    while True:
        count += 20
        imageElement = driver.find_element(By.CSS_SELECTOR,".card-article-image:last-of-type")
        cardElement = imageElement
        for _ in range(5):  # 向上查找三次
            cardElement = cardElement.find_element(By.XPATH, "..")
        date = cardElement.find_element(By.CSS_SELECTOR,"p[color='foregroundMuted']:first-of-type").text
        print(date)
        if date:
            # 转换为日期格式
            timeFormat = '%B %d, %Y'  # 指定格式
            # 定义正则表达式，匹配日期格式
            pattern = re.compile(r'(^\w+ \d{1,2},? \d{4}),?$')
            date = pattern.match(date).group(1)
            dateObj = datetime.strptime(date, timeFormat)
        if max_time_doc:
                max_time = max_time_doc['time']  # 提取最大 time 值
                if max_time >= dateObj:
                    break
        try:
            #只获取前40个 不然太慢了
            if count == 40 and args.test:
                break
            driver.execute_script("arguments[0].scrollIntoView(); window.scrollBy(0, -200);", span_element)
            button_element.click()
            span_element = driver.find_element(By.XPATH, "//span[text()='Show more']")
            button_element = span_element
            for _ in range(3):  # 向上查找两次
                button_element = button_element.find_element(By.XPATH, "..")
            time.sleep(2)
        except Exception as e:
            break
        
        # 查找所有具有 data-qa 属性的元素
        elements = driver.find_elements(By.XPATH, "//a[@data-qa]")

        # 定义正则表达式
        pattern = re.compile(r'Wayfinding-Child\d+-CardImage')

        # 过滤符合条件的元素
        matching_elements = [elem for elem in elements if pattern.match(elem.get_attribute('data-qa'))]
        for link_element in matching_elements:
            link_target = link_element.get_property('href')
            # 在新标签页中打开另一个 URL
            driver.execute_script("window.open(arguments[0]);", link_target)

            # 切换到新标签页
            driver.switch_to.window(driver.window_handles[1])  # 切换到第二个标签页

            # 等待页面加载
            time.sleep(1)  # 根据需要调整等待时间

            # 在新标签页中执行操作
            title = driver.find_element(By.CSS_SELECTOR,"h1").text

            author = driver.find_elements(By.CSS_SELECTOR,"p")[0].text.strip()
            category = driver.find_elements(By.CSS_SELECTOR, "p")[1].text.strip()
            timePosted = driver.find_elements(By.CSS_SELECTOR,"p")[2].text.strip()
            elementCount = 0
            while not author.startswith("By "):
                elementCount += 1
                author = driver.find_elements(By.CSS_SELECTOR,"p")[elementCount].text.strip()
                category = driver.find_elements(By.CSS_SELECTOR, "p")[elementCount+1].text.strip()
                timePosted = driver.find_elements(By.CSS_SELECTOR,"p")[elementCount+2].text.strip()
            author = author.split(" ",1)[1]
            if timePosted:
                # 转换为日期格式
                timeFormat = '%B %d, %Y'  # 指定格式
                # 定义正则表达式，匹配日期格式
                timePosted=timePosted.split(" ",1)[1]
                print(timePosted)
                dateObj = datetime.strptime(timePosted, timeFormat)
            if max_time_doc:
                max_time = max_time_doc['time']  # 提取最大 time 值
                if max_time >= dateObj:
                    break
            image_element = driver.find_elements(By.CSS_SELECTOR,"img")[2]
            image = image_element.get_attribute('src')

            postInfo = {
                'title':title,
                'author':author,
                'time': dateObj,
                'link': link_target,
                'category': category,
                'image': image,
                'source': 'Coinbase'
            }   

            content = driver.find_element(By.CSS_SELECTOR,"[id='article_introduction']").text.strip()

            postInfo['summary']=get_blog_summary(content)

            collection.insert_one(postInfo)

            # 关闭新标签页
            driver.close()
            # 切换回初始标签页
            driver.switch_to.window(driver.window_handles[0])
            
            
    # cookies = driver.get_cookies


    # scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance
    # # Or: scraper = cloudscraper.CloudScraper()  # CloudScraper inherits from requests.Session

    # siteXml = scraper.get("https://www.coinbase.com/blog/sitemaps.xml").text

    # root = ET.fromstring(siteXml)
    # response = requests.get(url)
    # print(response.text)
    # return
    # namespaces = {}
    # for elem in root.findall('.//*'):
    #     if '}' in elem.tag:
    #         ns = elem.tag.split('}')[0].strip('{')
    #         namespaces[ns] = ns  # 将命名空间添加到字典中
    # loc_links = []
    # 查找 loc 元素，使用提取的命名空间
    
    
    

    return True

def get_blog_summary(content):
    if args.model == 'NLP':
        # 对文章内容进行编码
        Inputs = Tokenizer.encode('summarize: '+ content, return_tensors='tf', truncation=True, max_length=512)

        # 生成摘要
        summaryIDs = Model.generate(Inputs, max_length=200, min_length = 100, num_beams=4, early_stopping=False, length_penalty=2.0)
        # 解码摘要
        return Tokenizer.decode(summaryIDs[0], skip_special_tokens=True)
    elif args.model == 'LLM':
        completion = client.chat.completions.create(    
            model = "moonshot-v1-8k",
            messages = [
                {"role": "system", "content": "You are Kimi, the AI assistant provided by Moonshot AI, and you are better at conversations in Chinese and English. You'll provide users with safe, helpful, and accurate answers. At the same time, you will reject all answers to questions about terrorism, racial discrimination, pornography, etc. The user will enter a piece of text, you need to provide users with a summary of the text, don't introduce any superfluous replies, just summarize the text, the language of the text is English, and your summary language needs to be English. Your reply should be limited between 100 to 150 words in English. Your reply must not include any comments on the article, including the use of expressions such as \"the text propose\" or \"the text says\" or \"the text describe\" in the reply. You must not use any markdown format in your reply."},
                {"role": "user", "content": content}
            ],
            temperature = 0.3,
        )
        return completion.choices[0].message.content

if __name__ == '__main__':
    protocolUrl = 'https://protocol.ai'
    protocolSite = '/blog'
    ethereumUrl = 'https://blog.ethereum.org/'
    coinbaseUrl = 'https://www.coinbase.com/blog/landing'
    parser = argparse.ArgumentParser(description="Choose AI model type")
    
    # 添加 --model 参数，指定类型为字符串
    parser.add_argument('--model', type=str, choices=['NLP', 'LLM'], required=True,
                        help='Choose between NLP or LLM')
    parser.add_argument('--test', action='store_true', required=False,
                        help='enable test mode')
    parser.add_argument('--apikey', type=str, required= False,
                        help='provide apikey')
    # 解析参数
    args = parser.parse_args()
    if args.model == 'LLM' and not args.apikey:
        parser.error("--apikey is required when --model is 'LLM'")
    if args.model == 'NLP':
        from transformers import T5Tokenizer, TFT5ForConditionalGeneration
        model_name = 't5-base' 
        Tokenizer = T5Tokenizer.from_pretrained(model_name)
        Model = TFT5ForConditionalGeneration.from_pretrained(model_name)
    elif args.model == 'LLM':
        from openai import OpenAI
            #使用Moonshot大模型 提供apikey和密钥 可以更换为任意openai相容的模型
        client = OpenAI(
            api_key=args.apikey, # 在这里将 MOONSHOT_API_KEY 替换为你从 Kimi 开放平台申请的 API Key
            base_url="https://api.moonshot.cn/v1",
        )   
    else:
        print('Please set AI model type!')
        exit 

    #fetch_protocol_posts(protocolUrl,protocolSite)
    #fetch_ethereum_posts(ethereumUrl)
    fetch_coinbase_posts(coinbaseUrl)

