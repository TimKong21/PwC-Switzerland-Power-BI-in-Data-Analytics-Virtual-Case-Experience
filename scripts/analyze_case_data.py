"""Generate the static site's chart data from the three supplied case workbooks.

The GitHub Pages site reads the committed JSON output at runtime. This script is
the auditable analysis step: it does not read, write, or alter the PBIX files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site" / "data" / "case-metrics.json"


def number(value: float | int | None, digits: int = 2) -> float | int | None:
    if pd.isna(value):
        return None
    result = round(float(value), digits)
    return int(result) if result.is_integer() else result


def percent(numerator: int | float, denominator: int | float, digits: int = 1) -> float:
    return number(numerator / denominator * 100, digits) if denominator else 0


def records(frame: pd.DataFrame) -> list[dict]:
    return json.loads(frame.to_json(orient="records"))


def category_counts(frame: pd.DataFrame, column: str, *, order: list[str] | None = None) -> list[dict]:
    grouped = frame.groupby(column, dropna=False).size().rename("count").reset_index()
    grouped = grouped.rename(columns={column: "label"})
    grouped["share"] = grouped["count"].apply(lambda count: percent(count, len(frame)))
    if order:
        grouped["label"] = pd.Categorical(grouped["label"], categories=order, ordered=True)
        grouped = grouped.sort_values("label")
        grouped["label"] = grouped["label"].astype(str)
    else:
        grouped = grouped.sort_values("count", ascending=False)
    return records(grouped)


def loyalty_band(tenure: float) -> str:
    if tenure <= 12:
        return "< 1 year"
    if tenure <= 24:
        return "< 2 years"
    if tenure <= 36:
        return "< 3 years"
    if tenure <= 48:
        return "< 4 years"
    if tenure <= 60:
        return "< 5 years"
    return "< 6 years"


def call_center_metrics() -> dict:
    source = ROOT / "Task 1 - Call Centre Trends" / "01 Call-Center-Dataset.xlsx"
    calls = pd.read_excel(source)
    calls["Date"] = pd.to_datetime(calls["Date"])
    calls["hour"] = pd.to_datetime(calls["Time"].astype(str), format="%H:%M:%S").dt.hour
    calls["month"] = calls["Date"].dt.month
    answered = calls["Answered (Y/N)"].eq("Y")
    resolved = calls["Resolved"].eq("Y")
    month_order = [1, 2, 3]

    monthly = (
        calls.groupby(["month", "Answered (Y/N)"]).size().unstack(fill_value=0).reindex(month_order, fill_value=0)
    )
    monthly = monthly.rename(index={1: "January", 2: "February", 3: "March"}).reset_index(names="label")
    monthly["answered"] = monthly.get("Y", 0)
    monthly["unanswered"] = monthly.get("N", 0)
    monthly["total"] = monthly["answered"] + monthly["unanswered"]

    agent = (
        calls.groupby("Agent")
        .agg(
            answered=("Answered (Y/N)", lambda value: int(value.eq("Y").sum())),
            resolved=("Resolved", lambda value: int(value.eq("Y").sum())),
            satisfaction=("Satisfaction rating", "mean"),
            answer_speed=("Speed of answer in secs", "mean"),
        )
        .reset_index()
        .rename(columns={"Agent": "label"})
        .sort_values("label")
    )
    agent["satisfaction"] = agent["satisfaction"].map(number)
    agent["answer_speed"] = agent["answer_speed"].map(number)

    hourly = calls.groupby("hour").size().rename("count").reset_index().rename(columns={"hour": "label"})

    return {
        "source": "Task 1 - Call Centre Trends/01 Call-Center-Dataset.xlsx",
        "reportPages": ["Call Center Trend Analysis Dashboard"],
        "kpis": {
            "totalCalls": int(len(calls)),
            "averageAnswerSpeed": number(calls.loc[answered, "Speed of answer in secs"].mean()),
            "averageSatisfaction": number(calls["Satisfaction rating"].mean()),
            "answered": int(answered.sum()),
            "answeredRate": percent(answered.sum(), len(calls), 2),
            "resolved": int(resolved.sum()),
            "resolvedRate": percent(resolved.sum(), len(calls), 2),
        },
        "charts": {
            "answerOutcome": [
                {"label": "Answered", "count": int(answered.sum()), "share": percent(answered.sum(), len(calls), 2)},
                {"label": "Not answered", "count": int((~answered).sum()), "share": percent((~answered).sum(), len(calls), 2)},
            ],
            "resolutionOutcome": [
                {"label": "Resolved", "count": int(resolved.sum()), "share": percent(resolved.sum(), len(calls), 2)},
                {"label": "Not resolved", "count": int((~resolved).sum()), "share": percent((~resolved).sum(), len(calls), 2)},
            ],
            "hourlyCalls": records(hourly),
            "monthlyCalls": records(monthly[["label", "answered", "unanswered", "total"]]),
            "agentStatistics": records(agent),
        },
    }


def churn_metrics() -> dict:
    source = ROOT / "Task 2 - Customer Retention" / "02 Churn-Dataset.xlsx"
    customers = pd.read_excel(source, sheet_name="01 Churn-Dataset")
    customers["TotalCharges"] = pd.to_numeric(customers["TotalCharges"], errors="coerce").fillna(0)
    customers["loyalty"] = customers["tenure"].map(loyalty_band)
    churned = customers.loc[customers["Churn"].eq("Yes")].copy()
    loyalty_order = ["< 1 year", "< 2 years", "< 3 years", "< 4 years", "< 5 years", "< 6 years"]
    contract_order = ["Month-to-month", "One year", "Two year"]

    payment_profile = category_counts(churned, "PaymentMethod")
    payment_profile = sorted(payment_profile, key=lambda item: item["count"], reverse=True)
    service_share = []
    for field, label in [
        ("PhoneService", "Phone service"),
        ("StreamingTV", "Streaming TV"),
        ("StreamingMovies", "Streaming Movies"),
        ("DeviceProtection", "Device protection"),
        ("OnlineBackup", "Online backup"),
        ("TechSupport", "Tech Support"),
        ("OnlineSecurity", "Online security"),
    ]:
        service_share.append({"label": label, "share": percent(churned[field].eq("Yes").sum(), len(churned))})

    internet = (
        customers.groupby("InternetService")
        .agg(customers=("customerID", "size"), churned=("Churn", lambda value: int(value.eq("Yes").sum())))
        .reset_index()
        .rename(columns={"InternetService": "label"})
    )
    internet["churnRate"] = internet.apply(lambda row: percent(row["churned"], row["customers"]), axis=1)
    internet = internet.sort_values("customers", ascending=False)

    payment_risk = (
        customers.groupby("PaymentMethod")
        .agg(customers=("customerID", "size"), churned=("Churn", lambda value: int(value.eq("Yes").sum())), monthlyCharges=("MonthlyCharges", "sum"))
        .reset_index()
        .rename(columns={"PaymentMethod": "label"})
    )
    payment_risk["churnRate"] = payment_risk.apply(lambda row: percent(row["churned"], row["customers"]), axis=1)
    payment_risk["monthlyCharges"] = payment_risk["monthlyCharges"].map(number)
    payment_risk = payment_risk.sort_values("churnRate", ascending=False)

    tickets = (
        customers.groupby("Churn")
        .agg(adminTickets=("numAdminTickets", "sum"), techTickets=("numTechTickets", "sum"))
        .reset_index()
        .rename(columns={"Churn": "label"})
        .sort_values("label")
    )

    charges = (
        customers.groupby(["Churn", "InternetService"])["TotalCharges"]
        .sum()
        .reset_index()
        .rename(columns={"Churn": "outcome", "InternetService": "service", "TotalCharges": "value"})
    )
    charges["value"] = charges["value"].map(number)

    contract_tenure = (
        customers.groupby(["Contract", "loyalty"])
        .agg(customers=("customerID", "size"), churned=("Churn", lambda value: int(value.eq("Yes").sum())), monthlyCharges=("MonthlyCharges", "sum"))
        .reset_index()
        .rename(columns={"Contract": "contract", "loyalty": "label"})
    )
    contract_tenure["contract"] = pd.Categorical(contract_tenure["contract"], categories=contract_order, ordered=True)
    contract_tenure["label"] = pd.Categorical(contract_tenure["label"], categories=loyalty_order, ordered=True)
    contract_tenure["churnRate"] = contract_tenure.apply(lambda row: percent(row["churned"], row["customers"]), axis=1)
    contract_tenure["monthlyCharges"] = contract_tenure["monthlyCharges"].map(number)
    contract_tenure = contract_tenure.sort_values(["contract", "label"])
    contract_tenure["contract"] = contract_tenure["contract"].astype(str)
    contract_tenure["label"] = contract_tenure["label"].astype(str)

    return {
        "source": "Task 2 - Customer Retention/02 Churn-Dataset.xlsx",
        "reportPages": ["Customer Churn Exploratory Dashboard", "Customer Risk Analysis Dashboard"],
        "kpis": {
            "totalCustomers": int(len(customers)),
            "overallChurnRate": percent(len(churned), len(customers)),
        },
        "pageOne": {
            "kpis": {
                "churnedCustomers": int(len(churned)),
                "techTickets": int(churned["numTechTickets"].sum()),
                "adminTickets": int(churned["numAdminTickets"].sum()),
                "totalCharges": number(churned["TotalCharges"].sum()),
                "averageMonthlyCharges": number(churned["MonthlyCharges"].mean()),
                "averageTotalCharges": number(churned["TotalCharges"].mean()),
            },
            "demographics": {
                "gender": category_counts(churned, "gender"),
                "seniorCitizen": percent(churned["SeniorCitizen"].eq(1).sum(), len(churned)),
                "partner": percent(churned["Partner"].eq("Yes").sum(), len(churned)),
                "dependents": percent(churned["Dependents"].eq("Yes").sum(), len(churned)),
                "loyalty": category_counts(churned, "loyalty", order=loyalty_order),
            },
            "account": {
                "payment": payment_profile,
                "paperless": category_counts(churned, "PaperlessBilling", order=["Yes", "No"]),
                "contract": category_counts(churned, "Contract", order=contract_order),
            },
            "services": {
                "adoption": service_share,
                "multipleLines": category_counts(churned, "MultipleLines"),
                "internetService": category_counts(churned, "InternetService"),
            },
        },
        "pageTwo": {
            "kpis": {"totalCharges": number(customers["TotalCharges"].sum())},
            "internetChurn": records(internet),
            "chargesByOutcomeAndService": records(charges),
            "paymentRisk": records(payment_risk),
            "ticketsByOutcome": records(tickets),
            "contractTenure": records(contract_tenure),
            "contractTenureByContract": {
                contract: records(contract_tenure.loc[contract_tenure["contract"].eq(contract), ["label", "churnRate", "monthlyCharges"]])
                for contract in contract_order
            },
        },
    }


def inclusion_metrics() -> dict:
    source = ROOT / "Task 3 - Diversity & Inclusion" / "03 Diversity-Inclusion-Dataset.xlsx"
    people = pd.read_excel(source, sheet_name="Pharma Group AG")
    level_fy20 = "Job Level after FY20 promotions"
    level_fy21 = "Job Level after FY21 promotions"
    level_order = [
        "1 - Executive",
        "2 - Director",
        "3 - Senior Manager",
        "4 - Manager",
        "5 - Senior Officer",
        "6 - Junior Officer",
    ]
    people[level_fy20] = pd.Categorical(people[level_fy20], categories=level_order, ordered=True)
    people[level_fy21] = pd.Categorical(people[level_fy21], categories=level_order, ordered=True)
    promotion_base = people.loc[people["In base group for Promotion FY21"].eq("Yes")]
    turnover_base = people.loc[people["In base group for turnover FY20"].eq("Y")]

    level_gender_fy20 = (
        people.groupby([level_fy20, "Gender"], observed=True).size().unstack(fill_value=0).reindex(level_order).reset_index()
        .rename(columns={level_fy20: "label"})
    )
    level_gender_fy20["Female"] = level_gender_fy20.get("Female", 0)
    level_gender_fy20["Male"] = level_gender_fy20.get("Male", 0)

    promotion = (
        people.loc[people["Promotion in FY21?"].eq("Yes")]
        .groupby([level_fy20, "Gender"], observed=True)
        .size().unstack(fill_value=0).reindex(level_order).fillna(0).reset_index()
        .rename(columns={level_fy20: "label"})
    )
    promotion["Female"] = promotion.get("Female", 0)
    promotion["Male"] = promotion.get("Male", 0)
    promotion["femaleShare"] = promotion.apply(lambda row: percent(row["Female"], row["Female"] + row["Male"]), axis=1)

    time_in_level = (
        people.groupby([level_fy20, "Gender"], observed=True)["Time in Job Level @01.07.2020"]
        .mean().unstack().reindex(level_order).reset_index().rename(columns={level_fy20: "label"})
    )
    time_in_level["Female"] = time_in_level.get("Female").map(number)
    time_in_level["Male"] = time_in_level.get("Male").map(number)

    performance = (
        people.groupby([level_fy20, "Gender"], observed=True)["FY20 Performance Rating"]
        .mean().unstack().reindex(level_order).reset_index().rename(columns={level_fy20: "label"})
    )
    performance["Female"] = performance.get("Female").map(number)
    performance["Male"] = performance.get("Male").map(number)

    performance_distribution = (
        people.groupby(["FY20 Performance Rating", "Gender"], observed=True).size().unstack(fill_value=0).reindex([1.0, 2.0, 3.0, 4.0], fill_value=0).reset_index()
        .rename(columns={"FY20 Performance Rating": "label"})
    )
    performance_distribution["label"] = performance_distribution["label"].astype(int).astype(str)
    performance_distribution["Female"] = performance_distribution.get("Female", 0)
    performance_distribution["Male"] = performance_distribution.get("Male", 0)

    def executive_balance(level: str) -> list[dict]:
        cohort = people.loc[people[level].eq("1 - Executive")]
        return category_counts(cohort, "Gender")

    executive_fy20 = executive_balance(level_fy20)
    executive_fy21 = executive_balance(level_fy21)
    promotion_rate = (
        promotion_base.groupby("Gender")
        .agg(eligible=("Employee ID", "size"), promoted=("Promotion in FY21?", lambda value: int(value.eq("Yes").sum())))
        .assign(rate=lambda frame: frame.apply(lambda row: percent(row["promoted"], row["eligible"]), axis=1))
        .reset_index().rename(columns={"Gender": "label"})
    )

    def category_share(items: list[dict], label: str) -> float:
        return next(item["share"] for item in items if item["label"] == label)

    age_level = (
        people.groupby(["Age group", level_fy21], observed=True).size().reset_index(name="count")
        .rename(columns={"Age group": "ageGroup", level_fy21: "level"})
    )

    return {
        "source": "Task 3 - Diversity & Inclusion/03 Diversity-Inclusion-Dataset.xlsx (Pharma Group AG sheet)",
        "reportPages": ["Diversity & Inclusion Analysis Dashboard I", "Diversity & Inclusion Analysis Dashboard II"],
        "pageOne": {
            "kpis": {
                "womenWorkforceShare": percent(people["Gender"].eq("Female").sum(), len(people)),
                "menWorkforceShare": percent(people["Gender"].eq("Male").sum(), len(people)),
                "overallTurnoverRate": percent(people["FY20 leaver?"].eq("Yes").sum(), len(people)),
                "womenPromotionRate": number(promotion_rate.loc[promotion_rate["label"].eq("Female"), "rate"].iloc[0]),
            },
            "hiringByLevel": records(level_gender_fy20[["label", "Female", "Male"]]),
            "promotionByLevel": records(promotion[["label", "Female", "Male", "femaleShare"]]),
            "timeInLevel": records(time_in_level[["label", "Female", "Male"]]),
            "performanceByLevel": records(performance[["label", "Female", "Male"]]),
        },
        "pageTwo": {
            "kpis": {
                "averageRatingMen": number(people.loc[people["Gender"].eq("Male"), "FY20 Performance Rating"].mean()),
                "averageRatingWomen": number(people.loc[people["Gender"].eq("Female"), "FY20 Performance Rating"].mean()),
                "age20to29": int(people["Age group"].eq("20 to 29").sum()),
                "womenExecutiveShareFY21": category_share(executive_fy21, "Female"),
            },
            "performanceDistribution": records(performance_distribution[["label", "Female", "Male"]]),
            "executiveBalance": {
                "fy20": executive_fy20,
                "fy21": executive_fy21,
            },
            "ageLevel": records(age_level),
            "promotionRate": records(promotion_rate),
        },
    }


payload = {
    "generatedFrom": "Source workbooks in this repository; see scripts/analyze_case_data.py for every aggregation.",
    "callCenter": call_center_metrics(),
    "churn": churn_metrics(),
    "inclusion": inclusion_metrics(),
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
print(f"Wrote {OUTPUT.relative_to(ROOT)}")
