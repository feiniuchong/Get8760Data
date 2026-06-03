import streamlit as st
import hashlib

# ============ 登录验证配置 ============
# 设置用户名和密码（建议修改成你自己的）
VALID_USERNAME = "1276"
# 密码使用SHA256加密存储（实际密码是 "123456"）
VALID_PASSWORD_HASH = hashlib.sha256("1276".encode()).hexdigest()


def check_password():
    """验证用户登录"""

    # 如果已经登录，直接返回True
    if st.session_state.get("authenticated", False):
        return True

    # 显示登录表单
    st.title("🔐 用户登录")
    st.write("请输入用户名和密码")

    with st.form("login_form"):
        username = st.text_input("用户名", placeholder="请输入用户名")
        password = st.text_input("密码", type="password", placeholder="请输入密码")
        submit = st.form_submit_button("登录")

    # 验证逻辑
    if submit:
        # 加密输入的密码
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if username == VALID_USERNAME and password_hash == VALID_PASSWORD_HASH:
            st.session_state.authenticated = True
            st.success("✅ 登录成功！正在跳转...")
            st.rerun()
        else:
            st.error("❌ 用户名或密码错误，请重试！")
            return False

    return False


# 执行登录验证（放在所有代码之前）
if not check_password():
    st.stop()  # 如果未登录，停止后续代码执行

# ============ 以下是原有的所有代码 ============

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium  # 关键导入

st.set_page_config(page_title="气象数据下载工具", layout="wide")
st.title("🌍 全年8760h气象数据下载工具")
st.markdown("点击地图选择位置，获取全年逐时光资源（太阳能）和风资源数据(By LZP)")

# 会话状态初始化
if 'latitude' not in st.session_state:
    st.session_state.latitude = 37.7
if 'longitude' not in st.session_state:
    st.session_state.longitude = 118.8
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None

# 布局：左侧地图，右侧控制面板
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ 点击地图选择位置")

    # 创建地图，使用 session_state 中的坐标
    #这个地图是openstreet
    # m = folium.Map(location=[st.session_state.latitude, st.session_state.longitude], zoom_start=6)
    #改为高德地图
    m = folium.Map(
        location=[st.session_state.latitude, st.session_state.longitude],
        zoom_start=8,
        tiles='http://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}',
        attr='© <a href="http://www.gaode.com/">高德地图</a>'
    )
    folium.Marker(
        [st.session_state.latitude, st.session_state.longitude],
        popup=f"选中点: ({st.session_state.latitude:.4f}, {st.session_state.longitude:.4f})",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

    output = st_folium(m, width=700, height=500)

    # 处理地图点击 - 直接更新 st.session_state
    if output and output.get('last_clicked'):
        clicked_lat = output['last_clicked']['lat']
        clicked_lon = output['last_clicked']['lng']

        if (abs(clicked_lat - st.session_state.latitude) > 0.00001 or
                abs(clicked_lon - st.session_state.longitude) > 0.00001):
            # 直接更新 session_state
            st.session_state.latitude = clicked_lat
            st.session_state.longitude = clicked_lon
            # 同时更新输入框对应的 key
            st.session_state.lat_input_widget = clicked_lat
            st.session_state.lon_input_widget = clicked_lon
            st.rerun()

with col2:
    st.subheader("📍 位置设置")

    # 使用 key 绑定，值会自动同步
    st.number_input(
        "纬度 (Latitude)",
        value=st.session_state.latitude,
        format="%.6f",
        key="lat_input_widget",
        step=0.0001
    )
    st.number_input(
        "经度 (Longitude)",
        value=st.session_state.longitude,
        format="%.6f",
        key="lon_input_widget",
        step=0.0001
    )

    # 监听输入框变化，同步到主坐标
    if st.session_state.lat_input_widget != st.session_state.latitude:
        st.session_state.latitude = st.session_state.lat_input_widget
        st.rerun()
    elif st.session_state.lon_input_widget != st.session_state.longitude:
        st.session_state.longitude = st.session_state.lon_input_widget
        st.rerun()

    st.write(f"**当前选中位置:**")
    st.write(f"纬度: {st.session_state.latitude:.6f}°")
    st.write(f"经度: {st.session_state.longitude:.6f}°")

    fetch_button = st.button("🚀 获取8760小时数据", type="primary", use_container_width=True)


# ------------------- 以下为 NASA 数据获取、绘图、导出函数（与原代码完全相同） -------------------
def fetch_nasa_power_data(lat, lon, year=2023):
    start_date = f"{year}0101"
    end_date = f"{year}1231"
    base_url = "https://power.larc.nasa.gov/api/temporal/hourly/point"

    # 修改后的参数（与你URL中的参数对齐）
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,WS50M",
        "community": "re",  # 改为小写 're'
        "longitude": lon,
        "latitude": lat,
        "start": start_date,
        "end": end_date,
        "format": "json",  # 改为小写 'json'
        "units": "metric",  # 新增：公制单位
        "header": "true",  # 新增：返回头信息
        "time-standard": "lst",  # 新增：使用本地太阳时
        # "user": "streamlit_app"
    }

    with st.spinner(f"正在从NASA POWER下载{year}年全年8760小时数据..."):
        try:
            response = requests.get(base_url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            solar_data = data['properties']['parameter']['ALLSKY_SFC_SW_DWN']
            wind_data_50m = data['properties']['parameter']['WS50M']
            timestamps = list(solar_data.keys())
            # ============ 新增：将50米风速转换为100米风速 ============
            # 使用风切变指数公式：V100 = V50 * (100/50)^α
            alpha = 0.14  # 风切变指数（适用于开阔地形）
            H1 = 50  # 原始高度（米）
            H2 = 100  # 目标高度（米）

            # 计算转换系数
            wind_factor = (H2 / H1) ** alpha  # (100/50)^0.14 = 2^0.14 ≈ 1.102

            # 转换为100米风速
            wind_data_100m = [w * wind_factor for w in wind_data_50m.values()]

            # 创建DataFrame
            df = pd.DataFrame({
                '时间': timestamps,
                '光资源_Wm2': list(solar_data.values()),
                '风资源_ms': wind_data_100m  # 使用100米风速
            })

            df['datetime'] = pd.to_datetime(df['时间'], format='%Y%m%d%H')
            df['时间格式化'] = df['datetime'].dt.strftime('%Y%m%d%H')

            # 光资源单位转换（kW-hr/m²/hour → W/m²）
            df['光资源_Wm2'] = df['光资源_Wm2'] * 1

            expected_hours = 8760 if (year % 4 != 0) else 8784
            actual_hours = len(df)

            # 显示转换信息
            st.info(f"✅ 数据获取完成！实际获取 {actual_hours} 小时数据")
            st.info(f"🌬️ 风速已从50米高度转换为100米高度（转换系数: {wind_factor:.3f}）")

            # 处理缺失值
            missing_solar = df['光资源_Wm2'].isna().sum()
            missing_wind = df['风资源_ms'].isna().sum()
            if missing_solar > 0 or missing_wind > 0:
                st.warning(f"数据中存在缺失值: 光资源缺失{missing_solar}小时, 风资源缺失{missing_wind}小时")
                df['光资源_Wm2'] = df['光资源_Wm2'].fillna(method='ffill')
                df['风资源_ms'] = df['风资源_ms'].fillna(method='ffill')

            return df

        except Exception as e:
            st.error(f"数据获取失败: {e}")
            return None


if fetch_button:
    with st.spinner("正在获取NASA POWER数据..."):
        df = fetch_nasa_power_data(st.session_state.latitude, st.session_state.longitude, 2023)
        if df is not None:
            st.session_state.weather_data = df
            st.success("✅ 数据获取成功！")
        else:
            st.error("❌ 数据获取失败，请检查网络连接或经纬度后重试")

# ============ 电价输入表格（放在数据获取之后、数据可视化之前） ============

st.header("💰 电价设置")

# 初始化电价session_state
if 'grid_price' not in st.session_state:
    st.session_state.grid_price = [0.5] * 24  # 下网电价，默认0.5
if 'feedin_price' not in st.session_state:
    st.session_state.feedin_price = [0.0] * 24  # 上网电价，默认0.0

# 下网电价（购电电价）
st.subheader("🔌 下网电价（购电电价）")
st.caption("从电网买电的价格（元/kWh）")

# 创建12列
grid_cols = st.columns(12)

# 第一行：时段标题（0-11时）
for hour in range(12):
    with grid_cols[hour]:
        st.write(f"**{hour:02d}:00**")

# 第一行：输入框（0-11时）
grid_row1_values = []
for hour in range(12):
    with grid_cols[hour]:
        new_value = st.number_input(
            "",
            key=f"grid_price_row1_{hour}",
            value=st.session_state.grid_price[hour],
            format="%.3f",
            step=0.01,
            label_visibility="collapsed"
        )
        st.session_state.grid_price[hour] = new_value

# 第二行：时段标题（12-23时）
grid_cols2 = st.columns(12)
for hour in range(12, 24):
    with grid_cols2[hour - 12]:
        st.write(f"**{hour:02d}:00**")

# 第二行：输入框（12-23时）
for hour in range(12, 24):
    with grid_cols2[hour - 12]:
        new_value = st.number_input(
            "",
            key=f"grid_price_row2_{hour}",
            value=st.session_state.grid_price[hour],
            format="%.3f",
            step=0.01,
            label_visibility="collapsed"
        )
        st.session_state.grid_price[hour] = new_value

# 上网电价（售电电价）
st.subheader("🌞 上网电价（售电电价）")
st.caption("向电网卖电的价格（元/kWh）")

# 第一行：时段标题（0-11时）
feedin_cols = st.columns(12)
for hour in range(12):
    with feedin_cols[hour]:
        st.write(f"**{hour:02d}:00**")

# 第一行：输入框（0-11时）
for hour in range(12):
    with feedin_cols[hour]:
        new_value = st.number_input(
            "",
            key=f"feedin_price_row1_{hour}",
            value=st.session_state.feedin_price[hour],
            format="%.3f",
            step=0.01,
            label_visibility="collapsed"
        )
        st.session_state.feedin_price[hour] = new_value

# 第二行：时段标题（12-23时）
feedin_cols2 = st.columns(12)
for hour in range(12, 24):
    with feedin_cols2[hour - 12]:
        st.write(f"**{hour:02d}:00**")

# 第二行：输入框（12-23时）
for hour in range(12, 24):
    with feedin_cols2[hour - 12]:
        new_value = st.number_input(
            "",
            key=f"feedin_price_row2_{hour}",
            value=st.session_state.feedin_price[hour],
            format="%.3f",
            step=0.01,
            label_visibility="collapsed"
        )
        st.session_state.feedin_price[hour] = new_value

# 显示电价汇总（可选）
with st.expander("📊 查看电价汇总"):
    price_df = pd.DataFrame({
        '时段': [f"{h:02d}:00" for h in range(24)],
        '下网电价(元/kWh)': st.session_state.grid_price,
        '上网电价(元/kWh)': st.session_state.feedin_price
    })
    st.dataframe(price_df, use_container_width=True)


# 如果已有数据，显示图表和导出按钮
if st.session_state.weather_data is not None:
    df = st.session_state.weather_data
    st.header("📊 8760小时数据可视化")
    sample_rate = st.slider("数据点采样率（减少点数以加快渲染）", min_value=1, max_value=24, value=6,
                            help="1=显示全部8760点，24=每天显示1点")
    sampled_df = df.iloc[::sample_rate, :]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=sampled_df['datetime'], y=sampled_df['光资源_Wm2'], name="光资源 (太阳辐射)",
                   line=dict(color='orange', width=1), opacity=0.8),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(x=sampled_df['datetime'], y=sampled_df['风资源_ms'],
                   name="风资源 (风速 @ 100m)",  # 标注100米
                   line=dict(color='skyblue', width=1), opacity=0.8),
        secondary_y=True
    )
    fig.update_layout(
        title=f"{st.session_state.latitude:.4f}°N, {st.session_state.longitude:.4f}°E 位置2023年全年气象数据（风速已转换至100米高度）",
        xaxis_title="时间", hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500
    )
    fig.update_yaxes(title_text="光资源 (W/m²)", secondary_y=False, color='orange')
    fig.update_yaxes(title_text="风资源 (m/s)", secondary_y=True, color='skyblue')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 年度统计")
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("全年光资源", f"{df['光资源_Wm2'].sum()/1000:.1f} kW/m²")
    with col_stat2:
        st.metric("年均风速", f"{df['风资源_ms'].mean():.2f} m/s")
    with col_stat3:
        st.metric("最大光资源", f"{df['光资源_Wm2'].max():.0f} W/m²")
    with col_stat4:
        st.metric("最大风速", f"{df['风资源_ms'].max():.2f} m/s")

    df['月份'] = df['datetime'].dt.month
    monthly_stats = df.groupby('月份').agg({'光资源_Wm2': 'mean', '风资源_ms': 'mean'}).round(2)
    monthly_stats.columns = ['平均光资源(W/m²)', '平均风速(m/s)']
    with st.expander("📅 查看月度统计"):
        st.dataframe(monthly_stats, use_container_width=True)

    st.subheader("💾 导出数据")

    # 准备导出数据
    export_df = df[['时间格式化', '光资源_Wm2', '风资源_ms']].copy()
    export_df.columns = ['时间', '光资源(W/m²)', '风资源(m/s)']

    # ============ 新增：循环填充电价数据到8760行 ============
    # 提取小时信息（从时间格式化列，格式为YYYYMMDDHH）
    export_df['小时'] = export_df['时间'].astype(str).str[8:10].astype(int)

    # 根据小时映射电价
    export_df['下网电价(元/kWh)'] = export_df['小时'].apply(lambda h: st.session_state.grid_price[h])
    export_df['上网电价(元/kWh)'] = export_df['小时'].apply(lambda h: st.session_state.feedin_price[h])

    # 删除临时列
    export_df = export_df.drop(columns=['小时'])

    # 调整列顺序：时间、光资源、风资源、下网电价、上网电价
    export_df = export_df[['时间', '光资源(W/m²)', '风资源(m/s)', '下网电价(元/kWh)', '上网电价(元/kWh)']]

    st.write("数据预览（前24行）:")
    st.dataframe(export_df.head(24), use_container_width=True)

    from io import BytesIO


    def to_excel_bytes(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='NASA气象数据', index=False)
            worksheet = writer.sheets['NASA气象数据']
            # 调整列宽
            worksheet.column_dimensions['A'].width = 15  # 时间
            worksheet.column_dimensions['B'].width = 18  # 光资源
            worksheet.column_dimensions['C'].width = 15  # 风资源
            worksheet.column_dimensions['D'].width = 18  # 下网电价
            worksheet.column_dimensions['E'].width = 18  # 上网电价
        return output.getvalue()


    excel_data = to_excel_bytes(export_df)
    st.download_button(
        label="📥 下载 Excel 文件",
        data=excel_data,
        file_name=f"Weather_{st.session_state.latitude:.4f}_{st.session_state.longitude:.4f}_2023_ZP.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    with st.expander("🔍 查看全部数据"):
        st.dataframe(export_df, use_container_width=True, height=400)

st.divider()
#st.caption("数据来源: NASA POWER (Prediction Of Worldwide Energy Resources) API")
st.caption("光资源参数: ALLSKY_SFC_SW_DWN (地表接收的总太阳辐射, 全天空条件下)")
st.caption("风资源参数: WS50M (50米高度原始数据) → 已转换为100米高度风速")
st.caption(f"风切变指数: α = 0.14 (适用于开阔地形)，转换系数 = (100/50)^{0.14} = {((100/50)**0.14):.3f}")
