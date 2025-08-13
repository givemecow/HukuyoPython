import cv2
import numpy as np
from hokuyolx import HokuyoLX

def scan_to_xy(scan):
    angles_deg = np.linspace(-135, 135, len(scan))
    angles_rad = np.radians(angles_deg)
    scan_m = np.array(scan, dtype=np.float32) / 1000.0
    xs = scan_m * np.cos(angles_rad)
    ys = scan_m * np.sin(angles_rad)
    return xs, ys

# 라이다 연결
laser = HokuyoLX(addr=('192.168.0.10', 10940))

# 시각화 설정
canvas_size = 800
scale = 100
center = canvas_size // 2
canvas = np.zeros((canvas_size, canvas_size, 3), dtype=np.uint8)

# 한 프레임만 받아와서 저장
for scan, ts, status in laser.iter_dist():
    # ✅ 디버깅: 거리 값 시각화 및 평균 출력
    print("평균 거리(mm):", np.mean(scan))
    print("최대 거리(mm):", np.max(scan))
    print("유효 데이터 수:", np.count_nonzero(scan))

    if np.mean(scan) < 100:
        print("⚠️ 너무 가까운 거리만 인식되고 있습니다.")

    xs, ys = scan_to_xy(scan)

    for x, y in zip(xs, ys):
        px = int(x * scale + center)
        py = int(center - y * scale)
        if 0 <= px < canvas_size and 0 <= py < canvas_size:
            cv2.circle(canvas, (px, py), 1, (0, 255, 0), -1)

    cv2.circle(canvas, (center, center), 3, (0, 0, 255), -1)

    # 이미지로 저장
    cv2.imwrite("Lidar_View.png", canvas)
    print("이미지 저장 완료: Lidar_View.png")
    break  # 한 번만 받고 종료

cv2.destroyAllWindows()
