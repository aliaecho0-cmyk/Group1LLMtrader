import streamlit as st
from bt_copilot import BtCopilot
from coding_agent import SimpleCodingAgent
import yaml
import os
import pandas as pd
import datetime
import backtrader as bt
import numpy as np
from datetime import datetime as dt
import traceback

# ========== 内置数据加载函数 ==========
@st.cache_data(ttl=3600)
def load_builtin_data():
    """
    从内置的 data/stocks.csv 加载多股票数据
    返回: {stock_code: DataFrame} 格式的字典
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, 'data', 'stocks.csv')
    
    if not os.path.exists(csv_path):
        st.error(f"数据文件不存在：{csv_path}")
        st.info("请在项目根目录下创建 data 文件夹，并把 stocks.csv 放进去")
        return None, None
    
    try:
        df = pd.read_csv(csv_path)
        
        required_cols = ['date', 'stock_code', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"CSV文件缺少必要列：{missing_cols}")
            return None, None
        
        df['date'] = pd.to_datetime(df['date'])
        available_stocks = sorted(df['stock_code'].unique().tolist())
        
        stocks_data = {}
        for stock_code in available_stocks:
            stock_df = df[df['stock_code'] == stock_code].copy()
            stock_df.sort_values('date', inplace=True)
            stock_df.set_index('date', inplace=True)
            stock_df['openinterest'] = 0
            stock_df = stock_df[['open', 'high', 'low', 'close', 'volume', 'openinterest']]
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                stock_df[col] = pd.to_numeric(stock_df[col], errors='coerce')
            
            stocks_data[stock_code] = stock_df
        
        return stocks_data, available_stocks
        
    except Exception as e:
        st.error(f"读取数据文件失败：{e}")
        return None, None


# ========== 动态策略执行器 ==========
class DynamicStrategy(bt.Strategy):
    """动态策略类，用于执行生成的代码"""
    
    def __init__(self, strategy_code=None, **kwargs):
        self.strategy_code = strategy_code
        self.params = kwargs
        self.order = None
        
        # 如果有生成的代码，执行它
        if strategy_code:
            # 创建一个安全的命名空间
            safe_dict = {
                'bt': bt,
                'self': self,
                '__builtins__': __builtins__
            }
            try:
                exec(strategy_code, safe_dict)
            except Exception as e:
                st.error(f"策略初始化失败: {e}")
    
    def next(self):
        if self.order:
            return
        # 这里的逻辑将由生成的代码覆盖


def run_multi_stock_backtest(stocks_data, initial_cash=100000, strategy_desc=None, fast_ma=10, slow_ma=30):
    """
    多股票回测函数 - 使用backtrader原生夏普比率
    """
    try:
        cerebro = bt.Cerebro()
        
        # 记录净值的列表
        portfolio_values_history = []
        dates_history = []
        
        # 添加所有股票数据
        for stock_code, stock_df in stocks_data.items():
            data = bt.feeds.PandasData(dataname=stock_df)
            cerebro.adddata(data, name=str(stock_code))
        
        # 设置初始资金
        cerebro.broker.setcash(initial_cash)
        cerebro.broker.setcommission(commission=0.0001)
        
        # 根据策略描述选择策略
        if strategy_desc and "均线" in strategy_desc:
            class TestStrategy(bt.Strategy):
                params = (('fast', fast_ma), ('slow', slow_ma))
                
                def __init__(self):
                    self.orders = {}
                    self.smas_fast = {}
                    self.smas_slow = {}
                    for data in self.datas:
                        self.smas_fast[data._name] = bt.indicators.SMA(data.close, period=self.params.fast)
                        self.smas_slow[data._name] = bt.indicators.SMA(data.close, period=self.params.slow)
                
                def next(self):
                    for data in self.datas:
                        if data._name not in self.orders:
                            self.orders[data._name] = None
                        
                        if self.orders[data._name]:
                            continue
                        
                        position = self.getposition(data)
                        
                        if not position:
                            # 金叉买入
                            if self.smas_fast[data._name][0] > self.smas_slow[data._name][0] and \
                               self.smas_fast[data._name][-1] <= self.smas_slow[data._name][-1]:
                                self.orders[data._name] = self.buy(data=data, size=100)
                        else:
                            # 死叉卖出
                            if self.smas_fast[data._name][0] < self.smas_slow[data._name][0] and \
                               self.smas_fast[data._name][-1] >= self.smas_slow[data._name][-1]:
                                self.orders[data._name] = self.sell(data=data, size=100)
            
            cerebro.addstrategy(TestStrategy)
        else:
            # 默认简单策略
            class DefaultStrategy(bt.Strategy):
                def __init__(self):
                    pass
                
                def next(self):
                    for data in self.datas:
                        if len(data) == 1 and not self.getposition(data):
                            self.buy(data=data, size=100)
            
            cerebro.addstrategy(DefaultStrategy)
        
        # ========== 分析器配置 ==========
        # 添加分析器 - 使用backtrader原生夏普比率
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, 
                           _name='sharpe',
                           timeframe=bt.TimeFrame.Years,  # 年化
                           riskfreerate=0.02,  # 2% 无风险利率
                           annualize=True)
        
        cerebro.addanalyzer(bt.analyzers.Returns, 
                           _name='returns', 
                           timeframe=bt.TimeFrame.Years)
        
        cerebro.addanalyzer(bt.analyzers.DrawDown, 
                           _name='drawdown')
        
        # 添加交易分析器，用于检查是否有交易
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, 
                           _name='trades')
        
        # 添加观察者来记录净值
        cerebro.addobserver(bt.observers.Value)
        
        # 运行回测
        results = cerebro.run()
        strat = results[0]
        
        # 获取结果
        final_value = cerebro.broker.getvalue()
        total_return = (final_value - initial_cash) / initial_cash * 100
        
        # ========== 获取backtrader原生计算结果 ==========
        # 获取分析结果 - 直接使用backtrader返回的值
        sharpe_analysis = strat.analyzers.sharpe.get_analysis()
        returns_analysis = strat.analyzers.returns.get_analysis()
        drawdown_analysis = strat.analyzers.drawdown.get_analysis()
        trades_analysis = strat.analyzers.trades.get_analysis()
        
        # 调试信息 - 打印到控制台
        print("=" * 50)
        print("Sharpe分析结果:", sharpe_analysis)
        print("Returns分析结果:", returns_analysis)
        print("DrawDown分析结果:", drawdown_analysis)
        print("=" * 50)
        
        # ========== 直接使用backtrader返回的夏普比率 ==========
        # 尝试获取夏普比率 - 使用backtrader原生的键名
        sharpe_value = 0.0
        
        if isinstance(sharpe_analysis, dict):
            # backtrader通常返回 'sharpe_ratio' 键
            if 'sharpe_ratio' in sharpe_analysis:
                sharpe_value = float(sharpe_analysis['sharpe_ratio'])
            # 如果没有，尝试其他可能的键名
            elif 'sharpe' in sharpe_analysis:
                sharpe_value = float(sharpe_analysis['sharpe'])
            elif 'annual_sharpe' in sharpe_analysis:
                sharpe_value = float(sharpe_analysis['annual_sharpe'])
        
        # 获取年化收益率
        annual_return = 0
        if isinstance(returns_analysis, dict):
            annual_return = returns_analysis.get('rnorm100', 0)
        
        # 获取最大回撤
        max_drawdown = 0
        if isinstance(drawdown_analysis, dict):
            max_drawdown = drawdown_analysis.get('max', {}).get('drawdown', 0)
        
        # 获取交易次数
        total_trades = 0
        if isinstance(trades_analysis, dict):
            total_trades = trades_analysis.get('total', {}).get('total', 0)
        
        # 获取净值曲线数据
        if stocks_data:
            first_stock = list(stocks_data.values())[0]
            dates_history = first_stock.index.tolist()
            
            # 简单模拟净值变化
            portfolio_values_history = []
            if len(dates_history) > 0:
                step = (final_value - initial_cash) / len(dates_history)
                for i in range(len(dates_history)):
                    value = initial_cash + step * (i + 1)
                    portfolio_values_history.append(value)
        
        return {
            'success': True,
            'total_return': total_return,
            'sharpe': sharpe_value,  # 直接使用backtrader返回的夏普比率
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'final_value': final_value,
            'portfolio_values': portfolio_values_history if portfolio_values_history else [initial_cash, final_value],
            'dates': dates_history if dates_history else [],
            'total_trades': total_trades,
            'debug_info': {  # 添加调试信息
                'sharpe_raw': str(sharpe_analysis),
                'returns_raw': str(returns_analysis)
            }
        }
        
    except Exception as e:
        print("错误详情:", traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


# ========== 页面配置 ==========
st.set_page_config(
    page_title="AI量化回测助手",
    page_icon="📈",
    layout="wide",
)

# 轻量式 CSS 美化
st.markdown(
    """
    <style>
    .stApp { background-color: #f7fafc; }
    header {visibility: hidden}
    .main-title {font-size:34px; font-weight:700; margin-bottom:6px}
    .subtitle {color: #6b7280; margin-top:0; margin-bottom:18px}
    .card {background: #ffffff; padding:18px; border-radius:12px; box-shadow: 0 4px 20px rgba(16,24,40,0.04);}
    .sidebar .stButton>button {width:100%;}
    .muted {color:#6b7280}
    .metric-label {color:#6b7280; font-size:12px}
    .info-box {
        background-color: #e3f2fd;
        color: #0d47a1;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        border-left: 4px solid #2196f3;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ========== 读取配置 ==========
@st.cache_resource
def load_copilot():
    """加载配置并初始化 copilot"""
    settings_path = os.path.join(os.getcwd(), 'settings.yaml')
    if not os.path.exists(settings_path):
        raise FileNotFoundError("settings.yaml 未找到，请参照 settings.yaml.example 创建并填写 API Key")

    with open(settings_path, 'r') as f:
        settings = yaml.safe_load(f)

    agent = SimpleCodingAgent(API_KEY=settings['openai']['api_key'])
    copilot = BtCopilot(coding_agent=agent)
    return copilot, settings


# ========== 初始化 ==========
try:
    copilot, settings = load_copilot()
except Exception as e:
    st.error(f"无法加载 copilot：{e}")
    st.stop()

# ========== 加载数据 ==========
stocks_data, available_stocks = load_builtin_data()
if stocks_data is None:
    st.stop()

# ========== 初始化session state ==========
if 'run' not in st.session_state:
    st.session_state['run'] = False
if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'start_date' not in st.session_state:
    st.session_state.start_date = None
if 'end_date' not in st.session_state:
    st.session_state.end_date = None
if 'selected_stocks' not in st.session_state:
    st.session_state.selected_stocks = []
if 'show_debug' not in st.session_state:
    st.session_state.show_debug = False

# ========== 侧边栏 ==========
with st.sidebar:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("⚙️ 回测参数")
    
    # 股票选择模式
    stock_select_mode = st.radio(
        "选择模式",
        ["单支股票", "多支股票"],
        help="选择回测单支股票还是多支股票组合",
        key="stock_select_mode"
    )
    
    if stock_select_mode == "单支股票":
        selected_stock = st.selectbox(
            "选择股票",
            options=available_stocks,
            format_func=lambda x: f"{x} (数据量: {len(stocks_data[x])}天)",
            index=available_stocks.index(1309) if 1309 in available_stocks else 0,
            key="selected_stock"
        )
        selected_stocks = [selected_stock]
        
        stock_df = stocks_data[selected_stock]
        st.info(f"📅 数据范围：{stock_df.index.min().date()} 至 {stock_df.index.max().date()}")
        
    else:
        selected_stocks = st.multiselect(
            "选择多支股票",
            options=available_stocks,
            default=available_stocks[:3] if len(available_stocks) >= 3 else available_stocks,
            format_func=lambda x: f"{x} ({len(stocks_data[x])}天)",
            key="selected_stocks_multi"
        )
        st.info(f"已选择 {len(selected_stocks)} 支股票")
    
    # 日期范围选择
    if selected_stocks:
        all_dates = []
        for code in selected_stocks:
            all_dates.extend(stocks_data[code].index.tolist())
        
        min_date = min(all_dates).date()
        max_date = max(all_dates).date()
        
        st.markdown("---")
        st.subheader("📅 日期范围")
        
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.date_input(
                "开始日期",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                key="start_date_input"
            )
        with col_date2:
            end_date = st.date_input(
                "结束日期",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key="end_date_input"
            )
        
        st.session_state.start_date = start_date
        st.session_state.end_date = end_date
    
    initial_cash = st.number_input("初始资金", 100000, step=1000, key="initial_cash")
    
    st.markdown("---")
    st.markdown(f"📊 **数据统计**")
    st.markdown(f"- 股票数量：{len(available_stocks)} 支")
    if selected_stocks:
        st.markdown(f"- 日期范围：{min_date} 至 {max_date}")
    
    # 策略参数
    st.markdown("---")
    st.subheader("📊 策略参数")
    fast_ma = st.number_input("快线周期", 5, 50, 10, step=1, key="fast_ma")
    slow_ma = st.number_input("慢线周期", 20, 200, 30, step=1, key="slow_ma")
    
    # 调试选项
    st.markdown("---")
    st.checkbox("显示调试信息", key="show_debug", value=False)
    
    st.markdown("---")
    st.markdown("<div class='muted'>示例：600519 贵州茅台</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ========== 主界面 ==========
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📝 输入策略描述")
    strategy_desc = st.text_area(
        "用自然语言描述你的交易策略",
        height=150,
        placeholder="例如：当50日均线上穿200日均线时买入，下穿时卖出，止损设为5%",
        key="strategy_desc"
    )
    
    # 按钮放在col1内部
    if st.button("🚀 开始回测", key="run_backtest", type="primary"):
        if not selected_stocks:
            st.warning("请选择股票")
        elif st.session_state.start_date is None or st.session_state.end_date is None:
            st.warning("请选择日期范围")
        else:
            with st.spinner("正在运行多股票回测..."):
                try:
                    # 筛选选中股票在指定日期范围内的数据
                    selected_data = {}
                    for code in selected_stocks:
                        stock_df = stocks_data[code]
                        mask = (stock_df.index >= pd.Timestamp(st.session_state.start_date)) & \
                               (stock_df.index <= pd.Timestamp(st.session_state.end_date))
                        filtered_df = stock_df[mask].copy()
                        
                        if not filtered_df.empty:
                            selected_data[code] = filtered_df
                    
                    if not selected_data:
                        st.error("所选股票在指定日期范围内无数据")
                        st.stop()
                    
                    # 运行回测
                    results = run_multi_stock_backtest(
                        selected_data, 
                        initial_cash,
                        strategy_desc,
                        fast_ma,
                        slow_ma
                    )
                    
                    if results['success']:
                        st.session_state['results'] = results
                        st.session_state['selected_stocks'] = list(selected_data.keys())
                        st.session_state['run'] = True
                        st.success(f"回测完成！总收益率：{results['total_return']:.2f}%")
                        
                        # 显示交易统计
                        if results.get('total_trades', 0) > 0:
                            st.info(f"📊 交易次数：{results['total_trades']} 次")
                        else:
                            st.warning("⚠️ 策略没有产生任何交易，夏普比率可能为0")
                    else:
                        st.error(f"回测失败：{results.get('error', '未知错误')}")
                        
                except Exception as e:
                    st.error(f"回测失败：{e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 回测结果")
    
    if st.session_state.get('run') and st.session_state.get('results'):
        results = st.session_state['results']
        selected_stocks = st.session_state.get('selected_stocks', [])
        
        st.caption(f"回测股票：{', '.join([str(s) for s in selected_stocks])}")
        
        if results.get('portfolio_values') and results.get('dates'):
            df_chart = pd.DataFrame({
                '日期': results['dates'],
                '资产价值': results['portfolio_values']
            })
            df_chart.set_index('日期', inplace=True)
            st.line_chart(df_chart)
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("总收益率", f"{results['total_return']:.2f}%")
        with col_b:
            st.metric("最大回撤", f"{results['max_drawdown']:.2f}%", delta_color="inverse")
        with col_c:
            # 显示夏普比率 - 直接使用backtrader返回的值
            sharpe = results['sharpe']
            if results.get('total_trades', 0) == 0:
                st.metric("夏普比率", "0.00", delta="无交易")
            else:
                st.metric("夏普比率", f"{sharpe:.2f}")
        
        st.markdown(f"**最终资产**：¥ {results['final_value']:,.2f}")
        
        # 显示夏普比率说明
        if results['sharpe'] > 0 and results.get('total_trades', 0) > 0:
            if results['sharpe'] > 2:
                sharpe_desc = "优秀"
            elif results['sharpe'] > 1:
                sharpe_desc = "良好"
            else:
                sharpe_desc = "一般"
            st.markdown(f"<div class='info-box'>📈 夏普比率 {sharpe_desc}：{results['sharpe']:.2f}</div>", unsafe_allow_html=True)
        
        # 显示调试信息
        if st.session_state.get('show_debug', False) and results.get('debug_info'):
            with st.expander("🔧 调试信息"):
                st.json(results['debug_info'])
        
    else:
        st.info("👈 在左侧输入策略并点击开始")
        if available_stocks:
            sample_dates = pd.date_range(end=datetime.date.today(), periods=100)
            sample_data = pd.DataFrame({
                'portfolio': (1 + 0.0005 * (pd.Series(range(100)) - 50)).cumprod()
            }, index=sample_dates)
            st.line_chart(sample_data)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== 底部 ==========
st.markdown("---")
st.markdown("💡 **示例策略**：'当50日均线上穿200日均线时买入，下穿时卖出'")
st.markdown("<div class='muted' style='margin-top:8px'>提示：若遇到 API Key/权限问题，请检查 `settings.yaml` 配置文件。</div>", unsafe_allow_html=True)