# 🎉 Aigroup Video MCP - PyPI发布成功！

## 📦 包信息

- **包名**: `aigroup-video-mcp`
- **当前版本**: 1.1.0 (PyPI最新版本)
- **我们发布的版本**: 1.1.0
- **PyPI链接**: https://pypi.org/project/aigroup-video-mcp/
- **作者**: jackdark425 (您的PyPI账户)

## 🚀 安装方式

### 从PyPI安装（推荐）

```bash
# 安装最新版本
pip install aigroup-video-mcp

# 安装特定版本
pip install aigroup-video-mcp==1.1.0
```

### 验证安装

```bash
# 检查安装
aigroup-video-mcp --version

# 运行健康检查
aigroup-video-mcp health

# 查看帮助
aigroup-video-mcp --help
```

## 📋 快速使用

### 1. 设置环境变量

```bash
export DASHSCOPE_API_KEY=你的API密钥
```

### 2. 启动MCP服务器

```bash
# stdio模式（MCP客户端）
aigroup-video-mcp serve

# SSE模式（HTTP客户端）
aigroup-video-mcp serve --transport sse --port 3001
```

### 3. 命令行视频分析

```bash
# 分析视频
aigroup-video-mcp analyze video.mp4 --prompt "分析视频内容"

# 生成摘要
aigroup-video-mcp analyze video.mp4 --prompt "生成视频摘要"
```

## 🔧 MCP客户端配置

### Claude Desktop

```json
{
  "mcpServers": {
    "aigroup-video-mcp": {
      "command": "python",
      "args": [
        "-m",
        "aigroup_video_mcp.main",
        "serve"
      ],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      },
      "alwaysAllow": [
        "analyze_video",
        "summarize_video",
        "analyze_video_scenes",
        "analyze_video_custom",
        "validate_video_source"
      ],
      "disabled": false
      }
    }
  }
}
```

### Continue.dev

```json
{
  "mcp": {
    "aigroup-video-mcp": {
      "command": ["python", "-m", "aigroup_video_mcp.main", "serve"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      },
      "alwaysAllow": [
        "analyze_video",
        "summarize_video",
        "analyze_video_scenes",
        "analyze_video_custom",
        "validate_video_source"
      ],
      "disabled": false
      }
    }
  }
}
```

## 🛠️ 可用工具

| 工具名 | 功能 | 说明 |
|--------|------|------|
| `analyze_video` | 基础视频分析 | 全面分析视频内容 |
| `summarize_video` | 视频摘要 | 生成简洁/详细/通用摘要 |
| `analyze_video_scenes` | 场景分析 | 识别场景和转换 |
| `analyze_video_custom` | 自定义分析 | 灵活的自定义提示词 |
| `validate_video_source` | 源验证 | 检查视频格式和可访问性 |

## 📊 系统资源

| 资源URI | 功能 | 说明 |
|---------|------|------|
| `config://system` | 系统配置 | 完整配置信息 |
| `models://available` | 模型信息 | 可用模型列表 |
| `status://system` | 系统状态 | 健康检查和监控 |
| `stats://usage` | 使用统计 | 工具使用分析 |

## 🎯 支持的视频格式

- ✅ MP4 - 推荐格式
- ✅ AVI - 兼容性好
- ✅ MOV - Apple格式
- ✅ MKV - 高质量
- ✅ WebM - Web优化
- ✅ FLV - 流媒体

## 🔒 限制和要求

- **Python版本**: ≥ 3.8
- **最大文件大小**: 100MB
- **最大视频时长**: 1小时
- **API要求**: DashScope API密钥

## 📈 性能优化

### 推荐设置

```bash
# 高质量分析
aigroup-video-mcp analyze video.mp4 \
  --prompt "详细分析" \
  --temperature 0.3 \
  --max-tokens 2000

# 快速摘要
aigroup-video-mcp analyze video.mp4 \
  --prompt "简要摘要" \
  --temperature 0.7 \
  --max-tokens 500
```

## 🐛 故障排除

### 常见问题

1. **导入错误**
   ```bash
   pip install --upgrade aigroup-video-mcp
   ```

2. **API密钥问题**
   ```bash
   export DASHSCOPE_API_KEY=你的密钥
   ```

3. **权限问题**
   ```bash
   pip install --user aigroup-video-mcp
   ```

## 📞 支持和反馈

- **PyPI页面**: https://pypi.org/project/aigroup-video-mcp/
- **问题反馈**: 通过PyPI或GitHub提交
- **版本更新**: 定期检查PyPI获取最新版本

## 🎊 发布里程碑

- ✅ **v1.1.0** - 最新版本发布到PyPI
- ✅ **功能完整** - 5个核心工具 + 16个系统资源
- ✅ **文档完善** - 完整的使用指南和示例
- ✅ **测试验证** - 所有功能测试通过
- ✅ **MCP兼容** - 完全兼容MCP协议

---

**🏆 恭喜！您的aigroup-video-mcp已成功发布到PyPI，现在全世界的开发者都可以使用这个强大的视频分析MCP服务器了！**