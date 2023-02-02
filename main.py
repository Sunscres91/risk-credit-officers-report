import pyodbc
import pandas as pd
import numpy as np
import streamlit as st
import datetime
from controller import generate_report
from helper_functions import determine_products
from PIL import Image
from datetime import datetime, timedelta

image = Image.open("logo.png")
st.set_page_config(page_title="Credit Officers Report", layout="wide")


col1, col2, col3 = st.columns(3)

with col1:
    st.write(" ")

with col2:
    st.image(image)

with col3:
    st.write(" ")


channel = st.multiselect(
    "Channel", ["Кеш Кредит ЕАД", "Web", "Cashio", "A1"], default="Кеш Кредит ЕАД"
)


# change it to 2019
start = datetime(2022, 4, 1)
today = datetime.today()


form = st.form(
    key="my_form",
)

products = form.multiselect("Products", determine_products(channel))
start_date = form.date_input("Start date", start)
end_date = form.date_input("End date", today)
submit_button = form.form_submit_button(
    label="Generate Report",
    on_click=generate_report(
        channel=channel,
        products=products,
        start_date=start_date,
        end_date=end_date,
    ),
)
