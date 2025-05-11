#!/usr/bin/env python3

import csv
import sys
import os

def collect_rows(csv_file):
    collected_rows = set()
    with open(csv_file, 'r', newline='') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header row
        for row in csv_reader:
            row_key = tuple(row)  # Use the entire row as the key
            collected_rows.add(row_key)
    return collected_rows

def write_row(output_file, row):
    with open(output_file, 'a', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(row)

def main(input_file_1, input_file_2, output_file):
    # Clear the output file if it exists
    if os.path.exists(output_file):
        os.remove(output_file)

    # Collect rows from the second input file
    collected_rows_2 = collect_rows(input_file_2)

    # Iterate through the first input file and write unmatched rows to the output file
    with open(input_file_1, 'r', newline='') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader)

        # Write header to the output file
        with open(output_file, 'w', newline='') as out_file:
            csv_writer = csv.writer(out_file)
            csv_writer.writerow(header)

        for row in csv_reader:
            row_key = tuple(row)
            if row_key not in collected_rows_2:
                write_row(output_file, row)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python repair_finder_diff.py <input_file_1> <input_file_2> <output_file>")
        sys.exit(1)

    input_file_1 = sys.argv[1]
    input_file_2 = sys.argv[2]
    output_file = sys.argv[3]

    main(input_file_1, input_file_2, output_file)
