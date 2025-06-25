import streamlit as st
import pandas as pd
import plotly.express as px
import io
from fpdf import FPDF
from PIL import Image
import os
from datetime import datetime
import tempfile

st.set_page_config(page_title="Agri Value Chain Analyzer", layout="wide")

st.title("🌾 Agricultural Value Chain Analyzer")

# Inputs
st.sidebar.header("Enter Value Chain Details")

num_actors = st.sidebar.number_input("Number of Actors", min_value=2, max_value=10, value=3)

actors = []
for i in range(num_actors):
    with st.sidebar.expander(f"Actor {i+1}"):
        name = st.text_input(f"Name of Actor {i+1}", key=f"name_{i}")
        cost = st.number_input(f"Buying Price (Cost)", key=f"cost_{i}")
        revenue = st.number_input(f"Selling Price (Revenue)", key=f"revenue_{i}")
        actors.append({"name": name, "cost": cost, "revenue": revenue})

# Computation
data = []
prev_revenue = 0
retail_price = actors[-1]["revenue"] if actors else 1

for actor in actors:
    gross_income = actor["revenue"] - actor["cost"]
    gross_margin = (gross_income / actor["revenue"]) * 100 if actor["revenue"] else 0
    added_value = actor["revenue"] - prev_revenue
    value_share = (added_value / retail_price) * 100 if retail_price else 0

    data.append({
        "Actor": actor["name"],
        "Buying Price": actor["cost"],
        "Selling Price": actor["revenue"],
        "Gross Income": gross_income,
        "Gross Margin (%)": round(gross_margin, 2),
        "Added Value": round(added_value, 2),
        "Value Share (%)": round(value_share, 2)
    })

    prev_revenue = actor["revenue"]

df = pd.DataFrame(data)

st.subheader("📊 Value Chain Table")
st.dataframe(df, use_container_width=True)

# Visualization
st.subheader("📈 Gross Margin & Value Share Visualization")
col1, col2 = st.columns(2)

with col1:
    color_palette = px.colors.qualitative.Bold
    fig_margin = px.bar(
        df,
        x="Actor",
        y="Gross Margin (%)",
        title="Gross Margin by Actor",
        color="Actor",
        color_discrete_sequence=color_palette
    )
    fig_margin.update_layout(template="plotly_white", title_font_size=16, font=dict(size=12))
    st.plotly_chart(fig_margin, use_container_width=True)

with col2:
    fig_share = px.bar(
        df,
        x="Actor",
        y="Value Share (%)",
        title="Value Share by Actor",
        color="Actor",
        color_discrete_sequence=color_palette
    )
    fig_share.update_layout(template="plotly_white", title_font_size=16, font=dict(size=12))
    st.plotly_chart(fig_share, use_container_width=True)

# Recommendations
st.subheader("📖 Recommendations")
recommendations = []
for row in data:
    if row["Gross Margin (%)"] < 20:
        recommendations.append(f"Actor '{row['Actor']}' has a low gross margin ({row['Gross Margin (%)']}%). Consider reducing input costs or increasing selling price.")
    if row["Value Share (%)"] < 10:
        recommendations.append(f"Actor '{row['Actor']}' has a small value share ({row['Value Share (%)']}%). Consider improving value addition strategies.")

if recommendations:
    for rec in recommendations:
        st.warning(rec)
else:
    st.success("All actors have reasonable margins and value shares.")

# Export to PDF
st.subheader("📄 Export Report")
def export_pdf(fig_margin, fig_share, image_path="logo.png"):
    pdf = FPDF()
    pdf.add_page()

    # Logo
    if os.path.exists(image_path):
        pdf.image(image_path, x=10, y=10, w=190)
        pdf.ln(45)

    # Title and timestamp
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(0, 10, "Agricultural Value Chain Analysis Report", ln=True, align="C")
    pdf.set_font("Arial", '', size=11)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.ln(10)

    # Table
    headers = ["Actor", "Buying Price", "Selling Price", "Gross Income", "Gross Margin (%)", "Added Value", "Value Share (%)"]
    col_widths = [40, 25, 25, 25, 30, 25, 30]

    pdf.set_font("Arial", 'B', size=10)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1)
    pdf.ln()

    pdf.set_font("Arial", size=10)
    for row in df.itertuples():
        pdf.cell(col_widths[0], 10, str(row.Actor), border=1)
        pdf.cell(col_widths[1], 10, str(row._2), border=1)
        pdf.cell(col_widths[2], 10, str(row._3), border=1)
        pdf.cell(col_widths[3], 10, str(row._4), border=1)
        pdf.cell(col_widths[4], 10, f"{row._5}%", border=1)
        pdf.cell(col_widths[5], 10, str(row._6), border=1)
        pdf.cell(col_widths[6], 10, f"{row._7}%", border=1)
        pdf.ln()

    # Recommendations
    pdf.ln(10)
    pdf.set_font("Arial", 'B', size=11)
    pdf.cell(200, 10, txt="Recommendations", ln=True)
    pdf.set_font("Arial", size=10)
    for rec in recommendations:
        pdf.multi_cell(0, 10, f"- {rec}")

    # Save Plotly figures as temp images
    with tempfile.TemporaryDirectory() as tmpdir:
        margin_path = os.path.join(tmpdir, "margin.png")
        share_path = os.path.join(tmpdir, "share.png")

        fig_margin.write_image(margin_path)
        fig_share.write_image(share_path)

        # Add charts
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=12)
        pdf.cell(0, 10, "Gross Margin by Actor", ln=True)
        pdf.image(margin_path, w=180)

        pdf.ln(5)
        pdf.cell(0, 10, "Value Share by Actor", ln=True)
        pdf.image(share_path, w=180)

    # Return as byte stream
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer = io.BytesIO(pdf_bytes)
    return buffer

if st.button("📄 Download PDF Report"):
    pdf_buffer = export_pdf(fig_margin, fig_share)
    st.download_button(
        label="Download Report",
        data=pdf_buffer,
        file_name="value_chain_report.pdf",
        mime="application/pdf"
    )

