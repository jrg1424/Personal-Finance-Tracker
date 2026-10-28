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
category_options = ["Income", "Expense", "Food", "Transport", "Entertainment", "Utilities", "Other", "Salary", "Investment", "Gift", "Healthcare", "Education", "Travel", "Shopping", "Rent", "Insurance", "Taxes", "Housing", "Miscellaneous"]

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
        category = st.selectbox("Category", category_options)
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
        st.dataframe(df[["date", "description", "amount", "t_type", "category"]], use_container_width=True)
#########Transcation Edit/Delete Feature
        st.subheader("Edit or delete a transaction")
        transaction_labels = {
            row["id"]: f'{row["date"]} | {row["description"]} | ${row["amount"]:,.2f} ({row["t_type"]})'
            for _, row in df.iterrows()
        }
        selected_id = st.selectbox(
            "Choose a transaction",
            options=list(transaction_labels),
            format_func=lambda transaction_id: transaction_labels[transaction_id],
        )
        selected_transaction = df.loc[df["id"] == selected_id].iloc[0]
        action = st.radio("Action", ["Edit", "Delete"], horizontal=True)

        if action == "Edit":
            with st.form(f"edit_transaction_form_{selected_id}"):
                edit_date = st.date_input(
                    "Date",
                    value=datetime.strptime(selected_transaction["date"], "%Y-%m-%d").date(),
                    key=f"edit_date_{selected_id}",
                )
                edit_description = st.text_input(
                    "Description",
                    value=selected_transaction["description"],
                    key=f"edit_description_{selected_id}",
                )
                edit_amount = st.number_input(
                    "Amount",
                    min_value=0.0,
                    step=0.01,
                    value=float(selected_transaction["amount"]),
                    key=f"edit_amount_{selected_id}",
                )
                edit_type = st.selectbox(
                    "Type",
                    ["Income", "Expense"],
                    index=["Income", "Expense"].index(selected_transaction["t_type"]),
                    key=f"edit_type_{selected_id}",
                )
                edit_category = st.selectbox(
                    "Category",
                    category_options,
                    index=category_options.index(selected_transaction["category"]),
                    key=f"edit_category_{selected_id}",
                )
                edit_notes = st.text_area(
                    "Notes (Optional)",
                    value="" if pd.isna(selected_transaction["notes"]) else selected_transaction["notes"],
                    key=f"edit_notes_{selected_id}",
                )
                edit_submitted = st.form_submit_button("Save changes")

                if edit_submitted:
                    conn = sqlite3.connect("finance.db")
                    conn.execute(
                        """UPDATE transactions
                           SET date = ?, description = ?, amount = ?, t_type = ?, category = ?, notes = ?
                           WHERE id = ?""",
                        (
                            edit_date.strftime("%Y-%m-%d"),
                            edit_description,
                            edit_amount,
                            edit_type,
                            edit_category,
                            edit_notes,
                            selected_id,
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Transaction updated.")
                    st.rerun()
        else:
            confirmed = st.checkbox(
                "I understand this permanently deletes the transaction",
                key=f"confirm_delete_{selected_id}",
            )
            if st.button("Delete transaction", key=f"delete_transaction_{selected_id}"):
                if confirmed:
                    conn = sqlite3.connect("finance.db")
                    conn.execute("DELETE FROM transactions WHERE id = ?", (selected_id,))
                    conn.commit()
                    conn.close()
                    st.success("Transaction removed.")
                    st.rerun()
                else:
                    st.error("Confirm deletion before removing the transaction.")
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
