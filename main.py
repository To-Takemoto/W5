from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import io
import base64

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def calculate_mjd(year: int, month :int, day :int, hour:int=0, minute:int=0, second:float=0.0):
    a = int((14 - month) / 12)
    y = year + 4800 - a
    m = month + 12 * a - 3

    jd = day + int((153 * m + 2) / 5) + 365 * y + int(y / 4) - int(y / 100) + int(y / 400) - 32045
    jd += (hour + minute / 60.0 + second / 3600.0) / 24.0

    mjd = jd - 2400000.5

    return mjd

def calc_greenwich_sidereal_time(mjd):
    MJD_0 = 51544.5
    T = (mjd - MJD_0) / 36525.0
    theta_G = 24.065709 + 8640184.812866 * T + 0.093104 * T**2 - 6.2E-6 * T**3
    theta_G = theta_G % 24.0
    return theta_G

def calc_local_hour_angle(greenwich_sidereal_time, longitude, ra):
    local_sidereal_time = greenwich_sidereal_time - longitude / 15.0
    local_sidereal_time %= 24.0
    hour_angle = local_sidereal_time - ra / 15.0
    return hour_angle

def calc_azimuth_altitude(latitude, declination, hour_angle):
    phi = np.deg2rad(latitude)
    dec = np.deg2rad(declination)
    H = np.deg2rad(hour_angle)

    Az_matrix = np.array([
        [-np.sin(H), np.cos(H), 0],
        [-np.cos(H) * np.sin(phi), -np.sin(phi) * np.sin(H), np.cos(phi)],
        [np.cos(H) * np.cos(phi), np.sin(phi) * np.cos(H), np.sin(phi)]
    ])

    radec_vector = np.array([np.cos(dec) * np.cos(H), np.cos(dec) * np.sin(H), np.sin(dec)])

    azalt_vector = Az_matrix.T @ radec_vector

    azimuth = np.rad2deg(np.arctan2(azalt_vector[1], azalt_vector[0])) % 360
    altitude = np.rad2deg(np.arcsin(azalt_vector[2]))

    return azimuth, altitude

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/calculate/")
async def calculate_position(
    request: Request,
    latitude: float = Form(...),
    longitude: float = Form(...),
    declination: float = Form(...),
    ra: float = Form(...),
    year: int = Form(...),
    month: int = Form(...),
    day: int = Form(...),
    hour: int = Form(...),
    minute: int = Form(...),
    second: float = Form(...),
):
    mjd = calculate_mjd(year, month, day, hour, minute, second)
    greenwich_sidereal_time = calc_greenwich_sidereal_time(mjd)
    hour_angle = calc_local_hour_angle(greenwich_sidereal_time, longitude, ra)
    azimuth, altitude = calc_azimuth_altitude(latitude, declination, hour_angle)

    # 3Dプロットの作成
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # 球座標から直交座標への変換
    r = 1  # 任意の半径
    x = r * np.cos(np.deg2rad(altitude)) * np.cos(np.deg2rad(azimuth))
    y = r * np.cos(np.deg2rad(altitude)) * np.sin(np.deg2rad(azimuth))
    z = r * np.sin(np.deg2rad(altitude))

    # プロット
    ax.scatter(x, y, z, c='r', marker='o')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    # 球を描画
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    sphere_x = r * np.outer(np.cos(u), np.sin(v))
    sphere_y = r * np.outer(np.sin(u), np.sin(v))
    sphere_z = r * np.outer(np.ones(np.size(u)), np.cos(v))
    ax.plot_surface(sphere_x, sphere_y, sphere_z, color='b', alpha=0.1)

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    graph_url = f"data:image/png;base64,{graph_url}"

    return templates.TemplateResponse("result.html", {
        "request": request,
        "azimuth": azimuth,
        "altitude": altitude,
        "graph_url": graph_url
    })