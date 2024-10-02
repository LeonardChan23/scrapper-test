# Python Scraper integrated with NLP/LLM summarizing function, stored in MongoDB Backend, providing GraphQL Query Service

## About Future scaling strategies and scalability

As far as I'm concerned, if 500 blogs is under watched, the scraper server should be decentralized for different blogs. The blog data is so huge that you may need to slice the data into shades. The scraper should be multi-processed on multiple servers, controlled by a scheduler. One possible way is using Kubernetes to create cron jobs. We can prepare several scraper images in different deployments or stateful sets.  

Also, if there're one milion users, the first bottleneck lies in the database. The database will experience really high throughput at peeks. First thing to do is to caching static data using CDN, also performs load-balancing. The datase should also be in a cluster with load-balancing modules. If we have to support a large number of keep-alived connections, the connection limit can be easily reached. To avoid connection error with backend database, we should limit the connection usage on each server, scale up cluster when demand increases. We may choose cloud databases and servers which support high-availability deployments, AWS, for example.
