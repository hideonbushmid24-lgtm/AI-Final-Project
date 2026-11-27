"""PyGame graphical interface for Tank Battle."""

import pygame
from pathlib import Path

from ..constants import Action, PlayerId, Direction, GAME_WIDTH, GAME_HEIGHT
from ..game_engine import GameEngine
from ..scenario import create_default_scenario
from ..agents import (
    PluginLoader,
    PluginLoadError,
    create_search_agent,
    get_search_algorithm_names,
)

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 760
FPS = 60
CELL_SIZE = 44
BOARD_LEFT = 28
BOARD_TOP = 112
BOARD_WIDTH = GAME_WIDTH * CELL_SIZE
BOARD_HEIGHT = GAME_HEIGHT * CELL_SIZE
PANEL_LEFT = 630
PANEL_TOP = 90
PANEL_WIDTH = 440
PANEL_HEIGHT = 640
AI_DELAY_MS = 400

BACKGROUND = (16, 25, 34)
PANEL_BACKGROUND = (27, 39, 50)
BOARD_LIGHT = (42, 58, 67)
BOARD_DARK = (36, 51, 60)
GRID_COLOR = (63, 82, 91)
WHITE = (238, 243, 245)
MUTED = (160, 175, 184)
PLAYER_1_COLOR = (64, 160, 235)
PLAYER_2_COLOR = (235, 91, 91)
WALL_COLOR = (143, 124, 103)
BULLET_COLOR = (255, 205, 74)
BUTTON_COLOR = (51, 75, 91)
BUTTON_HOVER = (67, 104, 127)
BUTTON_DISABLED = (43, 52, 60)
SUCCESS_COLOR = (100, 205, 145)
WARNING_COLOR = (245, 190, 83)

MODES = ("Human vs Human", "Human vs AI", "AI vs AI")
DIRECTION_VECTORS = {
    Direction.UP: (0, -1),
    Direction.DOWN: (0, 1),
    Direction.LEFT: (-1, 0),
    Direction.RIGHT: (1, 0),
}


class TankBattleApp:
    """Main PyGame application."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tank Battle - AI Search Game")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont("segoeui", 28, bold=True)
        self.heading_font = pygame.font.SysFont("segoeui", 20, bold=True)
        self.font = pygame.font.SysFont("segoeui", 16)
        self.small_font = pygame.font.SysFont("segoeui", 13)

        self.engine = GameEngine()
        self.state = create_default_scenario()
        self.mode_index = 1
        self.algorithm_names = get_search_algorithm_names()
        self.algorithm_index = 0
        self.search_depth = 2
        self.auto_play = True
        self.paused = False
        self.running = True

        self.plugin_path = None
        self.plugin_class_name = None
        self.use_plugin = False
        self.ai_agents = {}

        self.buttons = []
        self.last_message = "Game ready. Player 1's turn."
        self.last_search_info = "No AI search performed yet."
        self.next_ai_time = pygame.time.get_ticks() + AI_DELAY_MS
        self._build_ai_agents()

    @property
    def current_mode(self):
        return MODES[self.mode_index]

    @property
    def current_algorithm(self):
        if self.use_plugin:
            return f"Plugin: {self.plugin_class_name}"
        return self.algorithm_names[self.algorithm_index]

    def _is_ai_player(self, player):
        if self.current_mode == "Human vs Human":
            return False
        if self.current_mode == "Human vs AI":
            return player == PlayerId.PLAYER_2
        return self.current_mode == "AI vs AI"

    def _build_ai_agents(self):
        self.ai_agents.clear()
        for player in (PlayerId.PLAYER_1, PlayerId.PLAYER_2):
            if not self._is_ai_player(player):
                continue
            if self.use_plugin:
                if not self.plugin_path or not self.plugin_class_name:
                    continue
                agent = PluginLoader.load_agent(
                    self.plugin_path, self.plugin_class_name
                )
            else:
                agent = create_search_agent(
                    algorithm=self.algorithm_names[self.algorithm_index],
                    depth=self.search_depth,
                )
            self.ai_agents[player] = agent

    def _apply_action(self, action, source="Human"):
        if self.state.is_terminal:
            self.last_message = "The game has already ended."
            return
        try:
            result = self.engine.apply_action(self.state, action)
            self.state = result.state
            messages = [event.message for event in result.events if event.message]
            detail = messages[-1] if messages else "Action completed."
            self.last_message = f"{source}: {Action(action).value}. {detail}"
            self.next_ai_time = pygame.time.get_ticks() + AI_DELAY_MS
            if self.state.is_terminal:
                if self.state.winner is None:
                    self.last_message = "Game over: Draw."
                else:
                    self.last_message = (
                        f"Game over: Player {self.state.winner.value} wins!"
                    )
        except Exception as exc:
            self.last_message = f"Game error: {exc}"

    def _run_ai_turn(self):
        if self.state.is_terminal or self.paused:
            return
        player = self.state.current_player
        if not self._is_ai_player(player):
            self.last_message = "It is a human player's turn."
            return
        agent = self.ai_agents.get(player)
        if agent is None:
            self.last_message = f"No AI agent configured for Player {player.value}."
            self.paused = True
            return
        try:
            action = agent.get_action(self.state)
            result = getattr(agent, "last_result", None)
            if result is not None:
                self.last_search_info = (
                    f"Algorithm: {result.algorithm} | Nodes: "
                    f"{result.nodes_explored} | Time: "
                    f"{result.elapsed_time_ms:.2f} ms"
                )
            else:
                self.last_search_info = f"Agent: {agent.name}"
            self._apply_action(action, source=agent.name)
        except Exception as exc:
            self.last_message = f"AI error: {exc}"
            self.paused = True

    def _reset_game(self):
        self.state = create_default_scenario()
        self.paused = False
        for agent in self.ai_agents.values():
            agent.reset()
        self.last_message = "New game started."
        self.last_search_info = "No AI search performed yet."
        self.next_ai_time = pygame.time.get_ticks() + AI_DELAY_MS

    def _change_mode(self):
        self.mode_index = (self.mode_index + 1) % len(MODES)
        self._build_ai_agents()
        self._reset_game()
        self.last_message = f"Mode changed to {self.current_mode}."

    def _change_algorithm(self):
        self.algorithm_index = (self.algorithm_index + 1) % len(self.algorithm_names)
        self.use_plugin = False
        self._build_ai_agents()
        self._reset_game()
        self.last_message = f"AI algorithm: {self.current_algorithm}."

    def _change_depth(self, delta):
        self.search_depth = max(1, min(3, self.search_depth + delta))
        self._build_ai_agents()
        self.last_message = f"Search depth changed to {self.search_depth}."

    def _load_plugin(self):
        """Select and load a trusted external Python agent."""
        try:
            import tkinter as tk
            from tkinter import filedialog, simpledialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            try:
                selected_file = filedialog.askopenfilename(
                    title="Select External Tank Battle Agent",
                    filetypes=[("Python files", "*.py")],
                )
                if not selected_file:
                    self.last_message = "Plugin selection cancelled."
                    return
                class_name = simpledialog.askstring(
                    "External Agent",
                    "Enter the agent class name:",
                    parent=root,
                )
            finally:
                root.destroy()

            if not class_name:
                self.last_message = "Plugin class name is required."
                return

            test_agent = PluginLoader.load_agent(selected_file, class_name)
            self.plugin_path = str(Path(selected_file).resolve())
            self.plugin_class_name = class_name
            self.use_plugin = True
            self._build_ai_agents()
            self._reset_game()
            self.last_message = f"Plugin loaded: {test_agent.name}"
        except PluginLoadError as exc:
            self.last_message = f"Plugin error: {exc}"
        except Exception as exc:
            self.last_message = f"Could not open plugin dialog: {exc}"

    def _clear_plugin(self):
        self.plugin_path = None
        self.plugin_class_name = None
        self.use_plugin = False
        self._build_ai_agents()
        self._reset_game()
        self.last_message = "External plugin cleared."

    def _handle_keydown(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
            return
        if key == pygame.K_p:
            self.paused = not self.paused
            return
        if key == pygame.K_r:
            self._reset_game()
            return
        if self.paused or self.state.is_terminal:
            return

        player = self.state.current_player
        if self._is_ai_player(player):
            return

        if player == PlayerId.PLAYER_1:
            controls = {
                pygame.K_w: Action.MOVE_UP,
                pygame.K_s: Action.MOVE_DOWN,
                pygame.K_a: Action.MOVE_LEFT,
                pygame.K_d: Action.MOVE_RIGHT,
                pygame.K_f: Action.FIRE,
                pygame.K_x: Action.STAY,
                pygame.K_SPACE: Action.FIRE,
            }
        else:
            controls = {
                pygame.K_UP: Action.MOVE_UP,
                pygame.K_DOWN: Action.MOVE_DOWN,
                pygame.K_LEFT: Action.MOVE_LEFT,
                pygame.K_RIGHT: Action.MOVE_RIGHT,
                pygame.K_RCTRL: Action.FIRE,
                pygame.K_RETURN: Action.STAY,
                pygame.K_KP_ENTER: Action.STAY,
            }
        action = controls.get(key)
        if action is not None:
            self._apply_action(action)

    def _draw_text(self, text, position, font=None, color=WHITE):
        font = font or self.font
        surface = font.render(str(text), True, color)
        self.screen.blit(surface, position)

    def _draw_centered_text(self, text, rect, font=None, color=WHITE):
        font = font or self.font
        surface = font.render(str(text), True, color)
        self.screen.blit(surface, surface.get_rect(center=rect.center))

    def _draw_button(self, rect, label, action, enabled=True):
        hovered = enabled and rect.collidepoint(pygame.mouse.get_pos())
        if not enabled:
            color = BUTTON_DISABLED
        elif hovered:
            color = BUTTON_HOVER
        else:
            color = BUTTON_COLOR
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(
            self.screen, (83, 105, 119), rect, width=1, border_radius=8
        )
        self._draw_centered_text(
            label, rect, self.font, WHITE if enabled else MUTED
        )
        self.buttons.append((rect, action, enabled))

    def _cell_center(self, position):
        return (
            BOARD_LEFT + position.x * CELL_SIZE + CELL_SIZE // 2,
            BOARD_TOP + position.y * CELL_SIZE + CELL_SIZE // 2,
        )

    def _draw_tank(self, player):
        tank = self.state.tanks[player]
        if not tank.is_alive:
            return
        color = PLAYER_1_COLOR if player == PlayerId.PLAYER_1 else PLAYER_2_COLOR
        center_x, center_y = self._cell_center(tank.position)
        pygame.draw.rect(
            self.screen,
            color,
            pygame.Rect(center_x - 15, center_y - 15, 30, 30),
            border_radius=7,
        )
        dx, dy = DIRECTION_VECTORS[tank.facing]
        pygame.draw.line(
            self.screen,
            WHITE,
            (center_x, center_y),
            (center_x + dx * 21, center_y + dy * 21),
            7,
        )
        pygame.draw.circle(self.screen, WHITE, (center_x, center_y), 6)
        label = self.small_font.render(f"P{player.value}", True, WHITE)
        self.screen.blit(label, label.get_rect(center=(center_x, center_y + 23)))

    def _draw_base(self, player):
        base = self.state.bases[player]
        if not base.is_alive:
            return
        color = PLAYER_1_COLOR if player == PlayerId.PLAYER_1 else PLAYER_2_COLOR
        center_x, center_y = self._cell_center(base.position)
        rect = pygame.Rect(center_x - 15, center_y - 15, 30, 30)
        pygame.draw.rect(self.screen, color, rect, border_radius=4)
        pygame.draw.rect(self.screen, WHITE, rect, width=2, border_radius=4)
        pygame.draw.line(
            self.screen, WHITE,
            (center_x - 7, center_y), (center_x + 7, center_y), 3
        )
        pygame.draw.line(
            self.screen, WHITE,
            (center_x, center_y - 7), (center_x, center_y + 7), 3
        )

    def _draw_board(self):
        board_rect = pygame.Rect(
            BOARD_LEFT, BOARD_TOP, BOARD_WIDTH, BOARD_HEIGHT
        )
        pygame.draw.rect(self.screen, BOARD_DARK, board_rect)

        for y in range(GAME_HEIGHT):
            for x in range(GAME_WIDTH):
                color = BOARD_LIGHT if (x + y) % 2 == 0 else BOARD_DARK
                cell = pygame.Rect(
                    BOARD_LEFT + x * CELL_SIZE,
                    BOARD_TOP + y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )
                pygame.draw.rect(self.screen, color, cell)
                pygame.draw.rect(self.screen, GRID_COLOR, cell, width=1)

        for position, wall in self.state.walls.items():
            rect = pygame.Rect(
                BOARD_LEFT + position.x * CELL_SIZE + 4,
                BOARD_TOP + position.y * CELL_SIZE + 4,
                CELL_SIZE - 8,
                CELL_SIZE - 8,
            )
            pygame.draw.rect(self.screen, WALL_COLOR, rect, border_radius=5)
            pygame.draw.rect(
                self.screen, (190, 171, 145), rect, width=2, border_radius=5
            )
            self._draw_centered_text(str(wall.hp), rect, self.small_font)

        self._draw_base(PlayerId.PLAYER_1)
        self._draw_base(PlayerId.PLAYER_2)
        self._draw_tank(PlayerId.PLAYER_1)
        self._draw_tank(PlayerId.PLAYER_2)

        for bullet in self.state.bullets:
            center = self._cell_center(bullet.position)
            pygame.draw.circle(self.screen, BULLET_COLOR, center, 6)
            pygame.draw.circle(self.screen, WHITE, center, 2)

        pygame.draw.rect(self.screen, WHITE, board_rect, width=2)

    def _draw_wrapped_text(self, text, x, y, max_width, font, color, max_lines=2):
        words = str(text).split()
        lines = []
        current_line = ""
        for word in words:
            candidate = f"{current_line} {word}".strip()
            if font.size(candidate)[0] <= max_width:
                current_line = candidate
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        for line in lines[:max_lines]:
            self._draw_text(line, (x, y), font, color)
            y += font.get_linesize() + 2

    def _draw_status_panel(self):
        pygame.draw.rect(
            self.screen,
            PANEL_BACKGROUND,
            pygame.Rect(PANEL_LEFT, PANEL_TOP, PANEL_WIDTH, PANEL_HEIGHT),
            border_radius=12,
        )
        self._draw_text(
            "GAME CONTROL", (PANEL_LEFT + 20, PANEL_TOP + 16), self.heading_font
        )

        self._draw_button(
            pygame.Rect(PANEL_LEFT + 20, PANEL_TOP + 56, 400, 40),
            f"MODE: {self.current_mode}", "mode"
        )
        self._draw_button(
            pygame.Rect(PANEL_LEFT + 20, PANEL_TOP + 106, 400, 40),
            f"AI: {self.current_algorithm}", "algorithm"
        )

        self._draw_text("Search depth:", (PANEL_LEFT + 20, PANEL_TOP + 169))
        self._draw_button(
            pygame.Rect(PANEL_LEFT + 170, PANEL_TOP + 157, 55, 36),
            "-", "depth_minus"
        )
        self._draw_button(
            pygame.Rect(PANEL_LEFT + 235, PANEL_TOP + 157, 65, 36),
            str(self.search_depth), "depth_display", enabled=False
        )
        self._draw_button(
            pygame.Rect(PANEL_LEFT + 310, PANEL_TOP + 157, 55, 36),
            "+", "depth_plus"
        )

        self._draw_button(
            pygame.Rect(PANEL_LEFT + 20, PANEL_TOP + 213, 190, 40),
            "AI STEP", "ai_step"
        )
        self._draw_button(
            pygame.Rect(PANEL_LEFT + 230, PANEL_TOP + 213, 190, 40),
            f"AUTO PLAY: {'ON' if self.auto_play else 'OFF'}", "auto"
        )
        self._draw_button(
            pygame.Rect(PANEL_LEFT + 20, PANEL_TOP + 263, 190, 40),
            "RESUME" if self.paused else "PAUSE", "pause"
        )
        self._draw_button(
            pygame.Rect(PANEL_LEFT + 230, PANEL_TOP + 263, 190, 40),
            "RESET GAME", "reset"
        )
        self._draw_button(
            pygame.Rect(PANEL_LEFT + 20, PANEL_TOP + 313, 190, 40),
            "LOAD PLUGIN", "plugin_load"
        )
        self._draw_button(
            pygame.Rect(PANEL_LEFT + 230, PANEL_TOP + 313, 190, 40),
            "CLEAR PLUGIN", "plugin_clear", enabled=self.plugin_path is not None
        )

        section_y = PANEL_TOP + 354
        self._draw_text(
            "GAME STATUS", (PANEL_LEFT + 20, section_y), self.heading_font
        )
        self._draw_text(
            f"Cycle: {self.state.cycle_number}",
            (PANEL_LEFT + 20, section_y + 31)
        )
        self._draw_text(
            f"Current player: Player {self.state.current_player.value}",
            (PANEL_LEFT + 20, section_y + 55)
        )
        self._draw_text(
            f"Tank 1 HP: {self.state.tanks[PlayerId.PLAYER_1].hp}",
            (PANEL_LEFT + 20, section_y + 82), color=PLAYER_1_COLOR
        )
        self._draw_text(
            f"Base 1 HP: {self.state.bases[PlayerId.PLAYER_1].hp}",
            (PANEL_LEFT + 225, section_y + 82), color=PLAYER_1_COLOR
        )
        self._draw_text(
            f"Tank 2 HP: {self.state.tanks[PlayerId.PLAYER_2].hp}",
            (PANEL_LEFT + 20, section_y + 108), color=PLAYER_2_COLOR
        )
        self._draw_text(
            f"Base 2 HP: {self.state.bases[PlayerId.PLAYER_2].hp}",
            (PANEL_LEFT + 225, section_y + 108), color=PLAYER_2_COLOR
        )
        self._draw_text(
            "LAST EVENT", (PANEL_LEFT + 20, section_y + 145), self.heading_font
        )
        self._draw_wrapped_text(
            self.last_message, PANEL_LEFT + 20, section_y + 171,
            PANEL_WIDTH - 40, self.small_font, MUTED, max_lines=2
        )
        self._draw_text(
            "AI SEARCH", (PANEL_LEFT + 20, section_y + 215), self.heading_font
        )
        self._draw_wrapped_text(
            self.last_search_info, PANEL_LEFT + 20, section_y + 241,
            PANEL_WIDTH - 40, self.small_font, SUCCESS_COLOR, max_lines=2
        )

    def _draw_interface(self):
        self.screen.fill(BACKGROUND)
        self._draw_text("TANK BATTLE", (28, 24), self.title_font)
        self._draw_text(
            "AI Adversarial Search Demonstration", (30, 65), self.small_font, MUTED
        )
        self._draw_text("GAME BOARD - 13 x 13", (BOARD_LEFT, 88), self.heading_font)
        self._draw_board()
        self.buttons = []
        self._draw_status_panel()

        self._draw_text(
            "P1: W A S D = Move | F / SPACE = Fire | X = Stay",
            (28, 700), self.small_font, MUTED
        )
        self._draw_text(
            "P2: Arrow Keys = Move | Right Ctrl = Fire | Enter = Stay",
            (28, 722), self.small_font, MUTED
        )

        if self.paused:
            overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 115))
            self.screen.blit(overlay, (BOARD_LEFT, BOARD_TOP))
            self._draw_centered_text(
                "PAUSED",
                pygame.Rect(BOARD_LEFT, BOARD_TOP, BOARD_WIDTH, BOARD_HEIGHT),
                self.title_font,
            )

        if self.state.is_terminal:
            result = (
                "DRAW" if self.state.winner is None
                else f"PLAYER {self.state.winner.value} WINS"
            )
            self._draw_centered_text(
                result,
                pygame.Rect(
                    BOARD_LEFT, BOARD_TOP + BOARD_HEIGHT // 2 - 30,
                    BOARD_WIDTH, 60
                ),
                self.title_font,
                WARNING_COLOR,
            )
        pygame.display.flip()

    def _handle_button(self, action):
        if action == "mode":
            self._change_mode()
        elif action == "algorithm":
            self._change_algorithm()
        elif action == "depth_minus":
            self._change_depth(-1)
        elif action == "depth_plus":
            self._change_depth(1)
        elif action == "ai_step":
            self._run_ai_turn()
        elif action == "auto":
            self.auto_play = not self.auto_play
            self.last_message = (
                "Automatic AI play enabled."
                if self.auto_play else "Automatic AI play disabled."
            )
        elif action == "pause":
            self.paused = not self.paused
        elif action == "reset":
            self._reset_game()
        elif action == "plugin_load":
            self._load_plugin()
        elif action == "plugin_clear":
            self._clear_plugin()

    def _handle_mouse_click(self, position):
        for rect, action, enabled in self.buttons:
            if enabled and rect.collidepoint(position):
                self._handle_button(action)
                return

    def run(self):
        """Run the PyGame event loop."""
        while self.running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_mouse_click(event.pos)

            if (
                self.auto_play
                and not self.paused
                and not self.state.is_terminal
                and self._is_ai_player(self.state.current_player)
                and pygame.time.get_ticks() >= self.next_ai_time
            ):
                self._run_ai_turn()

            self._draw_interface()
        pygame.quit()


def main():
    TankBattleApp().run()


if __name__ == "__main__":
    main()
