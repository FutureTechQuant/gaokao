# Business-Unit-for-Gaokao 代码资产目录

这份目录用于回答：`Business-Unit-for-Gaokao` 组织下面的代码仓库分别是干什么的、当前应该怎么管理。

> 原则：这里先做代码资产盘点，不等同于业务任务清单。GitHub Project 可以用这些条目做卡片，再用字段标记状态、负责人和下一步。

## 总体分层

| 层级 | 作用 | 代表仓库 |
|---|---|---|
| 主线应用与运营入口 | 直接面向获客、咨询、AI 问答或运营动作 | `gaokao-volunteer-bot`, `gaokao-landing`, `invite`, `gaokao-tool` |
| 数据资产 | 存放高校、专业、薪资、AI 替代率等可复用数据 | `gaokao`, `gaokao-universities-data`, `gaokao-salary`, `ai-gaokao-jobs-china` |
| 数据采集/爬虫 | 从阳光高考、学职平台、掌上高考等来源采集数据 | `gaokao-xuezhi-crawler`, `gaokao-plans-crawler`, `gaokao-scores-crawler` 等 |
| 咨询交付工具 | 辅助咨询师、老师、本地交付或客户服务 | `gaokao-teacher-package`, `gaokao-zhiyuan-consulting-system-open` |
| 历史/参考资产 | 可参考但不应默认当主线继续开发 | `uni-app-gaokao`, `Zhangxuefeng-AI-gaokao`, `gaokao-crawler`, `python_for_gaokao` |

## 主线应用与运营入口

| 仓库 | 当前作用 | 建议状态 | 下一步 |
|---|---|---|---|
| `gaokao-volunteer-bot` | 高考志愿 AI 对话机器人；通过 Playwright/数据检索辅助回答志愿问题，是线上 AI 服务核心。 | 主线 AI 应用 | 继续围绕陕西 MVP、免责声明、数据引用和咨询转化优化。 |
| `gaokao-landing` | 高考宣传落地页，用于 6.25 报志愿前的广告/直播流量承接。线上地址包含 `ad.studybp.com` 与 `ad.yuanzhoulv.cloud`。 | 主线线上入口 | 保持转化文案、二维码、咨询入口和产品档位同步。 |
| `invite` | 高考志愿填报邀请码 H5，用于邀请注册和邀请码绑定。 | 主线转化工具 | 与运营系统/小程序账号体系确认接口和邀请码规则。 |
| `gaokao-tool` | 邀请码、license、充值、手机号查询等运营脚本集合。 | 运营工具 | 补 README，明确每个脚本用途、入参、风险和使用场景。 |

## 数据资产

| 仓库 | 当前作用 | 建议状态 | 下一步 |
|---|---|---|---|
| `gaokao` | 高考、专业、就业与升学决策的信息聚合主仓库，当前含信源摘要、结果数据和静态展示。 | 主线资料库 | 作为组织级代码资产目录和信源/数据总览入口。 |
| `gaokao-universities-data` | 全国高校基础数据库、专业目录、百度百科/MCP 采集结果和高校详情脚本；README 标注 2919 所高校基础库。 | 核心数据资产 | 明确哪些 JSON 是权威可用数据，哪些是中间产物或内容生成素材。 |
| `gaokao-salary` | 高考专业薪资数据与页面。 | 数据分析资产 | 作为专业选择/就业解释的辅助数据，不直接承诺就业收益。 |
| `ai-gaokao-jobs-china` | 根据专业和岗位数据计算专业 AI 当前替代风险指数。 | 数据分析资产 | 用于专业风险解释，输出需加方法说明和不确定性提示。 |

## 数据采集与爬虫

| 仓库 | 当前作用 | 建议状态 | 下一步 |
|---|---|---|---|
| `gaokao-xuezhi-crawler` | 爬取高考专业、院校、职业数据，目标包含阳光高考/CHSI 和学职平台/XZ，并保存阶段数据。 | 核心爬虫 | 作为阳光高考/学职平台主线爬虫之一，优先维护。 |
| `xuezhi-gaokao-crawler` | AI 协作开发的高考数据爬虫项目，含 AI 规范、架构和数据 schema 文档。 | 待合并/对比 | 与 `gaokao-xuezhi-crawler` 对比，保留有价值规范，避免重复维护两套。 |
| `sunshine-gaokao-scraper` | 阳光高考专业信息爬虫；README 明确网站有阿里云盾 WAF，自动化抓取可能受限。 | 数据爬虫/受限 | 保留为阳光高考采集方案和 WAF 经验参考，谨慎承诺稳定性。 |
| `gaokao-plans-crawler` | 掌上高考招生计划数据爬虫。 | 核心数据爬虫 | 与分数线、院校、专业等掌上高考爬虫统一调度和输出 schema。 |
| `gaokao-scores-crawler` | 掌上高考分数线数据爬虫。 | 核心数据爬虫 | 重点用于冲稳保/位次判断的数据输入。 |
| `gaokao-school-scores-crawler` | 掌上高考学校分数线爬虫。 | 核心数据爬虫 | 与 `gaokao-scores-crawler` 区分学校维度和专业/批次维度。 |
| `gaokao-special-crawler` | 掌上高考 special/major 数据爬虫。 | 数据爬虫 | 确认 special 数据业务含义后决定是否并入主数据管道。 |
| `gaokao-qiangji-crawler` | 强基计划数据爬虫。 | 数据爬虫 | 作为高端咨询/特殊招生解释的补充数据。 |
| `gaokao-jobs-crawler` | 掌上高考就业/岗位数据爬虫。 | 数据爬虫 | 与薪资、AI 替代率数据一起服务专业解释。 |
| `gaokao-department-crawler` | 掌上高考学校院系数据爬虫。 | 数据爬虫 | 用于院校/专业层级解释和学校详情补充。 |
| `gaokao-crawler-factory` | 爬虫工厂/管理项目，当前不定义单一目标站点。 | 工具/生成器 | 仅在需要批量生成爬虫时使用；否则保持低优先级。 |
| `gaokao-crawler` | 老高考数据爬虫，README 指向 `sxgk114.com` 等旧源；此前已判断旧 `sxgk114` 不是核心。 | 历史/待降级 | 不作为当前主线数据来源，必要时归档或仅保留参考。 |

## 咨询交付工具与参考系统

| 仓库 | 当前作用 | 建议状态 | 下一步 |
|---|---|---|---|
| `gaokao-teacher-package` | 咨询师/老师本地工具包，包含 UI、授权、数据管理、筛选等模块。 | 交付工具 | 确认是否仍用于线下咨询交付；若继续使用，补安装和使用说明。 |
| `gaokao-zhiyuan-consulting-system-open` | 高考志愿咨询系统开源版，含局域网前后端启动脚本和抓分数脚本。 | 参考/可复用 | 审计可复用模块，避免直接混入线上主线。 |
| `Zhangxuefeng-AI-gaokao` | fork 的本地知识库 + Qdrant + 大模型高考志愿咨询系统。 | 参考/fork | 只作为知识库/架构参考，避免当作自有主线维护。 |

## 历史、封存与待清理

| 仓库 | 当前作用 | 建议状态 | 下一步 |
|---|---|---|---|
| `uni-app-gaokao` | 2025 年立森的 uniapp 前端版本，README 写明暂时封存。 | 已封存 | 保留只读参考；不要作为当前小程序/前端主线。 |
| `gaokao-scheduler` | 调度/部署/浏览器自动化相关项目，含大量 Docker/部署文档。 | 待审计 | 需要确认它是否仍承担线上调度；未确认前不要删除。 |
| `python_for_gaokao` | 空仓或无明显内容。 | 待清理 | 如确认无内容，可归档或删除。 |

## 建议的 GitHub Project 字段

| 字段 | 用途 | 示例值 |
|---|---|---|
| `资产类型` | 代码属于哪一类 | 线上应用、落地页、爬虫、数据资产、运营工具、参考项目 |
| `业务状态` | 当前是否主线可用 | 主线使用、核心数据、待合并、待审计、已封存、历史废弃 |
| `当前用途` | 一句话说明仓库干什么 | 高考志愿 AI 对话机器人 |
| `下一步` | 管理动作 | 补 README、合并、归档、接入数据管道、继续维护 |
| `优先级` | 管理优先级 | P0、P1、P2 |
| `负责人` | 谁维护/判断 | Peter、技术、运营、咨询师 |

## 当前建议优先级

### P0：主线必须清楚

- `gaokao-volunteer-bot`
- `gaokao-landing`
- `invite`
- `gaokao-tool`
- `gaokao`

### P1：数据主线需要收敛

- `gaokao-universities-data`
- `gaokao-xuezhi-crawler`
- `gaokao-plans-crawler`
- `gaokao-scores-crawler`
- `gaokao-school-scores-crawler`

### P2：参考、封存、待清理

- `uni-app-gaokao`
- `gaokao-crawler`
- `python_for_gaokao`
- `Zhangxuefeng-AI-gaokao`
- `gaokao-zhiyuan-consulting-system-open`

## 后续整理原则

1. 不要让所有仓库都变成“主线”。主线只保留应用、落地页、运营工具、数据总览和核心爬虫。
2. 爬虫仓库需要统一输出 schema 和数据落点，否则后续 AI/报告系统难以使用。
3. fork 或开源参考项目只标为参考，不默认承诺维护。
4. 封存项目保留历史价值，但不进入当前业务排期。
5. Project 只管理状态，仓库用途说明以本文件和各仓库 README 为准。
