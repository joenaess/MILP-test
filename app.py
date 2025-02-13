import streamlit as st
import pandas as pd
import pulp
import random
import io

# --- Function to Generate Mock Data ---
def generate_mock_data(num_employees=10, num_shifts=3, num_days=7):
    skills = ["RN", "LPN", "CNA"]
    employee_data = []
    for i in range(num_employees):
        employee_id = f"E{i+1}"
        skill = random.choice(skills)
        max_hours = random.randint(30, 48)
        availability = {day: [1] * num_shifts for day in range(num_days)}
        for day in range(num_days):
            for shift in range(num_shifts):
                if random.random() < 0.2:
                    availability[day][shift] = 0
        employee_data.append([employee_id, skill, max_hours, availability])
    employee_df = pd.DataFrame(employee_data, columns=["employee_id", "skill", "max_hours", "availability"])
    employee_df.set_index("employee_id", inplace=True)
    employee_df['availability'] = employee_df['availability'].apply(lambda x: str(x)) # String for CSV

    shift_data = []
    shift_names = ["Day", "Evening", "Night"]
    for shift_name in shift_names:
        required_staff = {skill: random.randint(0, 2) for skill in skills}
        shift_length = 8
        shift_data.append([shift_name, required_staff, shift_length])
    shift_df = pd.DataFrame(shift_data, columns=["shift_id", "required_staff", "shift_length"])
    shift_df.set_index("shift_id", inplace=True)
    shift_df['required_staff'] = shift_df['required_staff'].apply(lambda x: str(x))
    return employee_df, shift_df

# --- Function to Solve the MILP Model ---
def solve_schedule(employee_df, shift_df):
    # Convert string representations back to dictionaries
    employee_df['availability'] = employee_df['availability'].apply(eval)
    shift_df['required_staff'] = shift_df['required_staff'].apply(eval)

    num_days = len(employee_df['availability'].iloc[0]) # Get num_days from availability
    shifts = shift_df.index.tolist()
    employees = employee_df.index.tolist()

    model = pulp.LpProblem("Nursing_Home_Scheduling", pulp.LpMinimize)
    x = pulp.LpVariable.dicts("schedule",
                              [(employee, shift, day)
                               for employee in employees
                               for shift in shifts
                               for day in range(num_days)],
                              cat='Binary')

    # Objective: Minimize total shifts (simple example)
    model += pulp.lpSum(x[employee, shift, day]
                        for employee in employees
                        for shift in shifts
                        for day in range(num_days)), "Total_Shifts"

    # Constraints
    for day in range(num_days):
        for shift in shifts:
            for skill, required in shift_df.loc[shift, "required_staff"].items():
                model += pulp.lpSum(x[employee, shift, day]
                                    for employee in employees
                                    if employee_df.loc[employee, "skill"] == skill) >= required, f"Staffing_{skill}_{shift}_{day}"

    for employee in employees:
        for day in range(num_days):
            model += pulp.lpSum(x[employee, shift, day] for shift in shifts) <= 1, f"One_Shift_{employee}_{day}"

    for employee in employees:
        model += pulp.lpSum(x[employee, shift, day] * shift_df.loc[shift, "shift_length"]
                            for shift in shifts
                            for day in range(num_days)) <= employee_df.loc[employee, "max_hours"], f"Max_Hours_{employee}"

    for employee in employees:
        for day in range(num_days):
            for shift_index, shift in enumerate(shifts):
                if employee_df.loc[employee, "availability"][day][shift_index] == 0:
                    model += x[employee, shift, day] == 0, f"Availability_{employee}_{shift}_{day}"

    model.solve()

    if pulp.LpStatus[model.status] == 'Optimal':
        schedule_data = []
        for day in range(num_days):
            for shift in shifts:
                for employee in employees:
                    if x[employee, shift, day].varValue > 0.9:
                        schedule_data.append([day, shift, employee, employee_df.loc[employee, 'skill']])
        schedule_df = pd.DataFrame(schedule_data, columns=['Day', 'Shift', 'Employee', 'Skill'])
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        schedule_df['Day'] = schedule_df['Day'].map(lambda d: day_names[d % 7]) #handle more than 7 days.
        return schedule_df, "Optimal"
    else:
        return None, pulp.LpStatus[model.status]

# --- Streamlit App ---
st.title("Nursing Home Staff Scheduler")

# File Uploader
uploaded_file = st.file_uploader("Upload employee data CSV (optional)", type="csv")

# Choose Data Source
use_mock_data = st.checkbox("Use Mock Data", value=True)  # Default to mock data

if use_mock_data:
    num_employees = st.sidebar.number_input("Number of Employees", min_value=5, max_value=50, value=10, step=1)
    num_days = st.sidebar.number_input("Number of Days", min_value=1, max_value=30, value=7, step=1) # Allow more days.
    employee_df, shift_df = generate_mock_data(num_employees=num_employees, num_days=num_days)
    st.write("Using Mock Data:")
    st.write("Employee Data:")
    st.dataframe(employee_df)
    st.write("Shift Data:")
    st.dataframe(shift_df)


elif uploaded_file is not None:
    try:
        employee_df = pd.read_csv(uploaded_file, index_col="employee_id")
        shift_file = st.file_uploader("Upload shift data CSV", type="csv") #Separate file uploader
        if shift_file is not None:
            shift_df = pd.read_csv(shift_file, index_col="shift_id")

            st.write("Using Uploaded Data:")
            st.write("Employee Data:")
            st.dataframe(employee_df)
            st.write("Shift Data:")
            st.dataframe(shift_df)
        else:
            st.stop() #Stop if shift file not uploaded.

    except Exception as e:
        st.error(f"Error reading CSV: {e}.  Please ensure the CSV is formatted correctly.")
        st.stop()

else: #No file, no mock.
    st.stop()


# Run Optimization
if st.button("Generate Schedule"):
    with st.spinner("Generating schedule..."):  # Show a spinner while solving
        schedule_df, status = solve_schedule(employee_df, shift_df)

    if status == "Optimal":
        st.success("Schedule generated successfully!")
        st.write("Optimal Schedule:")
        st.dataframe(schedule_df)

        # Download link for schedule
        csv = schedule_df.to_csv(index=False)
        st.download_button(
            label="Download schedule as CSV",
            data=csv,
            file_name="nursing_home_schedule.csv",
            mime="text/csv",
        )
    else:
        st.error(f"Optimization failed. Status: {status}")