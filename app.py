import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================
# Page Config (MUST BE FIRST)
# =========================
st.set_page_config(
    page_title="🔥 Ultimate FIRE Planner",
    layout="wide",
    page_icon="🔥"
)

# =========================
# Custom Styling
# =========================
st.markdown("""
<style>
.big-font { font-size:22px !important; font-weight:600; }
.metric-card {
    background-color: #111827;
    padding: 20px;
    border-radius: 12px;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("🔥 Ultimate FIRE Planner")
st.markdown("Plan your Financial Independence journey with clarity and precision.")

# =========================
# Sidebar Inputs
# =========================
st.sidebar.header("📥 Your Financial Inputs")

age = st.sidebar.number_input(
    "Current Age",
    18, 70, 30,
    help="Your current age today."
)

savings = st.sidebar.number_input(
    "Current Investment Portfolio ($)",
    0, 10_000_000, 100000,
    help="Total amount already invested (stocks, ETFs, retirement accounts, etc.)."
)

monthly_investment = st.sidebar.number_input(
    "Monthly Investment ($)",
    0, 100_000, 2000,
    help="How much you invest every month."
)

return_rate = st.sidebar.slider(
    "Expected Annual Return (%)",
    1, 15, 7,
    help="Long-term expected annual return. 7% is typical for diversified equities."
)

inflation = st.sidebar.slider(
    "Inflation Rate (%)",
    0, 10, 3,
    help="Expected long-term inflation rate."
)

monthly_expenses = st.sidebar.number_input(
    "Monthly Expenses ($)",
    0, 50_000, 2500,
    help="Your expected monthly spending during retirement."
)

retirement_age = st.sidebar.number_input(
    "Retirement Age",
    18, 75, 50,
    help="Age when you stop contributing to investments."
)

end_age = st.sidebar.number_input(
    "Life Expectancy Age",
    50, 100, 85,
    help="Age until which you want your portfolio to last."
)

run = st.sidebar.button("🚀 Run FIRE Simulation")

# =========================
# Validation
# =========================
if run:

    if end_age <= age:
        st.error("End age must be greater than current age.")
        st.stop()

    if retirement_age < age:
        st.error("Retirement age must be greater than or equal to current age.")
        st.stop()

    # =========================
    # Model
    # =========================
    months = int((end_age - age) * 12)

    monthly_return = (1 + return_rate/100) ** (1/12) - 1
    monthly_inflation = (1 + inflation/100) ** (1/12) - 1

    balance = savings
    cumulative_inflation = 1

    nominal_values = []
    real_values = []
    ages = []

    for m in range(months + 1):
        current_age = age + m / 12

        contribution = monthly_investment if current_age < retirement_age else 0
        withdrawal = monthly_expenses * cumulative_inflation if current_age >= retirement_age else 0

        balance = balance * (1 + monthly_return) + contribution - withdrawal
        cumulative_inflation *= (1 + monthly_inflation)

        nominal_values.append(balance)
        real_values.append(balance / cumulative_inflation)
        ages.append(current_age)

    df = pd.DataFrame({
        "Age": ages,
        "Nominal": nominal_values,
        "Real": real_values
    })

    # =========================
    # FIRE Metrics
    # =========================
    annual_expenses = monthly_expenses * 12
    fire_number = annual_expenses / 0.04

    final_value = df["Nominal"].iloc[-1]
    final_real = df["Real"].iloc[-1]

    # Detect FIRE Age
    fire_age = None
    for i, val in enumerate(df["Real"]):
        if val >= fire_number:
            fire_age = df["Age"].iloc[i]
            break

    # =========================
    # Metrics Dashboard
    # =========================
    st.subheader("📊 FIRE Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🔥 FIRE Number (4% Rule)", f"${fire_number:,.0f}")
    col2.metric("💰 Final Portfolio (Nominal)", f"${final_value:,.0f}")
    col3.metric("💰 Final Portfolio (Real)", f"${final_real:,.0f}")

    if fire_age:
        col4.metric("🎯 Estimated FIRE Age", f"{fire_age:.1f}")
    else:
        col4.metric("🎯 FIRE Age", "Not reached")

    # =========================
    # Chart
    # =========================
    st.subheader("📈 Portfolio Growth Projection")

    fig, ax = plt.subplots(figsize=(12,6))

    ax.plot(df["Age"], df["Nominal"], label="Nominal Portfolio", linewidth=3)
    ax.plot(df["Age"], df["Real"], linestyle="--", linewidth=3, label="Inflation-Adjusted Portfolio")

    ax.axhline(y=fire_number, linestyle=":", linewidth=2, label="FIRE Target (4% Rule)")

    ax.axvspan(retirement_age, end_age, alpha=0.1, label="Retirement Phase")

    ax.set_xlabel("Age", fontsize=12)
    ax.set_ylabel("Portfolio Value ($)", fontsize=12)
    ax.set_title("Wealth Growth Over Time", fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    st.pyplot(fig)

    # =========================
    # Depletion Warning
    # =========================
    if final_value < 0:
        st.error("⚠️ Your portfolio depletes before life expectancy.")
    elif fire_age:
        st.success(f"🎉 You reach FIRE at approximately age {fire_age:.1f}!")
    else:
        st.warning("You do not reach FIRE with current assumptions.")

    # =========================
    # Data Table
    # =========================
    with st.expander("📋 View Detailed Data Table"):
        st.dataframe(df.round(0))
