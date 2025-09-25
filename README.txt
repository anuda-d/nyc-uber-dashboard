# NYC Uber Data Analytics Dashboard  

An interactive analytics dashboard built with **Python** and **Streamlit** to uncover insights from New York City Uber trip data. This project demonstrates data wrangling, visualization, and exploratory analysis skills by transforming raw TLC datasets into actionable business intelligence.  

## Live Demo  
[NYC Uber Data Analytics Dashboard](https://nyc-uber-dashboard-6btrgveappnty2zsqekgcky.streamlit.app/)  

---

## Features  
- **Commentary**: Automatically generated high-level takeaways that summarize ridership and revenue performance.  
- **Daily Trends**: Track ride counts, revenue, and average fares with interactive time-series plots.  
- **Performance Insights**: Key operational metrics such as total rides, total revenue, and average trip distance displayed with clear KPIs.  
- **Payment Analysis**: Breakdown of customer payment preferences across methods (credit card, cash, and others).  
- **Geographic View**: Identification of top pickup zones by ride volume, highlighting hotspots across the city.  
- **Interactive Exploration**: Filter data by date range and attributes to tailor the analysis to specific business questions.  

---

## Tech Stack  
- [Python 3.11+](https://www.python.org/)  
- [Streamlit](https://streamlit.io/)  
- [Pandas](https://pandas.pydata.org/)  
- [NumPy](https://numpy.org/)  
- [Plotly](https://plotly.com/python/)  
- [Jupyter Notebook](https://jupyter.org/)  

---

## 📂 Project Structure  
├── data/
│ └── sample_uber_data.csv # small subset of TLC data
├── dashboard.py # main Streamlit app
├── rideshare_data_cleaning.ipynb# notebook used for preprocessing
├── requirements.txt # dependencies
├── .gitignore # prevents large data from being pushed
└── README.md

---

## 📊 Data Source  
This project uses the **NYC Taxi & Limousine Commission (TLC) Trip Record Data**, publicly available here:  
[NYC TLC Trip Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)  

Due to file size constraints, only a **sample dataset** (`data/sample_uber_data.csv`) is included in this repository. For full analysis, download the trip data directly from the TLC website.  

---

##  Installation & Setup  

Clone the repository:  
```bash
git clone https://github.com/your-username/nyc-uber-dashboard.git
cd nyc-uber-dashboard
