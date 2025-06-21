from scapy.all import rdpcap
from collections import Counter

ip_region_map = {
    '18.61.0.0':'ap-south-2',
    '13.203.0.0':'ap-south-1',
    '15.161.0.0':'eu-south-1',
    '51.92.0.0':'eu-south-2',
    '51.112.0.0':'me-central-1',
    '51.17.0.0':'il-central-1',
    '15.156.0.0':'ca-central-1',
    '78.12.0.0':'mx-central-1',
    '3.71.0.0':'eu-central-1',
    '51.96.0.0':'eu-central-2',
    '35.94.0.0':'us-west-2',
    '13.245.0.0':'af-south-1',
    '13.60.0.0':'eu-north-1',
    '13.38.0.0':'eu-west-3',
    '35.179.0.0':'eu-west-2',
    '52.50.0.0':'eu-west-1',
    '15.168.0.0':'ap-northeast-3',
    '13.209.0.0':'ap-northeast-2',
    '15.185.0.0':'me-south-1',
    '15.229.0.0':'sa-east-1',
    '43.198.0.0':'ap-east-1',
    '40.176.0.0':'ca-west-1',
    '3.27.0.0':'ap-southeast-2',
    '43.218.0.0':'ap-southeast-3',
    '16.50.0.0':'ap-southeast-4',
    '43.216.0.0':'ap-southeast-5',
    '3.142.0.0':'us-east-2',
    '43.208.0.0':'ap-southeast-7',
    '18.141.0.0':'ap-southeast-1',
    '13.57.0.0':'us-west-1',
    '52.68.0.0':'ap-northeast-1',
    '3.95.0.0':'us-east-1',
}

region_common_map = {
    'ap-south-2': 'Asia Pacific (Hyderabad)',
    'ap-south-1': 'Asia Pacific (Mumbai)',
    'eu-south-1': 'Europe (Milan)',
    'eu-south-2': 'Europe (Spain)',
    'me-central-1': 'Middle East (UAE)',
    'il-central-1': 'Israel (Tel Aviv)',
    'ca-central-1': 'Canada (Central)',
    'mx-central-1': 'Mexico (Central)',
    'eu-central-1': 'Europe (Frankfurt)',
    'eu-central-2': 'Europe (Zurich)',
    'us-west-2': 'US West (Oregon)',
    'af-south-1': 'Africa (Cape Town)',
    'eu-north-1': 'Europe (Stockholm)',
    'eu-west-3': 'Europe (Paris)',
    'eu-west-2': 'Europe (London)',
    'eu-west-1': 'Europe (Ireland)',
    'ap-northeast-3': 'Asia Pacific (Osaka)',
    'ap-northeast-2': 'Asia Pacific (Seoul)',
    'me-south-1': 'Middle East (Bahrain)',
    'sa-east-1': 'South America (Sao Paulo)',
    'ap-east-1': 'Asia Pacific (Hong Kong)',
    'ca-west-1': 'Canada (Calgary)',
    'ap-southeast-2': 'Asia Pacific (Sydney)',
    'ap-southeast-3': 'Asia Pacific (Jakarta)',
    'ap-southeast-4': 'Asia Pacific (Melbourne)',
    'ap-southeast-5': 'Asia Pacific (Malaysia)',
    'us-east-2': 'US East (Ohio)',
    'ap-southeast-7': 'Asia Pacific (Thailand)',
    'ap-southeast-1': 'Asia Pacific (Singapore)',
    'us-west-1': 'US West (N. California)',
    'ap-northeast-1': 'Asia Pacific (Tokyo)',
    'us-east-1': 'US East (N. Virginia)',
}

def count_packets_per_source_ip(pcap_file):
    packets = rdpcap(pcap_file)
    src_ip_counter = Counter()
    for pkt in packets:
        if 'IP' in pkt:
            src_ip = pkt['IP'].src
            src_ip_counter[src_ip] += 1

    return src_ip_counter

def gen_table(ip_counter):
# Generate LaTeX table
    header = "\\begin{table}[h!]\n\\small\n\\centering\n\\begin{tabular}{lr}"
    columns = "\\toprule\n{Common Name} & {Count (\\% of 360)} \\\\ \\midrule"
    rows = []

    for ip, count in sorted(ip_counter.items(), key=lambda x: region_common_map.get(ip_region_map.get(x[0], "Unknown"), "Unknown")):
        region = ip_region_map.get(ip, "Unknown")
        common_name = region_common_map.get(region, "Unknown")
        percent = (count / 360) * 100
        rows.append(f"{common_name} & {count} ({percent:.2f}\\%) \\\\")

    footer = "\\bottomrule\n\\end{tabular}\n\\caption{Summary of AWS region data.}\n\\label{tab:aws-region-data}\n\\end{table}"

    latex_table = "\n".join([header, columns] + rows + [footer])
    return latex_table

if __name__ == "__main__":
    pcap_file = '01_22_25/server_during_anon.pcap'
    ip_counter = count_packets_per_source_ip(pcap_file)
    print(gen_table(ip_counter))
