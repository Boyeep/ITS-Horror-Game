# %%manim -qm -v WARNING HillClimbGhostAI
from manimgx import *
import numpy as np

class HillClimbGhostAI(ThreeDScene):
    def construct(self):
        hl = Text(
            "Hill Climbing (Local Search) pada Game AI",
            t2w={"Hill Climbing": BOLD},
        ).scale(0.8)
        punch = (
            Text(
                "cara Ghost mendeteksi & mengejar Player",
                t2w={"Ghost": BOLD},
                t2c={"Ghost": "#EE4B2B"},
            )
            .scale(0.7)
            .next_to(hl, DOWN, buff=0.43)
        )
        watermark = Text("@strxlette.dev", fill_opacity=0.35, font_size=30).to_corner(DL)
        self.add_fixed_in_frame_mobjects(watermark)

        self.play(Write(hl), Write(watermark), run_time=1.55)
        self.wait(0.3)
        self.play(Write(punch), run_time=1.4)
        self.wait(1.7)

        axes = ThreeDAxes(
            x_range=[-3.2, 3.2, 1],
            y_range=[-3.2, 3.2, 1],
            z_range=[-0.5, 3.0, 1],
            x_length=6.8,
            y_length=6.8,
            z_length=3.6,
            axis_config={"color": BLUE_D, "include_tip": False},
        ).shift(DOWN * 0.35)

        # Smooth terrain with 3 ambiguous gentle peaks + subtle ripples
        def terrain_z(u, v, px=0.0, py=0.0, p_amp=0.0):
            h1 = 0.85 * np.exp(-((u + 1.6) ** 2 + (v - 1.2) ** 2) / 2.2)
            h2 = 0.90 * np.exp(-((u - 1.5) ** 2 + (v - 1.3) ** 2) / 2.0)
            h3 = 0.82 * np.exp(-((u - 0.2) ** 2 + (v + 1.6) ** 2) / 2.4)
            ripples = 0.10 * np.sin(1.5 * u) * np.cos(1.5 * v)
            base = 0.18 + h1 + h2 + h3 + ripples
            if p_amp > 0.001:
                spike = p_amp * np.exp(-((u - px) ** 2 + (v - py) ** 2) / (2 * 0.45 ** 2))
                base += spike
            return base

        # ValueTrackers for Player (x, y, peak amplitude) and Ghost (x, y)
        px_tr = ValueTracker(-0.3)
        py_tr = ValueTracker(-0.2)
        p_amp_tr = ValueTracker(0.0)

        gx_tr = ValueTracker(-0.4)
        gy_tr = ValueTracker(-0.3)

        base_surface = Surface(
            lambda u, v: axes.c2p(u, v, terrain_z(u, v)),
            u_range=[-3.0, 3.0],
            v_range=[-3.0, 3.0],
            resolution=(20, 20),
            checkerboard_colors=[BLUE_E, TEAL_E],
            fill_opacity=0.55,
            stroke_color=TEAL_C,
            stroke_width=0.6,
        )

        # Dynamic 3D topographic wireframe mesh that morphs when Player peak appears/moves
        u_grid = np.linspace(-3.0, 3.0, 17)
        v_grid = np.linspace(-3.0, 3.0, 17)
        dyn_mesh = VGroup()
        for _ in range(len(u_grid) + len(v_grid)):
            line = VMobject(stroke_color=TEAL_B, stroke_width=1.3, stroke_opacity=0.65)
            dyn_mesh.add(line)

        def update_dyn_mesh(mob):
            px_v = px_tr.get_value()
            py_v = py_tr.get_value()
            amp_v = p_amp_tr.get_value()
            idx = 0
            for u in u_grid:
                pts = [axes.c2p(u, v, terrain_z(u, v, px_v, py_v, amp_v)) for v in v_grid]
                mob[idx].set_points_as_corners(pts)
                idx += 1
            for v in v_grid:
                pts = [axes.c2p(u, v, terrain_z(u, v, px_v, py_v, amp_v)) for u in u_grid]
                mob[idx].set_points_as_corners(pts)
                idx += 1

        update_dyn_mesh(dyn_mesh)

        # Transition from Section 0 to 3D Hill Map
        self.play(FadeOut(punch), ReplacementTransform(hl, axes), run_time=1.6)
        self.move_camera(phi=62 * DEGREES, theta=-48 * DEGREES, run_time=2.2)

        sec1_badge = Text(
            "1. Smooth Hill Map — Ambiguous Peaks & Simulated Annealing",
            font_size=19,
            t2w={"1. Smooth Hill Map": BOLD},
        ).to_corner(UL, buff=0.35)
        sec1_box = SurroundingRectangle(
            sec1_badge, color=BLUE_C, fill_color=BLACK, fill_opacity=0.75, buff=0.12, corner_radius=0.1
        )
        sec1_hud = VGroup(sec1_box, sec1_badge)
        self.add_fixed_in_frame_mobjects(sec1_hud)

        self.play(Create(base_surface), Create(dyn_mesh), FadeIn(sec1_hud), run_time=2.4)
        dyn_mesh.add_updater(update_dyn_mesh)

        # Highlight the 3 ambiguous peaks (similar heights, no clear global target)
        amb_coords = [(-1.6, 1.2), (1.5, 1.3), (0.2, -1.6)]
        amb_markers = VGroup()
        for ux, vy in amb_coords:
            z_val = terrain_z(ux, vy)
            pt = axes.c2p(ux, vy, z_val)
            ring = Circle(radius=0.32, color=YELLOW, stroke_width=2.5).move_to(pt)
            dot = Dot3D(point=pt, radius=0.07, color=YELLOW)
            amb_markers.add(VGroup(ring, dot))

        amb_label = Text(
            "Ambiguous Peaks (hampir sama tinggi)",
            font_size=18,
            t2c={"Ambiguous Peaks": "#FFFF00"},
        )
        amb_label.next_to(sec1_hud, DOWN, aligned_edge=LEFT, buff=0.16)
        self.add_fixed_in_frame_mobjects(amb_label)

        self.play(FadeIn(amb_markers, scale=1.3), FadeIn(amb_label), run_time=1.4)
        self.play(*[Indicate(m, color=YELLOW, scale_factor=1.2) for m in amb_markers], run_time=1.4)
        self.wait(0.6)

        # Spawn Ghost entity on 3D surface + Temperature HUD bar (Simulated Annealing)
        ghost_dot = Dot3D(radius=0.13, color=RED_B)
        ghost_ring = Circle(radius=0.38, color=RED_A, stroke_width=2.5)
        ghost_stem = Line(ORIGIN, UP * 0.4, color=RED_C, stroke_width=2.5)
        ghost_group = VGroup(ghost_ring, ghost_stem, ghost_dot)

        def update_ghost_3d(mob):
            gx_v = gx_tr.get_value()
            gy_v = gy_tr.get_value()
            gz_v = terrain_z(gx_v, gy_v, px_tr.get_value(), py_tr.get_value(), p_amp_tr.get_value())
            surf_pt = axes.c2p(gx_v, gy_v, gz_v)
            base_pt = axes.c2p(gx_v, gy_v, 0)
            mob[0].move_to(surf_pt + OUT * 0.03)
            mob[1].put_start_and_end_on(base_pt, surf_pt + OUT * 0.12)
            mob[2].move_to(surf_pt + OUT * 0.12)

        update_ghost_3d(ghost_group)
        ghost_group.add_updater(update_ghost_3d)

        # Simulated Annealing Temperature HUD (Top-Right, updated in-place to stay fixed-in-frame)
        temp_tr = ValueTracker(0.85)
        temp_title = Text(
            "Ghost AI: Simulated Annealing",
            font_size=18,
            color=RED_B,
            t2w={"Ghost AI": BOLD},
        )
        temp_bar_bg = Rectangle(width=2.2, height=0.20, color=GREY_B, fill_color=GREY_E, fill_opacity=0.8)
        temp_lbl = Text("Temp (Randomness)", font_size=15, color=GREY_A)
        temp_hud = VGroup(temp_title, temp_bar_bg, temp_lbl).arrange(DOWN, aligned_edge=LEFT, buff=0.09)
        temp_hud.to_corner(UR, buff=0.35)

        temp_bar_fill = Rectangle(
            width=2.2 * 0.85,
            height=0.20,
            stroke_width=0,
            fill_color=ORANGE,
            fill_opacity=0.9,
        ).move_to(temp_bar_bg.get_left(), aligned_edge=LEFT)

        def update_temp_bar(mob):
            val = np.clip(temp_tr.get_value(), 0.05, 1.0)
            mob.stretch_to_fit_width(2.2 * val)
            mob.move_to(temp_bar_bg.get_left(), aligned_edge=LEFT)
            mob.set_fill(color=interpolate_color(BLUE_C, ORANGE, val), opacity=0.9)

        temp_bar_fill.add_updater(update_temp_bar)
        self.add_fixed_in_frame_mobjects(temp_hud, temp_bar_fill)

        self.play(FadeIn(ghost_group), FadeIn(temp_hud), FadeIn(temp_bar_fill), run_time=1.4)

        # Helper to show Ghost sampling local neighbors before moving
        def ghost_step_3d(target_x, target_y, temp_val, step_time=1.35, is_jump=False):
            cx, cy = gx_tr.get_value(), gy_tr.get_value()
            px_v, py_v, amp_v = px_tr.get_value(), py_tr.get_value(), p_amp_tr.get_value()
            offsets = [(0.45, 0.0), (-0.45, 0.0), (0.0, 0.45), (0.0, -0.45)]
            probes = VGroup()
            for dx, dy in offsets:
                nx, ny = np.clip(cx + dx, -2.9, 2.9), np.clip(cy + dy, -2.9, 2.9)
                nz = terrain_z(nx, ny, px_v, py_v, amp_v)
                probes.add(
                    Dot3D(point=axes.c2p(nx, ny, nz + 0.06), radius=0.055, color=ORANGE if is_jump else YELLOW)
                )
            self.play(FadeIn(probes, scale=1.4), temp_tr.animate.set_value(temp_val), run_time=0.45)
            self.play(
                gx_tr.animate.set_value(target_x),
                gy_tr.animate.set_value(target_y),
                FadeOut(probes),
                run_time=step_time,
            )

        # Start gentle ambient camera rotation during Section 1 search
        self.begin_ambient_camera_rotation(rate=0.08)

        # Climb toward Ambiguous Peak 1 (-1.6, 1.2)
        ghost_step_3d(-1.0, 0.4, 0.65, step_time=1.3)
        ghost_step_3d(-1.6, 1.2, 0.40, step_time=1.4)
        self.play(Indicate(amb_markers[0], color=RED_A, scale_factor=1.25), run_time=0.9)

        # Stuck at local ambiguous peak -> Simulated Annealing increases randomness & jumps across saddle
        sa_note = Text(
            "Local Optimum! Random Jump (SA)",
            font_size=17,
            t2c={"Local Optimum!": "#FFA500"},
        )
        sa_note.next_to(temp_hud, DOWN, aligned_edge=RIGHT, buff=0.16)
        self.add_fixed_in_frame_mobjects(sa_note)
        self.play(FadeIn(sa_note), temp_tr.animate.set_value(0.95), run_time=0.8)

        ghost_step_3d(-0.2, 0.3, 0.90, step_time=1.4, is_jump=True)
        self.play(FadeOut(sa_note), run_time=0.5)

        # Climbs toward Ambiguous Peak 2 (1.5, 1.3)
        ghost_step_3d(0.8, 0.9, 0.60, step_time=1.3)
        ghost_step_3d(1.5, 1.3, 0.35, step_time=1.3)
        self.play(Indicate(amb_markers[1], color=RED_A, scale_factor=1.25), run_time=0.9)

        # Jumps again toward Peak 3 / middle-right (0.6, -0.6) searching indefinitely
        ghost_step_3d(0.7, -0.1, 0.85, step_time=1.3, is_jump=True)
        ghost_step_3d(0.2, -1.5, 0.55, step_time=1.3)
        self.play(Indicate(amb_markers[2], color=RED_A, scale_factor=1.25), run_time=0.9)
        ghost_step_3d(0.6, -0.6, 0.75, step_time=1.3, is_jump=True)

        self.stop_ambient_camera_rotation()
        self.play(FadeOut(amb_markers), FadeOut(amb_label), run_time=0.9)

        sec2_badge = Text(
            "2. Player Entity — Narrow & Tall Moving Peak",
            font_size=19,
            t2w={"2. Player Entity": BOLD},
        ).to_corner(UL, buff=0.35)
        sec2_box = SurroundingRectangle(
            sec2_badge, color=GREEN_C, fill_color=BLACK, fill_opacity=0.75, buff=0.12, corner_radius=0.1
        )
        sec2_hud = VGroup(sec2_box, sec2_badge)
        self.add_fixed_in_frame_mobjects(sec2_hud)
        self.play(FadeOut(sec1_hud), FadeIn(sec2_hud), run_time=1.0)

        # Concentric 3D contour rings that visualize the sharp Player spike clearly
        spike_rings = VGroup()
        ring_fracs = [0.18, 0.36, 0.55, 0.74, 0.90]
        for f in ring_fracs:
            c = Circle(radius=0.2, stroke_width=2.4, color=interpolate_color(TEAL_A, YELLOW, f))
            spike_rings.add(c)

        player_dot = Dot3D(radius=0.13, color=GREEN_B)
        player_beacon = Line(ORIGIN, UP * 0.5, color=GREEN_A, stroke_width=2.5)
        player_group = VGroup(spike_rings, player_beacon, player_dot)

        def update_player_3d(mob):
            px_v = px_tr.get_value()
            py_v = py_tr.get_value()
            amp_v = p_amp_tr.get_value()
            top_z = terrain_z(px_v, py_v, px_v, py_v, amp_v)
            base_z_val = terrain_z(px_v, py_v, px_v, py_v, 0.0)
            sigma = 0.45
            for idx, f in enumerate(ring_fracs):
                ring_mob = mob[0][idx]
                if amp_v < 0.08:
                    ring_mob.set_stroke(opacity=0.0)
                else:
                    r_val = sigma * np.sqrt(-2.0 * np.log(f))
                    theta_pts = np.linspace(0, TAU, 28)
                    pts = [
                        axes.c2p(
                            px_v + r_val * np.cos(th),
                            py_v + r_val * np.sin(th),
                            terrain_z(px_v + r_val * np.cos(th), py_v + r_val * np.sin(th), px_v, py_v, amp_v) + 0.02,
                        )
                        for th in theta_pts
                    ]
                    ring_mob.set_points_as_corners(pts)
                    ring_mob.set_stroke(opacity=min(0.95, amp_v / 1.5))
            mob[1].put_start_and_end_on(axes.c2p(px_v, py_v, base_z_val), axes.c2p(px_v, py_v, top_z + 0.14))
            mob[2].move_to(axes.c2p(px_v, py_v, top_z + 0.14))

        update_player_3d(player_group)
        player_group.add_updater(update_player_3d)
        self.add(player_group)

        # Spawn Player & raise the narrow tall peak!
        p_note = Text(
            "Player Peak: sempit tapi sangat tinggi",
            font_size=18,
            t2c={"Player Peak": "#00FFAA"},
        )
        p_note.next_to(sec2_hud, DOWN, aligned_edge=LEFT, buff=0.16)
        self.add_fixed_in_frame_mobjects(p_note)

        self.play(
            p_amp_tr.animate.set_value(1.85),
            FadeIn(p_note),
            run_time=2.4,
        )
        self.wait(0.8)

        # Show that the peak moves along with the Player
        self.move_camera(phi=58 * DEGREES, theta=-30 * DEGREES, run_time=1.8)
        self.play(
            px_tr.animate.set_value(0.25),
            py_tr.animate.set_value(-0.15),
            run_time=2.5,
        )
        self.wait(0.5)

        # Ghost at (0.6, -0.6) is now on the slope of the Player's peak!
        detect_lbl = Text(
            "Peak Detected! Ghost climbs steep gradient",
            font_size=17,
            t2w={"Peak Detected!": BOLD},
            t2c={"Peak Detected!": "#FF4444"},
        )
        detect_lbl.next_to(temp_hud, DOWN, aligned_edge=RIGHT, buff=0.16)
        self.add_fixed_in_frame_mobjects(detect_lbl)
        self.play(FadeIn(detect_lbl), temp_tr.animate.set_value(0.15), run_time=0.9)

        # Ghost climbs the Player's moving peak step by step and nearly meets the Player!
        ghost_step_3d(0.45, -0.38, 0.15, step_time=1.4)
        self.play(
            px_tr.animate.set_value(0.15),
            py_tr.animate.set_value(0.05),
            gx_tr.animate.set_value(0.30),
            gy_tr.animate.set_value(-0.12),
            run_time=1.8,
        )
        # Ghost reaches right next to Player (center of peak!)
        ghost_step_3d(0.18, 0.02, 0.10, step_time=1.3)
        self.wait(0.6)

        # Player dashes away! Because the peak is narrow, Ghost loses the peak!
        lost_lbl = Text(
            "Player Moves Away → Ghost kehilangan jejak peak!",
            font_size=17,
            t2c={"Player Moves Away": "#FFFF00"},
        )
        lost_lbl.next_to(temp_hud, DOWN, aligned_edge=RIGHT, buff=0.16)
        self.add_fixed_in_frame_mobjects(lost_lbl)

        self.play(
            FadeOut(detect_lbl),
            FadeIn(lost_lbl),
            px_tr.animate.set_value(-1.75),
            py_tr.animate.set_value(-1.35),
            temp_tr.animate.set_value(0.80),
            run_time=2.3,
        )
        self.wait(0.5)

        # Ghost falls back onto smooth terrain and wanders toward the wrong ambiguous peak (1.5, 1.3)
        ghost_step_3d(0.75, 0.55, 0.70, step_time=1.4, is_jump=True)
        ghost_step_3d(1.45, 1.25, 0.45, step_time=1.4)
        self.wait(1.0)

        # Clean up Section 1 & 2 3D objects before Section 3
        dyn_mesh.remove_updater(update_dyn_mesh)
        ghost_group.remove_updater(update_ghost_3d)
        player_group.remove_updater(update_player_3d)
        temp_bar_fill.remove_updater(update_temp_bar)

        self.play(
            FadeOut(base_surface),
            FadeOut(dyn_mesh),
            FadeOut(ghost_group),
            FadeOut(player_group),
            FadeOut(axes),
            FadeOut(p_note),
            FadeOut(lost_lbl),
            FadeOut(temp_hud),
            FadeOut(temp_bar_fill),
            run_time=1.6,
        )

        self.move_camera(phi=0 * DEGREES, theta=-90 * DEGREES, run_time=1.6)

        sec3_badge = Text(
            "3. Real Game Grid Simulation — Walls, Exit & Local Search",
            font_size=19,
            t2w={"3. Real Game Grid Simulation": BOLD},
        ).to_corner(UL, buff=0.35)
        sec3_box = SurroundingRectangle(
            sec3_badge, color=YELLOW, fill_color=BLACK, fill_opacity=0.75, buff=0.12, corner_radius=0.1
        )
        sec3_hud = VGroup(sec3_box, sec3_badge)
        self.add_fixed_in_frame_mobjects(sec3_hud)
        self.play(FadeOut(sec2_hud), FadeIn(sec3_hud), run_time=0.9)

        # 9x9 Grid Map definition (y=0 bottom .. y=8 top, x=0 left .. x=8 right)
        # 1 = Wall, 0 = Floor, 2 = Exit at right boundary (8, 4)
        grid_rows_top_down = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1],  # y=8
            [1, 0, 0, 0, 1, 0, 0, 0, 1],  # y=7
            [1, 0, 1, 0, 0, 0, 1, 0, 1],  # y=6
            [1, 0, 1, 0, 1, 0, 1, 0, 1],  # y=5
            [1, 0, 0, 0, 1, 0, 0, 0, 2],  # y=4 (Exit at x=8, y=4)
            [1, 0, 1, 1, 1, 0, 1, 0, 1],  # y=3
            [1, 0, 0, 0, 0, 0, 1, 0, 1],  # y=2
            [1, 0, 1, 0, 0, 0, 0, 0, 1],  # y=1
            [1, 1, 1, 1, 1, 1, 1, 1, 1],  # y=0
        ]
        grid = grid_rows_top_down[::-1]

        # Static random height initialization on valid paths (with ambiguous higher hill at top-left (1,7)-(2,7))
        # Walls have very low height (-1.0)
        base_z_map = np.full((9, 9), -1.0)
        floor_heights = {
            (1, 7): 1.08, (2, 7): 0.94, (3, 7): 0.78, (5, 7): 0.48, (6, 7): 0.42, (7, 7): 0.38,
            (1, 6): 0.82,               (3, 6): 0.64, (4, 6): 0.60, (5, 6): 0.57,               (7, 6): 0.40,
            (1, 5): 0.55,               (3, 5): 0.52,               (5, 5): 0.50,               (7, 5): 0.41,
            (1, 4): 0.36, (2, 4): 0.39, (3, 4): 0.42,               (5, 4): 0.42, (6, 4): 0.38, (7, 4): 0.35, (8, 4): 0.32,
            (1, 3): 0.34,                                           (5, 3): 0.39,               (7, 3): 0.36,
            (1, 2): 0.33, (2, 2): 0.35, (3, 2): 0.37, (4, 2): 0.36, (5, 2): 0.38,               (7, 2): 0.37,
            (1, 1): 0.31,               (3, 1): 0.34, (4, 1): 0.35, (5, 1): 0.36, (6, 1): 0.34, (7, 1): 0.33,
        }
        for (cx, cy), h_val in floor_heights.items():
            base_z_map[cy][cx] = h_val

        cell_size = 0.60

        def cell_pos(gx, gy, z=0.0):
            return np.array([(gx - 4.0) * cell_size, (gy - 4.0) * cell_size - 0.15, z])

        # Build 2D Grid Tiles (~10s creation & visualization of Grid map, Player, and Ghost)
        tiles_group = VGroup()
        tile_dict = {}
        for y in range(9):
            for x in range(9):
                val = grid[y][x]
                if val == 1:
                    col = "#1B222C"
                    stroke_col = "#2E3B4E"
                elif val == 2:
                    col = "#1E6F50"
                    stroke_col = GREEN_A
                else:
                    col = "#2C3E50"
                    stroke_col = "#4A6582"
                sq = Square(
                    side_length=cell_size * 0.94,
                    fill_color=col,
                    fill_opacity=0.92,
                    stroke_color=stroke_col,
                    stroke_width=1.5,
                ).move_to(cell_pos(x, y, 0))
                tiles_group.add(sq)
                tile_dict[(x, y)] = sq

        exit_lbl = Text("EXIT", font_size=16, weight=BOLD, color=GREEN_A).move_to(cell_pos(8, 4, 0.02))

        # Legend in top-right (fixed in frame)
        leg_wall = VGroup(
            Square(side_length=0.19, fill_color="#1B222C", fill_opacity=1, stroke_color="#2E3B4E"),
            Text("Wall (Low z)", font_size=15),
        ).arrange(RIGHT, buff=0.10)
        leg_floor = VGroup(
            Square(side_length=0.19, fill_color="#2C3E50", fill_opacity=1, stroke_color="#4A6582"),
            Text("Floor (Valid Path)", font_size=15),
        ).arrange(RIGHT, buff=0.10)
        leg_exit = VGroup(
            Square(side_length=0.19, fill_color="#1E6F50", fill_opacity=1, stroke_color=GREEN_A),
            Text("Exit Boundary", font_size=15, color=GREEN_B),
        ).arrange(RIGHT, buff=0.10)
        leg_p = VGroup(
            Dot(color=GREEN_B, radius=0.08), Text("Player (Tall Peak)", font_size=15, color=GREEN_B)
        ).arrange(RIGHT, buff=0.10)
        leg_g = VGroup(
            Dot(color=RED_B, radius=0.08), Text("Ghost (Hill + SA)", font_size=15, color=RED_B)
        ).arrange(RIGHT, buff=0.10)
        legend_box = VGroup(leg_wall, leg_floor, leg_exit, leg_p, leg_g).arrange(DOWN, aligned_edge=LEFT, buff=0.09)
        legend_bg = SurroundingRectangle(
            legend_box, color=GREY_C, fill_color=BLACK, fill_opacity=0.75, buff=0.12, corner_radius=0.1
        )
        legend_hud = VGroup(legend_bg, legend_box).to_corner(UR, buff=0.35)
        self.add_fixed_in_frame_mobjects(legend_hud)

        self.play(
            LaggedStartMap(FadeIn, tiles_group, lag_ratio=0.015),
            FadeIn(exit_lbl),
            FadeIn(legend_hud),
            run_time=3.2,
        )
        self.wait(0.8)

        # Spawn Player at (1, 4) and Ghost near Escape at (6, 4)
        g_px = ValueTracker(1.0)
        g_py = ValueTracker(4.0)
        g_gx = ValueTracker(6.0)
        g_gy = ValueTracker(4.0)
        hill_alpha = ValueTracker(0.0)  # Controls 3D hill extrusion height

        def grid_total_z(x, y, px_v, py_v):
            ix, iy = int(round(np.clip(x, 0, 8))), int(round(np.clip(y, 0, 8)))
            if grid[iy][ix] == 1:
                return -0.85
            p_boost = 1.40 * np.exp(-((x - px_v) ** 2 + (y - py_v) ** 2) / (2 * 1.10 ** 2))
            return base_z_map[iy][ix] + p_boost

        player_token = VGroup(
            Circle(radius=cell_size * 0.36, color=GREEN_A, stroke_width=2.5),
            Dot3D(radius=0.11, color=GREEN_B),
        ).move_to(cell_pos(1, 4, 0.08))

        ghost_token = VGroup(
            Circle(radius=cell_size * 0.38, color=RED_A, stroke_width=2.5),
            Dot3D(radius=0.11, color=RED_B),
        ).move_to(cell_pos(6, 4, 0.08))

        spawn_note = Text(
            "Player di kiri (1,4) | Ghost spawn dekat Exit (6,4)",
            font_size=17,
            t2w={"(1,4)": BOLD, "(6,4)": BOLD},
        ).next_to(sec3_hud, DOWN, aligned_edge=LEFT, buff=0.15)
        self.add_fixed_in_frame_mobjects(spawn_note)

        self.play(
            FadeIn(player_token, scale=1.4),
            FadeIn(ghost_token, scale=1.4),
            FadeIn(spawn_note),
            run_time=1.8,
        )
        self.play(
            Indicate(player_token, color=GREEN_A),
            Indicate(ghost_token, color=RED_A),
            Indicate(tile_dict[(8, 4)], color=GREEN_A),
            run_time=1.6,
        )
        self.wait(1.2)

        hill_note = Text(
            "3D Grid Hill Map: Wall = Rendah (-z), Path = Static Hill + Player Peak",
            font_size=17,
            t2w={"3D Grid Hill Map": BOLD},
            t2c={"Player Peak": "#00FFAA"},
        ).next_to(sec3_hud, DOWN, aligned_edge=LEFT, buff=0.15)
        self.add_fixed_in_frame_mobjects(hill_note)

        # Create 3D Grid Hill wireframe + elevated cell plates
        grid_hill_lines = VGroup()
        for _ in range(18):
            grid_hill_lines.add(VMobject(stroke_color=TEAL_A, stroke_width=2.0, stroke_opacity=0.85))

        elevated_plates = VGroup()
        plate_coords = []
        for y in range(9):
            for x in range(9):
                is_wall = grid[y][x] == 1
                p_sq = Square(
                    side_length=cell_size * 0.86,
                    fill_color="#3A1C24" if is_wall else TEAL_C,
                    fill_opacity=0.55 if not is_wall else 0.35,
                    stroke_color=RED_E if is_wall else TEAL_A,
                    stroke_width=1.2,
                )
                elevated_plates.add(p_sq)
                plate_coords.append((x, y))

        plate_opacity_tr = ValueTracker(0.65)

        def update_grid_3d_hill(mob_lines):
            a = hill_alpha.get_value()
            op = plate_opacity_tr.get_value()
            px_v, py_v = g_px.get_value(), g_py.get_value()
            z_scale = 1.05 * a

            # Update 9 horizontal + 9 vertical 3D hill lines across grid centers
            idx = 0
            for y in range(9):
                pts = [cell_pos(x, y, grid_total_z(x, y, px_v, py_v) * z_scale) for x in range(9)]
                mob_lines[idx].set_points_as_corners(pts)
                mob_lines[idx].set_stroke(opacity=op)
                idx += 1
            for x in range(9):
                pts = [cell_pos(x, y, grid_total_z(x, y, px_v, py_v) * z_scale) for y in range(9)]
                mob_lines[idx].set_points_as_corners(pts)
                mob_lines[idx].set_stroke(opacity=op)
                idx += 1

            # Update elevated 3D plates & dynamic heatmap coloring on floor
            for p_idx, (cx, cy) in enumerate(plate_coords):
                zv = grid_total_z(cx, cy, px_v, py_v)
                plate = elevated_plates[p_idx]
                plate.move_to(cell_pos(cx, cy, zv * z_scale))
                if grid[cy][cx] == 1:
                    plate.set_fill(color="#3A1C24", opacity=op * 0.45)
                    plate.set_stroke(color=RED_E, opacity=op * 0.5)
                else:
                    t_col = np.clip((zv - 0.3) / 1.4, 0.0, 1.0)
                    c_fill = interpolate_color(TEAL_D, YELLOW, t_col)
                    plate.set_fill(color=c_fill, opacity=op * 0.65)
                    plate.set_stroke(color=c_fill, opacity=op * 0.85)
                    if (cx, cy) != (8, 4):
                        tile_dict[(cx, cy)].set_fill(
                            color=interpolate_color(BLUE_E, c_fill, 0.42),
                            opacity=0.92,
                        )

        def update_tokens(mob):
            a = hill_alpha.get_value()
            z_scale = 1.05 * a
            px_v, py_v = g_px.get_value(), g_py.get_value()
            gx_v, gy_v = g_gx.get_value(), g_gy.get_value()
            pz = max(0.08, grid_total_z(px_v, py_v, px_v, py_v) * z_scale + 0.08)
            gz = max(0.08, grid_total_z(gx_v, gy_v, px_v, py_v) * z_scale + 0.08)
            player_token.move_to(cell_pos(px_v, py_v, pz))
            ghost_token.move_to(cell_pos(gx_v, gy_v, gz))

        update_grid_3d_hill(grid_hill_lines)
        grid_hill_lines.add_updater(update_grid_3d_hill)
        player_token.add_updater(update_tokens)
        self.add(elevated_plates, grid_hill_lines)

        # Tilt camera & extrude the 3D hill graph of the grid map!
        self.play(FadeOut(spawn_note), FadeIn(hill_note), run_time=0.8)
        self.move_camera(
            phi=56 * DEGREES,
            theta=-55 * DEGREES,
            added_anims=[hill_alpha.animate.set_value(1.0)],
            run_time=2.8,
        )
        self.wait(1.2)

        # Highlight the Ambiguous Higher Hill at top-left (1,7)-(2,7) vs Player Peak at (1,4)
        amb_grid_ring = Circle(radius=0.45, color=YELLOW, stroke_width=3.0).move_to(
            cell_pos(1.5, 7.0, 1.08 * 1.05 + 0.1)
        )
        self.play(Create(amb_grid_ring), Indicate(elevated_plates[7 * 9 + 1], color=YELLOW), run_time=1.4)
        self.wait(1.4)
        self.play(FadeOut(amb_grid_ring), run_time=0.6)

        sim_note = Text(
            "Simulasi: Ghost terdistraksi bukit (1,7) → SA Jump keluar dari Local Peak!",
            font_size=17,
            t2w={"Simulasi": BOLD, "(1,7)": BOLD, "SA Jump": BOLD},
            t2c={"SA Jump": "#FFA500"},
        ).next_to(sec3_hud, DOWN, aligned_edge=LEFT, buff=0.15)
        self.add_fixed_in_frame_mobjects(sim_note)

        self.play(FadeOut(hill_note), FadeIn(sim_note), run_time=0.8)
        self.move_camera(
            phi=28 * DEGREES,
            theta=-78 * DEGREES,
            added_anims=[
                plate_opacity_tr.animate.set_value(0.24),
                hill_alpha.animate.set_value(0.55),
            ],
            run_time=2.2,
        )

        # Pre-verified exact simulation trajectory:
        # 1. Ghost climbs toward Player's peak, loses Player behind center walls, and gets lured to local peak (1,7).
        # 2. At (1,7), Simulated Annealing increases randomness (Temp ↑) so Ghost accepts downhill moves out of (1,7)!
        # 3. Freed from the local optimum, Ghost pursues down the left & bottom corridors and re-detects Player near Exit!
        sim_steps = [
            # (player_xy, ghost_xy, status_color)
            ((2, 4), (5, 4), YELLOW),
            ((3, 4), (5, 5), YELLOW),
            ((3, 5), (5, 6), ORANGE),   # Player nears upper pass; Ghost climbs toward (5,6)
            ((3, 6), (4, 6), RED_A),    # Ghost detects Player peak & enters (4,6)!
            ((3, 5), (3, 6), RED_A),    # Player retreats down; Ghost chases into (3,6)!
            ((3, 4), (3, 5), RED_A),    # Player ducks behind wall; Ghost reaches (3,5)!
            ((2, 4), (3, 6), YELLOW),   # Player breaks distance left; Ghost checks (3,6)
            ((1, 4), (3, 7), YELLOW),   # Player peak too far; Ghost lured by higher hill at (3,7) [z=0.78]!
            ((1, 3), (2, 7), YELLOW),   # Ghost climbs ambiguous hill (2,7) [z=0.94]
            ((1, 2), (1, 7), YELLOW),   # Ghost reaches local maximum (1,7) [z=1.08]!
            ((2, 2), (1, 6), ORANGE),   # SA ESCAPE! High Temp accepts downhill move (1,7) -> (1,6) [z=0.82]!
            ((3, 2), (1, 5), ORANGE),   # SA ESCAPE! Continues downhill (1,6) -> (1,5) [z=0.55]!
            ((4, 2), (1, 4), ORANGE),   # Ghost breaks out of local peak basin at (1,4)!
            ((5, 2), (1, 3), YELLOW),   # Ghost explores down the left corridor (1,3)
            ((5, 1), (1, 2), YELLOW),   # Player takes bottom-right loop; Ghost rounds bottom-left (1,2)
            ((6, 1), (2, 2), YELLOW),   # Ghost moves along bottom corridor (2,2)
            ((7, 1), (3, 2), YELLOW),   # Ghost advances to (3,2)
            ((7, 2), (4, 2), ORANGE),   # Ghost senses rising gradient toward (5,2)
            ((7, 3), (5, 2), RED_A),    # Ghost detects Player's peak & takes inner shortcut (5,2)!
            ((7, 4), (5, 3), RED_A),    # Ghost climbs steep Player gradient (5,3)!
            ((7, 4), (5, 4), RED_A),    # Ghost bursts into (5,4) right behind Player!
            ((8, 4), (6, 4), GREEN_A),  # Player barely escapes into EXIT (8,4) with Ghost at (6,4)!
        ]

        # Path trail lines on the grid for visual clarity
        p_trail = VMobject(stroke_color=GREEN_B, stroke_width=3.5, stroke_opacity=0.8)
        g_trail = VMobject(stroke_color=RED_B, stroke_width=3.5, stroke_opacity=0.8)
        p_pts = [cell_pos(1, 4, 0.04)]
        g_pts = [cell_pos(6, 4, 0.04)]
        p_trail.set_points_as_corners(p_pts + p_pts)
        g_trail.set_points_as_corners(g_pts + g_pts)
        self.add(p_trail, g_trail)

        sa_escape_note = None

        for step_i, ((npx, npy), (ngx, ngy), s_col) in enumerate(sim_steps):
            cgx, cgy = int(round(g_gx.get_value())), int(round(g_gy.get_value()))
            # Briefly flash Ghost's local search neighbor evaluation on the grid
            probes = VGroup()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                tx, ty = cgx + dx, cgy + dy
                if 0 <= tx < 9 and 0 <= ty < 9 and grid[ty][tx] != 1:
                    probes.add(
                        Square(
                            side_length=cell_size * 0.88,
                            stroke_color=s_col,
                            stroke_width=2.5,
                            fill_color=s_col,
                            fill_opacity=0.18,
                        ).move_to(cell_pos(tx, ty, 0.03))
                    )

            p_pts.append(cell_pos(npx, npy, 0.04))
            g_pts.append(cell_pos(ngx, ngy, 0.04))

            self.play(FadeIn(probes), run_time=0.20)
            self.play(
                g_px.animate.set_value(npx),
                g_py.animate.set_value(npy),
                g_gx.animate.set_value(ngx),
                g_gy.animate.set_value(ngy),
                FadeOut(probes),
                run_time=0.62,
            )
            p_trail.set_points_as_corners(p_pts)
            g_trail.set_points_as_corners(g_pts)

            # Highlight key moments during the simulation
            if step_i == 3:
                # Ghost detects player peak at upper pass!
                chase_alert = Circle(radius=cell_size * 0.55, color=RED_A, stroke_width=4).move_to(cell_pos(4, 6, 0.1))
                self.play(FadeIn(chase_alert, scale=0.6), run_time=0.35)
                self.play(FadeOut(chase_alert, scale=1.5), run_time=0.35)
            elif step_i == 9:
                # Ghost reaches local peak (1,7) -> Simulated Annealing triggers to escape!
                trap_alert = Circle(radius=cell_size * 0.6, color=ORANGE, stroke_width=4).move_to(cell_pos(1, 7, 0.1))
                sa_escape_note = Text(
                    "Local Peak (1,7)! SA (Temp ↑) terima langkah turun → bebas dari jebakan!",
                    font_size=17,
                    t2w={"Local Peak (1,7)!": BOLD, "SA (Temp ↑)": BOLD},
                    t2c={"Local Peak (1,7)!": "#FFFF00", "SA (Temp ↑)": "#FFA500"},
                ).next_to(sec3_hud, DOWN, aligned_edge=LEFT, buff=0.15)
                self.add_fixed_in_frame_mobjects(sa_escape_note)
                self.play(
                    FadeIn(trap_alert, scale=0.6),
                    FadeOut(sim_note),
                    FadeIn(sa_escape_note),
                    Flash(ghost_token, color=ORANGE, line_length=0.35, flash_radius=0.45),
                    run_time=0.55,
                )
                self.play(FadeOut(trap_alert, scale=1.5), run_time=0.4)
            elif step_i == 18:
                # Ghost re-detects Player's tall peak near the exit corridor!
                re_alert = Circle(radius=cell_size * 0.55, color=RED_A, stroke_width=4).move_to(cell_pos(5, 2, 0.1))
                self.play(FadeIn(re_alert, scale=0.6), run_time=0.3)
                self.play(FadeOut(re_alert, scale=1.5), run_time=0.3)

        # Final celebration as Player barely escapes at (8, 4) with Ghost right behind!
        win_banner = Text(
            "PLAYER ESCAPED! SA bebaskan Ghost dari Peak (1,7) & kejar sampai Exit",
            font_size=18,
            t2w={"PLAYER ESCAPED!": BOLD, "Peak (1,7)": BOLD},
            t2c={"PLAYER ESCAPED!": "#00FF88", "SA": "#FFA500"},
        ).to_edge(DOWN, buff=0.32).shift(RIGHT * 0.85)
        win_box = SurroundingRectangle(
            win_banner, color=GREEN_A, fill_color=BLACK, fill_opacity=0.85, buff=0.15, corner_radius=0.12
        )
        win_group = VGroup(win_box, win_banner)
        self.add_fixed_in_frame_mobjects(win_group)

        self.play(
            FadeIn(win_group),
            Flash(player_token, color=GREEN_A, line_length=0.4, flash_radius=0.5),
            Indicate(tile_dict[(8, 4)], color=GREEN_A, scale_factor=1.25),
            run_time=1.6,
        )
        self.wait(2.5)