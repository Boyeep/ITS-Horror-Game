"""Interior dressing is cosmetic: plans only read the grid and stay on plain floor and plain walls."""
import copy
import unittest

from horror.campus import FLOOR_COUNTS
from horror.config import TILE
from horror.decor import floor_wear, is_open, stair_zone, wall_fixtures
from horror.floors import BuildingLayout


def building_floors():
    for building, count in sorted(FLOOR_COUNTS.items()):
        for floor in range(1, count):
            layout = BuildingLayout(building, floor)
            if not layout.rooftop:  # the renderer leaves rooftops alone
                yield layout


def skipped(layout):
    zone = stair_zone(getattr(layout, "stairs", ()), TILE)
    return set(getattr(layout, "void_cells", ())) | set(getattr(layout, "outdoor_cells", ())) | set(layout.glass) | zone


def furniture_cells(layout):
    return {(x, y) for item in layout.furniture for y in range(item.y, item.y + item.height) for x in range(item.x, item.x + item.width)}


class DecorPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = list(building_floors())

    def test_plans_never_change_the_layout(self):
        for layout in self.layouts:
            before = copy.deepcopy(layout.grid)
            wall_fixtures(layout.grid, layout.doors, skipped(layout))
            floor_wear(layout.grid, layout.doors, skipped(layout))
            self.assertEqual(layout.grid, before, (layout.building, layout.floor))

    def test_fixtures_hang_on_walls_that_face_open_floor(self):
        for layout in self.layouts:
            for kind, x, y in wall_fixtures(layout.grid, layout.doors, skipped(layout)):
                self.assertEqual(layout.grid[y][x], 1)
                self.assertGreater(y, 0)
                self.assertTrue(is_open(layout.grid, (x, y + 1), layout.doors, skipped(layout)))
                for dx in (-1, 0, 1):
                    self.assertNotIn((x + dx, y), layout.doors)
                    self.assertNotIn((x + dx, y + 1), layout.doors)

    def test_dressing_keeps_clear_of_stairs(self):
        """Regression: a rug once drew over a staircase because stairs are props, not grid cells."""
        checked = 0
        for layout in self.layouts:
            zone = stair_zone(layout.stairs, TILE)
            checked += len(zone)
            for _, x, y in wall_fixtures(layout.grid, layout.doors, skipped(layout)):
                self.assertNotIn((x, y), zone)
            for _, x, y in floor_wear(layout.grid, layout.doors, skipped(layout)):
                self.assertNotIn((x, y), zone)
        self.assertGreater(checked, 0)

    def test_wear_only_marks_plain_floor(self):
        for layout in self.layouts:
            blocked = furniture_cells(layout)
            for variant, x, y in floor_wear(layout.grid, layout.doors, skipped(layout)):
                self.assertEqual(layout.grid[y][x], 0)
                self.assertNotIn((x, y), blocked)
                self.assertNotIn((x, y), layout.doors)

    def test_plans_are_repeatable_and_modest(self):
        for layout in self.layouts:
            args = (layout.grid, layout.doors, skipped(layout))
            self.assertEqual(wall_fixtures(*args), wall_fixtures(*args))
            self.assertEqual(floor_wear(*args), floor_wear(*args))
            floor_cells = sum(row.count(0) for row in layout.grid)
            self.assertLess(len(floor_wear(*args)), floor_cells * .2)

    def test_nothing_is_placed_beside_a_door(self):
        # A 9x7 room split by an inner wall (row 3) that has a door at (4, 3).
        grid = [[1] * 9] + [[1] + [0] * 7 + [1] for _ in range(5)] + [[1] * 9]
        grid[3] = [1] * 9
        grid[3][4] = 0
        doors = {(4, 3): object()}
        columns = {x for _, x, y in wall_fixtures(grid, doors, density=1., spacing=1) if y == 3}
        self.assertFalse(columns & {3, 4, 5}, columns)
        self.assertTrue(columns & {1, 2, 6, 7}, "fixtures should still appear away from the door")


if __name__ == "__main__":
    unittest.main()