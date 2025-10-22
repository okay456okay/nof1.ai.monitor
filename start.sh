#!/bin/bash
# AI交易监控系统启动脚本

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先创建虚拟环境"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt 文件不存在"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖包..."
pip install -r requirements.txt

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  配置文件 .env 不存在"
    if [ -f "config.env.example" ]; then
        echo "📋 请复制 config.env.example 为 .env 并配置参数："
        echo "   cp config.env.example .env"
        echo "   然后编辑 .env 文件配置企业微信webhook等参数"
    fi
    exit 1
fi

# 检查企业微信webhook配置
if ! grep -q "WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com" .env; then
    echo "⚠️  企业微信webhook配置可能不正确"
    echo "请确保 .env 文件中的 WECHAT_WEBHOOK_URL 是有效的企业微信机器人地址"
fi

echo "🚀 启动AI交易监控系统..."
echo "📊 系统将每分钟检查一次持仓变化"
echo "📱 如有交易变化将发送企业微信通知"
echo "⏹️  按 Ctrl+C 停止监控"
echo ""

# 启动监控系统
python main.py
