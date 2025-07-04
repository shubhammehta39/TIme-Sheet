import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import time
import io
import plotly.io as pio

# --- CONFIGURATION ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SHEET_URLS = {
    # "TF_003": "https://docs.google.com/spreadsheets/d/1qRiex4L1bpXu-4q1VwgxsiqB6f5KR0qZUmJrAXZI0II",
    # "TF_004": "https://docs.google.com/spreadsheets/d/1xEXlpnvu8Xxy-Pr7VtIdWnLYBqDjO0CWgq6Y4UPl3wA",
    # "TF_005": "https://docs.google.com/spreadsheets/d/14VLlqc3GRYjkovBd4xc4ypTQOiiXYvf9c3OCOqw9LNI",
    "TDFS44": "https://docs.google.com/spreadsheets/d/1p3583-UC0odlroqFyfdYqKF5AlO2NbA7EY9_95yNloE",#aditi
    "TDFS46": "https://docs.google.com/spreadsheets/d/1fwj1MWZGqbcDATuUfoeuRhEJ7tmqKlQ9v29fRy1IeVA",#chirag
    "TDFS47": "https://docs.google.com/spreadsheets/d/1NKLyLNN1AEKlVaS1ejfAO6MmRrdqDt1qjhnuuGL5xAw" #harsh
    
}

CREDENTIALS_PATH = "credentials.json"
MASTER_SHEET_ID = "1keBMyJdHJIeHrCsM70_xJlq4lugoHJibTelqKP_S3hs"
EMPLOYEE_SHEET_NAME = "Employee Detail"

# --- AUTHENTICATION ---
#creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
service_account_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=creds)
sheets_service = build("sheets", "v4", credentials=creds)

st.set_page_config(page_title="📊 Project Tracker Dashboard", layout="wide")
st.title("📊 Project Work Tracker")

# --- UTILITY FUNCTIONS ---

def get_designation_effort_by_project(df_all, emp_designation_map, selected_project):
    df_proj = df_all[df_all["Project"] == selected_project].copy()
    df_proj["Designation"] = df_proj["Employee ID"].map(emp_designation_map).fillna("Unknown")
    designation_summary = df_proj.groupby("Designation")["Hours"].sum().reset_index()
    designation_summary.rename(columns={"Hours": "Total Hours"}, inplace=True)
    return designation_summary

def get_designation_map():
    df = load_sheet_data(MASTER_SHEET_ID, EMPLOYEE_SHEET_NAME)
    df.columns = df.columns.str.strip()
    if "Employee ID" in df.columns and "Designation" in df.columns:
        return dict(zip(df["Employee ID"].astype(str).str.strip(), df["Designation"].astype(str).str.strip()))
    return {}


def analyze_all_months():
    all_data = []
    # emp_map = get_employee_map()
    emp_map, emp_level_map = get_employee_map()
    emp_designation_map = get_designation_map()



    for month in all_months:
        for emp_id, url in SHEET_URLS.items():
            emp_name = emp_map.get(emp_id, "Unknown")
            file_id = extract_file_id(url)
            df = load_sheet_data(file_id, month)

            if df.empty:
                continue

            project_col = df.columns[0]
            date_cols = df.columns[1:]

            for _, row in df.iterrows():
                project = str(row[project_col]).strip()
                if project.lower() in ["", "nan"]:
                    continue

                for date in date_cols:
                    val = row[date]
                    if pd.notna(val) and str(val).strip() not in ["", "-"]:
                        try:
                            all_data.append({
                                "Employee ID": emp_id,
                                "Employee Name": emp_name,
                                "Project": project,
                                "Month": month,
                                "Date": date,
                                "Hours": float(val)
                            })
                        except:
                            continue

    return pd.DataFrame(all_data)
def get_expected_effort_map():
    df_effort = load_sheet_data(MASTER_SHEET_ID, "Project Master")
    df_effort.columns = df_effort.columns.astype(str).str.strip()

    if "ProjectList" not in df_effort.columns or "Project Effort Plan" not in df_effort.columns:
        return {}

    return dict(zip(
        df_effort["ProjectList"].astype(str).str.strip(),
        pd.to_numeric(df_effort["Project Effort Plan"], errors="coerce").fillna(0)
    ))

def extract_file_id(url):
    return url.split("/d/")[1].split("/")[0]

def get_sheet_names(file_id):
    metadata = sheets_service.spreadsheets().get(spreadsheetId=file_id).execute()
    return [sheet["properties"]["title"] for sheet in metadata["sheets"]]

def sort_months_chronologically(months):
    month_dates = []
    for month in months:
        try:
            if '-' in month:
                month_date = datetime.strptime(month, "%B-%y")
            else:
                month_date = datetime.strptime(month, "%B-%Y")
            month_dates.append((month_date, month))
        except:
            try:
                month_date = datetime.strptime(month.upper(), "%b-%y")
                month_dates.append((month_date, month))
            except:
                month_dates.append((datetime.max, month))
    month_dates.sort(key=lambda x: x[0])
    return [month for _, month in month_dates]

# --- LOAD EMPLOYEE MASTER MAP ---
def load_sheet_data(file_id, sheet_name):
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=file_id,
        range=sheet_name
    ).execute()
    values = result.get('values', [])
    if not values:
        return pd.DataFrame()
    df = pd.DataFrame(values)
    df.columns = df.iloc[0]
    df = df[1:]
    df.reset_index(drop=True, inplace=True)
    df.dropna(how="all", inplace=True)
    return df

# def get_employee_map():
#     df_map = load_sheet_data(MASTER_SHEET_ID, EMPLOYEE_SHEET_NAME)
#     if df_map.empty or "Employee ID" not in df_map.columns or "Employee Name" not in df_map.columns:
#         return {}
#     df_map.columns = df_map.columns.astype(str).str.strip().str.replace('\n', ' ').str.replace('\r', ' ')
#     emp_map = dict(zip(df_map["Employee ID"].astype(str).str.strip(), df_map["Employee Name"].astype(str).str.strip()))
#     return emp_map
def get_employee_map():
    df_map = load_sheet_data(MASTER_SHEET_ID, EMPLOYEE_SHEET_NAME)
    if df_map.empty or not {"Employee ID", "Employee Name", "Designation"}.issubset(df_map.columns):
        return {}, {}
    df_map.columns = df_map.columns.astype(str).str.strip().str.replace('\n', ' ').str.replace('\r', ' ')
    emp_name_map = dict(zip(df_map["Employee ID"].astype(str).str.strip(), df_map["Employee Name"].astype(str).str.strip()))
    emp_designation_map = dict(zip(df_map["Employee ID"].astype(str).str.strip(), df_map["Designation"].astype(str).str.strip()))
    return emp_name_map, emp_designation_map


# --- ANALYZE GOOGLE SHEETS ---
def analyze_sheets(selected_month):
    employee_data = []
   # emp_map = get_employee_map()
    emp_map, designation_map = get_employee_map()


    for employee_id, url in SHEET_URLS.items():
        employee_name = emp_map.get(employee_id, "Unknown")
        file_id = extract_file_id(url)
        df = load_sheet_data(file_id, selected_month)
        if df.empty: continue

        project_col = df.columns[0]
        date_cols = df.columns[1:]
        for _, row in df.iterrows():
            project = str(row[project_col]).strip()
            if project.lower() in ["", "nan"]: continue

            for date in date_cols:
                val = row[date]
                if pd.notna(val) and str(val).strip() not in ["", "-"]:
                    try:
                        employee_data.append({
                            "Employee ID": employee_id,
                            "Employee Name": employee_name,
                            "Project": project,
                            "Date": date,
                            "Hours": float(val),
                            "Designation": designation_map.get(employee_id, "Unknown")
                        })
                    except ValueError:
                        continue

    return pd.DataFrame(employee_data)

# --- SUMMARY TABLES ---
def total_summary_table(df):
    df = df[df["Project"].astype(str).str.strip().ne("")]
    # df["Employee"] = df["Employee Name"] + " (" + df["Employee ID"] + ")"
    df["Employee Composite"] = df["Employee Name"] + " (" + df["Employee ID"] + ")"
    pivot = df.pivot_table(index='Project', columns='Employee Composite', values='Hours', aggfunc='sum', fill_value=0)
    pivot = df.pivot_table(index='Project', columns='Employee', values='Hours', aggfunc='sum', fill_value=0)
    pivot = pivot[~(pivot.index.to_series().str.strip() == "")]
    pivot['Total'] = pivot.sum(axis=1)
    pivot.loc['Total'] = pivot.sum(numeric_only=True)
    return pivot
def project_wise_employee_table(df, selected_project):
    filtered_df = df[df["Project"] == selected_project]
    grouped = (
        filtered_df.groupby("Employee")["Hours"]
        .sum()
        .reset_index()
        .sort_values("Hours", ascending=False)
    )
    grouped = grouped[grouped["Hours"] > 0]
    return grouped.set_index("Employee")


def compare_months(current_df, previous_df, current_month, previous_month):
    current_df["Employee"] = current_df["Employee Name"] + " (" + current_df["Employee ID"] + ")"
    previous_df["Employee"] = previous_df["Employee Name"] + " (" + previous_df["Employee ID"] + ")"
    current_total = current_df.groupby("Employee")["Hours"].sum()
    previous_total = previous_df.groupby("Employee")["Hours"].sum()

    all_employees = set(current_total.index.tolist() + previous_total.index.tolist())
    compare_data = []
    for employee in all_employees:
        prev_hours = previous_total.get(employee, 0)
        curr_hours = current_total.get(employee, 0)
        compare_data.append({
            "Employee": employee,
            f"Previous Month ({previous_month})": prev_hours,
            f"Current Month ({current_month})": curr_hours,
            "Change": curr_hours - prev_hours,
            "Total Time": prev_hours + curr_hours
        })
    return pd.DataFrame(compare_data).set_index("Employee").sort_index()

def compare_projects(current_df, previous_df, current_month, previous_month):
    current_total = current_df.groupby("Project")["Hours"].sum()
    previous_total = previous_df.groupby("Project")["Hours"].sum()
    all_projects = set(current_total.index.tolist() + previous_total.index.tolist())
    compare_data = []
    for project in all_projects:
        prev_hours = previous_total.get(project, 0)
        curr_hours = current_total.get(project, 0)
        compare_data.append({
            "Project": project,
            f"Previous Month ({previous_month})": prev_hours,
            f"Current Month ({current_month})": curr_hours,
            "Change": curr_hours - prev_hours,
            "Total Time": prev_hours + curr_hours
        })
    return pd.DataFrame(compare_data).set_index("Project").sort_index()

# --- EXPORT TO EXCEL ---
def generate_excel_download(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name="Summary")
        writer.close()
    return output.getvalue()

# --- TABLE RENDERING ---
def display_large_table(df, caption):
    st.markdown(f"#### {caption}")
    st.dataframe(df.style.format("{:.1f}"), use_container_width=True)


# --- MAIN LOGIC ---
# --- GET ALL MONTHS ---
all_months_raw = []
for url in SHEET_URLS.values():
    file_id = extract_file_id(url)
    try:
        months = get_sheet_names(file_id)
        all_months_raw.extend(months)
    except Exception as e:
        st.error(f"Error getting sheet names: {e}")

all_months = sort_months_chronologically(list(set(all_months_raw)))
month = st.selectbox("Select Month", all_months)

if month:
    df_summary = analyze_sheets(month)
    # st.subheader("🔍 Effort by Designation Level")
    designation_summary = df_summary.groupby("Designation")["Hours"].sum().reset_index()
    fig_designation = px.bar(designation_summary, x="Designation", y="Hours", color="Designation", text="Hours")
    fig_designation.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    # st.plotly_chart(fig_designation, use_container_width=True)


    if df_summary.empty:
        st.warning("No data found for this month")
    else:
        df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
        if "Employee" not in df_summary.columns:
            # df_summary['Employee'] = df_summary['Employee Name'] + " (" + df_summary['Employee ID'] + ")"
            df_summary['Employee'] = df_summary['Employee Name'] + " (" + df_summary['Designation'] + ", " + df_summary['Employee ID'] + ")"


        # df_summary['Employee'] = df_summary['Employee Name'] + " (" + df_summary['Employee ID'] + ")"

        # --- MULTI PROJECT SEARCH ---
        st.markdown("### 🔎 Filter Projects")
        all_proj = sorted(df_summary['Project'].unique())
        selected_projects = st.multiselect("Select project(s) to analyze", all_proj)

        if selected_projects:
            proj_df = df_summary[df_summary['Project'].isin(selected_projects)]
            # proj_grouped = proj_df.groupby(['Project', 'Employee'],as_index=False)['Hours'].sum().reset_index()
            proj_grouped = proj_df.groupby(['Project', 'Employee', 'Designation'], as_index=False)['Hours'].sum()

            fig_proj = px.bar(proj_grouped, x='Hours', y='Project', color='Employee', text='Hours', barmode='group')
            # pio.write_image(fig_proj, "example_chart.png", width=800, height=500)
            # save_chart_as_image(fig_proj, "project_chart_1.png")   #1
            fig_proj.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            unique_projects = proj_grouped['Project'].nunique()
            fig_proj.update_layout(height=max(500, (unique_projects)*80), plot_bgcolor="#131313", paper_bgcolor="#0E1117", font=dict(color="white"))
            st.plotly_chart(fig_proj, use_container_width=True)

        # --- SUMMARY TABLE ---
        df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
        # Filter out project names that are purely numeric or too short
        df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
        df_summary = df_summary[~df_summary['Project'].str.match(r'^\d+$')]  # remove numeric-only names
        df_summary = df_summary[df_summary['Project'].str.len() > 2]         # remove short junk names like '3', '5'

        proj_total = df_summary.groupby('Project')['Hours'].sum().reset_index()
        proj_total = proj_total[proj_total['Project'] != '']
        proj_total.rename(columns={'Hours': 'Total Days'}, inplace=True)

        # Plot with legend on the right
        fig = px.bar(
            proj_total,
            x='Total Days',
            y='Project',
            color='Project',
            orientation='h',
            height=500,
            title='Total Days Spent Per Project'
        )
        # pio.write_image(fig, "example_chart_2.png", width=800, height=500)

        fig.update_layout(
            showlegend=True,
            legend_title_text="Project",
            plot_bgcolor="#131313",
            paper_bgcolor="#0E1117",
            bargap=0.3,
            font=dict(color="white"),
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02,
                borderwidth=0,
                bgcolor="rgba(0,0,0,0)",
            )
        )

        # st.plotly_chart(fig, use_container_width=True)
        # save_chart_as_image(fig, "project_chart_2.png")
        pivot = total_summary_table(df_summary)
        display_large_table(pivot, f"📊 Employee Project Summary for {month}")

        # --- EXPORT OPTION ---
        # st.download_button("🧾 Download Summary as Excel", data=generate_excel_download(pivot),
        #                    file_name=f"Summary_{month}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # --- INTERACTIVE EMPLOYEE TABLE BY PROJECT ---
        st.markdown("### 📌 View Employees Working on Specific Project")
        unique_projects_list = sorted(df_summary["Project"].unique())
        selected_proj_for_table = st.selectbox("Select a project to see employee contributions", unique_projects_list)

        if selected_proj_for_table:
            proj_emp_table = project_wise_employee_table(df_summary, selected_proj_for_table)
            display_large_table(proj_emp_table, f"💼 Employee Contributions for '{selected_proj_for_table}'")

        # --- EMPLOYEE CHART ---
        # st.subheader("👥 Total Days Per Employee")
        emp_total = df_summary.groupby('Employee')['Hours'].sum().reset_index()
        fig_emp = px.bar(emp_total, x='Hours', y='Employee', orientation='h', color='Employee')
        # save_chart_as_image(fig_emp, "project_chart_3.png")
        # st.plotly_chart(fig_emp, use_container_width=True)

        # --- PROJECT STACKED ---
        # st.subheader("📊 Project-wise Contribution by Employees")
        proj_emp_df = df_summary.groupby(['Project', 'Employee'])['Hours'].sum().reset_index()
        fig = px.bar(proj_emp_df, x="Project", y="Hours", color="Employee", text="Hours", barmode="stack")
        # save_chart_as_image(proj_emp_df, "project_chart.png")
        # st.plotly_chart(fig, use_container_width=True)

        # --- MONTH ON MONTH COMPARISON ---
        st.subheader(f"📈 Month-on-Month Comparison for {month}")
        curr_index = all_months.index(month)
        if curr_index == 0:
            st.info(f"This is the first month ({month}) in the data. No previous month available for comparison.")
            emp_df = df_summary.groupby("Employee")["Hours"].sum().reset_index()
            proj_df = df_summary.groupby("Project")["Hours"].sum().reset_index()
            # st.write("🔍 Sample Data Extracted:")
            # st.dataframe(df_summary.head(20))

            display_large_table(emp_df.set_index("Employee"), f"Employee Summary for {month}")
            display_large_table(proj_df.set_index("Project"), f"Project Summary for {month}")
        else:
            prev_month = all_months[curr_index - 1]
            df_prev = analyze_sheets(prev_month)
            compare_emp_df = compare_months(df_summary, df_prev, current_month=month, previous_month=prev_month)
            compare_proj_df = compare_projects(df_summary, df_prev, current_month=month, previous_month=prev_month)
            display_large_table(compare_emp_df, f"📈 Month-on-Month by Employee ({prev_month} vs {month})")
            display_large_table(compare_proj_df, f"📈 Month-on-Month by Project ({prev_month} vs {month})")
        
        
        st.subheader("🕓 Total Effort Across All Months")

        df_all_time = analyze_all_months()
        if df_all_time.empty:
            st.info("No data found across months.")
        else:
            df_all_time['Project'] = df_all_time['Project'].astype(str).str.strip()
            proj_overall = df_all_time.groupby('Project')['Hours'].sum().reset_index()
            proj_overall = proj_overall[proj_overall['Project'].str.len() > 2]
            proj_overall.rename(columns={'Hours': 'Actual Days Spent'}, inplace=True)

            # Add expected effort
            expected_map = get_expected_effort_map()
            proj_overall['Expected Days'] = proj_overall['Project'].map(expected_map).fillna(0)

            # Calculate variance
            proj_overall['Variance'] = proj_overall['Actual Days Spent'] - proj_overall['Expected Days']

            # Sort by variance or effort
            proj_overall = proj_overall.sort_values(by='Variance', ascending=False)


            # Sort descending
            proj_overall = proj_overall.sort_values(by='Actual Days Spent', ascending=False)

                # st.dataframe(proj_overall)

            # Optional: Add a horizontal bar chart
            fig_all = px.bar(
                proj_overall,
                x="Actual Days Spent",
                y="Project",
                orientation="h",
                color="Project",
                title="Total Days Spent per Project (All Months)"
            )
            fig_all.update_layout(
                plot_bgcolor="#131313",
                paper_bgcolor="#0E1117",
                font=dict(color="white"),
                showlegend=False
            )
            st.plotly_chart(fig_all, use_container_width=True)
            st.dataframe(
            proj_overall.style
            .format({"Expected Days": "{:.1f}", "Actual Days Spent": "{:.1f}", "Variance": "{:+.1f}"})
            .background_gradient(subset=["Variance"], cmap="RdYlGn_r")
            )
            emp_designation_map = get_designation_map()

            st.markdown("### 🧑‍💼 Designation-wise Effort per Project")

            if not df_all_time.empty:
                all_projects = sorted(df_all_time["Project"].dropna().unique())
                selected_proj = st.selectbox("Select Project", all_projects, key="designation_project")

                if selected_proj:
                    desg_table = get_designation_effort_by_project(df_all_time, emp_designation_map, selected_proj)
                    st.dataframe(desg_table.set_index("Designation"), use_container_width=True)
            else:
                st.info("No all-time project data found.")



                    
