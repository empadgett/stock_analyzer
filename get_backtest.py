import pandas as pd
import yfinance as yf
import backtrader as bt
import matplotlib.pyplot as plt
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradeObserver(bt.observer.Observer):
    lines = ('buy', 'sell',)
    plotinfo = dict(plot=True, subplot=False, plotlinelabels=True)
    plotlines = dict(
        buy=dict(marker='^', markersize=8, color='lime', fillstyle='full'),
        sell=dict(marker='v', markersize=8, color='red', fillstyle='full')
    )


    def __init__(self):
        self.order = None
        self.buyprice = None
        self.sellprice = None

    def next(self):
        if self.order is None:
            return

        if self.order.status in [bt.Order.Completed]:
            if self.order.isbuy():
                self.lines.buy[0] = self.order.executed.price
                self.buyprice = self.order.executed.price
            else:
                self.lines.sell[0] = self.order.executed.price
                self.sellprice = self.order.executed.price

        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        self.order = order

class HullMovingAverageStrategy(bt.Strategy):
    params = (
        ('n1', 8),
        ('n2', 25),
        ('n3', 20),
        ('stop_loss', 0.02),  # 2% stop loss
    )
    

    def __init__(self):
        self.hma1 = bt.indicators.HullMovingAverage(self.data.close, period=self.params.n1)
        self.hma2 = bt.indicators.HullMovingAverage(self.data.close, period=self.params.n2)
        self.ema1 = bt.indicators.EMA(self.data.close, period=self.params.n3)
        self.cross_over = bt.indicators.CrossOver(self.hma1, self.ema1)
        self.order = None
        self.stop_loss_order = None
        self.max_drawdown = 0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
            elif order.issell():
                self.sell_price = order.executed.price

        self.order = None

    def next(self):
        current_value = self.broker.getvalue()
        peak_value = max(self.broker.getvalue(), self.broker.startingcash)
        drawdown = (peak_value - current_value) / peak_value
        self.max_drawdown = max(self.max_drawdown, drawdown)

        if self.max_drawdown > 0.5:  # 50% drawdown
            self.close()
            return

        if self.order:
            return

        if not self.position:
            if self.cross_over > 0:
                self.order = self.buy(size=100)
                if self.params.stop_loss:
                    stop_price = self.data.close[0] * (1 - self.params.stop_loss)
                    self.stop_loss_order = self.sell(size=100, exectype=bt.Order.Stop, price=stop_price)

        elif self.position:
            if self.cross_over < 0:
                self.order = self.close()
                if self.stop_loss_order:
                    self.cancel(self.stop_loss_order)
                    self.stop_loss_order = None

class BuyAndHoldStrategy(bt.Strategy):
    def __init__(self):
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price

        self.order = None

    def next(self):
        if not self.position:
            self.order = self.buy(size=100)

    def stop(self):
        portfolio_value = self.broker.getvalue()
        roi = (portfolio_value - self.broker.startingcash) / self.broker.startingcash * 100
        #print(f'Buy and Hold ROI: {roi:.2f}%')

ticker = 'AAPL'
try:
    df = yf.download(ticker, start='2020-01-01', end='2024-10-01', progress=False)
except Exception as e:
    logging.error(f"Error downloading data: {e}")
    raise

# Convert the DataFrame to Backtrader format
data = bt.feeds.PandasData(dataname=df)

# Create two Cerebro engines
cerebro_main = bt.Cerebro(optreturn=False)
cerebro_buyhold = bt.Cerebro()

# Add data to both engines
cerebro_main.adddata(data)
cerebro_buyhold.adddata(data)

# Set initial cash for both engines
initial_cash = 100000
cerebro_main.broker.setcash(initial_cash)
cerebro_buyhold.broker.setcash(initial_cash)

# Add commission to both engines
cerebro_main.broker.setcommission(commission=0.001)
cerebro_buyhold.broker.setcommission(commission=0.001)

# Add analyzers to main strategy
cerebro_main.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio')
cerebro_main.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
cerebro_main.addanalyzer(bt.analyzers.Returns, _name='returns')

# Add the Buy and Hold strategy to its Cerebro instance
cerebro_buyhold.addstrategy(BuyAndHoldStrategy)

# Optimize main strategy parameters
cerebro_main.optstrategy(
    HullMovingAverageStrategy,
    n1=range(10, 16, 2),
    #n2=range(30, 200, 25),
    n3=range(10, 60, 10),
    stop_loss=[0.01, 0.02, 0.03, None]
)

# Run the optimization for main strategy
try:
    results_main = cerebro_main.run()
except Exception as e:
    logging.error(f"Error running main strategy: {e}")
    raise

# Run the Buy and Hold strategy
results_buyhold = cerebro_buyhold.run()

# Find the best strategy from optimization results
best_roi = float('-inf')
best_params = None
best_sharpe = None
best_drawdown = None
best_run = None

for run in results_main:
    roi = run[0].analyzers.returns.get_analysis()['rnorm100']
    if roi > best_roi:
        best_roi = roi
        best_params = run[0].params
        best_sharpe = run[0].analyzers.sharpe_ratio.get_analysis()['sharperatio']
        best_drawdown = run[0].analyzers.drawdown.get_analysis()['max']['drawdown']
        best_run = run

# Print the results
logging.info(f'Best Strategy ROI: {best_roi:.2f}%')
logging.info(f'Parameters: n1: {best_params.n1}, n3: {best_params.n3}, Stop Loss: {best_params.stop_loss}')
logging.info(f'Sharpe Ratio: {best_sharpe:.2f}')
logging.info(f'Max Drawdown: {best_drawdown:.2f}%')

# Plot the best strategy results
if best_run:
    cerebro_plot = bt.Cerebro()
    cerebro_plot.adddata(data)
    cerebro_plot.addstrategy(HullMovingAverageStrategy, 
                             n1=best_params.n1, 
                             n2=best_params.n2, 
                             n3=best_params.n3,
                             stop_loss=best_params.stop_loss)
    cerebro_plot.broker.setcash(initial_cash)
    cerebro_plot.broker.setcommission(commission=0.001)
    
    # Add custom trade observer
    cerebro_plot.addobserver(TradeObserver)
    
    cerebro_plot.run()
    fig = cerebro_plot.plot(style='candlestick', barup='green', bardown='red', volume=False)[0][0]
    # Save the plot
    # fig.savefig('best_hull_moving_average_strategy.png')
    plt.close(fig)

# Plot the buy and hold strategy results
cerebro_buyhold_plot = bt.Cerebro()
cerebro_buyhold_plot.adddata(data)
cerebro_buyhold_plot.addstrategy(BuyAndHoldStrategy)
cerebro_buyhold_plot.broker.setcash(initial_cash)
cerebro_buyhold_plot.broker.setcommission(commission=0.001)

# Add custom trade observer
cerebro_buyhold_plot.addobserver(TradeObserver)

cerebro_buyhold_plot.run()
#fig = cerebro_buyhold_plot.plot(style='candlestick', barup='green', bardown='red', volume=False)[0][0]
# Save the plot
# fig.savefig('buy_and_hold_strategy.png')
plt.close(fig)