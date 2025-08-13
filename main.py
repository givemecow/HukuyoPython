import numpy as np
from hokuyolx import HokuyoLX
from pythonosc import udp_client
import pickle
import os

# 라이다 거리 데이터 XY 좌표로 변환
def scan_to_xy(scan):
    angles_deg = np.linspace(-135, 135, len(scan))
    angles_rad = np.radians(angles_deg)
    scan_m = np.array(scan, dtype=np.float32) / 1000.0
    xs = scan_m * np.cos(angles_rad)
    ys = scan_m * np.sin(angles_rad)
    return xs, ys


# OSC 클라이언트 설정
osc_ip = "127.0.0.1"
osc_port = 8000
osc_client = udp_client.SimpleUDPClient(osc_ip, osc_port)

# 라이다 연결
laser = HokuyoLX(addr=('192.168.0.10', 10940))

# 캘리브레이션 파일 로드 또는 생성
baseline_path = "baseline_scan.pkl"
if os.path.exists(baseline_path):
    with open(baseline_path, "rb") as f:
        baseline_scan = pickle.load(f)
    print("[INFO] 기존 baseline 로드 완료")
else:
    print("[INFO] baseline 캘리브레이션 중...")
    _, baseline_scan = laser.get_dist()
    with open(baseline_path, "wb") as f:
        pickle.dump(baseline_scan, f)
    print("[INFO] baseline 저장 완료")

# 무시할 고정 포인트 (지속적으로 흔들리는 지점)
ignored_indices = {}

# 변화 감지 및 전송
threshold = 100  # mm 단위
for scan, ts, status in laser.iter_dist():
    scan_np = np.array(scan, dtype=np.float32)
    baseline_np = np.array(baseline_scan, dtype=np.float32)
    diff = np.abs(scan_np - baseline_np)

    # 변화량이 threshold 이상이고, 무시 리스트에 포함되지 않은 인덱스만 선택
    changed_indices = [i for i in np.where(diff > threshold)[0] if i not in ignored_indices]

    if len(changed_indices) > 0:
        xs, ys = scan_to_xy(scan_np)
        changed_points = [(xs[i], ys[i]) for i in changed_indices]
        flat_points = [v for pair in changed_points for v in pair]

        osc_client.send_message("/lidar", flat_points)

        print(f"[SEND] {len(changed_points)} points changed")
        for i in changed_indices:
            x, y = xs[i], ys[i]
            distance_diff = diff[i]
            print(f"  Point {i}: x = {x:.3f} m, y = {y:.3f} m, Δd = {distance_diff:.1f} mm")
    else:
        print("[INFO] 변화 없음")