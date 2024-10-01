# Python Scraper integrated with NLP/LLM summarizing function, stored in MongoDB Backend, providing GraphQL Query Service

## Introduction

The project is to develop a python scraper to capture blog post from [protocol.ai](https://protocl.ai), [Ethereum Foundation Blog](https://blog.ethereum.org/en) and [Coinbase Blog](https://www.coinbase.com/blog/landing) and using NLP/LLM model to summrize the blog, storing the data in a MongoDB Backend and using a node.js express server to exposing the data through GraphQL service.

### Explanation for technolog stack choices
- #### Python, BeautifulSoup and Selenium
    Obviously, python provides several ready-to-use data scraper packages, which is convenient for developers to use.

    I choose BeautfulSoup4 for none-lazy-loading blogs, such as Ethereum blog, the main page of protocol.ai (but the cover pictures of proctol.ai is lazy-loading). bs4 is suitable for static pages, but it can not load dynamic pages which load data through user click or scrolling. 

    To solve the problem, I use Selenium for dynamic pages, such as Coinbase Blog (user click loading) and cover images for protocol ai.

- #### NLP and LLM model
    Traditional NLP model provided in transformers is easy to deploy locally. As my computer is running with Intel Arc GPU, it's really difficult for me to use GPU for prediction. For the project, I choose Google's t5-base model in tensorflow. Due to the complexity of pytorch versions (you should choose cuda versions, etc), in my case I choose tensorflow which is easier to install. As for t5-base, it's a classical NLP model which support maximum 512 tokens as inputs. I choose to use t5ForConditionalGeneration branch for the summarization task as summarizing is within the kind of generation. 

    For LLM model, as I could not use ChatGPT here in Hong Kong, I choose to use an OpenAI compatible LLM service named moonshot.ai. They provide LLMs which support up to 128k tokens. Here I choose to use 8k version as the target blogs are from 1000 words to 3000 words generally, 8k is enough for the generation (16k and 128k versions are expensive😔).

    If you need to run the project for testing, I will provide an Api key for you to use.

    Also, you can use your own Api key from any other OpenAI compatible LLMs, see [this section](#1)
- #### MongoDB
    MongoDB is suitable for rapidly growing data, which is pefect for the initialization process using the scraper (periodical running of the scraper will not cause much growing data each time). Also, MongoDB provides node.js packages, which is compatible with graphQL backend.

- #### Express Server on node.js
    The easist way to build an api server, also provide packages to start an Appolo Server which supports GraphQL service.

## Prerequisite

Before start, make sure you have installed the following:

- Install [Node.js](https://nodejs.org/) (v20.7 in development environment)
- Install [MongoDB](https://www.mongodb.com/) (Local version in the project)
- Install [Python](https://python.org/) (v3.12.6 in development environment)
- Install [Git](https://git-scm.com/) (To clone the project, you may choose downloading the zip file as well)

To run the scraper, make sure you have installed all the packages listed in [requiremnts](./scraper/requirements.txt).

<h3 id="1">LLM service</h3>
To use the LLM service to summarize the blog, you should register an API key from any OpenAI compatible LLM service provider. moonshot.ai is used in the project. 

To change to your own LLM provider, simply change this line in [scraper.py](./scraper/scraper.py):
```python
completion = client.chat.completions.create(    
    model = "You api model",
    messages = [
        {"role": "system", "content": "Your Prompt for summarization"},            
        {"role": "user", "content": content}
    ],        
    temperature = 0.3,
)
```
And run the scraper using your own api:
```bash
python scraper.py --model LLM --apikey YOUR_API_KEY
```


## Implementation

Follow the steps to intsall dependencies:

1. Clone the project (master branch)：
   ```bash
   git clone https://github.com/LeonardChan23/scraper-test.git
2. Download and set up a MongoDB server, follow the docs [here](https://www.mongodb.com/products/self-managed/community-edition). Alternatively, cloud service can also be used, simply create your account in MongoDB and revise the connection configuration in [scraper.py](./scraper/scraper.py) and [server.js](./backend/server.js).
   Start the MongoDB and expose a port for scraper and backend usage.

3. Enter scraper folder：
   ```bash
   cd scraper
4. Install packages:
   ```bash
   pip install -r requirenments.txt
   ```
5. (Optional, you can also start later) Start the scraper:
   ```bash
   python scraper.py --model NLP/LLM --apikey YOUR_API_KEY
6. Open another termial, enter backend folder:
   ```bash
   cd backend
7. Install all the packages needed:
   ```bash
   npm install
   ```
## Start
#### Before start, make sure you have a running MongoDB server.
To start the project, run this command in scraper folder:
```bash
python scraper.py --model NLP/LLM --apikey YOUR_API_KEY
```
Then run this command in backend folder:
```bash
node server.js
```

By default, the GraphQL service will run on http://localhost:4000/graphql.

## Testing
Since in initialization of scraper, about 4000 blogs will be sent to NLP/LLM for summarization, add --test when running scraper.py will only send 10 blogs from protocol.ai, 2 pages of blogs from Ethereum Foundation Blog and 2 scrolls of blogs from Coinbase Blog.

```bash
python scraper.py --model NLP/LLM --apikey YOUR_API_KEY --test
```
