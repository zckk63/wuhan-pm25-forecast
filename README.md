# Wuhan Next-Hour PM2.5 Forecast

\[!\[Project CI](https://github.com/zckk63/wuhan-pm25-forecast/actions/workflows/ci.yml/badge.svg)](https://github.com/zckk63/wuhan-pm25-forecast/actions/workflows/ci.yml)



使用武汉 2025 年逐小时空气质量历史数据，预测下一小时的 PM2.5 浓度，并通过 Streamlit 展示数据覆盖情况、模型评估结果和历史预测回放。



应用用于历史数据回放，不提供实时监测或实时预报。



\## 1. 数据来源与质量



数据来自 \[Quotsoft 中国空气质量历史数据归档](https://quotsoft.net/air/)，来源页注明数据来自中国环境监测总站发布的信息。



项目提取武汉城市级的 `PM2.5` 小时记录，不使用 `PM2.5\_24h` 替代小时浓度，也不将城市级数据视为单个监测站序列。时间按北京时间整理。



| 项目 | 数量 |

|---|---:|

| 数据范围 | 2025-01-01 至 2025-12-31 |

| 下载的每日源文件 | 365 |

| 全年应有小时数 | 8,760 |

| 有效 PM2.5 小时数 | 8,432 |

| 缺失小时数 | 328 |

| 源文件没有对应 PM2.5 记录 | 138 |

| 存在记录但浓度为空 | 190 |

| 总缺失率 | 3.7443% |



完整小时表保留缺失值。构建特征时，仅保留所需历史浓度及目标浓度均有效的样本，没有对缺失浓度进行插值。



相关说明与报告：



\- `data/README\_data.md`：数据来源和处理说明。

\- `reports/monthly\_coverage.csv`：逐月数据覆盖情况。

\- `reports/pm25\_missing\_hours.csv`：缺失小时明细。



\## 2. 预测任务与特征



预测目标为：在时刻 t，使用当前及历史信息预测 t+1 小时的 PM2.5 浓度，单位为 μg/m³。



输入特征包括：



\- 当前小时 PM2.5 浓度；

\- 过去 1、2、3、6、12、24 小时的 PM2.5 浓度；

\- 目标小时的周期编码；

\- 目标日期的星期信息。



目标小时和星期属于预测时已经确定的日历信息。目标浓度及其他未来实测浓度不进入输入特征。



\## 3. 时间划分与模型



按目标时间顺序划分数据，不进行随机打乱：



| 数据集 | 时间范围 | 有效特征样本 |

|---|---|---:|

| 训练集 | 2025 年 1—9 月 | 5,625 |

| 验证集 | 2025 年 10 月 | 529 |

| 测试集 | 2025 年 11—12 月 | 924 |

| 合计 | | 7,078 |



比较两个模型：



\- Persistence\_Baseline：预测下一小时浓度等于当前小时浓度。

\- RandomForest\_300\_leaf2：使用 300 棵树、最小叶节点样本数为 2 的随机森林回归模型。



验证后固定模型配置，再进行留出测试集评估。测试结果不用于反复调整参数。



\## 4. 评估结果



MAE 和 RMSE 的单位均为 μg/m³，数值越小越好。



\### 验证集



| 模型 | MAE | RMSE |

|---|---:|---:|

| Persistence\_Baseline | 2.1550 | 3.1007 |

| RandomForest\_300\_leaf2 | 2.0714 | 3.0616 |



\### 测试集



| 模型 | MAE | RMSE |

|---|---:|---:|

| Persistence\_Baseline | 3.3095 | 5.5019 |

| RandomForest\_300\_leaf2 | 3.1276 | 5.1290 |



随机森林在验证集和测试集上均优于持续性基线，但提升幅度有限，说明当前小时浓度本身已经具有较强的下一小时预测能力。



评估报告保存在：



\- `reports/validation\_metrics.csv`

\- `reports/test\_metrics.csv`

\- `reports/test\_predictions.csv`



这些结果来自 2025 年的历史时间划分，不能直接代表其他年份或实时运行时的效果。



\## 5. DVC 数据与模型版本



Git 保存代码、数据指针和评估报告；DVC 保存数据及导出的模型，并将其上传至 Azure Blob Storage。



Azure DVC 远程路径：



`azure://dvc/wuhan-pm25`



两个数据版本标签：



| Git 标签 | 数据版本内容 |

|---|---|

| `data-v1-source-audit` | 原始数据、小时数据整理和缺失审计 |

| `data-v2-lag-features` | 加入下一小时预测所需的滞后特征数据 |



导出的模型位于 `models/random\_forest`，通过 DVC 管理。模型导出后重新加载，并与保存的 924 条测试预测逐一核对，结果全部一致。



Azure 凭据保存在本地 `.dvc/config.local` 中，该文件被 Git 忽略。仓库不包含 SAS 令牌。



\## 6. MLflow 实验记录



MLflow 使用项目根目录下的 `mlflow.db` 记录实验，实验名称为：



`Wuhan\_PM25\_Next\_Hour`



实验记录包含模型参数、评估指标、代码提交号、特征数据 SHA-256 和模型文件，以便追踪训练结果对应的代码与数据。



本地 MLflow 数据库不提交到 GitHub。导出的应用模型由 DVC 和 Azure 保存。



\## 7. 本地运行



以下命令以 Windows PowerShell 为例。



\### 获取项目并安装依赖



```powershell

git clone https://github.com/zckk63/wuhan-pm25-forecast.git

Set-Location wuhan-pm25-forecast

python -m venv .venv

.\\.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt

```



\### 恢复数据和模型



先为 DVC 配置自己的有效 Azure 凭据，并将凭据保存在被忽略的本地配置中。数据恢复需要相应存储资源的读取和列出权限。



```powershell

.\\.venv\\Scripts\\dvc.exe pull

```



公开 GitHub 仓库提供代码和 DVC 指针；恢复 Azure 中的数据和模型仍需要访问凭据。



\### 启动仪表盘



```powershell

.\\.venv\\Scripts\\python.exe -m streamlit run app\\streamlit\_app.py

```



在浏览器打开：



http://localhost:8501



仪表盘提供数据覆盖情况、测试集模型指标、历史时刻选择、下一小时预测与实际值对照，以及预测趋势图。



本项目已在 Edge 浏览器验证显示和交互正常。



\### 查看本地 MLflow 实验



在项目根目录的 PowerShell 中运行：



```powershell

$trackingUri = "sqlite:///" + ((Join-Path (Get-Location).Path "mlflow.db") -replace '\\\\', '/')

.\\.venv\\Scripts\\mlflow.exe ui --backend-store-uri $trackingUri --host 127.0.0.1 --port 5000

```



在浏览器打开 http://127.0.0.1:5000。



首次克隆的仓库没有原开发环境的本地 MLflow 数据库，需要运行训练脚本生成实验记录。



\## 8. Docker 运行



构建镜像前，先通过 DVC 恢复处理后的数据和模型。



```powershell

docker build -t wuhan-pm25-forecast:0.1 .

docker run --rm -p 127.0.0.1:8501:8501 wuhan-pm25-forecast:0.1

```



在浏览器打开 http://localhost:8501。



镜像包含应用、处理后的数据、评估报告和导出模型。原始下载目录、DVC 缓存、虚拟环境及本地 Azure 凭据不进入镜像。



Docker 镜像已在本地成功构建并运行，容器内的仪表盘和预测结果已人工验证。



\## 9. 测试与持续集成



本地检查命令：



```powershell

.\\.venv\\Scripts\\ruff.exe check .

.\\.venv\\Scripts\\python.exe -m pytest -q

```



当前包含 4 项自动测试：



1\. 全年小时表的时间轴、唯一性和有效浓度数量。

2\. 特征样本数量、数据集划分及必要字段完整性。

3\. 每个样本的目标时间恰好比预测发起时间晚一小时。

4\. 随机森林的测试集 MAE 和 RMSE 优于持续性基线。



GitHub Actions 在推送到 main 后自动执行：



1\. 安装 Python 依赖。

2\. 运行 Ruff 代码检查。

3\. 使用 GitHub Secrets 从 Azure 恢复所需数据和模型。

4\. 运行 pytest。

5\. 构建 Docker 镜像。



工作流已成功运行通过。CI 中验证了镜像能够构建；容器内的页面和交互另外经过本地人工验证。



所需仓库 Secrets：



\- `AZURE\_STORAGE\_ACCOUNT`

\- `AZURE\_STORAGE\_SAS\_TOKEN`



\## 10. 主要目录



```text

app/                    Streamlit 仪表盘

data/                   数据说明、DVC 指针及数据目录

models/                 DVC 管理的导出模型

reports/                数据质量、评估指标和测试预测报告

scripts/                下载、审计、特征构建、训练和评估脚本

src/pm25\_forecast/      数据处理代码

tests/                  自动测试

.github/workflows/      GitHub Actions 配置

Dockerfile              Docker 镜像构建配置

```



\## 11. 局限与后续改进



\- 当前模型仅使用浓度历史和日历信息，尚未加入气象变量。

\- 数据为武汉城市级历史记录，不能用于解释单个监测站的变化。

\- 缺失时段会减少可用特征样本，完整样本的评估结果不能覆盖所有缺失场景。

\- 模型目前用于历史回放，尚未接入实时数据获取、定时重训和运行监控。

\- 后续可加入气象特征、扩展年份，并采用滚动时间验证评估模型稳定性。

