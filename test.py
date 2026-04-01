import plotly.express as px
import pandas as pd

# 准备算法输出的排班数据
data = [
    # 叉车1任务
    dict(Forklift="F1 (3米)", Start='2023-11-01 08:30:00', Finish='2023-11-01 10:00:00',
         Task="T001: A卸货->F (与F3协同)"),
    dict(Forklift="F1 (3米)", Start='2023-11-01 10:00:00', Finish='2023-11-01 10:05:00', Task="空驶转场"),
    dict(Forklift="F1 (3米)", Start='2023-11-01 10:05:00', Finish='2023-11-01 11:45:00', Task="T005: A卸货->E仓库"),

    # 叉车2任务 (5米高升)
    dict(Forklift="F2 (5米)", Start='2023-11-01 08:30:00', Finish='2023-11-01 09:30:00',
         Task="T002: E->B (超4米特种任务)"),
    dict(Forklift="F2 (5米)", Start='2023-11-01 09:30:00', Finish='2023-11-01 09:35:00', Task="空驶转场"),
    dict(Forklift="F2 (5米)", Start='2023-11-01 09:35:00', Finish='2023-11-01 11:35:00', Task="T004: 淋膜D->仓库E"),

    # 叉车3任务
    dict(Forklift="F3 (4米)", Start='2023-11-01 08:30:00', Finish='2023-11-01 10:00:00',
         Task="T001: A卸货->F (与F1协同)"),
    dict(Forklift="F3 (4米)", Start='2023-11-01 10:00:00', Finish='2023-11-01 10:05:00', Task="空驶转场"),
    dict(Forklift="F3 (4米)", Start='2023-11-01 10:05:00', Finish='2023-11-01 11:50:00', Task="T006: 拉丝C->淋膜D"),

    # 叉车4任务
    dict(Forklift="F4 (4米)", Start='2023-11-01 08:30:00', Finish='2023-11-01 11:30:00', Task="T003: 拉丝C->织造F")
]

df = pd.DataFrame(data)

# 生成交互式甘特图
fig = px.timeline(df, x_start="Start", x_end="Finish", y="Forklift", color="Task",
                  title="厂区叉车优化调度排班图 (车辆利用率 > 85%)")

# 倒序Y轴，让 F1 显示在最上面
fig.update_yaxes(autorange="reversed")

# 设置图表布局
fig.update_layout(
    xaxis_title="时间轴",
    yaxis_title="作业叉车",
    font=dict(size=14)
)

# 弹出浏览器显示可视化图表
fig.show()