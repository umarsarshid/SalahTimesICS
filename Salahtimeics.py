# Import Module 
import tabula 
import pandas as pd
import re
from ics import Calendar, Event
from datetime import timedelta
import pytz



# Function to ensure times are PM for specific columns
def ensure_pm(time_str):
    if time_str is not None:
        time_parts = time_str.split(':')
        if len(time_parts) == 2:
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            # If hour is not 12, adjust to PM
            if hour < 12:
                hour += 12  # Convert to PM
            return f"{hour}:{minute:02d}"  # Return as 'HH:MM'
    return time_str

# Function to convert datetime from PST to GMT
def convert_from_pst_to_gmt(dt):
    if dt is not None:
        # Localize the naive timestamp to PST
        pst_tz = pytz.timezone('America/Los_Angeles')  # Pacific Time (PST/PDT)
        dt = pst_tz.localize(dt)  # Localize to PST

        # Convert to GMT
        gmt_tz = pytz.timezone('GMT')
        return dt.astimezone(gmt_tz)  # Convert to GMT
    return dt

# Step 0: Read PDF File 
df = tabula.read_pdf('/Users/umararshid/Programming/Salahtimes/SalahTimes.pdf', pages = 1)[0]
# Convert into Excel File 
df.to_csv('Salahtimes.csv')

# Step 1: Load the CSV and skip the first 5 lines
def load_and_clean_csv(file_path):
    # Skip first 5 lines that are not part of the table
    df = pd.read_csv(file_path, skiprows=5, header=None)
    
    # Step 2: Rename the columns (accounting for the extra columns)
    df.columns = ['index', 'Date', 'Empty', 'Islamic date', 'Fajr', 'Fajr at Masjid', 'Ishraaq', 
                  'Zawaal', 'Dhuhr', 'Asr (Shafi)', 'Asr (Hanafi)', 'Asr at Masjid', 
                  'Maghrib', 'Isha', 'Isha at Masjid', '1st Jummah']
    
    # Step 3: Convert the 'Date' column to a datetime object (October 2024)
    df['Date'] = pd.to_datetime(df['Date'].apply(lambda x: f"2024-10-{x.split()[1]}"), format='%Y-%m-%d')
    
    # Step 4: Clean the rest of the rows to remove extra text after the time
    time_columns = ['Fajr', 'Fajr at Masjid', 'Ishraaq', 'Zawaal', 'Dhuhr', 'Asr (Shafi)', 
                    'Asr (Hanafi)', 'Asr at Masjid', 'Maghrib', 'Isha', 'Isha at Masjid', '1st Jummah']
    
    # Define a function to keep only the time part and remove any trailing text
    def clean_time(time_str):
        # Remove leading/trailing whitespace and replace multiple spaces with a single space
        cleaned_str = re.sub(r'\s+', ' ', str(time_str).strip())
        
        # Regex to match only the time part (e.g., '5:33', '1:03') and remove anything after it
        match = re.match(r'^(\d{1,2}):(\d{2})$', cleaned_str)
        
        # If match is found, return formatted time, otherwise return None
        if match:
            return f"{int(match.group(1)):d}:{match.group(2)}"  # Format to ensure no leading zero on hour
        return None  # Return None if no valid time found

    
    # Apply the cleaning function to each relevant column
    for col in time_columns:
        df[col] = df[col].apply(clean_time)
    
    # Step 5: Ensure PM for all prayer times after Zawaal
    pm_columns = ['Zawaal','Dhuhr', 'Asr (Shafi)', 'Asr (Hanafi)', 'Asr at Masjid', 'Maghrib', 'Isha', 'Isha at Masjid', '1st Jummah']
    for col in pm_columns:
        df[col] = df[col].apply(ensure_pm)

    # Combine the date and time into full timestamps
    for col in time_columns:
        df[col] = df.apply(lambda row: pd.to_datetime(f"{row['Date'].date()} {row[col]}", errors='coerce'), axis=1)

    return df


# Step 6: Create .ics file based on selected columns
def create_ics(df, selected_columns, output_file='salah_times.ics'):
    calendar = Calendar()
    
    # Set the timezone for the calendar
    pacific_tz = pytz.timezone('America/Los_Angeles')
    
    # Step 7: Add events to the calendar based on selected prayer times
    for index, row in df.iterrows():
        for col in selected_columns:
            if pd.notna(row[col]):  # Only create events for non-null times
                event = Event()
                event.name = f"{col.replace('_', ' ').capitalize()} Prayer"
                
                # Convert event time to Pacific Time
                event.begin = convert_from_pst_to_gmt(row[col])
                # event.begin = row[col]
                event.duration = timedelta(minutes=15)  # Set default duration for each prayer event
                event.description = f"{col.replace('_', ' ').capitalize()} prayer time."  # Optional description
                event.location = "Your Mosque Name"  # Optional location

                # Set a unique UID for the event (could be based on date and prayer name)
                event.uid = f"{event.name.replace(' ', '_')}_{event.begin.strftime('%Y%m%dT%H%M%S')}@yourdomain.com"
                
                calendar.events.add(event)
    
    # Step 8: Save the .ics file
    with open(output_file, 'w') as f:
        f.writelines(str(calendar))
    
    print(f".ics file created: {output_file}")

# Step 9: Save the cleaned CSV with the new column names and format
def save_cleaned_csv(df, output_path):
    df.to_csv(output_path, index=False)
    print(f"Cleaned CSV saved to {output_path}")


# Example usage
def main():
    csv_file_path = '/Users/umararshid/Programming/Salahtimes/Salahtimes.csv'  # Replace with your input CSV file path
    output_csv_path = '/Users/umararshid/Programming/Salahtimes/Salahtimesupdated.csv'  # Replace with desired output path
    output_ics_path = 'salah_times.ics'  # Replace with desired output .ics file path
    
    # Step 1: Load and clean the CSV
    cleaned_df = load_and_clean_csv(csv_file_path)
    
    # Step 2: Save the cleaned CSV
    save_cleaned_csv(cleaned_df, output_csv_path)
    
    # Step 3: Ask user to select which columns to include in the .ics file
    print("Available prayer times:")
    time_columns = ['Fajr', 'Fajr at Masjid', 'Ishraaq', 'Zawaal', 'Dhuhr', 
                    'Asr (Shafi)', 'Asr (Hanafi)', 'Asr at Masjid', 'Maghrib', 
                    'Isha', 'Isha at Masjid', '1st Jummah']
    
    for i, col in enumerate(time_columns):
        print(f"{i + 1}. {col}")
    
    selected = input("Enter the numbers of the columns you want to include in the .ics file (comma separated, e.g., 1,3,5): ")
    selected_columns = [time_columns[int(num) - 1] for num in selected.split(",")]
    
    # Step 4: Create the .ics file with the selected columns
    create_ics(cleaned_df, selected_columns, output_file=output_ics_path)

# Run the main function
if __name__ == "__main__":
    main()
