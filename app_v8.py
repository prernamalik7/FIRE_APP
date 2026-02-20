
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import plotly.graph_objects as go
import plotly.express as px


# =========================
# Page Config
# =========================
st.set_page_config(page_title="🔥 Ultimate FIRE Planner", page_icon="🔥", layout="wide")
st.title("🔥 Ultimate FIRE Planner")
st.markdown("Simulate your Financial Independence (FIRE) journey in a way anyone can understand. Hover over metrics for explanations.")

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
        st.error("Retirement age must be greater than your current age.")
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
    # =========================
    # Age-Aware FIRE Calculation
    # =========================

    annual_expenses = monthly_expenses * 12
    retirement_years = life_expectancy - retirement_age

    # Real return (inflation adjusted)
    real_return = ((1 + return_rate/100) / (1 + inflation/100)) - 1

    # Safety check (avoid divide by zero)
    if real_return <= 0:
        fire_number = annual_expenses * retirement_years
    else:
        fire_number = annual_expenses * (
            (1 - (1 + real_return) ** (-retirement_years)) / real_return
        )

    final_nominal = df_yearly["Nominal Portfolio (CAD)"].iloc[-1]
    final_real = df_yearly["Real Portfolio (CAD)"].iloc[-1]

    fire_age = None
    for i, val in enumerate(df_yearly["Real Portfolio (CAD)"]):
        if val >= fire_number:
            fire_age = df_yearly["Age"].iloc[i]
            break

    retirement_date = dob + timedelta(days=int(retirement_age*365.25))

    # =========================
    # Dashboard with explanatory hover texts
    # =========================
    st.subheader("📊 FIRE Dashboard")
    col1, col2, col3, col4, col5 = st.columns([1,1,1,1,0.5])

    # 🔥 FIRE Number
    fire_text = (
        f"You need ${fire_number:,.0f} to retire at age {retirement_age}. "
        "This is based on the 4% safe withdrawal rule — you can withdraw 4% per year to cover your expenses."
    )
    col1.metric("🔥 FIRE Number", f"${fire_number:,.0f}", help=fire_text)

    # 💰 Final Portfolio
    final_text = (
        f"Your projected portfolio at age {life_expectancy if retirement_age < life_expectancy else retirement_age} is ${final_nominal:,.0f}. "
        "This includes all your contributions and investment growth."
    )
    col2.metric("💰 Final Portfolio", f"${final_nominal:,.0f}", help=final_text)

    # 📈 Real Portfolio
    real_text = (
        f"This is the inflation-adjusted portfolio value: ${final_real:,.0f}. "
        "It shows what your money is worth in today's dollars."
    )
    col3.metric("📈 Real Portfolio", f"${final_real:,.0f}", help=real_text)

    # 🎯 Retirement Date
    retirement_text = (
        f"You will reach retirement age on {retirement_date.strftime('%b %d, %Y')}. "
        "This is when you can start using your money to cover living expenses."
    )
    col4.metric("🎯 Retirement Date", retirement_date.strftime("%b %d, %Y"), help=retirement_text)

    # Pie chart: Contributions vs Growth
    total_contrib = savings + monthly_investment*12*max(0, retirement_age-age)
    growth = final_nominal - total_contrib
    with col5:
        fig2, ax2 = plt.subplots(figsize=(2.5,2.5))
        ax2.pie(
            [max(total_contrib,0), max(growth,0)],
            labels=["Contributions", "Investment Growth"],
            autopct="%1.0f%%",
            startangle=90,
            colors=["#4e79a7","#f28e2b"]
        )
        ax2.set_title("Wealth Sources", fontsize=10)
        st.pyplot(fig2)
    st.caption("Pie chart shows how much of your wealth comes from your savings vs investment growth.")

    # =========================
    # Gamified FIRE Tracker
    # =========================
    st.subheader("Your FIRE Progress Tracker")

    latest_real_value = df_yearly["Real Portfolio (CAD)"].iloc[0]
    fire_progress = min(latest_real_value / fire_number, 1.0)

    # -------------------------
    # Progress Bar
    # -------------------------
    st.progress(fire_progress)

    st.markdown(
        f"**Progress to Financial Independence:** {fire_progress*100:,.1f}% complete"
    )

    # -------------------------
    # Level System
    # -------------------------
    if fire_progress < 0.25:
        level = "Level 1: Getting Started"
    elif fire_progress < 0.5:
        level = "Level 2: Building Momentum"
    elif fire_progress < 0.75:
        level = "Level 3: Serious Wealth Builder"
    elif fire_progress < 1:
        level = "Level 4: Almost Free"
    else:
        level = "Level 5: Financially Independent"

    st.markdown(f"### {level}")

    # =========================
    # Interactive Plotly Chart
    # =========================
    fig = go.Figure()

    # Nominal line
    fig.add_trace(go.Scatter(
        x=df_yearly["Age"],
        y=df_yearly["Nominal Portfolio (CAD)"],
        mode="lines",
        name="Portfolio Value",
        line=dict(width=4, color="#1f77b4"),
        hovertemplate=
        "<b>Age:</b> %{x:.1f}<br>" +
        "<b>Portfolio:</b> $%{y:,.0f}<br>" +
        "This is what your account statement shows.<extra></extra>"
    ))

    # Real line
    fig.add_trace(go.Scatter(
        x=df_yearly["Age"],
        y=df_yearly["Real Portfolio (CAD)"],
        mode="lines",
        name="Inflation Adjusted Value",
        line=dict(width=4, dash="dash", color="#2ca02c"),
        hovertemplate=
        "<b>Age:</b> %{x:.1f}<br>" +
        "<b>Today's Dollar Value:</b> $%{y:,.0f}<br>" +
        "This reflects real buying power.<extra></extra>"
    ))

    # FIRE Target Line
    fig.add_hline(
        y=fire_number,
        line_dash="dot",
        line_width=3,
        line_color="#ff7f0e",
        annotation_text="Financial Independence Target",
        annotation_position="top left"
    )

    # Retirement Shaded Area
    fig.add_vrect(
        x0=retirement_age,
        x1=life_expectancy,
        fillcolor="orange",
        opacity=0.07,
        line_width=0,
        annotation_text="Retirement Phase",
        annotation_position="top left"
    )

    # You Are Here Marker
    fig.add_trace(go.Scatter(
        x=[age],
        y=[df_yearly["Nominal Portfolio (CAD)"].iloc[0]],
        mode="markers+text",
        marker=dict(size=14, color="black"),
        text=["You Are Here"],
        textposition="top center",
        showlegend=False
    ))

    # FIRE Achieved Marker
    if fire_age:
        fire_value = df_yearly.loc[df_yearly["Age"] >= fire_age,
                                "Real Portfolio (CAD)"].iloc[0]

        fig.add_trace(go.Scatter(
            x=[fire_age],
            y=[fire_value],
            mode="markers+text",
            marker=dict(size=16, color="gold"),
            text=["Work Becomes Optional Here"],
            textposition="top center",
            showlegend=False
        ))

        st.success("Congratulations. Based on this projection, you reach Financial Independence.")

    # Layout Styling
    fig.update_layout(
        title="Your Road to Financial Independence",
        xaxis_title="Your Age",
        yaxis_title="Portfolio Value (Dollars)",
        template="plotly_white",
        hovermode="x unified",
        height=650
    )

    fig.update_yaxes(tickprefix="$", separatethousands=True)

    st.plotly_chart(fig, use_container_width=True)



    # =========================
    # Monte Carlo Simulation (updated)
    # =========================
    with st.expander("🎲 Monte Carlo Simulation (Risk Analysis)"):
        simulations = 2000
        end_values = []

        for _ in range(simulations):
            balance_sim = savings
            cumulative_inflation_sim = 1.0

            for month in range(months_total):
                current_age = age + month/12

                # Determine contribution or withdrawal
                contribution = monthly_investment if current_age < retirement_age else 0
                withdrawal = monthly_expenses * cumulative_inflation_sim if current_age >= retirement_age else 0

                # Add random return for this month
                random_return = np.random.normal(return_rate/100, 0.12)/12
                balance_sim = balance_sim*(1+random_return) + contribution - withdrawal

                # Update inflation for withdrawals
                cumulative_inflation_sim *= (1 + monthly_inflation)

            end_values.append(balance_sim)

        p10, p50, p90 = np.percentile(end_values, [10,50,90])
        
        # Display with human-friendly explanations
        st.markdown(
            f"10th percentile: **${p10:,.0f}** 🛈 — In 10% of worst-case scenarios, your portfolio might end up this low after including contributions, withdrawals, and investment variability."
        )
        st.markdown(
            f"Median outcome: **${p50:,.0f}** 🛈 — Most likely portfolio outcome (50th percentile), including all contributions and withdrawals."
        )
        st.markdown(
            f"90th percentile: **${p90:,.0f}** 🛈 — In 10% of best-case scenarios, your portfolio could reach this high."
        )

    # =========================
    # Detailed Yearly Table
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
        st.caption("Table shows portfolio, contributions, and withdrawals year by year. All amounts are easy-to-read dollars.")

