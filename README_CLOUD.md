# 宝钢板材智慧供应链系统 - 云端部署版

## 🚀 快速开始

### 本地运行
```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run main.py
```

### 云端部署

#### 方式一：Streamlit Cloud（最简单）

1. **Windows用户：**
   ```cmd
   deploy.bat
   ```

2. **Linux/Mac用户：**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **访问 [https://share.streamlit.io](https://share.streamlit.io)**
   - 点击"New app"
   - 选择您的GitHub仓库
   - 选择main.py作为主文件
   - 点击"Deploy"

#### 方式二：Docker部署

```bash
# 构建并启动容器
docker-compose up -d

# 访问 http://localhost:8501
```

#### 方式三：Heroku部署

```bash
# 安装Heroku CLI后
heroku create
git push heroku main
heroku open
```

## 📁 项目结构

```
Taidi/
├── main.py                    # 主应用文件
├── models.py                  # TCN模型定义
├── utils.py                   # 工具函数
├── predict.py                 # 预测脚本
├── requirements.txt           # Python依赖
├── Procfile                  # Heroku配置
├── Dockerfile                # Docker配置
├── docker-compose.yml        # Docker编排
├── .streamlit/
│   ├── config.toml          # Streamlit配置
│   └── secrets.toml.example # 密钥配置示例
├── deploy.bat               # Windows部署脚本
├── deploy.sh               # Linux/Mac部署脚本
├── DEPLOYMENT.md           # 详细部署指南
└── README_CLOUD.md        # 本文件
```

## 🔧 配置说明

### Streamlit配置
编辑 `.streamlit/config.toml` 来自定义应用外观和行为。

### 环境变量
如需配置环境变量：
- **Streamlit Cloud**: 在项目设置中添加Secrets
- **Heroku**: 使用 `heroku config:set`
- **Docker**: 在 `docker-compose.yml` 中添加

## 📊 功能特性

- ✅ 全局运营看板
- ✅ 智能订单预测（TCN模型）
- ✅ 数据可视化图表
- ✅ 数据导出功能
- ✅ 响应式设计
- ✅ 云端部署支持

## 🛠️ 技术栈

- **前端**: Streamlit
- **数据处理**: Pandas, NumPy
- **可视化**: Plotly
- **机器学习**: PyTorch
- **部署**: Docker, Heroku, Streamlit Cloud

## 📖 详细文档

查看 [DEPLOYMENT.md](DEPLOYMENT.md) 了解：
- 详细的部署步骤
- 常见问题解决
- 性能优化建议
- 安全配置指南

## 🆘 故障排除

### 问题1：依赖安装失败
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题2：模型加载失败
- 确保 `tcn_model.pth` 文件在项目根目录
- 检查PyTorch版本兼容性

### 问题3：端口被占用
```bash
# 修改 .streamlit/config.toml 中的端口号
[server]
port = 8502
```

## 📝 更新日志

### v1.0.0 (2024-03-31)
- ✨ 初始版本发布
- 🚀 支持云端部署
- 📊 完整的数据可视化功能
- 🤖 TCN模型预测功能

## 📞 支持

如有问题，请查看：
1. [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南
2. [Streamlit文档](https://docs.streamlit.io)
3. 项目Issues页面

---

**注意**: 首次部署建议从Streamlit Cloud开始，配置最简单且免费。