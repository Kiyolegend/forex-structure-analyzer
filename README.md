# Forex Market Structure Analyzer 📊

A Streamlit-based web application that analyzes forex market structure using multi-timeframe logic and generates trade ideas.

---

## 🚀 Features

* Multi-timeframe analysis:

  * **4H** → Higher timeframe bias
  * **1H** → Confirmation
  * **5M** → Entry signals

* Market structure detection:

  * Higher High (HH)
  * Higher Low (HL)
  * Lower High (LH)
  * Lower Low (LL)

* Automated trade idea generation:

  * Buy/Sell bias
  * Entry guidance
  * Risk/Reward suggestion

* Interactive candlestick chart with structure points

---

## 📸 Screenshots


<img width="2048" height="1365" alt="image" src="https://github.com/user-attachments/assets/b781bc7c-09cc-418d-ad01-894474d9e320" />



### Main Analysis
<img width="2048" height="1365" alt="image" src="https://github.com/user-attachments/assets/5d1cf888-bea2-4e48-a7f5-f0f3a40d0e07" />



### Chart View
<img width="2048" height="1365" alt="image" src="https://github.com/user-attachments/assets/9c717e57-18cd-4c5b-bb50-7025d999e5f1" />


![Chart](screenshots/chart.png)

---

## 🛠️ Tech Stack

* Python
* Streamlit
* Pandas
* Plotly
* REST API (Twelve Data)

---

## ⚙️ How to Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🧠 Strategy Logic (Simplified)

* Identify market structure using swing highs/lows

* Determine trend:

  * HH + HL → Bullish
  * LH + LL → Bearish

* Align multiple timeframes:

  * Trade in direction of 4H trend
  * Confirm with 1H
  * Enter on 5M pullback

---

## 📈 Future Improvements

* Backtesting system
* Break of Structure (BOS) detection
* Liquidity sweep identification
* Risk management calculator
* Live deployment

---

## 👨‍💻 Author

Developed as a learning + portfolio project to explore algorithmic trading and market structure analysis.
