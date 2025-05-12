#!/usr/bin/env python3

import os
import sqlite3
import requests
import xml.etree.ElementTree as ET
import glob

# --- Configuration ---
QUERIES_FOLDER = "constraint_instances_queries"   # Folder containing your constraint_instances *.rq QUERY files
DB_FILE = "constraints.db"
ENDPOINT_2019 = "BASE_URL/wd2019"
ENDPOINT_2023 = "BASE_URL/wd2023"

# --- Functions ---

def send_sparql_query(query, endpoint_url):
    encoded_query = requests.utils.quote(query)
    url = f"{endpoint_url}?query={encoded_query}"
    headers = {"Accept": "application/sparql-results+xml"}
    
    response = requests.get(url, headers=headers)
    if not response.ok:
        print(f"Error querying {endpoint_url}: {response.status_code}")
        return []

    root = ET.fromstring(response.text)
    results = []
    for result in root.findall('.//{http://www.w3.org/2005/sparql-results#}result'):
        binding_dict = {}
        for binding in result.findall('{http://www.w3.org/2005/sparql-results#}binding'):
            name = binding.attrib['name']
            uri = binding.find('{http://www.w3.org/2005/sparql-results#}uri')
            literal = binding.find('{http://www.w3.org/2005/sparql-results#}literal')
            value = uri.text if uri is not None else (literal.text if literal is not None else None)
            binding_dict[name] = value
        results.append(binding_dict)
    return results

def save_results_to_db(results, table_name, constraint_name, conn):
    cur = conn.cursor()
    for row in results:
        cur.execute(f"""
            INSERT INTO {table_name} (constraint_name, property, constraint_instance, constraint_predicate_parameters, constraint_object_parameters)
            VALUES (?, ?, ?, ?, ?)
        """, (
            constraint_name,
            row.get('property'),
            row.get('constraint_instance'),
            row.get('constraint_predicate_parameters'),
            row.get('constraint_object_parameters')
        ))
    conn.commit()

def setup_database(conn):
    cur = conn.cursor()

    # Create tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS constraint_instances_2019 (
            constraint_name TEXT, property TEXT, constraint_instance TEXT,
            constraint_predicate_parameters TEXT, constraint_object_parameters TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS constraint_instances_2023 (
            constraint_name TEXT, property TEXT, constraint_instance TEXT,
            constraint_predicate_parameters TEXT, constraint_object_parameters TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dados_adicionados (
            constraint_name TEXT, property TEXT, constraint_instance TEXT,
            constraint_predicate_parameters TEXT, constraint_object_parameters TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dados_removidos (
            constraint_name TEXT, property TEXT, constraint_instance TEXT,
            constraint_predicate_parameters TEXT, constraint_object_parameters TEXT
        )
    """)

    # Create indexes
    cur.execute("CREATE INDEX IF NOT EXISTS ind1 ON constraint_instances_2023 (constraint_name, property, constraint_predicate_parameters, constraint_object_parameters)")
    cur.execute("CREATE INDEX IF NOT EXISTS ind2 ON constraint_instances_2023 (constraint_instance, constraint_predicate_parameters)")
    cur.execute("CREATE INDEX IF NOT EXISTS ind_1 ON constraint_instances_2019 (constraint_name, property, constraint_predicate_parameters, constraint_object_parameters)")
    cur.execute("CREATE INDEX IF NOT EXISTS ind_2 ON constraint_instances_2019 (constraint_instance, constraint_predicate_parameters)")
    
    conn.commit()

def compare_and_fill_differences(conn):
    cur = conn.cursor()

    # Dados adicionados: 2023 - 2019
    cur.execute("""
        INSERT INTO dados_adicionados
        SELECT * FROM constraint_instances_2023
        EXCEPT
        SELECT * FROM constraint_instances_2019
    """)

    # Dados removidos: 2019 - 2023
    cur.execute("""
        INSERT INTO dados_removidos
        SELECT * FROM constraint_instances_2019
        EXCEPT
        SELECT * FROM constraint_instances_2023
    """)
    
    conn.commit()

def main():
    conn = sqlite3.connect(DB_FILE)
    setup_database(conn)

    # Read all SPARQL query files
    query_files = glob.glob(os.path.join(QUERIES_FOLDER, "*.rq"))

    for query_file in query_files:
        with open(query_file, 'r', encoding='utf-8') as f:
            query = f.read()
        
        constraint_name = os.path.basename(query_file).replace(".rq", "").replace("constraints_", "")
        print(f"Processing constraint: {constraint_name}")

        # Query both endpoints
        results_2019 = send_sparql_query(query, ENDPOINT_2019)
        results_2023 = send_sparql_query(query, ENDPOINT_2023)

        print(f" - 2019 results: {len(results_2019)} rows")
        print(f" - 2023 results: {len(results_2023)} rows")

        # Save into the database
        save_results_to_db(results_2019, "constraint_instances_2019", constraint_name, conn)
        save_results_to_db(results_2023, "constraint_instances_2023", constraint_name, conn)

    # Compare and fill added/removed
    print("Comparing differences...")
    compare_and_fill_differences(conn)
    print("Done!")

    conn.close()

if __name__ == "__main__":
    main()
