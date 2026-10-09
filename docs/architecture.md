# 架构设计

## 一、为什么用「Agent + Skill」而不是写一个大脚本

| 方案 | 问题 |
|---|---|
| 一个大脚本处理所有业务 | 改一处可能影响全部；业务同学不会改代码 |
| 每个业务一个独立脚本 | 要记住哪个脚本、怎么传参，学习成本高 |
| **Agent + Skill（本项目）** | 每个 Skill 独立维护；用户只说自然语言，由 Agent 负责路由和传参 |

## 二、分层结构

```mermaid
flowchart TB
    subgraph 交互层
        A1[聊天窗口：自然语言]
        A2[文件：Excel / 截图]
    end
    subgraph 调度层
        B[AI Agent<br/>意图识别 · Skill 选择 · 参数抽取 · 异常追问]
    end
    subgraph 能力层["能力层（Skill）"]
        C1[开户助手]
        C2[防骚扰开白]
        C3[挂接查询]
        C3a[分配判定模块<br/>--alloc 独立开关]
        C4[分配结果查询]
        C5[周会纪要]
        C6[文档 / 表格 / 网页发布]
    end
    subgraph 数据层
        D1[(CRM)]
        D2[(工单系统)]
        D3[(在线文档 / 分配表)]
        D4[(会议转写)]
    end
    A1 & A2 --> B
    B --> C1 & C2 & C3 & C4 & C5 & C6
    C3 --> C3a
    C1 --> D1
    C2 --> D2
    C2 -.回填挂接.-> D1
    C3 --> D1
    C4 --> D3
    C5 --> D4
```

## 三、一个 Skill 由什么组成

```
skill-name/
├── SKILL.md      # 给 Agent 看的说明书：什么时候触发、流程、规则、注意事项
└── scripts/      # 确定性逻辑：API 调用、规则判定、Excel 读写
```

**设计原则：**
- **能写成规则的交给代码，需要理解的交给 Agent。** 分配判定、字段校验写在脚本里，结果稳定可测；读截图、理解用户意图、处理例外交给 Agent。
- **只在必要时停下来问人。** 字段缺失、截图缺失、信息冲突时才打断确认，其余情况直接执行。
- **结果可追溯。** 每笔操作都返回申请 ID 或工单号，并导出结果表。

## 四、典型执行流程：防骚扰批量提报

```mermaid
sequenceDiagram
    participant U as 运营
    participant A as Agent
    participant S as 防骚扰 Skill
    participant T as 工单系统
    participant C as CRM
    U->>A: 上传提报 Excel
    A->>S: 解析表格 + 自检（必填项 / ID 格式 / 截图）
    alt 字段缺失或冲突
        S-->>A: 返回问题清单
        A-->>U: 只就有问题的行确认
    end
    loop 每一条记录
        S->>T: 上传截图
        S->>T: 创建工单
        S->>C: 查询挂接信息
    end
    S-->>A: 结果 Excel（工单号 + 链接 + 挂接）
    A-->>U: 下载链接 + 汇总
```
