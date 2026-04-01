#!/bin/bash

# 宝钢板材智慧供应链系统 - 快速部署脚本

echo "========================================="
echo "宝钢板材智慧供应链系统 - 部署脚本"
echo "========================================="
echo ""

# 检查Git是否安装
if ! command -v git &> /dev/null; then
    echo "❌ Git未安装，请先安装Git"
    exit 1
fi

# 检查是否在Git仓库中
if [ ! -d ".git" ]; then
    echo "📦 初始化Git仓库..."
    git init
    git add .
    git commit -m "Initial commit - 宝钢板材智慧供应链系统"
    echo "✅ Git仓库初始化完成"
else
    echo "✅ Git仓库已存在"
fi

# 检查是否有远程仓库
if ! git remote get-url origin &> /dev/null; then
    echo "⚠️  未配置远程仓库"
    echo "请执行以下命令添加远程仓库："
    echo "git remote add origin https://github.com/你的用户名/你的仓库名.git"
    echo ""
    echo "然后重新运行此脚本"
    exit 1
fi

echo ""
echo "🚀 开始部署..."
echo ""

# 推送到远程仓库
echo "📤 推送代码到远程仓库..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 代码推送成功！"
    echo ""
    echo "📋 下一步操作："
    echo "1. 访问 https://share.streamlit.io"
    echo "2. 点击 'New app'"
    echo "3. 选择您的GitHub仓库"
    echo "4. 选择 main.py 作为主文件"
    echo "5. 点击 'Deploy' 开始部署"
    echo ""
    echo "📖 详细部署指南请查看 DEPLOYMENT.md"
else
    echo ""
    echo "❌ 代码推送失败，请检查网络连接和Git配置"
    exit 1
fi