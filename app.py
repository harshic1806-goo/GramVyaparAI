
from flask import Flask, render_template, request
import json
import os
import math

# ==========================================
# PROJECT CONFIGURATION
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# HTML files are directly inside the main project folder.
app = Flask(__name__, template_folder=BASE_DIR)

# JSON file is also directly inside the main project folder.
JSON_FILE = os.path.join(
    BASE_DIR,
    "maharashtra_market_data.json"
)

DATA_SOURCE = (
    "Government mandi snapshot "
    "(downloaded data; not a live feed)"
)

PUNE_MARKET = "Pune(Moshi)"
RATNAGIRI_MARKET = "APMC Ratnagiri (Nachane)"


# ==========================================
# PRODUCT NAME NORMALIZATION
# ==========================================

def normalize_product(product):
    return " ".join(
        str(product).strip().casefold().split()
    )


# ==========================================
# LOAD GOVERNMENT MANDI DATA
# ==========================================

def load_market_data():

    if not os.path.isfile(JSON_FILE):
        raise FileNotFoundError(
            "maharashtra_market_data.json was not found "
            "in the main project folder."
        )

    with open(JSON_FILE, "r", encoding="utf-8") as file:
        payload = json.load(file)

    records = payload.get("records", [])

    if not isinstance(records, list):
        raise ValueError(
            "Invalid JSON format. The records field must be a list."
        )

    data = []

    for row in records:
        try:
            product = str(row.get("commodity", "")).strip()
            market = str(row.get("market", "")).strip()

            price_value = str(
                row.get("modal_price", "0")
            ).replace(",", "").strip()

            modal_price = float(price_value)

            if (
                not product
                or not market
                or not math.isfinite(modal_price)
                or modal_price <= 0
            ):
                continue

            # Government mandi prices are in Rs/quintal.
            # Convert them into Rs/kg.
            price_per_kg = round(modal_price / 100.0, 2)

            data.append({
                "product": product,
                "market": market,
                "price_per_kg": price_per_kg,
                "transport_cost_per_kg": 0.0,
                "demand": "Not provided by government data",
                "arrival_date": str(
                    row.get("arrival_date", "Not provided")
                ),
                "district": str(row.get("district", "")),
                "source_unit_price": modal_price
            })

        except (ValueError, TypeError, AttributeError):
            continue

    if not data:
        raise ValueError(
            "No valid market records were found in the JSON file."
        )

    return data


# ==========================================
# NUMBER VALIDATION
# ==========================================

def get_number(value, field_name, default=None):

    if value is None or str(value).strip() == "":
        if default is not None:
            return float(default)

        raise ValueError(
            f"Please enter a valid number for {field_name}."
        )

    try:
        number = float(value)
    except (ValueError, TypeError):
        raise ValueError(
            f"Please enter a valid number for {field_name}."
        )

    if not math.isfinite(number):
        raise ValueError(
            f"Please enter a valid number for {field_name}."
        )

    return number


# ==========================================
# TRANSPORT COSTS
# ==========================================

def get_transport_costs(source=None):

    if source is None:
        source = request.values

    pune_cost = get_number(
        source.get("transport_cost_pune", "0"),
        "Pune transport cost",
        0
    )

    ratnagiri_cost = get_number(
        source.get("transport_cost_ratnagiri", "0"),
        "Ratnagiri transport cost",
        0
    )

    if pune_cost < 0 or ratnagiri_cost < 0:
        raise ValueError(
            "Transport costs cannot be negative."
        )

    return {
        PUNE_MARKET: pune_cost,
        RATNAGIRI_MARKET: ratnagiri_cost
    }


# ==========================================
# MATCH MARKET TO TRANSPORT COST
# ==========================================

def get_market_transport_cost(market, transport_costs):

    market_name = str(market).strip().lower()

    if market_name == PUNE_MARKET.lower():
        return transport_costs[PUNE_MARKET]

    if market_name == RATNAGIRI_MARKET.lower():
        return transport_costs[RATNAGIRI_MARKET]

    if "pune" in market_name:
        return transport_costs[PUNE_MARKET]

    if "ratnagiri" in market_name:
        return transport_costs[RATNAGIRI_MARKET]

    return 0.0


# ==========================================
# ATTACH TRANSPORT COSTS
# ==========================================

def attach_transport_costs(selected_data, transport_costs):

    updated = []

    for row in selected_data:
        copy = dict(row)

        copy["transport_cost_per_kg"] = (
            get_market_transport_cost(
                copy["market"],
                transport_costs
            )
        )

        updated.append(copy)

    return updated


# ==========================================
# CALCULATE MARKET PROFIT
# ==========================================

def calculate_market_results(
    selected_data,
    quantity,
    production_cost
):

    results = []

    for row in selected_data:

        selling_price = row["price_per_kg"]
        transport_cost = row["transport_cost_per_kg"]

        profit_per_kg = (
            selling_price
            - production_cost
            - transport_cost
        )

        total_profit = profit_per_kg * quantity

        results.append({
            "product": row["product"],
            "market": row["market"],
            "price_per_kg": selling_price,
            "transport_cost_per_kg": transport_cost,
            "production_cost": production_cost,
            "profit_per_kg": round(profit_per_kg, 2),
            "total_profit": round(total_profit, 2),
            "demand": row["demand"],
            "arrival_date": row["arrival_date"],
            "district": row["district"]
        })

    results.sort(
        key=lambda item: item["total_profit"],
        reverse=True
    )

    return results


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():

    try:
        data = load_market_data()

        products = sorted(set(
            row["product"] for row in data
        ))

        return render_template(
            "index.html",
            products=products,
            available_products=products,
            data_source=DATA_SOURCE
        )

    except Exception as error:
        print("HOME PAGE ERROR:", repr(error))
        return "Home Page Error: " + str(error), 500


# ==========================================
# MARKET RECOMMENDATIONS
# ==========================================

@app.route("/recommend", methods=["POST"])
def recommend():

    try:
        data = load_market_data()

        product = request.form.get("product", "").strip()

        quantity = get_number(
            request.form.get("quantity"),
            "quantity"
        )

        production_cost = get_number(
            request.form.get("production_cost"),
            "production cost"
        )

        transport_costs = get_transport_costs(request.form)

        if not product:
            raise ValueError("Please select a product.")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        if production_cost < 0:
            raise ValueError("Production cost cannot be negative.")

        selected_data = [
            row for row in data
            if normalize_product(row["product"])
            == normalize_product(product)
        ]

        if not selected_data:
            raise ValueError(
                "Selected product is not available "
                "in the downloaded mandi data."
            )

        selected_data = attach_transport_costs(
            selected_data,
            transport_costs
        )

        results = calculate_market_results(
            selected_data,
            quantity,
            production_cost
        )

        if not results:
            raise ValueError(
                "No market results could be calculated."
            )

        best_result = results[0]

        return render_template(
            "result.html",
            results=results,
            recommendations=results,
            product=product,
            quantity=quantity,
            production_cost=production_cost,
            best_market=best_result["market"],
            best_profit=best_result["total_profit"],
            transport_cost_pune=transport_costs[PUNE_MARKET],
            transport_cost_ratnagiri=transport_costs[RATNAGIRI_MARKET],
            data_source=DATA_SOURCE
        )

    except Exception as error:

        print("RECOMMENDATION ERROR:", repr(error))

        return render_template(
            "result.html",
            error=str(error),
            results=[],
            recommendations=[],
            product=request.form.get("product", ""),
            quantity=0,
            production_cost=0,
            best_market="",
            best_profit=0,
            transport_cost_pune=0,
            transport_cost_ratnagiri=0,
            data_source=DATA_SOURCE
        ), 400


# ==========================================
# BUSINESS DASHBOARD
# ==========================================

@app.route("/dashboard")
def dashboard():

    try:
        data = load_market_data()

        total_products = len(set(
            row["product"] for row in data
        ))

        total_markets = len(set(
            row["market"] for row in data
        ))

        available_products = sorted(set(
            row["product"] for row in data
        ))

        default_product = (
            "Onion"
            if "Onion" in available_products
            else available_products[0]
        )

        product = request.args.get(
            "product", default_product
        ).strip()

        quantity = get_number(
            request.args.get("quantity", 100),
            "quantity"
        )

        production_cost = get_number(
            request.args.get("production_cost", 15),
            "production cost"
        )

        transport_costs = get_transport_costs(request.args)

        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        if production_cost < 0:
            raise ValueError(
                "Production cost cannot be negative."
            )

        selected_data = [
            row for row in data
            if normalize_product(row["product"])
            == normalize_product(product)
        ]

        if not selected_data:
            raise ValueError(
                "Selected product is not available."
            )

        selected_data = attach_transport_costs(
            selected_data,
            transport_costs
        )

        results = calculate_market_results(
            selected_data,
            quantity,
            production_cost
        )

        markets = []
        prices = []
        profits = []
        profit_per_kg_values = []
        transport_cost_values = []

        for item in results:
            markets.append(item["market"])
            prices.append(item["price_per_kg"])
            profits.append(item["total_profit"])
            profit_per_kg_values.append(item["profit_per_kg"])
            transport_cost_values.append(
                item["transport_cost_per_kg"]
            )

        best_result = results[0]

        best_market = best_result["market"]
        best_profit = best_result["total_profit"]
        best_profit_per_kg = best_result["profit_per_kg"]

        break_even_price = (
            production_cost
            + best_result["transport_cost_per_kg"]
        )

        if best_profit > 0:
            message = (
                "This market offers the highest estimated profit."
            )
        elif best_profit == 0:
            message = (
                "This market is at the break-even point."
            )
        else:
            message = (
                "No available market is profitable with these costs."
            )

        return render_template(
            "dashboard.html",
            total_products=total_products,
            total_markets=total_markets,
            available_products=available_products,
            product=product,
            quantity=quantity,
            production_cost=production_cost,
            best_market=best_market,
            best_profit=best_profit,
            best_profit_per_kg=best_profit_per_kg,
            break_even_price=break_even_price,
            markets=markets,
            prices=prices,
            profits=profits,
            profit_per_kg_values=profit_per_kg_values,
            transport_costs=transport_cost_values,
            message=message,
            transport_cost_pune=transport_costs[PUNE_MARKET],
            transport_cost_ratnagiri=transport_costs[RATNAGIRI_MARKET],
            data_source=DATA_SOURCE
        )

    except Exception as error:
        print("DASHBOARD ERROR:", repr(error))
        return "Dashboard Error: " + str(error), 500


# ==========================================
# WHAT-IF BUSINESS SIMULATOR
# ==========================================

@app.route("/simulator", methods=["GET", "POST"])
def simulator():

    result = None
    profit_per_kg = None
    break_even_price = None

    if request.method == "POST":

        try:
            selling_price = get_number(
                request.form.get("selling_price"),
                "selling price"
            )

            production_cost = get_number(
                request.form.get("production_cost"),
                "production cost"
            )

            transport_cost = get_number(
                request.form.get("transport_cost"),
                "transportation cost"
            )

            quantity = get_number(
                request.form.get("quantity"),
                "quantity"
            )

            if min(
                selling_price,
                production_cost,
                transport_cost
            ) < 0:
                raise ValueError(
                    "Costs and selling price cannot be negative."
                )

            if quantity <= 0:
                raise ValueError(
                    "Quantity must be greater than zero."
                )

            profit_per_kg = (
                selling_price
                - production_cost
                - transport_cost
            )

            result = profit_per_kg * quantity

            break_even_price = (
                production_cost + transport_cost
            )

            profit_per_kg = round(profit_per_kg, 2)
            result = round(result, 2)
            break_even_price = round(break_even_price, 2)

        except ValueError as error:
            return "Simulator Error: " + str(error), 400

        except Exception as error:
            print("SIMULATOR ERROR:", repr(error))
            return "Simulator Error: " + str(error), 500

    return render_template(
        "simulator.html",
        result=result,
        profit_per_kg=profit_per_kg,
        break_even_price=break_even_price
    )


# ==========================================
# SMALL QUANTITY SELLING ADVISOR
# ==========================================

@app.route(
    "/small-quantity-advisor",
    methods=["GET", "POST"]
)
def small_quantity_advisor():

    try:
        data = load_market_data()

        products = sorted(set(
            row["product"]
            for row in data
            if row.get("product")
        ))

        selected_product = ""
        production_cost = ""
        quantity_results = []
        error = None

        transport_costs = {
            PUNE_MARKET: 0.0,
            RATNAGIRI_MARKET: 0.0
        }

        if request.method == "POST":

            selected_product = (
                request.form.get("selected_product")
                or request.form.get("product", "")
            ).strip()

            production_cost = request.form.get(
                "production_cost", ""
            ).strip()

            try:
                cost = get_number(
                    production_cost,
                    "production cost"
                )

                if cost < 0:
                    raise ValueError(
                        "Production cost cannot be negative."
                    )

                if not selected_product:
                    raise ValueError(
                        "Please select a product."
                    )

                transport_costs = get_transport_costs(
                    request.form
                )

                selected_data = [
                    row for row in data
                    if normalize_product(row["product"])
                    == normalize_product(selected_product)
                ]

                if not selected_data:
                    error = (
                        "No market data found for this product. "
                        "Please select a product available in the "
                        "downloaded government mandi data."
                    )

                else:
                    selected_data = attach_transport_costs(
                        selected_data,
                        transport_costs
                    )

                    quantities = [25, 50, 100, 200]

                    for quantity in quantities:

                        market_results = calculate_market_results(
                            selected_data,
                            quantity,
                            cost
                        )

                        quantity_results.append({
                            "quantity": quantity,
                            "best_market": market_results[0]["market"],
                            "best_profit": market_results[0]["total_profit"],
                            "market_results": [
                                {
                                    "market": item["market"],
                                    "price": item["price_per_kg"],
                                    "transport": item["transport_cost_per_kg"],
                                    "profit_per_kg": item["profit_per_kg"],
                                    "total_profit": item["total_profit"]
                                }
                                for item in market_results
                            ]
                        })

            except ValueError as validation_error:
                error = str(validation_error)

            except Exception as exception:
                print("SMALL QUANTITY ERROR:", repr(exception))
                error = (
                    "Unable to calculate results. "
                    "Please check the entered values."
                )

        return render_template(
            "small_quantity.html",
            products=products,
            selected_product=selected_product,
            production_cost=production_cost,
            quantity_results=quantity_results,
            error=error,
            transport_cost_pune=transport_costs[PUNE_MARKET],
            transport_cost_ratnagiri=transport_costs[RATNAGIRI_MARKET]
        )

    except Exception as error:
        print("SMALL QUANTITY PAGE ERROR:", repr(error))
        return "Small Quantity Advisor Error: " + str(error), 500


# ==========================================
# VERCEL AND LOCAL APPLICATION ENTRY POINT
# ==========================================

if __name__ == "__main__":

    print("Starting GramVyapar AI...")

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
