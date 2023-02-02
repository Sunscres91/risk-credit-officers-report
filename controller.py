import pyodbc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import math
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from datetime import timedelta, datetime
from plotly.subplots import make_subplots
import statistics
from helper_functions import create_button


cm = sns.light_palette("green", as_cmap=True)


colors = px.colors.qualitative.Prism

d = datetime.today() - timedelta(days=90)

dwh = (
    "Driver={SQL Server Native Client 11.0};"
    "Server=dwh;"
    "Database=dwh;"
    "UID=risk;"
    "PWD=12345678;"
)
cnxn_2 = pyodbc.connect(dwh)

cnxn_str = (
    "Driver={SQL Server Native Client 11.0};"
    "Server=10.1.1.19;"
    "Database=cashcredit;"
    "UID=sstanev;"
    "PWD=12345678"
)
cnxn = pyodbc.connect(cnxn_str)


def find_number(x):
    x = x["ScoreDecision"].upper()
    x = x.replace(":", ": ")
    x = x.replace(".", " . ")
    if "ОТКАЗАН" in x:
        return 0
    elif "ОТКАЗ" in x or x == "ПРЕПОРЪЧАН ЗА OТКАЗ":
        return 100000
    elif "МНЕНИЕ" in x:
        return 500
    elif "ИСКА" in x:
        return 10000
    else:
        return [int(s) for s in x.split() if s.isdigit()][0]


def generate_report(channel, products, start_date, end_date):

    len_products = len(products)

    if len(channel) == 0:
        st.warning("Choose at least one Channel from the menu")
    else:

        channel = (
            tuple(channel) + tuple(channel) if len(channel) <= 1 else tuple(channel)
        )
        clienttype = tuple(["NEW", "REPEATWITHOUTHISTORY", "REPEAT"])
        products = (
            tuple(products) + tuple(products)
            if len(products) > 0
            else tuple(
                [
                    "Кеш на ден",
                    "Кредитна линия",
                    "Пенсионер",
                    "Cashio Wave",
                    "Cashio Fix",
                    "Cashio Uni",
                    "A1Credit",
                    "Кредит на момента",
                    "Кредит решение",
                    "Кредит премиум",
                    "Потребителски кредит",
                    "Кредит за Майки",
                    "Обединение",
                    "Държавен служител",
                    "Специален Продукт",
                    "A1 Кредит екстра",
                    "A1 Кредит плюс",
                    "A1 Кредит стандарт",
                    "A1 Потребителски кредит",
                    "A1Credit",
                ]
            )
        )

        default = pd.read_sql(
            """declare @char char='|'
select 
l.CreditID,
case when isnull(FirstInstalmentDPD,0)>isnull(SecondInstalmentDPD,0) then FirstInstalmentDPD
else isnull(SecondInstalmentDPD,0) end as maxFSDPD
,FirstInstalmentDPD
,SecondInstalmentDPD 

from (
select CreditID,
AllInstDPD,
FirstInstalmentDPD,
case when CHARINDEX(@char,nextstr)=0 then nextstr -- ще върне стойността на втората вноска ако кредита е за 2 вноски, или "null" (в случай, че кредита е за една вноска или няма запис в "AllInstDPD") 
else convert(int,substring(nextstr,1,CHARINDEX(@char,nextstr)-1)) end AS  SecondInstalmentDPD

 from (
select creditid,AllInstDPD
,case when CHARINDEX(@char,AllInstDPD)=0 then AllInstDPD --когато кредита е за 1 вноска или няма запис в "AllInstDPD"
else convert(int,substring(AllInstDPD,1,CHARINDEX(@char,AllInstDPD)-1)) end AS  FirstInstalmentDPD
,case when CHARINDEX(@char,AllInstDPD)=0 then null --когато кредита е за 1 вноска или няма запис в "AllInstDPD"
else substring(AllInstDPD,CHARINDEX(@char,AllInstDPD)+1,len(AllInstDPD)) end as nextstr -- модулиране на "AllInstDPD" с премахване на данните за първата вноска
from CommonCredits where AllInstDPD is not null and disbursementdate is not null and DisbursementDate > '1-1-2019')ms)l 

order by 1 desc""",
            cnxn_2,
        )

        df = pd.read_sql(
            f"""
        set datefirst 1
        select se.creditID,se.PID,RecommendProductName,se.clientType,se.CapitalRequested,overridereason,se.RequestDate,se.Channel,PreapprovedAmount,ScoreDecision,se.RequestOffice,FinalDecision,RejectedReason,se.ProductName,se.DecisionUser,cc.ApprovedAmount,disbursementdate,cc.ApprovedTerm,cc.Status,case when disbursementdate is null then month(se.RequestDate) when DisbursementDate is not null then month(DisbursementDate) end Month ,case when disbursementdate is null then Year(se.RequestDate) when DisbursementDate is not null then Year(DisbursementDate) end Year ,RelID,case when disbursementdate is null then DATEPART(ww,se.RequestDate) when DisbursementDate is not null then DATEPART(ww,cc.disbursementdate) end Week  ,MaxCreditDPD,ceiling(DATEDIFF(d,disbursementdate,endcreditdate)/30) + 1 as loanterm,FullInstallmentAmount,FirstOpenInstDPD from scoreevents se
        left join commoncredits cc on cc.creditid = se.creditid
        where se.channel in {channel}
        and se.requestDate between '{start_date}' and '{end_date}'
        and se.clienttype in {clienttype}
        and finalDecision != 'КОНТРА ОФЕРТА'
        and se.decisionuser in ('nikolai.tishinov@cashcredit.bg',
        'yordan.babadzhankov@cashcredit.bg',
        'gergana.evdokieva@cashcredit.bg',
        'kristina.ivanova@cashcredit.bg',
        'hristiyana.uzunova@cashcredit.bg',
        'nikoleta.veselinova@cashcredit.bg','sysuser_SMS')
        """,
            cnxn_2,
        )

        if "Кеш Кредит ЕАД" in channel:
            df_2 = pd.read_sql(
                f""" select se.creditID,se.PID,RecommendProductName,se.clientType,se.CapitalRequested,overridereason,se.RequestDate,se.Channel,PreapprovedAmount,ScoreDecision,se.RequestOffice,FinalDecision,RejectedReason,se.ProductName,se.DecisionUser,cc.ApprovedAmount,disbursementdate,cc.ApprovedTerm,cc.Status,case when disbursementdate is null then month(se.RequestDate) when DisbursementDate is not null then month(DisbursementDate) end Month ,case when disbursementdate is null then year(se.RequestDate) when DisbursementDate is not null then year(DisbursementDate) end Year ,RelID,case when disbursementdate is null then DATEPART(ww,se.RequestDate) when DisbursementDate is not null then DATEPART(ww,cc.disbursementdate) end Week  ,MaxCreditDPD,ceiling(DATEDIFF(d,disbursementdate,endcreditdate)/30) + 1 as loanterm,FullInstallmentAmount,FirstOpenInstDPD from scoreevents se
        left join commoncredits cc on cc.creditid = se.creditid
        where se.channel = 'Call Center'
        and se.requestDate between '{start_date}' and '{end_date}'
        and se.clienttype in {clienttype}
        and se.requestoffice != 'CALL CENTER' 
        and finalDecision != 'КОНТРА ОФЕРТА'
        and se.decisionuser in ('nikolai.tishinov@cashcredit.bg',
        'yordan.babadzhankov@cashcredit.bg',
        'gergana.evdokieva@cashcredit.bg',
        'kristina.ivanova@cashcredit.bg',
        'hristiyana.uzunova@cashcredit.bg',
        'nikoleta.veselinova@cashcredit.bg','sysuser_SMS')
        """,
                cnxn_2,
            )
            df = pd.concat([df, df_2])

        if "Web" in channel:
            df_3 = pd.read_sql(
                f""" select se.creditID,se.PID,RecommendProductName,se.clientType,se.CapitalRequested,overridereason,se.RequestDate,se.Channel,PreapprovedAmount,ScoreDecision,se.RequestOffice,FinalDecision,RejectedReason,se.ProductName,se.DecisionUser,cc.ApprovedAmount,disbursementdate,cc.ApprovedTerm,cc.Status,case when disbursementdate is null then month(se.RequestDate) when DisbursementDate is not null then month(DisbursementDate) end Month ,case when disbursementdate is null then Year(se.RequestDate) when DisbursementDate is not null then Year(DisbursementDate) end Year ,RelID,case when disbursementdate is null then DATEPART(ww,se.RequestDate) when DisbursementDate is not null then DATEPART(ww,cc.disbursementdate) end Week  ,MaxCreditDPD,ceiling(DATEDIFF(d,disbursementdate,endcreditdate)/30) + 1 as loanterm,FullInstallmentAmount,FirstOpenInstDPD from scoreevents se
        left join commoncredits cc on cc.creditid = se.creditid
        where se.channel = 'Call Center'
        and se.requestDate between '{start_date}' and '{end_date}'
        and se.clienttype in {clienttype}
        and se.requestoffice = 'CALL CENTER' 
        and finalDecision != 'КОНТРА ОФЕРТА'
        and se.decisionuser in ('nikolai.tishinov@cashcredit.bg',
        'yordan.babadzhankov@cashcredit.bg',
        'gergana.evdokieva@cashcredit.bg',
        'kristina.ivanova@cashcredit.bg',
        'hristiyana.uzunova@cashcredit.bg',
        'nikoleta.veselinova@cashcredit.bg','sysuser_SMS')

        """,
                cnxn_2,
            )
            df = pd.concat([df, df_3])

        df.loc[df["ProductName"] == "Spec", "ProductName"] = "Специален Продукт"
        df.loc[
            df["ProductName"] == "Специален Продукт", "RecommendProductName"
        ] = "Специален Продукт"

        df["RecommendProductName"].fillna(df["ProductName"], inplace=True)

        df = df.loc[df["ScoreDecision"] != "Одобрен%-1.00/500*1000|2000"]
        # Remove Duplicates caused by Change in Decision
        df.sort_values(by=["creditID", "FinalDecision"], inplace=True)
        df.drop_duplicates(subset=["creditID"], keep="first", inplace=True)

        ids = tuple(df.loc[df["RelID"] > 0]["RelID"].values)

        try:
            update_df = pd.read_sql(
                f"""
            select creditID,ProductName,disbursementdate,CapitalRequested from scoreevents 
            where creditID in {ids}
            and requestdate > '3-1-2022'
            """,
                cnxn_2,
            )

            df.set_index("RelID", inplace=True)
            df.update(update_df.set_index("creditID"))
            df.reset_index(inplace=True)  # to recover the initial structure
        except:
            pass

        df.loc[df["clientType"] == "REPEATWITHOUTHISTORY", "clientType"] = "NEW"

        df = df.loc[df["RecommendProductName"].isin(products)]

        df = df.merge(default, left_on="creditID", right_on="CreditID", how="left")

        grouped = (
            df.groupby(["DecisionUser", "clientType"])
            .agg({"clientType": "count"})
            .unstack()
        )

        grouped["percentage of clients which are New"] = round(
            grouped.iloc[:, 0] / (grouped.iloc[:, 0] + grouped.iloc[:, 1]) * 100, 2
        )

        s1, s2 = st.columns(2)
        s1.markdown("### Percent of Decisions on New and Repeat Customers")
        s1.write(grouped)

        fig = px.bar(
            grouped,
            x=grouped.index,
            y="percentage of clients which are New",
            title="Percent of Decisions on New and Repeat Customers",
            text_auto=True,
        )
        fig.update_layout(barmode="stack", xaxis={"categoryorder": "total descending"})
        s2.plotly_chart(fig)

        df_new = create_table(df.loc[df["clientType"] == "NEW"])
        df_repeat = create_table(df.loc[df["clientType"] != "NEW"])

        df_new_data = df_new.data.drop(columns=["Total"]).T
        df_repeat_data = df_repeat.data.drop(columns=["Total"]).T

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add traces
        fig.add_trace(
            go.Scatter(
                x=df_new_data.index,
                y=df_new_data["Default Rate"],
                name="Default Rate",
            ),
            secondary_y=False,
        )

        fig.add_trace(
            go.Scatter(
                x=df_new_data.index,
                y=df_new_data["Approval Rate"],
                name="Approval Rate",
            ),
            secondary_y=False,
        )

        fig.add_trace(
            go.Bar(
                x=df_new_data.index,
                y=df_new_data["Taken Decisions"],
                name="Taken Decisions",
                opacity=0.3,
            ),
            secondary_y=True,
        )
        fig.update_yaxes(title_text="%", secondary_y=False)
        fig.update_yaxes(title_text="#", secondary_y=True)

        fig.update_layout(
            xaxis_title="Credit Officer",
            font=dict(
                family="Courier New, monospace",
                size=18,
                color="RebeccaPurple",
            ),
        )

        fig.update_layout(
            autosize=False,
            height=750,
        )

        st.markdown("### Decisions on New Customers")
        st.write(df_new)
        st.plotly_chart(figure_or_data=fig, use_container_width=True)

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add traces
        fig.add_trace(
            go.Scatter(
                x=df_repeat_data.index,
                y=df_repeat_data["Default Rate"],
                name="Default Rate",
            ),
            secondary_y=False,
        )

        fig.add_trace(
            go.Scatter(
                x=df_repeat_data.index,
                y=df_repeat_data["Approval Rate"],
                name="Approval Rate",
            ),
            secondary_y=False,
        )

        fig.add_trace(
            go.Bar(
                x=df_repeat_data.index,
                y=df_repeat_data["Taken Decisions"],
                name="Taken Decisions",
                opacity=0.3,
            ),
            secondary_y=True,
        )
        fig.update_yaxes(title_text="%", secondary_y=False)
        fig.update_yaxes(title_text="#", secondary_y=True)

        fig.update_layout(
            xaxis_title="Credit Officer",
            font=dict(
                family="Courier New, monospace",
                size=18,
                color="RebeccaPurple",
            ),
        )

        fig.update_layout(
            autosize=False,
            height=750,
        )
        st.markdown("### Decisions on Repeat Customers")
        st.write(df_repeat)
        st.plotly_chart(figure_or_data=fig, use_container_width=True)


def create_table(df):
    df["approved_percentage"] = 0
    df.loc[df["FinalDecision"] == "ОДОБРЕН", "approved_percentage"] = 100

    approved = df.loc[df["FinalDecision"] == "ОДОБРЕН"]

    df["MaxApproved"] = df.apply(lambda x: find_number(x), axis=1)
    df["Overrites"] = 0
    df.loc[df["ApprovedAmount"] > df["MaxApproved"], "Overrites"] = 1
    df["PreapprovedAmount"].fillna(0, inplace=True)

    df.loc[
        (df["ScoreDecision"] == "Отказан") & (df["clientType"] == "REPEAT"),
        "Overrites",
    ] = 0

    df.loc[
        df["PreapprovedAmount"] > 0,
        "Overrites",
    ] = 0
    df.loc[
        df["overridereason"] == "Препоръка от офис",
        "Overrites",
    ] = 0

    df["Disbursed"] = 0

    df.loc[
        df["Status"].isin(
            [
                "Погасен",
                "Предсрочно погасен",
                "Забавен",
                "Просрочен",
                "Активен",
                "Отказ от кредит",
            ]
        ),
        "Disbursed",
    ] = 1

    date_delta = datetime.today() - timedelta(days=60 + 31)
    df["Time"] = 0

    df.loc[df["disbursementdate"] < date_delta, "Time"] = 1

    df["Eligable"] = 0
    df.loc[(df["Time"] == 1) & (df["Disbursed"] == 1), "Eligable"] = 1

    df["Defaulted"] = 0
    df["Defaulted_maxFSDPD"] = 0
    df.loc[(df["Eligable"] == 1) & (df["MaxCreditDPD"] > 59), "Defaulted"] = 1
    df.loc[(df["Eligable"] == 1) & (df["maxFSDPD"] > 59), "Defaulted_maxFSDPD"] = 1

    df["Eligable_Overrites"] = 0
    df.loc[
        (df["Time"] == 1) & (df["Disbursed"] == 1) & (df["Overrites"] == 1),
        "Eligable_Overrites",
    ] = 1

    df["Defaulted_Overrites"] = 0
    df.loc[
        (df["Eligable_Overrites"] == 1) & (df["MaxCreditDPD"] > 59),
        "Defaulted_Overrites",
    ] = 1

    df["Defaulted_Overrites_maxFSDPD"] = 0
    df.loc[
        (df["Eligable_Overrites"] == 1) & (df["maxFSDPD"] > 59),
        "Defaulted_Overrites_maxFSDPD",
    ] = 1

    grouped = df.groupby(["DecisionUser"]).agg(
        {
            "Status": "count",
            "approved_percentage": "mean",
            "Overrites": "sum",
            "Eligable": "sum",
            "Defaulted": "sum",
            "Defaulted_maxFSDPD": "sum",
            "Defaulted_Overrites": "sum",
            "Defaulted_Overrites_maxFSDPD": "sum",
        }
    )

    grouped["Approved"] = grouped["Status"] * grouped["approved_percentage"] / 100
    grouped["Approved"] = grouped["Approved"].astype("int32")
    grouped["Overrites Percentage"] = grouped["Overrites"] / grouped["Approved"] * 100
    grouped["Default Rate"] = grouped["Defaulted"] / grouped["Eligable"] * 100
    grouped["Default Rate FS"] = (
        grouped["Defaulted_maxFSDPD"] / grouped["Eligable"] * 100
    )

    grouped["Default Rate Overrites"] = (
        grouped["Defaulted_Overrites"] / grouped["Overrites"]
    ) * 100
    grouped["Default Rate FS Overrites"] = (
        grouped["Defaulted_Overrites_maxFSDPD"] / grouped["Overrites"] * 100
    )

    grouped = grouped[
        [
            "Status",
            "approved_percentage",
            "Approved",
            "Overrites",
            "Overrites Percentage",
            "Default Rate",
            "Default Rate FS",
            "Default Rate Overrites",
            "Default Rate FS Overrites",
        ]
    ]

    grouped.columns = [
        "Taken Decisions",
        "Approval Rate",
        "Approved",
        "Overrites #",
        "Overrites %",
        "Default Rate",
        "Default Rate FS60",
        "Default Rate Overrites",
        "Default Rate Overrites FS60",
    ]

    new_row = [
        grouped["Taken Decisions"].sum(),
        grouped["Approval Rate"].mean(),
        grouped["Approved"].sum(),
        grouped["Overrites #"].sum(),
        grouped["Overrites %"].mean(),
        grouped["Default Rate"].mean(),
        grouped["Default Rate FS60"].mean(),
        grouped["Default Rate Overrites"].mean(),
        grouped["Default Rate Overrites FS60"].mean(),
    ]
    grouped.loc["Total"] = new_row

    final = pd.DataFrame()

    return grouped.T.style.format(
        formatter="{0:,.1f}%",
        subset=pd.IndexSlice[
            [
                "Approval Rate",
                "Overrites %",
                "Default Rate",
                "Default Rate FS60",
                "Default Rate Overrites",
                "Default Rate Overrites FS60",
            ],
            :,
        ],
    ).format(
        formatter="{0:,.0f}",
        subset=pd.IndexSlice[
            [
                "Taken Decisions",
                "Approved",
                "Overrites #",
            ],
            :,
        ],
    )
