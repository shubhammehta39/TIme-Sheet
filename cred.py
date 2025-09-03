import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
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


# @st.cache_resource
# def get_google_services():
#     creds = service_account.Credentials.from_service_account_info(
#         st.secrets["gcp_service_account"],  # <-- from secrets, not file
#         scopes=SCOPES
#     )
#     drive_service = build("drive", "v3", credentials=creds)
#     sheets_service = build("sheets", "v4", credentials=creds)
#     return drive_service, sheets_service

# drive_service, sheets_service = get_google_services()

# st.set_page_config(page_title="TDf Project Tracker Dashboard", layout="wide")
# st.title("TDF Project Work Tracker")
# @st.cache_resource
# def get_google_services():
#     creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
#     drive_service = build("drive", "v3", credentials=creds)
#     sheets_service = build("sheets", "v4", credentials=creds)
#     return drive_service, sheets_service

# drive_service, sheets_service = get_google_services()

# st.set_page_config(page_title="TDf Project Tracker Dashboard", layout="wide")
# st.title("TDF Project Work Tracker")

# # --- CACHED UTILITY FUNCTIONS ---
# @st.cache_data(ttl=3600)
# def extract_file_id(url):
#     try:
#         return url.split("/d/")[1].split("/")[0]
#     except Exception:
#         return None

# @st.cache_data(ttl=3600)
# def get_sheet_names_cached(file_id: str):
#     if not file_id:
#         return []
#     try:
#         metadata = sheets_service.spreadsheets().get(spreadsheetId=file_id).execute()
#         return [sheet["properties"]["title"] for sheet in metadata.get("sheets", [])]
#     except Exception as e:
#         print(f"Error fetching sheet names for {file_id}: {e}")
#         return []

# @st.cache_data(ttl=3600)
# def load_sheet_data_cached(file_id: str, sheet_name: str):
#     try:
#         time.sleep(1.0)
#         result = sheets_service.spreadsheets().values().get(
#             spreadsheetId=file_id,
#             range=sheet_name
#         ).execute()
#         values = result.get('values', [])
#         if not values:
#             return pd.DataFrame()
#         df = pd.DataFrame(values)
#         df.columns = df.iloc[0]
#         df = df[1:]
#         df.reset_index(drop=True, inplace=True)
#         df.dropna(how="all", inplace=True)
#         return df
#     except Exception as e:
#         print(f"Error loading sheet data {sheet_name} from {file_id}: {e}")
#         return pd.DataFrame()
    
# @st.cache_data(ttl=3600)
# def get_employee_map_cached():
#     df = load_sheet_data_cached(MASTER_SHEET_ID, EMPLOYEE_SHEET_NAME)
#     if df.empty or not {"Employee ID", "Employee Name", "Designation"}.issubset(df.columns):
#         return {}, {}
#     df.columns = df.columns.astype(str).str.strip().str.replace('\n', ' ').str.replace('\r', ' ')
#     emp_name_map = dict(zip(df["Employee ID"].astype(str).str.strip(), df["Employee Name"].astype(str).str.strip()))
#     emp_designation_map = dict(zip(df["Employee ID"].astype(str).str.strip(), df["Designation"].astype(str).str.strip()))
#     return emp_name_map, emp_designation_map

# @st.cache_data(ttl=3600)
# def get_expected_effort_map_cached():
#     df_effort = load_sheet_data_cached(MASTER_SHEET_ID, "Project Master")
#     if df_effort.empty or not {"ProjectList", "Project Effort Plan"}.issubset(df_effort.columns):
#         return {}
#     df_effort.columns = df_effort.columns.astype(str).str.strip()
#     return dict(zip(
#         df_effort["ProjectList"].astype(str).str.strip(),
#         pd.to_numeric(df_effort["Project Effort Plan"], errors="coerce").fillna(0)
#     ))

# # --- DATA PROCESSING (no API calls here) ---
# def extract_individual_dates(date_string):
#     if not date_string or pd.isna(date_string):
#         return []
#     date_string = str(date_string).strip()
#     dates = []
#     patterns = [
#         r'(\d{1,2}/\d{1,2}/\d{4})',
#         r'(\d{2}-\d{2}-\d{4})',
#         r'(\d{1,2}-\d{1,2}-\d{4})',
#         r'(\d{4}-\d{2}-\d{2})',
#     ]
#     for pattern in patterns:
#         found_dates = re.findall(pattern, date_string)
#         if found_dates:
#             dates.extend(found_dates)
#             break
#     if not dates:
#         separators = ['/', '-', '_', ' ', ',']
#         for sep in separators:
#             if sep in date_string:
#                 potential_dates = date_string.split(sep)
#                 for i in range(0, len(potential_dates) - 2, 3):
#                     if i + 2 < len(potential_dates):
#                         try:
#                             month, day, year = potential_dates[i:i + 3]
#                             if len(year) == 4 and year.isdigit():
#                                 dates.append(f"{month}/{day}/{year}")
#                         except:
#                             continue
#                 break
#     return dates

# def parse_sheet_data_with_split_dates(file_id, sheet_name):
#     df = load_sheet_data_cached(file_id, sheet_name)
#     if df.empty:
#         return df
#     project_col = df.columns[0]
#     date_cols = df.columns[1:]
#     expanded_data = []
#     for _, row in df.iterrows():
#         project = str(row[project_col]).strip()
#         if project.lower() in ["", "nan", "none"]:
#             continue
#         for date_col in date_cols:
#             date_value = row[date_col]
#             if pd.isna(date_value) or str(date_value).strip() in ["", "-", "0"]:
#                 continue
#             individual_dates = extract_individual_dates(str(date_col))
#             if individual_dates:
#                 try:
#                     total_value = float(str(date_value).strip())
#                     value_per_date = total_value / len(individual_dates)
#                     for individual_date in individual_dates:
#                         expanded_data.append({
#                             project_col: project,
#                             'Date': individual_date,
#                             'Hours': value_per_date
#                         })
#                 except (ValueError, TypeError):
#                     continue
#             else:
#                 try:
#                     hours_value = float(str(date_value).strip())
#                     expanded_data.append({
#                         project_col: project,
#                         'Date': str(date_col),
#                         'Hours': hours_value
#                     })
#                 except (ValueError, TypeError):
#                     continue
#     if expanded_data:
#         return pd.DataFrame(expanded_data)
#     else:
#         return pd.DataFrame()

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

# def add_week_column(df):
#     df = df.copy()
#     if "Date" in df.columns:
#         df["Week"] = df["Date"].apply(assign_week)
#         return df[df["Week"] != "Unknown"]
#     return df

# # --- DATA ANALYSIS FUNCTIONS (use cached loads) ---
# def analyze_sheets(selected_month, all_months, sheet_urls, emp_map, designation_map):
#     employee_data = []
#     for employee_id, url in sheet_urls.items():
#         file_id = extract_file_id(url)
#         if not file_id:
#             continue
#         file_sheets = get_sheet_names_cached(file_id)
#         if selected_month not in file_sheets:
#             continue
#         df = parse_sheet_data_with_split_dates(file_id, selected_month)
#         if df.empty:
#             continue
#         for _, row in df.iterrows():
#             project = str(row.iloc[0]).strip()
#             date = str(row['Date']).strip()
#             hours = row['Hours']
#             if project.lower() not in ["", "nan", "none"] and hours > 0:
#                 employee_data.append({
#                     "Employee ID": employee_id,
#                     "Employee Name": emp_map.get(employee_id, "Unknown"),
#                     "Project": project,
#                     "Date": date,
#                     "Hours": float(hours),
#                     "Designation": designation_map.get(employee_id, "Unknown"),
#                     "Month": selected_month
#                 })
#     return pd.DataFrame(employee_data)

# def analyze_all_months(all_months, sheet_urls, emp_map, designation_map):
#     all_data = []
#     for month in all_months:
#         for emp_id, url in sheet_urls.items():
#             file_id = extract_file_id(url)
#             if not file_id:
#                 continue
#             file_sheets = get_sheet_names_cached(file_id)
#             if month not in file_sheets:
#                 continue
#             df = parse_sheet_data_with_split_dates(file_id, month)
#             if df.empty:
#                 continue
#             for _, row in df.iterrows():
#                 project = str(row.iloc[0]).strip()
#                 date = str(row['Date']).strip()
#                 hours = row['Hours']
#                 if project.lower() not in ["", "nan", "none"] and hours > 0:
#                     all_data.append({
#                         "Employee ID": emp_id,
#                         "Employee Name": emp_map.get(emp_id, "Unknown"),
#                         "Project": project,
#                         "Month": month,
#                         "Date": date,
#                         "Hours": float(hours),
#                         "Designation": designation_map.get(emp_id, "Unknown")
#                     })
#     return pd.DataFrame(all_data)

# def sort_months_chronologically(months):
#     month_dates = []
#     for month in months:
#         try:
#             if '-' in month:
#                 month_date = datetime.strptime(month, "%B-%y")
#             else:
#                 month_date = datetime.strptime(month, "%B-%Y")
#             month_dates.append((month_date, month))
#         except:
#             try:
#                 month_date = datetime.strptime(month.upper(), "%b-%y")
#                 month_dates.append((month_date, month))
#             except:
#                 month_dates.append((datetime.max, month))
#     month_dates.sort(key=lambda x: x[0])
#     return [month for _, month in month_dates]

# # --- NEW DAILY/WEEKLY TABLE UTILITY FUNCTIONS ---

# def get_weeks_for_month(df):
#     if df.empty or "Date" not in df.columns:
#         return []
#     # Parse all dates as pd.Timestamp
#     dates = pd.to_datetime(df["Date"], errors='coerce').dropna().sort_values().unique()
#     if len(dates) == 0:
#         return []
#     # Explicitly convert to pd.Timestamp for safe timedelta operations
#     min_date = pd.Timestamp(dates[0])
#     max_date = pd.Timestamp(dates[-1])
#     weeks = []
#     curr = min_date
#     while curr <= max_date:
#         week_end = curr + timedelta(days=6)
#         weeks.append( (curr, week_end) )
#         curr = week_end + timedelta(days=1)
#     return weeks


# def filter_df_by_week(df, week_start, week_end):
#     df = df.copy()
#     df["Date_parsed"] = pd.to_datetime(df["Date"], errors='coerce')
#     mask = (df["Date_parsed"] >= week_start) & (df["Date_parsed"] <= week_end)
#     return df[mask].copy()

# # -- MAIN APP LOGIC --
# # Load employee map and designation once
# emp_name_map, emp_designation_map = get_employee_map_cached()
# # Get all months from all employees, cached
# all_months_raw = []
# for emp_id, url in SHEET_URLS.items():
#     file_id = extract_file_id(url)
#     if not file_id:
#         continue
#     months = get_sheet_names_cached(file_id)
#     all_months_raw.extend(months)
# all_months = sort_months_chronologically(list(set(all_months_raw)))

# # Month selection from UI
# month = st.selectbox("Select Month", all_months)
# if month:
#     df_all_time = analyze_all_months([month], SHEET_URLS, emp_name_map, emp_designation_map)
#     df_summary = df_all_time[df_all_time['Month'] == month]
#     if df_summary.empty:
#         st.warning("No data found for this month")
#     else:
#         df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
#         df_summary = df_summary[~df_summary['Project'].str.match(r'^\d+$')]
#         df_summary = df_summary[df_summary['Project'].str.len() > 2]
#         if "Employee" not in df_summary.columns:
#             df_summary['Employee'] = (df_summary['Employee Name'] + " (" +
#                                      df_summary['Designation'] + ", " + df_summary['Employee ID'] + ")")
#         df_with_week = add_week_column(df_summary)
#         st.subheader("📅 Weekly Resource Effort Table")
#         if not df_with_week.empty:
#             unique_projects_weekly = sorted(df_with_week["Project"].unique())
#             selected_proj_week = st.selectbox("Select a project for weekly breakdown", unique_projects_weekly, key="weekly_project")
#             if selected_proj_week:
#                 df_proj_week = df_with_week[df_with_week["Project"] == selected_proj_week].copy()
#                 if not df_proj_week.empty:
#                     st.subheader(f"📋 Weekly Resource Effort Table - {selected_proj_week}")
#                     weekly_table = pd.pivot_table(
#                         df_proj_week, values="Hours", index="Employee Name",
#                         columns="Week", aggfunc="sum", fill_value=0
#                     )
#                     for week in ["Week 1", "Week 2", "Week 3", "Week 4"]:
#                         if week not in weekly_table.columns:
#                             weekly_table[week] = 0
#                     weekly_table = weekly_table[["Week 1", "Week 2", "Week 3", "Week 4"]]
#                     weekly_table["TOTAL (Man Days)"] = weekly_table.sum(axis=1)
#                     weekly_table = weekly_table.sort_values("TOTAL (Man Days)", ascending=False)
#                     st.dataframe(weekly_table.style.format("{:.1f}"), use_container_width=True)
#                 else:
#                     st.info("No weekly data found for this project in selected month.")
#         else:
#             st.warning("No valid date data found for weekly breakdown")
#         st.subheader("👤 Individual Employee Project Breakdown")
#         if not df_with_week.empty:
#             unique_employees = sorted(df_with_week["Employee Name"].unique())
#             selected_employee = st.selectbox("Select Employee", unique_employees, key="individual_employee")
#             if selected_employee:
#                 df_employee = df_with_week[df_with_week["Employee Name"] == selected_employee].copy()
#                 if not df_employee.empty:
#                     st.subheader(f"📋 Project Breakdown for {selected_employee} - {month}")
#                     employee_table = pd.pivot_table(
#                         df_employee, values="Hours", index="Project",
#                         columns="Week", aggfunc="sum", fill_value=0
#                     )
#                     for week in ["Week 1", "Week 2", "Week 3", "Week 4"]:
#                         if week not in employee_table.columns:
#                             employee_table[week] = 0
#                     employee_table = employee_table[["Week 1", "Week 2", "Week 3", "Week 4"]]
#                     employee_table["TOTAL (Man Days)"] = employee_table.sum(axis=1)
#                     working_days_per_month = 22
#                     employee_table["Utilization (%)"] = (employee_table["TOTAL (Man Days)"] / working_days_per_month * 100).round(2)
#                     total_row = employee_table.sum(numeric_only=True)
#                     total_row.name = "Total"
#                     total_row["Utilization (%)"] = (total_row["TOTAL (Man Days)"] / working_days_per_month * 100).round(2)
#                     employee_table = pd.concat([employee_table, total_row.to_frame().T])
#                     employee_table_sorted = employee_table.iloc[:-1].sort_values("TOTAL (Man Days)", ascending=False)
#                     employee_table = pd.concat([employee_table_sorted, employee_table.iloc[[-1]]])
#                     def format_table(df):
#                         styled_df = df.style.format({
#                             "Week 1": "{:.1f}", "Week 2": "{:.1f}", "Week 3": "{:.1f}",
#                             "Week 4": "{:.1f}", "TOTAL (Man Days)": "{:.1f}",
#                             "Utilization (%)": "{:.2f}%"
#                         })
#                         def color_utilization(val):
#                             if pd.isna(val): return ""
#                             try:
#                                 num_val = float(str(val).replace('%', ''))
#                                 if num_val < 50: return "background-color: #ff9800"
#                                 elif num_val < 80: return "background-color: #42a5f5"
#                                 elif num_val <= 100: return "background-color: #1976d2"
#                                 else: return "background-color: #c62828"
#                             except: return ""
#                         styled_df = styled_df.applymap(color_utilization, subset=["Utilization (%)"])
#                         return styled_df
#                     st.dataframe(format_table(employee_table), use_container_width=True)
#                     total_utilization = employee_table.loc["Total", "Utilization (%)"]
#                     if total_utilization < 50:
#                         st.warning("🔴 Low Utilization - Employee may need more work allocation")
#                     elif total_utilization > 120:
#                         st.error("🔴 Over-Utilization - Employee may be overloaded")
#                     elif total_utilization > 100:
#                         st.warning("🟡 High Utilization - Monitor workload carefully")
#                     else:
#                         st.success("🟢 Good Utilization - Well balanced workload")
#                 else:
#                     st.info(f"No data found for {selected_employee} in {month}")
#         else:
#             st.warning("No valid date data found for individual employee analysis")

#         # ---------- NEW: DAILY/WEEKLY NAVIGATION TABLE ----------
#         st.subheader("🗓️ Daily Employee Effort Table (Per Project, by Week)")

#         if not df_with_week.empty:
#             all_employee_names = sorted(df_with_week["Employee Name"].unique())
#             selected_emp_daily = st.selectbox("Select Employee for Daily Effort Table", all_employee_names, key="daily_employee")
#             emp_data = df_with_week[df_with_week["Employee Name"] == selected_emp_daily].copy()
#             emp_data = emp_data[~pd.to_datetime(emp_data["Date"], errors='coerce').isna()]
#             if not emp_data.empty:
#                 weeks = get_weeks_for_month(emp_data)
#                 if weeks:
#                     if f"{selected_emp_daily}_week_pos" not in st.session_state:
#                         st.session_state[f"{selected_emp_daily}_week_pos"] = 0
#                     total_weeks = len(weeks)
#                     col1, col2, col3 = st.columns([1,2,1])
#                     with col1:
#                         if st.button("< Previous Week", key=f"prev_{selected_emp_daily}",
#                                      disabled=st.session_state[f"{selected_emp_daily}_week_pos"]==0):
#                             st.session_state[f"{selected_emp_daily}_week_pos"] = max(0,
#                                 st.session_state[f"{selected_emp_daily}_week_pos"] - 1)
#                     with col3:
#                         if st.button("Next Week >", key=f"next_{selected_emp_daily}",
#                                      disabled=st.session_state[f"{selected_emp_daily}_week_pos"]==(total_weeks-1)):
#                             st.session_state[f"{selected_emp_daily}_week_pos"] = min(total_weeks-1,
#                                 st.session_state[f"{selected_emp_daily}_week_pos"] + 1)
#                     week_start, week_end = weeks[st.session_state[f"{selected_emp_daily}_week_pos"]]
#                     st.markdown(f"**Week:** {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
#                     week_df = filter_df_by_week(emp_data, week_start, week_end)
#                     if not week_df.empty:
#                         week_df["Date_formatted"] = week_df["Date_parsed"].dt.strftime("%a %d-%b")
#                         displayed_cols = [(week_start + timedelta(days=i)).strftime("%a %d-%b") for i in range(7)]
#                         result_pivot = pd.pivot_table(
#                             week_df,
#                             values="Hours",
#                             index="Project",
#                             columns="Date_formatted",
#                             aggfunc="sum",
#                             fill_value=0
#                         )
#                         for col in displayed_cols:
#                             if col not in result_pivot.columns:
#                                 result_pivot[col] = 0
#                         result_pivot = result_pivot[displayed_cols]
#                         result_pivot["TOTAL (Hours)"] = result_pivot.sum(axis=1)
#                         result_pivot = result_pivot.sort_values("TOTAL (Hours)", ascending=False)
#                         st.dataframe(result_pivot.style.format("{:.1f}"), use_container_width=True)
#                     else:
#                         st.info("No effort data for this week.")
#                 else:
#                     st.info("No week data found for this employee.")
#             else:
#                 st.info("No records with valid dates for the selected employee.")
#         else:
#             st.warning("No valid data for daily effort analysis.")

#         # ------- Month-on-Month Project Resource Analysis -------
#         st.subheader("📊 Month-on-Month Project Resource Analysis")
#         if not df_all_time.empty:
#             all_projects_mom = sorted(df_all_time["Project"].dropna().unique())
#             selected_project_mom = st.selectbox("Select Project for Month-on-Month Analysis", all_projects_mom, key="mom_project_selection")
#             if selected_project_mom:
#                 df_all_months = analyze_all_months(all_months, SHEET_URLS, emp_name_map, emp_designation_map)
#                 def create_month_on_month_project_table(df_all, selected_project, current_month, all_months):
#                     expected_map = get_expected_effort_map_cached()
#                     planned_effort = expected_map.get(selected_project, 0)
#                     project_data = df_all[df_all["Project"] == selected_project].copy()
#                     if project_data.empty:
#                         return pd.DataFrame(), []
#                     try:
#                         current_month_idx = all_months.index(current_month)
#                     except ValueError:
#                         return pd.DataFrame(), []
#                     display_months = []
#                     month_labels = []
#                     for offset in [2, 1, 0]:
#                         target_idx = current_month_idx - offset
#                         if 0 <= target_idx < len(all_months):
#                             month_name = all_months[target_idx]
#                             display_months.append(month_name)
#                             month_labels.append(month_name)
#                         else:
#                             placeholder_name = f"NoData-{offset}"
#                             display_months.append(placeholder_name)
#                             if offset == 2:
#                                 month_labels.append("2 Months Ago")
#                             elif offset == 1:
#                                 month_labels.append("1 Month Ago")
#                             else:
#                                 month_labels.append("Current")
#                     all_project_resources = project_data["Employee Name"].unique()
#                     if len(all_project_resources) == 0:
#                         return pd.DataFrame(), display_months
#                     table_data = []
#                     for resource in sorted(all_project_resources):
#                         resource_data = project_data[project_data["Employee Name"] == resource]
#                         row = {"Resource": resource}
#                         total_effort = 0
#                         for i, month_name in enumerate(display_months):
#                             if month_name.startswith("NoData-"):
#                                 row[f"M{i+1}"] = 0.0
#                             else:
#                                 month_effort = resource_data[resource_data["Month"] == month_name]["Hours"].sum()
#                                 row[f"M{i+1}"] = month_effort
#                                 total_effort += month_effort
#                         row["TOTAL Effort (Man Days)"] = total_effort
#                         planned_per_resource = planned_effort / len(all_project_resources) if len(all_project_resources) > 0 and planned_effort > 0 else 0
#                         row["Planned Effort (Man Days)"] = planned_per_resource
#                         table_data.append(row)
#                     total_row = {"Resource": "Total"}
#                     for i in range(1, 4):
#                         total_row[f"M{i}"] = sum(row[f"M{i}"] for row in table_data)
#                     total_row["TOTAL Effort (Man Days)"] = sum(row["TOTAL Effort (Man Days)"] for row in table_data)
#                     total_row["Planned Effort (Man Days)"] = planned_effort
#                     table_data.append(total_row)
#                     return pd.DataFrame(table_data), month_labels
#                 mom_table, month_labels = create_month_on_month_project_table(
#                     df_all_months, selected_project_mom, month, all_months
#                 )
#                 if not mom_table.empty:
#                     st.markdown(f"#### 📈 Month-on-Month Analysis: {selected_project_mom}")
#                     st.markdown(f"**Months:** M1 ({month_labels[0]}) → M2 ({month_labels[1]}) → M3 ({month_labels[2]})")
#                     display_table = mom_table.copy()
#                     for i, month_label in enumerate(month_labels):
#                         old_col = f"M{i+1}"
#                         new_col = f"M{i+1} ({month_label})"
#                         if old_col in display_table.columns:
#                             display_table = display_table.rename(columns={old_col: new_col})
#                     styled_table = display_table.style.format({
#                         col: "{:.1f}" for col in display_table.columns
#                         if col not in ["Resource"] and col in display_table.select_dtypes(include=[int, float]).columns
#                     }).background_gradient(
#                         subset=["TOTAL Effort (Man Days)", "Planned Effort (Man Days)"],
#                         cmap="RdYlGn"
#                     )
#                     st.dataframe(styled_table, use_container_width=True)
#                 else:
#                     st.info(f"No data found for project: {selected_project_mom}")
#         else:
#             st.info("No all-time data available for Month-on-Month project resource analysis.")

#         # ------- Month-on-Month Project Dashboard (Overall) -------
#         st.subheader("📋 A. Project Dashboard: Month on Month")
#         if not df_all_time.empty:
#             def create_project_dashboard_month_on_month(df_all_time, current_month, all_months):
#                 try:
#                     current_month_idx = all_months.index(current_month)
#                 except ValueError:
#                     return pd.DataFrame(), []
#                 display_months = []
#                 month_labels = []
#                 for offset in [2, 1, 0]:
#                     target_idx = current_month_idx - offset
#                     if 0 <= target_idx < len(all_months):
#                         month_name = all_months[target_idx]
#                         display_months.append(month_name)
#                         month_labels.append(month_name)
#                     else:
#                         placeholder_name = f"NoData-{offset}"
#                         display_months.append(placeholder_name)
#                         month_labels.append("No Data")
#                 all_projects = sorted(df_all_time["Project"].dropna().unique())
#                 expected_map = get_expected_effort_map_cached()
#                 table_data = []
#                 for project in all_projects:
#                     project_data = df_all_time[df_all_time["Project"] == project]
#                     row = {"Project": project}
#                     total_effort = 0
#                     for i, month_name in enumerate(display_months):
#                         if month_name.startswith("NoData-"):
#                             row[f"M{i+1}"] = 0.0
#                         else:
#                             month_effort = project_data[project_data["Month"] == month_name]["Hours"].sum()
#                             row[f"M{i+1}"] = month_effort
#                             total_effort += month_effort
#                     row["Total"] = total_effort
#                     row["Effort Planned"] = expected_map.get(project, 0)
#                     table_data.append(row)
#                 return pd.DataFrame(table_data), month_labels
#             df_all_months_for_proj = analyze_all_months(all_months, SHEET_URLS, emp_name_map, emp_designation_map)
#             project_mom_table, project_mom_labels = create_project_dashboard_month_on_month(
#                 df_all_months_for_proj, month, all_months
#             )
#             if not project_mom_table.empty:
#                 display_project_table = project_mom_table.copy()
#                 st.markdown(f"**Timeline:** {project_mom_labels[0]} → {project_mom_labels[1]} → {project_mom_labels[2]}")
#                 styled_project_table = display_project_table.style.format({
#                     col: "{:.1f}" for col in display_project_table.columns
#                     if col not in ["Project"] and col in display_project_table.select_dtypes(include=[int, float]).columns
#                 })
#                 st.dataframe(styled_project_table, use_container_width=True)
#             else:
#                 st.info("No project data available for dashboard")
#         else:
#             st.info("No all-time data available for Month-on-Month project dashboard")

#         # ------- Individual Dashboard for the selected month -------
#         st.subheader(f"📋 B. Individual Dashboard: {month}")
#         individual_dashboard_table = None
#         if not df_all_time.empty:
#             def create_individual_dashboard(df_all_time, current_month, emp_designation_map):
#                 current_data = df_all_time[df_all_time["Month"] == current_month].copy()
#                 if current_data.empty:
#                     return pd.DataFrame()
#                 def assign_week_simple(date_str):
#                     try:
#                         date_str = str(date_str).strip()
#                         formats = ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"]
#                         for fmt in formats:
#                             try:
#                                 dt = datetime.strptime(date_str, fmt)
#                                 day = dt.day
#                                 if day <= 7:
#                                     return "W1"
#                                 elif day <= 14:
#                                     return "W2"
#                                 elif day <= 21:
#                                     return "W3"
#                                 else:
#                                     return "W4"
#                             except ValueError:
#                                 continue
#                         return "W1"
#                     except:
#                         return "W1"
#                 current_data["Week"] = current_data["Date"].apply(assign_week_simple)
#                 all_employees = sorted(current_data["Employee Name"].unique())
#                 table_data = []
#                 for employee in all_employees:
#                     emp_data = current_data[current_data["Employee Name"] == employee]
#                     emp_id = emp_data["Employee ID"].iloc[0] if not emp_data.empty else "Unknown"
#                     designation = emp_designation_map.get(emp_id, "Unknown")
#                     weekly_pivot = pd.pivot_table(
#                         emp_data,
#                         values="Hours",
#                         columns="Week",
#                         aggfunc="sum",
#                         fill_value=0
#                     )
#                     row = {
#                         "Resource": employee,
#                         "Designation": designation,
#                         "W1": float(weekly_pivot.get("W1", 0)),
#                         "W2": float(weekly_pivot.get("W2", 0)),
#                         "W3": float(weekly_pivot.get("W3", 0)),
#                         "W4": float(weekly_pivot.get("W4", 0))
#                     }
#                     total_man_days = row["W1"] + row["W2"] + row["W3"] + row["W4"]
#                     row["Total (Man Days)"] = float(total_man_days)
#                     working_days_per_month = 22
#                     utilization = (total_man_days / working_days_per_month * 100) if working_days_per_month > 0 else 0
#                     row["Utilization (%)"] = f"{utilization:.1f}%"
#                     table_data.append(row)
#                 return pd.DataFrame(table_data)
#             individual_dashboard_table = create_individual_dashboard(df_all_time, month, emp_designation_map)
#             if not individual_dashboard_table.empty:
#                 def format_individual_table(df):
#                     df_copy = df.copy()
#                     numeric_cols = ["W1", "W2", "W3", "W4", "Total (Man Days)"]
#                     for col in numeric_cols:
#                         if col in df_copy.columns:
#                             df_copy[col] = df_copy[col].round(1)
#                     return df_copy.style.set_properties(**{'text-align': 'center'}).set_table_styles([
#                         {'selector': 'th', 'props': [('text-align', 'center')]},
#                         {'selector': 'td', 'props': [('text-align', 'center')]}
#                     ])
#                 st.dataframe(format_individual_table(individual_dashboard_table), use_container_width=True)
#             else:
#                 st.info("No individual data available for current month")
#         else:
#             st.info("No all-time data available for Individual Dashboard")
# else:
#     st.info("Please select a month to begin analysis.")


# START====================================      START      ==================================     START    ==========================================
@st.cache_resource
def get_google_services():
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    drive_service = build("drive", "v3", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)
    return drive_service, sheets_service

drive_service, sheets_service = get_google_services()
@st.cache_resource
def get_google_services():
    service_account_info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
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
            if pd.isna(date_value) or str(date_value).strip() in ["", "-", "0"]:
                continue
            individual_dates = extract_individual_dates(str(date_col))
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

def assign_week(date_str):
    try:
        if not date_str or pd.isna(date_str) or str(date_str).strip() == "":
            return "Unknown"
        date_str = str(date_str).strip()
        formats = [
            "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y",
            "%m-%d-%Y", "%m/%d/%y", "%d/%m/%y",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                day = dt.day
                if day <= 7:
                    return "Week 1"
                elif day <= 14:
                    return "Week 2"
                elif day <= 21:
                    return "Week 3"
                else:
                    return "Week 4"
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

        df_with_week = add_week_column(df_summary)

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
                        displayed_cols = [(week_start + timedelta(days=i)).strftime("%a %d-%b") for i in range(7)]
                        
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

                def assign_week_simple(date_str):
                    try:
                        date_str = str(date_str).strip()
                        formats = ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"]
                        for fmt in formats:
                            try:
                                dt = datetime.strptime(date_str, fmt)
                                day = dt.day
                                if day <= 7:
                                    return "W1"
                                elif day <= 14:
                                    return "W2"
                                elif day <= 21:
                                    return "W3"
                                else:
                                    return "W4"
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


# import streamlit as st
# import pandas as pd
# import plotly.express as px
# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# from datetime import datetime
# import time
# import io
# import plotly.io as pio
# import hashlib
# from dotenv import load_dotenv
# import re

# # --- CONFIGURATION ---
# SCOPES = [
#     "https://www.googleapis.com/auth/spreadsheets",
#     "https://www.googleapis.com/auth/drive"
# ]

# SHEET_URLS = {
#     "TDFS44": "https://docs.google.com/spreadsheets/d/1p3583-UC0odlroqFyfdYqKF5AlO2NbA7EY9_95yNloE",  # aditi
#     "TDFS46": "https://docs.google.com/spreadsheets/d/1fwj1MWZGqbcDATuUfoeuRhEJ7tmqKlQ9v29fRy1IeVA",  # chirag
#     "TDFS47": "https://docs.google.com/spreadsheets/d/1NKLyLNN1AEKlVaS1ejfAO6MmRrdqDt1qjhnuuGL5xAw"   # harsh
# }

# CREDENTIALS_PATH = "credentials.json"
# MASTER_SHEET_ID = "1keBMyJdHJIeHrCsM70_xJlq4lugoHJibTelqKP_S3hs"
# EMPLOYEE_SHEET_NAME = "Employee Detail"

# # --- AUTHENTICATION ---
# creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
# drive_service = build("drive", "v3", credentials=creds)
# sheets_service = build("sheets", "v4", credentials=creds)

# st.set_page_config(page_title="📊 Project Tracker Dashboard", layout="wide")
# st.title("📊 Project Work Tracker")

# # --- UTILITY FUNCTIONS ---
# def extract_individual_dates(date_string):
#     """Extract individual dates from concatenated date strings"""
#     if not date_string or pd.isna(date_string):
#         return []
    
#     date_string = str(date_string).strip()
#     dates = []
    
#     # Pattern for dates like "6/1/2025", "06-01-2025", etc.
#     # Try different date patterns
#     patterns = [
#         r'(\d{1,2}/\d{1,2}/\d{4})',  # 6/1/2025
#         r'(\d{2}-\d{2}-\d{4})',      # 06-01-2025
#         r'(\d{1,2}-\d{1,2}-\d{4})',  # 6-1-2025
#         r'(\d{4}-\d{2}-\d{2})',      # 2025-01-06
#     ]
    
#     for pattern in patterns:
#         found_dates = re.findall(pattern, date_string)
#         if found_dates:
#             dates.extend(found_dates)
#             break
    
#     # If no pattern worked, try to split by common separators and validate
#     if not dates:
#         # Try splitting by various separators
#         separators = ['/', '-', '_', ' ', ',']
#         for sep in separators:
#             if sep in date_string:
#                 potential_dates = date_string.split(sep)
#                 # Check if we have date-like components
#                 for i in range(0, len(potential_dates) - 2, 3):
#                     if i + 2 < len(potential_dates):
#                         try:
#                             month, day, year = potential_dates[i:i+3]
#                             if len(year) == 4 and year.isdigit():
#                                 dates.append(f"{month}/{day}/{year}")
#                         except:
#                             continue
#                 break
    
#     return dates

# def get_expected_effort_map():
#     df_effort = load_sheet_data(MASTER_SHEET_ID, "Project Master")
#     df_effort.columns = df_effort.columns.astype(str).str.strip()
#     if "ProjectList" not in df_effort.columns or "Project Effort Plan" not in df_effort.columns:
#         return {}
#     return dict(zip(
#         df_effort["ProjectList"].astype(str).str.strip(),
#         pd.to_numeric(df_effort["Project Effort Plan"], errors="coerce").fillna(0)
#     ))

# def parse_sheet_data_with_split_dates(file_id, sheet_name):
#     """Load and parse sheet data, handling concatenated date columns"""
#     try:
#         result = sheets_service.spreadsheets().values().get(
#             spreadsheetId=file_id,
#             range=sheet_name
#         ).execute()
#         values = result.get('values', [])
        
#         if not values:
#             return pd.DataFrame()
        
#         # Create initial dataframe
#         df = pd.DataFrame(values)
        
#         # Set first row as headers
#         if len(df) > 0:
#             df.columns = df.iloc[0]
#             df = df[1:].reset_index(drop=True)
#             df.dropna(how="all", inplace=True)
        
#         if df.empty:
#             return df
        
#         # Process date columns (skip first column which is project names)
#         project_col = df.columns[0]
#         date_cols = df.columns[1:]
        
#         # Create new dataframe to store split data
#         expanded_data = []
        
#         for _, row in df.iterrows():
#             project = str(row[project_col]).strip()
#             if project.lower() in ["", "nan", "none"]:
#                 continue
            
#             # Process each date column
#             for date_col in date_cols:
#                 date_value = row[date_col]
                
#                 # Skip empty values
#                 if pd.isna(date_value) or str(date_value).strip() in ["", "-", "0"]:
#                     continue
                
#                 # Extract individual dates from the column header
#                 individual_dates = extract_individual_dates(str(date_col))
                
#                 if individual_dates:
#                     # If we found multiple dates, distribute the value
#                     try:
#                         total_value = float(str(date_value).strip())
#                         value_per_date = total_value / len(individual_dates)
                        
#                         for individual_date in individual_dates:
#                             expanded_data.append({
#                                 project_col: project,
#                                 'Date': individual_date,
#                                 'Hours': value_per_date
#                             })
#                     except (ValueError, TypeError):
#                         # If value is not numeric, skip
#                         continue
#                 else:
#                     # If no dates found in header, use the column name as date
#                     try:
#                         hours_value = float(str(date_value).strip())
#                         expanded_data.append({
#                             project_col: project,
#                             'Date': str(date_col),
#                             'Hours': hours_value
#                         })
#                     except (ValueError, TypeError):
#                         continue
        
#         # Create expanded dataframe
#         if expanded_data:
#             expanded_df = pd.DataFrame(expanded_data)
#             return expanded_df
#         else:
#             return pd.DataFrame()
            
#     except Exception as e:
#         print(f"Error parsing sheet data: {e}")
#         return pd.DataFrame()

# def get_designation_effort_by_project(df_all, emp_designation_map, selected_project):
#     df_proj = df_all[df_all["Project"] == selected_project].copy()
#     df_proj["Designation"] = df_proj["Employee ID"].map(emp_designation_map).fillna("Unknown")
#     designation_summary = df_proj.groupby("Designation")["Hours"].sum().reset_index()
#     designation_summary.rename(columns={"Hours": "Total Days"}, inplace=True)
#     return designation_summary

# def get_designation_map():
#     df = load_sheet_data(MASTER_SHEET_ID, EMPLOYEE_SHEET_NAME)
#     df.columns = df.columns.str.strip()
#     if "Employee ID" in df.columns and "Designation" in df.columns:
#         return dict(zip(df["Employee ID"].astype(str).str.strip(), df["Designation"].astype(str).str.strip()))
#     return {}

# def extract_file_id(url):
#     return url.split("/d/")[1].split("/")[0]

# def get_sheet_names(file_id):
#     metadata = sheets_service.spreadsheets().get(spreadsheetId=file_id).execute()
#     return [sheet["properties"]["title"] for sheet in metadata["sheets"]]

# def sort_months_chronologically(months):
#     month_dates = []
#     for month in months:
#         try:
#             if '-' in month:
#                 month_date = datetime.strptime(month, "%B-%y")
#             else:
#                 month_date = datetime.strptime(month, "%B-%Y")
#             month_dates.append((month_date, month))
#         except:
#             try:
#                 month_date = datetime.strptime(month.upper(), "%b-%y")
#                 month_dates.append((month_date, month))
#             except:
#                 month_dates.append((datetime.max, month))
#     month_dates.sort(key=lambda x: x[0])
#     return [month for _, month in month_dates]

# def load_sheet_data(file_id, sheet_name):
#     result = sheets_service.spreadsheets().values().get(
#         spreadsheetId=file_id,
#         range=sheet_name
#     ).execute()
#     values = result.get('values', [])
#     if not values:
#         return pd.DataFrame()
#     df = pd.DataFrame(values)
#     df.columns = df.iloc[0]
#     df = df[1:]
#     df.reset_index(drop=True, inplace=True)
#     df.dropna(how="all", inplace=True)
#     return df

# def get_employee_map():
#     df_map = load_sheet_data(MASTER_SHEET_ID, EMPLOYEE_SHEET_NAME)
#     if df_map.empty or not {"Employee ID", "Employee Name", "Designation"}.issubset(df_map.columns):
#         return {}, {}
#     df_map.columns = df_map.columns.astype(str).str.strip().str.replace('\n', ' ').str.replace('\r', ' ')
#     emp_name_map = dict(zip(df_map["Employee ID"].astype(str).str.strip(), df_map["Employee Name"].astype(str).str.strip()))
#     emp_designation_map = dict(zip(df_map["Employee ID"].astype(str).str.strip(), df_map["Designation"].astype(str).str.strip()))
#     return emp_name_map, emp_designation_map

# def create_month_on_month_project_table(df_all_time, selected_project, current_month, all_months):
#     """
#     Create a month-on-month table showing: [Previous Month 2] [Previous Month 1] [Current Month]
#     For example: If current is August, show: June → July → August
#     """
#     # Get expected effort from Project Master
#     expected_map = get_expected_effort_map()
#     planned_effort = expected_map.get(selected_project, 0)
    
#     print(f"📊 Creating month-on-month for project: {selected_project}")
#     print(f"📅 Current month: {current_month}")
#     print(f"💼 Planned effort from Project Master: {planned_effort}")
    
#     # Filter data for the selected project
#     project_data = df_all_time[df_all_time["Project"] == selected_project].copy()
    
#     if project_data.empty:
#         print("❌ No project data found")
#         return pd.DataFrame(), []
    
#     # Get current month index in chronological order
#     try:
#         current_month_idx = all_months.index(current_month)
#         print(f"📍 Current month index: {current_month_idx}")
#     except ValueError:
#         print(f"❌ Current month {current_month} not found in all_months")
#         return pd.DataFrame(), []
    
#     # Create the 3 months to display: [Month-2] [Month-1] [Current Month]
#     display_months = []
#     month_labels = []
    
#     for offset in [2, 1, 0]:  # 2 months ago, 1 month ago, current month
#         target_idx = current_month_idx - offset
        
#         if target_idx >= 0 and target_idx < len(all_months):
#             # Real month exists
#             month_name = all_months[target_idx]
#             display_months.append(month_name)
#             month_labels.append(month_name)
#         else:
#             # Month doesn't exist - create placeholder
#             placeholder_name = f"NoData-{offset}"
#             display_months.append(placeholder_name)
#             if offset == 2:
#                 month_labels.append("2 Months Ago")
#             elif offset == 1:
#                 month_labels.append("1 Month Ago")
#             else:
#                 month_labels.append("Current")
    
#     print(f"📋 Display months: {display_months}")
#     print(f"🏷️  Month labels: {month_labels}")
    
#     # Get unique resources (employees) from the project data
#     all_project_resources = project_data["Employee Name"].unique()
    
#     if len(all_project_resources) == 0:
#         print("❌ No resources found for project")
#         return pd.DataFrame(), display_months
    
#     print(f"👥 Found {len(all_project_resources)} resources: {list(all_project_resources)}")
    
#     # Create the table structure
#     table_data = []
    
#     for resource in sorted(all_project_resources):
#         resource_data = project_data[project_data["Employee Name"] == resource]
        
#         row = {"Resource": resource}
#         total_effort = 0
        
#         # Add data for each of the 3 months
#         for i, month_name in enumerate(display_months):
#             if month_name.startswith("NoData-"):
#                 # This is a placeholder month (no data available)
#                 row[f"M{i+1}"] = 0.0
#             else:
#                 # Real month - get actual data
#                 month_effort = resource_data[resource_data["Month"] == month_name]["Hours"].sum()
#                 row[f"M{i+1}"] = month_effort
#                 total_effort += month_effort
        
#         row["TOTAL Effort (Man Days)"] = total_effort
        
#         # Planned effort per resource (distribute equally among all resources)
#         planned_per_resource = planned_effort / len(all_project_resources) if len(all_project_resources) > 0 and planned_effort > 0 else 0
#         row["Planned Effort (Man Days)"] = planned_per_resource
        
#         table_data.append(row)
#         print(f"  👤 {resource}: M1={row['M1']}, M2={row['M2']}, M3={row['M3']}, Total={total_effort:.1f}, Planned={planned_per_resource:.1f}")
    
#     # Add Total row - sum all individual resource efforts
#     total_row = {"Resource": "Total"}
#     for i in range(1, 4):  # M1, M2, M3
#         total_row[f"M{i}"] = sum(row[f"M{i}"] for row in table_data)
    
#     # Total effort is sum of all months for all resources
#     total_row["TOTAL Effort (Man Days)"] = sum(row["TOTAL Effort (Man Days)"] for row in table_data)
    
#     # Total planned effort for the entire project (not per resource)
#     total_row["Planned Effort (Man Days)"] = planned_effort
    
#     table_data.append(total_row)
    
#     print(f"📊 Total row: M1={total_row['M1']}, M2={total_row['M2']}, M3={total_row['M3']}")
#     print(f"📈 Grand total effort: {total_row['TOTAL Effort (Man Days)']}")
#     print(f"🎯 Total planned effort: {total_row['Planned Effort (Man Days)']}")
    
#     # Create dataframe
#     df_result = pd.DataFrame(table_data)
    
#     return df_result, month_labels

# # NEW FUNCTIONS FOR OVERALL DASHBOARD

# def create_project_dashboard_month_on_month(df_all_time, current_month, all_months):
#     """
#     Create Project Dashboard: Month on Month for ALL projects
#     """
#     # Get current month index
#     try:
#         current_month_idx = all_months.index(current_month)
#     except ValueError:
#         return pd.DataFrame()
    
#     # Create the 3 months to display: [Month-2] [Month-1] [Current Month]
#     display_months = []
#     month_labels = []
    
#     for offset in [2, 1, 0]:  # 2 months ago, 1 month ago, current month
#         target_idx = current_month_idx - offset
        
#         if target_idx >= 0 and target_idx < len(all_months):
#             month_name = all_months[target_idx]
#             display_months.append(month_name)
#             month_labels.append(month_name)
#         else:
#             placeholder_name = f"NoData-{offset}"
#             display_months.append(placeholder_name)
#             month_labels.append("No Data")
    
#     # Get all unique projects
#     all_projects = sorted(df_all_time["Project"].dropna().unique())
#     expected_map = get_expected_effort_map()
    
#     # Create table data
#     table_data = []
    
#     for project in all_projects:
#         project_data = df_all_time[df_all_time["Project"] == project]
        
#         row = {"Project": project}
#         total_effort = 0
        
#         # Add data for each of the 3 months
#         for i, month_name in enumerate(display_months):
#             if month_name.startswith("NoData-"):
#                 row[f"M{i+1}"] = 0.0
#             else:
#                 month_effort = project_data[project_data["Month"] == month_name]["Hours"].sum()
#                 row[f"M{i+1}"] = month_effort
#                 total_effort += month_effort
        
#         row["Total"] = total_effort
#         row["Effort Planned"] = expected_map.get(project, 0)
        
#         table_data.append(row)
    
#     return pd.DataFrame(table_data), month_labels

# def create_individual_dashboard(df_all_time, current_month, emp_designation_map):
#     """
#     Create Individual Dashboard showing all resources with their designations
#     """
#     # Filter data for current month
#     current_data = df_all_time[df_all_time["Month"] == current_month].copy()
    
#     if current_data.empty:
#         return pd.DataFrame()
    
#     # Add week column
#     def assign_week_simple(date_str):
#         try:
#             date_str = str(date_str).strip()
#             formats = ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"]
            
#             for fmt in formats:
#                 try:
#                     dt = datetime.strptime(date_str, fmt)
#                     day = dt.day
#                     if day <= 7:
#                         return "W1"
#                     elif day <= 14:
#                         return "W2"
#                     elif day <= 21:
#                         return "W3"
#                     else:
#                         return "W4"
#                 except ValueError:
#                     continue
#             return "W1"  # Default
#         except:
#             return "W1"
    
#     current_data["Week"] = current_data["Date"].apply(assign_week_simple)
    
#     # Create pivot table for each employee
#     all_employees = sorted(current_data["Employee Name"].unique())
    
#     table_data = []
    
#     for employee in all_employees:
#         emp_data = current_data[current_data["Employee Name"] == employee]
        
#         # Get designation
#         emp_id = emp_data["Employee ID"].iloc[0] if not emp_data.empty else "Unknown"
#         designation = emp_designation_map.get(emp_id, "Unknown")
        
#         # Create weekly breakdown
#         weekly_pivot = pd.pivot_table(
#             emp_data,
#             values="Hours",
#             columns="Week",
#             aggfunc="sum",
#             fill_value=0
#         )
        
#         row = {
#             "Resource": employee,
#             "Designation": designation,
#             "W1": float(weekly_pivot.get("W1", 0)),
#             "W2": float(weekly_pivot.get("W2", 0)),
#             "W3": float(weekly_pivot.get("W3", 0)),
#             "W4": float(weekly_pivot.get("W4", 0))
#         }
        
#         total_man_days = row["W1"] + row["W2"] + row["W3"] + row["W4"]
#         row["Total (Man Days)"] = float(total_man_days)
        
#         # Utilization calculation (22 working days per month)
#         working_days_per_month = 22
#         utilization = (total_man_days / working_days_per_month * 100) if working_days_per_month > 0 else 0
#         # row["Utilization (%)"] = f"=(Total Man Days/22) *100"
#         row["Utilization (%)"] = f"{utilization:.1f}%"
        
#         table_data.append(row)
    
#     return pd.DataFrame(table_data)

# def analyze_sheets(selected_month):
#     """Analyze sheets with improved date parsing"""
#     employee_data = []
#     emp_map, designation_map = get_employee_map()

#     print(f"🔍 Analyzing month: {selected_month}")

#     for employee_id, url in SHEET_URLS.items():
#         employee_name = emp_map.get(employee_id, "Unknown")
#         file_id = extract_file_id(url)
        
#         print(f"📊 Processing {employee_id} ({employee_name})")
        
#         try:
#             file_sheets = get_sheet_names(file_id)
#             if selected_month not in file_sheets:
#                 print(f"  ❌ Sheet '{selected_month}' not found for {employee_id}")
#                 continue
#         except Exception as e:
#             print(f"  ❌ Error getting sheet names for {employee_id}: {e}")
#             continue
        
#         # Use the new parsing function
#         df = parse_sheet_data_with_split_dates(file_id, selected_month)
        
#         if df.empty:
#             print(f"  ❌ No data found for {employee_id}")
#             continue
        
#         print(f"  ✅ Found {len(df)} records for {employee_id}")
        
#         # Process the already-expanded data
#         for _, row in df.iterrows():
#             project = str(row.iloc[0]).strip()  # First column is project
#             date = str(row['Date']).strip()
#             hours = row['Hours']
            
#             if project.lower() not in ["", "nan", "none"] and hours > 0:
#                 employee_data.append({
#                     "Employee ID": employee_id,
#                     "Employee Name": employee_name,
#                     "Project": project,
#                     "Date": date,
#                     "Hours": float(hours),
#                     "Designation": designation_map.get(employee_id, "Unknown")
#                 })

#     print(f"📈 Total records processed: {len(employee_data)}")
#     return pd.DataFrame(employee_data)

# def analyze_all_months():
#     """Analyze all months with improved date parsing"""
#     all_data = []
#     emp_map, emp_level_map = get_employee_map()

#     for month in all_months:
#         print(f"🔍 Processing all-time data for month: {month}")
#         for emp_id, url in SHEET_URLS.items():
#             emp_name = emp_map.get(emp_id, "Unknown")
#             file_id = extract_file_id(url)

#             try:
#                 file_sheets = get_sheet_names(file_id)
#                 if month not in file_sheets:
#                     continue
#             except Exception as e:
#                 continue

#             # Use the new parsing function
#             df = parse_sheet_data_with_split_dates(file_id, month)
            
#             if df.empty:
#                 continue

#             # Process the already-expanded data
#             for _, row in df.iterrows():
#                 project = str(row.iloc[0]).strip()  # First column is project
#                 date = str(row['Date']).strip()
#                 hours = row['Hours']
                
#                 if project.lower() not in ["", "nan", "none"] and hours > 0:
#                     all_data.append({
#                         "Employee ID": emp_id,
#                         "Employee Name": emp_name,
#                         "Project": project,
#                         "Month": month,
#                         "Date": date,
#                         "Hours": float(hours)
#                     })

#     return pd.DataFrame(all_data)

# def assign_week(date_str):
#     """Assign week based on date string with improved parsing"""
#     try:
#         if not date_str or pd.isna(date_str) or str(date_str).strip() == "":
#             return "Unknown"
        
#         date_str = str(date_str).strip()
        
#         # Try different date formats
#         formats = [
#             "%m/%d/%Y",     # 6/1/2025
#             "%d/%m/%Y",     # 1/6/2025
#             "%Y-%m-%d",     # 2025-01-06
#             "%d-%m-%Y",     # 06-01-2025
#             "%m-%d-%Y",     # 01-06-2025
#             "%m/%d/%y",     # 6/1/25
#             "%d/%m/%y",     # 1/6/25
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
        
#         print(f"⚠️ Could not parse date: {date_str}")
#         return "Unknown"
#     except Exception as e:
#         print(f"⚠️ Error in assign_week: {e}")
#         return "Unknown"

# def add_week_column(df):
#     """Add week column to dataframe"""
#     df = df.copy()
#     df["Week"] = df["Date"].apply(assign_week)
#     # Filter out unknown weeks and return
#     valid_df = df[df["Week"] != "Unknown"]
#     print(f"📅 Week assignment: {len(df)} total → {len(valid_df)} valid")
#     return valid_df

# # --- MAIN LOGIC ---
# # Get all available months
# all_months_raw = []
# for url in SHEET_URLS.values():
#     file_id = extract_file_id(url)
#     try:
#         months = get_sheet_names(file_id)
#         all_months_raw.extend(months)
#     except Exception as e:
#         st.error(f"Error getting sheet names: {e}")

# all_months = sort_months_chronologically(list(set(all_months_raw)))

# # Month selection
# month = st.selectbox("Select Month", all_months)

# if month:
#     # Load data for selected month
#     df_summary = analyze_sheets(month)

#     if df_summary.empty:
#         st.warning("No data found for this month")
#         st.info("This could be due to:")
#         st.write("- Date format issues in the spreadsheets")
#         st.write("- No data entered for this month")
#         st.write("- Connectivity issues with Google Sheets")
#     else:
#         # st.success(f"✅ Found {len(df_summary)} records for {month}")
        
#         # Clean project names
#         df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
#         df_summary = df_summary[~df_summary['Project'].str.match(r'^\d+$')]
#         df_summary = df_summary[df_summary['Project'].str.len() > 2]
        
#         # Add employee composite field
#         if "Employee" not in df_summary.columns:
#             df_summary['Employee'] = df_summary['Employee Name'] + " (" + df_summary['Designation'] + ", " + df_summary['Employee ID'] + ")"

#         # Add week column to summary data (define at top level)
#         df_with_week = add_week_column(df_summary)

#         # --- INDIVIDUAL EMPLOYEE PROJECT BREAKDOWN ---
#         st.subheader("👤 Individual Employee Project Breakdown")
        
#         if not df_with_week.empty:
#             # Employee selection dropdown
#             unique_employees = sorted(df_with_week["Employee Name"].unique())
#             selected_employee = st.selectbox("Select Employee", unique_employees, key="individual_employee")
            
#             if selected_employee:
#                 # Filter data for selected employee
#                 df_employee = df_with_week[df_with_week["Employee Name"] == selected_employee].copy()
                
#                 if not df_employee.empty:
#                     st.subheader(f"📋 Project Breakdown for {selected_employee} - {month}")
                    
#                     # Create pivot table: Projects vs Weeks for the selected employee
#                     employee_table = pd.pivot_table(
#                         df_employee,
#                         values="Hours",
#                         index="Project",
#                         columns="Week",
#                         aggfunc="sum",
#                         fill_value=0
#                     )
                    
#                     # Ensure all weeks are present
#                     for week in ["Week 1", "Week 2", "Week 3", "Week 4"]:
#                         if week not in employee_table.columns:
#                             employee_table[week] = 0
                    
#                     # Reorder columns
#                     employee_table = employee_table[["Week 1", "Week 2", "Week 3", "Week 4"]]
                    
#                     # Add TOTAL column
#                     employee_table["TOTAL (Man Days)"] = employee_table.sum(axis=1)
                    
#                     # Add Utilization (%) column
#                     # Assuming 22 working days in a month as standard
#                     working_days_per_month = 22
#                     employee_table["Utilization (%)"] = (employee_table["TOTAL (Man Days)"] / working_days_per_month * 100).round(2)
                    
#                     # Add Total row
#                     total_row = employee_table.sum(numeric_only=True)
#                     total_row.name = "Total"
#                     # Recalculate total utilization
#                     total_row["Utilization (%)"] = (total_row["TOTAL (Man Days)"] / working_days_per_month * 100).round(2)
#                     employee_table = pd.concat([employee_table, total_row.to_frame().T])
                    
#                     # Sort by total effort (excluding Total row)
#                     employee_table_sorted = employee_table.iloc[:-1].sort_values("TOTAL (Man Days)", ascending=False)
#                     employee_table = pd.concat([employee_table_sorted, employee_table.iloc[[-1]]])
                    
#                     # Display table with custom formatting
#                     def format_table(df):
#                         # Format numeric columns to 1 decimal place except Utilization
#                         styled_df = df.style.format({
#                             "Week 1": "{:.1f}",
#                             "Week 2": "{:.1f}", 
#                             "Week 3": "{:.1f}",
#                             "Week 4": "{:.1f}",
#                             "TOTAL (Man Days)": "{:.1f}",
#                             "Utilization (%)": "{:.2f}%"
#                         })
                        
#                         # Add color coding for utilization
#                         def color_utilization(val):
#                             if pd.isna(val):
#                                 return ""
#                             try:
#                                 num_val = float(str(val).replace('%', ''))
#                                 if num_val < 50:
#                                     return "background-color: #ff9800"  # Very light red
#                                 elif num_val < 80:
#                                     return "background-color: #42a5f5"  # Light red
#                                 elif num_val <= 100:
#                                     return "background-color: #1976d2"  # Medium red
#                                 else:
#                                     return "background-color: #c62828"  # Dark red
#                             except:
#                                 return ""
                        
#                         styled_df = styled_df.applymap(color_utilization, subset=["Utilization (%)"])
#                         return styled_df
                    
#                     st.dataframe(format_table(employee_table), use_container_width=True)
                    
#                     # Add utilization summary
#                     total_utilization = employee_table.loc["Total", "Utilization (%)"]
                    
#                     col1, col2, col3 = st.columns(3)
#                     # with col1:
#                     #     st.metric("Total Hours", f"{employee_table.loc['Total', 'TOTAL (Man Days)']:.1f}")
#                     # with col2:
#                     #     st.metric("Working Days in Month", f"{working_days_per_month}")
#                     # with col3:
#                     #     utilization_color = "normal"
#                     #     if total_utilization < 50:
#                     #         utilization_color = "inverse"
#                     #     elif total_utilization > 100:
#                     #         utilization_color = "off"
                        
#                     #     st.metric(
#                     #         "Overall Utilization", 
#                     #         f"{total_utilization:.2f}%",
#                     #         delta=f"{total_utilization - 100:.2f}% vs 100% target"
#                     #     )
                    
#                     # Utilization interpretation
#                     if total_utilization < 50:
#                         st.warning("🔴 Low Utilization - Employee may need more work allocation")
#                     elif total_utilization > 120:
#                         st.error("🔴 Over-Utilization - Employee may be overloaded")
#                     elif total_utilization > 100:
#                         st.warning("🟡 High Utilization - Monitor workload carefully")
#                     else:
#                         st.success("🟢 Good Utilization - Well balanced workload")
                        
#                 else:
#                     st.info(f"No data found for {selected_employee} in {month}")
#         else:
#             st.warning("No valid date data found for individual employee analysis")

#         # --- WEEKLY BREAKDOWN SECTION (ONLY WEEKLY RESOURCE EFFORT TABLE) ---
#         st.subheader("📅 Weekly Resource Effort Table")
        
#         if not df_with_week.empty:
#             # Project selection for weekly breakdown
#             unique_projects_weekly = sorted(df_with_week["Project"].unique())
#             selected_proj_week = st.selectbox("Select a project for weekly breakdown", unique_projects_weekly, key="weekly_project")

#             if selected_proj_week:
#                 # Filter data for selected project
#                 df_proj_week = df_with_week[df_with_week["Project"] == selected_proj_week].copy()
                
#                 if not df_proj_week.empty:
#                     # 📋 Weekly resource table
#                     st.subheader(f"📋 Weekly Resource Effort Table - {selected_proj_week}")
#                     weekly_table = pd.pivot_table(
#                         df_proj_week,
#                         values="Hours",
#                         index="Employee Name",
#                         columns="Week",
#                         aggfunc="sum",
#                         fill_value=0
#                     )
                    
#                     # Ensure all weeks are present
#                     for week in ["Week 1", "Week 2", "Week 3", "Week 4"]:
#                         if week not in weekly_table.columns:
#                             weekly_table[week] = 0
                    
#                     weekly_table = weekly_table[["Week 1", "Week 2", "Week 3", "Week 4"]]
#                     weekly_table["TOTAL (Man Days)"] = weekly_table.sum(axis=1)
#                     weekly_table = weekly_table.sort_values("TOTAL (Man Days)", ascending=False)
                    
#                     st.dataframe(weekly_table.style.format("{:.1f}"), use_container_width=True)
#                 else:
#                     st.info("No weekly data found for this project in selected month.")
#         else:
#             st.warning("No valid date data found for weekly breakdown")

#         # --- NEW SECTION: OVERALL DASHBOARD ---
#         st.header("📊 Overall Dashboard")
        
#         # Load all time data for dashboard
#         df_all_time = analyze_all_months()
        
#         if not df_all_time.empty:
#             # A. Project Dashboard: Month on Month
#             st.subheader("📋 A. Project Dashboard: Month on Month")
            
#             project_mom_table, project_mom_labels = create_project_dashboard_month_on_month(
#                 df_all_time, month, all_months
#             )
            
#             if not project_mom_table.empty:
#                 # Rename columns to show month names
#                 display_project_table = project_mom_table.copy()
#                 for i, month_label in enumerate(project_mom_labels):
#                     old_col = f"M{i+1}"
#                     if month_label == "No Data":
#                         new_col = f"M{i+1}"
#                     else:
#                         new_col = f"M{i+1}"
                    
#                     if old_col in display_project_table.columns:
#                         display_project_table = display_project_table.rename(columns={old_col: new_col})
                
#                 st.markdown(f"**Timeline:** {project_mom_labels[0]} → {project_mom_labels[1]} → {project_mom_labels[2]}")
                
#                 # Format and display the table
#                 styled_project_table = display_project_table.style.format({
#                     col: "{:.1f}" for col in display_project_table.columns 
#                     if col not in ["Project"] and col in display_project_table.select_dtypes(include=[int, float]).columns
#                 })
                
#                 st.dataframe(styled_project_table, use_container_width=True)
#             else:
#                 st.info("No project data available for dashboard")
            
#             # B. Individual Dashboard
#             st.subheader(f"📋 B. Individual Dashboard: {month}")
            
#             emp_designation_map = get_designation_map()
#             individual_dashboard_table = create_individual_dashboard(
#                 df_all_time, month, emp_designation_map
#             )
            
#             if not individual_dashboard_table.empty:
#                 # Format the table
#                 def format_individual_table(df):
#                     # Create a copy and convert numeric columns only
#                     df_copy = df.copy()
#                     numeric_cols = ["W1", "W2", "W3", "W4", "Total (Man Days)"]
                    
#                     for col in numeric_cols:
#                         if col in df_copy.columns:
#                             df_copy[col] = df_copy[col].round(1)
                    
#                     return df_copy.style.set_properties(**{
#                         'text-align': 'center'
#                     }).set_table_styles([
#                         {'selector': 'th', 'props': [('text-align', 'center')]},
#                         {'selector': 'td', 'props': [('text-align', 'center')]}
#                     ])
                
#                 st.dataframe(individual_dashboard_table, use_container_width=True)
                
#                 # # Add explanation for utilization formula
#                 # with st.expander("ℹ️ Utilization Formula Explanation"):
#                 #     st.write("**Utilization (%) = (Total Man Days / 22) × 100**")
#                 #     st.write("- **22** represents the standard working days in a month")
#                 #     st.write("- **Total Man Days** is the sum of hours worked across all weeks")
#                 #     st.write("- **100%** utilization means the employee worked all available working days")
#             else:
#                 st.info("No individual data available for current month")

#         # --- COMMENTED OUT SECTIONS ---
#         # # --- MULTI PROJECT SEARCH ---
#         # st.markdown("### 🔎 Filter Projects")
#         # all_proj = sorted(df_summary['Project'].unique())
#         # selected_projects = st.multiselect("Select project(s) to analyze", all_proj)

#         # if selected_projects:
#         #     proj_df = df_summary[df_summary['Project'].isin(selected_projects)]
#         #     proj_grouped = proj_df.groupby(['Project', 'Employee', 'Designation'], as_index=False)['Hours'].sum()

#         #     fig_proj = px.bar(proj_grouped, x='Hours', y='Project', color='Employee', text='Hours', barmode='group')
#         #     fig_proj.update_traces(texttemplate='%{text:.1f}', textposition='outside')
#         #     unique_projects = proj_grouped['Project'].nunique()
#         #     fig_proj.update_layout(
#         #         height=max(500, unique_projects * 80),
#         #         plot_bgcolor="#131313",
#         #         paper_bgcolor="#0E1117",
#         #         font=dict(color="white")
#         #     )
#         #     st.plotly_chart(fig_proj, use_container_width=True)

#         # # --- SUMMARY TABLE ---
#         # proj_total = df_summary.groupby('Project')['Hours'].sum().reset_index()
#         # proj_total = proj_total[proj_total['Project'] != '']
#         # proj_total.rename(columns={'Hours': 'Total Days'}, inplace=True)

#         # # Project summary chart
#         # fig = px.bar(
#         #     proj_total,
#         #     x='Total Days',
#         #     y='Project',
#         #     color='Project',
#         #     orientation='h',
#         #     height=500,
#         #     title='Total Days Spent Per Project'
#         # )
#         # fig.update_layout(
#         #     showlegend=True,
#         #     legend_title_text="Project",
#         #     plot_bgcolor="#131313",
#         #     paper_bgcolor="#0E1117",
#         #     bargap=0.3,
#         #     font=dict(color="white"),
#         #     legend=dict(
#         #         orientation="v",
#         #         yanchor="middle",
#         #         y=0.5,
#         #         xanchor="left",
#         #         x=1.02,
#         #         borderwidth=0,
#         #         bgcolor="rgba(0,0,0,0)",
#         #     )
#         # )
#         # st.plotly_chart(fig, use_container_width=True)

#         # # Summary pivot table
#         # pivot = total_summary_table(df_summary)
#         # display_large_table(pivot, f"📊 Employee Project Summary for {month}")

#         # # --- MONTH ON MONTH COMPARISON ---
#         # st.subheader(f"📈 Month-on-Month Comparison for {month}")
#         # curr_index = all_months.index(month)
        
#         # if curr_index == 0:
#         #     st.info(f"This is the first month ({month}) in the data. No previous month available for comparison.")
#         #     emp_df = df_summary.groupby("Employee")["Hours"].sum().reset_index()
#         #     emp_df.rename(columns={"Hours": "Days"}, inplace=True)
#         #     proj_df = df_summary.groupby("Project")["Hours"].sum().reset_index()
#         #     proj_df.rename(columns={"Hours": "Days"}, inplace=True)
            
#         #     display_large_table(emp_df.set_index("Employee"), f"Employee Summary for {month}")
#         #     display_large_table(proj_df.set_index("Project"), f"Project Summary for {month}")
#         # else:
#         #     prev_month = all_months[curr_index - 1]
#         #     df_prev = analyze_sheets(prev_month)
            
#         #     if not df_prev.empty:
#         #         compare_emp_df = compare_months(df_summary, df_prev, current_month=month, previous_month=prev_month)
#         #         compare_proj_df = compare_projects(df_summary, df_prev, current_month=month, previous_month=prev_month)
                
#         #         display_large_table(compare_emp_df, f"📈 Month-on-Month by Employee ({prev_month} vs {month})")
#         #         display_large_table(compare_proj_df, f"📈 Month-on-Month by Project ({prev_month} vs {month})")

#         # --- ALL TIME ANALYSIS (ONLY DESIGNATION-WISE EFFORT) ---
#         # st.subheader("🕓 Total Effort Across All Months")
#         if df_all_time.empty:
#             st.info("No data found across months.")
#         else:
#             df_all_time['Project'] = df_all_time['Project'].astype(str).str.strip()
            
#             # # --- COMMENTED OUT: Chart and variance table ---
#             # proj_overall = df_all_time.groupby('Project')['Hours'].sum().reset_index()
#             # proj_overall = proj_overall[proj_overall['Project'].str.len() > 2]
#             # proj_overall.rename(columns={'Hours': 'Actual Days Spent'}, inplace=True)

#             # # Add expected effort
#             # expected_map = get_expected_effort_map()
#             # proj_overall['Expected Days'] = proj_overall['Project'].map(expected_map).fillna(0)
#             # proj_overall['Variance'] = proj_overall['Actual Days Spent'] - proj_overall['Expected Days']
#             # proj_overall = proj_overall.sort_values(by='Actual Days Spent', ascending=False)

#             # # Chart
#             # fig_all = px.bar(
#             #     proj_overall,
#             #     x="Actual Days Spent",
#             #     y="Project",
#             #     orientation="h",
#             #     color="Project",
#             #     title="Total Days Spent per Project (All Months)"
#             # )
#             # fig_all.update_layout(
#             #     plot_bgcolor="#131313",
#             #     paper_bgcolor="#0E1117",
#             #     font=dict(color="white"),
#             #     showlegend=False
#             # )
#             # st.plotly_chart(fig_all, use_container_width=True)
            
#             # # Display table with variance
#             # st.dataframe(
#             #     proj_overall.style
#             #     .format({"Expected Days": "{:.1f}", "Actual Days Spent": "{:.1f}", "Variance": "{:+.1f}"})
#             #     .background_gradient(subset=["Variance"], cmap="RdYlGn_r")
#             # )

#             # --- DESIGNATION WISE EFFORT (KEPT) ---
#             # st.markdown("### 🧑‍💼 Designation-wise Effort per Project")
#             emp_designation_map = get_designation_map()
            
#             if not df_all_time.empty:
#                 all_projects = sorted(df_all_time["Project"].dropna().unique())
#                 selected_proj = st.selectbox("Select Project", all_projects, key="designation_project")

#                 if selected_proj:
#                     desg_table = get_designation_effort_by_project(df_all_time, emp_designation_map, selected_proj)
#                     # st.dataframe(desg_table.set_index("Designation"), use_container_width=True)
#             else:
#                 st.info("No all-time project data found.")
                
#         # --- COMMENTED OUT: Month-on-Month Project Resource Analysis ---        
#         if not df_all_time.empty:
#             st.subheader("📊 Month-on-Month Project Resource Analysis")
            
#             # Project selection for month-on-month analysis
#             all_projects_mom = sorted(df_all_time["Project"].dropna().unique())
#             selected_project_mom = st.selectbox(
#                 "Select Project for Month-on-Month Analysis", 
#                 all_projects_mom, 
#                 key="mom_project_selection"
#             )
            
#             if selected_project_mom:
#                 # FIXED: Create the month-on-month table with correct logic
#                 mom_table, month_labels = create_month_on_month_project_table(
#                     df_all_time, 
#                     selected_project_mom,
#                     month,  # Current selected month
#                     all_months  # All available months in chronological order
#                 )
                
#                 if not mom_table.empty:
#                     st.markdown(f"#### 📈 Month-on-Month Analysis: {selected_project_mom}")
                    
#                     # Display month information
#                     st.markdown(f"**Months:** M1 ({month_labels[0]}) → M2 ({month_labels[1]}) → M3 ({month_labels[2]})")
                    
#                     # Rename columns to show actual month names in the table
#                     display_table = mom_table.copy()
#                     for i, month_label in enumerate(month_labels):
#                         old_col = f"M{i+1}"
#                         if "Ago" in month_label or month_label in ["Current"]:
#                             new_col = f"M{i+1} ({month_label})"
#                         else:
#                             new_col = f"M{i+1} ({month_label})"
                        
#                         if old_col in display_table.columns:
#                             display_table = display_table.rename(columns={old_col: new_col})
                    
#                     # Display the table with formatting
#                     styled_table = display_table.style.format({
#                         col: "{:.1f}" for col in display_table.columns 
#                         if col not in ["Resource"] and col in display_table.select_dtypes(include=[int, float]).columns
#                     }).background_gradient(
#                         subset=["TOTAL Effort (Man Days)", "Planned Effort (Man Days)"], 
#                         cmap="RdYlGn"
#                     )
                    
#                     st.dataframe(styled_table, use_container_width=True)
                    
#                     # Add variance analysis - only if we have a Total row
#                     # total_rows = display_table[display_table["Resource"] == "Total"]
#                     # if not total_rows.empty:
#                     #     total_actual = total_rows["TOTAL Effort (Man Days)"].iloc[0]
#                     #     total_planned = total_rows["Planned Effort (Man Days)"].iloc[0]
#                     #     variance = total_actual - total_planned
#                     #     variance_pct = (variance / total_planned * 100) if total_planned > 0 else 0
                        
#                     #     # Display variance metrics
#                     #     col1, col2, col3, col4 = st.columns(4)
                        
#                     #     with col1:
#                     #         st.metric("Total Actual Effort", f"{total_actual:.1f} days")
                        
#                     #     with col2:
#                     #         st.metric("Total Planned Effort", f"{total_planned:.1f} days")
                        
#                     #     with col3:
#                     #         st.metric(
#                     #             "Variance", 
#                     #             f"{variance:+.1f} days",
#                     #             delta=f"{variance_pct:+.1f}%"
#                     #         )
                        
#                     #     with col4:
#                     #         if total_planned == 0:
#                     #             status = "❓ No Plan"
#                     #         elif abs(variance_pct) <= 10:
#                     #             status = "✅ On Track"
#                     #         else:
#                     #             status = "⚠️ Off Track"
#                     #         st.metric("Status", status)
                    
#                     # Show explanation of planned effort
                    
                        
#                         # if total_planned > 0:
#                         #     num_resources = len(mom_table) - 1  # Exclude total row
#                         #     planned_per_resource = total_planned / num_resources if num_resources > 0 else 0
#                         #     st.write(f"5. **Per Resource**: {total_planned:.1f} ÷ {num_resources} = {planned_per_resource:.1f} days per resource")
                    
#                     # Resource utilization chart - exclude Total row and only show resources with data
#                     chart_data = display_table[
#                         (display_table["Resource"] != "Total") & 
#                         (display_table["TOTAL Effort (Man Days)"] > 0)
#                     ].copy()
                    
#                     # if not chart_data.empty:
#                     #     fig_resource = px.bar(
#                     #         chart_data,
#                     #         x="Resource",
#                     #         y=["TOTAL Effort (Man Days)", "Planned Effort (Man Days)"],
#                     #         title=f"Actual vs Planned Effort: {selected_project_mom}",
#                     #         barmode="group"
#                     #     )
#                     #     fig_resource.update_layout(
#                     #         plot_bgcolor="#131313",
#                     #         paper_bgcolor="#0E1117",
#                     #         font=dict(color="white")
#                     #     )
#                     #     st.plotly_chart(fig_resource, use_container_width=True)
#                     # else:
#                     #     st.info("No resource data available for chart visualization.")
                        
#                 else:
#                     st.info(f"No data found for project: {selected_project_mom}")
#         else:
#             st.info("No all-time data available for month-on-month analysis.")
