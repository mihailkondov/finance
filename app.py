import asyncio
import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, fetch_portfolio_data, login_required, lookup, usd

# Configure application
app = Flask(__name__)
app.config['DEBUG'] = True


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # pull stocks owned from database
    portfolio_db = db.execute("""
                SELECT ticker,
                SUM(price * quantity_left) AS position_acquisition_value,
                SUM(quantity_left) AS quantity,
                SUM(price * quantity_left) / SUM(quantity_left) AS weighted_average_price
        FROM (
                SELECT s.ticker, t.price, p.quantity_left
                FROM portfolio AS p
                JOIN transactions AS t ON t.id = p.transactions_id
                JOIN stocks AS s ON s.id = t.stocks_id
                WHERE t.users_id = ?
                AND p.quantity_left > 0
        )
        GROUP BY ticker
    """, session["user_id"])

    # fetch market value of stocks
    portfolio = asyncio.run(fetch_portfolio_data(portfolio_db))

    # pull cash from database
    user_cash = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])[0]["cash"]
    user_cash = float(user_cash)

    # calculate stats
    total_in_stocks = 0
    total_shares = 0
    total_acquisition_value = sum(item["position_acquisition_value"] for item in portfolio_db)
    for stock in portfolio:
        total_in_stocks += stock['position_market_value']
        total_shares += stock['quantity']
    total_portfolio_value = total_in_stocks + user_cash
    unrealized_profit = total_in_stocks - total_acquisition_value
    stats = {'cash': user_cash,
            'total_in_stocks': total_in_stocks,
            'total_shares': total_shares,
            'total_portfolio_value': total_portfolio_value,
            'total_acquisition_value': total_acquisition_value,
            'unrealized_profit': unrealized_profit}
    
    return render_template("index.html", portfolio=portfolio, stats=stats)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":  # Execute buy transaction

        # harvest data from form
        ticker = str.upper(request.form["symbol"])
        shares = request.form["shares"]

        # validate number of shares
        try:
            shares = int(shares)
            if shares <= 0:
                raise Exception()
        except:
            return apology("Invalid number of shares")

        # validate symbol entered
        if not ticker:
            return apology("No symbol entered")

        # search selected stock
        stock = lookup(ticker)
        if not stock:
            return apology(f"Stock {ticker} not found")

        # calculate cost
        price = stock["price"]
        total = shares * price

        # check if sufficient cash
        user_id = session["user_id"]
        user_cash = db.execute("SELECT cash FROM users WHERE id=?", user_id)[0]["cash"]
        if total > user_cash:
            return apology("Insufficient funds for the transaction")

        db.execute("BEGIN TRANSACTION")
        try:
            # find stock in DB
            ticker_query = db.execute("SELECT id FROM stocks WHERE ticker=?", ticker)

            # if not found add stock
            if not ticker_query:
                db.execute("INSERT INTO stocks (ticker, company_name) VALUES (?, ?)",
                           ticker, stock["name"])
                ticker_query = db.execute("SELECT id FROM stocks WHERE ticker=?", ticker)

            stock_id = ticker_query[0]["id"]
            # record transaction
            db.execute("INSERT INTO transactions (price, type, quantity, stocks_id, users_id) VALUES (?, 1, ?, ?, ?)",
                       price, shares, stock_id, user_id)
            # add stock to portfolio
            db.execute("""
                        INSERT INTO portfolio (transactions_id, quantity_left)
                        SELECT id, quantity
                          FROM transactions
                         WHERE id = last_insert_rowid()
            """)
            # reduce user's money
            db.execute("UPDATE users SET cash = cash - ? WHERE id =?", total, user_id)
            db.execute("COMMIT TRANSACTION")
            shares_word = "shares"
            if shares == 1:
                shares_word = "share"
            message = f'Bought {shares} {shares_word} of {stock["name"]} ({ticker}) at ${stock["price"]:.2f} per share for a grand total of ${total:.2f}'
            flash(message)
            return redirect("/")
        except:
            db.execute("ROLLBACK TRANSACTION")
            return apology("Transaction failed", 500)
    else:  # render buy page
        user_cash = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])[0]["cash"]
        return render_template("buy.html", cash=user_cash)


@app.route("/cash_add", methods=["GET", "POST"])
@login_required
def cash_add():
    if request.method == "POST":
        try:
            cash_added = float(request.form["cash"])
            if cash_added < 0 or cash_added > 1000000000000:
                raise Exception()
        except:
            return apology("Invalid amount", 400)

        try:
            db.execute("BEGIN TRANSACTION")
            # set new cash amount
            db.execute("""
                       WITH vars AS (SELECT ? AS user_id, ? AS cash_added)
                       UPDATE users
                       SET cash = (SELECT cash FROM users WHERE id = (SELECT user_id FROM vars)) + (SELECT cash_added FROM vars)
                       WHERE id = (SELECT user_id FROM vars)
                       """, session["user_id"], cash_added)

            # insert in transactions
            db.execute("INSERT INTO transactions (price, type, quantity, users_id) VALUES (?, 3, 0, ?)",
                       cash_added, session["user_id"])
            db.execute("COMMIT")
        except:
            db.execute("ROLLBACK")

    user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
    return render_template("cash_add.html", cash=user_cash)


@app.route("/cash_withdraw", methods=["GET", "POST"])
@login_required
def cash_withdraw():
    if request.method == "POST":
        try:
            cash_withdrawn = float(request.form["cash"])
            if cash_withdrawn < 0 or cash_withdrawn > 1000000000000:
                raise Exception()
        except:
            return apology("Invalid amount", 400)

        try:
            db.execute("BEGIN TRANSACTION")
            # set new cash amount
            db.execute("""
                       WITH vars AS (SELECT ? AS user_id, ? AS cash_added)
                       UPDATE users
                       SET cash = (SELECT cash FROM users WHERE id = (SELECT user_id FROM vars)) - (SELECT cash_added FROM vars)
                       WHERE id = (SELECT user_id FROM vars)
                       """, session["user_id"], cash_withdrawn)

            # insert in transactions
            db.execute("INSERT INTO transactions (price, type, quantity, users_id) VALUES (?, 4, 0, ?)",
                       cash_withdrawn, session["user_id"])
            db.execute("COMMIT")
        except:
            db.execute("ROLLBACK")

    user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
    return render_template("cash_withdraw.html", cash=user_cash)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("""
                                SELECT
                                    date(t.datetime, 'unixepoch') AS 'date',
                                    time(t.datetime, 'unixepoch') AS 'time',
                                    CASE
                                            WHEN ticker IS NULL THEN '-'
                                            ELSE ticker
                                    END AS symbol,
                                    tt.type AS type,
                                    quantity AS 'shares',
                                    price AS 'share price',
                                    CASE
                                        WHEN t.stocks_id NOT NULL THEN price * quantity
                                        ELSE
                                            CASE
                                                WHEN t.type = 3 THEN t.price
                                                WHEN t.type = 4 THEN t.price * (-1)
                                            END
                                    END AS total
                                FROM transactions AS t
                                LEFT JOIN stocks AS s ON s.id = t.stocks_id
                                JOIN transaction_types AS tt ON tt.id = t.type
                                WHERE users_id  = ?
                                ORDER BY t.datetime DESC
    """, session["user_id"])

    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(  # <-this is a list of dictionaries (should be of length 1)
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        ticker = request.form["symbol"]
        if not ticker:
            return apology("No symbol entered", 400)

        stock = lookup(ticker)
        if not stock:
            return apology("Stock not found", 400)

        return render_template("quote.html", stock=stock)
    else:
        return render_template("quote.html")


@app.route("/profits", methods=["GET"])
def profits():
    profits = "Feature coming soon"
    return render_template("profits.html", profits=profits)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # POST request
    if request.method == "POST":
        # Collect data from form:
        username = request.form["username"]
        password = request.form["password"]
        confirmation = request.form["confirmation"]

        # Check if fields are empty
        if not (username and password and confirmation):
            return apology("Please enter username, password, and confirm your password.")

        # Check passoword confirmed correctly:
        if password != confirmation:
            return apology("Password confirmation failed. Please enter the same password in both fields correctly")

        # Check if username is taken
        duplicate = db.execute("SELECT * FROM users WHERE username = ?", username)
        if duplicate:
            return apology("Username already taken", 400)

        # Insert user into database
        password_hash = generate_password_hash(password)
        try:
            db.execute("INSERT INTO users (username, hash) VALUES(? , ?)", username, password_hash)
        except:
            return apology("Registration failed", 500)

        return redirect("/login")

    # GET request (or any other than POST)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":

        # read data from form
        shares_requested = request.form["shares"]
        symbol = request.form["symbol"]

        # check if form is filled
        if not shares_requested or not symbol:
            return apology("Please select stock and a valid number of shares")

        # check shares is valid number
        try:
            shares_requested = int(shares_requested)
            if shares_requested < 1:
                raise Exception()
        except:
            return apology("Invalid number of shares", 400)

        # fetch user's stock from database
        stock_reserve = db.execute("""
                            SELECT s.id AS stock_id, s.ticker, quantity_left, t.datetime, t.id
                            FROM portfolio as p
                            JOIN transactions as t ON t.id = p.transactions_id
                            JOIN stocks as s ON s.id = t.stocks_id
                            WHERE quantity_left > 0
                            AND t.users_id = ?
                            AND s.ticker = ?
                            ORDER BY t.datetime ASC
                           """, session["user_id"], symbol)

        # check if user owns any of this particular stock
        if not stock_reserve:
            return apology(f"Stock {symbol} not found in your portfolio", 400)

        # check if user owns enough shares
        shares_available = sum(item["quantity_left"] for item in stock_reserve)
        if shares_available < shares_requested:
            return apology(f"You only own {shares_available} shares of {symbol}. Cannot sell {shares_requested} shares.")

        # fetch purchase transactions of stock owned
        sell_list = []
        shares_prepared = 0

        # list the batches of purchases to be reduced
        for stock in stock_reserve:
            diff = shares_requested - shares_prepared
            # last step condition:
            if diff <= stock["quantity_left"]:
                stock["quantity_left"] = stock["quantity_left"] - diff
                sell_list.append(stock)
                break
            else:
                shares_prepared += stock["quantity_left"]
                stock["quantity_left"] = 0
                sell_list.append(stock)

        # calculate sale revenue:
        stock = lookup(symbol)
        price = float(stock["price"])
        total_revenue = price * shares_requested

        # alter database:
        db.execute("BEGIN TRANSACTION")
        try:
            # record new transaction
            db.execute("INSERT INTO transactions (price, type, quantity, stocks_id, users_id) VALUES (?, 2, ?, ?, ?)",
                       price, shares_requested, stock_reserve[0]["stock_id"], session["user_id"])

            # create temporary table if one doesn't alrady exist
            db.execute(
                "CREATE TEMPORARY TABLE IF NOT EXISTS temp_sold (id INTEGER, t_quantity_left INTEGER)")

            # delete temporary table contents in case table alrady exists
            db.execute("DELETE FROM temp_sold")

            # insert new values in temp table
            for entry in sell_list:
                db.execute("INSERT INTO temp_sold(id, t_quantity_left) VALUES (?, ?)",
                           entry["id"], entry["quantity_left"])

            # update portfolio with temp table values <- I need to delete the ones that hit 0?
            db.execute("""
                        UPDATE portfolio
                        SET quantity_left = (
                                SELECT t_quantity_left
                                FROM temp_sold
                                WHERE temp_sold.id = portfolio.transactions_id
                        )
                        WHERE portfolio.transactions_id IN (SELECT id FROM temp_sold)
            """)

            # add money from transaction
            db.execute("UPDATE users SET cash = cash + ? WHERE id =?",
                       total_revenue, session["user_id"])

            # commit changes
            db.execute("COMMIT TRANSACTION")

        except:
            db.execute("DROP table temp_sold")
            db.execute("ROLLBACK")
            return apology("Sale failed", 500)

        shares_word = "shares"
        if shares_requested == 1:
            shares_word = "share"
        message = f'Sold {shares_requested} {shares_word} of {stock["name"]} ({symbol}) at ${stock["price"]:,.2f} per share for a grand total of ${total_revenue:,.2f}'
        flash(message)
        return redirect("/")

    # pull stocks owned from database
    portfolio = db.execute("""
                SELECT ticker,
                SUM(quantity_left) AS quantity
                FROM (
                        SELECT s.ticker, t.price, p.quantity_left
                        FROM portfolio AS p
                        JOIN transactions AS t ON t.id = p.transactions_id
                        JOIN stocks AS s ON s.id = t.stocks_id
                        WHERE t.users_id = ?
                        AND p.quantity_left > 0
                )
                GROUP BY ticker
    """, session["user_id"])

    # pull cash from database
    cash = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])[0]["cash"]
    cash = float(cash)
    return render_template("sell.html", portfolio=portfolio, cash=cash)
