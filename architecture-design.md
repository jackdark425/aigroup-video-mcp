# Aigroup-Video-MCP 项目架构设计说明

## 1. 项目概述

Aigroup-Video-MCP 是一个基于阿里云 DashScope 的视频多模态理解 MCP（Model Control Protocol）服务器，提供强大的视频内容分析功能。该项目旨在帮助开发者和企业用户快速理解和提取视频中的关键信息，支持视频摘要生成、场景识别、自定义分析等多种功能。

### 1.1 核心功能

- **视频内容分析**：支持通过 URL 或本地路径分析视频内容
- **智能摘要**：自动生成视频摘要和关键信息
- **场景识别**：识别视频中的主要场景和场景转换
- **自定义提示词**：支持灵活的自定义分析需求
- **MCP 协议支持**：完全兼容 MCP 协议，支持 stdio 模式运行
- **高性能处理**：基于异步处理，支持并发请求

### 1.2 技术特点

- 基于 Python 的模块化设计
- 使用 DashScope 进行视频多模态理解
- 基于 FastAPI 和异步处理实现高性能服务
- 使用 FastMCP 快速实现 MCP 协议服务部署
- 采用 MCP 协议进行标准化交互

### 1.3 技术依赖

项目依赖以下关键技术和库：

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)：用于实现 MCP 协议支持
- [阿里云DashScope SDK](https://github.com/dashscope/dashscope-sdk-python)：用于视频多模态理解
  - 包名: `dashscope`
  - 版本要求: `dashscope>=1.14.0`

项目使用 MCP Python SDK 中的 FastMCP 类来快速将 API 部署为 MCP 服务。FastMCP 提供了便捷的方式来创建符合 MCP 协议的服务，通过简单的初始化和配置，即可将我们的视频分析功能以标准化的方式暴露给客户端。

示例代码展示如何使用 FastMCP 初始化一个 MCP 服务：
```python
from mcp.server.fastmcp import FastMCP

# 初始化 MCP 服务，"Structured Output Example" 为服务名称
mcp = FastMCP("Structured Output Example")
```

### 1.4 部署架构

系统基于 FastMCP 实现并通过 stdio 传输模式运行，这是当前支持的主要部署方式。用户可以在本地环境中安装和运行该服务，通过标准输入输出与服务进行交互。

FastMCP 提供了简单易用的部署方式，通过封装底层的 MCP 协议交互细节，使得我们的视频分析服务可以快速暴露给各种 MCP 客户端。这种部署方式保证了服务的标准化和跨平台兼容性。

环境要求：
- Python 3.8+
- DashScope API Key
- 依赖库：mcp (Python MCP SDK), dashscope, pydantic, fastapi, loguru 等

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                  Client Applications                        │
│  (CLI, Python API, MCP-compatible clients)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │  MCP Protocol (stdio)
┌─────────────────────▼───────────────────────────────────────┐
│                   MCP Server Layer                          │
│              (mcp_server.py)                                │
├─────────────────────┬───────────────────────────────────────┤
│        Tool         │              Resource                  │
│      Management     │            Management                 │
│  (tools/base.py)    │     (resources/base.py)               │
└─────────────────────┼───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  Core Analysis Layer                        │
│              (core/analyzer.py)                             │
├─────────────────────────────────────────────────────────────┤
│                 Configuration Management                    │
│                 (settings.py)                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 DashScope API Layer                         │
│              (Alibaba Cloud Services)                       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 架构层次说明

系统采用分层架构设计，从上到下分为以下几个层次：

1. **客户端应用层**：包括命令行接口、Python API 和兼容 MCP 协议的客户端
2. **MCP 服务层**：负责处理 MCP 协议请求，管理工具和资源
3. **核心分析层**：提供视频分析的核心功能实现
4. **配置管理层**：统一管理系统配置
5. **底层服务层**：阿里云 DashScope API 服务

## 3. 模块设计

### 3.1 核心模块

#### 3.1.1 配置管理模块 (settings.py)

配置管理模块基于 Pydantic v2 实现，支持环境变量和配置文件，提供以下子配置：

- **DashScopeSettings**：DashScope API 配置
- **VideoSettings**：视频处理配置
- **MCPSettings**：MCP 服务配置
- **LogSettings**：日志配置
- **SecuritySettings**：安全配置

该模块采用单例模式，确保全局配置的一致性。

#### 3.1.2 视频分析模块 (core/analyzer.py)

视频分析模块是系统的核心，提供异步视频分析功能：

- **AsyncVideoAnalyzer**：异步视频分析器，支持基础分析、摘要分析、场景分析等功能
- **VideoAnalyzer**：同步视频分析器，兼容性包装

主要功能包括：
- 视频源验证
- 基础视频分析
- 视频摘要分析
- 场景分析
- 自定义提示词分析

#### 3.1.3 MCP 服务模块 (server/mcp_server.py)

MCP 服务模块实现了标准的 MCP 服务器，支持以下功能：

- 工具列表管理
- 工具调用处理
- 资源列表管理
- 资源读取处理

使用官方 MCP SDK 实现，支持 stdio 传输模式。

### 3.2 工具模块 (tools/)

工具模块实现了各种视频分析工具，所有工具都继承自 VideoAnalysisTool 基类：

- **AnalyzeVideoTool**：基础视频分析工具
- **SummarizeVideoTool**：视频摘要工具
- **AnalyzeVideoScenesTool**：视频场景分析工具
- **AnalyzeVideoCustomTool**：自定义视频分析工具
- **ValidateVideoSourceTool**：视频源验证工具

工具模块采用注册表模式管理所有工具实例。

### 3.3 资源模块 (resources/)

资源模块提供系统相关信息的访问接口，所有资源都继承自 MCPResource 基类：

- **ConfigResource**：配置资源
- **ModelsResource**：模型资源
- **StatusResource**：状态资源
- **UsageStatsResource**：使用统计资源

资源模块同样采用注册表模式管理所有资源实例。

