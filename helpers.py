import aiohttp
import asyncio
import requests

from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


async def lookup(symbol):
    """Look up quote for symbol."""
    url = f"https://finance.cs50.io/quote?symbol={symbol.upper()}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()  # Raise an error for HTTP error responses
                quote_data = await response.json()
                return {
                    "name": quote_data["companyName"],
                    "price": quote_data["latestPrice"],
                    "symbol": symbol.upper()
                }
    except aiohttp.ClientError as e:
        print(f"Request error: {e}")
    except (KeyError, ValueError) as e:
        print(f"Data parsing error: {e}")
    return None

async def fetch_portfolio_data(portfolio_db):
    tasks = [lookup(position["ticker"]) for position in portfolio_db]
    stock_prices = await asyncio.gather(*tasks)

    portfolio = [
        {
            **item, 
            'price': float(stock_price['price']),
            'position_market_value': item['quantity'] * float(stock_price['price'])
        } for item, stock_price in zip(portfolio_db, stock_prices)
    ]
    return portfolio



def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
