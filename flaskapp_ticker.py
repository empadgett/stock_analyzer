from flask import Flask, render_template, request
from stock_fetcher import get_current_price

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ticker = request.form['ticker'].upper()
        price = get_current_price(ticker)

        if price:
            return render_template('result.html', ticker=ticker, price=price)
        else:
            return "Invalid ticker symbol. Please try again." 

    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)


