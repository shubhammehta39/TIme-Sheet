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



# ============================================
# PAGE CONFIGURATION
# ============================================

st.set_page_config(
    page_title="TDF Project Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# PROFESSIONAL STYLING
# ============================================

st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
    }
    
    /* Header Styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-weight: 700;
        font-size: 2.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    
    /* Card Styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-left: 4px solid #667eea;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    /* Data Tables */
    .stDataFrame {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox label {
        font-weight: 600;
        font-size: 0.95rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
        border: 2px solid #e2e8f0;
        transition: all 0.3s;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: 2px solid #667eea;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    .status-green {
        background: #d1fae5;
        color: #065f46;
    }
    
    .status-yellow {
        background: #fef3c7;
        color: #92400e;
    }
    
    .status-red {
        background: #fee2e2;
        color: #991b1b;
    }
    
    /* Remove padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Section Headers */
    h2 {
        color: #1e293b;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }
    
    h3 {
        color: #475569;
        font-weight: 600;
        margin-top: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================
# UTILITY FUNCTIONS
# ============================================

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
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=MASTER_SHEET_ID,
            range="Project Master"
        ).execute()
        values = result.get('values', [])
        
        if len(values) < 2:
            return {}
        
        headers = values[1]
        data_rows = values[2:]
        
        df_effort = pd.DataFrame(data_rows, columns=headers)
        
        if df_effort.empty or not {"ProjectList", "Project Effort Plan"}.issubset(df_effort.columns):
            return {}
        
        df_effort.columns = df_effort.columns.astype(str).str.strip()
        
        return dict(zip(
            df_effort["ProjectList"].astype(str).str.strip(),
            pd.to_numeric(df_effort["Project Effort Plan"], errors="coerce").fillna(0)
        ))
    except Exception as e:
        return {}

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
    return dates

def parse_sheet_data_with_split_dates(file_id, sheet_name):
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
            
            individual_dates = extract_individual_dates(str(date_value))
            
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

def get_utilization_status(utilization):
    if utilization < 50:
        return "🔴 Under-utilized", "#ff9800"
    elif utilization < 80:
        return "🟡 Below Target", "#ffc107"
    elif utilization <= 100:
        return "🟢 Optimal", "#4caf50"
    else:
        return "🔴 Over-utilized", "#f44336"

def export_to_excel(dataframe, filename):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=True, sheet_name='Data')
    output.seek(0)
    return output

# ============================================
# MAIN APP
# ============================================

# Header
st.markdown("""
    <div class="main-header">
        <h1>📊 TDF Project Work Tracker</h1>
        <p>Professional Resource & Project Management Dashboard</p>
    </div>
""", unsafe_allow_html=True)

# Load employee maps
emp_name_map, emp_designation_map = get_employee_map_cached()

# Get all months
all_months_raw = []
for emp_id, url in SHEET_URLS.items():
    file_id = extract_file_id(url)
    if not file_id:
        continue
    months = get_sheet_names_cached(file_id)
    all_months_raw.extend(months)

all_months = sort_months_chronologically(list(set(all_months_raw)))

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.markdown("### 🎯 Filters & Controls")
    
    month = st.selectbox(
        "📅 Select Month",
        all_months,
        help="Choose the month to analyze"
    )
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ Data refreshed!")
        st.rerun()
    
    st.markdown("---")
    
    if month:
        with st.spinner("Loading metrics..."):
            df_summary_temp = analyze_sheets(month, all_months, SHEET_URLS, emp_name_map, emp_designation_map)
            
            if not df_summary_temp.empty:
                st.markdown("### 📊 Quick Stats")
                
                total_projects = df_summary_temp['Project'].nunique()
                total_resources = df_summary_temp['Employee Name'].nunique()
                total_hours = df_summary_temp['Hours'].sum()
                avg_util = (total_hours / (total_resources * 22) * 100) if total_resources > 0 else 0
                
                st.metric("Projects", total_projects)
                st.metric("Resources", total_resources)
                st.metric("Total Hours", f"{total_hours:.1f}")
                st.metric("Avg Utilization", f"{avg_util:.1f}%")
    
    st.markdown("---")
    st.caption(f"🕐 Last updated: {datetime.now().strftime('%H:%M')}")

# ============================================
# MAIN CONTENT
# ============================================

if not month:
    st.info("👈 Please select a month from the sidebar to begin analysis.")
    st.stop()

# Load data with spinner
with st.spinner("🔄 Loading data... Please wait."):
    df_all_time = analyze_sheets(month, all_months, SHEET_URLS, emp_name_map, emp_designation_map)
    df_summary = df_all_time[df_all_time['Month'] == month]

if df_summary.empty:
    st.warning(f"⚠️ No data found for {month}")
    st.stop()

# Clean data
df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
df_summary = df_summary[~df_summary['Project'].str.match(r'^\d+$')]
df_summary = df_summary[df_summary['Project'].str.len() > 2]

if "Employee" not in df_summary.columns:
    df_summary['Employee'] = (df_summary['Employee Name'] + " (" +
                             df_summary['Designation'] + ", " + df_summary['Employee ID'] + ")")

df_with_week = add_week_column(df_summary)

# ============================================
# TABS
# ============================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "👥 Resources",
    "📅 Weekly View",
    "📈 Trends",
    "📋 Reports"
])

# ============================================
# TAB 1: OVERVIEW
# ============================================

with tab1:
    st.markdown(f"## 📊 Project Overview - {month}")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_projects = df_summary['Project'].nunique()
    total_hours = df_summary['Hours'].sum()
    avg_hours = df_summary.groupby('Employee Name')['Hours'].sum().mean()
    active_employees = df_summary['Employee Name'].nunique()
    
    with col1:
        st.metric("Active Projects", total_projects, help="Total unique projects this month")
    with col2:
        st.metric("Total Man-Days", f"{total_hours:.1f}", help="Sum of all hours worked")
    with col3:
        st.metric("Avg Hours/Employee", f"{avg_hours:.1f}", help="Average hours per employee")
    with col4:
        st.metric("Active Resources", active_employees, help="Number of employees working")
    
    st.markdown("---")
    
    # Project Summary with Chart
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Project Effort Summary")
        project_summary = df_summary.groupby('Project').agg({
            'Hours': 'sum',
            'Employee Name': 'nunique'
        }).reset_index()
        project_summary.columns = ['Project', 'Total Hours', 'Resources']
        project_summary = project_summary.sort_values('Total Hours', ascending=False).head(15)
        
        st.dataframe(
            project_summary.style.format({'Total Hours': '{:.1f}'})
            .background_gradient(subset=['Total Hours'], cmap='Blues'),
            use_container_width=True,
            height=400
        )
        
        # Download button
        st.download_button(
            label="📥 Download Excel",
            data=export_to_excel(project_summary, f"project_summary_{month}.xlsx"),
            file_name=f"project_summary_{month}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col2:
        st.markdown("### 📊 Top Projects")
        
        # Create pie chart for top projects
        top_10 = project_summary.head(10)
        fig = px.pie(
            top_10,
            values='Total Hours',
            names='Project',
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Purples_r
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            showlegend=False,
            height=400,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================
# TAB 2: RESOURCE ANALYSIS
# ============================================

with tab2:
    st.markdown(f"## 👥 Resource Analysis - {month}")
    
    if not df_with_week.empty:
        # Search box
        search_employee = st.text_input("🔍 Search Employee", placeholder="Type employee name...")
        
        unique_employees = sorted(df_with_week["Employee Name"].unique())
        
        if search_employee:
            unique_employees = [emp for emp in unique_employees if search_employee.lower() in emp.lower()]
        
        selected_employee = st.selectbox(
            "Select Employee",
            unique_employees,
            key="resource_employee"
        )
        
        if selected_employee:
            df_employee = df_with_week[df_with_week["Employee Name"] == selected_employee].copy()
            
            if not df_employee.empty:
                # Employee Stats
                col1, col2, col3, col4 = st.columns(4)
                
                total_hours = df_employee['Hours'].sum()
                projects_count = df_employee['Project'].nunique()
                utilization = (total_hours / 22 * 100)
                status, color = get_utilization_status(utilization)
                
                with col1:
                    st.metric("Total Hours", f"{total_hours:.1f}")
                with col2:
                    st.metric("Projects Involved", projects_count)
                with col3:
                    st.metric("Utilization", f"{utilization:.1f}%")
                with col4:
                    st.markdown(f"<div style='background:{color}; color:white; padding:10px; border-radius:8px; text-align:center; margin-top:20px;'><strong>{status}</strong></div>", unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Weekly breakdown with visualization
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("### 📅 Weekly Project Breakdown")
                    employee_table = pd.pivot_table(
                        df_employee, values="Hours", index="Project",
                        columns="Week", aggfunc="sum", fill_value=0
                    )
                    for week in ["Week 1", "Week 2", "Week 3", "Week 4"]:
                        if week not in employee_table.columns:
                            employee_table[week] = 0
                    employee_table = employee_table[["Week 1", "Week 2", "Week 3", "Week 4"]]
                    employee_table["TOTAL"] = employee_table.sum(axis=1)
                    employee_table["Utilization %"] = (employee_table["TOTAL"] / 22 * 100).round(2)
                    
                    # Sort by total
                    employee_table = employee_table.sort_values("TOTAL", ascending=False)
                    
                    st.dataframe(
                        employee_table.style.format({
                            "Week 1": "{:.1f}", "Week 2": "{:.1f}",
                            "Week 3": "{:.1f}", "Week 4": "{:.1f}",
                            "TOTAL": "{:.1f}", "Utilization %": "{:.1f}%"
                        }).background_gradient(subset=['TOTAL'], cmap='RdYlGn'),
                        use_container_width=True
                    )
                
                with col2:
                    st.markdown("### 📊 Weekly Trend")
                    
                    # Create weekly trend chart
                    weekly_data = df_employee.groupby('Week')['Hours'].sum().reindex(['Week 1', 'Week 2', 'Week 3', 'Week 4'], fill_value=0)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=['W1', 'W2', 'W3', 'W4'],
                        y=weekly_data.values,
                        marker_color=['#667eea', '#764ba2', '#f093fb', '#4facfe'],
                        text=weekly_data.values,
                        texttemplate='%{text:.1f}h',
                        textposition='outside'
                    ))
                    fig.update_layout(
                        showlegend=False,
                        height=300,
                        margin=dict(l=0, r=0, t=30, b=0),
                        yaxis_title="Hours"
                    )
                    st.plotly_chart(fig, use_container_width=True)

# ============================================
# TAB 3: WEEKLY VIEW
# ============================================

with tab3:
    st.markdown(f"## 📅 Weekly Breakdown - {month}")
    
    if not df_with_week.empty:
        # Project Weekly View
        st.markdown("### 📊 Weekly Resource Effort by Project")
        
        unique_projects = sorted(df_with_week["Project"].unique())
        selected_project = st.selectbox("Select Project", unique_projects, key="weekly_project")
        
        if selected_project:
            df_proj = df_with_week[df_with_week["Project"] == selected_project].copy()
            
            if not df_proj.empty:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    weekly_table = pd.pivot_table(
                        df_proj, values="Hours", index="Employee Name",
                        columns="Week", aggfunc="sum", fill_value=0
                    )
                    for week in ["Week 1", "Week 2", "Week 3", "Week 4"]:
                        if week not in weekly_table.columns:
                            weekly_table[week] = 0
                    weekly_table = weekly_table[["Week 1", "Week 2", "Week 3", "Week 4"]]
                    weekly_table["TOTAL"] = weekly_table.sum(axis=1)
                    weekly_table = weekly_table.sort_values("TOTAL", ascending=False)
                    
                    st.dataframe(
                        weekly_table.style.format("{:.1f}")
                        .background_gradient(subset=["TOTAL"], cmap='RdYlGn'),
                        use_container_width=True
                    )
                
                with col2:
                    st.markdown("### 📈 Resource Distribution")
                    
                    # Stacked bar chart for weekly distribution
                    fig = go.Figure()
                    
                    colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe']
                    for i, week in enumerate(['Week 1', 'Week 2', 'Week 3', 'Week 4']):
                        if week in weekly_table.columns:
                            fig.add_trace(go.Bar(
                                name=week,
                                x=weekly_table.index[:5],  # Top 5 employees
                                y=weekly_table[week][:5],
                                marker_color=colors[i]
                            ))
                    
                    fig.update_layout(
                        barmode='stack',
                        height=400,
                        margin=dict(l=0, r=0, t=30, b=0),
                        yaxis_title="Hours",
                        xaxis_title="Employee"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Daily Employee Effort Table
        st.markdown("### 🗓️ Daily Employee Effort Table")
        
        all_employees = sorted(df_with_week["Employee Name"].unique())
        selected_emp_daily = st.selectbox("Select Employee for Daily View", all_employees, key="daily_emp")
        
        if selected_emp_daily:
            emp_data = df_with_week[df_with_week["Employee Name"] == selected_emp_daily].copy()
            emp_data['Date_parsed'] = pd.to_datetime(emp_data["Date"], errors='coerce')
            emp_data = emp_data[~emp_data['Date_parsed'].isna()]
            
            if not emp_data.empty:
                # Get all unique dates and create weeks
                dates = emp_data['Date_parsed'].sort_values().unique()
                if len(dates) > 0:
                    min_date = pd.Timestamp(dates[0])
                    max_date = pd.Timestamp(dates[-1])
                    
                    weeks = []
                    curr = min_date
                    while curr <= max_date:
                        week_end = curr + pd.Timedelta(days=6)
                        weeks.append((curr, week_end))
                        curr = week_end + pd.Timedelta(days=1)
                    
                    if weeks:
                        # Week navigation
                        if f"{selected_emp_daily}_week_pos" not in st.session_state:
                            st.session_state[f"{selected_emp_daily}_week_pos"] = 0
                        
                        total_weeks = len(weeks)
                        
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col1:
                            if st.button("◀ Previous", key=f"prev_{selected_emp_daily}",
                                       disabled=st.session_state[f"{selected_emp_daily}_week_pos"]==0):
                                st.session_state[f"{selected_emp_daily}_week_pos"] -= 1
                        with col2:
                            week_start, week_end = weeks[st.session_state[f"{selected_emp_daily}_week_pos"]]
                            st.markdown(f"<div style='text-align:center; padding:10px; background:#667eea; color:white; border-radius:8px;'><strong>Week {st.session_state[f'{selected_emp_daily}_week_pos'] + 1} of {total_weeks}</strong><br>{week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}</div>", unsafe_allow_html=True)
                        with col3:
                            if st.button("Next ▶", key=f"next_{selected_emp_daily}",
                                       disabled=st.session_state[f"{selected_emp_daily}_week_pos"]==(total_weeks-1)):
                                st.session_state[f"{selected_emp_daily}_week_pos"] += 1
                        
                        # Filter data for current week
                        week_start, week_end = weeks[st.session_state[f"{selected_emp_daily}_week_pos"]]
                        mask = (emp_data["Date_parsed"] >= week_start) & (emp_data["Date_parsed"] <= week_end)
                        week_df = emp_data[mask].copy()
                        
                        if not week_df.empty:
                            week_df["Date_formatted"] = week_df["Date_parsed"].dt.strftime("%a %d-%b")
                            displayed_cols = [(week_start + pd.Timedelta(days=i)).strftime("%a %d-%b") for i in range(7)]
                            
                            result_pivot = pd.pivot_table(
                                week_df,
                                values="Hours",
                                index="Project",
                                columns="Date_formatted",
                                aggfunc="sum",
                                fill_value=0
                            )
                            
                            for col in displayed_cols:
                                if col not in result_pivot.columns:
                                    result_pivot[col] = 0
                            
                            result_pivot = result_pivot[displayed_cols]
                            result_pivot["TOTAL"] = result_pivot.sum(axis=1)
                            result_pivot = result_pivot.sort_values("TOTAL", ascending=False)
                            
                            st.dataframe(
                                result_pivot.style.format("{:.1f}")
                                .background_gradient(subset=["TOTAL"], cmap='Blues'),
                                use_container_width=True
                            )
                        else:
                            st.info("No data for this week")

# ============================================
# TAB 4: TRENDS & ANALYTICS
# ============================================

with tab4:
    st.markdown("## 📈 Month-on-Month Trends")
    
    # Load all months data
    with st.spinner("Loading trend data..."):
        df_all_months = analyze_all_months(all_months, SHEET_URLS, emp_name_map, emp_designation_map)
    
    if not df_all_months.empty:
        # Project MoM Analysis
        st.markdown("### 📊 Project Resource Analysis")
        
        all_projects = sorted(df_all_months["Project"].dropna().unique())
        selected_proj_mom = st.selectbox("Select Project", all_projects, key="mom_project")
        
        if selected_proj_mom:
            try:
                current_month_idx = all_months.index(month)
                display_months = []
                month_labels = []
                
                for offset in [2, 1, 0]:
                    target_idx = current_month_idx - offset
                    if 0 <= target_idx < len(all_months):
                        month_name = all_months[target_idx]
                        display_months.append(month_name)
                        month_labels.append(month_name)
                
                if len(display_months) >= 2:
                    project_data = df_all_months[df_all_months["Project"] == selected_proj_mom]
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Create MoM table
                        all_resources = sorted(project_data["Employee Name"].unique())
                        table_data = []
                        
                        for resource in all_resources:
                            resource_data = project_data[project_data["Employee Name"] == resource]
                            row = {"Resource": resource}
                            
                            for i, month_name in enumerate(display_months):
                                month_effort = resource_data[resource_data["Month"] == month_name]["Hours"].sum()
                                row[month_labels[i]] = month_effort
                            
                            row["TOTAL"] = sum([row[m] for m in month_labels])
                            table_data.append(row)
                        
                        mom_table = pd.DataFrame(table_data)
                        
                        if not mom_table.empty:
                            # Add totals row
                            total_row = {"Resource": "TOTAL"}
                            for m in month_labels:
                                total_row[m] = mom_table[m].sum()
                            total_row["TOTAL"] = mom_table["TOTAL"].sum()
                            
                            mom_table = pd.concat([mom_table, pd.DataFrame([total_row])], ignore_index=True)
                            
                            st.dataframe(
                                mom_table.style.format({col: "{:.1f}" for col in month_labels + ["TOTAL"]})
                                .background_gradient(subset=month_labels + ["TOTAL"], cmap='RdYlGn'),
                                use_container_width=True
                            )
                    
                    with col2:
                        st.markdown("### 📈 Effort Trend")
                        
                        # Line chart for trend
                        trend_data = []
                        for m in month_labels:
                            total = mom_table[mom_table["Resource"] == "TOTAL"][m].values[0]
                            trend_data.append(total)
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=month_labels,
                            y=trend_data,
                            mode='lines+markers+text',
                            marker=dict(size=12, color='#667eea'),
                            line=dict(width=3, color='#764ba2'),
                            text=[f"{v:.1f}h" for v in trend_data],
                            textposition="top center"
                        ))
                        fig.update_layout(
                            height=300,
                            margin=dict(l=0, r=0, t=30, b=0),
                            yaxis_title="Total Hours",
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
            except ValueError:
                st.warning("Current month not found in available months")
        
        st.markdown("---")
        
        # Overall utilization trend
        st.markdown("### 📊 Overall Team Utilization Trend")
        
        # Calculate monthly utilization
        monthly_util = []
        for m in all_months[-6:]:  # Last 6 months
            month_data = df_all_months[df_all_months["Month"] == m]
            if not month_data.empty:
                total_hours = month_data["Hours"].sum()
                total_employees = month_data["Employee Name"].nunique()
                util = (total_hours / (total_employees * 22) * 100) if total_employees > 0 else 0
                monthly_util.append({"Month": m, "Utilization": util})
        
        if monthly_util:
            util_df = pd.DataFrame(monthly_util)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=util_df["Month"],
                y=util_df["Utilization"],
                marker_color=['#4caf50' if u >= 80 and u <= 100 else '#ffc107' if u >= 50 else '#f44336' for u in util_df["Utilization"]],
                text=[f"{u:.1f}%" for u in util_df["Utilization"]],
                textposition='outside'
            ))
            
            # Add target line
            fig.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Target: 80%")
            
            fig.update_layout(
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
                yaxis_title="Utilization %",
                xaxis_title="Month",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

# ============================================
# TAB 5: REPORTS & DASHBOARDS
# ============================================

with tab5:
    st.markdown("## 📋 Executive Reports")
    
    # Project Dashboard
    st.markdown("### A. Project Dashboard: Month on Month")
    
    with st.spinner("Generating project dashboard..."):
        df_all_months_proj = analyze_all_months(all_months, SHEET_URLS, emp_name_map, emp_designation_map)
        
        if not df_all_months_proj.empty:
            try:
                current_month_idx = all_months.index(month)
                display_months = []
                month_labels = []
                
                for offset in [2, 1, 0]:
                    target_idx = current_month_idx - offset
                    if 0 <= target_idx < len(all_months):
                        month_name = all_months[target_idx]
                        display_months.append(month_name)
                        month_labels.append(month_name)
                
                if display_months:
                    st.markdown(f"**Timeline:** {' → '.join(month_labels)}")
                    
                    all_projects = sorted(df_all_months_proj["Project"].dropna().unique())
                    expected_map = get_expected_effort_map_cached()
                    
                    table_data = []
                    for project in all_projects:
                        project_data = df_all_months_proj[df_all_months_proj["Project"] == project]
                        row = {"Project": project}
                        
                        for i, month_name in enumerate(display_months):
                            month_effort = project_data[project_data["Month"] == month_name]["Hours"].sum()
                            row[f"M{i+1}"] = month_effort
                        
                        row["Total"] = sum([row[f"M{i+1}"] for i in range(len(display_months))])
                        row["Planned"] = expected_map.get(project, 0)
                        row["Variance"] = row["Total"] - row["Planned"]
                        
                        table_data.append(row)
                    
                    project_dashboard = pd.DataFrame(table_data)
                    project_dashboard = project_dashboard.sort_values("Total", ascending=False)
                    
                    # Rename columns
                    for i, label in enumerate(month_labels):
                        project_dashboard = project_dashboard.rename(columns={f"M{i+1}": label})
                    
                    # Style the dataframe
                    def color_variance(val):
                        if pd.isna(val) or val == 0:
                            return ''
                        color = '#d1fae5' if val >= 0 else '#fee2e2'
                        return f'background-color: {color}'
                    
                    st.dataframe(
                        project_dashboard.style.format({
                            col: "{:.1f}" for col in month_labels + ["Total", "Planned", "Variance"]
                        })
                        .applymap(color_variance, subset=["Variance"])
                        .background_gradient(subset=["Total"], cmap='Blues'),
                        use_container_width=True,
                        height=500
                    )
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Project Dashboard",
                        data=export_to_excel(project_dashboard, f"project_dashboard_{month}.xlsx"),
                        file_name=f"project_dashboard_{month}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
            except ValueError:
                st.warning("Current month not found")
    
    st.markdown("---")
    
    # Individual Dashboard
    st.markdown("### B. Individual Resource Dashboard")
    
    with st.spinner("Generating individual dashboard..."):
        current_data = df_all_months_proj[df_all_months_proj["Month"] == month].copy()
        
        if not current_data.empty:
            def assign_week_simple(date_str):
                try:
                    date_str = str(date_str).strip()
                    formats = ["%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
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
                row["Total"] = float(total_man_days)
                utilization = (total_man_days / 22 * 100) if 22 > 0 else 0
                row["Utilization %"] = f"{utilization:.1f}%"
                
                table_data.append(row)
            
            individual_dashboard = pd.DataFrame(table_data)
            individual_dashboard = individual_dashboard.sort_values("Total", ascending=False)
            
            # Color coding for utilization
            def color_utilization(val):
                if isinstance(val, str) and '%' in val:
                    try:
                        num_val = float(val.replace('%', ''))
                        if num_val < 50:
                            return 'background-color: #fee2e2; color: #991b1b'
                        elif num_val < 80:
                            return 'background-color: #fef3c7; color: #92400e'
                        elif num_val <= 100:
                            return 'background-color: #d1fae5; color: #065f46'
                        else:
                            return 'background-color: #fee2e2; color: #991b1b'
                    except:
                        return ''
                return ''
            
            st.dataframe(
                individual_dashboard.style.format({
                    "W1": "{:.1f}", "W2": "{:.1f}",
                    "W3": "{:.1f}", "W4": "{:.1f}",
                    "Total": "{:.1f}"
                })
                .applymap(color_utilization, subset=["Utilization %"])
                .background_gradient(subset=["Total"], cmap='Blues'),
                use_container_width=True,
                height=500
            )
            
            # Download button
            st.download_button(
                label="📥 Download Individual Dashboard",
                data=export_to_excel(individual_dashboard, f"individual_dashboard_{month}.xlsx"),
                file_name=f"individual_dashboard_{month}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.markdown(f"""
    <div style='text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; margin-top: 50px;'>
        <h3 style='color: white; margin: 0;'>📊 TDF Project Tracker Dashboard</h3>
        <p style='margin: 10px 0; opacity: 0.9;'>Version 1.0 | Professional Resource Management System</p>
        <p style='margin: 5px 0; font-size: 0.9em;'>
            Last Updated: {datetime.now().strftime("%B %d, %Y at %H:%M")}
        </p>
        <p style='margin: 15px 0 0 0; font-size: 0.85em; opacity: 0.8;'>
            © 2025 TDF. All rights reserved.
        </p>
    </div>
""", unsafe_allow_html=True)
