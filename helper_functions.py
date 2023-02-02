import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events


def create_button(df, key):
    copy_button = Button(label="Copy Table to ClipBoard")
    copy_button.js_on_event(
        "button_click",
        CustomJS(
            args=dict(df=df.to_csv(sep="\t")),
            code="""
            if (navigator.clipboard && window.isSecureContext) {
        // navigator clipboard api method'
        return navigator.clipboard.writeText(df);
    }
else {
        // text area method
        let textArea = document.createElement("textarea");
        textArea.value = df;
        // make the textarea out of viewport
        textArea.style.position = "fixed";
        textArea.style.left = "0px";
        textArea.style.top = "0px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        return new Promise((res, rej) => {
            // here the magic happens
            document.execCommand('copy') ? res() : rej();
            textArea.remove();
        });
    }
            """,
        ),
    )

    no_event = streamlit_bokeh_events(
        copy_button,
        events="GET_TEXT",
        key=key,
        refresh_on_update=True,
        override_height=75,
        debounce_time=0,
    )
    return no_event


def determine_products(channel):
    products = []
    if "Кеш Кредит ЕАД" in channel:
        products.append("Кеш на ден")
        products.append("Кредит на момента")
        products.append("Кредит решение")
        products.append("Кредит премиум")
        products.append("Потребителски кредит")
        products.append("Пенсионер")
        products.append("Кредитна линия")
        products.append("Кредит за Майки")
        products.append("Обединение")
        products.append("Специален Продукт")

    if "Web" in channel and "Кеш Кредит ЕАД" not in channel:
        products.append("Кеш на ден")
        products.append("Кредит на момента")
        products.append("Кредит решение")
        products.append("Кредит премиум")
        products.append("Потребителски кредит")
        products.append("Пенсионер")
        products.append("Кредитна линия")
        products.append("Кредит за Майки")
        products.append("Обединение")
        products.append("Специален Продукт")

    if "Cashio" in channel:
        products.append("Cashio Wave")
        products.append("Cashio Fix")
        products.append("Cashio Uni")

    if "A1" in channel:
        products.append("A1Credit")
        products.append("A1 Кредит екстра")
        products.append("A1 Кредит плюс")
        products.append("A1 Кредит стандарт")
        products.append("A1 Потребителски кредит")

    return products
