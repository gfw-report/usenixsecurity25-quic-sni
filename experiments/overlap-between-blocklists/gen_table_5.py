import pandas as pd

def calculate_jaccard_index(set1, set2):
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    if union == 0:
        return 0.0
    return intersection / union

def read_domains_from_file(fname):
    top10k = []
    with open('./data/tranco-664NX-top-10k.txt') as f:
    	top10k = set(f.readlines())

    with open(fname) as f:
    	return set(f.readlines()).intersection(top10k)

def generate_jaccard_table_with_calculation():
    
    dns_blocklist = read_domains_from_file("./data/dns-blocklist.txt")
    http_blocklist = read_domains_from_file("./data/http-blocklist.txt")
    tls_blocklist = read_domains_from_file("./data/https-blocklist.txt")
    quic_blocklist = read_domains_from_file("./data/quic-blocklist.txt")
    sup_quic = read_domains_from_file("./data/top-10k-supporting-quic.txt")
    random_500 = read_domains_from_file("./data/random-500.txt")

    domain_sets = {
        "DNS": dns_blocklist,
        "HTTP": http_blocklist,
        "TLS": tls_blocklist,
        "QUIC": quic_blocklist,
        "Support QUIC": sup_quic,
        "Random 500": random_500
    }

    headers = list(domain_sets.keys())
    jaccard_matrix = []

    for i, row_header in enumerate(headers):
        row_values = []
        for j, col_header in enumerate(headers):
            if i > j: 
                jaccard_val = calculate_jaccard_index(domain_sets[row_header], domain_sets[col_header])
                row_values.append(f"{jaccard_val:.2f}") 
            elif i == j:
                row_values.append("-") 
            else:
                row_values.append("-") 

        jaccard_matrix.append(row_values)

    df = pd.DataFrame(jaccard_matrix, index=headers, columns=headers)

    print(df.to_string())

if __name__ == "__main__":
    generate_jaccard_table_with_calculation()
