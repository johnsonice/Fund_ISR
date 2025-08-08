import os
import pandas as pd
import glob
from pathlib import Path
import re
import argparse
from tqdm import tqdm

def process_csv_to_excel_as_tabs(input_folder, output_excel_file):
    """
    Read all CSV files in a folder and create an Excel file with each CSV as a separate tab.
    
    Args:
        input_folder (str): Path to folder containing CSV files
        output_excel_file (str): Path to output Excel file
    """
    # Get all CSV files in the input folder
    csv_files = glob.glob(os.path.join(input_folder, "*.csv"))
    if not csv_files:
        print(f"No CSV files found in {input_folder}")
        return
    print(f"Found {len(csv_files)} CSV files")
    
    # Create Excel writer
    with pd.ExcelWriter(output_excel_file, engine='openpyxl') as writer:
        # Use tqdm to show progress
        for csv_file in tqdm(csv_files, desc="Processing CSV files"):
            try:
                # Read CSV file
                df = pd.read_csv(csv_file)
                # Get the filename without extension to use as the sheet name
                sheet_name = Path(csv_file).stem
                # Clean sheet name (Excel has a 31 character limit and restricts certain characters)
                sheet_name = re.sub(r'[\[\]:*?/\\]', '', sheet_name)[:31]
                # Write DataFrame to Excel sheet
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            except Exception as e:
                print(f"Error processing {os.path.basename(csv_file)}: {str(e)}")
    print(f"Successfully created Excel file: {output_excel_file}")

def process_csv_to_excel_append(input_folder, output_excel_file):
    # Get all CSV files in the input folder
    csv_files = glob.glob(os.path.join(input_folder, "*.csv"))
    if not csv_files:
        print(f"No CSV files found in {input_folder}")
        return
    print(f"Found {len(csv_files)} CSV files")
    
    # Also create a combined sheet with all CSV files
    print("Creating combined Excel file with all data...")
    all_data = []
    # Process each CSV file
    for csv_file in tqdm(csv_files, desc="Combining CSV files"):
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            # Add filename as identifier
            df['source_file'] = Path(csv_file).stem
            # Append to list
            all_data.append(df)
        except Exception as e:
            print(f"Error processing {os.path.basename(csv_file)} for combined sheet: {str(e)}")
    # Combine all dataframes
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        # Create output path for combined file
        combined_output_file = os.path.splitext(output_excel_file)[0] + "_combined.xlsx"
        # Save to Excel
        combined_df.to_excel(combined_output_file, index=False)
        print(f"Successfully created combined Excel file: {combined_output_file}")
    else:
        print("No data to combine into a single sheet")

if __name__ == "__main__":
    
    input_folder = Path('/ephemeral/home/xiong/data/Fund/RAM_Table/RAM_Table_Examples_Outputs_v2/clean')
    output_excel_tabs = Path('/ephemeral/home/xiong/data/Fund/RAM_Table/RAM_2022-2025_by_doc.xlsx')
    output_excel_agg = Path('/ephemeral/home/xiong/data/Fund/RAM_Table/RAM_2022-2025_agg.xlsx')
    
    process_csv_to_excel_as_tabs(input_folder,output_excel_tabs)
    process_csv_to_excel_append(input_folder,output_excel_agg)