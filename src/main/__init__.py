# -*- coding: utf-8 -*-
"""AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块（学生骨架）。
你的全部作业都在本文件里：按题面（题面.pdf）各题的规范补全每个标有 TODO 的函数。
- 骨架已提供：Facing / SentryState 枚举、SentryGrid 的构造与只读属性、
  渲染函数 render_frame（demo 用，不进测试）。
- 你要实现：Q1-Q6 与 Bonus 的全部 TODO，以及 SentryGrid 的
  四个方法（current_pos 的 setter、move_forward、turn_left、turn_right）。
- 未实现的函数 raise NotImplementedError：可见测试会自动 skip，
  CI 一开始就是绿的；实现一个，对应测试亮一个。
- `python main.py`（或 PYTHONPATH=src python -m main）可看 ASCII 演示。
"""
import json
from enum import Enum


# ---------------------------------------------------------------------------
# 仿真世界基础（已提供，勿改）
# ---------------------------------------------------------------------------
class Facing(Enum):
    """朝向枚举。世界坐标 (x, y)：x 向右增长，y 向上增长（数学系）。"""

    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self):
        """该朝向的单位位移向量 (dx, dy)。"""
        return self.value[0], self.value[1]


# ---------------------------------------------------------------------------
# Q1 机器人自检（题面 Q1·自检状态计算与报告生成）
# ---------------------------------------------------------------------------
def hp_ratio(hp, max_hp):
    """TODO(Q1)：血量百分比，返回 0-100 的 int；计算与边界规则见题面 Q1 规范。"""
    if max_hp <= 0:
        return 0
    ratio = (hp / max_hp) * 100
    return int(max(0, min(100, ratio)))


def status_report(name, robot_type, hp, max_hp, battery):
    """TODO(Q1)：一行自检报告字符串；档位判定与逐字符格式见题面 Q1 规范。"""
    hp_percentage = hp_ratio(hp, max_hp)
    if battery >= 40:
        battery_status = "OK"
    elif battery >= 20:
        battery_status = "WARNING"
    else:
        battery_status = "LOW"
    return (f"{name:<10}|{robot_type:^10}|HP {hp_percentage:>3}%"f"|BAT {battery:>3}%|{battery_status}")


print(status_report("Sentry-07", "HERO", 65, 100, 75))


# ---------------------------------------------------------------------------
# Q2 战斗日志分析（题面 Q2·多源日志解析与统计）
# ---------------------------------------------------------------------------
"""TODO(Q2)：解析混合格式伤害日志，返回固定契约的统计 dict；
    行格式、去重与统计口径见题面 Q2 规范。"""


def analyze_damage_log(lines):
    total = 0
    by_armor = {"front": 0, "left": 0, "right": 0}
    seen_ids = set()
    count = 0
    for raw_line in lines:
        line = str(raw_line).strip()
        if not line or line.startswith("#"):
            continue  # 如果是空行或注释，跳过此次循环
        if line.startswith("{"):  # 在字符串里，以{开头的只能是json行了，所以下面要解析json行
            try:
                data = json.loads(line)
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            armor, damage = data.get("armor"), data.get("damage")
            if (armor not in by_armor or isinstance(damage, bool)
                    or not isinstance(damage, int) or damage < 0):
                continue
            if "id" in data:
                try:
                    duplicate = data["id"] in seen_ids
                except TypeError:
                    duplicate = False
                if duplicate:
                    continue
                try:
                    seen_ids.add(data["id"])
                except TypeError:
                    pass
            by_armor[armor] += damage
            total += damage
            count += 1
            continue  # json行解析完毕
        mapping = {"F": "front", "L": "left", "R": "right"}
        parsed = []
        for part in line.split(","):
            fields = part.strip().split(":")
            if (len(fields) != 2 or fields[0] not in mapping
                    or not fields[1].isdigit() or int(fields[1]) <= 0):
                parsed = []
                break
            parsed.append((mapping[fields[0]], int(fields[1])))
        for armor, damage in parsed:
            by_armor[armor] += damage
            total += damage
            count += 1
    return {"total": total, "by_armor": by_armor,
            "most_hit": max(by_armor, key=by_armor.get) if count else None,
            "avg": round(total / count, 2) if count else 0.0}


'''
    
        
# ---------------------------------------------------------------------------
# Q3 SentryGrid（题面 Q3·载体物理规则）
# ---------------------------------------------------------------------------
'''


class SentryGrid:
    """哨兵仿真载体（构造与只读属性已提供；四个 TODO 方法由你实现）。"""

    def __init__(self, width, height, obstacles, enemy_pos,
                 start_pos=(0, 0), facing=Facing.UP, fuel=100):
        self._width = int(width)
        self._height = int(height)
        if self._width <= 0 or self._height <= 0:
            raise ValueError("地图尺寸必须为正")
        # 障碍坐标存入 set，查询 O(1)——已有实现，勿改。
        self._obstacles = set()
        for ob in obstacles:
            x, y = ob
            self._obstacles.add((int(x), int(y)))
        if not isinstance(enemy_pos, (tuple, list)) or len(enemy_pos) != 2:
            raise TypeError("enemy_pos 需要长度为 2 的 tuple/list")
        self._enemy_pos = self._clamp_cell(enemy_pos)
        if self._enemy_pos in self._obstacles:
            raise ValueError("enemy_pos 不能位于障碍物上")
        if not isinstance(facing, Facing):
            facing = Facing.UP
        self._facing = facing
        self._fuel = int(fuel)
        self._collision_count = 0
        self._pos = self._clamp_cell(start_pos)
        if self._pos in self._obstacles:
            raise ValueError("start_pos 不能位于障碍物上")

    def _clamp_cell(self, cell):
        """已提供：元素转 int 并夹回地图范围（供 __init__ 使用）。"""
        x = int(cell[0])
        y = int(cell[1])
        x = max(0, min(self._width - 1, x))
        y = max(0, min(self._height - 1, y))
        return (x, y)

    # -- 只读属性（已提供，勿改） ------------------------------------------
    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def enemy_pos(self):
        return self._enemy_pos

    @property
    def facing(self):
        return self._facing

    @property
    def fuel(self):
        return self._fuel

    @property
    def collision_count(self):
        return self._collision_count

    @property
    def obstacles(self):
        """障碍集合的只读视图（内部 set 引用，不要修改它）。"""
        return self._obstacles

    @property
    def found_enemy(self):
        return self._pos == self._enemy_pos

    def is_blocked(self, x, y):
        """已提供：坐标是否为障碍或越界（O(1)）。"""
        return ((x, y) in self._obstacles
                or not (0 <= x < self._width and 0 <= y < self._height))

    # -- 你要实现的部分 ------------------------------------------------------
    @property
    def current_pos(self):
        """当前位置 (x, y) 的 tuple。"""
        return self._pos

    @current_pos.setter
    def current_pos(self, value):
        """TODO(Q3)：位置 setter；三重输入校验见题面 Q3 规范第 1 条。"""
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise TypeError
        new_pos = self._clamp_cell(value)
        if new_pos in self._obstacles:
            raise ValueError("current_pos 不能位于障碍物上")
        self._pos = new_pos

    def move_forward(self):
        """TODO(Q3)：朝当前 facing 前进一格，返回执行后的位置；
        碰撞、耗电与断电语义见题面 Q3 规范。"""
        move_forward = (self._pos[0] + self._facing.delta[0],
                        self._pos[1] + self._facing.delta[1])
        if self._fuel <= 0:
            return self._pos
        if self.is_blocked(move_forward[0], move_forward[1]):
            self._collision_count += 1
            self._fuel -= 1
            return self._pos
        if not self.is_blocked(move_forward[0], move_forward[1]):
            self._pos = move_forward
            self._fuel -= 1
            if self._fuel <= 0:
                move_forward = self._pos
            return self._pos

    def turn_left(self):
        """TODO(Q3)：原地左转 90°，返回新的 Facing（不耗电）。"""
        turn_left_mapping = {
            Facing.UP: Facing.LEFT,
            Facing.LEFT: Facing.DOWN,
            Facing.DOWN: Facing.RIGHT,
            Facing.RIGHT: Facing.UP
        }
        self._facing = turn_left_mapping[self._facing]
        return self._facing

    def turn_right(self):
        """TODO(Q3)：原地右转 90°，返回新的 Facing（不耗电）。"""
        turn_right_mapping = {
            Facing.UP: Facing.RIGHT,
            Facing.RIGHT: Facing.DOWN,
            Facing.DOWN: Facing.LEFT,
            Facing.LEFT: Facing.UP
        }
        self._facing = turn_right_mapping[self._facing]
        return self._facing


# ---------------------------------------------------------------------------
# Q4 贪心导航（题面 Q4·单步贪心导航策略）
# ---------------------------------------------------------------------------
def _q4_placeholder(pos, target, obstacles, current_facing=Facing.UP):
    """TODO(Q4)：返回下一步应朝向的 Facing；
    候选判定、优先级与回退规则见题面 Q4 规范。"""
    # distance = abs(x1 - x2) + abs(y1 - y2)曼哈顿距离公式
    def next_step_toward(pos, target, obstacles, current_facing=Facing.UP):
        x, y = pos
        tx, ty = target
        dx, dy = tx - x, ty - y
        directions = []
        if abs(dx) >= abs(dy):
            if dx:
                directions.append(Facing.RIGHT if dx > 0 else Facing.LEFT)
            if dy:
                directions.append(Facing.UP if dy > 0 else Facing.DOWN)
        else:
            if dy:
                directions.append(Facing.UP if dy > 0 else Facing.DOWN)
            if dx:
                directions.append(Facing.RIGHT if dx > 0 else Facing.LEFT)
        blocked = set(obstacles)
        for direction in directions:
            cell = (x + direction.delta[0], y + direction.delta[1])
            if cell not in blocked:
                return direction
        return current_facing


def next_step_toward(pos, target, obstacles, current_facing=Facing.UP):
    """Return the preferred Manhattan step toward target, avoiding obstacles."""
    x, y = pos
    tx, ty = target
    dx, dy = tx - x, ty - y
    if dx == 0 and dy == 0:
        return current_facing
    directions = []
    if abs(dx) >= abs(dy):
        if dx:
            directions.append(Facing.RIGHT if dx > 0 else Facing.LEFT)
        if dy:
            directions.append(Facing.UP if dy > 0 else Facing.DOWN)
    else:
        if dy:
            directions.append(Facing.UP if dy > 0 else Facing.DOWN)
        if dx:
            directions.append(Facing.RIGHT if dx > 0 else Facing.LEFT)
    blocked = set(obstacles)
    for direction in directions:
        cell = (x + direction.delta[0], y + direction.delta[1])
        if cell not in blocked:
            return direction
    return current_facing


# ---------------------------------------------------------------------------
# Q5 哨兵决策机（题面 Q5·裁判系统决策规则表）
# ---------------------------------------------------------------------------
class SentryState(Enum):
    """哨兵状态机（已提供，勿改）。"""

    PATROL = "PATROL"
    SUSPECT = "SUSPECT"
    ENGAGE = "ENGAGE"
    RETREAT = "RETREAT"
    RETURN = "RETURN"


def decide(sensor, state, hp, heat):
    """TODO(Q5)：纯函数决策，返回 (action: str, new_state: SentryState)；
    sensor 字段契约、R1-R7 规则表与非法输入处理见题面 Q5 规范。"""
    # Validate the decision contract up front.  Keeping this function pure makes
    # malformed sensor packets fail deterministically instead of being treated
    # as a false negative.
    if not isinstance(sensor, dict):
        raise ValueError("sensor must be a dict")
    if not isinstance(state, SentryState):
        raise ValueError("state must be a SentryState")
    frames = sensor.get("enemy_frames")
    if not isinstance(frames, (tuple, list)) or not frames:
        raise ValueError("enemy_frames must be a non-empty sequence")
    if any(type(flag) is not bool for flag in frames):
        raise ValueError("enemy_frames must contain booleans")
    distance = sensor.get("enemy_dist")
    if distance is not None or any(flag for flag in frames):
        if distance is not None and (isinstance(distance, bool)
                                     or not isinstance(distance, (int, float))
                                     or distance < 0):
            raise ValueError(
                "enemy_dist must be a non-negative number or None")
    if not isinstance(sensor.get("robot_type"), str) or not sensor["robot_type"]:
        raise ValueError("robot_type must be a non-empty string")
    max_hp = sensor.get("max_hp")
    if isinstance(max_hp, bool) or not isinstance(max_hp, (int, float)) or max_hp <= 0:
        raise ValueError("max_hp must be positive")
    if isinstance(hp, bool) or not isinstance(hp, (int, float)):
        raise ValueError("hp must be numeric")
    if isinstance(heat, bool) or not isinstance(heat, (int, float)):
        raise ValueError("heat must be numeric")

    visible = bool(frames[-1])
    confirmed = len(frames) >= 2 and frames[-1] and frames[-2]
    low_hp = hp / max_hp <= 0.30

    if state is SentryState.PATROL:
        return (("SCAN", SentryState.SUSPECT) if visible
                else ("PATROL_MOVE", SentryState.PATROL))
    if state is SentryState.SUSPECT:
        if confirmed and visible:
            return ("SHOOT", SentryState.ENGAGE)
        return (("SCAN", SentryState.SUSPECT) if visible
                else ("PATROL_MOVE", SentryState.PATROL))
    if state is SentryState.ENGAGE:
        if low_hp:
            return ("RETREAT", SentryState.RETREAT)
        if heat >= 80:
            return ("COOL", SentryState.ENGAGE)
        if visible:
            return ("SHOOT", SentryState.ENGAGE)
        return ("SCAN", SentryState.SUSPECT)
    if state is SentryState.RETREAT:
        return (("RETURN", SentryState.RETURN) if not visible and not low_hp
                else ("RETREAT", SentryState.RETREAT))
    # RETURN: one movement command completes the transition to patrol.
    return ("MOVE_BASE", SentryState.PATROL)


# ---------------------------------------------------------------------------
# Q6 巡逻任务（题面 Q6·巡逻契约与验收阈值）
# ---------------------------------------------------------------------------
def run_patrol(grid, max_steps=500):
    """TODO(Q6)：sense → decide → act 主循环；
    循环结构、终止条件、脱困自由度与统计返回契约见题面 Q6 规范。"""
    steps = 0
    while steps < max_steps and grid.fuel > 0 and not grid.found_enemy:
        path_len = bfs_path_length(grid.current_pos, grid.enemy_pos,
                                   grid.obstacles | _grid_border(grid))
        if path_len < 0:
            break
        pos = grid.current_pos
        candidates = []
        for facing in Facing:
            nxt = (pos[0] + facing.delta[0], pos[1] + facing.delta[1])
            if grid.is_blocked(*nxt):
                continue
            remaining = bfs_path_length(nxt, grid.enemy_pos,
                                        grid.obstacles | _grid_border(grid))
            if remaining >= 0:
                candidates.append((remaining, facing.value, facing))
        if not candidates:
            break
        facing = min(candidates, key=lambda item: (item[0], item[1]))[2]
        rights = {Facing.UP: 0, Facing.RIGHT: 1,
                  Facing.DOWN: 2, Facing.LEFT: 3}
        diff = (rights[facing] - rights[grid.facing]) % 4
        if diff == 3:
            grid.turn_left()
        else:
            for _ in range(diff):
                grid.turn_right()
        grid.move_forward()
        steps += 1
    return {"success": grid.found_enemy, "steps": steps,
            "collisions": grid.collision_count}


def report_to_json(stats):
    """TODO(Q6)：把 stats 序列化为确定性的 JSON 字符串，见题面 Q6 规范。"""
    return json.dumps(stats, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


# ---------------------------------------------------------------------------
# Bonus：BFS 全局最短路（题面 Bonus·BFS 语义与排行榜）
# ---------------------------------------------------------------------------
def bfs_path_length(start, target, obstacles):
    """TODO(Bonus)：BFS 全局最短路步数；返回语义与边界职责见题面 Bonus 规范。"""
    from collections import deque
    if start == target:
        return 0
    blocked = set(obstacles or ())
    if start in blocked or target in blocked:
        return -1
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        (x, y), distance = queue.popleft()
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nxt in blocked or nxt in seen:
                continue
            if nxt == target:
                return distance + 1
            seen.add(nxt)
            queue.append((nxt, distance + 1))
    return -1


def _grid_border(grid):
    return ({(x, -1) for x in range(-1, grid.width + 1)} |
            {(x, grid.height) for x in range(-1, grid.width + 1)} |
            {(-1, y) for y in range(-1, grid.height + 1)} |
            {(grid.width, y) for y in range(-1, grid.height + 1)})


# ---------------------------------------------------------------------------
# 渲染（已提供，demo 专用，不进测试）
# ---------------------------------------------------------------------------
def render_frame(grid, trail=()):
    """ASCII 渲染一帧战场；trail 为走过的格子集合。返回 list[str]。"""
    trail = set(trail)
    rows = []
    for y in range(grid.height - 1, -1, -1):
        row = []
        for x in range(grid.width):
            if (x, y) == grid.current_pos:
                row.append("◉")
            elif (x, y) == grid.enemy_pos:
                row.append("▲")
            elif (x, y) in grid.obstacles:
                row.append("█")
            elif (x, y) in trail:
                row.append("·")
            else:
                row.append(".")
        rows.append("".join(row))
    return rows
