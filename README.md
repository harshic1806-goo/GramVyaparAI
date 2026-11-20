🌱 GramVyapar AI

A Data-Driven Decision Support System for Rural Entrepreneurs

📌 About the Project

GramVyapar AI is a web-based decision support system designed to help farmers and rural entrepreneurs in Maharashtra make better business decisions.

It compares agricultural market prices across different mandis and calculates estimated profits by considering production costs, transportation expenses, and product quantity.

The main aim is to help users identify better selling opportunities through simple data analysis.

## 🎯 Problem Statement

Farmers and rural entrepreneurs often face difficulties in choosing the right market to sell their agricultural products. Different markets offer different prices, and transportation costs can affect their final profit.

GramVyapar AI helps solve this problem by comparing market prices and estimating profitability.

## ✨ Key Features

1. **Market Profitability Advisor** – Compares market prices and calculates estimated profit.
2. **Business Dashboard** – Displays market and profit-related information using charts and graphs.
3. **What-If Business Simulator** – Allows users to analyse profit under different selling prices and expenses.
4. **Small Quantity Selling Advisor** – Compares estimated profits for different product quantities.
5. **Market Comparison** – Helps users identify potentially better markets based on available data.

## 🛠️ Technologies Used

- Python
- Flask
- HTML
- CSS
- JavaScript
- Chart.js
- JSON

## 📊 Data Source

Government of India's Open Government Data Platform:

https://data.gov.in/

The current prototype uses downloaded agricultural market price data for selected Maharashtra markets, including Pune and Ratnagiri.

## 💰 Profit Calculation

**Profit per kg = Selling Price − Production Cost − Transportation Cost**

**Total Estimated Profit = Profit per kg × Quantity**

## 🚀 How to Run the Project

1. Clone or download this repository.
2. Open the project folder.
3. Install Flask:

   `pip install flask`

4. Run the application:

   `python app.py`

5. Open your browser and visit:

   `http://127.0.0.1:5000`

🔮 Future Scope

- Integration of live mandi prices through APIs.
- Addition of more agricultural markets.
- Support for more regional languages.
- Weather and demand-related information.
- Machine learning-based market price prediction.
- Mobile application development.

⚠️ Important Note

This project currently uses downloaded market data and does not provide live market prices. Profit calculations are estimates based on available data and user inputs. Actual profits may vary depending on market conditions and additional expenses.

👩‍💻 Developed By

Harshita Chaubey

Computer Engineering

Shree L. R. Tiwari College of Engineering

---

*GramVyapar AI – Empowering Rural Entrepreneurs Through Data-Driven Decisions.*
