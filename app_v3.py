import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
import matplotlib.pyplot as plt

# =========================
# Page Config
# =========================
st.set_page_config(page_title="🔥 Ultimate FIRE Planner", page_icon="🔥", layout="wide")

st.title("🔥 Ultimate FIRE Planner")
st.markdown("Simulate your Financial Independence journey with clarity.")

# =========================
# Sidebar Inputs
# =========================
st.sidebar.header("Your Inputs")

dob = st.sidebar.date_input(
    "Date of Birth",
    value=date(1994,1,1),
    help="Used to calculate your real retirement date."
)

savings = st.sidebar.number_input(
    "Current Portfolio ($)",
    0, 20_000_000, 100000
)

monthly_investment = st.sidebar.number_input(
    "Monthly Investment ($)",
    0, 100_000, 2000
)

monthly_expenses = st.sidebar.number_input(
    "Monthly Expenses ($)",
    0, 50_000, 3000
)

retirement_age = st.sidebar.number_input(
    "Retirement Age",
    18, 80, 50
)

life_expectancy = st.sidebar.number_input(
    "Life Expectancy Age",
    50, 100, 85
)

return_rate = st.sidebar.slider(
    "Expected Annual Return (%)",
    1, 15, 7
)

inflation = st.sidebar.slider(
    "Inflation (%)",
    0, 10, 3
)

run = st.sidebar.button("🚀 Run Simulation")

# =========================
# Run Model
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
    ages = []
    nominal_values = []
    real_values = []
    contributions_list = [savings]
    real_contributions_list = [savings]
    withdrawals_list = [0]

    balance = savings
    cumulative_inflation = 1.0

    for month in range(months_total+1):
        current_age = age + month/12
        contribution = monthly_investment if current_age < retirement_age else 0
        withdrawal = monthly_expenses * cumulative_inflation if current_age >= retirement_age else 0

        # Update balance
        balance = balance * (1 + monthly_return) + contribution - withdrawal
        cumulative_inflation *= (1 + monthly_inflation)

        # Track contributions
        cumulative_contrib = contributions_list[-1] + contribution if current_age < retirement_age else contributions_list[-1]
        contributions_list.append(cumulative_contrib)

        real_contrib = cumulative_contrib / cumulative_inflation
        real_contributions_list.append(real_contrib)

        # Track withdrawals
        withdrawals_list.append(withdrawal)

        # Track portfolio values
        nominal_values.append(balance)
        real_values.append(balance / cumulative_inflation)
        ages.append(current_age)

    # =========================
    # Build DataFrame
    # =========================
    df = pd.DataFrame({
        "Age": ages,
        "Nominal Portfolio (CAD)": nominal_values,
        "Real Portfolio (CAD)": real_values,
        "Total Contributed (CAD)": contributions_list[1:],  # skip initial duplication
        "Real Contributed (CAD)": real_contributions_list[1:],
        "Annual Withdrawal (CAD)": [w*12 for w in withdrawals_list[1:]],
        "Net Gain (Nominal)": [n - c for n, c in zip(nominal_values, contributions_list[1:])],
        "Net Gain (Real)": [r - rc for r, rc in zip(real_values, real_contributions_list[1:])]
    })

    # =========================
    # Yearly Snapshot
    # =========================
    yearly_indexes = [i for i in range(0, len(df), 12)]
    df_yearly = df.iloc[yearly_indexes].reset_index(drop=True)

    # =========================
    # FIRE Metrics
    # =========================
    annual_expenses = monthly_expenses * 12
    fire_number = annual_expenses / 0.04
    final_nominal = df_yearly["Nominal Portfolio (CAD)"].iloc[-1]
    final_real = df_yearly["Real Portfolio (CAD)"].iloc[-1]

    fire_age = None
    for i, val in enumerate(df_yearly["Real Portfolio (CAD)"]):
        if val >= fire_number:
            fire_age = df_yearly["Age"].iloc[i]
            break

    retirement_date = dob + timedelta(days=int(retirement_age*365.25))

    # =========================
    # Dashboard
    # =========================
    st.subheader("📊 FIRE Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔥 FIRE Number", f"${fire_number:,.0f}")
    col2.metric("💰 Final Portfolio", f"${final_nominal:,.0f}")
    col3.metric("📈 Real Portfolio", f"${final_real:,.0f}")
    col4.metric("🎯 Retirement Date", retirement_date.strftime("%b %d, %Y"))

    if fire_age:
        st.success(f"🎉 You reach FIRE around age {fire_age:.1f}")
    else:
        st.warning("You do not reach FIRE under current assumptions.")

    # =========================
    # Main Chart
    # =========================
    st.subheader("📈 Wealth Projection")
    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(df_yearly["Age"], df_yearly["Nominal Portfolio (CAD)"], linewidth=3, label="Nominal Portfolio")
    ax.plot(df_yearly["Age"], df_yearly["Real Portfolio (CAD)"], linestyle="--", linewidth=3, label="Inflation Adjusted")
    ax.axhline(fire_number, linestyle=":", linewidth=2, label="FIRE Target")
    ax.axvspan(retirement_age, life_expectancy, alpha=0.08, color='orange')
    ax.set_xlabel("Age")
    ax.set_ylabel("Portfolio ($)")
    ax.legend()
    ax.grid(alpha=0.3)
    st.pyplot(fig)

    # =========================
    # Detailed Table
    # =========================
    with st.expander("📋 Detailed Yearly Breakdown"):
        st.dataframe(
            df_yearly.style.format({
                "Nominal Portfolio (CAD)": "${:,.0f}",
                "Real Portfolio (CAD)": "${:,.0f}",
                "Total Contributed (CAD)": "${:,.0f}",
                "Real Contributed (CAD)": "${:,.0f}",
                "Annual Withdrawal (CAD)": "${:,.0f}",
                "Net Gain (Nominal)": "${:,.0f}",
                "Net Gain (Real)": "${:,.0f}"
            }),
            use_container_width=True
        )
