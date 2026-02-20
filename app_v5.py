import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# =========================
# Page Config
# =========================
st.set_page_config(page_title="🔥 Ultimate FIRE Planner", page_icon="🔥", layout="wide")

st.title("🔥 Ultimate FIRE Planner")
st.markdown("Simulate your Financial Independence journey with clarity and confidence.")

# =========================
# Sidebar Inputs
# =========================
st.sidebar.header("Your Inputs")

dob = st.sidebar.date_input("Date of Birth", value=date(1994,1,1))
savings = st.sidebar.number_input("Current Portfolio ($)", 0, 20_000_000, 100_000)
monthly_investment = st.sidebar.number_input("Monthly Investment ($)", 0, 100_000, 2_000)
monthly_expenses = st.sidebar.number_input("Monthly Expenses ($)", 0, 50_000, 3_000)
retirement_age = st.sidebar.number_input("Retirement Age", 18, 80, 50)
life_expectancy = st.sidebar.number_input("Life Expectancy Age", 50, 100, 85)
return_rate = st.sidebar.slider("Expected Annual Return (%)", 1, 15, 7)
inflation = st.sidebar.slider("Inflation (%)", 0, 10, 3)
run = st.sidebar.button("🚀 Run Simulation")

# =========================
# Run Simulation
# =========================
if run:
    today = date.today()
    age = (today - dob).days / 365.25
    if retirement_age <= age:
        st.error("Retirement age must be greater than current age.")
        st.stop()

    months_total = int((life_expectancy - age) * 12)
    monthly_return = (1 + return_rate/100) ** (1/12) - 1
    monthly_inflation = (1 + inflation/100) ** (1/12) - 1

    # Lists to track
    nominal_values, real_values = [], []
    contributions_list, real_contributions_list = [savings], [savings]
    withdrawals_list = [0]
    ages, year_months = [], []

    balance = savings
    cumulative_inflation = 1.0
    current_date = today

    for month in range(months_total+1):
        current_age = age + month/12
        contribution = monthly_investment if current_age < retirement_age else 0
        withdrawal = monthly_expenses * cumulative_inflation if current_age >= retirement_age else 0

        # Update balance
        balance = balance*(1+monthly_return) + contribution - withdrawal
        cumulative_inflation *= (1+monthly_inflation)

        # Track contributions
        cumulative_contrib = contributions_list[-1] + contribution if current_age < retirement_age else contributions_list[-1]
        contributions_list.append(cumulative_contrib)
        real_contrib = cumulative_contrib / cumulative_inflation
        real_contributions_list.append(real_contrib)

        withdrawals_list.append(withdrawal)
        nominal_values.append(balance)
        real_values.append(balance / cumulative_inflation)
        ages.append(current_age)
        year_months.append((today + pd.DateOffset(months=month)).strftime("%Y/%b"))

    # Build full DataFrame
    df = pd.DataFrame({
        "Year/Month": year_months,
        "Age": ages,
        "Nominal Portfolio (CAD)": nominal_values,
        "Real Portfolio (CAD)": real_values,
        "Total Contributed (CAD)": contributions_list[1:],
        "Real Contributed (CAD)": real_contributions_list[1:],
        "Annual Withdrawal (CAD)": [w*12 for w in withdrawals_list[1:]],
        "Net Gain (Nominal)": [n - c for n, c in zip(nominal_values, contributions_list[1:])],
        "Net Gain (Real)": [r - rc for r, rc in zip(real_values, real_contributions_list[1:])],
    })

    # Add cumulative return %
    df["Cumulative Return %"] = df["Net Gain (Nominal)"] / df["Total Contributed (CAD)"] * 100

    # Yearly snapshot
    yearly_indexes = [i for i in range(0, len(df), 12)]
    df_yearly = df.iloc[yearly_indexes].reset_index(drop=True)

    # FIRE metrics
    annual_expenses = monthly_expenses*12
    fire_number = annual_expenses/0.04
    final_nominal = df_yearly["Nominal Portfolio (CAD)"].iloc[-1]
    final_real = df_yearly["Real Portfolio (CAD)"].iloc[-1]

    fire_age = None
    for i, val in enumerate(df_yearly["Real Portfolio (CAD)"]):
        if val >= fire_number:
            fire_age = df_yearly["Age"].iloc[i]
            break

    retirement_date = dob + timedelta(days=int(retirement_age*365.25))

    # =========================
    # Dashboard with inline mini pie chart
    # =========================
    st.subheader("📊 FIRE Dashboard")

    # Create 5 columns: 4 for metrics, 1 for pie chart
    col1, col2, col3, col4, col5 = st.columns([1,1,1,1,0.5])

    # Metrics
    col1.metric("🔥 FIRE Number", f"${fire_number:,.0f}")
    col2.metric("💰 Final Portfolio", f"${final_nominal:,.0f}")
    col3.metric("📈 Real Portfolio", f"${final_real:,.0f}")
    col4.metric("🎯 Retirement Date", retirement_date.strftime("%b %d, %Y"))

    # Small inline pie chart
    total_contrib = savings + monthly_investment*12*max(0, retirement_age-age)
    growth = final_nominal - total_contrib

    with col5:
        fig2, ax2 = plt.subplots(figsize=(2.5,2.5))  # compact size
        ax2.pie(
            [max(total_contrib,0), max(growth,0)],
            labels=["Contributions", "Investment Growth"],  # user-friendly labels
            autopct="%1.0f%%",
            startangle=90,
            colors=["#4e79a7","#f28e2b"]
        )
        ax2.set_title("Wealth Sources", fontsize=10)
        st.pyplot(fig2)

    # =========================
    # Wealth Projection Chart
    # =========================
    st.subheader("📈 Wealth Projection")
    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(df_yearly["Age"], df_yearly["Nominal Portfolio (CAD)"], linewidth=3, label="Nominal Portfolio")
    ax.plot(df_yearly["Age"], df_yearly["Real Portfolio (CAD)"], linestyle="--", linewidth=3, label="Inflation Adjusted")
    ax.axhline(fire_number, linestyle=":", linewidth=2, label="FIRE Target")
    ax.axvspan(retirement_age, life_expectancy, alpha=0.08, color='orange')
    ax.set_xlabel("Age")
    ax.set_ylabel("Portfolio ($)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend()
    ax.grid(alpha=0.3)
    st.pyplot(fig)

    # =========================
    # Monte Carlo Simulation in Expander
    # =========================
    with st.expander("🎲 Monte Carlo Simulation (Risk Analysis)"):
        simulations = 2000
        end_values = []
        for _ in range(simulations):
            balance_sim = savings
            for month in range(months_total):
                random_return = np.random.normal(return_rate/100, 0.12)/12
                balance_sim = balance_sim*(1+random_return)
            end_values.append(balance_sim)
        p10, p50, p90 = np.percentile(end_values, [10,50,90])
        st.write(f"10th percentile: ${p10:,.0f}")
        st.write(f"Median outcome: ${p50:,.0f}")
        st.write(f"90th percentile: ${p90:,.0f}")



    # =========================
    # Detailed Yearly Table (no Date, only Year/Month)
    # =========================
    with st.expander("📋 Detailed Yearly Breakdown"):
        st.dataframe(
            df_yearly.drop(columns=["Date"], errors='ignore').style.format({
                "Nominal Portfolio (CAD)": "${:,.0f}",
                "Real Portfolio (CAD)": "${:,.0f}",
                "Total Contributed (CAD)": "${:,.0f}",
                "Real Contributed (CAD)": "${:,.0f}",
                "Annual Withdrawal (CAD)": "${:,.0f}",
                "Net Gain (Nominal)": "${:,.0f}",
                "Net Gain (Real)": "${:,.0f}",
                "Cumulative Return %": "{:.1f}%"
            }),
            use_container_width=True
        )
