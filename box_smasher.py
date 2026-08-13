"""
Box Smasher — a Breakout-style game built with Pygame.

Smash the paddle to keep the ball alive, break every box to clear the level.

Controls:
    Left / Right arrows or A / D   — move paddle
    Space                          — launch the ball
    P                              — pause / unpause
    R                              — restart after game over / win
    Esc / close window             — quit

Setup:
    pip install pygame

Run:
    python box_smasher.py
"""

import sys
import random

import pygame

# ============================================================================
# Config
# ============================================================================
SCREEN_WIDTH = 720
SCREEN_HEIGHT = 640
TOP_BAR_HEIGHT = 60

PADDLE_WIDTH = 110
PADDLE_HEIGHT = 16
PADDLE_SPEED = 8
PADDLE_Y_OFFSET = 40  # distance from bottom of screen

BALL_RADIUS = 8
BALL_SPEED = 6

BOX_ROWS = 6
BOX_COLS = 9
BOX_PADDING = 6
BOX_TOP_MARGIN = TOP_BAR_HEIGHT + 30
BOX_SIDE_MARGIN = 20
BOX_HEIGHT = 26

LIVES_START = 3

COLOR_BG = (18, 18, 24)
COLOR_TEXT = (235, 235, 240)
COLOR_MUTED = (150, 150, 160)
COLOR_BAR_BG = (28, 28, 36)
COLOR_PADDLE = (98, 214, 122)
COLOR_BALL = (235, 235, 240)

# Row colors (top row = toughest/most points, bottom row = easiest)
ROW_COLORS = [
    (230, 90, 90),
    (230, 150, 90),
    (230, 210, 90),
    (150, 220, 100),
    (100, 190, 220),
    (150, 130, 230),
]
# Points per row, top row worth the most (matches ROW_COLORS order top->bottom)
ROW_POINTS = [60, 50, 40, 30, 20, 10]


class Paddle:
    def __init__(self):
        self.width = PADDLE_WIDTH
        self.rect = pygame.Rect(
            SCREEN_WIDTH // 2 - self.width // 2,
            SCREEN_HEIGHT - PADDLE_Y_OFFSET,
            self.width,
            PADDLE_HEIGHT,
        )

    def move(self, dx):
        self.rect.x += dx
        self.rect.x = max(0, min(SCREEN_WIDTH - self.rect.width, self.rect.x))

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_PADDLE, self.rect, border_radius=6)


class Ball:
    def __init__(self, paddle):
        self.radius = BALL_RADIUS
        self.reset(paddle)

    def reset(self, paddle):
        self.x = paddle.rect.centerx
        self.y = paddle.rect.top - self.radius - 1
        self.vx = 0
        self.vy = 0
        self.launched = False

    def launch(self):
        if not self.launched:
            # Launch up-ish, with a random horizontal nudge so it's not identical every time.
            self.vx = random.choice([-1, 1]) * BALL_SPEED * 0.5
            self.vy = -BALL_SPEED
            self.launched = True

    def follow_paddle(self, paddle):
        if not self.launched:
            self.x = paddle.rect.centerx
            self.y = paddle.rect.top - self.radius - 1

    def update(self):
        if self.launched:
            self.x += self.vx
            self.y += self.vy

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def draw(self, screen):
        pygame.draw.circle(screen, COLOR_BALL, (int(self.x), int(self.y)), self.radius)


class Box:
    def __init__(self, x, y, width, height, color, points):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.points = points
        self.alive = True

    def draw(self, screen):
        if self.alive:
            pygame.draw.rect(screen, self.color, self.rect, border_radius=4)
            pygame.draw.rect(screen, COLOR_BG, self.rect, width=1, border_radius=4)


class BoxSmasher:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Box Smasher")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.big_font = pygame.font.SysFont("consolas", 48, bold=True)

        self.high_score = 0
        self.reset()

    def reset(self):
        self.paddle = Paddle()
        self.ball = Ball(self.paddle)
        self.boxes = self.build_boxes()
        self.score = 0
        self.lives = LIVES_START
        self.paused = False
        self.game_over = False
        self.won = False

    def build_boxes(self):
        boxes = []
        usable_width = SCREEN_WIDTH - 2 * BOX_SIDE_MARGIN
        box_width = (usable_width - (BOX_COLS - 1) * BOX_PADDING) / BOX_COLS

        for row in range(BOX_ROWS):
            for col in range(BOX_COLS):
                x = BOX_SIDE_MARGIN + col * (box_width + BOX_PADDING)
                y = BOX_TOP_MARGIN + row * (BOX_HEIGHT + BOX_PADDING)
                color = ROW_COLORS[row % len(ROW_COLORS)]
                points = ROW_POINTS[row % len(ROW_POINTS)]
                boxes.append(Box(x, y, box_width, BOX_HEIGHT, color, points))
        return boxes

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                elif event.key == pygame.K_p and not self.game_over and not self.won:
                    self.paused = not self.paused
                elif event.key == pygame.K_r and (self.game_over or self.won):
                    self.reset()
                elif event.key == pygame.K_SPACE:
                    self.ball.launch()

        keys = pygame.key.get_pressed()
        if not self.paused and not self.game_over and not self.won:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.paddle.move(-PADDLE_SPEED)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.paddle.move(PADDLE_SPEED)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self):
        if self.paused or self.game_over or self.won:
            return

        self.ball.follow_paddle(self.paddle)
        self.ball.update()

        if not self.ball.launched:
            return

        # Wall collisions
        if self.ball.x - self.ball.radius <= 0:
            self.ball.x = self.ball.radius
            self.ball.vx *= -1
        elif self.ball.x + self.ball.radius >= SCREEN_WIDTH:
            self.ball.x = SCREEN_WIDTH - self.ball.radius
            self.ball.vx *= -1
        if self.ball.y - self.ball.radius <= TOP_BAR_HEIGHT:
            self.ball.y = TOP_BAR_HEIGHT + self.ball.radius
            self.ball.vy *= -1

        # Paddle collision
        ball_rect = self.ball.rect()
        if ball_rect.colliderect(self.paddle.rect) and self.ball.vy > 0:
            self.ball.y = self.paddle.rect.top - self.ball.radius
            # Bounce angle depends on where it hit the paddle (edge = sharper angle).
            offset = (self.ball.x - self.paddle.rect.centerx) / (self.paddle.rect.width / 2)
            offset = max(-1, min(1, offset))
            speed = (self.ball.vx ** 2 + self.ball.vy ** 2) ** 0.5
            self.ball.vx = offset * speed
            self.ball.vy = -abs(self.ball.vy)
            self._normalize_ball_speed()

        # Box collisions (only check one per frame to keep bounce logic simple/stable)
        for box in self.boxes:
            if box.alive and ball_rect.colliderect(box.rect):
                box.alive = False
                self.score += box.points
                self.high_score = max(self.high_score, self.score)

                # Decide bounce direction from overlap shape (cheap but effective).
                overlap_x = min(ball_rect.right, box.rect.right) - max(ball_rect.left, box.rect.left)
                overlap_y = min(ball_rect.bottom, box.rect.bottom) - max(ball_rect.top, box.rect.top)
                if overlap_x < overlap_y:
                    self.ball.vx *= -1
                else:
                    self.ball.vy *= -1
                break

        # Ball fell below paddle -> lose a life
        if self.ball.y - self.ball.radius > SCREEN_HEIGHT:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
            else:
                self.ball.reset(self.paddle)

        # Win condition
        if all(not box.alive for box in self.boxes):
            self.won = True

    def _normalize_ball_speed(self):
        # Keep overall speed roughly constant even after angled bounces.
        speed = (self.ball.vx ** 2 + self.ball.vy ** 2) ** 0.5
        if speed == 0:
            return
        scale = BALL_SPEED / speed
        self.ball.vx *= scale
        self.ball.vy *= scale

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def draw(self):
        self.screen.fill(COLOR_BG)
        for box in self.boxes:
            box.draw(self.screen)
        self.paddle.draw(self.screen)
        self.ball.draw(self.screen)
        self.draw_top_bar()

        if self.paused:
            self.draw_overlay("PAUSED", "Press P to resume")
        elif self.game_over:
            self.draw_overlay("GAME OVER", f"Score: {self.score}   |   Press R to restart")
        elif self.won:
            self.draw_overlay("YOU SMASHED IT!", f"Score: {self.score}   |   Press R to play again")
        elif not self.ball.launched:
            self.draw_hint("Press SPACE to launch")

        pygame.display.flip()

    def draw_top_bar(self):
        pygame.draw.rect(self.screen, COLOR_BAR_BG, (0, 0, SCREEN_WIDTH, TOP_BAR_HEIGHT))
        score_surf = self.font.render(f"Score: {self.score}", True, COLOR_TEXT)
        high_surf = self.font.render(f"Best: {self.high_score}", True, COLOR_MUTED)
        lives_surf = self.font.render(f"Lives: {self.lives}", True, COLOR_TEXT)
        self.screen.blit(score_surf, (16, 18))
        self.screen.blit(high_surf, (SCREEN_WIDTH // 2 - high_surf.get_width() // 2, 18))
        self.screen.blit(lives_surf, (SCREEN_WIDTH - lives_surf.get_width() - 16, 18))

    def draw_hint(self, text):
        surf = self.font.render(text, True, COLOR_MUTED)
        self.screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, SCREEN_HEIGHT - 90))

    def draw_overlay(self, title, subtitle):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        title_surf = self.big_font.render(title, True, COLOR_TEXT)
        sub_surf = self.font.render(subtitle, True, COLOR_MUTED)
        self.screen.blit(
            title_surf,
            (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 50),
        )
        self.screen.blit(
            sub_surf,
            (SCREEN_WIDTH // 2 - sub_surf.get_width() // 2, SCREEN_HEIGHT // 2 + 10),
        )

    # ------------------------------------------------------------------
    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(60)


if __name__ == "__main__":
    BoxSmasher().run()
