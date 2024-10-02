const express = require('express');
// const mongoose = require('mongoose');
const { ApolloServer, gql } = require('apollo-server-express');
const cors = require('cors');
const mongoose = require('mongoose');
const { DateTime } = require('graphql-scalars');
const { exec } = require('child_process');

// 定义要执行的 Bash 脚本路径
const scriptPath = '../scraper.py';

// 获取命令行参数（跳过前两个参数）
const args = process.argv.slice(2);

// 检查是否提供参数
if (args.length === 0) {
    console.error("请提供参数。");
    process.exit(1);
}

// 将参数转换为字符串形式
const pythonArgs = args.join(' ');

// 定时调用 Bash 脚本的函数
const callScript = () => {
    exec(`python ${scriptPath} ${pythonArgs}`,(error, stdout, stderr) => {
        if (error) {
            console.error(`执行错误: ${error.message}`);
            return;
        }
        if (stderr) {
            console.error(`错误输出: ${stderr}`);
            return;
        }
        console.log(`脚本输出:\n${stdout}`);
    });
};

// 设置定时调用，每隔 30min 执行一次
const interval = 1800000; // 30 min
setInterval(callScript, interval);

// 立即调用一次
//callScript();

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