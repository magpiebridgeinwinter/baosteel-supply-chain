import pandas as pd
import torch
from models import TCN

# 区域映射字典（4个基地）
REGION_MAP = {
    102: '武汉青山基地',
    101: '上海宝山基地',
    103: '湛江东山基地',
    100: '南京梅山基地'
}


BASE_REMAP = {
    105: 102,
    102: 101,
    101: 103,
    103: 100,
    104: 102
}


def load_tcn_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = TCN()
    try:
        model.load_state_dict(torch.load("./tcn_model.pth", map_location=torch.device('cpu')))
        model.to(device)
        model.eval()
        return model, True, device
    except FileNotFoundError:
        return model, False, device
    except Exception as e:
        return model, False, device


def load_and_process_data():
    try:
        df = pd.read_csv('order_train0.csv')

        df['order_date'] = pd.to_datetime(df['order_date'])
        
        df['sales_region_code'] = df['sales_region_code'].map(BASE_REMAP).fillna(df['sales_region_code'])
        df['sales_region_code'] = df['sales_region_code'].astype(int)
        
        df['base_name'] = df['sales_region_code'].map(REGION_MAP).fillna('其他协同工厂')
        df['year_month'] = df['order_date'].dt.to_period("M")

        monthly_df = (
            df.groupby(["sales_region_code", "item_code", "year_month"])["ord_qty"]
            .sum()
            .reset_index()
            .sort_values("year_month")
        )
        return df, monthly_df, ""
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), str(e)


def load_sku_list():
    try:
        return pd.read_csv('predict_sku0.csv')
    except Exception as e:
        return pd.DataFrame()


def get_device():
    return "cuda" if torch.cuda.is_available() else "cpu"
