import os

def aggregate_files(file_list, output_file='snapshot.txt'):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for filename in file_list:
            if os.path.exists(filename):
                outfile.write(f"# File: {filename}\n\n")
                with open(filename, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                outfile.write("\n\n")
            else:
                print(f"Warning: File {filename} not found.")
    
    print(f"Aggregated code saved to {output_file}")

# Example usage
files_to_aggregate = ['templates/base.html','templates/base.html','templates/login.html',
                      'templates/register.html','app.py','init_db.py','schema.sql']
aggregate_files(files_to_aggregate)