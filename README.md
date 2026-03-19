# Taiko Rating Pro — 太鼓达人谱面多维难度评定系统

## 项目简介

Taiko Rating Pro 是一个面向太鼓达人（太鼓の達人）谱面的多维难度评定系统。不同于传统的单一分数评估，本系统从 **七个基础维度** 同时分析谱面，并输出三种不同视角的目标难度：

- **过关难度** — 能否通关的整体压力
- **全连难度** — 全连（Full Combo）的操作难度
- **高精度难度** — 追求高良率的精确控制难度

所有评定结果均具备 **可解释性**：系统会标出最难的时间段、指出主要贡献维度，并生成简要文字说明。

## 设计目标

1. **多维度**：七个独立维度，覆盖速度、耐力、手法、节奏、读谱、精度、容错
2. **三类输出**：过关 / 全连 / 高精度，不混成单一分数
3. **可解释**：难点窗口 + 维度归因 + 文字说明
4. **可扩展**：维度算法、聚合公式、标准化参数均可独立替换
5. **纯 Python**：全部计算逻辑由 Python 实现，零外部服务依赖

## 快速开始

### 安装

```bash
# 克隆项目后在项目根目录执行
pip install -e ".[dev]"
```

### 命令行使用

```bash
# 评定单个 TJA 文件
taiko-rating examples/sample_easy.tja

# 以 JSON 输出
taiko-rating examples/sample_hard.tja --json --pretty

# 批量评定整个目录
taiko-rating batch examples/ --json -o results.json
```

### Python API 调用

```python
from taiko_rating.engine import RatingEngine

engine = RatingEngine()

# 从文件评定
result = engine.rate_file("examples/sample_hard.tja")

# 输出为字典
print(result.to_dict())

# 访问具体数据
for cr in result.chart_results:
    for br in cr.branch_results:
        print(f"{cr.course.label}: 过关={br.target_difficulties['pass']:.2f}")
        for dim in br.dimensions:
            print(f"  {dim.name}: {dim.normalized:.2f}/10")
```

### Web 界面

```bash
# 一键启动（推荐）
python start.py

# 1. 安装后端依赖
pip install flask

# 2. 构建前端（首次使用或前端代码更新后）
cd webui && npm install && npm run build && cd ..

# 3. 启动服务器
python -m taiko_rating.api --port 5000

# 浏览器访问 http://127.0.0.1:5000
```

开发模式（前端热更新）：

```bash
# 终端 1：启动后端
python -m taiko_rating.api --port 5000

# 终端 2：启动前端开发服务器
cd webui && npm run dev
# 浏览器访问 http://localhost:3000（自动代理 API 到 5000 端口）
```

### 运行测试

```bash
pytest tests/ -v
```

## 项目结构

```
src/taiko_rating/
├── models/          # 数据模型（谱面、结果、枚举）
├── parsers/         # 谱面解析器（TJA 格式）
├── features/        # 音符级特征提取（第一层）
├── analysis/        # 段落级滑窗分析（第二层）
├── dimensions/      # 七个基础维度计算模块
├── aggregation/     # 三类目标难度聚合（第三层）
├── normalization/   # 标准化模块
├── explanation/     # 可解释性输出生成
├── engine.py        # 评定引擎主流程
├── api.py           # Flask Web API
└── cli.py           # 命令行入口

webui/               # Vue 3 + Vite 前端
├── src/
│   ├── App.vue
│   └── components/  # FileUpload / RatingResult / DimensionChart / ...
├── package.json
└── vite.config.js

start.py             # 一键启动脚本（自动检查依赖 + 构建前端 + 启动服务）
```

## 计算流程

```
TJA 文件 → 解析器 → 标准化谱面数据
                          ↓
                   音符级特征提取（第一层）
                          ↓
                   段落级滑窗分析（第二层）
                          ↓
                   七维度独立计算
                          ↓
                   三类目标难度聚合（第三层）
                          ↓
                   难点窗口 + 解释生成
                          ↓
                      结果输出
```

## 输入数据格式

### TJA 格式

标准 TJA 格式，支持以下命令：

| 元数据 | 谱面命令 |
|--------|----------|
| TITLE, SUBTITLE | #START, #END |
| BPM, OFFSET | #BPMCHANGE |
| COURSE, LEVEL | #SCROLL |
| BALLOON | #MEASURE |
| GENRE, MAKER | #DELAY |
| WAVE, SIDE | #GOGOSTART, #GOGOEND |
| DEMOSTART | #BRANCHSTART, #N, #E, #M |

音符编码：`0`=空, `1`=咚, `2`=咔, `3`=大咚, `4`=大咔, `5`=连打, `6`=大连打, `7`=气球, `8`=结束, `9`=彩球

### JSON 格式（规划中）

未来版本将支持标准化 JSON 输入。

## 输出数据格式

### 谱面级结果 (BranchResult)

| 字段 | 说明 |
|------|------|
| song_title | 歌曲名 |
| course | 难度名 |
| branch_type | 分支类型 |
| target_difficulties | 三类目标难度 |
| dimensions | 七个维度评分 |
| hotspots | 难点窗口列表 |
| summary | 文字总结 |
| stats | 统计信息 |
| missing_fields | 缺失字段 |
| calc_version | 计算版本号 |

### 歌曲级结果 (SongResult)

| 字段 | 说明 |
|------|------|
| title | 歌曲名 |
| chart_results | 所有谱面评定结果 |
| overview | 概览摘要 |

详细维度定义请参见 [docs/dimensions.md](docs/dimensions.md)。

## 如何扩展新维度

参见 [docs/extending.md](docs/extending.md)。

## 当前限制

1. 第一版使用规则模型，公式参数为经验值，未经大规模样本标定
2. 手法复杂度使用简化规则版配手推断，非完整 DP 模型
3. 读谱复杂度使用代理特征，未建模真实视觉认知过程
4. 标准化参数为固定值，尚未支持外部标定文件
5. 仅支持 TJA 输入，JSON 输入格式待实现
6. 当前 WebUI 为基础版本（文件上传 / 文本粘贴 / 结果可视化），高级交互能力仍可继续扩展

## 未来改进方向

1. 基于 DP 的完整配手推断模型
2. 基于玩家数据的样本标定
3. JSON 谱面输入支持
4. Web 可视化界面（热力图）
5. 成对比较排序优化
6. 机器学习模型接入
7. 批量标定工具

## License

MIT
