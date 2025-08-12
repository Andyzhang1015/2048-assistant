// 数据库配置文件
// 导入mysql2模块，这是Node.js中用于连接MySQL数据库的驱动程序
// 使用mysql2/promise子模块可以更方便地使用Promise语法处理异步操作
const mysql = require('mysql2');

// 创建连接池
// 连接池是一种数据库连接管理技术，可以复用数据库连接，提高性能
const pool = mysql.createPool({
  host: 'localhost',           // 数据库服务器地址，这里使用本地数据库
  user: 'root',                // 数据库用户名，这里使用默认的root用户
  password: '',                // 数据库密码，这里为空（开发环境）
  database: 'game_db',         // 要连接的数据库名称
  waitForConnections: true,    // 当连接池中无可用连接时是否等待
  connectionLimit: 10,         // 连接池中最大连接数
  queueLimit: 0                // 等待连接的最大请求数，0表示无限制
});

// 导出数据库连接池的Promise封装
// 使用pool.promise()可以让我们在使用连接池时使用更简洁的Promise语法
// 而不需要手动处理回调函数
module.exports = pool.promise();