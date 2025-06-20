# -*- coding: utf-8 -*-
"""streamlit.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/17T4yBC8v1Pmu7sUOkBfnHflAXLpTYMR7
"""
import pandas as pd
import streamlit as st
from io import BytesIO

# Function to filter data
def filter_data(df):
    df = df[df['ClaimStatus'] == 'R']
    return df

# Function to handle duplicates
def keep_last_duplicate(df):
    duplicate_claims = df[df.duplicated(subset='ClaimNo', keep=False)]
    if not duplicate_claims.empty:
        st.write("Duplicated ClaimNo values:")
        st.write(duplicate_claims[['ClaimNo']].drop_duplicates())
    df = df.drop_duplicates(subset='ClaimNo', keep='last')
    return df


# Main processing function
def move_to_template(df):
    # Step 1: Filter the data
    new_df = filter_data(df)

    # Step 2: Handle duplicates
    new_df = keep_last_duplicate(new_df)

    # Step 3: Convert date columns to datetime
    date_columns = ["TreatmentStart", "TreatmentFinish", "Date"]
    for col in date_columns:
        new_df[col] = pd.to_datetime(new_df[col], errors='coerce')
        if new_df[col].isnull().any():
            st.warning(f"Invalid date values detected in column '{col}'. Coerced to NaT.")

    # Step 4: Standardize (uppercase etc)
    upper_columns = ["RoomOption", "TreatmentPlace", "PrimaryDiagnosis"]
    for col in upper_columns:
        new_df[col] = new_df[col].str.upper()
    if "RoomOption" in new_df.columns:
        new_df["RoomOption"] = new_df["RoomOption"].astype(str).str.strip().str.upper()
        new_df.loc[new_df["RoomOption"] == "ON PLAN", "RoomOption"] = "ONPLAN"
    new_df["RoomOption"] = new_df["RoomOption"].replace(
        to_replace=["NAN", "NONE", "NaN", "nan", ""], value=""
    )

    # Step 5: Transform to the new template
    df_transformed = pd.DataFrame({
        "No": range(1, len(new_df) + 1),
        "Policy No": new_df["PolicyNo"],
        "Client Name": new_df["ClientName"],
        "Note No": new_df["NoteNo"],
        "Claim No": new_df["ClaimNo"],
        "Member No": new_df["MemberNo"],
        "Emp ID": new_df["EmpID"],
        "Emp Name": new_df["EmpName"],
        "Patient Name": new_df["PatientName"],
        "Membership": new_df["Membership"],
        "Product Type": new_df["ProductType"],
        "Claim Type": new_df["ClaimType"],
        "Room Option": new_df["RoomOption"],
        "Area": new_df["Area"],
        "Plan": new_df["PPlan"],
        "Diagnosis": new_df["PrimaryDiagnosis"],
        "Treatment Place": new_df["TreatmentPlace"],
        "Treatment Start": new_df["TreatmentStart"],
        "Treatment Finish": new_df["TreatmentFinish"],
        "Settled Date": new_df["Date"],
        "Year": new_df["Date"].dt.year,
        "Month": new_df["Date"].dt.month,
        "Length of Stay": new_df["LOS"],
        "Sum of Billed": new_df["Billed"],
        "Sum of Accepted": new_df["Accepted"],
        "Sum of Excess Coy": new_df["ExcessCoy"],
        "Sum of Excess Emp": new_df["ExcessEmp"],
        "Sum of Excess Total": new_df["ExcessTotal"],
        "Sum of Unpaid": new_df["Unpaid"]
    })
    return df_transformed

def move_to_template_benefit(df):
    # Step 1: Filter the data
    df = df.rename(columns={
    'Status_Claim': 'ClaimStatus',
    })
    new_df = filter_data(df)

    # Step 2: Convert date columns to datetime
    date_columns = ["TreatmentStart", "TreatmentFinish", "PaymentDate"]
    for col in date_columns:
        new_df[col] = pd.to_datetime(new_df[col], errors='coerce')
        if new_df[col].isnull().any():
            st.warning(f"Invalid date values detected in column '{col}'. Coerced to NaT.")

    # Step 3: Standardize (uppercase etc)
    upper_columns = ["RoomOption", "TreatmentPlace", "Diagnosis"]
    for col in upper_columns:
        new_df[col] = new_df[col].str.upper()
    if "RoomOption" in new_df.columns:
        new_df["RoomOption"] = new_df["RoomOption"].astype(str).str.strip().str.upper()
        new_df.loc[new_df["RoomOption"] == "ON PLAN", "RoomOption"] = "ONPLAN"
    new_df["RoomOption"] = new_df["RoomOption"].replace(
        to_replace=["NAN", "NONE", "NaN", "nan", ""], value=""
    )

    # Step 4: Transform to the new template
    df_transformed = new_df.drop(columns=['StatusClaim', 'BAmount'])
    return df_transformed

def move_to_template_summary(df_sc, summary):
    # 1. Ambil policy no unik dari df_sc
    unique_policies = df_sc['PolicyNo'].astype(str).str.strip().unique()

    # 2. Filter summary
    filtered_summary = summary[
        summary['PolicyNo'].astype(str).str.strip().isin(unique_policies)
        ].copy()
    # 3. Hitung agregasi di df_sc
    agg_sc = (
        df_sc
        .groupby('PolicyNo', as_index=False)
        .agg(
            Billed       = ('Sum of Billed',      'sum'),
            Unpaid       = ('Sum of Unpaid',      'sum'),
            ExcessTotal  = ('Sum of Excess Total', 'sum'),
            ExcessCoy    = ('Sum of Excess Coy',   'sum'),
            ExcessEmp    = ('Sum of Excess Emp',   'sum'),
            Claim        = ('Sum of Accepted',    'sum'),  # rename Accepted → Claim
        )
    )
    # 4. Merge dengan filtered_summary dan pilih kolom
    result = (
        filtered_summary
        .merge(agg_sc, on='PolicyNo', how='left')
        .loc[:, [
            'Company',
            'Net Premi',
            'Billed',
            'Unpaid',
            'ExcessTotal',
            'ExcessCoy',
            'ExcessEmp',
            'Claim',
        ]]
    )
    return result


# Save the processed data to Excel and return as BytesIO
def save_to_excel(df, filename):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write the transformed data
        claim_ratio.to_excel(writer, index=False, sheet_name='Summary')
        df.to_excel(writer, index=False, sheet_name='SC')
        df_benefit.to_excel(writer, index=False, sheet_name='Benefit')
    output.seek(0)
    return output, filename

# Streamlit app
st.title("Claim Data Raw to Template")

# SC File uploader
uploaded_sc_file = st.file_uploader("Upload your SC file", type=["csv"])
uploaded_benefit_file = st.file_uploader("Upload your Benefit file", type=["csv"])
uploaded_cr_file = st.file_uploader("Upload your CR file", type=["xlsx"])

if uploaded_sc_file and uploaded_benefit_file and uploaded_cr_file:
    raw_sc = pd.read_csv(uploaded_sc_file)
    raw_benefit = pd.read_csv(uploaded_benefit_file)
    raw_cr = pd.read_excel(uploaded_cr_file, engine="openpyxl")

    # Process data
    st.write("Processing data...")
    transformed_sc_data = move_to_template(raw_sc)
    transformed_benefit_data = move_to_template(raw_benefit)
    transformed_cr_data = move_to_template(raw_cr)

    # Show a preview of the transformed data
    st.write("SC Data Preview:")
    st.dataframe(transformed_sc_data.head())

    st.write("Benefit Data Preview:")
    st.dataframe(transformed_benefit_data.head())

    st.write("CR Data Preview:")
    st.dataframe(transformed_cr_data.head())

    # Compute summary statistics
    total_claims = len(transformed_sc_data)
    total_billed = int(transformed_sc_data["Sum of Billed"].sum())
    total_accepted = int(transformed_sc_data["Sum of Accepted"].sum())
    total_excess = int(transformed_sc_data["Sum of Excess Total"].sum())
    total_unpaid = int(transformed_sc_data["Sum of Unpaid"].sum())

    st.write("Claim Summary:")
    st.write(f"- Total Claims: {total_claims:,}")
    st.write(f"- Total Billed: {total_billed:,.2f}")
    st.write(f"- Total Accepted: {total_accepted:,.2f}")
    st.write(f"- Total Excess: {total_excess:,.2f}")
    st.write(f"- Total Unpaid: {total_unpaid:,.2f}")

    # User input for filename
    filename = st.text_input("Enter the Excel file name (without extension):", "Transformed_Claim_Data")

    # Download link for the Excel file
    if filename:
        excel_file, final_filename = save_to_excel(transformed_data, filename=filename + ".xlsx")
        st.download_button(
            label="Download Excel File",
            data=excel_file,
            file_name=final_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

