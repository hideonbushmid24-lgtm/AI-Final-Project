
from __future__ import annotations

from collections import Counter
from time import perf_counter

import pygame

from ..puzzle import build_puzzle
from ..propagation import create_initial_domains
from ..solver import SolveResult, SolverEvent, solve
from ..demo_puzzle import build_backtracking_demo


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

WINDOW_WIDTH = 1420
WINDOW_HEIGHT = 850

BOARD_X = 35
BOARD_Y = 135
CELL_SIZE = 60

PANEL_X = 625

BACKGROUND = (20, 25, 36)
PANEL = (31, 39, 53)
PANEL_LIGHT = (42, 53, 71)

WHITE_CELL = (238, 241, 246)
BLACK_CELL = (24, 29, 40)

TEXT = (236, 240, 248)
MUTED = (156, 169, 188)

ACCENT = (75, 150, 235)
GREEN = (65, 190, 135)
ORANGE = (245, 170, 75)
RED = (225, 90, 95)

GRID = (105, 118, 137)

BUTTONS = [
    ("Run Solver", "run"),
    ("Step", "step"),
    ("Play", "play"),
    ("Pause", "pause"),
    ("Reset", "reset"),
]


class KakuroApp:

    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Kakuro CSP Solver")

        self.screen = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            pygame.RESIZABLE,
        )

        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("segoeui", 29, bold=True)
        self.font_heading = pygame.font.SysFont("segoeui", 19, bold=True)
        self.font_normal = pygame.font.SysFont("segoeui", 15)
        self.font_small = pygame.font.SysFont("segoeui", 12)
        self.font_digit = pygame.font.SysFont("segoeui", 25, bold=True)
        self.font_candidate = pygame.font.SysFont("segoeui", 13, bold=True)
        self.font_mono = pygame.font.SysFont("consolas", 12)

        self.mode = "reference"
        self.puzzle = build_puzzle()

        self.result: SolveResult | None = None
        self.events: tuple[SolverEvent, ...] = ()

        self.domains = create_initial_domains(self.puzzle)
        self.solution: dict[tuple[int, int], int] = {}

        self.selected_cell = min(self.puzzle.white_cells)
        self.last_cell = None

        self.event_index = 0
        self.history: list[SolverEvent] = []

        self.started = False
        self.solved = False
        self.playing = False

        self.speed = 12
        self.playback_accumulator = 0.0

        self.elapsed_seconds = 0.0
        self.status_message = "Ready. Click Run Solver to begin."

        self.button_rects: dict[str, pygame.Rect] = {}

        self.running = True

    # -----------------------------------------------------
    # Solver control
    # -----------------------------------------------------

    def start_solver(self):
        """Run the solver once and prepare its event sequence."""

        start = perf_counter()

        self.result = solve(
            self.puzzle,
            max_nodes=100_000,
        )

        self.elapsed_seconds = perf_counter() - start

        self.events = self.result.events

        self.domains = create_initial_domains(self.puzzle)
        self.solution = {}

        self.event_index = 0
        self.history.clear()

        self.last_cell = None

        self.started = True
        self.solved = False
        self.playing = False

        self.playback_accumulator = 0.0

        self.status_message = (
            f"Solver prepared: {len(self.events)} events."
        )

    def reset(self):
        self.result = None
        self.events = ()

        self.domains = create_initial_domains(self.puzzle)
        self.solution = {}

        self.event_index = 0
        self.history.clear()

        self.last_cell = None

        self.started = False
        self.solved = False
        self.playing = False

        self.playback_accumulator = 0.0
        self.elapsed_seconds = 0.0

        self.status_message = "Reset complete."

    def switch_puzzle(self, mode: str):
        if mode == self.mode:
            return

        if mode == "reference":
            self.puzzle = build_puzzle()

        elif mode == "demo":
            self.puzzle = build_backtracking_demo()

        else:
            raise ValueError(f"Unknown puzzle mode: {mode}")

        self.mode = mode
        self.reset()

        self.selected_cell = min(self.puzzle.white_cells)

        self.status_message = (
            "Reference 9x9 selected."
            if mode == "reference"
            else "Backtracking Demo selected."
        )

    def apply_event(self, event: SolverEvent):
        """Apply one recorded solver event to the visual state."""

        if event.event_type == "domain_pruned":
            if event.cell is not None:
                self.domains[event.cell] = set(
                    event.remaining_domain
                )

                self.last_cell = event.cell

            self.status_message = (
                f"Constraint Propagation: {event.message}"
            )

        elif event.event_type == "decision":
            if event.cell is not None and event.value is not None:
                self.domains[event.cell] = {event.value}
                self.last_cell = event.cell

            self.status_message = (
                f"Decision at depth {event.depth}: {event.message}"
            )

        elif event.event_type == "backtrack":
            # Restore the exact domain state before the failed branch.
            if event.domains_snapshot:
                self.domains = {
                    cell: set(values)
                    for cell, values in event.domains_snapshot
                }

            self.last_cell = event.cell

            self.status_message = (
                f"Backtracking: {event.message}"
            )

        elif event.event_type == "contradiction":
            self.status_message = (
                f"Contradiction: {event.message}"
            )

        elif event.event_type == "solution":
            self.solution = dict(self.result.solution)
            self.solved = True

            for cell, value in self.solution.items():
                self.domains[cell] = {value}

            self.status_message = (
                "Solution found and independently validated."
            )

        elif event.event_type == "search_limit":
            self.status_message = event.message
            self.playing = False

        elif event.event_type == "invalid_solution":
            self.status_message = event.message

        self.history.append(event)

    def step(self):
        if not self.started:
            self.start_solver()

        if self.event_index >= len(self.events):
            self.playing = False
            return

        event = self.events[self.event_index]

        self.apply_event(event)

        self.event_index += 1

        if self.event_index >= len(self.events):
            self.playing = False

    def play(self):
        if not self.started:
            self.start_solver()

        if self.event_index < len(self.events):
            self.playing = True
            self.status_message = "Playing solver trace..."

    def pause(self):
        self.playing = False
        self.status_message = "Playback paused."

    # -----------------------------------------------------
    # Drawing helpers
    # -----------------------------------------------------

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color=TEXT,
        font=None,
    ):
        font = font or self.font_normal

        surface = font.render(str(text), True, color)
        self.screen.blit(surface, (x, y))

    def draw_panel(self, rect, color=PANEL):
        pygame.draw.rect(
            self.screen,
            color,
            rect,
            border_radius=9,
        )

    def draw_button(
        self,
        rect: pygame.Rect,
        label: str,
        enabled: bool = True,
        active: bool = False,
    ):
        color = (
            ACCENT if active else
            PANEL_LIGHT if enabled else
            (48, 52, 62)
        )

        pygame.draw.rect(
            self.screen,
            color,
            rect,
            border_radius=7,
        )

        rendered = self.font_small.render(
            label,
            True,
            TEXT if enabled else MUTED,
        )

        self.screen.blit(
            rendered,
            rendered.get_rect(center=rect.center),
        )

    # -----------------------------------------------------
    # Kakuro board
    # -----------------------------------------------------

    def draw_clue_cell(self, row, col, rect):
        pygame.draw.rect(
            self.screen,
            BLACK_CELL,
            rect,
        )

        pygame.draw.line(
            self.screen,
            GRID,
            rect.topleft,
            rect.bottomright,
            1,
        )

        clue = self.puzzle.clues.get((row, col))

        if clue is None:
            return

        if clue.down is not None:
            self.draw_text(
                clue.down,
                rect.x + 35,
                rect.y + 5,
                ORANGE,
                self.font_small,
            )

        if clue.across is not None:
            self.draw_text(
                clue.across,
                rect.x + 5,
                rect.y + 39,
                GREEN,
                self.font_small,
            )

    def draw_white_cell(self, row, col, rect):
        cell = (row, col)

        selected = cell == self.selected_cell
        recently_changed = cell == self.last_cell

        fill = WHITE_CELL

        pygame.draw.rect(self.screen, fill, rect)

        if self.solved and cell in self.solution:
            value = self.solution[cell]

            rendered = self.font_digit.render(
                str(value),
                True,
                (28, 49, 76),
            )

            self.screen.blit(
                rendered,
                rendered.get_rect(center=rect.center),
            )

        else:
            domain = sorted(self.domains.get(cell, set()))

            if len(domain) == 1:
                rendered = self.font_digit.render(
                    str(domain[0]),
                    True,
                    (35, 95, 90),
                )

                self.screen.blit(
                    rendered,
                    rendered.get_rect(center=rect.center),
                )

            else:
                # Arrange candidates in a 3 x 3 mini-grid.
                for value in domain:
                    mini_col = (value - 1) % 3
                    mini_row = (value - 1) // 3

                    x = rect.x + 10 + mini_col * 18
                    y = rect.y + 5 + mini_row * 17

                    self.draw_text(
                        value,
                        x,
                        y,
                        (55, 74, 98),
                        self.font_candidate,
                    )

        if recently_changed:
            pygame.draw.rect(
                self.screen,
                ORANGE,
                rect,
                width=3,
            )

        if selected:
            pygame.draw.rect(
                self.screen,
                ACCENT,
                rect,
                width=3,
            )
        else:
            pygame.draw.rect(
                self.screen,
                GRID,
                rect,
                width=1,
            )

    def draw_board(self):
        self.draw_text(
            "KAKURO BOARD",
            BOARD_X,
            91,
            TEXT,
            self.font_heading,
        )

        reference_rect = pygame.Rect(245, 88, 135, 32)
        demo_rect = pygame.Rect(390, 88, 165, 32)

        self.button_rects["reference"] = reference_rect
        self.button_rects["demo"] = demo_rect

        self.draw_button(
            reference_rect,
            "Reference 9x9",
            active=self.mode == "reference",
        )

        self.draw_button(
            demo_rect,
            "Backtracking Demo",
            active=self.mode == "demo",
        )

        for row_index, row in enumerate(
            self.puzzle.grid_layout,
            start=1,
        ):
            for col_index, symbol in enumerate(
                row,
                start=1,
            ):
                x = BOARD_X + (col_index - 1) * CELL_SIZE
                y = BOARD_Y + (row_index - 1) * CELL_SIZE

                rect = pygame.Rect(
                    x,
                    y,
                    CELL_SIZE,
                    CELL_SIZE,
                )

                if symbol == "#":
                    self.draw_clue_cell(
                        row_index,
                        col_index,
                        rect,
                    )
                else:
                    self.draw_white_cell(
                        row_index,
                        col_index,
                        rect,
                    )

    # -----------------------------------------------------
    # Information panel
    # -----------------------------------------------------

    def draw_controls(self):
        x = PANEL_X

        self.draw_text(
            "SOLVER CONTROL",
            x,
            90,
            TEXT,
            self.font_heading,
        )

        button_width = 132
        button_height = 40
        gap = 10

        for index, (label, action) in enumerate(BUTTONS):
            rect = pygame.Rect(
                x + index * (button_width + gap),
                125,
                button_width,
                button_height,
            )

            self.button_rects[action] = rect

            self.draw_button(
                rect,
                label,
                active=(
                    action == "play" and self.playing
                ),
            )

        slower = pygame.Rect(x, 180, 105, 32)
        faster = pygame.Rect(x + 120, 180, 105, 32)

        self.button_rects["slower"] = slower
        self.button_rects["faster"] = faster

        self.draw_button(slower, "Speed -")
        self.draw_button(faster, "Speed +")

        self.draw_text(
            f"Playback speed: {self.speed} events/second",
            x + 245,
            188,
            MUTED,
            self.font_small,
        )

    def draw_statistics(self):
        x = PANEL_X

        self.draw_panel(
            pygame.Rect(x, 225, 730, 91)
        )

        if self.result is None:
            nodes = backtracks = 0
            event_total = 0
            status = "Not started"
        else:
            nodes = self.result.nodes_explored
            backtracks = self.result.backtracks
            event_total = len(self.events)

            if self.solved:
                status = "Solved"
            elif self.result.limit_reached:
                status = "Search limit reached"
            else:
                status = "Trace ready / running"

        self.draw_text(
            f"Status: {status}",
            x + 16,
            238,
            GREEN if self.solved else ORANGE,
            self.font_heading,
        )

        self.draw_text(
            f"Nodes: {nodes}",
            x + 16,
            274,
            TEXT,
            self.font_small,
        )

        self.draw_text(
            f"Backtracks: {backtracks}",
            x + 160,
            274,
            TEXT,
            self.font_small,
        )

        self.draw_text(
            f"Events: {self.event_index}/{event_total}",
            x + 330,
            274,
            TEXT,
            self.font_small,
        )

        self.draw_text(
            f"Time: {self.elapsed_seconds:.4f}s",
            x + 510,
            274,
            TEXT,
            self.font_small,
        )

    def draw_progress(self):
        x = PANEL_X
        y = 331
        width = 730
        height = 12

        pygame.draw.rect(
            self.screen,
            PANEL_LIGHT,
            (x, y, width, height),
            border_radius=6,
        )

        if self.events:
            ratio = self.event_index / len(self.events)
        else:
            ratio = 0.0

        pygame.draw.rect(
            self.screen,
            GREEN,
            (x, y, int(width * ratio), height),
            border_radius=6,
        )

    def draw_inspector(self):
        x = PANEL_X
        y = 365

        self.draw_panel(
            pygame.Rect(x, y, 730, 110)
        )

        row, col = self.selected_cell
        domain = sorted(self.domains.get(self.selected_cell, set()))

        self.draw_text(
            f"VARIABLE INSPECTOR - X[{row},{col}]",
            x + 15,
            y + 12,
            TEXT,
            self.font_heading,
        )

        self.draw_text(
            f"Current domain: {domain}",
            x + 15,
            y + 48,
            ACCENT,
            self.font_normal,
        )

        # Display the constraints containing this variable.
        related_runs = [
            run for run in self.puzzle.runs
            if self.selected_cell in run.cells
        ]

        descriptions = [
            f"{run.direction.value}: {run.target_sum}"
            for run in related_runs
        ]

        self.draw_text(
            " | ".join(descriptions),
            x + 15,
            y + 77,
            MUTED,
            self.font_small,
        )

    def draw_trace(self):
        x = PANEL_X
        y = 502

        self.draw_text(
            "SOLVER EVENT TRACE",
            x,
            y,
            TEXT,
            self.font_heading,
        )

        self.draw_panel(
            pygame.Rect(x, y + 35, 730, 285)
        )

        recent_events = self.history[-8:]

        if not recent_events:
            self.draw_text(
                "No events yet. Press Run Solver, then Step or Play.",
                x + 15,
                y + 55,
                MUTED,
                self.font_small,
            )
            return

        for index, event in enumerate(recent_events):
            line_y = y + 50 + index * 32

            color = {
                "domain_pruned": GREEN,
                "decision": ACCENT,
                "backtrack": RED,
                "contradiction": RED,
                "solution": ORANGE,
            }.get(event.event_type, MUTED)

            location = (
                f" [{event.cell[0]},{event.cell[1]}]"
                if event.cell is not None
                else ""
            )

            message = (
                f"{event.event_type.upper()}"
                f"{location}"
                f" | depth {event.depth}"
            )

            self.draw_text(
                message[:85],
                x + 15,
                line_y,
                color,
                self.font_mono,
            )

    def draw_status(self):
        x = BOARD_X
        y = BOARD_Y + self.puzzle.size * CELL_SIZE + 25

        self.draw_text(
            "Click a white cell to inspect its domain.",
            x,
            y,
            MUTED,
            self.font_small,
        )

        self.draw_text(
            self.status_message[:95],
            x,
            y + 27,
            ACCENT,
            self.font_small,
        )

        self.draw_text(
            "White cells: candidate digits | Black cells: across/down clues",
            x,
            y + 55,
            MUTED,
            self.font_small,
        )

    # -----------------------------------------------------
    # Main drawing
    # -----------------------------------------------------

    def draw(self):
        self.screen.fill(BACKGROUND)

        self.draw_text(
            "KAKURO CSP SOLVER",
            35,
            27,
            TEXT,
            self.font_title,
        )

        self.draw_text(
            "Constraint Propagation | MRV | Degree | LCV | Backtracking",
            38,
            65,
            MUTED,
            self.font_small,
        )

        self.button_rects.clear()

        self.draw_board()

        self.draw_controls()
        self.draw_statistics()
        self.draw_progress()
        self.draw_inspector()
        self.draw_trace()
        self.draw_status()

        pygame.display.flip()

    # -----------------------------------------------------
    # Mouse and keyboard events
    # -----------------------------------------------------

    def handle_button(self, action):
        if action == "run":
            self.start_solver()

        elif action == "step":
            self.step()

        elif action == "play":
            self.play()

        elif action == "pause":
            self.pause()

        elif action == "reset":
            self.reset()

        elif action == "slower":
            self.speed = max(1, self.speed - 2)

        elif action == "faster":
            self.speed = min(60, self.speed + 2)

        elif action == "reference":
            self.switch_puzzle("reference")

        elif action == "demo":
            self.switch_puzzle("demo")

    def handle_click(self, position):
        for action, rect in self.button_rects.items():
            if rect.collidepoint(position):
                self.handle_button(action)
                return

        mouse_x, mouse_y = position

        col = (mouse_x - BOARD_X) // CELL_SIZE + 1
        row = (mouse_y - BOARD_Y) // CELL_SIZE + 1

        if (
            1 <= row <= self.puzzle.size
            and 1 <= col <= self.puzzle.size
        ):
            cell = (row, col)

            if cell in self.puzzle.white_cells:
                self.selected_cell = cell

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    event.size,
                    pygame.RESIZABLE,
                )

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_click(event.pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.step()

                elif event.key == pygame.K_SPACE:
                    if self.playing:
                        self.pause()
                    else:
                        self.play()

                elif event.key == pygame.K_r:
                    self.reset()

    # -----------------------------------------------------
    # Main loop
    # -----------------------------------------------------

    def update(self, delta_time):
        if not self.playing:
            return

        self.playback_accumulator += delta_time

        interval = 1.0 / self.speed

        while self.playback_accumulator >= interval:
            self.playback_accumulator -= interval
            self.step()

            if not self.playing:
                break

    def run(self):
        while self.running:
            delta_time = self.clock.tick(60) / 1000.0

            self.handle_events()
            self.update(delta_time)
            self.draw()

        pygame.quit()


def main():
    app = KakuroApp()
    app.run()


if __name__ == "__main__":
    main()
