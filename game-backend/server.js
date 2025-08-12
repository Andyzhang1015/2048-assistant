// 导入需要的模块
const express = require('express');           // Express框架，用于创建Web服务器
const http = require('http');                 // Node.js内置HTTP模块
const socketIo = require('socket.io');        // Socket.IO，用于实现实时通信
const db = require('./database');             // 自定义数据库模块

// 创建Express应用实例
const app = express();

// 创建HTTP服务器（Socket.IO需要HTTP服务器作为基础）
const server = http.createServer(app);

// 初始化Socket.IO，并将其绑定到HTTP服务器
const io = socketIo(server);

// 连接到MySQL数据库
// 这里使用Promise方式处理异步操作
db.getConnection()
  .then(connection => {
    // 成功连接数据库后，输出提示信息
    console.log('已连接到MySQL数据库');
    // 释放连接回连接池
    connection.release();
  })
  .catch(err => {
    // 如果连接失败，输出错误信息
    console.error('数据库连接失败: ' + err.stack);
  });

// 创建必要的数据表的SQL语句
// 使用反引号(`)定义多行字符串，包含创建players表和games表的SQL语句
const createTables = `
  CREATE TABLE IF NOT EXISTS players (
    id INT AUTO_INCREMENT PRIMARY KEY,        -- 玩家ID，自增主键
    username VARCHAR(50) UNIQUE NOT NULL,     -- 用户名，唯一且不能为空
    password VARCHAR(255) NOT NULL,           -- 密码，不能为空
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 创建时间，默认为当前时间
  );
  
  CREATE TABLE IF NOT EXISTS games (
    id INT AUTO_INCREMENT PRIMARY KEY,        -- 游戏ID，自增主键
    room_id VARCHAR(50) NOT NULL,             -- 房间ID，不能为空
    state JSON,                               -- 游戏状态，使用JSON格式存储
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 创建时间，默认为当前时间
  );
`;

// 执行创建表的SQL语句
db.query(createTables)
  .then(() => {
    // 成功创建或已存在表时输出提示信息
    console.log('数据表已创建或已存在');
  })
  .catch(err => {
    // 创建表失败时输出错误信息
    console.error('创建表失败: ' + err.stack);
  });

// 设置中间件
// express.static中间件用于提供静态文件（如HTML、CSS、JS等）
app.use(express.static('public'));

// express.json中间件用于解析JSON格式的请求体
app.use(express.json());

// 定义路由
// 当用户访问根路径('/')时，返回index.html文件
app.get('/', (req, res) => {
  // sendFile方法发送指定文件作为响应
  res.sendFile(__dirname + '/public/index.html');
});

// 玩家注册接口
// 处理POST请求到'/register'路径
app.post('/register', (req, res) => {
  // 从请求体中获取用户名和密码
  const { username, password } = req.body;
  
  // 验证用户名和密码是否存在
  if (!username || !password) {
    // 如果缺少必要字段，返回400错误和错误信息
    return res.status(400).json({ error: '用户名和密码是必需的' });
  }
  
  // 定义插入玩家信息的SQL语句
  const query = 'INSERT INTO players (username, password) VALUES (?, ?)';
  
  // 执行数据库查询
  db.query(query, [username, password])
    .then(([results]) => {
      // 插入成功，返回201状态码和成功信息
      res.status(201).json({ message: '注册成功', playerId: results.insertId });
    })
    .catch(err => {
      // 处理错误情况
      if (err.code === 'ER_DUP_ENTRY') {
        // 如果是重复用户名错误，返回400状态码和错误信息
        return res.status(400).json({ error: '用户名已存在' });
      }
      // 其他错误，返回500状态码和错误信息
      res.status(500).json({ error: '注册失败' });
    });
});

// 创建一个Map来存储游戏房间信息
// Map是一种键值对集合，类似于对象，但提供了更多的便利方法
const rooms = new Map();

// Socket.IO连接处理
// 当有新的客户端连接时，会触发'connection'事件
io.on('connection', (socket) => {
  // 输出连接用户的socket ID，用于调试
  console.log('用户连接: ' + socket.id);
  
  // 监听'join game'事件，处理玩家加入游戏的请求
  socket.on('join game', (data) => {
    // 从接收到的数据中解构出用户名和房间ID
    const { username, roomId } = data;
    
    // 让该socket加入指定的房间
    // Socket.IO的房间功能可以将socket分组，便于向特定组广播消息
    socket.join(roomId);
    
    // 如果该房间还不存在，则创建新房间
    if (!rooms.has(roomId)) {
      // 使用rooms.set()方法创建新房间并初始化房间状态
      rooms.set(roomId, {
        players: [],                           // 玩家列表
        gameState: {                           // 游戏状态
          players: [],                         // 玩家信息
          ball: { x: 50, y: 50 },              // 球的位置（示例游戏对象）
          scores: {}                           // 玩家得分
        }
      });
    }
    
    // 获取房间对象
    const room = rooms.get(roomId);
    
    // 将新玩家添加到房间的玩家列表中
    room.players.push({
      id: socket.id,                           // 玩家的socket ID
      username: username,                      // 玩家用户名
      x: Math.floor(Math.random() * 700),      // 随机生成玩家的X坐标
      y: Math.floor(Math.random() * 500)       // 随机生成玩家的Y坐标
    });
    
    // 更新游戏状态中的玩家列表
    room.gameState.players = room.players;
    
    // 初始化该玩家的得分
    room.gameState.scores[username] = 0;
    
    // 向房间内所有玩家广播'player joined'事件，通知有新玩家加入
    io.to(roomId).emit('player joined', {
      username: username,                      // 新玩家用户名
      players: room.players,                   // 更新后的玩家列表
      gameState: room.gameState                // 当前游戏状态
    });
    
    // 将房间ID和用户名保存到socket对象上，便于后续使用
    socket.roomId = roomId;
    socket.username = username;
  });
  
  // 监听'player move'事件，处理玩家移动
  socket.on('player move', (data) => {
    // 从接收到的数据中解构出坐标信息
    const { x, y } = data;
    
    // 获取玩家所在的房间ID
    const roomId = socket.roomId;
    
    // 如果房间ID不存在或房间不存在，则直接返回
    if (!roomId || !rooms.has(roomId)) return;
    
    // 获取房间对象
    const room = rooms.get(roomId);
    
    // 在房间玩家列表中查找当前玩家
    const player = room.players.find(p => p.id === socket.id);
    
    // 如果找到该玩家，则更新其坐标
    if (player) {
      player.x = x;
      player.y = y;
      
      // 向房间内除自己外的所有玩家广播'player moved'事件
      // socket.to(roomId)表示向指定房间发送消息，但不包括发送者自己
      socket.to(roomId).emit('player moved', {
        id: socket.id,                         // 玩家ID
        username: socket.username,             // 玩家用户名
        x,                                     // 新的X坐标
        y                                      // 新的Y坐标
      });
    }
  });
  
  // 监听'disconnect'事件，处理玩家断开连接
  socket.on('disconnect', () => {
    // 输出断开连接的用户ID
    console.log('用户断开连接: ' + socket.id);
    
    // 获取玩家所在的房间ID
    const roomId = socket.roomId;
    
    // 如果房间ID不存在或房间不存在，则直接返回
    if (!roomId || !rooms.has(roomId)) return;
    
    // 获取房间对象
    const room = rooms.get(roomId);
    
    // 从房间玩家列表中移除该玩家
    room.players = room.players.filter(player => player.id !== socket.id);
    
    // 从游戏得分中删除该玩家
    delete room.gameState.scores[socket.username];
    
    // 检查房间是否还有玩家
    if (room.players.length === 0) {
      // 如果没有玩家了，则删除该房间
      rooms.delete(roomId);
    } else {
      // 如果还有其他玩家，则向房间内广播'player left'事件
      socket.to(roomId).emit('player left', {
        id: socket.id,                         // 离开的玩家ID
        username: socket.username,             // 离开的玩家用户名
        players: room.players                  // 更新后的玩家列表
      });
    }
  });
});

// 定义服务器监听端口
// 如果环境变量中有PORT，则使用环境变量中的端口，否则使用3000端口
const PORT = process.env.PORT || 3000;

// 启动服务器并监听指定端口
server.listen(PORT, () => {
  // 服务器启动成功后输出提示信息
  console.log(`服务器运行在端口 ${PORT}`);
});