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
另外，项目完成了两个实际用于训练的数据版本：

| 标签 | 特征变化 |
|---|---|
| training-data-v1 | 当前及历史浓度滞后值、目标日历特征 |
| training-data-v2 | 在 v1 上增加 1、3、24 小时浓度变化特征 |

两个版本的样本和时间划分一致。v2 的验证 RMSE 略低，
但 MAE 略高，因此应用继续使用 v1 特征模型。

数据版本、训练提交号和 DVC 哈希见
[数据说明](ml/README_data.md)；
完整对比与选择理由见
[实验说明](ml/README_experiments.md)。



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



## 9. 测试、分支与持续交付

本地检查命令：

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
```

当前共有 38 个测试案例，包含原有数据检查以及参数化边界测试，覆盖：

- 全年小时序列、特征样本和评估报告的一致性。
- 缺失字段、重复时间、时间间隔断开和非法浓度。
- 零浓度与缺失值的保留。
- 历史长度不足、滞后值和下一小时目标的对应关系。
- 缺失观测对特征样本的影响。
- 修改未来浓度不会改变当前输入特征。
- 跨月预测、时间划分和目标小时日历编码。

开发与合并路径：

功能分支 → dev → staging → main

dev、staging、main 均设置分支保护：要求通过 PR 合并，
check-and-build 检查成功，且源分支与目标分支保持最新。
规则同样约束管理员；个人项目不要求其他成员审批。

GitHub Actions 触发方式：

| 事件 | 检查、测试与 Docker 构建 | 环境交付 |
|---|---|---|
| PR 目标为 dev/staging/main | 执行 | 跳过 |
| 推送到 dev | 执行 | 跳过 |
| 推送到 staging | 执行 | staging |
| 推送到 main | 执行 | production |

环境交付必须在 CI 成功后运行。它使用对应 GitHub Environment
中的 Secrets 生成临时 .env 文件，构建带分支和提交号标签的镜像，
并在容器中运行 Streamlit AppTest，检查页面异常、标题和环境标识。

交付摘要以 delivery-summary.json 保存为工作流 Artifact，
保留 30 天。镜像在临时运行器中构建和验证，不推送到镜像仓库，
也不提供常驻的云端网页。

详细流程见 [DEPLOYMENT.md](DEPLOYMENT.md)。


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

## 12. 实验与交付证据

- [数据来源与两个训练版本](ml/README_data.md)
- [MLflow 实验及模型选择](ml/README_experiments.md)
- [当前应用模型登记](ml/registry/current_model.md)
- [数据和模型来源链](ml/PROVENANCE.md)
- [分支与环境交付流程](DEPLOYMENT.md)
- [MLflow 实验摘要](reports/mlflow_experiment_summary.csv)
- [MLflow 实验记录快照](reports/mlflow_experiment_records.json)
- [应用模型来源核对](reports/model_provenance.json)

实验快照用于核对本项目保存的历史结果，不替代 MLflow 后端。
本地 MLflow 数据库不提交到 Git；重新训练会生成新的运行 ID。

