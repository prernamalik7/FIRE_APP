
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
st.set_page_config(
    page_title="🔥 FIRE Planner: Financial Independence & Early Retirement",
    page_icon="🔥",
    layout="wide"
)

# =========================
# Header Section with Pie
# =========================
header_col1, header_col2 = st.columns([3, 2])

with header_col1:
    st.title("🔥 FIRE Planner")
    st.subheader("Financial Independence, Retire Early")
    st.markdown(
        " **Know your number. Track your progress. Own your freedom.**"
    )

# =========================
# Sidebar Inputs
# =========================
st.sidebar.header("💡 Your FIRE Blueprint")

dob = st.sidebar.date_input(
    "Date of Birth",
    value=date(1994, 1, 1),
    help="Your age is calculated from this to project your portfolio growth."
)

savings = st.sidebar.number_input(
    "Current Portfolio ($)",
    0, 20_000_000, 100_000,
    help="Total amount you currently have invested or saved. Typical early savers start from $10k–$50k."
)

monthly_investment = st.sidebar.number_input(
    "Monthly Investment ($)",
    0, 100_000, 2_000,
    help="The amount you plan to invest each month. Even small consistent contributions grow over time."
)

monthly_expenses = st.sidebar.number_input(
    "Monthly Expenses ($)",
    0, 50_000, 3_000,
    help="Your average monthly spending in today’s dollars. Helps calculate your FIRE target."
)

retirement_age = st.sidebar.number_input(
    "Retirement Age",
    18, 80, 50,
    help="The age you plan to stop working. Typical FIRE enthusiasts retire between 40–55."
)

life_expectancy = st.sidebar.number_input(
    "Life Expectancy Age",
    50, 100, 85,
    help="How long you expect to live. This helps estimate how long your portfolio needs to last."
)

return_rate = st.sidebar.slider(
    "Expected Annual Return (%)",
    1, 15, 7,
    help="Projected annual growth of your investments. For a broad index fund, 6–8% is common historically."
)

inflation = st.sidebar.slider(
    "Inflation (%)",
    0, 10, 3,
    help="Expected annual inflation rate. Historically, inflation is around 2–3% per year."
)

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


    # =========================
    # Time Until FIRE
    # =========================
    years_to_fire = None
    months_to_fire = None

    if fire_age:
        total_years_float = fire_age - age
        years_to_fire = int(total_years_float)
        months_to_fire = int((total_years_float - years_to_fire) * 12)

    # Retirement date should ALWAYS exist
    retirement_date = dob + timedelta(days=int(retirement_age * 365.25))


    # =========================
    # Dashboard with vertical dividers
    # =========================
    # =========================
    # Dashboard with smaller font
    # =========================
    st.subheader("📊 FIRE Dashboard")

    col1, col2, col3, col4, col5 = st.columns([1,1,1,1,1.2])

    # Helper to render a metric with smaller value font
    def metric_html(title, value, help_text=None):
        help_icon = f"<span title='{help_text}' style='cursor:help'>🛈</span>" if help_text else ""
        st.markdown(
            f"""
            <div style='text-align:center;'>
                <div style='font-weight:bold;font-size:16px;margin-bottom:5px;'>{title} {help_icon}</div>
                <div style='font-size:20px;color:#1f77b4;font-weight:bold;'>{value}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 🔥 FIRE Number
    fire_text = f"You need ${fire_number:,.0f} to retire at age {retirement_age}. Based on 4% rule (you can withdraw 4% per year to cover your expenses) and adjusted for inflation"
    with col1:
        metric_html("🔥 FIRE Number", f"${fire_number:,.0f}", fire_text)

    # 💰 Final Portfolio
    final_text = f"Projected portfolio at age {life_expectancy if retirement_age < life_expectancy else retirement_age}."
    with col2:
        metric_html("💰 Final Portfolio", f"${final_nominal:,.0f}", final_text)

    # 📈 Real Portfolio
    real_text = f"Inflation-adjusted portfolio value — It shows what your money is worth in todays dollars."
    with col3:
        metric_html("📈 Real Portfolio", f"${final_real:,.0f}", real_text)

    # 🎯 Retirement Date
    retirement_text = f"Your desired retirement date is {retirement_date.strftime('%b %d, %Y')}. This is when you plan to start using your money to cover living expenses."
    with col4:
        metric_html("🎯 Retirement Date", retirement_date.strftime("%b %d, %Y"), retirement_text)

    # 🥂 Work Becomes Optional
    if fire_age:
        work_optional_date = dob + timedelta(days=fire_age*365.25)
        work_optional_str = work_optional_date.strftime("%b %d, %Y")
        work_optional_text = "This is the date when your portfolio can fully cover your expenses — work becomes optional!"
        with col5:
            metric_html("🥂 Work Becomes Optional", work_optional_str, work_optional_text)












    # Pie chart: Contributions vs Growth
    total_contrib = savings + monthly_investment*12*max(0, retirement_age-age)
    growth = final_nominal - total_contrib
    with header_col2:

        fig_donut = go.Figure(data=[go.Pie(
            labels=["Your Contributions", "Investment Growth"],
            values=[max(total_contrib,0), max(growth,0)],
            hole=0.55,
            marker=dict(colors=["#1f77b4", "#00c853"]),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Amount: $%{value:,.0f}<br>"
                "Share: %{percent}<extra></extra>"
            ),
            textinfo="none"
        )])

        fig_donut.update_layout(
            showlegend=True,  # 👈 bring legend back
            legend=dict(
                orientation="h",           # horizontal legend
                yanchor="bottom",
                y=-0.15,                   # place slightly below donut
                xanchor="center",
                x=0.5,
                font=dict(size=12)
            ),
            height=250,                    # compact height
            margin=dict(t=10, b=40, l=10, r=10),  # extra bottom space for legend
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        st.plotly_chart(fig_donut, use_container_width=True)




        # Add spacing and a thin grey line before the FIRE Progress Tracker
    st.markdown(
        """
        <div style="margin-top:30px;margin-bottom:20px;">
            <hr style="border:0.5px solid #d3d3d3;">
        </div>
        """,
        unsafe_allow_html=True
    )


    # =========================
    # Gamified FIRE Tracker
    # =========================
    st.subheader("Your FIRE Progress Tracker")

    latest_real_value = df_yearly["Real Portfolio (CAD)"].iloc[0]
    fire_progress = min(latest_real_value / fire_number, 1.0)

    # -------------------------
    # Progress Bar
    # -------------------------
    # -------------------------
    # Visual Level Progress Tracker
    # -------------------------

    levels = [
        (0.00, "Getting Started"),
        (0.25, "Building Momentum"),
        (0.50, "Serious Wealth Builder"),
        (0.75, "Almost Free"),
        (1.00, "Financially Independent")
    ]

    fig_progress = go.Figure()

    # Base progress line
    fig_progress.add_trace(go.Scatter(
        x=[0, 1],
        y=[0, 0],
        mode="lines",
        line=dict(width=14, color="#e0e0e0"),
        showlegend=False
    ))

    # User progress overlay
    fig_progress.add_trace(go.Scatter(
        x=[0, fire_progress],
        y=[0, 0],
        mode="lines",
        line=dict(width=14, color="#1f77b4"),
        showlegend=False
    ))

    # Level markers (FIXED edge positioning)
    for value, label in levels:

        # Prevent clipping at edges
        if value == 0:
            text_pos = "top right"
        elif value == 1:
            text_pos = "top left"
        else:
            text_pos = "top center"

        fig_progress.add_trace(go.Scatter(
            x=[value],
            y=[0],
            mode="markers+text",
            marker=dict(size=16, color="black"),
            text=[label],
            textposition=text_pos,
            showlegend=False
        ))

    # Current position marker
    fig_progress.add_trace(go.Scatter(
        x=[fire_progress],
        y=[0],
        mode="markers",
        marker=dict(size=22, color="gold"),
        showlegend=False
    ))

    fig_progress.update_layout(
        xaxis=dict(
            range=[-0.04, 1.04],  # 👈 small padding added
            tickformat=".0%",
            showgrid=False,
            zeroline=False,
            fixedrange=True
        ),
        yaxis=dict(
            visible=False,
            fixedrange=True
        ),
        height=180,
        margin=dict(l=60, r=60, t=50, b=30),  # 👈 increased margins
        template="plotly_white"
    )

    st.plotly_chart(fig_progress, use_container_width=True)

    st.markdown(
        f"### 🔥 {fire_progress*100:,.1f}% Complete"
    )








    # =========================
    # Interactive Plotly Chart
    # =========================

    fig = go.Figure()

    # -------------------------
    # Nominal Portfolio Line
    # -------------------------
    fig.add_trace(go.Scatter(
        x=df_yearly["Age"],
        y=df_yearly["Nominal Portfolio (CAD)"],
        mode="lines",
        name="Portfolio Value",
        line=dict(width=4, color="#1f77b4"),
        hovertemplate=(
            "<b>Age:</b> %{x:.1f}<br>"
            "<b>Portfolio:</b> $%{y:,.0f}<br>"
            "This is what your account statement shows."
            "<extra></extra>"
        )
    ))

    # -------------------------
    # Real (Inflation-Adjusted) Line
    # -------------------------
    fig.add_trace(go.Scatter(
        x=df_yearly["Age"],
        y=df_yearly["Real Portfolio (CAD)"],
        mode="lines",
        name="Inflation Adjusted Value",
        line=dict(width=4, dash="dash", color="#2ca02c"),
        hovertemplate=(
            "<b>Age:</b> %{x:.1f}<br>"
            "<b>Today's Dollar Value:</b> $%{y:,.0f}<br>"
            "This reflects real buying power."
            "<extra></extra>"
        )
    ))

    # -------------------------
    # FIRE Target Line
    # -------------------------
    fig.add_hline(
        y=fire_number,
        line_dash="dot",
        line_width=3,
        line_color="#ff7f0e",
        annotation_text="Financial Independence Target",
        annotation_position="top left"
    )

    # -------------------------
    # Retirement Phase Shading
    # -------------------------
    fig.add_vrect(
        x0=retirement_age,
        x1=life_expectancy,
        fillcolor="orange",
        opacity=0.07,
        line_width=0,
        annotation_text="Retirement Phase",
        annotation_position="top left"
    )

    # -------------------------
    # Current Position Marker
    # -------------------------
    current_value = df_yearly["Nominal Portfolio (CAD)"].iloc[0]

    fig.add_trace(go.Scatter(
        x=[age],
        y=[current_value],
        mode="markers+text",
        marker=dict(
            size=18,
            color="black",
            line=dict(width=3, color="white")
        ),
        text=["You Are Here"],
        textposition="top center",
        textfont=dict(size=12, color="black"),
        cliponaxis=False,
        showlegend=False
    ))

    # -------------------------
    # FIRE Achieved Marker (Glow Effect)
    # -------------------------
    if fire_age:

        fire_value = df_yearly.loc[
            df_yearly["Age"] >= fire_age,
            "Real Portfolio (CAD)"
        ].iloc[0]

        # Glow layer (behind main marker)
        fig.add_trace(go.Scatter(
            x=[fire_age],
            y=[fire_value],
            mode="markers",
            marker=dict(
                size=42,
                color="rgba(255,215,0,0.25)"
            ),
            hoverinfo="skip",
            cliponaxis=False,
            showlegend=False
        ))

        # Main FIRE marker
        fig.add_trace(go.Scatter(
            x=[fire_age],
            y=[fire_value],
            mode="markers+text",
            marker=dict(
                size=20,
                color="gold",
                line=dict(width=3, color="white")
            ),
            text=["Work Becomes Optional Here"],
            textposition="top center",
            textfont=dict(size=12, color="black"),
            cliponaxis=False,
            showlegend=False
        ))

        st.success(
            "Congratulations. Based on this projection, you reach Financial Independence."
        )

    # -------------------------
    # Layout Styling
    # -------------------------
    fig.update_layout(
        title="Your Road to Financial Independence",
        xaxis_title="Your Age",
        yaxis_title="Portfolio Value (Dollars)",
        template="plotly_white",
        hovermode="x unified",
        height=650
    )

    fig.update_yaxes(
        tickprefix="$",
        separatethousands=True
    )

    st.plotly_chart(fig, use_container_width=True)


    st.divider()



    # =========================
    # 🎉 FIRE Messaging
    # =========================
    # =========================
    # 🎉 FIRE Messaging with Exact Date
    # =========================
    if fire_age:

        # Exact date when work becomes optional
        work_optional_date = dob + timedelta(days=fire_age*365.25)  # keep fractional part
        work_optional_str = work_optional_date.strftime("%b %d, %Y")  # e.g., Jan 01, 2030

        # Years and months until FIRE
        total_years_float = fire_age - age
        years_to_fire = int(total_years_float)
        months_to_fire = int(round((total_years_float - years_to_fire) * 12))

        # -------------------------
        # 🎉 Already Financially Independent
        # -------------------------
        if years_to_fire == 0 and months_to_fire == 0:
            st.success("🎉 Congratulations — You’re Financially Independent!")

            st.markdown(
                f"""
    ## 🥂 Work Is Officially Optional

    At age {age:.1f}, your portfolio already supports  
    **${monthly_expenses:,.0f}/month** through age **{life_expectancy}**.  

    Work becomes optional on **{work_optional_str}**.

    You built this. Freedom isn’t coming — it’s here.
    """
            )
            st.balloons()

        # -------------------------
        # 🔥 Less than 1 year to FIRE
        # -------------------------
        elif years_to_fire == 0 and months_to_fire > 0:
            st.markdown(
                f"""
    ## 🔥 Final Stretch — {months_to_fire} Month{'s' if months_to_fire > 1 else ''} to Freedom

    At your current pace — **${monthly_investment:,.0f}/month** invested at **{return_rate}%** — you reach Financial Independence at **age {fire_age:.1f}** (**{work_optional_str}**).

    That supports **${monthly_expenses:,.0f}/month** until **{life_expectancy}**.

    Stay consistent — you’re almost there!
    """
            )

        # -------------------------
        # 🚀 More than 1 year to FIRE
        # -------------------------
        else:
            st.markdown(
                f"""
    ### 🔥 You’re {years_to_fire} Year{'s' if years_to_fire > 1 else ''} From Optional Work

    At your current pace — **${monthly_investment:,.0f}/month** invested at **{return_rate}%** — you reach Financial Independence at **age {fire_age:.1f}** (**{work_optional_str}**).

    That supports **${monthly_expenses:,.0f}/month** until **{life_expectancy}**.

    Stay consistent. Time does the heavy lifting.
    """
            )

    # -------------------------
    # ⚠️ FIRE Not Reached
    # -------------------------
    else:
        st.warning(
            "Based on these assumptions, you do not reach Financial Independence within your projected lifespan. "
            "Consider increasing your monthly investments or adjusting retirement spending."
        )










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
                "Age": "{:.1f}",  # 👈 limit age to 1 decimal
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
        st.caption("Table shows portfolio, contributions, and withdrawals year by year.")

