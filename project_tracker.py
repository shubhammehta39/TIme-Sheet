import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import time
import io
import plotly.io as pio
from dotenv import load_dotenv
import os

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
load_dotenv()  # loads .env file into environment variables
MASTER_SHEET_ID = os.getenv("MASTER_ID")

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
def extract_individual_dates(date_string):
    """Extract individual dates from concatenated date strings"""
    if not date_string or pd.isna(date_string):
        return []
    
    date_string = str(date_string).strip()
    dates = []
    
    # Pattern for dates like "6/1/2025", "06-01-2025", etc.
    # Try different date patterns
    patterns = [
        r'(\d{1,2}/\d{1,2}/\d{4})',  # 6/1/2025
        r'(\d{2}-\d{2}-\d{4})',      # 06-01-2025
        r'(\d{1,2}-\d{1,2}-\d{4})',  # 6-1-2025
        r'(\d{4}-\d{2}-\d{2})',      # 2025-01-06
    ]
    
    for pattern in patterns:
        found_dates = re.findall(pattern, date_string)
        if found_dates:
            dates.extend(found_dates)
            break
    
    # If no pattern worked, try to split by common separators and validate
    if not dates:
        # Try splitting by various separators
        separators = ['/', '-', '_', ' ', ',']
        for sep in separators:
            if sep in date_string:
                potential_dates = date_string.split(sep)
                # Check if we have date-like components
                for i in range(0, len(potential_dates) - 2, 3):
                    if i + 2 < len(potential_dates):
                        try:
                            month, day, year = potential_dates[i:i+3]
                            if len(year) == 4 and year.isdigit():
                                dates.append(f"{month}/{day}/{year}")
                        except:
                            continue
                break
    
    return dates

def get_expected_effort_map():
    df_effort = load_sheet_data(MASTER_SHEET_ID, "Project Master")
    df_effort.columns = df_effort.columns.astype(str).str.strip()
    if "ProjectList" not in df_effort.columns or "Project Effort Plan" not in df_effort.columns:
        return {}
    return dict(zip(
        df_effort["ProjectList"].astype(str).str.strip(),
        pd.to_numeric(df_effort["Project Effort Plan"], errors="coerce").fillna(0)
    ))

def parse_sheet_data_with_split_dates(file_id, sheet_name):
    """Load and parse sheet data, handling concatenated date columns"""
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=file_id,
            range=sheet_name
        ).execute()
        values = result.get('values', [])
        
        if not values:
            return pd.DataFrame()
        
        # Create initial dataframe
        df = pd.DataFrame(values)
        
        # Set first row as headers
        if len(df) > 0:
            df.columns = df.iloc[0]
            df = df[1:].reset_index(drop=True)
            df.dropna(how="all", inplace=True)
        
        if df.empty:
            return df
        
        # Process date columns (skip first column which is project names)
        project_col = df.columns[0]
        date_cols = df.columns[1:]
        
        # Create new dataframe to store split data
        expanded_data = []
        
        for _, row in df.iterrows():
            project = str(row[project_col]).strip()
            if project.lower() in ["", "nan", "none"]:
                continue
            
            # Process each date column
            for date_col in date_cols:
                date_value = row[date_col]
                
                # Skip empty values
                if pd.isna(date_value) or str(date_value).strip() in ["", "-", "0"]:
                    continue
                
                # Extract individual dates from the column header
                individual_dates = extract_individual_dates(str(date_col))
                
                if individual_dates:
                    # If we found multiple dates, distribute the value
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
                        # If value is not numeric, skip
                        continue
                else:
                    # If no dates found in header, use the column name as date
                    try:
                        hours_value = float(str(date_value).strip())
                        expanded_data.append({
                            project_col: project,
                            'Date': str(date_col),
                            'Hours': hours_value
                        })
                    except (ValueError, TypeError):
                        continue
        
        # Create expanded dataframe
        if expanded_data:
            expanded_df = pd.DataFrame(expanded_data)
            return expanded_df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error parsing sheet data: {e}")
        return pd.DataFrame()

def get_designation_effort_by_project(df_all, emp_designation_map, selected_project):
    df_proj = df_all[df_all["Project"] == selected_project].copy()
    df_proj["Designation"] = df_proj["Employee ID"].map(emp_designation_map).fillna("Unknown")
    designation_summary = df_proj.groupby("Designation")["Hours"].sum().reset_index()
    designation_summary.rename(columns={"Hours": "Total Days"}, inplace=True)
    return designation_summary

def get_designation_map():
    df = load_sheet_data(MASTER_SHEET_ID, EMPLOYEE_SHEET_NAME)
    df.columns = df.columns.str.strip()
    if "Employee ID" in df.columns and "Designation" in df.columns:
        return dict(zip(df["Employee ID"].astype(str).str.strip(), df["Designation"].astype(str).str.strip()))
    return {}

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

def get_employee_map():
    df_map = load_sheet_data(MASTER_SHEET_ID, EMPLOYEE_SHEET_NAME)
    if df_map.empty or not {"Employee ID", "Employee Name", "Designation"}.issubset(df_map.columns):
        return {}, {}
    df_map.columns = df_map.columns.astype(str).str.strip().str.replace('\n', ' ').str.replace('\r', ' ')
    emp_name_map = dict(zip(df_map["Employee ID"].astype(str).str.strip(), df_map["Employee Name"].astype(str).str.strip()))
    emp_designation_map = dict(zip(df_map["Employee ID"].astype(str).str.strip(), df_map["Designation"].astype(str).str.strip()))
    return emp_name_map, emp_designation_map

def create_month_on_month_project_table(df_all_time, selected_project, current_month, all_months):
    """
    Create a month-on-month table showing: [Previous Month 2] [Previous Month 1] [Current Month]
    For example: If current is August, show: June → July → August
    """
    # Get expected effort from Project Master
    expected_map = get_expected_effort_map()
    planned_effort = expected_map.get(selected_project, 0)
    
    print(f"📊 Creating month-on-month for project: {selected_project}")
    print(f"📅 Current month: {current_month}")
    print(f"💼 Planned effort from Project Master: {planned_effort}")
    
    # Filter data for the selected project
    project_data = df_all_time[df_all_time["Project"] == selected_project].copy()
    
    if project_data.empty:
        print("❌ No project data found")
        return pd.DataFrame(), []
    
    # Get current month index in chronological order
    try:
        current_month_idx = all_months.index(current_month)
        print(f"📍 Current month index: {current_month_idx}")
    except ValueError:
        print(f"❌ Current month {current_month} not found in all_months")
        return pd.DataFrame(), []
    
    # Create the 3 months to display: [Month-2] [Month-1] [Current Month]
    display_months = []
    month_labels = []
    
    for offset in [2, 1, 0]:  # 2 months ago, 1 month ago, current month
        target_idx = current_month_idx - offset
        
        if target_idx >= 0 and target_idx < len(all_months):
            # Real month exists
            month_name = all_months[target_idx]
            display_months.append(month_name)
            month_labels.append(month_name)
        else:
            # Month doesn't exist - create placeholder
            placeholder_name = f"NoData-{offset}"
            display_months.append(placeholder_name)
            if offset == 2:
                month_labels.append("2 Months Ago")
            elif offset == 1:
                month_labels.append("1 Month Ago")
            else:
                month_labels.append("Current")
    
    print(f"📋 Display months: {display_months}")
    print(f"🏷️  Month labels: {month_labels}")
    
    # Get unique resources (employees) from the project data
    all_project_resources = project_data["Employee Name"].unique()
    
    if len(all_project_resources) == 0:
        print("❌ No resources found for project")
        return pd.DataFrame(), display_months
    
    print(f"👥 Found {len(all_project_resources)} resources: {list(all_project_resources)}")
    
    # Create the table structure
    table_data = []
    
    for resource in sorted(all_project_resources):
        resource_data = project_data[project_data["Employee Name"] == resource]
        
        row = {"Resource": resource}
        total_effort = 0
        
        # Add data for each of the 3 months
        for i, month_name in enumerate(display_months):
            if month_name.startswith("NoData-"):
                # This is a placeholder month (no data available)
                row[f"M{i+1}"] = 0.0
            else:
                # Real month - get actual data
                month_effort = resource_data[resource_data["Month"] == month_name]["Hours"].sum()
                row[f"M{i+1}"] = month_effort
                total_effort += month_effort
        
        row["TOTAL Effort (Man Days)"] = total_effort
        
        # Planned effort per resource (distribute equally among all resources)
        planned_per_resource = planned_effort / len(all_project_resources) if len(all_project_resources) > 0 and planned_effort > 0 else 0
        row["Planned Effort (Man Days)"] = planned_per_resource
        
        table_data.append(row)
        print(f"  👤 {resource}: M1={row['M1']}, M2={row['M2']}, M3={row['M3']}, Total={total_effort:.1f}, Planned={planned_per_resource:.1f}")
    
    # Add Total row - sum all individual resource efforts
    total_row = {"Resource": "Total"}
    for i in range(1, 4):  # M1, M2, M3
        total_row[f"M{i}"] = sum(row[f"M{i}"] for row in table_data)
    
    # Total effort is sum of all months for all resources
    total_row["TOTAL Effort (Man Days)"] = sum(row["TOTAL Effort (Man Days)"] for row in table_data)
    
    # Total planned effort for the entire project (not per resource)
    total_row["Planned Effort (Man Days)"] = planned_effort
    
    table_data.append(total_row)
    
    print(f"📊 Total row: M1={total_row['M1']}, M2={total_row['M2']}, M3={total_row['M3']}")
    print(f"📈 Grand total effort: {total_row['TOTAL Effort (Man Days)']}")
    print(f"🎯 Total planned effort: {total_row['Planned Effort (Man Days)']}")
    
    # Create dataframe
    df_result = pd.DataFrame(table_data)
    
    return df_result, month_labels

# NEW FUNCTIONS FOR OVERALL DASHBOARD

def create_project_dashboard_month_on_month(df_all_time, current_month, all_months):
    """
    Create Project Dashboard: Month on Month for ALL projects
    """
    # Get current month index
    try:
        current_month_idx = all_months.index(current_month)
    except ValueError:
        return pd.DataFrame()
    
    # Create the 3 months to display: [Month-2] [Month-1] [Current Month]
    display_months = []
    month_labels = []
    
    for offset in [2, 1, 0]:  # 2 months ago, 1 month ago, current month
        target_idx = current_month_idx - offset
        
        if target_idx >= 0 and target_idx < len(all_months):
            month_name = all_months[target_idx]
            display_months.append(month_name)
            month_labels.append(month_name)
        else:
            placeholder_name = f"NoData-{offset}"
            display_months.append(placeholder_name)
            month_labels.append("No Data")
    
    # Get all unique projects
    all_projects = sorted(df_all_time["Project"].dropna().unique())
    expected_map = get_expected_effort_map()
    
    # Create table data
    table_data = []
    
    for project in all_projects:
        project_data = df_all_time[df_all_time["Project"] == project]
        
        row = {"Project": project}
        total_effort = 0
        
        # Add data for each of the 3 months
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

def create_individual_dashboard(df_all_time, current_month, emp_designation_map):
    """
    Create Individual Dashboard showing all resources with their designations
    """
    # Filter data for current month
    current_data = df_all_time[df_all_time["Month"] == current_month].copy()
    
    if current_data.empty:
        return pd.DataFrame()
    
    # Add week column
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
            return "W1"  # Default
        except:
            return "W1"
    
    current_data["Week"] = current_data["Date"].apply(assign_week_simple)
    
    # Create pivot table for each employee
    all_employees = sorted(current_data["Employee Name"].unique())
    
    table_data = []
    
    for employee in all_employees:
        emp_data = current_data[current_data["Employee Name"] == employee]
        
        # Get designation
        emp_id = emp_data["Employee ID"].iloc[0] if not emp_data.empty else "Unknown"
        designation = emp_designation_map.get(emp_id, "Unknown")
        
        # Create weekly breakdown
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
        
        # Utilization calculation (22 working days per month)
        working_days_per_month = 22
        utilization = (total_man_days / working_days_per_month * 100) if working_days_per_month > 0 else 0
        # row["Utilization (%)"] = f"=(Total Man Days/22) *100"
        row["Utilization (%)"] = f"{utilization:.1f}%"
        
        table_data.append(row)
    
    return pd.DataFrame(table_data)

def analyze_sheets(selected_month):
    """Analyze sheets with improved date parsing"""
    employee_data = []
    emp_map, designation_map = get_employee_map()

    print(f"🔍 Analyzing month: {selected_month}")

    for employee_id, url in SHEET_URLS.items():
        employee_name = emp_map.get(employee_id, "Unknown")
        file_id = extract_file_id(url)
        
        print(f"📊 Processing {employee_id} ({employee_name})")
        
        try:
            file_sheets = get_sheet_names(file_id)
            if selected_month not in file_sheets:
                print(f"  ❌ Sheet '{selected_month}' not found for {employee_id}")
                continue
        except Exception as e:
            print(f"  ❌ Error getting sheet names for {employee_id}: {e}")
            continue
        
        # Use the new parsing function
        df = parse_sheet_data_with_split_dates(file_id, selected_month)
        
        if df.empty:
            print(f"  ❌ No data found for {employee_id}")
            continue
        
        print(f"  ✅ Found {len(df)} records for {employee_id}")
        
        # Process the already-expanded data
        for _, row in df.iterrows():
            project = str(row.iloc[0]).strip()  # First column is project
            date = str(row['Date']).strip()
            hours = row['Hours']
            
            if project.lower() not in ["", "nan", "none"] and hours > 0:
                employee_data.append({
                    "Employee ID": employee_id,
                    "Employee Name": employee_name,
                    "Project": project,
                    "Date": date,
                    "Hours": float(hours),
                    "Designation": designation_map.get(employee_id, "Unknown")
                })

    print(f"📈 Total records processed: {len(employee_data)}")
    return pd.DataFrame(employee_data)

def analyze_all_months():
    """Analyze all months with improved date parsing"""
    all_data = []
    emp_map, emp_level_map = get_employee_map()

    for month in all_months:
        print(f"🔍 Processing all-time data for month: {month}")
        for emp_id, url in SHEET_URLS.items():
            emp_name = emp_map.get(emp_id, "Unknown")
            file_id = extract_file_id(url)

            try:
                file_sheets = get_sheet_names(file_id)
                if month not in file_sheets:
                    continue
            except Exception as e:
                continue

            # Use the new parsing function
            df = parse_sheet_data_with_split_dates(file_id, month)
            
            if df.empty:
                continue

            # Process the already-expanded data
            for _, row in df.iterrows():
                project = str(row.iloc[0]).strip()  # First column is project
                date = str(row['Date']).strip()
                hours = row['Hours']
                
                if project.lower() not in ["", "nan", "none"] and hours > 0:
                    all_data.append({
                        "Employee ID": emp_id,
                        "Employee Name": emp_name,
                        "Project": project,
                        "Month": month,
                        "Date": date,
                        "Hours": float(hours)
                    })

    return pd.DataFrame(all_data)

def assign_week(date_str):
    """Assign week based on date string with improved parsing"""
    try:
        if not date_str or pd.isna(date_str) or str(date_str).strip() == "":
            return "Unknown"
        
        date_str = str(date_str).strip()
        
        # Try different date formats
        formats = [
            "%m/%d/%Y",     # 6/1/2025
            "%d/%m/%Y",     # 1/6/2025
            "%Y-%m-%d",     # 2025-01-06
            "%d-%m-%Y",     # 06-01-2025
            "%m-%d-%Y",     # 01-06-2025
            "%m/%d/%y",     # 6/1/25
            "%d/%m/%y",     # 1/6/25
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
        
        print(f"⚠️ Could not parse date: {date_str}")
        return "Unknown"
    except Exception as e:
        print(f"⚠️ Error in assign_week: {e}")
        return "Unknown"

def add_week_column(df):
    """Add week column to dataframe"""
    df = df.copy()
    df["Week"] = df["Date"].apply(assign_week)
    # Filter out unknown weeks and return
    valid_df = df[df["Week"] != "Unknown"]
    print(f"📅 Week assignment: {len(df)} total → {len(valid_df)} valid")
    return valid_df

# --- MAIN LOGIC ---
# Get all available months
all_months_raw = []
for url in SHEET_URLS.values():
    file_id = extract_file_id(url)
    try:
        months = get_sheet_names(file_id)
        all_months_raw.extend(months)
    except Exception as e:
        st.error(f"Error getting sheet names: {e}")

all_months = sort_months_chronologically(list(set(all_months_raw)))

# Month selection
month = st.selectbox("Select Month", all_months)

if month:
    # Load data for selected month
    df_summary = analyze_sheets(month)

    if df_summary.empty:
        st.warning("No data found for this month")
        st.info("This could be due to:")
        st.write("- Date format issues in the spreadsheets")
        st.write("- No data entered for this month")
        st.write("- Connectivity issues with Google Sheets")
    else:
        # st.success(f"✅ Found {len(df_summary)} records for {month}")
        
        # Clean project names
        df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
        df_summary = df_summary[~df_summary['Project'].str.match(r'^\d+$')]
        df_summary = df_summary[df_summary['Project'].str.len() > 2]
        
        # Add employee composite field
        if "Employee" not in df_summary.columns:
            df_summary['Employee'] = df_summary['Employee Name'] + " (" + df_summary['Designation'] + ", " + df_summary['Employee ID'] + ")"

        # Add week column to summary data (define at top level)
        df_with_week = add_week_column(df_summary)

        # --- INDIVIDUAL EMPLOYEE PROJECT BREAKDOWN ---
        st.subheader("👤 Individual Employee Project Breakdown")
        
        if not df_with_week.empty:
            # Employee selection dropdown
            unique_employees = sorted(df_with_week["Employee Name"].unique())
            selected_employee = st.selectbox("Select Employee", unique_employees, key="individual_employee")
            
            if selected_employee:
                # Filter data for selected employee
                df_employee = df_with_week[df_with_week["Employee Name"] == selected_employee].copy()
                
                if not df_employee.empty:
                    st.subheader(f"📋 Project Breakdown for {selected_employee} - {month}")
                    
                    # Create pivot table: Projects vs Weeks for the selected employee
                    employee_table = pd.pivot_table(
                        df_employee,
                        values="Hours",
                        index="Project",
                        columns="Week",
                        aggfunc="sum",
                        fill_value=0
                    )
                    
                    # Ensure all weeks are present
                    for week in ["Week 1", "Week 2", "Week 3", "Week 4"]:
                        if week not in employee_table.columns:
                            employee_table[week] = 0
                    
                    # Reorder columns
                    employee_table = employee_table[["Week 1", "Week 2", "Week 3", "Week 4"]]
                    
                    # Add TOTAL column
                    employee_table["TOTAL (Man Days)"] = employee_table.sum(axis=1)
                    
                    # Add Utilization (%) column
                    # Assuming 22 working days in a month as standard
                    working_days_per_month = 22
                    employee_table["Utilization (%)"] = (employee_table["TOTAL (Man Days)"] / working_days_per_month * 100).round(2)
                    
                    # Add Total row
                    total_row = employee_table.sum(numeric_only=True)
                    total_row.name = "Total"
                    # Recalculate total utilization
                    total_row["Utilization (%)"] = (total_row["TOTAL (Man Days)"] / working_days_per_month * 100).round(2)
                    employee_table = pd.concat([employee_table, total_row.to_frame().T])
                    
                    # Sort by total effort (excluding Total row)
                    employee_table_sorted = employee_table.iloc[:-1].sort_values("TOTAL (Man Days)", ascending=False)
                    employee_table = pd.concat([employee_table_sorted, employee_table.iloc[[-1]]])
                    
                    # Display table with custom formatting
                    def format_table(df):
                        # Format numeric columns to 1 decimal place except Utilization
                        styled_df = df.style.format({
                            "Week 1": "{:.1f}",
                            "Week 2": "{:.1f}", 
                            "Week 3": "{:.1f}",
                            "Week 4": "{:.1f}",
                            "TOTAL (Man Days)": "{:.1f}",
                            "Utilization (%)": "{:.2f}%"
                        })
                        
                        # Add color coding for utilization
                        def color_utilization(val):
                            if pd.isna(val):
                                return ""
                            try:
                                num_val = float(str(val).replace('%', ''))
                                if num_val < 50:
                                    return "background-color: #ff9800"  # Very light red
                                elif num_val < 80:
                                    return "background-color: #42a5f5"  # Light red
                                elif num_val <= 100:
                                    return "background-color: #1976d2"  # Medium red
                                else:
                                    return "background-color: #c62828"  # Dark red
                            except:
                                return ""
                        
                        styled_df = styled_df.applymap(color_utilization, subset=["Utilization (%)"])
                        return styled_df
                    
                    st.dataframe(format_table(employee_table), use_container_width=True)
                    
                    # Add utilization summary
                    total_utilization = employee_table.loc["Total", "Utilization (%)"]
                    
                    col1, col2, col3 = st.columns(3)
                    # with col1:
                    #     st.metric("Total Hours", f"{employee_table.loc['Total', 'TOTAL (Man Days)']:.1f}")
                    # with col2:
                    #     st.metric("Working Days in Month", f"{working_days_per_month}")
                    # with col3:
                    #     utilization_color = "normal"
                    #     if total_utilization < 50:
                    #         utilization_color = "inverse"
                    #     elif total_utilization > 100:
                    #         utilization_color = "off"
                        
                    #     st.metric(
                    #         "Overall Utilization", 
                    #         f"{total_utilization:.2f}%",
                    #         delta=f"{total_utilization - 100:.2f}% vs 100% target"
                    #     )
                    
                    # Utilization interpretation
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

        # --- WEEKLY BREAKDOWN SECTION (ONLY WEEKLY RESOURCE EFFORT TABLE) ---
        st.subheader("📅 Weekly Resource Effort Table")
        
        if not df_with_week.empty:
            # Project selection for weekly breakdown
            unique_projects_weekly = sorted(df_with_week["Project"].unique())
            selected_proj_week = st.selectbox("Select a project for weekly breakdown", unique_projects_weekly, key="weekly_project")

            if selected_proj_week:
                # Filter data for selected project
                df_proj_week = df_with_week[df_with_week["Project"] == selected_proj_week].copy()
                
                if not df_proj_week.empty:
                    # 📋 Weekly resource table
                    st.subheader(f"📋 Weekly Resource Effort Table - {selected_proj_week}")
                    weekly_table = pd.pivot_table(
                        df_proj_week,
                        values="Hours",
                        index="Employee Name",
                        columns="Week",
                        aggfunc="sum",
                        fill_value=0
                    )
                    
                    # Ensure all weeks are present
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

        # --- NEW SECTION: OVERALL DASHBOARD ---
        st.header("📊 Overall Dashboard")
        
        # Load all time data for dashboard
        df_all_time = analyze_all_months()
        
        if not df_all_time.empty:
            # A. Project Dashboard: Month on Month
            st.subheader("📋 A. Project Dashboard: Month on Month")
            
            project_mom_table, project_mom_labels = create_project_dashboard_month_on_month(
                df_all_time, month, all_months
            )
            
            if not project_mom_table.empty:
                # Rename columns to show month names
                display_project_table = project_mom_table.copy()
                for i, month_label in enumerate(project_mom_labels):
                    old_col = f"M{i+1}"
                    if month_label == "No Data":
                        new_col = f"M{i+1}"
                    else:
                        new_col = f"M{i+1}"
                    
                    if old_col in display_project_table.columns:
                        display_project_table = display_project_table.rename(columns={old_col: new_col})
                
                st.markdown(f"**Timeline:** {project_mom_labels[0]} → {project_mom_labels[1]} → {project_mom_labels[2]}")
                
                # Format and display the table
                styled_project_table = display_project_table.style.format({
                    col: "{:.1f}" for col in display_project_table.columns 
                    if col not in ["Project"] and col in display_project_table.select_dtypes(include=[int, float]).columns
                })
                
                st.dataframe(styled_project_table, use_container_width=True)
            else:
                st.info("No project data available for dashboard")
            
            # B. Individual Dashboard
            st.subheader(f"📋 B. Individual Dashboard: {month}")
            
            emp_designation_map = get_designation_map()
            individual_dashboard_table = create_individual_dashboard(
                df_all_time, month, emp_designation_map
            )
            
            if not individual_dashboard_table.empty:
                # Format the table
                def format_individual_table(df):
                    # Create a copy and convert numeric columns only
                    df_copy = df.copy()
                    numeric_cols = ["W1", "W2", "W3", "W4", "Total (Man Days)"]
                    
                    for col in numeric_cols:
                        if col in df_copy.columns:
                            df_copy[col] = df_copy[col].round(1)
                    
                    return df_copy.style.set_properties(**{
                        'text-align': 'center'
                    }).set_table_styles([
                        {'selector': 'th', 'props': [('text-align', 'center')]},
                        {'selector': 'td', 'props': [('text-align', 'center')]}
                    ])
                
                st.dataframe(individual_dashboard_table, use_container_width=True)
                
                # # Add explanation for utilization formula
                # with st.expander("ℹ️ Utilization Formula Explanation"):
                #     st.write("**Utilization (%) = (Total Man Days / 22) × 100**")
                #     st.write("- **22** represents the standard working days in a month")
                #     st.write("- **Total Man Days** is the sum of hours worked across all weeks")
                #     st.write("- **100%** utilization means the employee worked all available working days")
            else:
                st.info("No individual data available for current month")

        # --- COMMENTED OUT SECTIONS ---
        # # --- MULTI PROJECT SEARCH ---
        # st.markdown("### 🔎 Filter Projects")
        # all_proj = sorted(df_summary['Project'].unique())
        # selected_projects = st.multiselect("Select project(s) to analyze", all_proj)

        # if selected_projects:
        #     proj_df = df_summary[df_summary['Project'].isin(selected_projects)]
        #     proj_grouped = proj_df.groupby(['Project', 'Employee', 'Designation'], as_index=False)['Hours'].sum()

        #     fig_proj = px.bar(proj_grouped, x='Hours', y='Project', color='Employee', text='Hours', barmode='group')
        #     fig_proj.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        #     unique_projects = proj_grouped['Project'].nunique()
        #     fig_proj.update_layout(
        #         height=max(500, unique_projects * 80),
        #         plot_bgcolor="#131313",
        #         paper_bgcolor="#0E1117",
        #         font=dict(color="white")
        #     )
        #     st.plotly_chart(fig_proj, use_container_width=True)

        # # --- SUMMARY TABLE ---
        # proj_total = df_summary.groupby('Project')['Hours'].sum().reset_index()
        # proj_total = proj_total[proj_total['Project'] != '']
        # proj_total.rename(columns={'Hours': 'Total Days'}, inplace=True)

        # # Project summary chart
        # fig = px.bar(
        #     proj_total,
        #     x='Total Days',
        #     y='Project',
        #     color='Project',
        #     orientation='h',
        #     height=500,
        #     title='Total Days Spent Per Project'
        # )
        # fig.update_layout(
        #     showlegend=True,
        #     legend_title_text="Project",
        #     plot_bgcolor="#131313",
        #     paper_bgcolor="#0E1117",
        #     bargap=0.3,
        #     font=dict(color="white"),
        #     legend=dict(
        #         orientation="v",
        #         yanchor="middle",
        #         y=0.5,
        #         xanchor="left",
        #         x=1.02,
        #         borderwidth=0,
        #         bgcolor="rgba(0,0,0,0)",
        #     )
        # )
        # st.plotly_chart(fig, use_container_width=True)

        # # Summary pivot table
        # pivot = total_summary_table(df_summary)
        # display_large_table(pivot, f"📊 Employee Project Summary for {month}")

        # # --- MONTH ON MONTH COMPARISON ---
        # st.subheader(f"📈 Month-on-Month Comparison for {month}")
        # curr_index = all_months.index(month)
        
        # if curr_index == 0:
        #     st.info(f"This is the first month ({month}) in the data. No previous month available for comparison.")
        #     emp_df = df_summary.groupby("Employee")["Hours"].sum().reset_index()
        #     emp_df.rename(columns={"Hours": "Days"}, inplace=True)
        #     proj_df = df_summary.groupby("Project")["Hours"].sum().reset_index()
        #     proj_df.rename(columns={"Hours": "Days"}, inplace=True)
            
        #     display_large_table(emp_df.set_index("Employee"), f"Employee Summary for {month}")
        #     display_large_table(proj_df.set_index("Project"), f"Project Summary for {month}")
        # else:
        #     prev_month = all_months[curr_index - 1]
        #     df_prev = analyze_sheets(prev_month)
            
        #     if not df_prev.empty:
        #         compare_emp_df = compare_months(df_summary, df_prev, current_month=month, previous_month=prev_month)
        #         compare_proj_df = compare_projects(df_summary, df_prev, current_month=month, previous_month=prev_month)
                
        #         display_large_table(compare_emp_df, f"📈 Month-on-Month by Employee ({prev_month} vs {month})")
        #         display_large_table(compare_proj_df, f"📈 Month-on-Month by Project ({prev_month} vs {month})")

        # --- ALL TIME ANALYSIS (ONLY DESIGNATION-WISE EFFORT) ---
        # st.subheader("🕓 Total Effort Across All Months")
        if df_all_time.empty:
            st.info("No data found across months.")
        else:
            df_all_time['Project'] = df_all_time['Project'].astype(str).str.strip()
            
            # # --- COMMENTED OUT: Chart and variance table ---
            # proj_overall = df_all_time.groupby('Project')['Hours'].sum().reset_index()
            # proj_overall = proj_overall[proj_overall['Project'].str.len() > 2]
            # proj_overall.rename(columns={'Hours': 'Actual Days Spent'}, inplace=True)

            # # Add expected effort
            # expected_map = get_expected_effort_map()
            # proj_overall['Expected Days'] = proj_overall['Project'].map(expected_map).fillna(0)
            # proj_overall['Variance'] = proj_overall['Actual Days Spent'] - proj_overall['Expected Days']
            # proj_overall = proj_overall.sort_values(by='Actual Days Spent', ascending=False)

            # # Chart
            # fig_all = px.bar(
            #     proj_overall,
            #     x="Actual Days Spent",
            #     y="Project",
            #     orientation="h",
            #     color="Project",
            #     title="Total Days Spent per Project (All Months)"
            # )
            # fig_all.update_layout(
            #     plot_bgcolor="#131313",
            #     paper_bgcolor="#0E1117",
            #     font=dict(color="white"),
            #     showlegend=False
            # )
            # st.plotly_chart(fig_all, use_container_width=True)
            
            # # Display table with variance
            # st.dataframe(
            #     proj_overall.style
            #     .format({"Expected Days": "{:.1f}", "Actual Days Spent": "{:.1f}", "Variance": "{:+.1f}"})
            #     .background_gradient(subset=["Variance"], cmap="RdYlGn_r")
            # )

            # --- DESIGNATION WISE EFFORT (KEPT) ---
            # st.markdown("### 🧑‍💼 Designation-wise Effort per Project")
            emp_designation_map = get_designation_map()
            
            if not df_all_time.empty:
                all_projects = sorted(df_all_time["Project"].dropna().unique())
                selected_proj = st.selectbox("Select Project", all_projects, key="designation_project")

                if selected_proj:
                    desg_table = get_designation_effort_by_project(df_all_time, emp_designation_map, selected_proj)
                    # st.dataframe(desg_table.set_index("Designation"), use_container_width=True)
            else:
                st.info("No all-time project data found.")
                
        # --- COMMENTED OUT: Month-on-Month Project Resource Analysis ---        
        if not df_all_time.empty:
            st.subheader("📊 Month-on-Month Project Resource Analysis")
            
            # Project selection for month-on-month analysis
            all_projects_mom = sorted(df_all_time["Project"].dropna().unique())
            selected_project_mom = st.selectbox(
                "Select Project for Month-on-Month Analysis", 
                all_projects_mom, 
                key="mom_project_selection"
            )
            
            if selected_project_mom:
                # FIXED: Create the month-on-month table with correct logic
                mom_table, month_labels = create_month_on_month_project_table(
                    df_all_time, 
                    selected_project_mom,
                    month,  # Current selected month
                    all_months  # All available months in chronological order
                )
                
                if not mom_table.empty:
                    st.markdown(f"#### 📈 Month-on-Month Analysis: {selected_project_mom}")
                    
                    # Display month information
                    st.markdown(f"**Months:** M1 ({month_labels[0]}) → M2 ({month_labels[1]}) → M3 ({month_labels[2]})")
                    
                    # Rename columns to show actual month names in the table
                    display_table = mom_table.copy()
                    for i, month_label in enumerate(month_labels):
                        old_col = f"M{i+1}"
                        if "Ago" in month_label or month_label in ["Current"]:
                            new_col = f"M{i+1} ({month_label})"
                        else:
                            new_col = f"M{i+1} ({month_label})"
                        
                        if old_col in display_table.columns:
                            display_table = display_table.rename(columns={old_col: new_col})
                    
                    # Display the table with formatting
                    styled_table = display_table.style.format({
                        col: "{:.1f}" for col in display_table.columns 
                        if col not in ["Resource"] and col in display_table.select_dtypes(include=[int, float]).columns
                    }).background_gradient(
                        subset=["TOTAL Effort (Man Days)", "Planned Effort (Man Days)"], 
                        cmap="RdYlGn"
                    )
                    
                    st.dataframe(styled_table, use_container_width=True)
                    
                    # Add variance analysis - only if we have a Total row
                    # total_rows = display_table[display_table["Resource"] == "Total"]
                    # if not total_rows.empty:
                    #     total_actual = total_rows["TOTAL Effort (Man Days)"].iloc[0]
                    #     total_planned = total_rows["Planned Effort (Man Days)"].iloc[0]
                    #     variance = total_actual - total_planned
                    #     variance_pct = (variance / total_planned * 100) if total_planned > 0 else 0
                        
                    #     # Display variance metrics
                    #     col1, col2, col3, col4 = st.columns(4)
                        
                    #     with col1:
                    #         st.metric("Total Actual Effort", f"{total_actual:.1f} days")
                        
                    #     with col2:
                    #         st.metric("Total Planned Effort", f"{total_planned:.1f} days")
                        
                    #     with col3:
                    #         st.metric(
                    #             "Variance", 
                    #             f"{variance:+.1f} days",
                    #             delta=f"{variance_pct:+.1f}%"
                    #         )
                        
                    #     with col4:
                    #         if total_planned == 0:
                    #             status = "❓ No Plan"
                    #         elif abs(variance_pct) <= 10:
                    #             status = "✅ On Track"
                    #         else:
                    #             status = "⚠️ Off Track"
                    #         st.metric("Status", status)
                    
                    # Show explanation of planned effort
                    
                        
                        # if total_planned > 0:
                        #     num_resources = len(mom_table) - 1  # Exclude total row
                        #     planned_per_resource = total_planned / num_resources if num_resources > 0 else 0
                        #     st.write(f"5. **Per Resource**: {total_planned:.1f} ÷ {num_resources} = {planned_per_resource:.1f} days per resource")
                    
                    # Resource utilization chart - exclude Total row and only show resources with data
                    chart_data = display_table[
                        (display_table["Resource"] != "Total") & 
                        (display_table["TOTAL Effort (Man Days)"] > 0)
                    ].copy()
                    
                    # if not chart_data.empty:
                    #     fig_resource = px.bar(
                    #         chart_data,
                    #         x="Resource",
                    #         y=["TOTAL Effort (Man Days)", "Planned Effort (Man Days)"],
                    #         title=f"Actual vs Planned Effort: {selected_project_mom}",
                    #         barmode="group"
                    #     )
                    #     fig_resource.update_layout(
                    #         plot_bgcolor="#131313",
                    #         paper_bgcolor="#0E1117",
                    #         font=dict(color="white")
                    #     )
                    #     st.plotly_chart(fig_resource, use_container_width=True)
                    # else:
                    #     st.info("No resource data available for chart visualization.")
                        
                else:
                    st.info(f"No data found for project: {selected_project_mom}")
        else:
            st.info("No all-time data available for month-on-month analysis.")

# st.set_page_config(page_title="📊 Project Tracker Dashboard", layout="wide")
# st.title("📊 Project Work Tracker")
# # --- USER LOGIN / ROLE SETUP ---
# # with st.sidebar:
# #     st.header("🔐 Login")
# #     user_email = st.text_input("Email", placeholder="you@example.com")
# #     user_password = st.text_input("Password", type="password")

# # # Example user database (in real case, passwords should be hashed!)
# # USER_CREDENTIALS = {
# #     "shubham@example.com": {"password": "shubham123", "role": "Admin"},
# #     "tanya@example.com": {"password": "tanya456", "role": "Manager"},
# #     "intern@example.com": {"password": "intern789", "role": "Employee"},
# # }

# # # Check login
# # if user_email and user_password:
# #     user_info = USER_CREDENTIALS.get(user_email.lower())
# #     if user_info and user_info["password"] == user_password:
# #         role = user_info["role"]
# #         st.sidebar.success(f"Logged in as: {role}")
# #     else:
# #         st.sidebar.error("Invalid email or password")
# #         st.stop()
# # else:
# #     st.warning("Please enter your email and password to continue.")
# #     st.stop()
# # --- USER LOGIN / ROLE SETUP end end end end end  ---



# # --- UTILITY FUNCTIONS ---

# # --- UTILITY FUNCTIONS ---

# def get_designation_effort_by_project(df_all, emp_designation_map, selected_project):
#     df_proj = df_all[df_all["Project"] == selected_project].copy()
#     df_proj["Designation"] = df_proj["Employee ID"].map(emp_designation_map).fillna("Unknown")
#     designation_summary = df_proj.groupby("Designation")["Hours"].sum().reset_index()
#     designation_summary.rename(columns={"Hours": "Total Days"}, inplace=True)
#     # designation_summary.rename(columns={"Hours": "Days"}, inplace=True)
#     return designation_summary

# def get_designation_map():
#     df = load_sheet_data(MASTER_SHEET_ID, EMPLOYEE_SHEET_NAME)
#     df.columns = df.columns.str.strip()
#     if "Employee ID" in df.columns and "Designation" in df.columns:
#         return dict(zip(df["Employee ID"].astype(str).str.strip(), df["Designation"].astype(str).str.strip()))
#     return {}


# def analyze_all_months():
#     all_data = []
#     emp_map, emp_level_map = get_employee_map()
#     emp_designation_map = get_designation_map()

#     for month in all_months:
#         for emp_id, url in SHEET_URLS.items():
#             emp_name = emp_map.get(emp_id, "Unknown")
#             file_id = extract_file_id(url)

#             try:
#                 file_sheets = get_sheet_names(file_id)
#             except Exception as e:
#                 print(f"Error getting sheet names for file {file_id}: {e}")
#                 continue

#             # ✅ Check if the month (sheet name) exists in this file
#             if month not in file_sheets:
#                 continue

#             df = load_sheet_data(file_id, month)

#             if df.empty:
#                 continue

#             project_col = df.columns[0]
#             date_cols = df.columns[1:]

#             for _, row in df.iterrows():
#                 project = str(row[project_col]).strip()
#                 if project.lower() in ["", "nan"]:
#                     continue

#                 for date in date_cols:
#                     val = row[date]
#                     if pd.notna(val) and str(val).strip() not in ["", "-"]:
#                         try:
#                             all_data.append({
#                                 "Employee ID": emp_id,
#                                 "Employee Name": emp_name,
#                                 "Project": project,
#                                 "Month": month,
#                                 "Date": date,
#                                 "Hours": float(val)
#                             })
#                         except:
#                             continue

#     return pd.DataFrame(all_data)

#     all_data = []
#     # emp_map = get_employee_map()
#     emp_map, emp_level_map = get_employee_map()
#     emp_designation_map = get_designation_map()



#     for month in all_months:
#         for emp_id, url in SHEET_URLS.items():
#             emp_name = emp_map.get(emp_id, "Unknown")
#             file_id = extract_file_id(url)
#             df = load_sheet_data(file_id, month)

#             if df.empty:
#                 continue

#             project_col = df.columns[0]
#             date_cols = df.columns[1:]

#             for _, row in df.iterrows():
#                 project = str(row[project_col]).strip()
#                 if project.lower() in ["", "nan"]:
#                     continue

#                 for date in date_cols:
#                     val = row[date]
#                     if pd.notna(val) and str(val).strip() not in ["", "-"]:
#                         try:
#                             all_data.append({
#                                 "Employee ID": emp_id,
#                                 "Employee Name": emp_name,
#                                 "Project": project,
#                                 "Month": month,
#                                 "Date": date,
#                                 "Hours": float(val)
#                             })
#                         except:
#                             continue

#     return pd.DataFrame(all_data)
# def get_expected_effort_map():
#     df_effort = load_sheet_data(MASTER_SHEET_ID, "Project Master")
#     df_effort.columns = df_effort.columns.astype(str).str.strip()

#     if "ProjectList" not in df_effort.columns or "Project Effort Plan" not in df_effort.columns:
#         return {}

#     return dict(zip(
#         df_effort["ProjectList"].astype(str).str.strip(),
#         pd.to_numeric(df_effort["Project Effort Plan"], errors="coerce").fillna(0)
#     ))

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

# # --- LOAD EMPLOYEE MASTER MAP ---
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


# # --- ANALYZE GOOGLE SHEETS ---
# def analyze_sheets(selected_month):
#     employee_data = []
#    # emp_map = get_employee_map()
#     emp_map, designation_map = get_employee_map()


#     for employee_id, url in SHEET_URLS.items():
#         employee_name = emp_map.get(employee_id, "Unknown")
#         file_id = extract_file_id(url)
#         df = load_sheet_data(file_id, selected_month)
#         if df.empty: continue

#         project_col = df.columns[0]
#         date_cols = df.columns[1:]
#         for _, row in df.iterrows():
#             project = str(row[project_col]).strip()
#             if project.lower() in ["", "nan"]: continue

#             for date in date_cols:
#                 val = row[date]
#                 if pd.notna(val) and str(val).strip() not in ["", "-"]:
#                     try:
#                         employee_data.append({
#                             "Employee ID": employee_id,
#                             "Employee Name": employee_name,
#                             "Project": project,
#                             "Date": date,
#                             "Hours": float(val),
#                             "Designation": designation_map.get(employee_id, "Unknown")
#                         })
#                     except ValueError:
#                         continue

#     return pd.DataFrame(employee_data)

# # --- SUMMARY TABLES ---
# def total_summary_table(df):
#     df = df[df["Project"].astype(str).str.strip().ne("")]
#     # df["Employee"] = df["Employee Name"] + " (" + df["Employee ID"] + ")"
#     df["Employee Composite"] = df["Employee Name"] + " (" + df["Employee ID"] + ")"
#     pivot = df.pivot_table(index='Project', columns='Employee Composite', values='Hours', aggfunc='sum', fill_value=0)
#     pivot = df.pivot_table(index='Project', columns='Employee', values='Hours', aggfunc='sum', fill_value=0)
#     pivot = pivot[~(pivot.index.to_series().str.strip() == "")]
#     pivot['Total'] = pivot.sum(axis=1)
#     pivot.loc['Total'] = pivot.sum(numeric_only=True)
#     return pivot
# def project_wise_employee_table(df, selected_project):
#     filtered_df = df[df["Project"] == selected_project]
#     grouped = (
#         filtered_df.groupby("Employee")["Hours"]
#         .sum()
#         .reset_index()
#         .sort_values("Hours", ascending=False)
#     )
#     grouped = grouped[grouped["Hours"] > 0]
#     grouped.rename(columns={"Hours": "Days"}, inplace=True) 
#     return grouped.set_index("Employee")


# def compare_months(current_df, previous_df, current_month, previous_month):
#     current_df["Employee"] = current_df["Employee Name"] + " (" + current_df["Employee ID"] + ")"
#     previous_df["Employee"] = previous_df["Employee Name"] + " (" + previous_df["Employee ID"] + ")"
#     current_total = current_df.groupby("Employee")["Hours"].sum()
#     previous_total = previous_df.groupby("Employee")["Hours"].sum()

#     all_employees = set(current_total.index.tolist() + previous_total.index.tolist())
#     compare_data = []
#     for employee in all_employees:
#         prev_hours = previous_total.get(employee, 0)
#         curr_hours = current_total.get(employee, 0)
#         compare_data.append({
#             "Employee": employee,
#             f"Previous Month ({previous_month})": prev_hours,
#             f"Current Month ({current_month})": curr_hours,
#             "Change": curr_hours - prev_hours,
#             "Total Time": prev_hours + curr_hours
#         })
#     return pd.DataFrame(compare_data).set_index("Employee").sort_index()

# def compare_projects(current_df, previous_df, current_month, previous_month):
#     current_total = current_df.groupby("Project")["Hours"].sum()
#     previous_total = previous_df.groupby("Project")["Hours"].sum()
#     all_projects = set(current_total.index.tolist() + previous_total.index.tolist())
#     compare_data = []
#     for project in all_projects:
#         prev_hours = previous_total.get(project, 0)
#         curr_hours = current_total.get(project, 0)
#         compare_data.append({
#             "Project": project,
#             f"Previous Month ({previous_month})": prev_hours,
#             f"Current Month ({current_month})": curr_hours,
#             "Change": curr_hours - prev_hours,
#             "Total Time": prev_hours + curr_hours
#         })
#     return pd.DataFrame(compare_data).set_index("Project").sort_index()

# # --- EXPORT TO EXCEL ---
# def generate_excel_download(df):
#     output = io.BytesIO()
#     with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
#         df.to_excel(writer, sheet_name="Summary")
#         writer.close()
#     return output.getvalue()

# # --- TABLE RENDERING ---
# def display_large_table(df, caption):
#     st.markdown(f"#### {caption}")
#     st.dataframe(df.style.format("{:.1f}"), use_container_width=True)

# def add_week_column(df):
#     from datetime import datetime

#     df = df.copy()

#     def get_week_label(date_str):
#         if not date_str or str(date_str).strip() in ["", "-", "nan", "NaT"]:
#             return None
#         try:
#             dt = datetime.strptime(date_str, "%m/%d/%Y")
#             week_num = (dt.day - 1) // 7 + 1
#             return f"Week {week_num}"
#         except Exception as e:
#             return None

#     df["Week"] = df["Date"].apply(get_week_label)

#     # Remove rows where week could not be assigned
#     df = df[df["Week"].notna()]
#     return df



# # Define week label function
#     def get_week_label(date_str):
#         try:
#             if not date_str or pd.isna(date_str) or str(date_str).strip() == "":
#                 return "Unknown"
#             dt = datetime.strptime(date_str, "%m/%d/%Y")
#             week_num = (dt.day - 1) // 7 + 1
#             return f"Week {week_num}"
#         except:
#             return "Unknown"

#     # Apply week column
#     df_melted["Week"] = df_melted["Date"].apply(get_week_label)

#     # Drop rows with NaN hours or 0 (if you want)
#     df_melted = df_melted[df_melted["Hours"].notna() & (df_melted["Hours"] > 0)]

#     # Check final DataFrame
#     print(df_melted)

    
#     df = df.copy()
#     df["Week"] = df["Date"].apply(get_week_label)
#     return df


# # --- MAIN LOGIC ---
# # --- GET ALL MONTHS ---
# all_months_raw = []
# for url in SHEET_URLS.values():
#     file_id = extract_file_id(url)
#     try:
#         months = get_sheet_names(file_id)
#         all_months_raw.extend(months)
#     except Exception as e:
#         st.error(f"Error getting sheet names: {e}")

# all_months = sort_months_chronologically(list(set(all_months_raw)))
# month = st.selectbox("Select Month", all_months)

# if month:
#     df_summary = analyze_sheets(month)
#     # st.subheader("🔍 Effort by Designation Level")
#     designation_summary = df_summary.groupby("Designation")["Hours"].sum().reset_index()
#     fig_designation = px.bar(designation_summary, x="Designation", y="Hours", color="Designation", text="Hours")
#     fig_designation.update_traces(texttemplate='%{text:.1f}', textposition='outside')
#     # st.plotly_chart(fig_designation, use_container_width=True)


#     if df_summary.empty:
#         st.warning("No data found for this month")
#     else:
#         df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
#         if not df_summary.empty:
#             st.subheader("📅 Weekly Breakdown (Within Selected Month)")
#             df_with_week = add_week_column(df_summary)

#             week_proj_df = df_with_week.groupby(["Project", "Week"])["Hours"].sum().reset_index()

#             # Dropdown to select project
#             selected_proj_week = st.selectbox("Select a project for weekly breakdown", sorted(df_with_week["Project"].unique()), key="weekly_project")

#             if selected_proj_week:
#                 proj_week_data = week_proj_df[week_proj_df["Project"] == selected_proj_week]
#                 if not proj_week_data.empty:
#                     fig_week = px.bar(
#                         proj_week_data,
#                         x="Week",
#                         y="Hours",
#                         color="Week",
#                         text="Hours",
#                         title=f"Weekly Effort Distribution for '{selected_proj_week}' in {month}"
#                     )
#                     fig_week.update_traces(texttemplate='%{text:.1f}', textposition='outside')
#                     fig_week.update_layout(
#                         plot_bgcolor="#131313",
#                         paper_bgcolor="#0E1117",
#                         font=dict(color="white"),
#                         showlegend=False
#                     )
#                     st.plotly_chart(fig_week, use_container_width=True)
#                     st.dataframe(proj_week_data.set_index("Week"), use_container_width=True)
#                 else:
#                     st.info("No data found for this project in selected month.")
#         if "Employee" not in df_summary.columns:
#             # df_summary['Employee'] = df_summary['Employee Name'] + " (" + df_summary['Employee ID'] + ")"
#             df_summary['Employee'] = df_summary['Employee Name'] + " (" + df_summary['Designation'] + ", " + df_summary['Employee ID'] + ")"


#         # df_summary['Employee'] = df_summary['Employee Name'] + " (" + df_summary['Employee ID'] + ")"

#         # --- MULTI PROJECT SEARCH ---
#         st.markdown("### 🔎 Filter Projects")
#         all_proj = sorted(df_summary['Project'].unique())
#         selected_projects = st.multiselect("Select project(s) to analyze", all_proj)

#         if selected_projects:
#             proj_df = df_summary[df_summary['Project'].isin(selected_projects)]
#             # proj_grouped = proj_df.groupby(['Project', 'Employee'],as_index=False)['Hours'].sum().reset_index()
#             proj_grouped = proj_df.groupby(['Project', 'Employee', 'Designation'], as_index=False)['Hours'].sum()

#             fig_proj = px.bar(proj_grouped, x='Hours', y='Project', color='Employee', text='Hours', barmode='group')
#             # pio.write_image(fig_proj, "example_chart.png", width=800, height=500)
#             # save_chart_as_image(fig_proj, "project_chart_1.png")   #1
#             fig_proj.update_traces(texttemplate='%{text:.1f}', textposition='outside')
#             unique_projects = proj_grouped['Project'].nunique()
#             fig_proj.update_layout(height=max(500, (unique_projects)*80), plot_bgcolor="#131313", paper_bgcolor="#0E1117", font=dict(color="white"))
#             st.plotly_chart(fig_proj, use_container_width=True)

#         # --- SUMMARY TABLE ---
#         df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
#         # Filter out project names that are purely numeric or too short
#         df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
#         df_summary = df_summary[~df_summary['Project'].str.match(r'^\d+$')]  # remove numeric-only names
#         df_summary = df_summary[df_summary['Project'].str.len() > 2]         # remove short junk names like '3', '5'

#         proj_total = df_summary.groupby('Project')['Hours'].sum().reset_index()
#         proj_total = proj_total[proj_total['Project'] != '']
#         proj_total.rename(columns={'Hours': 'Total Days'}, inplace=True)

#         # Plot with legend on the right
#         fig = px.bar(
#             proj_total,
#             x='Total Days',
#             y='Project',
#             color='Project',
#             orientation='h',
#             height=500,
#             title='Total Days Spent Per Project'
#         )
#         # pio.write_image(fig, "example_chart_2.png", width=800, height=500)

#         fig.update_layout(
#             showlegend=True,
#             legend_title_text="Project",
#             plot_bgcolor="#131313",
#             paper_bgcolor="#0E1117",
#             bargap=0.3,
#             font=dict(color="white"),
#             legend=dict(
#                 orientation="v",
#                 yanchor="middle",
#                 y=0.5,
#                 xanchor="left",
#                 x=1.02,
#                 borderwidth=0,
#                 bgcolor="rgba(0,0,0,0)",
#             )
#         )

#         # st.plotly_chart(fig, use_container_width=True)
#         # save_chart_as_image(fig, "project_chart_2.png")
#         pivot = total_summary_table(df_summary)
#         display_large_table(pivot, f"📊 Employee Project Summary for {month}")

#         # --- EXPORT OPTION ---
#         # st.download_button("🧾 Download Summary as Excel", data=generate_excel_download(pivot),
#         #                    file_name=f"Summary_{month}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

#         # --- INTERACTIVE EMPLOYEE TABLE BY PROJECT ---
#         st.markdown("### 📌 View Employees Working on Specific Project")
#         unique_projects_list = sorted(df_summary["Project"].unique())
#         selected_proj_for_table = st.selectbox("Select a project to see employee contributions", unique_projects_list)

#         if selected_proj_for_table and month:
#             df_proj = df_summary[df_summary["Project"] == selected_proj_for_table].copy()

#             # Convert Dates to datetime
#             df_proj["Date_obj"] = pd.to_datetime(df_proj["Date"], errors="coerce")

#             # Remove rows where date is NaT (invalid) or Hours are missing/zero
#             df_proj = df_proj[df_proj["Date_obj"].notna()]
#             df_proj["Hours"] = pd.to_numeric(df_proj["Hours"], errors="coerce").fillna(0)
#             df_proj = df_proj[df_proj["Hours"] > 0]

#             # Assign week label
#             def assign_week(dt):
#                 day = dt.day
#                 if day <= 7:
#                     return "Week 1"
#                 elif day <= 14:
#                     return "Week 2"
#                 elif day <= 21:
#                     return "Week 3"
#                 else:
#                     return "Week 4"

#             df_proj["Week"] = df_proj["Date_obj"].apply(assign_week)

#             # Group by week
#             weekly_summary = df_proj.groupby("Week")["Hours"].sum().reset_index()
#             weekly_summary = weekly_summary.sort_values("Week")  # optional sorting

#             # Plot
#             fig_weekly = px.bar(
#                 weekly_summary,
#                 x="Week",
#                 y="Hours",
#                 text="Hours",
#                 title=f"Weekly Effort Distribution for '{selected_proj_for_table}' in {month}",
#                 color="Week"
#             )
#             fig_weekly.update_traces(texttemplate='%{text:.1f}', textposition='outside')
#             fig_weekly.update_layout(
#                 plot_bgcolor="#131313",
#                 paper_bgcolor="#0E1117",
#                 font=dict(color="white")
#             )
#             st.plotly_chart(fig_weekly, use_container_width=True)

#             # Show as table
#             st.dataframe(weekly_summary, use_container_width=True)

#         # --- EMPLOYEE CHART ---
#         # st.subheader("👥 Total Days Per Employee")
#         emp_total = df_summary.groupby('Employee')['Hours'].sum().reset_index()
#         emp_total.rename(columns={"Hours": "Days"}, inplace=True) 
#         fig_emp = px.bar(emp_total, x='Days', y='Employee', orientation='h', color='Employee')
#         # save_chart_as_image(fig_emp, "project_chart_3.png")
#         # st.plotly_chart(fig_emp, use_container_width=True)

#         # --- PROJECT STACKED ---
#         # st.subheader("📊 Project-wise Contribution by Employees")
#         proj_emp_df = df_summary.groupby(['Project', 'Employee'])['Hours'].sum().reset_index()
#         proj_emp_df.rename(columns={"Hours": "Days"}, inplace=True) 
#         fig = px.bar(proj_emp_df, x="Project", y="Days", color="Employee", text="Days", barmode="stack")
#         # save_chart_as_image(proj_emp_df, "project_chart.png")
#         # st.plotly_chart(fig, use_container_width=True)

#         # --- MONTH ON MONTH COMPARISON ---
#         st.subheader(f"📈 Month-on-Month Comparison for {month}")
#         curr_index = all_months.index(month)
#         if curr_index == 0:
#             st.info(f"This is the first month ({month}) in the data. No previous month available for comparison.")
#             emp_df = df_summary.groupby("Employee")["Hours"].sum().reset_index()
#             emp_df.rename(columns={"Hours": "Days"}, inplace=True)
#             proj_df = df_summary.groupby("Project")["Hours"].sum().reset_index()
#             proj_df.rename(columns={"Hours": "Days"}, inplace=True)
#             # st.write("🔍 Sample Data Extracted:")
#             # st.dataframe(df_summary.head(20))

#             display_large_table(emp_df.set_index("Employee"), f"Employee Summary for {month}")
#             display_large_table(proj_df.set_index("Project"), f"Project Summary for {month}")
#         else:
#             prev_month = all_months[curr_index - 1]
#             df_prev = analyze_sheets(prev_month)
#             compare_emp_df = compare_months(df_summary, df_prev, current_month=month, previous_month=prev_month)
#             compare_proj_df = compare_projects(df_summary, df_prev, current_month=month, previous_month=prev_month)
#             display_large_table(compare_emp_df, f"📈 Month-on-Month by Employee ({prev_month} vs {month})")
#             display_large_table(compare_proj_df, f"📈 Month-on-Month by Project ({prev_month} vs {month})")
        
        
#         st.subheader("🕓 Total Effort Across All Months")

#         df_all_time = analyze_all_months()
#         if df_all_time.empty:
#             st.info("No data found across months.")
#         else:
#             df_all_time['Project'] = df_all_time['Project'].astype(str).str.strip()
#             proj_overall = df_all_time.groupby('Project')['Hours'].sum().reset_index()
#             proj_overall = proj_overall[proj_overall['Project'].str.len() > 2]
#             proj_overall.rename(columns={'Hours': 'Actual Days Spent'}, inplace=True)

#             # Add expected effort
#             expected_map = get_expected_effort_map()
#             proj_overall['Expected Days'] = proj_overall['Project'].map(expected_map).fillna(0)

#             # Calculate variance
#             proj_overall['Variance'] = proj_overall['Actual Days Spent'] - proj_overall['Expected Days']

#             # Sort by variance or effort
#             proj_overall = proj_overall.sort_values(by='Variance', ascending=False)


#             # Sort descending
#             proj_overall = proj_overall.sort_values(by='Actual Days Spent', ascending=False)

#                 # st.dataframe(proj_overall)

#             # Optional: Add a horizontal bar chart
#             fig_all = px.bar(
#                 proj_overall,
#                 x="Actual Days Spent",
#                 y="Project",
#                 orientation="h",
#                 color="Project",
#                 title="Total Days Spent per Project (All Months)"
#             )
#             fig_all.update_layout(
#                 plot_bgcolor="#131313",
#                 paper_bgcolor="#0E1117",
#                 font=dict(color="white"),
#                 showlegend=False
#             )
#             st.plotly_chart(fig_all, use_container_width=True)
#             st.dataframe(
#             proj_overall.style
#             .format({"Expected Days": "{:.1f}", "Actual Days Spent": "{:.1f}", "Variance": "{:+.1f}"})
#             .background_gradient(subset=["Variance"], cmap="RdYlGn_r")
#             )
#             emp_designation_map = get_designation_map()

#             st.markdown("### 🧑‍💼 Designation-wise Effort per Project")

#             if not df_all_time.empty:
#                 all_projects = sorted(df_all_time["Project"].dropna().unique())
#                 selected_proj = st.selectbox("Select Project", all_projects, key="designation_project")

#                 if selected_proj:
#                     desg_table = get_designation_effort_by_project(df_all_time, emp_designation_map, selected_proj)
#                     st.dataframe(desg_table.set_index("Designation"), use_container_width=True)
#             else:
#                 st.info("No all-time project data found.")

# # import streamlit as st
# # import pandas as pd
# # import plotly.express as px
# # from google.oauth2 import service_account
# # from googleapiclient.discovery import build
# # from datetime import datetime
# # import time
# # import io
# # import plotly.io as pio
# # from dotenv import load_dotenv
# # import os

# # # --- CONFIGURATION ---
# # SCOPES = [
# #     "https://www.googleapis.com/auth/spreadsheets",
# #     "https://www.googleapis.com/auth/drive"
# # ]

# # SHEET_URLS = {
# #     # "TF_003": "https://docs.google.com/spreadsheets/d/1qRiex4L1bpXu-4q1VwgxsiqB6f5KR0qZUmJrAXZI0II",
# #     # "TF_004": "https://docs.google.com/spreadsheets/d/1xEXlpnvu8Xxy-Pr7VtIdWnLYBqDjO0CWgq6Y4UPl3wA",
# #     # "TF_005": "https://docs.google.com/spreadsheets/d/14VLlqc3GRYjkovBd4xc4ypTQOiiXYvf9c3OCOqw9LNI",
# #     "TDFS44": "https://docs.google.com/spreadsheets/d/1p3583-UC0odlroqFyfdYqKF5AlO2NbA7EY9_95yNloE",#aditi
# #     "TDFS46": "https://docs.google.com/spreadsheets/d/1fwj1MWZGqbcDATuUfoeuRhEJ7tmqKlQ9v29fRy1IeVA",#chirag
# #     "TDFS47": "https://docs.google.com/spreadsheets/d/1NKLyLNN1AEKlVaS1ejfAO6MmRrdqDt1qjhnuuGL5xAw" #harsh
    
# # }

# # CREDENTIALS_PATH = "credentials.json"
# # load_dotenv()  # loads .env file into environment variables
# # MASTER_SHEET_ID = os.getenv("MASTER_ID")

# # EMPLOYEE_SHEET_NAME = "Employee Detail"

# # # --- AUTHENTICATION ---
# # #creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
# # service_account_info = st.secrets["gcp_service_account"]
# # creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
# # drive_service = build("drive", "v3", credentials=creds)
# # sheets_service = build("sheets", "v4", credentials=creds)

# # st.set_page_config(page_title="📊 Project Tracker Dashboard", layout="wide")
# # st.title("📊 Project Work Tracker")
# # # --- USER LOGIN / ROLE SETUP ---
# # # with st.sidebar:
# # #     st.header("🔐 Login")
# # #     user_email = st.text_input("Email", placeholder="you@example.com")
# # #     user_password = st.text_input("Password", type="password")

# # # # Example user database (in real case, passwords should be hashed!)
# # # USER_CREDENTIALS = {
# # #     "shubham@example.com": {"password": "shubham123", "role": "Admin"},
# # #     "tanya@example.com": {"password": "tanya456", "role": "Manager"},
# # #     "intern@example.com": {"password": "intern789", "role": "Employee"},
# # # }

# # # # Check login
# # # if user_email and user_password:
# # #     user_info = USER_CREDENTIALS.get(user_email.lower())
# # #     if user_info and user_info["password"] == user_password:
# # #         role = user_info["role"]
# # #         st.sidebar.success(f"Logged in as: {role}")
# # #     else:
# # #         st.sidebar.error("Invalid email or password")
# # #         st.stop()
# # # else:
# # #     st.warning("Please enter your email and password to continue.")
# # #     st.stop()
# # # --- USER LOGIN / ROLE SETUP end end end end end  ---



# # # --- UTILITY FUNCTIONS ---

# # def get_designation_effort_by_project(df_all, emp_designation_map, selected_project):
# #     df_proj = df_all[df_all["Project"] == selected_project].copy()
# #     df_proj["Designation"] = df_proj["Employee ID"].map(emp_designation_map).fillna("Unknown")
# #     designation_summary = df_proj.groupby("Designation")["Hours"].sum().reset_index()
# #     designation_summary.rename(columns={"Hours": "Total Days"}, inplace=True)
# #     # designation_summary.rename(columns={"Hours": "Days"}, inplace=True)
# #     return designation_summary

# # def get_designation_map():
# #     df = load_sheet_data(MASTER_SHEET_ID, EMPLOYEE_SHEET_NAME)
# #     df.columns = df.columns.str.strip()
# #     if "Employee ID" in df.columns and "Designation" in df.columns:
# #         return dict(zip(df["Employee ID"].astype(str).str.strip(), df["Designation"].astype(str).str.strip()))
# #     return {}


# # def analyze_all_months():
# #     all_data = []
# #     # emp_map = get_employee_map()
# #     emp_map, emp_level_map = get_employee_map()
# #     emp_designation_map = get_designation_map()



# #     for month in all_months:
# #         for emp_id, url in SHEET_URLS.items():
# #             emp_name = emp_map.get(emp_id, "Unknown")
# #             file_id = extract_file_id(url)
# #             df = load_sheet_data(file_id, month)

# #             if df.empty:
# #                 continue

# #             project_col = df.columns[0]
# #             date_cols = df.columns[1:]

# #             for _, row in df.iterrows():
# #                 project = str(row[project_col]).strip()
# #                 if project.lower() in ["", "nan"]:
# #                     continue

# #                 for date in date_cols:
# #                     val = row[date]
# #                     if pd.notna(val) and str(val).strip() not in ["", "-"]:
# #                         try:
# #                             all_data.append({
# #                                 "Employee ID": emp_id,
# #                                 "Employee Name": emp_name,
# #                                 "Project": project,
# #                                 "Month": month,
# #                                 "Date": date,
# #                                 "Hours": float(val)
# #                             })
# #                         except:
# #                             continue

# #     return pd.DataFrame(all_data)
# # def get_expected_effort_map():
# #     df_effort = load_sheet_data(MASTER_SHEET_ID, "Project Master")
# #     df_effort.columns = df_effort.columns.astype(str).str.strip()

# #     if "ProjectList" not in df_effort.columns or "Project Effort Plan" not in df_effort.columns:
# #         return {}

# #     return dict(zip(
# #         df_effort["ProjectList"].astype(str).str.strip(),
# #         pd.to_numeric(df_effort["Project Effort Plan"], errors="coerce").fillna(0)
# #     ))

# # def extract_file_id(url):
# #     return url.split("/d/")[1].split("/")[0]

# # def get_sheet_names(file_id):
# #     metadata = sheets_service.spreadsheets().get(spreadsheetId=file_id).execute()
# #     return [sheet["properties"]["title"] for sheet in metadata["sheets"]]

# # def sort_months_chronologically(months):
# #     month_dates = []
# #     for month in months:
# #         try:
# #             if '-' in month:
# #                 month_date = datetime.strptime(month, "%B-%y")
# #             else:
# #                 month_date = datetime.strptime(month, "%B-%Y")
# #             month_dates.append((month_date, month))
# #         except:
# #             try:
# #                 month_date = datetime.strptime(month.upper(), "%b-%y")
# #                 month_dates.append((month_date, month))
# #             except:
# #                 month_dates.append((datetime.max, month))
# #     month_dates.sort(key=lambda x: x[0])
# #     return [month for _, month in month_dates]

# # # --- LOAD EMPLOYEE MASTER MAP ---
# # def load_sheet_data(file_id, sheet_name):
# #     result = sheets_service.spreadsheets().values().get(
# #         spreadsheetId=file_id,
# #         range=sheet_name
# #     ).execute()
# #     values = result.get('values', [])
# #     if not values:
# #         return pd.DataFrame()
# #     df = pd.DataFrame(values)
# #     df.columns = df.iloc[0]
# #     df = df[1:]
# #     df.reset_index(drop=True, inplace=True)
# #     df.dropna(how="all", inplace=True)
# #     return df

# # # def get_employee_map():
# # #     df_map = load_sheet_data(MASTER_SHEET_ID, EMPLOYEE_SHEET_NAME)
# # #     if df_map.empty or "Employee ID" not in df_map.columns or "Employee Name" not in df_map.columns:
# # #         return {}
# # #     df_map.columns = df_map.columns.astype(str).str.strip().str.replace('\n', ' ').str.replace('\r', ' ')
# # #     emp_map = dict(zip(df_map["Employee ID"].astype(str).str.strip(), df_map["Employee Name"].astype(str).str.strip()))
# # #     return emp_map
# # def get_employee_map():
# #     df_map = load_sheet_data(MASTER_SHEET_ID, EMPLOYEE_SHEET_NAME)
# #     if df_map.empty or not {"Employee ID", "Employee Name", "Designation"}.issubset(df_map.columns):
# #         return {}, {}
# #     df_map.columns = df_map.columns.astype(str).str.strip().str.replace('\n', ' ').str.replace('\r', ' ')
# #     emp_name_map = dict(zip(df_map["Employee ID"].astype(str).str.strip(), df_map["Employee Name"].astype(str).str.strip()))
# #     emp_designation_map = dict(zip(df_map["Employee ID"].astype(str).str.strip(), df_map["Designation"].astype(str).str.strip()))
# #     return emp_name_map, emp_designation_map


# # # --- ANALYZE GOOGLE SHEETS ---
# # def analyze_sheets(selected_month):
# #     employee_data = []
# #    # emp_map = get_employee_map()
# #     emp_map, designation_map = get_employee_map()


# #     for employee_id, url in SHEET_URLS.items():
# #         employee_name = emp_map.get(employee_id, "Unknown")
# #         file_id = extract_file_id(url)
# #         df = load_sheet_data(file_id, selected_month)
# #         if df.empty: continue

# #         project_col = df.columns[0]
# #         date_cols = df.columns[1:]
# #         for _, row in df.iterrows():
# #             project = str(row[project_col]).strip()
# #             if project.lower() in ["", "nan"]: continue

# #             for date in date_cols:
# #                 val = row[date]
# #                 if pd.notna(val) and str(val).strip() not in ["", "-"]:
# #                     try:
# #                         employee_data.append({
# #                             "Employee ID": employee_id,
# #                             "Employee Name": employee_name,
# #                             "Project": project,
# #                             "Date": date,
# #                             "Hours": float(val),
# #                             "Designation": designation_map.get(employee_id, "Unknown")
# #                         })
# #                     except ValueError:
# #                         continue

# #     return pd.DataFrame(employee_data)

# # # --- SUMMARY TABLES ---
# # def total_summary_table(df):
# #     df = df[df["Project"].astype(str).str.strip().ne("")]
# #     # df["Employee"] = df["Employee Name"] + " (" + df["Employee ID"] + ")"
# #     df["Employee Composite"] = df["Employee Name"] + " (" + df["Employee ID"] + ")"
# #     pivot = df.pivot_table(index='Project', columns='Employee Composite', values='Hours', aggfunc='sum', fill_value=0)
# #     pivot = df.pivot_table(index='Project', columns='Employee', values='Hours', aggfunc='sum', fill_value=0)
# #     pivot = pivot[~(pivot.index.to_series().str.strip() == "")]
# #     pivot['Total'] = pivot.sum(axis=1)
# #     pivot.loc['Total'] = pivot.sum(numeric_only=True)
# #     return pivot
# # def project_wise_employee_table(df, selected_project):
# #     filtered_df = df[df["Project"] == selected_project]
# #     grouped = (
# #         filtered_df.groupby("Employee")["Hours"]
# #         .sum()
# #         .reset_index()
# #         .sort_values("Hours", ascending=False)
# #     )
# #     grouped = grouped[grouped["Hours"] > 0]
# #     grouped.rename(columns={"Hours": "Days"}, inplace=True) 
# #     return grouped.set_index("Employee")


# # def compare_months(current_df, previous_df, current_month, previous_month):
# #     current_df["Employee"] = current_df["Employee Name"] + " (" + current_df["Employee ID"] + ")"
# #     previous_df["Employee"] = previous_df["Employee Name"] + " (" + previous_df["Employee ID"] + ")"
# #     current_total = current_df.groupby("Employee")["Hours"].sum()
# #     previous_total = previous_df.groupby("Employee")["Hours"].sum()

# #     all_employees = set(current_total.index.tolist() + previous_total.index.tolist())
# #     compare_data = []
# #     for employee in all_employees:
# #         prev_hours = previous_total.get(employee, 0)
# #         curr_hours = current_total.get(employee, 0)
# #         compare_data.append({
# #             "Employee": employee,
# #             f"Previous Month ({previous_month})": prev_hours,
# #             f"Current Month ({current_month})": curr_hours,
# #             "Change": curr_hours - prev_hours,
# #             "Total Time": prev_hours + curr_hours
# #         })
# #     return pd.DataFrame(compare_data).set_index("Employee").sort_index()

# # def compare_projects(current_df, previous_df, current_month, previous_month):
# #     current_total = current_df.groupby("Project")["Hours"].sum()
# #     previous_total = previous_df.groupby("Project")["Hours"].sum()
# #     all_projects = set(current_total.index.tolist() + previous_total.index.tolist())
# #     compare_data = []
# #     for project in all_projects:
# #         prev_hours = previous_total.get(project, 0)
# #         curr_hours = current_total.get(project, 0)
# #         compare_data.append({
# #             "Project": project,
# #             f"Previous Month ({previous_month})": prev_hours,
# #             f"Current Month ({current_month})": curr_hours,
# #             "Change": curr_hours - prev_hours,
# #             "Total Time": prev_hours + curr_hours
# #         })
# #     return pd.DataFrame(compare_data).set_index("Project").sort_index()

# # # --- EXPORT TO EXCEL ---
# # def generate_excel_download(df):
# #     output = io.BytesIO()
# #     with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
# #         df.to_excel(writer, sheet_name="Summary")
# #         writer.close()
# #     return output.getvalue()

# # # --- TABLE RENDERING ---
# # def display_large_table(df, caption):
# #     st.markdown(f"#### {caption}")
# #     st.dataframe(df.style.format("{:.1f}"), use_container_width=True)


# # # --- MAIN LOGIC ---
# # # --- GET ALL MONTHS ---
# # all_months_raw = []
# # for url in SHEET_URLS.values():
# #     file_id = extract_file_id(url)
# #     try:
# #         months = get_sheet_names(file_id)
# #         all_months_raw.extend(months)
# #     except Exception as e:
# #         st.error(f"Error getting sheet names: {e}")

# # all_months = sort_months_chronologically(list(set(all_months_raw)))
# # month = st.selectbox("Select Month", all_months)

# # if month:
# #     df_summary = analyze_sheets(month)
# #     # st.subheader("🔍 Effort by Designation Level")
# #     designation_summary = df_summary.groupby("Designation")["Hours"].sum().reset_index()
# #     fig_designation = px.bar(designation_summary, x="Designation", y="Hours", color="Designation", text="Hours")
# #     fig_designation.update_traces(texttemplate='%{text:.1f}', textposition='outside')
# #     # st.plotly_chart(fig_designation, use_container_width=True)


# #     if df_summary.empty:
# #         st.warning("No data found for this month")
# #     else:
# #         df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
# #         if "Employee" not in df_summary.columns:
# #             # df_summary['Employee'] = df_summary['Employee Name'] + " (" + df_summary['Employee ID'] + ")"
# #             df_summary['Employee'] = df_summary['Employee Name'] + " (" + df_summary['Designation'] + ", " + df_summary['Employee ID'] + ")"


# #         # df_summary['Employee'] = df_summary['Employee Name'] + " (" + df_summary['Employee ID'] + ")"

# #         # --- MULTI PROJECT SEARCH ---
# #         st.markdown("### 🔎 Filter Projects")
# #         all_proj = sorted(df_summary['Project'].unique())
# #         selected_projects = st.multiselect("Select project(s) to analyze", all_proj)

# #         if selected_projects:
# #             proj_df = df_summary[df_summary['Project'].isin(selected_projects)]
# #             # proj_grouped = proj_df.groupby(['Project', 'Employee'],as_index=False)['Hours'].sum().reset_index()
# #             proj_grouped = proj_df.groupby(['Project', 'Employee', 'Designation'], as_index=False)['Hours'].sum()

# #             fig_proj = px.bar(proj_grouped, x='Hours', y='Project', color='Employee', text='Hours', barmode='group')
# #             # pio.write_image(fig_proj, "example_chart.png", width=800, height=500)
# #             # save_chart_as_image(fig_proj, "project_chart_1.png")   #1
# #             fig_proj.update_traces(texttemplate='%{text:.1f}', textposition='outside')
# #             unique_projects = proj_grouped['Project'].nunique()
# #             fig_proj.update_layout(height=max(500, (unique_projects)*80), plot_bgcolor="#131313", paper_bgcolor="#0E1117", font=dict(color="white"))
# #             st.plotly_chart(fig_proj, use_container_width=True)

# #         # --- SUMMARY TABLE ---
# #         df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
# #         # Filter out project names that are purely numeric or too short
# #         df_summary['Project'] = df_summary['Project'].astype(str).str.strip()
# #         df_summary = df_summary[~df_summary['Project'].str.match(r'^\d+$')]  # remove numeric-only names
# #         df_summary = df_summary[df_summary['Project'].str.len() > 2]         # remove short junk names like '3', '5'

# #         proj_total = df_summary.groupby('Project')['Hours'].sum().reset_index()
# #         proj_total = proj_total[proj_total['Project'] != '']
# #         proj_total.rename(columns={'Hours': 'Total Days'}, inplace=True)

# #         # Plot with legend on the right
# #         fig = px.bar(
# #             proj_total,
# #             x='Total Days',
# #             y='Project',
# #             color='Project',
# #             orientation='h',
# #             height=500,
# #             title='Total Days Spent Per Project'
# #         )
# #         # pio.write_image(fig, "example_chart_2.png", width=800, height=500)

# #         fig.update_layout(
# #             showlegend=True,
# #             legend_title_text="Project",
# #             plot_bgcolor="#131313",
# #             paper_bgcolor="#0E1117",
# #             bargap=0.3,
# #             font=dict(color="white"),
# #             legend=dict(
# #                 orientation="v",
# #                 yanchor="middle",
# #                 y=0.5,
# #                 xanchor="left",
# #                 x=1.02,
# #                 borderwidth=0,
# #                 bgcolor="rgba(0,0,0,0)",
# #             )
# #         )

# #         # st.plotly_chart(fig, use_container_width=True)
# #         # save_chart_as_image(fig, "project_chart_2.png")
# #         pivot = total_summary_table(df_summary)
# #         display_large_table(pivot, f"📊 Employee Project Summary for {month}")

# #         # --- EXPORT OPTION ---
# #         # st.download_button("🧾 Download Summary as Excel", data=generate_excel_download(pivot),
# #         #                    file_name=f"Summary_{month}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# #         # --- INTERACTIVE EMPLOYEE TABLE BY PROJECT ---
# #         st.markdown("### 📌 View Employees Working on Specific Project")
# #         unique_projects_list = sorted(df_summary["Project"].unique())
# #         selected_proj_for_table = st.selectbox("Select a project to see employee contributions", unique_projects_list)

# #         if selected_proj_for_table:
# #             proj_emp_table = project_wise_employee_table(df_summary, selected_proj_for_table)
# #             display_large_table(proj_emp_table, f"💼 Employee Contributions for '{selected_proj_for_table}'")

# #         # --- EMPLOYEE CHART ---
# #         # st.subheader("👥 Total Days Per Employee")
# #         emp_total = df_summary.groupby('Employee')['Hours'].sum().reset_index()
# #         emp_total.rename(columns={"Hours": "Days"}, inplace=True) 
# #         fig_emp = px.bar(emp_total, x='Days', y='Employee', orientation='h', color='Employee')
# #         # save_chart_as_image(fig_emp, "project_chart_3.png")
# #         # st.plotly_chart(fig_emp, use_container_width=True)

# #         # --- PROJECT STACKED ---
# #         # st.subheader("📊 Project-wise Contribution by Employees")
# #         proj_emp_df = df_summary.groupby(['Project', 'Employee'])['Hours'].sum().reset_index()
# #         proj_emp_df.rename(columns={"Hours": "Days"}, inplace=True) 
# #         fig = px.bar(proj_emp_df, x="Project", y="Days", color="Employee", text="Days", barmode="stack")
# #         # save_chart_as_image(proj_emp_df, "project_chart.png")
# #         # st.plotly_chart(fig, use_container_width=True)

# #         # --- MONTH ON MONTH COMPARISON ---
# #         st.subheader(f"📈 Month-on-Month Comparison for {month}")
# #         curr_index = all_months.index(month)
# #         if curr_index == 0:
# #             st.info(f"This is the first month ({month}) in the data. No previous month available for comparison.")
# #             emp_df = df_summary.groupby("Employee")["Hours"].sum().reset_index()
# #             emp_df.rename(columns={"Hours": "Days"}, inplace=True)
# #             proj_df = df_summary.groupby("Project")["Hours"].sum().reset_index()
# #             proj_df.rename(columns={"Hours": "Days"}, inplace=True)
# #             # st.write("🔍 Sample Data Extracted:")
# #             # st.dataframe(df_summary.head(20))

# #             display_large_table(emp_df.set_index("Employee"), f"Employee Summary for {month}")
# #             display_large_table(proj_df.set_index("Project"), f"Project Summary for {month}")
# #         else:
# #             prev_month = all_months[curr_index - 1]
# #             df_prev = analyze_sheets(prev_month)
# #             compare_emp_df = compare_months(df_summary, df_prev, current_month=month, previous_month=prev_month)
# #             compare_proj_df = compare_projects(df_summary, df_prev, current_month=month, previous_month=prev_month)
# #             display_large_table(compare_emp_df, f"📈 Month-on-Month by Employee ({prev_month} vs {month})")
# #             display_large_table(compare_proj_df, f"📈 Month-on-Month by Project ({prev_month} vs {month})")
        
        
# #         st.subheader("🕓 Total Effort Across All Months")

# #         df_all_time = analyze_all_months()
# #         if df_all_time.empty:
# #             st.info("No data found across months.")
# #         else:
# #             df_all_time['Project'] = df_all_time['Project'].astype(str).str.strip()
# #             proj_overall = df_all_time.groupby('Project')['Hours'].sum().reset_index()
# #             proj_overall = proj_overall[proj_overall['Project'].str.len() > 2]
# #             proj_overall.rename(columns={'Hours': 'Actual Days Spent'}, inplace=True)

# #             # Add expected effort
# #             expected_map = get_expected_effort_map()
# #             proj_overall['Expected Days'] = proj_overall['Project'].map(expected_map).fillna(0)

# #             # Calculate variance
# #             proj_overall['Variance'] = proj_overall['Actual Days Spent'] - proj_overall['Expected Days']

# #             # Sort by variance or effort
# #             proj_overall = proj_overall.sort_values(by='Variance', ascending=False)


# #             # Sort descending
# #             proj_overall = proj_overall.sort_values(by='Actual Days Spent', ascending=False)

# #                 # st.dataframe(proj_overall)

# #             # Optional: Add a horizontal bar chart
# #             fig_all = px.bar(
# #                 proj_overall,
# #                 x="Actual Days Spent",
# #                 y="Project",
# #                 orientation="h",
# #                 color="Project",
# #                 title="Total Days Spent per Project (All Months)"
# #             )
# #             fig_all.update_layout(
# #                 plot_bgcolor="#131313",
# #                 paper_bgcolor="#0E1117",
# #                 font=dict(color="white"),
# #                 showlegend=False
# #             )
# #             st.plotly_chart(fig_all, use_container_width=True)
# #             st.dataframe(
# #             proj_overall.style
# #             .format({"Expected Days": "{:.1f}", "Actual Days Spent": "{:.1f}", "Variance": "{:+.1f}"})
# #             .background_gradient(subset=["Variance"], cmap="RdYlGn_r")
# #             )
# #             emp_designation_map = get_designation_map()

# #             st.markdown("### 🧑‍💼 Designation-wise Effort per Project")

# #             if not df_all_time.empty:
# #                 all_projects = sorted(df_all_time["Project"].dropna().unique())
# #                 selected_proj = st.selectbox("Select Project", all_projects, key="designation_project")

# #                 if selected_proj:
# #                     desg_table = get_designation_effort_by_project(df_all_time, emp_designation_map, selected_proj)
# #                     st.dataframe(desg_table.set_index("Designation"), use_container_width=True)
# #             else:
# #                 st.info("No all-time project data found.")



                    
