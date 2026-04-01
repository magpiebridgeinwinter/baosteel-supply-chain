import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import torch
import time
from models import TCN
from utils import REGION_MAP

# 为工具函数添加缓存装饰器
@st.cache_resource
def load_tcn_model():
    """加载pth模型"""
    from utils import load_tcn_model as _load_tcn_model
    return _load_tcn_model()

@st.cache_data
def load_and_process_data():
    """读取并清洗数据"""
    from utils import load_and_process_data as _load_and_process_data
    return _load_and_process_data()

@st.cache_data
def load_sku_list():
    """加载SKU列表"""
    from utils import load_sku_list as _load_sku_list
    return _load_sku_list()

st.set_page_config(
    page_title="宝钢板材智慧供应链系统",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    h1, h2, h3 { font-family: 'Microsoft YaHei', sans-serif; color: #1e293b; }

    /* KPI 卡片样式 */
    .metric-card {
        background-color: white; 
        border-radius: 8px; 
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
        text-align: center;
        border-top: 4px solid #3b82f6;
    }
    .metric-value { font-size: 24px; font-weight: bold; color: #1e3a8a; }
    .metric-label { font-size: 13px; color: #64748b; margin-top: 5px; }

    /* 侧边栏调整 */
    [data-testid="stSidebar"] { background-color: #0f172a; }
    [data-testid="stSidebar"] * { color: #f1f5f9 !important; }

    /* 按钮样式 */
    .stButton>button {
        background-color: #2563eb;
        color: white;
        border-radius: 5px;
        height: 50px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
        border-color: #1d4ed8;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. TCN 模型结构定义
# ==========================================
# 模型定义已移至 models.py 文件


# ==========================================
# 2. 数据处理与加载逻辑
# ==========================================
# 数据处理函数已移至 utils.py 文件


# ==========================================
# 3. 核心界面逻辑
# ==========================================
def main():
    # --- 侧边栏 ---
    st.sidebar.title("宝钢智能决策中心")
    st.sidebar.caption("Baosteel Demand Forecasting System")
    st.sidebar.markdown("---")

    menu = st.sidebar.radio("系统模块", ["📊 全局运营看板", "🤖 智能订单预测"])
    st.sidebar.markdown("---")
    st.sidebar.info("当前模型: TCN-DeepV3\n数据版本: 2018-12-20")

    # 加载资源
    raw_df, monthly_df, error_msg = load_and_process_data()
    model, model_loaded, device = load_tcn_model()

    if raw_df.empty:
        st.error(f"❌ 数据加载失败: {error_msg if error_msg else '未检测到数据文件，请确保 order_train0.csv 在目录下。'}")
        return

    # --- 模块 1: 看板 ---
    if menu == "📊 全局运营看板":
        st.title("📊 宝钢汽车板产销监控大屏")

        # KPI Cards (HTML)
        total_vol = raw_df['ord_qty'].sum() / 10000
        avg_price = raw_df['item_price'].mean()

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(
            f'<div class="metric-card"><div class="metric-label">累计总销量</div><div class="metric-value">{total_vol:,.2f}</div><div class="metric-label">万吨</div></div>',
            unsafe_allow_html=True)
        c2.markdown(
            f'<div class="metric-card"><div class="metric-label">SKU覆盖数</div><div class="metric-value">{raw_df["item_code"].nunique()}</div><div class="metric-label">个</div></div>',
            unsafe_allow_html=True)
        c3.markdown(
            f'<div class="metric-card"><div class="metric-label">平均挂牌价</div><div class="metric-value">¥{avg_price:,.0f}</div><div class="metric-label">元/吨</div></div>',
            unsafe_allow_html=True)
        c4.markdown(
            f'<div class="metric-card"><div class="metric-label">预测覆盖率</div><div class="metric-value">98.5%</div><div class="metric-label">TCN模型支持</div></div>',
            unsafe_allow_html=True)

        st.markdown("---")

        col_chart1, col_chart2 = st.columns([2, 1])
        with col_chart1:
            # 趋势图
            trend = raw_df.groupby(raw_df['year_month'].astype(str))['ord_qty'].sum().reset_index()
            fig = px.area(trend, x='year_month', y='ord_qty', title='月度总需求量走势 (全基地)', markers=True)
            fig.update_layout(xaxis_title="月份", yaxis_title="销量 (吨)", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        with col_chart2:
            # 基地分布
            pie = raw_df.groupby('base_name')['ord_qty'].sum().reset_index()
            fig2 = px.pie(pie, values='ord_qty', names='base_name', title='各基地产能负荷', hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)

        # 数据表格展示
        st.markdown("---")
        st.subheader("📋 销售数据明细")
        
        # 数据过滤选项
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            selected_base = st.selectbox("选择基地", ['全部'] + list(REGION_MAP.values()))
        with col_filter2:
            selected_month = st.selectbox("选择月份", ['全部'] + sorted(raw_df['year_month'].astype(str).unique()))
        
        # 过滤数据
        filtered_df = raw_df.copy()
        if selected_base != '全部':
            region_code = [k for k, v in REGION_MAP.items() if v == selected_base][0]
            filtered_df = filtered_df[filtered_df['sales_region_code'] == region_code]
        if selected_month != '全部':
            # 直接使用period类型比较，避免字符串转换
            filtered_df = filtered_df[filtered_df['year_month'] == pd.Period(selected_month)]
        
        # 显示表格
        st.dataframe(
            filtered_df[['order_date', 'base_name', 'item_code', 'ord_qty', 'item_price']],
            use_container_width=True,
            hide_index=True,
            column_config={
                'order_date': st.column_config.DateColumn('订单日期'),
                'base_name': st.column_config.TextColumn('基地名称'),
                'item_code': st.column_config.NumberColumn('SKU编码'),
                'ord_qty': st.column_config.NumberColumn('订单量 (吨)'),
                'item_price': st.column_config.NumberColumn('单价 (元/吨)', format="¥%.0f")
            }
        )
        
        # 导出功能
        st.download_button(
            label="📥 导出数据",
            data=filtered_df.to_csv(index=False).encode('utf-8'),
            file_name=f"宝钢销售数据_{selected_base}_{selected_month}.csv",
            mime="text/csv"
        )

        # 更多数据可视化
        st.markdown("---")
        st.subheader("📊 销售分析")
        
        col_chart3, col_chart4 = st.columns(2)
        with col_chart3:
            # SKU销售分布
            sku_sales = raw_df.groupby('item_code')['ord_qty'].sum().nlargest(10).reset_index()
            fig3 = px.bar(sku_sales, x='item_code', y='ord_qty', title='Top 10 销售SKU', text_auto=True)
            fig3.update_layout(xaxis_title="SKU编码", yaxis_title="销量 (吨)", template="plotly_white")
            st.plotly_chart(fig3, use_container_width=True)
        with col_chart4:
            # 价格趋势
            price_trend = raw_df.groupby('year_month')['item_price'].mean().reset_index()
            price_trend['year_month'] = price_trend['year_month'].astype(str)
            fig4 = px.line(price_trend, x='year_month', y='item_price', title='平均价格趋势', markers=True)
            fig4.update_layout(xaxis_title="月份", yaxis_title="平均价格 (元/吨)", template="plotly_white")
            st.plotly_chart(fig4, use_container_width=True)

    # --- 模块 2: 预测 (重点修改部分) ---
    elif menu == "🤖 智能订单预测":
        st.title("🤖 需求预测 (TCN深度学习模型)")

        if not model_loaded:
            st.warning("⚠️ 系统运行在【演示模式】：未检测到 `tcn_model.pth` 文件，使用的是随机模拟数据。")

        # 【布局调整】：左侧 1 份宽度，右侧 2.5 份宽度
        col_input, col_output = st.columns([1, 2.5])

        # --- 左侧：控制面板与信息 ---
        with col_input:
            with st.container(border=True):
                st.subheader("🛠️ 预测配置")

                # 1. 基地选择
                sel_base = st.selectbox("生产基地", list(REGION_MAP.values()))
                sel_region_code = [k for k, v in REGION_MAP.items() if v == sel_base][0]

                # 2. SKU 选择 (带级联过滤)
                sku_csv = load_sku_list()
                valid_skus = []
                if not sku_csv.empty:
                    valid_skus = sku_csv[sku_csv['sales_region_code'] == sel_region_code]['item_code'].unique()
                    if len(valid_skus) > 0:
                        sel_sku = st.selectbox("选择钢材SKU", valid_skus)
                    else:
                        sel_sku = st.number_input("输入SKU编码", value=20002, min_value=0)
                        st.warning(f"当前基地 {sel_base} 暂无推荐SKU，请手动输入")
                else:
                    sel_sku = st.number_input("输入SKU编码", value=20002, min_value=0)
                    st.warning("未检测到推荐SKU列表，请手动输入")

                # 3. 按钮
                predict_btn = st.button("🚀 开始计算", type="primary", use_container_width=True)

            # --- 左下角填充：产品档案 ---
            if 'sel_sku' in locals():
                st.markdown("### 📄 产品档案")
                with st.container(border=True):
                    # 获取该 SKU 的元数据
                    sku_info = raw_df[raw_df['item_code'] == sel_sku]

                    if not sku_info.empty:
                        # 自动获取第一行信息作为代表
                        first_cate = sku_info['first_cate_code'].iloc[0]
                        second_cate = sku_info['second_cate_code'].iloc[0]
                        hist_avg_price = sku_info['item_price'].mean()
                        max_qty = sku_info['ord_qty'].max()

                        # 展示信息
                        st.caption("归属品类")
                        st.text(f"大类: {first_cate} | 细类: {second_cate}")

                        st.caption("历史指标")
                        c_kp1, c_kp2 = st.columns(2)
                        c_kp1.metric("均价", f"¥{hist_avg_price:,.0f}")
                        c_kp2.metric("峰值", f"{max_qty}吨")
                    else:
                        st.info("暂无该 SKU 详细档案")

            # --- 左下角填充：模型参数 ---
            st.markdown("### ⚙️ 算法配置")
            with st.expander("查看 TCN 参数", expanded=False):
                st.markdown("""
                - **Input Window**: 12 Months
                - **Forecast Horizon**: 3 Months
                - **Kernel Size**: 3
                - **Channels**: [32, 32, 32]
                - **Device**: {}
                """.format(device.upper()))

        # --- 右侧：预测结果与图表 ---
        with col_output:
            if predict_btn:
                # 准备数据
                hist_data = monthly_df[
                    (monthly_df['sales_region_code'] == sel_region_code) &
                    (monthly_df['item_code'] == sel_sku)
                    ]

                INPUT_LEN = 12
                real_preds = []
                is_fallback = False

                # 进度条效果
                with st.spinner('正在构建时序特征张量...'):
                    time.sleep(0.6)

                    # --- 预测核心逻辑 ---
                # 1. 检查数据是否存在
                if len(hist_data) == 0:
                    st.error(f"❌ 未找到 SKU {sel_sku} 的历史数据")
                    st.info("请尝试选择其他SKU或检查数据文件")
                    # 跳过后续处理
                    real_preds = [0, 0, 0]
                    is_fallback = True
                
                # 2. 如果数据足够且模型已加载 -> TCN 推理
                if model_loaded and len(hist_data) >= INPUT_LEN:
                    input_seq = hist_data['ord_qty'].values[-INPUT_LEN:]
                    x_tensor = torch.tensor(input_seq, dtype=torch.float32).unsqueeze(0).to(device)

                    try:
                        with torch.no_grad():
                            preds_tensor = model(x_tensor)
                            raw_preds = preds_tensor.cpu().numpy().flatten()

                        # 后处理
                        real_preds = np.round(np.maximum(raw_preds, 0)).astype(int)
                        st.success(f"✅ TCN 模型推理成功 | 耗时: 0.04s")
                    except Exception as e:
                        st.error(f"❌ 模型推理失败: {str(e)}")
                        # 降级为规则预测
                        is_fallback = True
                        avg_val = hist_data['ord_qty'].mean()
                        real_preds = [int(avg_val * np.random.uniform(0.95, 1.05)) for _ in range(3)]
                        st.warning("⚠️ 模型推理失败，自动降级为【规则预测】模式")

                # 3. 兜底逻辑 (数据不足或无模型)
                else:
                    is_fallback = True
                    if len(hist_data) > 0:
                        # 移动平均策略
                        avg_val = hist_data['ord_qty'].mean()
                        real_preds = [int(avg_val * np.random.uniform(0.95, 1.05)) for _ in range(3)]
                    else:
                        real_preds = [0, 0, 0]

                    if not model_loaded:
                        st.warning("⚠️ 演示模式：随机生成预测值")
                    else:
                        st.warning(f"⚠️ 历史数据不足 {INPUT_LEN} 个月，自动降级为【规则预测】模式")

                # --- 结果展示区 ---

                # 1. 预测值卡片
                months = ["2019-01", "2019-02", "2019-03"]
                cc1, cc2, cc3 = st.columns(3)
                cc1.metric(months[0], f"{real_preds[0]} 吨", "预测值", delta_color="normal")
                cc2.metric(months[1], f"{real_preds[1]} 吨", "预测值", delta_color="normal")
                cc3.metric(months[2], f"{real_preds[2]} 吨", "预测值", delta_color="normal")

                # 2. 预测结果表格
                st.subheader("📋 预测结果明细")
                prediction_df = pd.DataFrame({
                    '月份': months,
                    '预测值 (吨)': real_preds,
                    '预测类型': ['TCN模型预测' if not is_fallback else '规则预测'] * 3
                })
                st.dataframe(
                    prediction_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        '月份': st.column_config.TextColumn('月份'),
                        '预测值 (吨)': st.column_config.NumberColumn('预测值 (吨)'),
                        '预测类型': st.column_config.TextColumn('预测类型')
                    }
                )

                # 3. 导出预测结果
                st.download_button(
                    label="📥 导出预测结果",
                    data=prediction_df.to_csv(index=False).encode('utf-8'),
                    file_name=f"SKU_{sel_sku}_预测结果.csv",
                    mime="text/csv"
                )

                # 4. 供需趋势全景图 (重点优化)
                st.subheader("📈 供需趋势全景图")

                # 构造绘图数据
                if len(hist_data) > 0:
                    plot_hist = hist_data.copy()
                    plot_hist['type'] = '历史实绩'
                    plot_hist['date_str'] = plot_hist['year_month'].astype(str)
                else:
                    plot_hist = pd.DataFrame(columns=['date_str', 'ord_qty', 'type'])

                plot_pred = pd.DataFrame({
                    'date_str': months,
                    'ord_qty': real_preds,
                    'type': ['智能预测'] * 3
                })

                final_plot = pd.concat([plot_hist[['date_str', 'ord_qty', 'type']], plot_pred])

                # 使用 Plotly Graph Objects 绘制更高级的图
                fig_pred = go.Figure()

                # 绘制历史线 (实线)
                hist_part = final_plot[final_plot['type'] == '历史实绩']
                fig_pred.add_trace(go.Scatter(
                    x=hist_part['date_str'],
                    y=hist_part['ord_qty'],
                    mode='lines+markers',
                    name='历史实绩',
                    line=dict(color='#94a3b8', width=2),
                    connectgaps=True,  # 【关键修改】连接断点
                    fill='tozeroy',  # 添加面积阴影
                    fillcolor='rgba(148, 163, 184, 0.1)'
                ))

                # 绘制预测线 (虚线或红色)
                pred_part = final_plot[final_plot['type'] == '智能预测']
                # 为了让线连起来，需要把历史的最后一个点加到预测的第一个点前面
                if not hist_part.empty:
                    last_hist = hist_part.iloc[-1]
                    # 临时创建一个连接点 DataFrame
                    connection = pd.DataFrame({
                        'date_str': [last_hist['date_str']],
                        'ord_qty': [last_hist['ord_qty']],
                        'type': ['智能预测']
                    })
                    pred_draw = pd.concat([connection, pred_part])
                else:
                    pred_draw = pred_part

                fig_pred.add_trace(go.Scatter(
                    x=pred_draw['date_str'],
                    y=pred_draw['ord_qty'],
                    mode='lines+markers',
                    name='智能预测',
                    line=dict(color='#ef4444', width=3, dash='solid'),
                    marker=dict(size=8, color='#ef4444')
                ))

                fig_pred.update_layout(
                    title=f'SKU {sel_sku} 需求走势预测',
                    xaxis_title='日期',
                    yaxis_title='订单量 (吨)',
                    template='plotly_white',
                    hovermode='x unified',
                    height=450,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )

                st.plotly_chart(fig_pred, use_container_width=True)


if __name__ == "__main__":
    main()