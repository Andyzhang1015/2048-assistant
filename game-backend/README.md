# 简单网络游戏后端

这是一个使用 Node.js、Express、Socket.IO 和 MySQL 构建的简单网络游戏后端示例。

## 功能

1. 用户注册
2. 实时多人游戏
3. 玩家移动同步
4. 房间管理系统

## 技术栈

- Node.js
- Express.js (Web 服务器框架)
- Socket.IO (实时通信)
- MySQL (数据库)
- HTML/CSS/JavaScript (前端)

## 安装和设置

### 先决条件

1. Node.js (v12 或更高版本)
2. MySQL 数据库服务器

### 安装步骤

1. 克隆或创建项目目录
2. 安装依赖项:
   ```
   npm install
   ```

3. 设置 MySQL 数据库:
   - 创建一个名为 `game_db` 的数据库
   - 更新 [database.js](file:///e:/test/game-backend/database.js) 中的数据库连接配置

4. 启动服务器:
   ```
   npm start
   ```
   
   或者在开发模式下运行(支持自动重启):
   ```
   npm run dev
   ```

## 项目结构

```
game-backend/
├── server.js          # 服务器主文件
├── database.js        # 数据库配置
├── package.json       # 项目配置和依赖
├── public/            # 前端静态文件
│   └── index.html     # 游戏客户端页面
└── README.md          # 项目说明文档
```

## API 端点

- `POST /register` - 用户注册
- `GET /` - 游戏客户端页面

## Socket.IO 事件

### 服务器监听的事件

- `join game` - 玩家加入游戏
- `player move` - 玩家移动
- `disconnect` - 玩家断开连接

### 服务器发送的事件

- `player joined` - 新玩家加入游戏
- `player moved` - 玩家移动
- `player left` - 玩家离开游戏

## 数据库结构

```sql
-- 玩家表
CREATE TABLE players (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 游戏表
CREATE TABLE games (
  id INT AUTO_INCREMENT PRIMARY KEY,
  room_id VARCHAR(50) NOT NULL,
  state JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 如何玩游戏

1. 打开浏览器访问 `http://localhost:3000`
2. 输入用户名和密码登录(或注册新用户)
3. 输入房间号加入游戏
4. 使用 WASD 键控制你的角色移动

## 扩展建议

1. 添加游戏逻辑(如碰撞检测、得分等)
2. 实现更完善的用户认证系统
3. 添加更多的游戏对象和交互
4. 实现游戏状态持久化
5. 添加聊天功能