# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import torch
from models import TCN
from utils import load_and_process_data, get_device
    
def predict_future(model, monthly_df, pred_df, input_len=12, device='cpu'):
    model.eval()
    results = []

    for _, row in pred_df.iterrows():
        region = row["sales_region_code"]
        item = row["item_code"]

        hist = monthly_df[
            (monthly_df.sales_region_code == region) &
            (monthly_df.item_code == item)
        ].sort_values("year_month")

        if len(hist) < input_len:
            continue

        x = hist["ord_qty"].values[-input_len:]
        x = torch.tensor(x, dtype=torch.float32).unsqueeze(0).to(device)

        with torch.no_grad():
            pred = model(x).cpu().numpy().flatten()

        results.append([region, item, *pred])

    return pd.DataFrame(
        results,
        columns=["sales_region_code", "item_code", "2019-01", "2019-02", "2019-03"]
    )

# 读取数据
df, monthly_df, error_msg = load_and_process_data()
if df.empty:
    print(f"数据加载失败: {error_msg}")
    exit(1)

# 读取预测SKU列表
try:
    pred_df = pd.read_csv('./predict_sku0.csv')
    if pred_df.empty:
        print("预测SKU列表为空")
        exit(1)
except Exception as e:
    print(f"读取预测SKU列表失败: {str(e)}")
    exit(1)

# 获取设备
device = get_device()

# 加载模型
try:
    model = TCN().to(device)
    model.load_state_dict(torch.load("./tcn_model.pth", map_location=torch.device(device)))
except Exception as e:
    print(f"加载模型失败: {str(e)}")
    exit(1)

# 执行预测
try:
    result_df = predict_future(model, monthly_df, pred_df, device=device)
    if result_df.empty:
        print("预测结果为空，请检查数据")
        exit(1)
except Exception as e:
    print(f"执行预测失败: {str(e)}")
    exit(1)

pred_cols = result_df.columns[2:]
# 1) 负数截断为0
result_df[pred_cols] = result_df[pred_cols].clip(lower=0)
# 2) 四舍五入为整数
result_df[pred_cols] = result_df[pred_cols].round(0)
# 3) 转成整型（去掉小数点）
result_df[pred_cols] = result_df[pred_cols].astype(int)

print(result_df)