# 贡献指南

感谢您对AI交易监控系统的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告问题
- 使用GitHub Issues报告bug或提出功能建议
- 在报告前请先搜索是否已有类似问题
- 提供详细的问题描述和复现步骤

### 提交代码
1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范
- 遵循PEP 8 Python代码规范
- 添加适当的注释和文档字符串
- 确保代码通过所有测试
- 保持代码简洁和可读性

## 开发环境设置

1. 克隆仓库
```bash
git clone https://github.com/your-username/nof1.ai.monitor.git
cd nof1.ai.monitor
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp env.example .env
# 编辑.env文件配置必要的参数
```

## 测试

在提交代码前，请确保：
- 运行测试模式验证功能正常
- 检查代码风格和语法
- 确保没有敏感信息泄露

```bash
python main.py --test
```

## 许可证

通过贡献代码，您同意您的贡献将在MIT许可证下发布。
