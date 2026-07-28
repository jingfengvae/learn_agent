import streamlit as st
import requests

# 设置页面标题
st.title("实时比特币价格图表")

# 加载数据的函数
def fetch_bitcoin_data():
    try:
        # 从 CoinGecko 获取比特币数据
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
        response = requests.get(url)
        data = response.json()
        
        # 检查返回数据的格式
        if 'bitcoin' not in data or 'usd' not in data['bitcoin'] or 'usd_24h_change' not in data['bitcoin']:
            st.error("返回数据不符合预期，请稍后重试。")
            return None
        
        price = data['bitcoin']['usd']
        price_change = data['bitcoin']['usd_24h_change']
        absolute_change = price * (price_change / 100)  # 计算绝对变动值
    
        return price, price_change, absolute_change
    except requests.exceptions.RequestException as e:
        print (f"数据获取失败: {e}")
        st.error(f"数据获取失败: {e}")
        return None

def main():
    # 实时刷新价格的按钮放在显眼位置
    if st.button("刷新价格"):
        with st.spinner("正在加载数据..."):
            data = fetch_bitcoin_data()
            if data:
                price, price_change, absolute_change = data
                st.success(f"当前比特币价格: ${price:.2f}")
                st.markdown(f"价格变化: ${absolute_change:.2f} ({price_change:.2f}%)")
    else:
        # 默认加载数据
        with st.spinner("正在加载数据..."):
            data = fetch_bitcoin_data()
            if data:
                price, price_change, absolute_change = data
                st.success(f"当前比特币价格: ${price:.2f}")
                st.markdown(f"价格变化: ${absolute_change:.2f} ({price_change:.2f}%)")
    
    # 加载状态
    if data is None:
        st.info("请确保网络连接正常，重试或稍后再试。")

if __name__ == '__main__':
    main()