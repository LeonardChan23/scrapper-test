const express = require('express');
// const mongoose = require('mongoose');
const { ApolloServer, gql } = require('apollo-server-express');
const cors = require('cors');
const mongoose = require('mongoose');
const { DateTime } = require('graphql-scalars');

// const { typeDefs: scalarTypeDefs } = require('graphql-scalars');
 

async function startServer() {
    //  // Connect to the database
    try {
        await mongoose.connect('mongodb://localhost:27017/scraper_post', {
          //useNewUrlParser: true,
          //useUnifiedTopology: true,
        });
    
        console.log('Successfully connected to MongoDB');
      } catch (error) {
        console.error('Error connecting to MongoDB:', error);
      }

    const itemSchema = new mongoose.Schema({
        title: String,
        author: String,
        time: Date,
        link: String,
        image: String,
        source: String,
        summary: String
    });
    const Item = mongoose.model('Item', itemSchema, 'scraper_post');

    // 定义数据模型
    // GraphQL 类型定义
    const typeDefs = gql`
      scalar DateTime
      enum SortOrder {
        ASC
        DESC
      }
      type Item {
        title: String!
        author: String!
        time: DateTime!
        link: String!
        image: String!
        source: String!
        summary: String!
      }
    
       type Query {
        items(sort: SortOrder, filter: String): [Item]!
      }
    `;

    // GraphQL 解析器
    const resolvers = {
        Query: {
            items: async (_, { sort,filter }, { Item }) => {
                const query = {};
                if(filter){
                    query.source = filter
                }
                const sortOptions = {};
                if (sort) {
                  sortOptions.time = sort === 'ASC' ? 1 : -1;  // 1 为升序，-1 为降序
                }
          
                // 从 MongoDB 获取数据并排序
                const items = await Item.find(query).sort(sortOptions).exec();
                return items;
            },
        },
        // 定义 DateTime scalar 的解析器
        //   DateTime: require('graphql-iso-date').GraphQLDateTime,
    };
    // Create an Express app
    const app = express();
    app.use(cors());

    // Create an Apollo server
    const server = new ApolloServer({
        typeDefs,
        resolvers,
        context: () => ({ Item }),
    });

    // Apply the Apollo middleware to the Express app
    await server.start()
    server.applyMiddleware({ app });

    // Start the Express server
    const PORT = process.env.PORT || 4000;
    app.listen(PORT, () => {
        console.log(`🚀 Server ready at http://localhost:${PORT}${server.graphqlPath}`);
    });
}

startServer();