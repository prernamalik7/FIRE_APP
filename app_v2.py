import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, timedelta

# ======================================================
# PAGE CONFIG (MUST BE FIRST)
# ======================================================
st.set_page_config(
    page_title="🔥 FIRE Planner Pro",
    page_icon="🔥",
    layout="wide"
)

# ======================================================
# CLEAN FINTECH STYLE
# ======================================================
st.markdown("""
<style>
.metric-box {
    background-color: #111827;
    padding: 18px;
    border-radius: 10px;
    color: white;
}
.small-text { font-size: 13px; color: #9CA3AF; }
</style>
""", unsafe_allow_html=True)

st.title("🔥 FIRE Planner Pro")
st.markdown("A clean, powerful Financial Independence simulator.")

# ======================================================
# SIDEBAR INPUTS
# ======================================================
st.sidebar.header("Your Inputs")

dob = st.sidebar.date_input(
    "Date of Birth",
    value=date(1994, 1, 1),
    help="Used to calculate your real retirement calendar date."
)

savings = st.sidebar.number_input(
    "Current Portfolio ($)",
    0, 20_000_000, 100000,
    help="Total invested assets."
)

monthly_investment = st.sidebar.number_input(
    "Monthly Investment ($)",
    0, 100_000, 2000,
    help="How much you invest each month."
)

monthly_expenses = st.sidebar.number_input(
    "Monthly Expenses ($)",
    0, 100_000, 3000,
    help="Expected monthly spending in retirement."
)

retirement_age = st.sidebar.number_input(
    "Retirement Age",
    18, 80, 50,
    help="Age when you stop contributing."
)

life_expectancy = st.sidebar.number_input(
    "Life Expectancy",
    50, 100, 85,
    help="How long portfolio must last."
)

return_rate = st.sidebar.slider(
    "Expected Return (%)",
    1, 15, 7,
    help="Expected long-term annual return."
)

inflation = st.sidebar.slider(
    "Inflation (%)",
    0, 10, 3,
    help="Expected annual inflation."
)

run = st.sidebar.button("🚀 Run Simulation")

# ======================================================
# RUN MODEL
# ======================================================
if run:

    today = date.today()
    age = (today - dob).days / 365.25

    if retirement_age <= age:
        st.error("Retirement age must be greater than current age.")
        st.stop()

    months = int((life_expectancy - age) * 12)

    monthly_return = (1 + return_rate/100) ** (1/12) - 1
    monthly_inflation = (1 + inflation/100) ** (1/12) - 1

    balance = savings
    cumulative_inflation = 1

    nominal_values = []
    real_values = []
    contributions = savings

    ages = []

    for m in range(months + 1):

        current_age = age + m/12
        contribution = monthly_investment if current_age < retirement_age else 0
        withdrawal = monthly_expenses * cumulative_inflation if current_age >= retirement_age else 0

        balance = balance*(1+monthly_return) + contribution - withdrawal
        cumulative_inflation *= (1+monthly_inflation)

        contributions += contribution

        nominal_values.append(balance)
        real_values.append(balance/cumulative_inflation)
        ages.append(current_age)

    df = pd.DataFrame({
        "Age": ages,
        "Nominal": nominal_values,
        "Real": real_values
    })

    # ==================================================
    # FIRE METRICS
    # ==================================================
    annual_expenses = monthly_expenses * 12
    fire_number = annual_expenses / 0.04
    final_nominal = df["Nominal"].iloc[-1]
    final_real = df["Real"].iloc[-1]

    fire_age = None
    for i, val in enumerate(df["Real"]):
        if val >= fire_number:
            fire_age = df["Age"].iloc[i]
            break

    retirement_date = dob + timedelta(days=int(retirement_age*365.25))

    # ==================================================
    # DASHBOARD
    # ==================================================
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

    # ==================================================
    # MAIN CHART
    # ==================================================
    st.subheader("📈 Wealth Projection")

    fig, ax = plt.subplots(figsize=(12,6))

    ax.plot(df["Age"], df["Nominal"], linewidth=3, label="Nominal Portfolio")
    ax.plot(df["Age"], df["Real"], linestyle="--", linewidth=3, label="Inflation Adjusted")
    ax.axhline(fire_number, linestyle=":", linewidth=2, label="FIRE Target")
    ax.axvspan(retirement_age, life_expectancy, alpha=0.08)

    ax.set_xlabel("Age")
    ax.set_ylabel("Portfolio ($)")
    ax.legend()
    ax.grid(alpha=0.3)

    st.pyplot(fig)

    # ==================================================
    # MONTE CARLO
    # ==================================================
    with st.expander("🎲 Monte Carlo Simulation (Risk Analysis)"):

        simulations = 200
        end_values = []

        for _ in range(simulations):
            balance = savings
            cumulative_inflation = 1

            for m in range(months):
                random_return = np.random.normal(return_rate/100, 0.12)/12
                balance = balance*(1+random_return)
            end_values.append(balance)

        p10 = np.percentile(end_values, 10)
        p50 = np.percentile(end_values, 50)
        p90 = np.percentile(end_values, 90)

        st.write(f"10th percentile: ${p10:,.0f}")
        st.write(f"Median outcome: ${p50:,.0f}")
        st.write(f"90th percentile: ${p90:,.0f}")


    # ==================================================
    # BREAKDOWN PIE (SAFE + PROFESSIONAL)
    # ==================================================
    with st.expander("📊 Contribution vs Growth Breakdown"):

        years_contributing = max(0, retirement_age - age)
        total_contributions = savings + (monthly_investment * 12 * years_contributing)
        growth = final_nominal - total_contributions

        fig2, ax2 = plt.subplots()

        if final_nominal <= 0:
            st.error("Portfolio depleted — no capital remaining to break down.")
        else:
            if growth >= 0:
                values = [total_contributions, growth]
                labels = ["Your Contributions", "Investment Growth"]
                colors = ["#4F46E5", "#10B981"]
            else:
                # If portfolio lost money
                values = [final_nominal, abs(growth)]
                labels = ["Remaining Portfolio", "Net Loss"]
                colors = ["#4F46E5", "#EF4444"]

            ax2.pie(
                values,
                labels=labels,
                autopct="%1.1f%%",
                colors=colors
            )

            ax2.set_title("Portfolio Composition at Final Age")
            st.pyplot(fig2)


    # ==================================================
    # ADVANCED TABLE
    # ==================================================
    with st.expander("📋 Detailed Data"):
        st.dataframe(df.round(0), use_container_width=True)
