# CG-Lab Homework 2

这是一个基于 **Taichi** 的计算机图形学练习项目：
程序会在窗口中渲染一个可交互旋转的立方体线框，并使用不同颜色区分 X/Y/Z 三组边。

## 项目结构

- `work2/main.py`：主程序，包含立方体数据、MVP 变换、线段离散绘制与交互控制。
- `work2/pyproject.toml`：项目依赖与基础元数据（Python 3.12+，依赖 Taichi）。

## 功能说明

- 使用 `model -> view -> projection` 变换流程将 3D 顶点投影到 2D 屏幕。
- 使用 8 个顶点和 12 条边定义立方体线框。
- 每条边离散采样为多个点，通过 `canvas.circles` 模拟线段绘制。
- 三个坐标方向边采用不同颜色：
  - X 方向：红色
  - Y 方向：绿色
  - Z 方向：蓝色
- 使用固定视口尺寸，窗口缩放时仍保持绘制主体稳定居中。

## 交互方式

运行后可使用键盘控制旋转：

- `A` / `←`：绕 Y 轴向左旋转
- `D` / `→`：绕 Y 轴向右旋转
- `W` / `↑`：绕 X 轴向上旋转
- `S` / `↓`：绕 X 轴向下旋转
- `ESC`：退出程序

## 环境准备（推荐使用 uv）

> 以下步骤在仓库根目录执行。

### 1) 安装 uv（如尚未安装）

可参考官方安装方式（任选其一）：

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

安装完成后确认：

```bash
uv --version
```

### 2) 进入项目目录并创建虚拟环境

```bash
cd work2
uv venv
```

创建后激活环境：

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3) 使用 `uv add taichi` 安装依赖

在 `work2` 目录下执行：

```bash
uv add taichi
```

这条命令会自动完成以下事情：

- 将 `taichi` 写入 `pyproject.toml` 的 dependencies。
- 解析并安装依赖到当前虚拟环境。
- 更新（或生成）`uv.lock`，便于后续复现环境。

如果你希望固定大版本，也可以这样写：

```bash
uv add "taichi>=1.7.4"
```

### 4) 同步 / 复现环境

当仓库已经包含 `pyproject.toml + uv.lock` 时，其他人只需要：

```bash
cd work2
uv sync
```

`uv sync` 会按锁文件安装精确版本，保证大家环境一致。

## 运行程序

在 `work2` 目录下：

```bash
python main.py
```

如果你不想手动激活虚拟环境，也可以直接：

```bash
uv run python main.py
```

## 实现要点（简述）

1. 在 `init_cube()` 中初始化立方体顶点与边。
2. 在 `compute_transform()` 中计算 MVP 矩阵并完成齐次裁剪坐标到屏幕坐标映射。
3. 在 `build_line_points()` 中将每条边离散为点列。
4. 在主循环中处理输入事件、更新角度并绘制三组彩色边。


## 相对基础三角形版本的改进


1. **渲染对象升级**：从 3 顶点三角形升级为 8 顶点 + 12 边的立方体线框。
2. **旋转维度升级**：从单轴旋转升级为绕 X、Y 双轴旋转。
3. **视口映射优化**：使用窗口中心 + 固定视口像素尺寸，窗口缩放时主体保持稳定居中。
4. **线段绘制策略升级**：将每条边离散成多个采样点，再用 `canvas.circles` 模拟连续线段绘制。
5. **交互升级**：支持 `W/S/A/D` 与方向键控制，旋转更直观。
6. **窗口与兼容性升级**：使用 `ti.ui.Window` + `canvas`，并兼容检测 `resizable` 参数。

## 完整画面如下
![7QcvLO9u_converted](https://github.com/user-attachments/assets/f2f4a998-d794-410c-a023-30a8702ced1f)


## 可扩展方向

- 增加透视参数调节（FOV、近平面、远平面）
- 增加自动旋转动画
- 改用三角形面片绘制实体立方体并加入简单光照
