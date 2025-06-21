from scapy.all import rdpcap
from collections import Counter
import folium
import requests

def get_geolocation_local(ip):

    ip_coords = {
        "15.168.0.0": (34.6937, 135.502),
        "43.216.0.0": (3.1408, 101.6852),
        "43.218.0.0": (-6.1741, 106.8296),
        "43.198.0.0": (22.3964, 114.109),
        "18.141.0.0": (1.28009, 103.851),
        "13.203.0.0": (19.076, 72.8777),
        "43.208.0.0": (13.7551, 100.5057),
        "16.50.0.0": (-37.8159, 144.9669),
        "13.209.0.0": (37.5665, 126.978),
        "3.27.0.0": (-33.8591, 151.2002),
        "52.68.0.0": (35.6895, 139.692),
        "3.71.0.0": (50.1109, 8.68213),
        "51.96.0.0": (47.3643, 8.5437),
        "13.57.0.0": (37.3394, -121.895),
        "52.50.0.0": (53.3498, -6.26031),
        "35.94.0.0": (45.5235, -122.676),
        "35.179.0.0": (51.5074, -0.127758),
        "13.38.0.0": (48.8566, 2.35222),
        "40.176.0.0": (51.0406, -114.0764),
        "13.60.0.0": (59.3293, 18.0686),
        "3.142.0.0": (40.0992, -83.1141),
        "15.156.0.0": (43.6532, -79.3832),
        "3.95.0.0": (39.0438, -77.4874),
        "51.17.0.0": (32.0804, 34.7807),
        "15.185.0.0": (26.2167, 50.5833),
        "51.112.0.0": (25.0734, 55.2979),
        "15.229.0.0": (-23.5505, -46.6333),
        "13.245.0.0": (-26.2041, 28.0473),
        "18.61.0.0": (17.3753, 78.4744),
        "15.161.0.0": (45.4681, 9.2011),
        "51.92.0.0": (41.6579, -0.8777),
        "78.12.0.0": (20.5879, -100.3879),
    }


    try:
        coords = ip_coords.get(ip)
        if coords:
            return coords
        else:
            print(f"Error:")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_geolocation(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        if data['status'] == 'success':
            return (data['lat'], data['lon'])
        else:
            print(f"Error: {data['message']}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def count_packets_per_source_ip(pcap_file):
    packets = rdpcap(pcap_file)
    src_ip_counter = Counter()
    for pkt in packets:
        if 'IP' in pkt:
            src_ip = pkt['IP'].src
            src_ip_counter[src_ip] += 1

    return src_ip_counter


def get_color_for_density(packet_count, max_count):
    intensity = packet_count / max_count
    red = int(255 * (1 - intensity))
    green = int(255 * intensity)
    return f"#{red:02x}{green:02x}00"


def wrap_longitude(lon):
    if lon < 0:
        return lon + 360
    return lon


def plot_geolocated_ips(ip_counter):
    m = folium.Map(location=[0, 180], zoom_start=2)

    max_packets = max(ip_counter.values())
    point_counter = 0
    for ip, count in ip_counter.items():
        location = get_geolocation_local(ip)
        if location:
            point_counter += 1
            lat, lon = location
            color = get_color_for_density(count, max_packets)

            folium.CircleMarker(
                location=[lat, lon],
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=f"IP: {ip}, Packets: {count}"
            ).add_to(m)

            wrapped_lon = wrap_longitude(lon)
            folium.CircleMarker(
                location=[lat, wrapped_lon],
                radius=5,  # Fixed radius
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=f"IP: {ip}, Packets: {count} (wrapped longitude)"
            ).add_to(m)
    print(point_counter)
    special_ips = ["8.134.0.0", "103.152.0.0"]
    for special_ip in special_ips:
        special_location = get_geolocation(special_ip)
        if special_ip == "103.152.0.0":
            special_location = (37.3387, -121.8853)
        if special_location:
            lat, lon = special_location
            folium.CircleMarker(
                location=[lat, lon],
                radius=5,  # Fixed radius
                color="black",
                fill=True,
                fill_color="black",
                fill_opacity=0.8,
                popup=f"IP: {special_ip} (special point)"
            ).add_to(m)

            wrapped_lon = wrap_longitude(lon)
            folium.CircleMarker(
                location=[lat, wrapped_lon],
                radius=5,
                color="black",
                fill=True,
                fill_color="black",
                fill_opacity=0.8,
                popup=f"IP: {special_ip} (wrapped special point)"
            ).add_to(m)

    m.save("ip_density_map.html")


if __name__ == "__main__":
    pcap_file = '01_22_25/server_during_anon.pcap'
    ip_counter = count_packets_per_source_ip(pcap_file)
    plot_geolocated_ips(ip_counter)
