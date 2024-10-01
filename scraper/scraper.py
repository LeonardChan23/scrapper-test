import requests
import time
import argparse
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urljoin
# import tensorflow
# from transformers import pipeline
from pymongo import MongoClient

driver = webdriver.ChromiumEdge()

# 连接到 MongoDB
client = MongoClient('mongodb://localhost:27017/')  
db = client['scraper_post']  
# 创建集合
collection = db['scraper_post'] 

def fetch_blog_posts(url, site):
    try:
        #查询数据中最新的时间
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
            if imageCount == 10:
                break
            

    except requests.exceptions.RequestException as e:
        print(f'Error fetching the blog posts: {e}')
    
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
    baseUrl = 'https://protocol.ai'
    blogSite = '/blog'
    parser = argparse.ArgumentParser(description="Choose AI model type")
    
    # 添加 --model 参数，指定类型为字符串
    parser.add_argument('--model', type=str, choices=['NLP', 'LLM'], required=True,
                        help='Choose between NLP or LLM')
    
    # 解析参数
    args = parser.parse_args()
    if args.model == 'NLP':
        from transformers import T5Tokenizer, TFT5ForConditionalGeneration
        model_name = 't5-base' 
        Tokenizer = T5Tokenizer.from_pretrained(model_name)
        Model = TFT5ForConditionalGeneration.from_pretrained(model_name)
    elif args.model == 'LLM':
        from openai import OpenAI
            #使用Moonshot大模型 提供apikey和密钥 可以更换为任意openai相容的模型
        client = OpenAI(
            api_key="sk-WlVaUY5r7rplD0XmJIACyDlmOTZObb81OaSMDCAC9kv0xzju", # 在这里将 MOONSHOT_API_KEY 替换为你从 Kimi 开放平台申请的 API Key
            base_url="https://api.moonshot.cn/v1",
        )   
    else:
        print('Please set AI model type!')
        exit 

    fetch_blog_posts(baseUrl,blogSite)
    driver.quit()

