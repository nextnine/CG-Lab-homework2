import taichi as ti
import math
import inspect

ti.init(arch=ti.gpu)

# =========================
# 配置
# =========================
WINDOW_RES = (900, 700)
BG_COLOR = (0.07, 0.19, 0.26)

EDGE_RADIUS_PX = 2.5
VIEWPORT_SIZE_PX = 700.0

COLOR_X = (1.0, 0.30, 0.30)   # 红
COLOR_Y = (0.32, 0.77, 0.10)  # 绿
COLOR_Z = (0.09, 0.47, 1.00)  # 蓝


# =========================
# 数据
# =========================
vertices = ti.Vector.field(3, dtype=ti.f32, shape=8)
screen_coords = ti.Vector.field(2, dtype=ti.f32, shape=8)
edges = ti.Vector.field(2, dtype=ti.i32, shape=12)

# 每条边离散成多个点来模拟 line
SAMPLES_PER_EDGE = 64
line_points = ti.Vector.field(2, dtype=ti.f32, shape=12 * SAMPLES_PER_EDGE)

# 颜色分 3 组分别画
line_points_x = ti.Vector.field(2, dtype=ti.f32, shape=4 * SAMPLES_PER_EDGE)
line_points_y = ti.Vector.field(2, dtype=ti.f32, shape=4 * SAMPLES_PER_EDGE)
line_points_z = ti.Vector.field(2, dtype=ti.f32, shape=4 * SAMPLES_PER_EDGE)


# =========================
# 变换矩阵
# =========================
@ti.func
def get_model_matrix(angle_x: ti.f32, angle_y: ti.f32):
    rad_x = angle_x * math.pi / 180.0
    rad_y = angle_y * math.pi / 180.0

    cx = ti.cos(rad_x)
    sx = ti.sin(rad_x)
    cy = ti.cos(rad_y)
    sy = ti.sin(rad_y)

    rot_x = ti.Matrix([
        [1.0, 0.0, 0.0, 0.0],
        [0.0,  cx, -sx, 0.0],
        [0.0,  sx,  cx, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])

    rot_y = ti.Matrix([
        [ cy, 0.0,  sy, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [-sy, 0.0,  cy, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])

    return rot_y @ rot_x


@ti.func
def get_view_matrix(eye_pos):
    return ti.Matrix([
        [1.0, 0.0, 0.0, -eye_pos[0]],
        [0.0, 1.0, 0.0, -eye_pos[1]],
        [0.0, 0.0, 1.0, -eye_pos[2]],
        [0.0, 0.0, 0.0, 1.0]
    ])


@ti.func
def get_projection_matrix(eye_fov: ti.f32, aspect_ratio: ti.f32, z_near: ti.f32, z_far: ti.f32):
    n = -z_near
    f = -z_far

    fov_rad = eye_fov * math.pi / 180.0
    t = ti.tan(fov_rad / 2.0) * ti.abs(n)
    b = -t
    r = aspect_ratio * t
    l = -r

    M_p2o = ti.Matrix([
        [n,   0.0, 0.0,   0.0],
        [0.0, n,   0.0,   0.0],
        [0.0, 0.0, n + f, -n * f],
        [0.0, 0.0, 1.0,   0.0]
    ])

    M_ortho_trans = ti.Matrix([
        [1.0, 0.0, 0.0, -(r + l) / 2.0],
        [0.0, 1.0, 0.0, -(t + b) / 2.0],
        [0.0, 0.0, 1.0, -(n + f) / 2.0],
        [0.0, 0.0, 0.0, 1.0]
    ])

    M_ortho_scale = ti.Matrix([
        [2.0 / (r - l), 0.0, 0.0, 0.0],
        [0.0, 2.0 / (t - b), 0.0, 0.0],
        [0.0, 0.0, 2.0 / (n - f), 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])

    return M_ortho_scale @ M_ortho_trans @ M_p2o


# =========================
# 核函数
# =========================
@ti.kernel
def compute_transform(angle_x: ti.f32, angle_y: ti.f32,
                      width: ti.f32, height: ti.f32,
                      viewport_size: ti.f32):
    eye_pos = ti.Vector([0.0, 0.0, 5.5])

    model = get_model_matrix(angle_x, angle_y)
    view = get_view_matrix(eye_pos)
    proj = get_projection_matrix(45.0, 1.0, 0.1, 50.0)  # 固定比例，不随窗口缩放

    mvp = proj @ view @ model

    center_x = width * 0.5
    center_y = height * 0.5
    half_view = viewport_size * 0.5

    for i in range(8):
        v = vertices[i]
        v4 = ti.Vector([v[0], v[1], v[2], 1.0])

        v_clip = mvp @ v4
        v_ndc = v_clip / v_clip[3]

        pixel_x = center_x + v_ndc[0] * half_view
        pixel_y = center_y + v_ndc[1] * half_view

        screen_coords[i] = ti.Vector([pixel_x / width, pixel_y / height])


@ti.kernel
def build_line_points():
    for e in range(12):
        a_idx = edges[e][0]
        b_idx = edges[e][1]

        a = screen_coords[a_idx]
        b = screen_coords[b_idx]

        for j in range(SAMPLES_PER_EDGE):
            t = 0.0
            if SAMPLES_PER_EDGE > 1:
                t = j / (SAMPLES_PER_EDGE - 1)

            p = a * (1.0 - t) + b * t

            global_idx = e * SAMPLES_PER_EDGE + j
            line_points[global_idx] = p

            # 按边方向分组：0-3 X, 4-7 Y, 8-11 Z
            if e < 4:
                line_points_x[e * SAMPLES_PER_EDGE + j] = p
            elif e < 8:
                line_points_y[(e - 4) * SAMPLES_PER_EDGE + j] = p
            else:
                line_points_z[(e - 8) * SAMPLES_PER_EDGE + j] = p


# =========================
# 初始化
# =========================
def init_cube():
    cube_vertices = [
        [-1.0, -1.0, -1.0],
        [ 1.0, -1.0, -1.0],
        [ 1.0,  1.0, -1.0],
        [-1.0,  1.0, -1.0],
        [-1.0, -1.0,  1.0],
        [ 1.0, -1.0,  1.0],
        [ 1.0,  1.0,  1.0],
        [-1.0,  1.0,  1.0],
    ]

    cube_edges = [
        [0, 1], [3, 2], [4, 5], [7, 6],  # X
        [0, 3], [1, 2], [4, 7], [5, 6],  # Y
        [0, 4], [1, 5], [2, 6], [3, 7],  # Z
    ]

    for i in range(8):
        vertices[i] = cube_vertices[i]

    for i in range(12):
        edges[i] = cube_edges[i]


def create_window():
    kwargs = {"res": WINDOW_RES}
    try:
        params = inspect.signature(ti.ui.Window).parameters
        if "resizable" in params:
            kwargs["resizable"] = True
    except (TypeError, ValueError):
        pass
    return ti.ui.Window("Resizable Centered Cube", **kwargs)


def pixel_radius_to_canvas_radius(pixel_radius, width, height):
    base = min(width, height) if width > 0 and height > 0 else min(WINDOW_RES)
    return pixel_radius / base


# =========================
# 主程序
# =========================
def main():
    init_cube()

    window = create_window()
    canvas = window.get_canvas()

    angle_x = 0
    angle_y = -35.0
    step = 5.0

    while window.running:
        if hasattr(window, "get_window_shape"):
            width, height = window.get_window_shape()
        else:
            width, height = WINDOW_RES

        while window.get_event(ti.ui.PRESS):
            if window.event.key == 'a' or window.event.key == ti.ui.LEFT:
                angle_y += step
            elif window.event.key == 'd' or window.event.key == ti.ui.RIGHT:
                angle_y -= step
            elif window.event.key == 'w' or window.event.key == ti.ui.UP:
                angle_x -= step
            elif window.event.key == 's' or window.event.key == ti.ui.DOWN:
                angle_x += step
            elif window.event.key == ti.ui.ESCAPE:
                window.running = False

        compute_transform(angle_x, angle_y, float(width), float(height), VIEWPORT_SIZE_PX)
        build_line_points()

        radius = pixel_radius_to_canvas_radius(EDGE_RADIUS_PX, width, height)

        canvas.set_background_color(BG_COLOR)
        canvas.circles(line_points_x, color=COLOR_X, radius=radius)
        canvas.circles(line_points_y, color=COLOR_Y, radius=radius)
        canvas.circles(line_points_z, color=COLOR_Z, radius=radius)

        window.show()


if __name__ == "__main__":
    main()
