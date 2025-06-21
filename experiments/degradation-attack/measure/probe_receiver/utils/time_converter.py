from datetime import datetime
import pytz
import sys


def get_cst(ts):
    utc_time = datetime.strptime(ts, "%Y-%m-%d_%H-%M")

    # Convert UTC to CST (China Standard Time)
    utc_zone = pytz.utc
    cst_zone = pytz.timezone("Asia/Shanghai")
    utc_time = utc_zone.localize(utc_time)  # Localize to UTC
    cst_time = utc_time.astimezone(cst_zone)  # Convert to CST
    return cst_time.strftime("%Y-%m-%d_%H:%M:%S")


def print_dict(dict):
    for key in dict:
        print(key, dict[key])

# line: 2024-12-02_02-30_no-stress/
# Input timestamp in UTC
stress_quic = {}
stress_rand = {}
no_stress = {}

for line in sys.stdin.readlines():
    if "no-stress" in line:
        splits = line.strip().split()
        ts = splits[0].split("_no-stress")[0]
        no_stress[get_cst(ts)] = splits[1]
    elif "stress_quic" in line:
        splits = line.strip().split()
        ts = splits[0].split("_stress_quic")[0]
        stress_quic[get_cst(ts)] = splits[1]
    elif "stress_rand" in line:
        splits = line.strip().split()
        ts = splits[0].split("_stress_rand")[0]
        stress_rand[get_cst(ts)] = splits[1]

print("no_stress")
print_dict(no_stress)
print("stress_quic")
print_dict(stress_quic)
print("stress_rand")
print_dict(stress_rand)
