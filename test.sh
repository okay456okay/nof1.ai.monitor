#!/bin/bash
# AI交易监控系统测试脚本

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先创建虚拟环境"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

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

echo "🧪 测试AI交易监控系统..."
echo ""

# 测试通知功能
echo "📱 测试企业微信通知功能..."
python main.py --test

echo ""
echo "✅ 测试完成"
echo "如果看到 '测试通知发送成功'，说明配置正确"
echo "请检查企业微信群是否收到测试消息"
