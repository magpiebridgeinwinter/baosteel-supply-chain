# 宝钢板材智慧供应链系统 - 云端部署指南

## 部署方式选择

本应用支持多种云端部署方式，您可以根据需求选择最适合的方案：

### 1. Streamlit Cloud (推荐 - 最简单)

**优点：**
- 免费使用
- 部署简单，只需几步
- 自动更新
- 支持自定义域名

**部署步骤：**

1. **准备代码仓库**
   ```bash
   # 初始化Git仓库
   git init
   git add .
   git commit -m "Initial commit"
   
   # 推送到GitHub
   git branch -M main
   git remote add origin https://github.com/你的用户名/你的仓库名.git
   git push -u origin main
   ```

2. **部署到Streamlit Cloud**
   - 访问 [https://share.streamlit.io](https://share.streamlit.io)
   - 点击"New app"
   - 选择您的GitHub仓库
   - 选择main.py作为主文件
   - 点击"Deploy"开始部署

3. **等待部署完成**
   - 通常需要2-5分钟
   - 部署成功后会获得一个公开URL

### 2. Heroku (推荐 - 稳定)

**优点：**
- 免费套餐可用
- 支持自定义域名
- 扩展性好

**部署步骤：**

1. **安装Heroku CLI**
   ```bash
   # Windows用户
   # 下载并安装 Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli

   # 验证安装
   heroku --version
   ```

2. **登录Heroku**
   ```bash
   heroku login
   ```

3. **创建应用**
   ```bash
   heroku create 你的应用名称
   ```

4. **部署应用**
   ```bash
   git push heroku main
   ```

5. **查看应用**
   ```bash
   heroku open
   ```

### 3. Docker + 云服务器 (推荐 - 专业)

**优点：**
- 完全控制
- 性能可定制
- 适合企业级部署

**部署步骤：**

1. **准备服务器**
   - 购买云服务器（阿里云、腾讯云、AWS等）
   - 安装Docker和Docker Compose

2. **上传代码**
   ```bash
   # 使用SCP上传代码
   scp -r ./Taidi root@服务器IP:/root/
   
   # 或使用Git克隆
   git clone https://github.com/你的用户名/你的仓库名.git
   ```

3. **启动容器**
   ```bash
   cd /root/Taidi
   docker-compose up -d
   ```

4. **配置反向代理（可选）**
   - 使用Nginx配置域名和SSL
   - 配置防火墙规则

### 4. Railway (推荐 - 现代化)

**优点：**
- 免费套餐
- 自动扩缩容
- 支持多种数据库

**部署步骤：**

1. **连接GitHub账号**
   - 访问 [https://railway.app](https://railway.app)
   - 使用GitHub账号登录

2. **创建新项目**
   - 点击"New Project"
   - 选择"Deploy from GitHub repo"
   - 选择您的仓库

3. **配置环境**
   - Railway会自动检测Python项目
   - 确认配置后点击"Deploy"

## 文件说明

### 必需文件
- `main.py` - 主应用文件
- `requirements.txt` - Python依赖列表
- `.streamlit/config.toml` - Streamlit配置
- `Procfile` - Heroku部署配置
- `Dockerfile` - Docker容器配置
- `docker-compose.yml` - Docker编排配置

### 可选文件
- `.gitignore` - Git忽略文件
- `DEPLOYMENT.md` - 本部署文档

## 环境变量配置

如果需要配置环境变量，可以在各平台设置：

### Streamlit Cloud
- 在项目设置中添加Secrets
- 格式：`VARIABLE_NAME=value`

### Heroku
```bash
heroku config:set VARIABLE_NAME=value
```

### Docker
```bash
# 在docker-compose.yml中添加
environment:
  - VARIABLE_NAME=value
```

## 常见问题解决

### 1. 内存不足
- **解决方案：** 升级到付费套餐或优化代码内存使用

### 2. 模型加载失败
- **解决方案：** 确保`tcn_model.pth`文件在仓库中，或使用外部存储

### 3. 数据文件过大
- **解决方案：** 
  - 使用云存储（如AWS S3、阿里云OSS）
  - 压缩数据文件
  - 使用数据库替代CSV文件

### 4. 端口冲突
- **解决方案：** 修改配置文件中的端口号

## 性能优化建议

1. **缓存优化**
   - 使用Streamlit的缓存功能
   - 实现数据预加载

2. **模型优化**
   - 使用量化模型
   - 实现模型懒加载

3. **CDN加速**
   - 静态资源使用CDN
   - 配置Gzip压缩

## 安全建议

1. **访问控制**
   - 添加用户认证
   - 限制IP访问

2. **数据安全**
   - 使用HTTPS
   - 加密敏感数据

3. **定期备份**
   - 自动备份数据
   - 版本控制

## 监控和维护

1. **日志监控**
   - 设置日志收集
   - 配置错误告警

2. **性能监控**
   - 使用APM工具
   - 监控资源使用

3. **定期更新**
   - 更新依赖包
   - 修复安全漏洞

## 联系支持

如遇到部署问题，请检查：
1. 日志文件中的错误信息
2. 依赖版本兼容性
3. 网络连接状态
4. 文件权限设置

---

**注意：** 首次部署建议从Streamlit Cloud开始，因为配置最简单且免费。