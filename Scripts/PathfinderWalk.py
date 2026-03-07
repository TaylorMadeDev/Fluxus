"""
PathfinderWalk — A* pathfinder that walks the player to a target position.

Uses Minescript movement controls (`player_press_forward`, `player_press_jump`,
`player_look_at`) and block sampling (`getblock`) to find and follow a route.
"""

# @ui.title "Pathfinder Walk"
# @param int target_x 0 -- Destination X
# @param int target_y 64 -- Destination Y (feet level)
# @param int target_z 0 -- Destination Z
# @param bool use_current_y true -- Ignore target_y and path on your current Y
# @param int max_search_distance 64 -- Max horizontal search distance in blocks
# @param int max_nodes 12000 -- Safety cap for A* explored nodes
# @param bool sprint true -- Sprint while walking
# @param float arrival_radius 0.55 -- Distance to each waypoint before advancing
# @param float node_timeout_sec 4.0 -- Max seconds trying each waypoint
# @param int look_ahead_nodes 2 -- How many nodes ahead to aim camera while moving
# @param float eye_height 1.52 -- Eye-level camera target height above feet

import heapq
import math
import time

import minescript


def _param(name: str, default):
    return globals().get(name, default)


target_x = _param("target_x", 0)
target_y = _param("target_y", 64)
target_z = _param("target_z", 0)
use_current_y = _param("use_current_y", True)
max_search_distance = _param("max_search_distance", 64)
max_nodes = _param("max_nodes", 12000)
sprint = _param("sprint", True)
arrival_radius = _param("arrival_radius", 0.55)
node_timeout_sec = _param("node_timeout_sec", 4.0)
look_ahead_nodes = _param("look_ahead_nodes", 2)
eye_height = _param("eye_height", 1.52)


PASSABLE_BLOCKS = {
    "minecraft:air",
    "minecraft:cave_air",
    "minecraft:void_air",
    "minecraft:grass",
    "minecraft:tall_grass",
    "minecraft:fern",
    "minecraft:large_fern",
    "minecraft:dead_bush",
    "minecraft:vine",
    "minecraft:glow_lichen",
    "minecraft:torch",
    "minecraft:redstone_torch",
    "minecraft:soul_torch",
    "minecraft:wall_torch",
    "minecraft:redstone_wall_torch",
    "minecraft:soul_wall_torch",
    "minecraft:tripwire",
    "minecraft:string",
    "minecraft:rail",
    "minecraft:powered_rail",
    "minecraft:detector_rail",
    "minecraft:activator_rail",
    "minecraft:ladder",
    "minecraft:water",
}

LIQUID_BLOCKS = {
    "minecraft:water",
    "minecraft:lava",
}


def _clean_block_name(name: str) -> str:
    if not name:
        return ""
    return name.split("[", 1)[0].strip()


def _is_passable(name: str) -> bool:
    b = _clean_block_name(name)
    if b in PASSABLE_BLOCKS:
        return True
    if b.endswith("_air"):
        return True
    if "flower" in b or "sapling" in b or "carpet" in b:
        return True
    return False


def _is_liquid(name: str) -> bool:
    b = _clean_block_name(name)
    return b in LIQUID_BLOCKS


class WorldSampler:
    def __init__(self):
        self._cache = {}

    def block(self, x: int, y: int, z: int) -> str:
        key = (x, y, z)
        if key in self._cache:
            return self._cache[key]
        value = minescript.getblock(x, y, z)
        self._cache[key] = value
        return value

    def walkable(self, x: int, y: int, z: int) -> bool:
        feet = self.block(x, y, z)
        head = self.block(x, y + 1, z)
        floor = self.block(x, y - 1, z)
        if not _is_passable(feet):
            return False
        if not _is_passable(head):
            return False
        if _is_passable(floor):
            return False
        if _is_liquid(floor):
            return False
        return True


def _heuristic(a, b) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _neighbors(node, sampler: WorldSampler):
    x, y, z = node
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, nz = x + dx, z + dz
        for ny in (y, y + 1, y - 1):
            if abs(ny - y) > 1:
                continue
            if sampler.walkable(nx, ny, nz):
                yield (nx, ny, nz)
                break


def astar_path(start, goal, sampler: WorldSampler, max_nodes: int, max_search_distance: int):
    sx, _, sz = start
    gx, _, gz = goal

    min_x = min(sx, gx) - max_search_distance
    max_x = max(sx, gx) + max_search_distance
    min_z = min(sz, gz) - max_search_distance
    max_z = max(sz, gz) + max_search_distance

    def in_bounds(node):
        x, _, z = node
        return min_x <= x <= max_x and min_z <= z <= max_z

    open_heap = []
    heapq.heappush(open_heap, (_heuristic(start, goal), 0, start))
    came_from = {}
    g_score = {start: 0}
    explored = 0

    while open_heap:
        _, _, current = heapq.heappop(open_heap)

        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        explored += 1
        if explored > max_nodes:
            break

        for nxt in _neighbors(current, sampler):
            if not in_bounds(nxt):
                continue
            step_cost = 1.25 if nxt[1] != current[1] else 1.0
            tentative = g_score[current] + step_cost
            if tentative < g_score.get(nxt, float("inf")):
                came_from[nxt] = current
                g_score[nxt] = tentative
                f = tentative + _heuristic(nxt, goal)
                heapq.heappush(open_heap, (f, explored, nxt))

    return None


def _distance_xz(px: float, pz: float, tx: float, tz: float) -> float:
    return math.hypot(tx - px, tz - pz)


def _stop_movement():
    minescript.player_press_forward(False)
    minescript.player_press_left(False)
    minescript.player_press_right(False)
    minescript.player_press_jump(False)
    minescript.player_press_sprint(False)


def _normalize_angle(a: float) -> float:
    while a <= -math.pi:
        a += 2.0 * math.pi
    while a > math.pi:
        a -= 2.0 * math.pi
    return a


def walk_path(path, *, sprinting: bool, arrival: float, node_timeout: float, look_ahead: int, eye_y: float):
    minescript.echo(f"[Pathfinder] Following {len(path)} nodes...")

    try:
        current_index = 1
        current_deadline = time.time() + max(0.5, node_timeout)
        best_dist = float("inf")
        stalled_ticks = 0
        previous_heading = None
        smoothed_aim_x = None
        smoothed_aim_z = None

        minescript.player_press_forward(True)

        while current_index < len(path):
            tx, ty, tz = path[current_index]
            waypoint_x = tx + 0.5
            waypoint_z = tz + 0.5

            px, py, pz = minescript.player_position()
            dist = _distance_xz(px, pz, waypoint_x, waypoint_z)

            if dist <= arrival:
                current_index += 1
                current_deadline = time.time() + max(0.5, node_timeout)
                best_dist = float("inf")
                stalled_ticks = 0
                continue

            if time.time() > current_deadline:
                minescript.echo(
                    f"[Pathfinder] Timed out on node {current_index}/{len(path)-1}; skipping..."
                )
                current_index += 1
                current_deadline = time.time() + max(0.5, node_timeout)
                best_dist = float("inf")
                stalled_ticks = 0
                continue

            # Find look-ahead target, ensuring it's sufficiently far ahead
            aim_index = current_index
            for i in range(current_index, min(len(path), current_index + max(1, int(look_ahead)) + 1)):
                test_x, test_y, test_z = path[i]
                test_dist = _distance_xz(px, pz, test_x + 0.5, test_z + 0.5)
                # Use this node if it's at least 1.2 blocks away or it's the last we can check
                if test_dist >= 1.2 or i == min(len(path) - 1, current_index + max(1, int(look_ahead))):
                    aim_index = i
                    break

            ax, ay, az = path[aim_index]
            raw_aim_x = ax + 0.5
            raw_aim_z = az + 0.5

            # Smooth camera target to prevent snapping
            if smoothed_aim_x is None:
                smoothed_aim_x = raw_aim_x
                smoothed_aim_z = raw_aim_z
            else:
                # Exponential smoothing
                alpha = 0.35  # Lower = smoother but slower response
                smoothed_aim_x += (raw_aim_x - smoothed_aim_x) * alpha
                smoothed_aim_z += (raw_aim_z - smoothed_aim_z) * alpha

            heading = math.atan2(smoothed_aim_z - pz, smoothed_aim_x - px)
            turn_delta = 0.0 if previous_heading is None else abs(_normalize_angle(heading - previous_heading))
            previous_heading = heading

            bob = math.sin(time.time() * 5.5) * 0.04
            look_y = py + max(1.2, float(eye_y)) + bob
            minescript.player_look_at(smoothed_aim_x, look_y, smoothed_aim_z)

            slow_for_turn = turn_delta > 1.05 and dist < 2.2
            minescript.player_press_sprint(bool(sprinting) and not slow_for_turn)

            current_block_y = int(math.floor(py))
            needs_upstep = ty > current_block_y
            minescript.player_press_jump(needs_upstep)

            if dist + 0.015 < best_dist:
                best_dist = dist
                stalled_ticks = 0
            else:
                stalled_ticks += 1

            if stalled_ticks > 16:
                minescript.player_press_jump(True)
                time.sleep(0.09)
                minescript.player_press_jump(False)
                stalled_ticks = 0

            time.sleep(0.05)

        minescript.echo("[Pathfinder] Arrived at destination.")
    finally:
        _stop_movement()


def main():
    px, py, pz = minescript.player_position()
    start = (int(math.floor(px)), int(math.floor(py)), int(math.floor(pz)))

    goal_y = start[1] if use_current_y else int(target_y)
    goal = (int(target_x), int(goal_y), int(target_z))

    minescript.echo(
        f"[Pathfinder] Start: {start[0]}, {start[1]}, {start[2]} | "
        f"Goal: {goal[0]}, {goal[1]}, {goal[2]}"
    )

    sampler = WorldSampler()

    if not sampler.walkable(*start):
        minescript.echo("[Pathfinder] Warning: current player block is not ideal for walking pathing.")

    if not sampler.walkable(*goal):
        minescript.echo("[Pathfinder] Goal not directly walkable. Trying nearest nearby standable block...")
        found = None
        for r in range(1, 4):
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    candidate = (goal[0] + dx, goal[1], goal[2] + dz)
                    if sampler.walkable(*candidate):
                        found = candidate
                        break
                if found:
                    break
            if found:
                break
        if found is None:
            minescript.echo("[Pathfinder] Could not find a standable destination near target.")
            return
        goal = found
        minescript.echo(f"[Pathfinder] Using nearby walkable goal: {goal[0]}, {goal[1]}, {goal[2]}")

    path = astar_path(
        start,
        goal,
        sampler,
        max_nodes=max(1000, int(max_nodes)),
        max_search_distance=max(16, int(max_search_distance)),
    )

    if not path:
        minescript.echo("[Pathfinder] No path found within limits.")
        return

    minescript.echo(f"[Pathfinder] Path found with {len(path)} nodes.")
    walk_path(
        path,
        sprinting=bool(sprint),
        arrival=max(0.2, float(arrival_radius)),
        node_timeout=max(0.5, float(node_timeout_sec)),
        look_ahead=max(0, int(look_ahead_nodes)),
        eye_y=max(1.2, float(eye_height)),
    )


if __name__ == "__main__":
    main()
