import streamlit as st
import pandas as pd
import pdfplumber
import io
import os
import re

st.set_page_config(page_title="Atlassian Expense Allocation Tool", layout="centered")
PERSIST_FILE = "bu_mapping_current.xlsx"

page = st.sidebar.radio("Go to page:", ["Expense Allocation", "BU Mapping Management"])

def extract_invoice_items(text):
    items = [
        ("Confluence", 30),
        ("draw.io Diagrams |", 30),
        ("Flowchart & PlantUML", 30),
        ("Jira Service", 14),
        ("Jira, Standard", 52),
        ("draw.io Diagrams for", 52),
    ]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    found = []
    for name, default_count in items:
        for line in lines:
            if name.lower() in line.lower():
                match = re.search(r"USD\s*([\d,]+\.\d{2})", line)
                amount = None
                if match:
                    amount = float(match.group(1).replace(',', ''))
                found.append({
                    "desc": name,
                    "amount": amount,
                    "count": default_count,
                })
                break
        else:
            found.append({"desc": name, "amount": None, "count": default_count})
    return found

def rounding_safe_split(total, n):
    per_user = total / n
    shares = [round(per_user, 2) for _ in range(n)]
    diff = round(total - sum(shares), 2)
    shares[-1] += diff
    return shares

# ===== BU Mapping Management =====
if page == "BU Mapping Management":
    st.title("BU Mapping Management")
    st.write("Add, edit, or delete Business Unit mapping here. All changes are saved instantly.")

    columns = ['User name', 'Email', 'Cost To']
    # Load existing or create new
    if os.path.exists(PERSIST_FILE):
        bu_df = pd.read_excel(PERSIST_FILE)
        for col in columns:
            if col not in bu_df.columns:
                bu_df[col] = ""
        bu_df = bu_df[columns]
    else:
        bu_df = pd.DataFrame(columns=columns)

    # Upload mapping
    bu_upload = st.file_uploader("Upload BU Mapping Excel (.xlsx) to replace current mapping", type=["xlsx"])
    if bu_upload:
        upload_df = pd.read_excel(bu_upload)
        for col in columns:
            if col not in upload_df.columns:
                upload_df[col] = ""
        bu_df = upload_df[columns]
        bu_df.to_excel(PERSIST_FILE, index=False)
        st.success("BU Mapping replaced and saved!")

    # Editable table (Streamlit 1.22+)
    edited_df = st.data_editor(
        bu_df,
        num_rows="dynamic",
        use_container_width=True,
        key="bu_edit"
    )

    # Add new blank row button
    if st.button("Add New Row"):
        edited_df = pd.concat([edited_df, pd.DataFrame([{"User name": "", "Email": "", "Cost To": ""}])], ignore_index=True)

    # Delete rows (checkbox selection)
    to_delete = st.multiselect("Select row(s) to delete", options=edited_df.index, format_func=lambda x: f"{edited_df.loc[x, 'User name']} ({edited_df.loc[x, 'Email']})")
    if st.button("Delete Selected Row(s)") and to_delete:
        edited_df = edited_df.drop(index=to_delete).reset_index(drop=True)
        st.success("Selected row(s) deleted.")

    # Save mapping (on every edit)
    edited_df.to_excel(PERSIST_FILE, index=False)

    # Download current mapping
    with io.BytesIO() as buf:
        edited_df.to_excel(buf, index=False)
        st.download_button("Download BU Mapping (Excel)", data=buf.getvalue(), file_name="BU-mapping.xlsx")

# ===== Expense Allocation =====
elif page == "Expense Allocation":
    st.title("Atlassian Expense Allocation")
    st.markdown("""
    1. **Upload Invoice PDF and Users CSV**
    2. The app will auto-check your BU mapping. If new users are found, they are auto-added with Cost To = "Unknown".
    3. Download your allocation Excel file.
    """)
    st.divider()
    pdf_file = st.file_uploader("Upload Invoice PDF", type=["pdf"], key="pdf_file")
    csv_file = st.file_uploader("Upload Users CSV (export-users.csv)", type=["csv"], key="csv_file")

    if pdf_file and csv_file:
        # -- Parse Invoice --
        with pdfplumber.open(pdf_file) as pdf:
            text = ''
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        st.text_area("PDF Text Preview", text, height=300)

        product_items = extract_invoice_items(text)
        missing = [i for i in product_items if i['amount'] is None]
        # If not all items found, allow manual input
        if missing:
            st.warning("Could not auto-extract all invoice item amounts. Please enter missing values below.")
            for i in range(len(product_items)):
                if product_items[i]['amount'] is None:
                    manual = st.number_input(f"Enter amount for: {product_items[i]['desc']}", min_value=0.0, format="%.2f", key=f"manual_{i}")
                    product_items[i]['amount'] = manual
            if any(i['amount'] is None or i['amount']==0 for i in product_items):
                st.stop()

        # -- Use real product names for output columns
        product_names = [p['desc'] for p in product_items]

        # -- Load Users --
        users_df = pd.read_csv(csv_file)
        users_df['email'] = users_df['email'].str.lower()
        # Try to use most likely name column or fallback to blank
        if 'User name' not in users_df.columns:
            users_df['User name'] = users_df.get('username', users_df.get('name', ''))

        # -- Load Current BU Mapping --
        if os.path.exists(PERSIST_FILE):
            bu_df = pd.read_excel(PERSIST_FILE)
            bu_df['Email'] = bu_df['Email'].str.lower()
        else:
            bu_df = pd.DataFrame(columns=['User name', 'Email', 'Cost To'])

        # -- Find unmapped users and auto-add them --
        merged = pd.merge(users_df, bu_df, left_on='email', right_on='Email', how='left')
        unmapped = merged[merged['Cost To'].isna()]
        new_bu_df = bu_df.copy()

        if len(unmapped) > 0:
            # Auto-add with default Cost To
            default_cost_to = "Unknown"  # Change as desired (e.g. "IT")
            auto_added = []
            for idx, row in unmapped.iterrows():
                new_entry = {
                    "User name": row.get("User name", ""),
                    "Email": row["email"],
                    "Cost To": default_cost_to,
                }
                auto_added.append(new_entry)
            # Append new users to mapping and save
            new_bu_df = pd.concat([new_bu_df, pd.DataFrame(auto_added)], ignore_index=True)
            new_bu_df = new_bu_df.drop_duplicates(subset=["Email"], keep="last")
            new_bu_df.to_excel(PERSIST_FILE, index=False)
            st.info(f"Auto-added {len(auto_added)} new user(s) to BU mapping with Cost To = '{default_cost_to}'. You can edit these on the BU Mapping Management page.")

            # Re-merge with updated mapping for allocation
            merged = pd.merge(users_df, new_bu_df, left_on='email', right_on='Email', how='left')

        # Now all users are mapped
        merged['Cost To'] = merged['Cost To'].fillna("")
        total_users = len(merged)
        it_users = merged[merged['Cost To'].str.upper() == "IT"]
        num_it_users = len(it_users)

        # Rounding-safe allocations for all users for each item
        alloc_shares = {}
        for idx in [0, 1, 2, 4, 5]:
            alloc_shares[product_names[idx]] = rounding_safe_split(product_items[idx]['amount'], total_users)

        # For Jira Service (IT only)
        inv4_shares = [0.00] * total_users
        if num_it_users > 0:
            shares_for_it = rounding_safe_split(product_items[3]['amount'], num_it_users)
            it_idx = merged["Cost To"].str.upper() == "IT"
            share_iter = iter(shares_for_it)
            for i in range(total_users):
                if it_idx.iloc[i]:
                    inv4_shares[i] = next(share_iter)

        # Output DataFrame with real product names
        output_df = pd.DataFrame({
            "User name": merged["User name_x"] if "User name_x" in merged.columns else merged["User name"],
            "Email": merged["email"],
            "Cost To": merged["Cost To"],
            product_names[0]: alloc_shares[product_names[0]],
            product_names[1]: alloc_shares[product_names[1]],
            product_names[2]: alloc_shares[product_names[2]],
            product_names[3]: inv4_shares,
            product_names[4]: alloc_shares[product_names[4]],
            product_names[5]: alloc_shares[product_names[5]],
        })

        st.success("Allocation calculated! Preview below.")
        st.dataframe(output_df.head(10), hide_index=True, use_container_width=True)

        # ----- SUMMARY BY COST TO -----
        summary_cols = product_names
        summary = output_df.groupby("Cost To")[summary_cols].sum().reset_index()
        summary["Grand Total"] = summary[summary_cols].sum(axis=1)

        st.subheader("Expense Allocation Summary by Cost To (Business Unit)")
        st.dataframe(summary, hide_index=True, use_container_width=True)

        # Download summary as Excel
        with io.BytesIO() as buf2:
            summary.to_excel(buf2, index=False)
            st.download_button("Download Summary by Cost To (Excel)", data=buf2.getvalue(), file_name="Expense_Allocation_Summary.xlsx")

        # ----- DOWNLOAD ALLOCATION -----
        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine="openpyxl") as writer:
            output_df.to_excel(writer, index=False, sheet_name="Expense Allocation")
        towrite.seek(0)
        st.download_button(
            label="Download Expense Allocation Excel",
            data=towrite,
            file_name="Expense_Allocation_Output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Please upload both Invoice PDF and Users CSV to proceed.")