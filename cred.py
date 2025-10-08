import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import time
import io
import plotly.io as pio
import hashlib
from dotenv import load_dotenv
import re
import os


# --- CONFIGURATION ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SHEET_URLS = {
    "TDFS44": "https://docs.google.com/spreadsheets/d/1p3583-UC0odlroqFyfdYqKF5AlO2NbA7EY9_95yNloE",  # Aditi
    "TDFS23": "https://docs.google.com/spreadsheets/d/1Q334Iq2HLaf9BmC3RSaqimOuWiRkGlakvjonZZOSKns",  # Akshat Chauhan
    "TDFS42": "https://docs.google.com/spreadsheets/d/176AtIuehVnQ0wQV4t7Pm9f2KtXAmBoaFy52vEyg7-OM",  # Animesh Paul
    "TDFS46": "https://docs.google.com/spreadsheets/d/1YqRzmGSu6fy6Y-cvE02279lfQS6c2MfzvHXDdLq3tfw",  # Chirag Aich
    "TDFS50": "https://docs.google.com/spreadsheets/d/1tKbsxjC18S-MtGWVGiMPBBeFzX_BTXGx3XXd_WR4-CQ",  # Deepanshu Kathuria
    "TDFS49": "https://docs.google.com/spreadsheets/d/1wWE7JYa24UwefUuHg8LrC2VUiK7hYkpNBAsm2neHczQ",  # Devyani Kundan Pande
    "TDFS54": "https://docs.google.com/spreadsheets/d/1iWsv-T7hHeMkU5bajsk_IJqAcl6mKXbKG_w-6V2LVcY",  # Drishti Wadhwa
    "TDFS47": "https://docs.google.com/spreadsheets/d/1qWH8m79U-bXt3ymPH9pysgR55aCHa6lhPzUN0RoTv7I",  # Harsh Raj
    "TDFS37": "https://docs.google.com/spreadsheets/d/1pjQHNr91-8S-gvaAQ0GF1zOgOh6VWCpzpyLaHQmXyKA",  # Himank Mehta
    "TDFS51": "https://docs.google.com/spreadsheets/d/1cw6CLZr4XZ4Vbg660z9ZRsxcj5d-u61-mpGXrTmLNF0",  # Himanshu Rajendra Dhirayan
    "TDFS55": "https://docs.google.com/spreadsheets/d/13I3xOIRlrJTQ3UBNqG61qeDJ5bPXSM2hmyB-cEexQ1k",  # Jatin Jadhav
    "TDFS52": "https://docs.google.com/spreadsheets/d/1-YxWd84LzE96S__7HvNhP5pFGsZp2RBu1D1WkTcs4ds",  # Jay Shah
    "TDFS35": "https://docs.google.com/spreadsheets/d/1-0wTSvt6hAck52Y_h8dgae5LDRFgmT0Y_100wB-JHAg",  # Lokeshkumar Malke
    "TDFS43": "https://docs.google.com/spreadsheets/d/12-i5cjUkzTE_dB0e-ryiRV4k4jKKh_r2X7AFvaOJKvA",  # Madhur Nema
    "TDFS57": "https://docs.google.com/spreadsheets/d/1OY3BdQXk5cx7FQJhzfjd254JkWP16uZdPSjpnMtnnTg",  # Mihir Vishwakarma
    "TDFS53": "https://docs.google.com/spreadsheets/d/1xU5KpBhGruMDXt8lRqoH_d2mZ9f5JcYfGDZ8MzX1V-I",  # Nandana Anil
    "TDFS08": "https://docs.google.com/spreadsheets/d/1rVyjP_7i1fhVhOYH7-S9hZhBHsyeweYDtvKWuDMaYbA",  # Podila Laxmi Deepak Sai Ram
    "TDFS45": "https://docs.google.com/spreadsheets/d/1H8LxmxF6DRwYMKPwYaX424HFNTh5YHeqpJl3y8L3N5Q",  # Prabhbir Singh
    "TDFS24": "https://docs.google.com/spreadsheets/d/1ywrI6euM77o4smPwoZ3CpNk7PSmPTJWBLr1U01cUNvU",  # Pratap Rajkumar M
    "TDFS17": "https://docs.google.com/spreadsheets/d/1cNNb6pyNcPORtl5hcs28SFVg9mO2on6d1S04Pta_VwM",  # Sakshi Toprani
    "TDFS10": "https://docs.google.com/spreadsheets/d/1zvEnuY3ue5aUJN9C5OIgyhu66zBmeAYddbiFulCcDNw",  # Sameer Singh Jaini
    "TDFS03": "https://docs.google.com/spreadsheets/d/1wq_p4ukSOxMazERqwEMIp7XDYAVeAJRMAyehqXAGfOo",  # Shashank Shekhar
    "TDFS56": "https://docs.google.com/spreadsheets/d/1SIvcD6NNWSA9w3CcBzpSvdaeXuNg0cg8uIZhsrk7LRM",  # Shubham Mehta
    "TDFS11": "https://docs.google.com/spreadsheets/d/1Iv98SeIJ-cYVNb3KlHpcpr_FqzPpqCfNaUOiPghHfk8",  # Sreekant R
    "TDFS30": "https://docs.google.com/spreadsheets/d/1Tfz85-KmyFT1E7p4jqKG_ZjwoQ4LJGGnUdgKxdC33Sc",  # Vanshika Agrawal
    "TDFS38": "https://docs.google.com/spreadsheets/d/1tOMMvAKLtix7zFbFqTBXezYx7Nun-RDhQ-d5LkvHk5I",  # Varun S Prakash
    "TDFS07": "https://docs.google.com/spreadsheets/d/1fE2GCJaFcATwh24ROA0qGITRoVRLLCV5edDim0DtSyU",  # Vikrant Kulkarni
    "TDFS48": "https://docs.google.com/spreadsheets/d/1TMQ-x2hviLIqsq5NbavkZ-k62-ns7GepFYSJw6R8cvw",  # Zishan Ali
    "ITDFS015": "https://docs.google.com/spreadsheets/d/16iWTfJ3Novpsgchvh8tH90WN2tiYm13eveoD9nB0zY0",  # Arun Ganapathy
    "ITDFS014": "https://docs.google.com/spreadsheets/d/1bOl-JvLfd3B5l5aMxRg5O2LZSXeVsEHHHmiKAYQYc34",  # Vidhi Vyas
    
}


# CREDENTIALS_PATH = "credentials.json"
# MASTER_SHEET_ID = "1keBMyJdHJIeHrCsM70_xJlq4lugoHJibTelqKP_S3hs"
# EMPLOYEE_SHEET_NAME = "Employee Detail"

# --- AUTHENTICATION ---
# Dummy cache key to force reload
# cache_key = st.session_state.get("cache_key", 0)

# --- CONFIGURATION ---


CREDENTIALS_PATH = "credentials.json"
load_dotenv()  # loads .env file into environment variables
MASTER_SHEET_ID = os.getenv("MASTER_ID")

EMPLOYEE_SHEET_NAME = "Employee Detail"

# --- AUTHENTICATION ---
#creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
# service_account_info = st.secrets["gcp_service_account"]
# creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
# drive_service = build("drive", "v3", credentials=creds)
# sheets_service = build("sheets", "v4", credentials=creds)


@st.cache_resource
def get_google_services():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],  # <-- from secrets, not file
        scopes=SCOPES
    )
    drive_service = build("drive", "v3", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)
    return drive_service, sheets_service

drive_service, sheets_service = get_google_services()




st.set_page_config(page_title="TDf Project Tracker Dashboard", layout="wide")
st.title("TDF Project Work Tracker")


# --- CACHED UTILITY FUNCTIONS ---

@st.cache_data(ttl=3600)
def extract_file_id(url):
    try:
        return url.split("/d/")[1].split("/")[0]
    except Exception:
        return None

@st.cache_data(ttl=3600)
def get_sheet_names_cached(file_id: str):
    if not file_id:
        return []
    try:
        metadata = sheets_service.spreadsheets().get(spreadsheetId=file_id).execute()
        return [sheet["properties"]["title"] for sheet in metadata.get("sheets", [])]
    except Exception as e:
        print(f"Error fetching sheet names for {file_id}: {e}")
        return []

@st.cache_data(ttl=3600)
def load_sheet_data_cached(file_id: str, sheet_name: str):
    try:
        time.sleep(1.0)
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
    except Exception as e:
        print(f"Error loading sheet data {sheet_name} from {file_id}: {e}")
        return pd.DataFrame()
    

@st.cache_data(ttl=3600)
def get_employee_map_cached():
    df = load_sheet_data_cached(MASTER_SHEET_ID, EMPLOYEE_SHEET_NAME)
    if df.empty or not {"Employee ID", "Employee Name", "Designation"}.issubset(df.columns):
        return {}, {}
    df.columns = df.columns.astype(str).str.strip().str.replace('\n', ' ').str.replace('\r', ' ')
    emp_name_map = dict(zip(df["Employee ID"].astype(str).str.strip(), df["Employee Name"].astype(str).str.strip()))
    emp_designation_map = dict(zip(df["Employee ID"].astype(str).str.strip(), df["Designation"].astype(str).str.strip()))
    return emp_name_map, emp_designation_map

@st.cache_data(ttl=3600)
def get_expected_effort_map_cached():
    df_effort = load_sheet_data_cached(MASTER_SHEET_ID, "Project Master")
    if df_effort.empty or not {"ProjectList", "Project Effort Plan"}.issubset(df_effort.columns):
        return {}
    df_effort.columns = df_effort.columns.astype(str).str.strip()
    return dict(zip(
        df_effort["ProjectList"].astype(str).str.strip(),
        pd.to_numeric(df_effort["Project Effort Plan"], errors="coerce").fillna(0)
    ))

# --- DATA PROCESSING (no API calls here) ---

def extract_individual_dates(date_string):
    if not date_string or pd.isna(date_string):
        return []
    date_string = str(date_string).strip()
    dates = []
    patterns = [
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{2}-\d{2}-\d{4})',
        r'(\d{1,2}-\d{1,2}-\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
    ]
    for pattern in patterns:
        found_dates = re.findall(pattern, date_string)
        if found_dates:
            dates.extend(found_dates)
            break
    if not dates:
        separators = ['/', '-', '_', ' ', ',']
        for sep in separators:
            if sep in date_string:
                potential_dates = date_string.split(sep)
                for i in range(0, len(potential_dates) - 2, 3):
                    if i + 2 < len(potential_dates):
                        try:
                            month, day, year = potential_dates[i:i + 3]
                            if len(year) == 4 and year.isdigit():
                                dates.append(f"{month}/{day}/{year}")
                        except:
                            continue
                break
    return dates

def parse_sheet_data_with_split_dates(file_id, sheet_name):
    """Parse sheet data and split date columns if needed."""
    df = load_sheet_data_cached(file_id, sheet_name)
    if df.empty:
        return df

    project_col = df.columns[0]
    date_cols = df.columns[1:]
    expanded_data = []

    for _, row in df.iterrows():
        project = str(row[project_col]).strip()
        if project.lower() in ["", "nan", "none"]:
            continue
        for date_col in date_cols:
            date_value = row[date_col]
            if isinstance(date_value, pd.Series):
                date_value = date_value.iloc[0]
            if pd.isna(date_value) or str(date_value).strip() in ["", "-", "0"]:
                continue

# individual_dates = extract_individual_dates(str(date_value))

            
#             if pd.isna(date_value) or str(date_value).strip() in ["", "-", "0"]:
#                 continue
            individual_dates = extract_individual_dates(str(date_value))  ##changes made here col-> value date_col->date_value
            
            if individual_dates:
                try:
                    total_value = float(str(date_value).strip())
                    value_per_date = total_value / len(individual_dates)
                    for individual_date in individual_dates:
                        expanded_data.append({
                            project_col: project,
                            'Date': individual_date,
                            'Hours': value_per_date
                        })
                except (ValueError, TypeError):
                    continue
            else:
                try:
                    hours_value = float(str(date_value).strip())
                    expanded_data.append({
                        project_col: project,
                        'Date': str(date_col),
                        'Hours': hours_value
                    })
                except (ValueError, TypeError):
                    continue
    if expanded_data:
        return pd.DataFrame(expanded_data)
    else:
        return pd.DataFrame()

# def assign_week(date_str):
#     try:
#         if not date_str or pd.isna(date_str) or str(date_str).strip() == "":
#             return "Unknown"
#         date_str = str(date_str).strip()
#         formats = [
#             "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y",
#             "%m-%d-%Y", "%m/%d/%y", "%d/%m/%y",
#         ]
#         for fmt in formats:
#             try:
#                 dt = datetime.strptime(date_str, fmt)
#                 day = dt.day
#                 if day <= 7:
#                     return "Week 1"
#                 elif day <= 14:
#                     return "Week 2"
#                 elif day <= 21:
#                     return "Week 3"
#                 else:
#                     return "Week 4"
#             except ValueError:
#                 continue
#         return "Unknown"
#     except Exception:
#         return "Unknown"

def assign_week(date_str):
    try:
        if not date_str or pd.isna(date_str) or str(date_str).strip() == "":
            return "Unknown"
        date_str = str(date_str).strip()
        # formats = [
        #     "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y",
        #     "%m-%d-%Y", "%m/%d/%y", "%d/%m/%y",
        # ]
        formats = [
                "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y",
                "%m/%d/%y", "%d/%m/%y",
            ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                day = dt.day
                if 1 <= day <= 7:
                    return "Week 1"
                elif 8 <= day <= 14:
                    return "Week 2"
                elif 15 <= day <= 21:
                    return "Week 3"
                elif 22 <= day <= 31:
                    return "Week 4"
                else:
                    return "Unknown"
            except ValueError:
                continue
        return "Unknown"
    except Exception:
        return "Unknown"

def add_week_column(df):
    df = df.copy()
    if "Date" in df.columns:
        df["Week"] = df["Date"].apply(assign_week)
        return df[df["Week"] != "Unknown"]
    return df

# --- DATA ANALYSIS FUNCTIONS (use cached loads) ---

def analyze_sheets(selected_month, all_months, sheet_urls, emp_map, designation_map):
    employee_data = []
    for employee_id, url in sheet_urls.items():
        file_id = extract_file_id(url)
        if not file_id:
            continue
        file_sheets = get_sheet_names_cached(file_id)
        if selected_month not in file_sheets:
            continue
        df = parse_sheet_data_with_split_dates(file_id, selected_month)
        if df.empty:
            continue
        for _, row in df.iterrows():
            project = str(row.iloc[0]).strip()
            date = str(row['Date']).strip()
            hours = row['Hours']
            if project.lower() not in ["", "nan", "none"] and hours > 0:
                employee_data.append({
                    "Employee ID": employee_id,
                    "Employee Name": emp_map.get(employee_id, "Unknown"),
                    "Project": project,
                    "Date": date,
                    "Hours": float(hours),
                    "Designation": designation_map.get(employee_id, "Unknown"),
                    "Month": selected_month
                })
    return pd.DataFrame(employee_data)

def analyze_all_months(all_months, sheet_urls, emp_map, designation_map):
    all_data = []
    for month in all_months:
        for emp_id, url in sheet_urls.items():
            file_id = extract_file_id(url)
            if not file_id:
                continue
            file_sheets = get_sheet_names_cached(file_id)
            if month not in file_sheets:
                continue
            df = parse_sheet_data_with_split_dates(file_id, month)
            if df.empty:
                continue
            for _, row in df.iterrows():
                project = str(row.iloc[0]).strip()
                date = str(row['Date']).strip()
                hours = row['Hours']
                if project.lower() not in ["", "nan", "none"] and hours > 0:
                    all_data.append({
                        "Employee ID": emp_id,
                        "Employee Name": emp_map.get(emp_id, "Unknown"),
                        "Project": project,
                        "Month": month,
                        "Date": date,
                        "Hours": float(hours),
                        "Designation": designation_map.get(emp_id, "Unknown")
                    })
    return pd.DataFrame(all_data)

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

# --- NEW DAILY/WEEKLY TABLE UTILITY FUNCTIONS ---
def get_weeks_for_month(df):
    if df.empty or "Date" not in df.columns:
        return []
    # Parse all dates as pd.Timestamp
    dates = pd.to_datetime(df["Date"], errors='coerce').dropna().sort_values().unique()
    if len(dates) == 0:
        return []
    # Explicitly convert to pd.Timestamp for safe timedelta operations
    min_date = pd.Timestamp(dates[0])
    max_date = pd.Timestamp(dates[-1])
    weeks = []
    curr = min_date
    while curr <= max_date:
        week_end = curr + timedelta(days=6)
        weeks.append( (curr, week_end) )
        curr = week_end + timedelta(days=1)
    return weeks

def filter_df_by_week(df, week_start, week_end):
    df = df.copy()
    df["Date_parsed"] = pd.to_datetime(df["Date"], errors='coerce')
    mask = (df["Date_parsed"] >= week_start) & (df["Date_parsed"] <= week_end)
    return df[mask].copy()



# -- MAIN APP LOGIC --

# Load employee map and designation once
emp_name_map, emp_designation_map = get_employee_map_cached()

# Get all months from all employees, cached
all_months_raw = []
for emp_id, url in SHEET_URLS.items():
    file_id = extract_file_id(url)
    if not file_id:
        continue
    months = get_sheet_names_cached(file_id)
    all_months_raw.extend(months)
    # no time.sleep needed due to caching

all_months = sort_months_chronologically(list(set(all_months_raw)))

# Month selection from UI
month = st.selectbox("Select Month", all_months)

if month:
    # Analyze data for only selected month to reduce API calls
    df_all_time = analyze_all_months([month], SHEET_URLS, emp_name_map, emp_designation_map)
    df_summary = df_all_time[df_all_time['Month'] == month]

    if df_summary.empty:
        st.warning("No data found for this month")
    else:
        df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
        df_summary = df_summary[~df_summary['Project'].str.match(r'^\d+$')]
        df_summary = df_summary[df_summary['Project'].str.len() > 2]

        if "Employee" not in df_summary.columns:
            df_summary['Employee'] = (df_summary['Employee Name'] + " (" +
                                     df_summary['Designation'] + ", " + df_summary['Employee ID'] + ")")

        df_with_week = add_week_column(df_summary)  #added lines below
        # st.write("DEBUG: Week distribution")
        # st.write(df_with_week["Week"].value_counts())
        # st.write("DEBUG: Sample dates and their weeks")
        # st.write(df_with_week[["Date", "Week"]].head(20))

        st.subheader("📅 Weekly Resource Effort Table")
        if not df_with_week.empty:
            unique_projects_weekly = sorted(df_with_week["Project"].unique())
            selected_proj_week = st.selectbox("Select a project for weekly breakdown", unique_projects_weekly, key="weekly_project")
            if selected_proj_week:
                df_proj_week = df_with_week[df_with_week["Project"] == selected_proj_week].copy()
                if not df_proj_week.empty:
                    st.subheader(f"📋 Weekly Resource Effort Table - {selected_proj_week}")
                    weekly_table = pd.pivot_table(
                        df_proj_week, values="Hours", index="Employee Name",
                        columns="Week", aggfunc="sum", fill_value=0
                    )
                    for week in ["Week 1", "Week 2", "Week 3", "Week 4"]:
                        if week not in weekly_table.columns:
                            weekly_table[week] = 0
                    weekly_table = weekly_table[["Week 1", "Week 2", "Week 3", "Week 4"]]
                    weekly_table["TOTAL (Man Days)"] = weekly_table.sum(axis=1)
                    weekly_table = weekly_table.sort_values("TOTAL (Man Days)", ascending=False)
                    st.dataframe(weekly_table.style.format("{:.1f}"), use_container_width=True)
                else:
                    st.info("No weekly data found for this project in selected month.")
        else:
            st.warning("No valid date data found for weekly breakdown")

        st.subheader("👤 Individual Employee Project Breakdown")
        if not df_with_week.empty:
            unique_employees = sorted(df_with_week["Employee Name"].unique())
            selected_employee = st.selectbox("Select Employee", unique_employees, key="individual_employee")
            if selected_employee:
                df_employee = df_with_week[df_with_week["Employee Name"] == selected_employee].copy()
                if not df_employee.empty:
                    st.subheader(f"📋 Project Breakdown for {selected_employee} - {month}")
                    employee_table = pd.pivot_table(
                        df_employee, values="Hours", index="Project",
                        columns="Week", aggfunc="sum", fill_value=0
                    )
                    for week in ["Week 1", "Week 2", "Week 3", "Week 4"]:
                        if week not in employee_table.columns:
                            employee_table[week] = 0
                    employee_table = employee_table[["Week 1", "Week 2", "Week 3", "Week 4"]]
                    employee_table["TOTAL (Man Days)"] = employee_table.sum(axis=1)
                    working_days_per_month = 22
                    employee_table["Utilization (%)"] = (employee_table["TOTAL (Man Days)"] / working_days_per_month * 100).round(2)
                    total_row = employee_table.sum(numeric_only=True)
                    total_row.name = "Total"
                    total_row["Utilization (%)"] = (total_row["TOTAL (Man Days)"] / working_days_per_month * 100).round(2)
                    employee_table = pd.concat([employee_table, total_row.to_frame().T])
                    employee_table_sorted = employee_table.iloc[:-1].sort_values("TOTAL (Man Days)", ascending=False)
                    employee_table = pd.concat([employee_table_sorted, employee_table.iloc[[-1]]])
                    def format_table(df):
                        styled_df = df.style.format({
                            "Week 1": "{:.1f}", "Week 2": "{:.1f}", "Week 3": "{:.1f}",
                            "Week 4": "{:.1f}", "TOTAL (Man Days)": "{:.1f}",
                            "Utilization (%)": "{:.2f}%"
                        })
                        def color_utilization(val):
                            if pd.isna(val): return ""
                            try:
                                num_val = float(str(val).replace('%', ''))
                                if num_val < 50: return "background-color: #ff9800"
                                elif num_val < 80: return "background-color: #42a5f5"
                                elif num_val <= 100: return "background-color: #1976d2"
                                else: return "background-color: #c62828"
                            except: return ""
                        styled_df = styled_df.applymap(color_utilization, subset=["Utilization (%)"])
                        return styled_df
                    st.dataframe(format_table(employee_table), use_container_width=True)
                    total_utilization = employee_table.loc["Total", "Utilization (%)"]
                    if total_utilization < 50:
                        st.warning("🔴 Low Utilization - Employee may need more work allocation")
                    elif total_utilization > 120:
                        st.error("🔴 Over-Utilization - Employee may be overloaded")
                    elif total_utilization > 100:
                        st.warning("🟡 High Utilization - Monitor workload carefully")
                    else:
                        st.success("🟢 Good Utilization - Well balanced workload")
                else:
                    st.info(f"No data found for {selected_employee} in {month}")
        else:
            st.warning("No valid date data found for individual employee analysis")

        # Could add Month-on-Month and Overall Dashboard here similarly, loading data only on demand
    # Add below inside your main app logic section (after the Individual Employee Project Breakdown)

    if month:
                # ---------- NEW: DAILY/WEEKLY NAVIGATION TABLE ----------
        st.subheader("🗓️ Daily Employee Effort Table (Per Project, by Week)")

        if not df_with_week.empty:
            all_employee_names = sorted(df_with_week["Employee Name"].unique())
            selected_emp_daily = st.selectbox("Select Employee for Daily Effort Table", all_employee_names, key="daily_employee")
            
            # Prepare employee data with valid dates
            emp_data = df_with_week[df_with_week["Employee Name"] == selected_emp_daily].copy()
            emp_data = emp_data[~pd.to_datetime(emp_data["Date"], errors='coerce').isna()]
            
            if not emp_data.empty:
                # Get all weeks for this employee's data
                weeks = get_weeks_for_month(emp_data)
                if weeks:
                    # Initialize week position in session state (unique per employee)
                    if f"{selected_emp_daily}_week_pos" not in st.session_state:
                        st.session_state[f"{selected_emp_daily}_week_pos"] = 0
                    
                    total_weeks = len(weeks)
                    
                    # Navigation controls
                    col1, col2, col3 = st.columns([1,2,1])
                    with col1:
                        if st.button("< Previous Week", key=f"prev_{selected_emp_daily}",
                                     disabled=st.session_state[f"{selected_emp_daily}_week_pos"]==0):
                            st.session_state[f"{selected_emp_daily}_week_pos"] = max(0,
                                st.session_state[f"{selected_emp_daily}_week_pos"] - 1)
                    with col3:
                        if st.button("Next Week >", key=f"next_{selected_emp_daily}",
                                     disabled=st.session_state[f"{selected_emp_daily}_week_pos"]==(total_weeks-1)):
                            st.session_state[f"{selected_emp_daily}_week_pos"] = min(total_weeks-1,
                                st.session_state[f"{selected_emp_daily}_week_pos"] + 1)
                    
                    # Current week information
                    week_start, week_end = weeks[st.session_state[f"{selected_emp_daily}_week_pos"]]
                    st.markdown(f"**Week {st.session_state[f'{selected_emp_daily}_week_pos'] + 1} of {total_weeks}:** {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
                    
                    # Filter data for current week
                    week_df = filter_df_by_week(emp_data, week_start, week_end)
                    
                    if not week_df.empty:
                        # Format dates for column headers
                        week_df["Date_formatted"] = week_df["Date_parsed"].dt.strftime("%a %d-%b")
                        
                        # Create all 7 days for the week
                        #displayed_cols = [(week_start + timedelta(days=i)).strftime("%a %d-%b") for i in range(7)]
                        displayed_cols = [(week_start + pd.Timedelta(days=i)).strftime("%a %d-%b") for i in range(7)]

                        
                        # Create pivot table: Projects as rows, Days as columns
                        result_pivot = pd.pivot_table(
                            week_df,
                            values="Hours",
                            index="Project",
                            columns="Date_formatted",
                            aggfunc="sum",
                            fill_value=0
                        )
                        
                        # Ensure all 7 days are present as columns
                        for col in displayed_cols:
                            if col not in result_pivot.columns:
                                result_pivot[col] = 0
                        
                        # Reorder columns to show days in sequence
                        result_pivot = result_pivot[displayed_cols]
                        
                        # Add total column
                        result_pivot["TOTAL (Hours)"] = result_pivot.sum(axis=1)
                        
                        # Sort by total hours (highest first)
                        result_pivot = result_pivot.sort_values("TOTAL (Hours)", ascending=False)
                        
                        # Display the table
                        st.dataframe(result_pivot.style.format("{:.1f}"), use_container_width=True)
                    else:
                        st.info("No effort data for this week.")
                else:
                    st.info("No week data found for this employee.")
            else:
                st.info("No records with valid dates for the selected employee.")
        else:
            st.warning("No valid data for daily effort analysis.")

        # Using df_all_time from previously computed only for selected month (if you want all months for MOM tables, consider caching all months carefully)
        # To avoid high API usage, analyze only all available months if needed - else use the selected month data.

        # For Month-on-Month Project Resource Analysis (per selected project)
        st.subheader("📊 Month-on-Month Project Resource Analysis")
        if not df_all_time.empty:
            all_projects_mom = sorted(df_all_time["Project"].dropna().unique())
            selected_project_mom = st.selectbox(
                "Select Project for Month-on-Month Analysis",
                all_projects_mom,
                key="mom_project_selection"
            )
            if selected_project_mom:
                # For month-on-month, we need to process multiple months of data
                # Let's cache and load all selected months used for MOM
                # To reduce API calls, check if you want to limit number of months or cache all months upfront

                # For demonstration, load all months:
                # Warning: This may increase API calls.
                df_all_months = analyze_all_months(all_months, SHEET_URLS, emp_name_map, emp_designation_map)

                def create_month_on_month_project_table(df_all, selected_project, current_month, all_months):
                    expected_map = get_expected_effort_map_cached()
                    planned_effort = expected_map.get(selected_project, 0)
                    project_data = df_all[df_all["Project"] == selected_project].copy()

                    if project_data.empty:
                        return pd.DataFrame(), []

                    try:
                        current_month_idx = all_months.index(current_month)
                    except ValueError:
                        return pd.DataFrame(), []

                    display_months = []
                    month_labels = []

                    for offset in [2, 1, 0]:
                        target_idx = current_month_idx - offset
                        if 0 <= target_idx < len(all_months):
                            month_name = all_months[target_idx]
                            display_months.append(month_name)
                            month_labels.append(month_name)
                        else:
                            placeholder_name = f"NoData-{offset}"
                            display_months.append(placeholder_name)
                            if offset == 2:
                                month_labels.append("2 Months Ago")
                            elif offset == 1:
                                month_labels.append("1 Month Ago")
                            else:
                                month_labels.append("Current")

                    all_project_resources = project_data["Employee Name"].unique()
                    if len(all_project_resources) == 0:
                        return pd.DataFrame(), display_months

                    table_data = []
                    for resource in sorted(all_project_resources):
                        resource_data = project_data[project_data["Employee Name"] == resource]
                        row = {"Resource": resource}
                        total_effort = 0
                        for i, month_name in enumerate(display_months):
                            if month_name.startswith("NoData-"):
                                row[f"M{i+1}"] = 0.0
                            else:
                                month_effort = resource_data[resource_data["Month"] == month_name]["Hours"].sum()
                                row[f"M{i+1}"] = month_effort
                                total_effort += month_effort
                        row["TOTAL Effort (Man Days)"] = total_effort
                        planned_per_resource = planned_effort / len(all_project_resources) if len(all_project_resources) > 0 and planned_effort > 0 else 0
                        row["Planned Effort (Man Days)"] = planned_per_resource
                        table_data.append(row)

                    total_row = {"Resource": "Total"}
                    for i in range(1, 4):
                        total_row[f"M{i}"] = sum(row[f"M{i}"] for row in table_data)
                    total_row["TOTAL Effort (Man Days)"] = sum(row["TOTAL Effort (Man Days)"] for row in table_data)
                    total_row["Planned Effort (Man Days)"] = planned_effort
                    table_data.append(total_row)
                    return pd.DataFrame(table_data), month_labels

                mom_table, month_labels = create_month_on_month_project_table(
                    df_all_months, selected_project_mom, month, all_months
                )
                if not mom_table.empty:
                    st.markdown(f"#### 📈 Month-on-Month Analysis: {selected_project_mom}")
                    st.markdown(f"**Months:** M1 ({month_labels[0]}) → M2 ({month_labels[1]}) → M3 ({month_labels[2]})")
                    display_table = mom_table.copy()
                    for i, month_label in enumerate(month_labels):
                        old_col = f"M{i+1}"
                        new_col = f"M{i+1} ({month_label})"
                        if old_col in display_table.columns:
                            display_table = display_table.rename(columns={old_col: new_col})
                    styled_table = display_table.style.format({
                        col: "{:.1f}" for col in display_table.columns
                        if col not in ["Resource"] and col in display_table.select_dtypes(include=[int, float]).columns
                    }).background_gradient(
                        subset=["TOTAL Effort (Man Days)", "Planned Effort (Man Days)"],
                        cmap="RdYlGn"
                    )
                    st.dataframe(styled_table, use_container_width=True)
                else:
                    st.info(f"No data found for project: {selected_project_mom}")
        else:
            st.info("No all-time data available for Month-on-Month project resource analysis.")

        # Month-on-Month Project Dashboard (Overall)
        st.subheader("📋 A. Project Dashboard: Month on Month")
        expected_map = get_expected_effort_map_cached()
        st.write("DEBUG: Effort Map from Master Sheet")
        st.write(expected_map)
        st.write("DEBUG: Projects in current data")
        if not df_all_time.empty:
            def create_project_dashboard_month_on_month(df_all_time, current_month, all_months):
                try:
                    current_month_idx = all_months.index(current_month)
                except ValueError:
                    return pd.DataFrame(), []

                display_months = []
                month_labels = []

                for offset in [2, 1, 0]:
                    target_idx = current_month_idx - offset
                    if 0 <= target_idx < len(all_months):
                        month_name = all_months[target_idx]
                        display_months.append(month_name)
                        month_labels.append(month_name)
                    else:
                        placeholder_name = f"NoData-{offset}"
                        display_months.append(placeholder_name)
                        month_labels.append("No Data")

                all_projects = sorted(df_all_time["Project"].dropna().unique())
                expected_map = get_expected_effort_map_cached()
                table_data = []

                for project in all_projects:
                    project_data = df_all_time[df_all_time["Project"] == project]
                    row = {"Project": project}
                    total_effort = 0
                    for i, month_name in enumerate(display_months):
                        if month_name.startswith("NoData-"):
                            row[f"M{i+1}"] = 0.0
                        else:
                            month_effort = project_data[project_data["Month"] == month_name]["Hours"].sum()
                            row[f"M{i+1}"] = month_effort
                            total_effort += month_effort
                    row["Total"] = total_effort
                    row["Effort Planned"] = expected_map.get(project, 0)
                    table_data.append(row)
                return pd.DataFrame(table_data), month_labels

            # For the overall dashboard, load all months data too (you may cache this)
            df_all_months_for_proj = analyze_all_months(all_months, SHEET_URLS, emp_name_map, emp_designation_map)

            project_mom_table, project_mom_labels = create_project_dashboard_month_on_month(
                df_all_months_for_proj, month, all_months
            )
            if not project_mom_table.empty:
                display_project_table = project_mom_table.copy()
                st.markdown(f"**Timeline:** {project_mom_labels[0]} → {project_mom_labels[1]} → {project_mom_labels[2]}")
                styled_project_table = display_project_table.style.format({
                    col: "{:.1f}" for col in display_project_table.columns
                    if col not in ["Project"] and col in display_project_table.select_dtypes(include=[int, float]).columns
                })
                st.dataframe(styled_project_table, use_container_width=True)
            else:
                st.info("No project data available for dashboard")
        else:
            st.info("No all-time data available for Month-on-Month project dashboard")

        # Overall Dashboard: Individual dashboard for the selected month
        st.subheader(f"📋 B. Individual Dashboard: {month}")
        individual_dashboard_table = None
        if not df_all_time.empty:
            def create_individual_dashboard(df_all_time, current_month, emp_designation_map):
                current_data = df_all_time[df_all_time["Month"] == current_month].copy()
                if current_data.empty:
                    return pd.DataFrame()

                # def assign_week_simple(date_str):
                #     try:
                #         date_str = str(date_str).strip()
                #         formats = ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"]
                #         for fmt in formats:
                #             try:
                #                 dt = datetime.strptime(date_str, fmt)
                #                 day = dt.day
                #                 if day <= 7:
                #                     return "W1"
                #                 elif day <= 14:
                #                     return "W2"
                #                 elif day <= 21:
                #                     return "W3"
                #                 else:
                #                     return "W4"
                #             except ValueError:
                #                 continue
                #         return "W1"
                #     except:
                #         return "W1"

                def assign_week_simple(date_str):
                    try:
                        date_str = str(date_str).strip()
                       # formats = ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"]
                        formats = [
                                "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y",
                                "%m/%d/%y", "%d/%m/%y",
                            ]
                        for fmt in formats:
                            try:
                                dt = datetime.strptime(date_str, fmt)
                                day = dt.day
                                if 1 <= day <= 7:
                                    return "W1"
                                elif 8 <= day <= 14:
                                    return "W2"
                                elif 15 <= day <= 21:
                                    return "W3"
                                elif 22 <= day <= 31:
                                    return "W4"
                                else:
                                    return "W1"
                            except ValueError:
                                continue
                        return "W1"
                    except:
                        return "W1"

                current_data["Week"] = current_data["Date"].apply(assign_week_simple)
                all_employees = sorted(current_data["Employee Name"].unique())
                table_data = []

                for employee in all_employees:
                    emp_data = current_data[current_data["Employee Name"] == employee]
                    emp_id = emp_data["Employee ID"].iloc[0] if not emp_data.empty else "Unknown"
                    designation = emp_designation_map.get(emp_id, "Unknown")
                    weekly_pivot = pd.pivot_table(
                        emp_data,
                        values="Hours",
                        columns="Week",
                        aggfunc="sum",
                        fill_value=0
                    )
                    row = {
                        "Resource": employee,
                        "Designation": designation,
                        "W1": float(weekly_pivot.get("W1", 0)),
                        "W2": float(weekly_pivot.get("W2", 0)),
                        "W3": float(weekly_pivot.get("W3", 0)),
                        "W4": float(weekly_pivot.get("W4", 0))
                    }
                    total_man_days = row["W1"] + row["W2"] + row["W3"] + row["W4"]
                    row["Total (Man Days)"] = float(total_man_days)
                    working_days_per_month = 22
                    utilization = (total_man_days / working_days_per_month * 100) if working_days_per_month > 0 else 0
                    row["Utilization (%)"] = f"{utilization:.1f}%"
                    table_data.append(row)
                return pd.DataFrame(table_data)

            individual_dashboard_table = create_individual_dashboard(df_all_time, month, emp_designation_map)
            if not individual_dashboard_table.empty:
                def format_individual_table(df):
                    df_copy = df.copy()
                    numeric_cols = ["W1", "W2", "W3", "W4", "Total (Man Days)"]
                    for col in numeric_cols:
                        if col in df_copy.columns:
                            df_copy[col] = df_copy[col].round(1)
                    return df_copy.style.set_properties(**{'text-align': 'center'}).set_table_styles([
                        {'selector': 'th', 'props': [('text-align', 'center')]},
                        {'selector': 'td', 'props': [('text-align', 'center')]}
                    ])
                st.dataframe(format_individual_table(individual_dashboard_table), use_container_width=True)
            else:
                st.info("No individual data available for current month")
        else:
            st.info("No all-time data available for Individual Dashboard")

    else:
        st.info("Please select a month to begin analysis.")
         

    # if st.button("Refresh Data"):
    #     # Increment cache_key to invalidate cache
    #     st.session_state["cache_key"] = cache_key + 1

    # data = load_data_with_cache(st.session_state.get("cache_key", 0))
    # st.write(data)

else:
    st.info("Please select a month to begin analysis.")



# ===========================END-------------------------------END==============================END----------------------END========================== #

