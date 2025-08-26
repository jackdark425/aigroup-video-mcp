# Aigroup Video MCP 配置和使用指南

## 🎯 服务器状态确认

✅ **服务器健康检查通过**
- 5个视频分析工具已注册
- 16个系统资源已注册
- 配置验证成功
- DashScope API连接正常

## 🚀 启动方式

### 1. MCP模式（stdio传输）- 推荐用于MCP客户端

```bash
# 启动stdio模式服务器
python -m aigroup_video_mcp.main serve

# 或者使用简短命令（如果安装了包）
aigroup-video-mcp serve
```

### 2. SSE模式（HTTP传输）- 用于HTTP客户端

```bash
# 启动SSE服务器（默认localhost:3001）
python -m aigroup_video_mcp.main serve --transport sse

# 指定主机和端口
python -m aigroup_video_mcp.main serve --transport sse --host 0.0.0.0 --port 3001
```

## 📋 MCP客户端配置

### Claude Desktop配置

在Claude Desktop的配置文件中添加：

```json
{
  "mcpServers": {
    "aigroup-video-mcp": {
      "command": "python",
      "args": [
        "-m", "aigroup_video_mcp.main", "serve"
      ],
      "cwd": "d:/aigroup-video-mcp",
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

### Continue.dev配置

```json
{
  "mcp": {
    "aigroup-video-mcp": {
      "command": ["python", "-m", "aigroup_video_mcp.main", "serve"],
      "cwd": "d:/aigroup-video-mcp",
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

## 🛠️ 可用工具

### 1. analyze_video - 基础视频分析
```json
{
  "video_path": "path/to/video.mp4",
  "prompt": "请分析这个视频的内容",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### 2. summarize_video - 视频摘要
```json
{
  "video_path": "path/to/video.mp4", 
  "summary_type": "general"  // "brief", "general", "detailed"
}
```

### 3. analyze_video_scenes - 场景分析
```json
{
  "video_path": "path/to/video.mp4",
  "scene_detection": true,
  "detailed_analysis": false
}
```

### 4. analyze_video_custom - 自定义分析
```json
{
  "video_path": "path/to/video.mp4",
  "custom_prompt": "请识别视频中的所有文字内容",
  "analysis_focus": "text",
  "output_format": "structured",
  "language": "zh-CN"
}
```

### 5. validate_video_source - 源验证
```json
{
  "video_path": "path/to/video.mp4",
  "check_accessibility": true,
  "check_format": true,
  "check_size": true,
  "detailed_info": true
}
```

## 📊 可用资源

### 系统配置
- `config://system` - 完整系统配置
- `config://system/dashscope` - DashScope配置
- `config://system/video` - 视频处理配置

### 模型信息
- `models://available` - 可用模型列表
- `models://qwen-vl-max/capabilities` - 模型能力详情

### 系统状态
- `status://system` - 系统状态
- `status://service/health` - 健康检查

### 使用统计
- `stats://usage` - 使用统计
- `stats://usage/report/24h` - 24小时报告

## 🧪 测试命令

### 命令行测试
```bash
# 视频分析测试
python -m aigroup_video_mcp.main analyze 1.MOV --prompt "请分析视频内容"

# 健康检查
python -m aigroup_video_mcp.main health

# 服务器信息
python -m aigroup_video_mcp.main info

# 配置验证
python -m aigroup_video_mcp.main config
```

### HTTP客户端测试（SSE模式）
```bash
# 启动SSE服务器
python -m aigroup_video_mcp.main serve --transport sse --host localhost --port 3001

# 在新终端测试（需要支持MCP协议的HTTP客户端）
curl -X POST http://localhost:3001/tools/analyze_video \
  -H "Content-Type: application/json" \
  -d '{"video_path": "1.MOV", "prompt": "分析视频"}'
```

## ⚙️ 环境变量配置

确保设置了以下环境变量：

```bash
# 必需
export DASHSCOPE_API_KEY=你的API密钥

# 可选配置
export VIDEO__MAX_FILE_SIZE=104857600  # 100MB
export VIDEO__MAX_DURATION=3600        # 1小时
export MCP__MAX_CONCURRENT_REQUESTS=10
export LOG__LEVEL=INFO
export ENVIRONMENT=production
export DEBUG=false
```

## 🔍 支持的视频格式

- ✅ MP4
- ✅ AVI  
- ✅ MOV
- ✅ MKV
- ✅ WebM
- ✅ FLV

## 📈 性能配置

### 推荐设置
- **并发请求数**: 5-10个
- **最大文件大小**: 100MB
- **请求超时**: 300秒
- **温度参数**: 0.7（平衡创造性和准确性）

### 优化建议
1. 对于大视频文件，考虑压缩或裁剪
2. 使用具体的提示词获得更好的分析结果
3. 根据使用场景调整温度参数
4. 定期查看使用统计优化配置

## 🐛 故障排除

### 常见问题

1. **API密钥错误**
   ```
   错误: DashScope API key is required
   解决: 设置 DASHSCOPE_API_KEY 环境变量
   ```

2. **视频格式不支持**
   ```
   错误: Unsupported format
   解决: 转换为支持的格式或检查文件扩展名
   ```

3. **文件过大**
   ```
   错误: File too large
   解决: 压缩视频或调整 VIDEO__MAX_FILE_SIZE
   ```

### 调试模式
```bash
# 启用调试模式获取详细日志
python -m aigroup_video_mcp.main --debug serve
```

## 📞 支持

如有问题，请：
1. 查看日志文件获取详细错误信息
2. 运行健康检查确认系统状态
3. 检查环境变量配置
4. 确认视频文件格式和大小符合要求

---

**服务器已准备就绪，可以开始使用！** 🎉