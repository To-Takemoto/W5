import numpy as np
#import math

# 準ユリウス日
def calculate_mjd(year: int, month :int, day :int, hour:int=0, minute:int=0, second:float=0.0):
    """
    年月日時分秒からMJD (準ユリウス日) を計算する

    Parameters:
        year (int): 年
        month (int): 月
        day (int): 日
        hour (int): 時 (デフォルト: 0)
        minute (int): 分 (デフォルト: 0)
        second (float): 秒 (デフォルト: 0.0)

    Returns:
        float: MJD (準ユリウス日)
    """
    a = int((14 - month) / 12)
    y = year + 4800 - a
    m = month + 12 * a - 3

    jd = day + int((153 * m + 2) / 5) + 365 * y + int(y / 4) - int(y / 100) + int(y / 400) - 32045
    jd += (hour + minute / 60.0 + second / 3600.0) / 24.0

    mjd = jd - 2400000.5

    return mjd



def calc_greenwich_sidereal_time(mjd):
    """
    準ユリウス日(MJD)からグリニッジ恒星時(θG)を計算する

    Parameters:
        mjd (float): 準ユリウス日

    Returns:
        float: グリニッジ恒星時(θG) [時間]
    """

    # 定数
    MJD_0 = 51544.5

    # 計算
    T = (mjd - MJD_0) / 36525.0
    theta_G = 24.065709 + 8640184.812866 * T + 0.093104 * T**2 - 6.2E-6 * T**3

    # 0~24時間の範囲に納める
    theta_G = theta_G % 24.0

    return theta_G


# 地方恒星時、時角の計算
def calc_local_hour_angle(greenwich_sidereal_time, longitude, ra):
    local_sidereal_time = greenwich_sidereal_time - longitude / 15.0
    local_sidereal_time %= 24.0
    hour_angle = local_sidereal_time - ra / 15.0
    return hour_angle

# 方位角、高度の計算
def calc_azimuth_altitude(latitude, declination, hour_angle):
    phi = np.deg2rad(latitude)
    dec = np.deg2rad(declination)
    H = np.deg2rad(hour_angle)

    # 座標変換行列
    Az_matrix = np.array([
        [-np.sin(H), np.cos(H), 0],
        [-np.cos(H) * np.sin(phi), -np.sin(phi) * np.sin(H), np.cos(phi)],
        [np.cos(H) * np.cos(phi), np.sin(phi) * np.cos(H), np.sin(phi)]
    ])

    # 赤緯赤経ベクトル
    radec_vector = np.array([np.cos(dec) * np.cos(H), np.cos(dec) * np.sin(H), np.sin(dec)])

    # 方位角・高度ベクトル
    azalt_vector = Az_matrix.T @ radec_vector

    azimuth = np.rad2deg(np.arctan2(azalt_vector[1], azalt_vector[0])) % 360
    altitude = np.rad2deg(np.arcsin(azalt_vector[2]))

    return azimuth, altitude

def seiza_doko(latitude, longitude, declination, ra, year, month, day, hour=0, minute=0, second=0.0):
    mjd = calculate_mjd(year, month, day, hour, minute, second)
    greenwich_sidereal_time = calc_greenwich_sidereal_time(mjd)
    hour_angle = calc_local_hour_angle(greenwich_sidereal_time, longitude, ra)
    azimuth, altitude = calc_azimuth_altitude(latitude, declination, hour_angle)

    print(f"方位角: {azimuth:.2f}度, 高度: {altitude:.2f}度")


def test():
    # 使用例
    # 例: ベテルギウス（オリオン座）の位置計算
    latitude = 35.6895  # 観測地点の緯度（東京）
    longitude = 139.6917  # 観測地点の経度（東京）
    declination = 7.4071  # ベテルギウスの赤緯（度）
    ra = 88.7929  # ベテルギウスの赤経（度）

    year = 2024
    month = 5
    day = 19
    hour = 22
    minute = 0
    second = 0

    seiza_doko(latitude, longitude, declination, ra, year, month, day, hour, minute, second)

test()