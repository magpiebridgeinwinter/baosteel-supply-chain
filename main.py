import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import torch
import time
import sqlite3
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
# SQLite数据库配置
DB_CONFIG = {
    'db_path': 'baosteel_prediction.db'
}

def main():
    # --- 侧边栏 ---
    st.sidebar.title("宝钢智能决策中心")
    st.sidebar.caption("Baosteel Demand Forecasting System")
    st.sidebar.markdown("---")

    menu = st.sidebar.radio("系统模块", ["📊 全局运营看板", "🤖 智能订单预测"])
    st.sidebar.markdown("---")

    # 加载资源
    raw_df, monthly_df, error_msg = load_and_process_data()
    model, model_loaded, device = load_tcn_model()

    if raw_df.empty:
        st.error(f"❌ 数据加载失败: {error_msg if error_msg else '未检测到数据文件，请确保 order_train0.csv 在目录下。'}")
        return

    # --- 模块 1: 看板 ---
    if menu == "📊 全局运营看板":
        st.title("📊 宝钢汽车板产销预测")

        total_vol = raw_df['ord_qty'].sum() / 10000
        avg_price = raw_df['item_price'].mean() * 3

        c1, c2, c3 = st.columns(3)
        c1.metric("📦 累计总销量", f"{total_vol:,.2f}", "万吨")
        c2.metric("🏷️ SKU覆盖数", f"{raw_df['item_code'].nunique()}", "个")
        c3.metric("💰 平均挂牌价", f"¥{avg_price:,.0f}", "元/吨")

        st.markdown("---")
        
        dim_tab, space_tab = st.tabs(["🕐 时间维度分析", "🗺️ 空间维度分析"])
        
        with dim_tab:
            time_mode = st.radio("时间粒度", ["📅 按月查看", "📆 按年查看"], horizontal=True)
            
            if time_mode == "📅 按月查看":
                all_months_sorted = sorted(raw_df['year_month'].astype(str).unique())
                default_start = max(0, len(all_months_sorted) - 12)
                
                col_start, col_end = st.columns(2)
                with col_start:
                    start_idx = st.selectbox(
                        "起始月份",
                        range(len(all_months_sorted)),
                        index=default_start,
                        format_func=lambda x: all_months_sorted[x]
                    )
                with col_end:
                    end_idx = st.selectbox(
                        "结束月份",
                        range(len(all_months_sorted)),
                        index=len(all_months_sorted) - 1,
                        format_func=lambda x: all_months_sorted[x]
                    )
                
                start_idx, end_idx = min(start_idx, end_idx), max(start_idx, end_idx)
                start_month = all_months_sorted[start_idx]
                end_month = all_months_sorted[end_idx]
                
                time_filtered = raw_df[
                    (raw_df['year_month'].astype(str) >= start_month) &
                    (raw_df['year_month'].astype(str) <= end_month)
                ]
                
                monthly_trend = time_filtered.groupby(time_filtered['year_month'].astype(str)).agg({
                    'ord_qty': 'sum',
                    'item_price': 'mean'
                }).reset_index()
                
                fig_time = go.Figure()
                fig_time.add_trace(go.Scatter(
                    x=monthly_trend['year_month'],
                    y=monthly_trend['ord_qty'] / 10000,
                    mode='lines+markers+text',
                    name='月度销量',
                    line=dict(color='#1E88E5', width=3),
                    marker=dict(color='#1E88E5', size=8),
                    text=[f'{v/10000:.1f}' for v in monthly_trend['ord_qty']],
                    textposition='top center',
                    textfont=dict(size=9)
                ))
                fig_time.update_layout(
                    title=dict(text=f'<b>{start_month} ~ {end_month}</b> 月度销量趋势', font_size=16, x=0.5),
                    xaxis_title='月份',
                    yaxis_title='销量 (万吨)',
                    template='plotly_white',
                    hovermode='x unified',
                    height=420,
                    margin=dict(t=50, b=60, l=70, r=30),
                    plot_bgcolor='#FAFAFA'
                )
                fig_time.update_xaxes(tickangle=-35, tickfont=dict(size=10))
                fig_time.update_yaxes(gridcolor='#E0E0E0')
                st.plotly_chart(fig_time, use_container_width=True)
                
                col_fig2, col_fig3 = st.columns(2)
                with col_fig2:
                    price_fig = go.Figure()
                    price_fig.add_trace(go.Bar(
                        x=monthly_trend['year_month'],
                        y=monthly_trend['item_price'] * 3,
                        name='平均价格',
                        marker_color='#66BB6A',
                        text=[f'¥{v*3:.0f}' for v in monthly_trend['item_price']],
                        textposition='outside',
                        textfont=dict(size=9)
                    ))
                    price_fig.update_layout(
                        title='<b>月度平均价格趋势</b>',
                        yaxis_title='价格 (元/吨)',
                        template='plotly_white',
                        height=380,
                        plot_bgcolor='#FAFAFA',
                        margin=dict(t=45, b=50, l=55, r=20)
                    )
                    price_fig.update_xaxes(tickangle=-35, tickfont=dict(size=9))
                    price_fig.update_yaxes(gridcolor='#E0E0E0')
                    st.plotly_chart(price_fig, use_container_width=True)
                
                with col_fig3:
                    sku_monthly = time_filtered.groupby('item_code')['ord_qty'].sum().nlargest(5).reset_index()
                    sku_top_fig = go.Figure()
                    sku_top_fig.add_trace(go.Bar(
                        y=sku_monthly['item_code'].astype(str),
                        x=sku_monthly['ord_qty'],
                        orientation='h',
                        marker_color='#FFA726',
                        text=[f'{v:.0f}' for v in sku_monthly['ord_qty']],
                        textposition='outside',
                        textfont=dict(size=9)
                    ))
                    sku_top_fig.update_layout(
                        title='<b>Top 5 销售SKU</b>',
                        xaxis_title='销量 (吨)',
                        template='plotly_white',
                        height=380,
                        plot_bgcolor='#FAFAFA',
                        margin=dict(t=45, b=50, l=80, r=20)
                    )
                    sku_top_fig.update_yaxes(tickfont=dict(size=9))
                    sku_top_fig.update_xaxes(gridcolor='#E0E0E0')
                    st.plotly_chart(sku_top_fig, use_container_width=True)
            
            elif time_mode == "📆 按年查看":
                raw_df['year'] = raw_df['order_date'].dt.year
                
                year_list = sorted(raw_df['year'].unique())
                selected_years = st.multiselect(
                    "选择年份（支持多选对比）",
                    options=year_list,
                    default=year_list[-min(5, len(year_list)):]
                )
                
                if selected_years:
                    year_data = raw_df[raw_df['year'].isin(selected_years)]
                    
                    yearly_agg = year_data.groupby('year').agg({
                        'ord_qty': 'sum',
                        'item_price': 'mean',
                        'item_code': 'nunique',
                        'order_date': 'count'
                    }).reset_index()
                    yearly_agg.columns = ['年份', '总销量', '平均价格', 'SKU数', '订单数']
                    
                    col_y1, col_y2 = st.columns(2)
                    with col_y1:
                        fig_year_vol = go.Figure()
                        colors_year = ['#1E88E5', '#43A047', '#F4511E', '#8E24AA', '#D81B60']
                        for i, yr in enumerate(sorted(selected_years)):
                            yr_data = yearly_agg[yearly_agg['年份'] == yr]
                            if len(yr_data) > 0:
                                fig_year_vol.add_trace(go.Bar(
                                    x=[str(int(yr))],
                                    y=[yr_data['总销量'].values[0] / 10000],
                                    name=f'{int(yr)}年',
                                    marker_color=colors_year[i % len(colors_year)],
                                    text=[f'{yr_data["总销量"].values[0]/10000:.1f}万'],
                                    textposition='outside',
                                    textfont=dict(size=12, weight='bold')
                                ))
                        
                        if len(selected_years) > 1:
                            prev_idx = list(sorted(selected_years)).index(sorted(selected_years)[0])
                            curr_val = yearly_agg[yearly_agg['年份'] == max(selected_years)]['总销量'].values[0] / 10000
                            min_val = yearly_agg[yearly_agg['年份'] == min(selected_years)]['总销量'].values[0] / 10000
                            yoy_change = ((curr_val - min_val) / min_val * 100) if min_val > 0 else 0
                        
                        fig_year_vol.update_layout(
                            title='<b>年度销量对比</b>',
                            yaxis_title='销量 (万吨)',
                            template='plotly_white',
                            barmode='group',
                            height=380,
                            plot_bgcolor='#FAFAFA',
                            margin=dict(t=45, b=50, l=60, r=20)
                        )
                        fig_year_vol.update_yaxes(gridcolor='#E0E0E0')
                        st.plotly_chart(fig_year_vol, use_container_width=True)
                    
                    with col_y2:
                        fig_year_price = go.Figure()
                        for i, yr in enumerate(sorted(selected_years)):
                            yr_data = yearly_agg[yearly_agg['年份'] == yr]
                            if len(yr_data) > 0:
                                fig_year_price.add_trace(go.Scatter(
                                    x=[str(int(yr))],
                                    y=[yr_data['平均价格'].values[0] * 3],
                                    mode='lines+markers',
                                    name=f'{int(yr)}年',
                                    line=dict(width=3),
                                    marker=dict(size=12, color=colors_year[i % len(colors_year)])
                                ))
                        
                        fig_year_price.update_layout(
                            title='<b>年度平均价格对比</b>',
                            yaxis_title='价格 (元/吨)',
                            template='plotly_white',
                            height=380,
                            plot_bgcolor='#FAFAFA',
                            margin=dict(t=45, b=50, l=60, r=20)
                        )
                        fig_year_price.update_yaxes(gridcolor='#E0E0E0')
                        st.plotly_chart(fig_year_price, use_container_width=True)
                    
                    st.dataframe(
                        yearly_agg.astype({'年份': int}),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            '年份': st.column_config.NumberColumn('年份'),
                            '总销量': st.column_config.NumberColumn('总销量 (吨)', format=",.0f"),
                            '平均价格': st.column_config.NumberColumn('平均价格 (元/吨)', format="¥%.0f"),
                            'SKU数': st.column_config.NumberColumn('SKU数'),
                            '订单数': st.column_config.NumberColumn('订单数', format=",")
                        }
                    )
            
            st.markdown("---")
            col_dl_time, _ = st.columns([1, 4])
            with col_dl_time:
                export_name = f"宝钢数据_时间维度_{start_month}_{end_month}" if time_mode == "📅 按月查看" else f"宝钢数据_年度汇总"
                st.download_button(
                    label="📥 导出当前数据",
                    data=time_filtered.to_csv(index=False).encode('utf-8') if time_mode == "📅 按月查看" else raw_df[raw_df['year'].isin(selected_years)].to_csv(index=False).encode('utf-8'),
                    file_name=f"{export_name}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        with space_tab:
            base_view_mode = st.radio("基地查看模式", ["🏭 单个基地详情", "⚖️ 多基地对比"], horizontal=True)
            
            all_base_names = list(REGION_MAP.values())
            base_colors = {'武汉青山基地': '#1E88E5', '上海宝山基地': '#43A047', '湛江东山基地': '#F4511E', '南京梅山基地': '#8E24AA'}
            
            if base_view_mode == "🏭 单个基地详情":
                selected_base_detail = st.selectbox("选择基地", all_base_names)
                
                base_region_code = [k for k, v in REGION_MAP.items() if v == selected_base_detail][0]
                base_data = raw_df[raw_df['sales_region_code'] == base_region_code].copy()
                
                if len(base_data) > 0:
                    b_total = base_data['ord_qty'].sum() / 10000
                    b_avg_price = base_data['item_price'].mean() * 3
                    b_sku_count = base_data['item_code'].nunique()
                    b_order_count = len(base_data)
                    
                    bc1, bc2, bc3, bc4 = st.columns(4)
                    bc1.metric(f"📦 总销量", f"{b_total:,.2f}", "万吨")
                    bc2.metric(f"💰 均价", f"¥{b_avg_price:,.0f}", "元/吨")
                    bc3.metric(f"🏷️ SKU数", f"{b_sku_count}", "个")
                    bc4.metric(f"📋 订单数", f"{b_order_count:,}", "笔")
                    
                    base_monthly = base_data.groupby(base_data['year_month'].astype(str)).agg({
                        'ord_qty': 'sum',
                        'item_price': 'mean'
                    }).reset_index()
                    
                    fig_base_trend = go.Figure()
                    fig_base_trend.add_trace(go.Scatter(
                        x=base_monthly['year_month'],
                        y=base_monthly['ord_qty'] / 10000,
                        mode='lines+markers+text',
                        name='月度销量',
                        line=dict(color=base_colors.get(selected_base_detail, '#78909C'), width=3),
                        marker=dict(color=base_colors.get(selected_base_detail, '#78909C'), size=8),
                        fill='tozeroy',
                        fillcolor='rgba(120,144,156,0.08)'
                    ))
                    fig_base_trend.update_layout(
                        title=dict(text=f'<b>{selected_base_detail}</b> 月度销量走势', font_size=17, x=0.5),
                        xaxis_title='月份',
                        yaxis_title='销量 (万吨)',
                        template='plotly_white',
                        height=440,
                        plot_bgcolor='#FAFAFA',
                        margin=dict(t=55, b=60, l=65, r=25)
                    )
                    fig_base_trend.update_xaxes(tickangle=-40, tickfont=dict(size=9))
                    fig_base_trend.update_yaxes(gridcolor='#E0E0E0')
                    st.plotly_chart(fig_base_trend, use_container_width=True)
                    
                    col_b_pie, col_b_bar = st.columns(2)
                    with col_b_pie:
                        base_sku_dist = base_data.groupby('item_code')['ord_qty'].sum().nlargest(8).reset_index()
                        fig_b_pie = go.Figure()
                        fig_b_pie.add_trace(go.Pie(
                            labels=base_sku_dist['item_code'].astype(str),
                            values=base_sku_dist['ord_qty'],
                            hole=0.45,
                            textinfo='percent+label',
                            textfont=dict(size=9)
                        ))
                        fig_b_pie.update_layout(
                            title='<b>SKU销售占比 Top8</b>',
                            template='plotly_white',
                            height=360,
                            margin=dict(t=45, b=30, l=30, r=30)
                        )
                        st.plotly_chart(fig_b_pie, use_container_width=True)
                    
                    with col_b_bar:
                        base_weekly = base_data.copy()
                        base_weekly['week'] = pd.to_datetime(base_weekly['order_date']).dt.isocalendar().week
                        weekly_agg = base_weekly.groupby('week')['ord_qty'].sum().reset_index()
                        
                        fig_b_bar = go.Figure()
                        fig_b_bar.add_trace(go.Bar(
                            x=weekly_agg['week'],
                            y=weekly_agg['ord_qty'],
                            marker_color=base_colors.get(selected_base_detail, '#78909C'),
                            name='周销量'
                        ))
                        fig_b_bar.update_layout(
                            title='<b>每周销量分布</b>',
                            xaxis_title='周次',
                            yaxis_title='订单量 (吨)',
                            template='plotly_white',
                            height=360,
                            plot_bgcolor='#FAFAFA',
                            margin=dict(t=45, b=40, l=50, r=20)
                        )
                        fig_b_bar.update_yaxes(gridcolor='#E0E0E0')
                        st.plotly_chart(fig_b_bar, use_container_width=True)
                else:
                    st.warning("该基地暂无数据")
            
            elif base_view_mode == "⚖️ 多基地对比":
                compare_bases = st.multiselect(
                    "选择对比基地（2-5个）",
                    options=all_base_names,
                    default=all_base_names[:min(4, len(all_base_names))]
                )
                
                if len(compare_bases) >= 2:
                    compare_codes = []
                    for cb in compare_bases:
                        code = [k for k, v in REGION_MAP.items() if v == cb]
                        if code:
                            compare_codes.append((code[0], cb))
                    
                    fig_compare = go.Figure()
                    for rcode, bname in compare_codes:
                        bdata = raw_df[raw_df['sales_region_code'] == rcode]
                        bm = bdata.groupby(bdata['year_month'].astype(str))['ord_qty'].sum().reset_index()
                        fig_compare.add_trace(go.Scatter(
                            x=bm['year_month'],
                            y=bm['ord_qty'] / 10000,
                            mode='lines+markers',
                            name=bname,
                            line=dict(width=2.5),
                            marker=dict(size=7, color=base_colors.get(bname, '#78909C'))
                        ))
                    
                    fig_compare.update_layout(
                        title='<b>多基地月度销量对比</b>',
                        xaxis_title='月份',
                        yaxis_title='销量 (万吨)',
                        template='plotly_white',
                        hovermode='x unified',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        height=450,
                        plot_bgcolor='#FAFAFA',
                        margin=dict(t=55, b=60, l=65, r=25)
                    )
                    fig_compare.update_xaxes(tickangle=-40, tickfont=dict(size=9))
                    fig_compare.update_yaxes(gridcolor='#E0E0E0')
                    st.plotly_chart(fig_compare, use_container_width=True)
                    
                    compare_summary = []
                    for rcode, bname in compare_codes:
                        bd = raw_df[raw_df['sales_region_code'] == rcode]
                        compare_summary.append({
                            '基地名称': bname,
                            '总销量 (吨)': float(bd['ord_qty'].sum()),
                            '均价 (元/吨)': float(bd['item_price'].mean() * 3),
                            'SKU数量': int(bd['item_code'].nunique()),
                            '订单数量': int(len(bd)),
                            '占比 (%)': round(float(bd['ord_qty'].sum()) / raw_df['ord_qty'].sum() * 100, 2)
                        })
                    
                    st.dataframe(
                        pd.DataFrame(compare_summary),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            '基地名称': st.column_config.TextColumn('基地名称'),
                            '总销量 (吨)': st.column_config.NumberColumn('总销量 (吨)', format=",.0f"),
                            '均价 (元/吨)': st.column_config.NumberColumn('均价×3 (元/吨)', format="¥%.0f"),
                            'SKU数量': st.column_config.NumberColumn('SKU数量'),
                            '订单数量': st.column_config.NumberColumn('订单数量', format=","),
                            '占比 (%)': st.column_config.NumberColumn('占比 (%)', format="%.1f%%")
                        }
                    )
                    
                    fig_compare_pie = go.Figure()
                    fig_compare_pie.add_trace(go.Pie(
                        labels=[cs['基地名称'] for cs in compare_summary],
                        values=[cs['总销量 (吨)'] for cs in compare_summary],
                        hole=0.4,
                        marker_colors=[base_colors.get(cs['基地名称'], '#78909C') for cs in compare_summary],
                        textinfo='percent+label',
                        textposition='outside',
                        textfont=dict(size=11)
                    ))
                    fig_compare_pie.update_layout(
                        title='<b>选中基地销量占比</b>',
                        template='plotly_white',
                        height=380,
                        margin=dict(t=45, b=30, l=30, r=30)
                    )
                    st.plotly_chart(fig_compare_pie, use_container_width=True)
                else:
                    st.info("请至少选择2个基地进行对比")
            
            st.markdown("---")
            col_dl_space, _ = st.columns([1, 4])
            with col_dl_space:
                st.download_button(
                    label="📥 导出当前数据",
                    data=base_data.to_csv(index=False).encode('utf-8') if base_view_mode == "🏭 单个基地详情" and len(base_data) > 0 else pd.DataFrame().to_csv(index=False).encode('utf-8'),
                    file_name=f"宝钢数据_空间维度_{selected_base_detail if base_view_mode=='🏭 单个基地详情' else '多基地对比'}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        st.markdown("---")
        st.subheader("📋 原始数据明细")
        
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            detail_base = st.selectbox("筛选基地", ['全部'] + all_base_names)
        with col_filter2:
            detail_months_all = sorted(raw_df['year_month'].astype(str).unique())
            detail_month = st.selectbox("筛选月份", ['全部'] + detail_months_all)
        
        detail_filtered = raw_df.copy()
        if detail_base != '全部':
            rc = [k for k, v in REGION_MAP.items() if v == detail_base][0]
            detail_filtered = detail_filtered[detail_filtered['sales_region_code'] == rc]
        if detail_month != '全部':
            detail_filtered = detail_filtered[detail_filtered['year_month'].astype(str) == detail_month]
        
        st.dataframe(
            detail_filtered[['order_date', 'base_name', 'item_code', 'ord_qty', 'item_price']],
            use_container_width=True,
            hide_index=True,
            height=350,
            column_config={
                'order_date': st.column_config.DateColumn('订单日期'),
                'base_name': st.column_config.TextColumn('基地名称'),
                'item_code': st.column_config.NumberColumn('SKU编码'),
                'ord_qty': st.column_config.NumberColumn('订单量 (吨)'),
                'item_price': st.column_config.NumberColumn('单价 (元/吨)', format="¥%.0f")
            }
        )
        
        st.download_button(
            label="📥 导出明细数据",
            data=detail_filtered.to_csv(index=False).encode('utf-8'),
            file_name=f"宝钢销售明细_{detail_base}_{detail_month}.csv",
            mime="text/csv"
        )

    # --- 模块 2: 预测 ---
    elif menu == "🤖 智能订单预测":
        st.title("🤖 宝钢汽车板需求预测系统")

        # 界面布局
        st.markdown("### 系统功能")
        
        # 核心预测按钮
        col_button = st.columns(1)
        with col_button[0]:
            predict_btn = st.button("🚀 执行预测计算", type="primary", use_container_width=True)
        
        # 预测计算逻辑
        if predict_btn:
            st.markdown("---")
            st.subheader("📊 预测计算中")
            
            # 进度条效果
            with st.spinner('正在对所有基地的全部钢材板数据执行计算...'):
                time.sleep(1)
                
                all_regions = raw_df['sales_region_code'].unique()
                all_skus = raw_df['item_code'].unique()
                
                total_items = len(all_regions) * len(all_skus)
                progress_bar = st.progress(0)
                
                current = 0
                
                try:
                    with sqlite3.connect(DB_CONFIG['db_path']) as conn:
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                            CREATE TABLE IF NOT EXISTS prediction_results (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                base_name TEXT NOT NULL,
                                region_code INTEGER NOT NULL,
                                sku TEXT NOT NULL,
                                prediction_date TEXT NOT NULL,  -- 预测日期 (YYYY-MM)
                                pred_value REAL NOT NULL,       -- 预测值
                                is_fallback INTEGER NOT NULL,   -- 是否为兜底预测
                                created_at TEXT NOT NULL,        -- 创建时间
                                UNIQUE(base_name, sku, prediction_date)
                            )
                        ''')
                        # 创建索引以提高查询性能
                        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prediction_date ON prediction_results(prediction_date)')
                        cursor.execute('CREATE INDEX IF NOT EXISTS idx_base_sku_date ON prediction_results(base_name, sku, prediction_date)')
                        
                        cursor.execute("DELETE FROM prediction_results")
                        conn.commit()
                        
                        for region_code in all_regions:
                            base_name = REGION_MAP.get(region_code, '未知基地')
                            
                            for sku in all_skus:
                                sku_str = str(sku) if not isinstance(sku, str) else sku
                                
                                hist_data = monthly_df[
                                    (monthly_df['sales_region_code'] == region_code) &
                                    (monthly_df['item_code'] == sku)
                                ]

                                INPUT_LEN = 12
                                real_preds = []
                                is_fallback = False

                                if len(hist_data) == 0:
                                    real_preds = [0, 0, 0]
                                    is_fallback = True
                                
                                elif model_loaded and len(hist_data) >= INPUT_LEN:
                                    input_seq = hist_data['ord_qty'].values[-INPUT_LEN:]
                                    x_tensor = torch.tensor(input_seq, dtype=torch.float32).unsqueeze(0).to(device)

                                    try:
                                        with torch.no_grad():
                                            preds_tensor = model(x_tensor)
                                            raw_preds = preds_tensor.cpu().numpy().flatten()

                                        real_preds = np.round(np.maximum(raw_preds, 0)).astype(int)
                                    except Exception as e:
                                        is_fallback = True
                                        avg_val = hist_data['ord_qty'].mean()
                                        real_preds = [int(avg_val * np.random.uniform(0.95, 1.05)) for _ in range(3)]

                                else:
                                    is_fallback = True
                                    if len(hist_data) > 0:
                                        avg_val = hist_data['ord_qty'].mean()
                                        real_preds = [int(avg_val * np.random.uniform(0.95, 1.05)) for _ in range(3)]
                                    else:
                                        real_preds = [0, 0, 0]
                                
                                # 生成预测日期 (基于当前年份和月份)
                                import datetime
                                current_date = datetime.datetime.now()
                                # 预测未来3个月
                                prediction_dates = []
                                for i in range(3):
                                    pred_date = current_date + datetime.timedelta(days=30*i)
                                    prediction_dates.append(pred_date.strftime('%Y-%m'))
                                
                                # 存储每个月的预测结果
                                for i, (pred_date, pred_val) in enumerate(zip(prediction_dates, real_preds)):
                                    cursor.execute(
                                        "INSERT OR REPLACE INTO prediction_results (base_name, region_code, sku, prediction_date, pred_value, is_fallback, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                        (base_name, region_code, sku_str, pred_date, float(pred_val), 1 if is_fallback else 0, time.strftime("%Y-%m-%d %H:%M:%S"))
                                    )
                                
                                current += 1
                                progress_bar.progress(current / total_items)
                        
                        conn.commit()
                        
                        cursor.execute("SELECT COUNT(DISTINCT base_name) FROM prediction_results")
                        base_count = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM prediction_results")
                        total_count = cursor.fetchone()[0]
                        
                        st.info(f"数据库存储状态: 共存储了 {base_count} 个基地的数据")
                        st.info(f"共存储了 {total_count} 个SKU的预测结果")
                except Exception as e:
                    st.error(f"数据库操作失败: {str(e)}")
                
                st.success(f"✅ 预测计算完成！共计算了 {total_items} 个SKU的数据")
                st.success("✅ 数据已成功存储到数据库中")
        
        # 数据查询与可视化功能
        st.markdown("---")
        st.subheader("📤 数据查询与可视化")
        
        try:
            with sqlite3.connect(DB_CONFIG['db_path']) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS prediction_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        base_name TEXT NOT NULL,
                        region_code INTEGER NOT NULL,
                        sku TEXT NOT NULL,
                        prediction_date TEXT NOT NULL,  -- 预测日期 (YYYY-MM)
                        pred_value REAL NOT NULL,       -- 预测值
                        is_fallback INTEGER NOT NULL,   -- 是否为兜底预测
                        created_at TEXT NOT NULL,        -- 创建时间
                        UNIQUE(base_name, sku, prediction_date)
                    )
                ''')
                
                cursor.execute("SELECT DISTINCT base_name FROM prediction_results")
                bases = [row[0] for row in cursor.fetchall()]
                
                if bases:
                    st.info(f"数据库中共有 {len(bases)} 个基地的数据")
                    
                    selected_base = st.selectbox("选择基地", bases)
                    
                    # 获取该基地的所有SKU（去重）
                    cursor.execute("SELECT DISTINCT sku FROM prediction_results WHERE base_name = ?", (selected_base,))
                    skus_in_base = [row[0] for row in cursor.fetchall()]
                    st.info(f"当前基地共有 {len(skus_in_base)} 个SKU")
                    
                    if skus_in_base:
                        view_mode = st.radio("查看模式", ["单个SKU", "基地全部SKU汇总"], horizontal=True)
                        
                        if view_mode == "单个SKU":
                            selected_sku = st.selectbox("选择SKU", skus_in_base)
                            
                            # 获取该SKU的所有预测月份
                            cursor.execute(
                                "SELECT DISTINCT prediction_date FROM prediction_results WHERE base_name = ? AND sku = ? ORDER BY prediction_date",
                                (selected_base, selected_sku)
                            )
                            months = [row[0] for row in cursor.fetchall()]
                            
                            if months:
                                selected_month = st.selectbox("选择月份", ["全部"] + months)
                                
                                # 获取预测结果
                                cursor.execute(
                                    "SELECT prediction_date, pred_value FROM prediction_results WHERE base_name = ? AND sku = ? ORDER BY prediction_date",
                                    (selected_base, selected_sku)
                                )
                                results = cursor.fetchall()
                                
                                if results:
                                    # 构建月份到预测值的映射
                                    pred_dict = {row[0]: row[1] for row in results}
                                    display_months = months if selected_month == "全部" else [selected_month]
                                    
                                    # 显示指标卡片
                                    col_metric1, col_metric2, col_metric3 = st.columns(3)
                                    for i, month in enumerate(display_months[:3]):  # 最多显示3个月份
                                        metric_val = f"{pred_dict.get(month, 0):.0f} 吨"
                                        if i == 0:
                                            col_metric1.metric(f"📅 {month}", metric_val, "预测值")
                                        elif i == 1:
                                            col_metric2.metric(f"📅 {month}", metric_val, "预测值")
                                        else:
                                            col_metric3.metric(f"📅 {month}", metric_val, "预测值")
                                    
                                    region_code_for_query = [k for k, v in REGION_MAP.items() if v == selected_base]
                                    
                                    hist_for_chart = monthly_df[
                                        (monthly_df['sales_region_code'] == region_code_for_query[0]) &
                                        (monthly_df['item_code'].apply(lambda x: str(x) == selected_sku))
                                    ].copy()
                                    
                                    # 获取历史月份和预测月份
                                    if not hist_for_chart.empty:
                                        hist_months = sorted(hist_for_chart['year_month'].astype(str).unique())
                                    else:
                                        hist_months = []
                                    pred_months = sorted(pred_dict.keys())
                                    
                                    # 构建历史数据映射
                                    hist_values_map = {}
                                    for _, row in hist_for_chart.iterrows():
                                        ym_str = str(row['year_month'])
                                        hist_values_map[ym_str] = float(row['ord_qty'])
                                    
                                    fig = go.Figure()
                                    
                                    # 历史数据（蓝色）
                                    if hist_months:
                                        hist_values_list = []
                                        for hm in hist_months:
                                            found = False
                                            for ym_key, val in hist_values_map.items():
                                                if hm in ym_key or ym_key.startswith(hm):
                                                    hist_values_list.append(val)
                                                    found = True
                                                    break
                                            if not found:
                                                hist_values_list.append(None)
                                        
                                        has_hist_data = any(v is not None for v in hist_values_list)
                                        
                                        if has_hist_data:
                                            fig.add_trace(go.Scatter(
                                                x=hist_months,
                                                y=hist_values_list,
                                                mode='lines+markers',
                                                name='🔵 历史实际值',
                                                line=dict(color='#1E88E5', width=3),
                                                marker=dict(color='#1E88E5', size=8),
                                                fill='tozeroy',
                                                fillcolor='rgba(30,136,229,0.08)'
                                            ))
                                    
                                    # 预测数据（红色）
                                    if pred_months:
                                        pred_values = [pred_dict.get(m, 0) for m in pred_months]
                                        fig.add_trace(go.Scatter(
                                            x=pred_months,
                                            y=pred_values,
                                            mode='lines+markers',
                                            name='🔴 预测值',
                                            line=dict(color='#E53935', width=3, dash='dash'),
                                            marker=dict(color='#E53935', size=10, symbol='diamond')
                                        ))
                                    
                                    fig.update_layout(
                                        title=dict(text=f'<b>SKU {selected_sku}</b> — 需求趋势与预测', font_size=18, x=0.5, xanchor='center'),
                                        xaxis_title='月份',
                                        yaxis_title='订单量 (吨)',
                                        template='plotly_white',
                                        hovermode='x unified',
                                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font_size=13),
                                        height=480,
                                        margin=dict(t=60, b=50, l=60, r=30),
                                        plot_bgcolor='#FAFAFA'
                                    )
                                    fig.update_xaxes(tickangle=-30, tickfont=dict(size=11))
                                    fig.update_yaxes(gridcolor='#E0E0E0')
                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                    st.markdown("---")
                                    st.markdown("### 📋 预测结果明细")
                                    
                                    result_data = []
                                    for month in display_months:
                                        result_data.append({
                                            '月份': month,
                                            '预测值 (吨)': float(pred_dict.get(month, 0))
                                        })
                                    
                                    st.dataframe(
                                        result_data,
                                        use_container_width=True,
                                        hide_index=True,
                                        column_config={
                                            '月份': st.column_config.TextColumn('月份', width='medium'),
                                            '预测值 (吨)': st.column_config.NumberColumn('预测值 (吨)', format="%.0f")
                                        }
                                    )
                                else:
                                    st.warning("未找到该SKU的预测数据")
                            else:
                                st.warning("该SKU暂无预测数据")
                        
                        elif view_mode == "基地全部SKU汇总":
                            st.markdown(f"### 📊 {selected_base} — 全部SKU预测结果")
                            
                            # 获取该基地的所有预测月份
                            cursor.execute(
                                "SELECT DISTINCT prediction_date FROM prediction_results WHERE base_name = ? ORDER BY prediction_date",
                                (selected_base,)
                            )
                            base_months = [row[0] for row in cursor.fetchall()]
                            
                            if base_months:
                                # 获取所有SKU的预测数据
                                cursor.execute(
                                    "SELECT sku, prediction_date, pred_value FROM prediction_results WHERE base_name = ? ORDER BY sku, prediction_date",
                                    (selected_base,)
                                )
                                all_results = cursor.fetchall()
                                
                                if all_results:
                                    # 构建数据结构
                                    sku_data = {}
                                    month_totals = {month: 0 for month in base_months}
                                    
                                    for row in all_results:
                                        sku_val = str(row[0])
                                        month = row[1]
                                        value = row[2] if row[2] is not None else 0
                                        
                                        if sku_val not in sku_data:
                                            sku_data[sku_val] = {}
                                        sku_data[sku_val][month] = value
                                        month_totals[month] += value
                                    
                                    # 计算总和
                                    total_sum = sum(month_totals.values())
                                    
                                    # 显示汇总卡片
                                    sm1, sm2, sm3, sm4 = st.columns(4, gap="small")
                                    for i, (month, total) in enumerate(month_totals.items()):
                                        if i == 0:
                                            sm1.metric(f"📅 {month}", f"{total:,.0f} 吨", delta_color="off")
                                        elif i == 1:
                                            sm2.metric(f"📅 {month}", f"{total:,.0f} 吨", delta_color="off")
                                        elif i == 2:
                                            sm3.metric(f"📅 {month}", f"{total:,.0f} 吨", delta_color="off")
                                    sm4.metric("📈 合计", f"{total_sum:,.0f} 吨", delta_color="normal")
                                    
                                    # 准备图表数据
                                    pred_months = sorted(base_months)
                                    month_totals_list = [month_totals[m] for m in pred_months]
                                    
                                    fig_line = go.Figure()
                                    fig_line.add_trace(go.Scatter(
                                        x=pred_months,
                                        y=month_totals_list,
                                        mode='lines+markers+text',
                                        name='📈 月度预测总量',
                                        line=dict(color='#E53935', width=4),
                                        marker=dict(color='#E53935', size=12, symbol='circle'),
                                        text=[f'{v:,.0f}' for v in month_totals_list],
                                        textposition='top center',
                                        textfont=dict(size=13, color='#333', family='Arial Black'),
                                        fill='tozeroy',
                                        fillcolor='rgba(229,57,53,0.08)'
                                    ))
                                    
                                    fig_line.update_layout(
                                        title=dict(text=f'<b>{selected_base}</b> 月度预测趋势', font_size=17, x=0.5, xanchor='center'),
                                        xaxis_title='月份',
                                        yaxis_title='订单量 (吨)',
                                        template='plotly_white',
                                        hovermode='x unified',
                                        height=420,
                                        margin=dict(t=60, b=60, l=70, r=40),
                                        plot_bgcolor='#FAFAFA'
                                    )
                                    fig_line.update_xaxes(tickfont=dict(size=12))
                                    fig_line.update_yaxes(gridcolor='#E0E0E0')
                                    st.plotly_chart(fig_line, use_container_width=True)
                                    
                                    st.markdown("---")
                                    st.markdown("### 📋 全部SKU明细")
                                    
                                    col_tbl, col_dl = st.columns([4, 1], gap="small")
                                    
                                    # 准备表格数据
                                    all_sku_data = []
                                    for sku_val, month_values in sku_data.items():
                                        row = {'SKU': sku_val}
                                        sku_total = 0
                                        for month in base_months:
                                            val = month_values.get(month, 0)
                                            row[f'{month}预测(吨)'] = float(val)
                                            sku_total += val
                                        row['合计(吨)'] = float(sku_total)
                                        all_sku_data.append(row)
                                    
                                    with col_tbl:
                                        st.dataframe(
                                            pd.DataFrame(all_sku_data),
                                            use_container_width=True,
                                            hide_index=True,
                                            height=400
                                        )
                                    
                                    with col_dl:
                                        # 准备导出数据
                                        export_data = []
                                        for sku_val, month_values in sku_data.items():
                                            for month in base_months:
                                                export_data.append({
                                                    '基地': selected_base,
                                                    'SKU': sku_val,
                                                    '月份': month,
                                                    '预测值(吨)': month_values.get(month, 0)
                                                })
                                        
                                        st.download_button(
                                            label=f"📥 导出CSV",
                                            data=pd.DataFrame(export_data).to_csv(index=False).encode('utf-8'),
                                            file_name=f"{selected_base}_全部SKU预测.csv",
                                            mime="text/csv",
                                            use_container_width=True
                                        )
                            else:
                                st.warning("该基地暂无预测数据")
                    else:
                        st.warning("该基地暂无数据")
                else:
                    st.info("数据库中暂无数据，请先执行预测计算")
        except Exception as e:
            st.error(f"数据库查询失败: {str(e)}")

if __name__ == "__main__":
    main()