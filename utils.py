import pandas as pd
import torch
from models import TCN

# 区域映射字典
REGION_MAP = {
    101: '上海宝山基地 (HQ)', 102: '武汉青山基地', 103: '湛江东山基地',
    104: '南京梅山基地', 105: '韶关钢铁基地'
}


def load_tcn_model():
    """加载pth模型"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = TCN()
    try:
        # map_location 确保在没有 GPU 的电脑上也能跑
        model.load_state_dict(torch.load("./tcn_model.pth", map_location=torch.device('cpu')))
        model.to(device)
        model.eval()
        return model, True, device
    except FileNotFoundError:
        return model, False, device
    except Exception as e:
        return model, False, device


def load_and_process_data():
    """读取并清洗数据"""
    try:
        df = pd.read_csv('order_train0.csv')

        df['order_date'] = pd.to_datetime(df['order_date'])
        df['base_name'] = df['sales_region_code'].map(REGION_MAP).fillna('其他协同工厂')
        df['year_month'] = df['order_date'].dt.to_period("M")

        # 聚合为月度数据 (用于TCN输入)
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
    """获取设备信息"""
    return "cuda" if torch.cuda.is_available() else "cpu"