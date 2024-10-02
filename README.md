# Python Scraper integrated with NLP/LLM summarizing function, stored in MongoDB Backend, providing GraphQL Query Service

## About the Frontend Integration
I choose to use Ionic React as my frontend integrated with Apollo Server. Since I have no template available, I can only start from scratch. I'm not quite confident with my frontend UI/UX development skills, though.

In my front end APP, there're several aspects to improve:
1. Should invole lazy loading of images to reduce the loading pressure
2. Should invole lazy loading of blogs to realize faster loading (one easy way is to use paginition in GraphQL
3. The blog lacks advanced search functions including result cache in my backend
4. The blog lacks management of data content, need to integrate more responsive design 

## Prerequiste
To run the frontend, Ionic CLI should be installed.
run
```
npm install @ionic/cli graphql @apollo/client
```
Then enter the folder, prepare the node_modules by
```
ionic init
```

## Run the Frontend
To run the frontend, run this command in frontend folder
```bash
ionic serve
```


By default, the frontend will run on http://localhost.8100. You may open a browser window for the blog.

