import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Initialize local SQLite Database file
def init_db():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            t_type TEXT NOT NULL,
            category TEXT NOT NULL,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db() # Initialize the database

st.set_page_config(page_title="Personal Finance MVP", layout="wide")
st.title("Personal Finance dashboard")

col1, col2 = st.columns([1, 2])

# Left column: User Input Form
with col1:
    st.header("Add Transaction")
    with st.form("transaction_form", clear_on_submit=True):
        ## There are 6 fields in the form: date, description, amount, type, category, notes, you need six ? bleow.
        date = st.date_input("Date", datetime.today())
        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0.0, step=0.01) ##
        t_type = st.selectbox("type", ["Income", "Expense"])
        category = st.selectbox("Category", ["Income", "Expense", "Food", "Transport", "Entertainment", "Utilities", "Other", "Salary", "Investment", "Gift", "Healthcare", "Education", "Travel", "Shopping", "Rent", "Insurance", "Taxes"])
        notes = st.text_area("Notes (Optional)")
        submitted = st.form_submit_button("Add Transaction")

        if submitted:
            conn = sqlite3.connect('finance.db')
            c = conn.cursor()
            ## Related to the comment above, you need to add six ? in the INSERT statement below to match the six fields in the form.
            c.execute("""
                INSERT INTO transactions (date, description, amount, t_type, category, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (date.strftime("%Y-%m-%d"), description, amount, t_type,category, notes))
            conn.commit()
            conn.close()
            st.success("Transaction added successfully!")

# Fetch live Data from SQLite Database
conn = sqlite3.connect('finance.db')
df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
conn.close()

# Right Column: Dashboard summary Data Visualizations

with col2:
    st.subheader("Financial Summary")
    if not df.empty:
        total_income = df[df["t_type"] == "Income"]["amount"].sum()
        total_expense = df[df["t_type"] == "Expense"]["amount"].sum()
        net_savings = total_income - total_expense

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Income", f"${total_income:,.2f}")
        m2.metric("Total Expense", f"${total_expense:,.2f}")
        m3.metric("Net Savings", f"${net_savings:,.2f}")

        st.subheader("Spening by Category")
        expense_df = df[df["t_type"] == "Expense"]
        if not expense_df.empty:
            category_summary = expense_df.groupby("category")["amount"].sum().reset_index()
            st.bar_chart(category_summary.set_index("category"))
        else:
            st.info("No expense data available to display.")

        st.subheader("Recent Transactions")
        ## WRONG LINE st.dataframe(df)[["date", "description", "amount", "category"]
        st.dataframe(df[["date", "description", "amount", "category"]], use_container_width=True)  
    else:
        st.info("No transactions available. Please add some transactions to see the summary.")


# NEW FEATURE: CSV Backup Exporter Tool
# ----------------------------------------------------
st.write("---")
st.subheader("Data Management")

# Convert the full active DataFrame into a download-ready CSV string
csv_data = df.to_csv(index=False).encode('utf-8')

# Native web-safe download interface block
st.download_button(
    label="Download Ledger Backup (.CSV)",
    data=csv_data,
    file_name=f"finance_backup_{datetime.today().strftime('%Y-%m-%d')}.csv",
    mime="text/csv",
    help="Click to extract your transactional data out of SQLite into a standard local Excel/CSV format."
)
# ----------------------------------------------------
