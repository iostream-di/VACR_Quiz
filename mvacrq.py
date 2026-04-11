# ---------------------------------------------------------
# VACR QUIZ — SILENT MODE ONLY
# by Marty Mayhem
# ---------------------------------------------------------

import pygame
import random
import sys
import time
import glob
import os

pygame.init()

# ---------------------------------------------------------
# FULLSCREEN SETUP
# ---------------------------------------------------------
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 120, 255)
RED = (200, 0, 0)

def rel_x(f): return int(SCREEN_WIDTH * f)
def rel_y(f): return int(SCREEN_HEIGHT * f)
def center_x(w): return (SCREEN_WIDTH - w) // 2
def center_y(h): return (SCREEN_HEIGHT - h) // 2

def scale_font(size):
    return int(size * (SCREEN_HEIGHT / 600))

FONT = pygame.font.SysFont("arial", scale_font(28))
BIG_FONT = pygame.font.SysFont("arial", scale_font(40))

pygame.display.set_caption("VACR QUIZ")

# ---------------------------------------------------------
# LOAD HOTLIST.TXT
# ---------------------------------------------------------
def load_hotlist():
    aircraft_categories = {}
    if not os.path.exists("hotlist.txt"):
        print("ERROR: hotlist.txt not found.")
        pygame.quit()
        sys.exit()

    with open("hotlist.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue

            name, category = line.split("|", 1)
            name = name.strip()
            category = category.strip().capitalize()  # case-insensitive normalization

            aircraft_categories[name] = category

    return aircraft_categories

aircraft_categories = load_hotlist()
aircraft_models = list(aircraft_categories.keys())

# ---------------------------------------------------------
# LOAD IMAGES
# ---------------------------------------------------------
extensions = ["png", "jpg", "jpeg", "webp", "bmp", "gif"]
aircraft_images = {}

for model in aircraft_models:
    safe = model.replace(" ", "_").replace("/", "_").lower()
    files = []
    for ext in extensions:
        files.extend(glob.glob(f"imgs/{safe}__*.{ext}"))
    files.sort()
    aircraft_images[model] = files

# ---------------------------------------------------------
# IMAGE SCALING (VACR LOGIC)
# ---------------------------------------------------------
def scale_vacr(img):
    sw, sh = SCREEN_WIDTH, SCREEN_HEIGHT
    w, h = img.get_size()

    if h > w:
        scale = sh / h
    else:
        scale = sw / w

    new_w = int(w * scale)
    new_h = int(h * scale)

    if new_w > sw:
        scale = sw / new_w
        new_w = int(new_w * scale)
        new_h = int(new_h * scale)

    if new_h > sh:
        scale = sh / new_h
        new_w = int(new_w * scale)
        new_h = int(new_h * scale)

    return pygame.transform.smoothscale(img, (new_w, new_h))

def load_image(path):
    try:
        img = pygame.image.load(path)
        return scale_vacr(img)
    except:
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        surf.fill(GRAY)
        text = FONT.render("no image, bro", True, BLACK)
        surf.blit(text, (center_x(text.get_width()), center_y(text.get_height())))
        return surf

# ---------------------------------------------------------
# QUIZ CLASS — SILENT MODE ONLY
# ---------------------------------------------------------
class Quiz:
    def __init__(self, num_questions=50, difficulty="Standard", num_choices=4):
        self.num_questions = num_questions
        self.difficulty = difficulty
        self.num_choices = num_choices

        if difficulty == "Easy":
            self.image_time = 10
            self.choice_time = 30
        elif difficulty == "Warfighter":
            self.image_time = 3
            self.choice_time = 4
        elif difficulty == "AI":
            self.image_time = 1
            self.choice_time = 3
        else:
            self.image_time = 5
            self.choice_time = 5

        self.questions = random.sample(aircraft_models, num_questions)
        self.index = 0
        self.score = 0
        self.wrong = 0

        self.selected_choice = None
        self.incorrect_log = []

        self.state = "show_image"
        self.image_start_time = None
        self.choice_start_time = None

        self.current_model = None
        self.current_image = None
        self.choices = []

        self.next_question()

    # -----------------------------------------------------
    def next_question(self):
        if self.index >= self.num_questions:
            self.state = "finished"
            return

        self.current_model = self.questions[self.index]
        img_path = random.choice(aircraft_images[self.current_model])
        self.current_image = load_image(img_path)

        category = aircraft_categories[self.current_model]
        same_cat = [m for m in aircraft_models if aircraft_categories[m] == category and m != self.current_model]

        wrong_needed = self.num_choices - 1

        if len(same_cat) >= wrong_needed:
            wrong = random.sample(same_cat, wrong_needed)
        else:
            wrong = same_cat + random.sample(
                [m for m in aircraft_models if aircraft_categories[m] != category],
                wrong_needed - len(same_cat)
            )

        self.choices = wrong + [self.current_model]
        random.shuffle(self.choices)

        self.selected_choice = None
        self.state = "show_image"
        self.image_start_time = time.time()

    # -----------------------------------------------------
    def update(self):
        now = time.time()

        if self.state == "show_image":
            if now - self.image_start_time >= self.image_time:
                self.state = "show_choices"
                self.choice_start_time = now

        elif self.state == "show_choices":
            if now - self.choice_start_time >= self.choice_time:
                final_choice = self.selected_choice if self.selected_choice else "TIMEOUT"

                if final_choice == self.current_model:
                    self.score += 1
                else:
                    self.wrong += 1
                    self.incorrect_log.append((self.current_model, final_choice))

                self.index += 1
                self.next_question()

    # -----------------------------------------------------
    def draw(self):
        screen.fill(WHITE)

        if self.state == "show_image":
            img = self.current_image
            screen.blit(img, (center_x(img.get_width()), center_y(img.get_height())))

        elif self.state == "show_choices":
            title = BIG_FONT.render("which one was it?", True, BLACK)
            screen.blit(title, (center_x(title.get_width()), rel_y(0.05)))

            btn_h = rel_y(0.07)
            btn_w = SCREEN_WIDTH * 0.5
            start_y = rel_y(0.2)
            gap = rel_y(0.02)

            for i, choice in enumerate(self.choices):
                y = start_y + i * (btn_h + gap)
                x = center_x(int(btn_w))
                rect = pygame.Rect(x, y, int(btn_w), int(btn_h))

                color = BLUE if self.selected_choice == choice else GRAY

                pygame.draw.rect(screen, color, rect, border_radius=8)
                label = FONT.render(choice, True, BLACK)
                screen.blit(label, (rect.x + (rect.width - label.get_width()) // 2,
                                    rect.y + (rect.height - label.get_height()) // 2))

        elif self.state == "finished":
            percent = (self.score / self.num_questions) * 100

            final = BIG_FONT.render(f"Score: {self.score}/{self.num_questions}  ({percent:.1f}%)", True, BLACK)
            screen.blit(final, (center_x(final.get_width()), rel_y(0.05)))
            
            if percent < 100:
                wrong_title = BIG_FONT.render("Incorrect Answers:", True, RED)
                screen.blit(wrong_title, (center_x(wrong_title.get_width()), rel_y(0.15)))
            else:
                wrong_title = BIG_FONT.render("Perfect Score!", True, BLACK)
                screen.blit(wrong_title, (center_x(wrong_title.get_width()), rel_y(0.15)))

            y = rel_y(0.25)
            for model, chosen in self.incorrect_log:
                correct = model
                text = FONT.render(f"{chosen}  →  {correct}", True, BLACK)
                screen.blit(text, (center_x(text.get_width()), y))
                y += text.get_height() + rel_y(0.01)

            btn_w = max(rel_x(0.22), 250)
            btn_h = max(rel_y(0.08), 60)

            play_btn = pygame.Rect(center_x(btn_w), rel_y(0.80), btn_w, btn_h)
            quit_btn = pygame.Rect(center_x(btn_w), rel_y(0.90), btn_w, btn_h)

            pygame.draw.rect(screen, BLUE, play_btn, border_radius=10)
            pygame.draw.rect(screen, RED, quit_btn, border_radius=10)

            play_label = FONT.render("main menu", True, WHITE)
            quit_label = FONT.render("quit", True, WHITE)

            screen.blit(play_label, (play_btn.centerx - play_label.get_width() // 2,
                                     play_btn.centery - play_label.get_height() // 2))

            screen.blit(quit_label, (quit_btn.centerx - quit_label.get_width() // 2,
                                     quit_btn.centery - quit_label.get_height() // 2))

            self.play_btn = play_btn
            self.quit_btn = quit_btn

        pygame.display.flip()

    # -----------------------------------------------------
    def handle_click(self, pos):
        if self.state == "show_choices":
            btn_h = rel_y(0.07)
            btn_w = SCREEN_WIDTH * 0.5
            start_y = rel_y(0.2)
            gap = rel_y(0.02)

            for i, choice in enumerate(self.choices):
                y = start_y + i * (btn_h + gap)
                x = center_x(int(btn_w))
                rect = pygame.Rect(x, y, int(btn_w), int(btn_h))

                if rect.collidepoint(pos):
                    self.selected_choice = choice

        elif self.state == "finished":
            if self.play_btn.collidepoint(pos):
                main()
            elif self.quit_btn.collidepoint(pos):
                pygame.quit()
                sys.exit()

# ---------------------------------------------------------
# START MENU
# ---------------------------------------------------------
def start_menu():
    selected = 50
    difficulties = ["Easy", "Standard", "Warfighter", "AI"]
    diff_index = 1
    num_choices = 4  # NEW

    while True:
        screen.fill(WHITE)

        y = rel_y(0.12)
        spacing = rel_y(0.06)

        title = BIG_FONT.render("Marty's Visual Aircraft Recognition Quiz", True, BLACK)
        screen.blit(title, (center_x(title.get_width()), y))
        y += title.get_height() + spacing

        prompt = FONT.render("how many aircraft?", True, BLACK)
        screen.blit(prompt, (center_x(prompt.get_width()), y))
        y += prompt.get_height() + spacing

        # Number of questions
        num_text = BIG_FONT.render(str(selected), True, BLUE)
        btn_size = max(rel_y(0.06), 40)
        gap = rel_x(0.015)

        row_w = btn_size + gap + num_text.get_width() + gap + btn_size
        row_x = center_x(row_w)

        minus_rect = pygame.Rect(row_x, y, btn_size, btn_size)
        plus_rect = pygame.Rect(row_x + btn_size + gap + num_text.get_width() + gap, y, btn_size, btn_size)

        pygame.draw.rect(screen, GRAY, minus_rect, border_radius=8)
        pygame.draw.rect(screen, GRAY, plus_rect, border_radius=8)

        screen.blit(num_text, (row_x + btn_size + gap, y + (btn_size - num_text.get_height()) // 2))

        minus_label = BIG_FONT.render("-", True, BLACK)
        plus_label = BIG_FONT.render("+", True, BLACK)

        screen.blit(minus_label, (minus_rect.centerx - minus_label.get_width() // 2,
                                  minus_rect.centery - minus_label.get_height() // 2))
        screen.blit(plus_label, (plus_rect.centerx - plus_label.get_width() // 2,
                                 plus_rect.centery - plus_label.get_height() // 2))

        y += btn_size + spacing

        # Difficulty selector
        diff_text = BIG_FONT.render(difficulties[diff_index], True, BLUE)
        arrow_size = btn_size
        row_w = arrow_size + gap + diff_text.get_width() + gap + arrow_size
        row_x = center_x(row_w)

        diff_left = pygame.Rect(row_x, y, arrow_size, arrow_size)
        diff_right = pygame.Rect(row_x + arrow_size + gap + diff_text.get_width() + gap, y, arrow_size, arrow_size)

        pygame.draw.rect(screen, GRAY, diff_left, border_radius=8)
        pygame.draw.rect(screen, GRAY, diff_right, border_radius=8)

        left_arrow = BIG_FONT.render("<", True, BLACK)
        right_arrow = BIG_FONT.render(">", True, BLACK)

        screen.blit(left_arrow, (diff_left.centerx - left_arrow.get_width() // 2,
                                 diff_left.centery - left_arrow.get_height() // 2))
        screen.blit(right_arrow, (diff_right.centerx - right_arrow.get_width() // 2,
                                  diff_right.centery - right_arrow.get_height() // 2))

        screen.blit(diff_text, (row_x + arrow_size + gap,
                                y + (arrow_size - diff_text.get_height()) // 2))

        y += arrow_size + spacing

        # -------------------------------------------------
        # NEW: Number of choices selector (4–6)
        # -------------------------------------------------
        choice_label = FONT.render("number of choices:", True, BLACK)
        screen.blit(choice_label, (center_x(choice_label.get_width()), y))
        y += choice_label.get_height() + rel_y(0.02)

        choice_text = BIG_FONT.render(str(num_choices), True, BLUE)
        row_w = arrow_size + gap + choice_text.get_width() + gap + arrow_size
        row_x = center_x(row_w)

        choice_left = pygame.Rect(row_x, y, arrow_size, arrow_size)
        choice_right = pygame.Rect(row_x + arrow_size + gap + choice_text.get_width() + gap, y, arrow_size, arrow_size)

        pygame.draw.rect(screen, GRAY, choice_left, border_radius=8)
        pygame.draw.rect(screen, GRAY, choice_right, border_radius=8)

        screen.blit(left_arrow, (choice_left.centerx - left_arrow.get_width() // 2,
                                 choice_left.centery - left_arrow.get_height() // 2))
        screen.blit(right_arrow, (choice_right.centerx - right_arrow.get_width() // 2,
                                  choice_right.centery - right_arrow.get_height() // 2))

        screen.blit(choice_text, (row_x + arrow_size + gap,
                                  y + (arrow_size - choice_text.get_height()) // 2))

        y += arrow_size + spacing * 1.5

        # Start button
        start_w = max(rel_x(0.22), 250)
        start_h = max(rel_y(0.08), 60)
        start_btn = pygame.Rect(center_x(start_w), y, start_w, start_h)

        pygame.draw.rect(screen, BLUE, start_btn, border_radius=10)
        start_label = FONT.render("send it!", True, WHITE)
        screen.blit(start_label, (start_btn.centerx - start_label.get_width() // 2,
                                  start_btn.centery - start_label.get_height() // 2))

        pygame.display.flip()

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if minus_rect.collidepoint(event.pos):
                    selected = max(1, selected - 1)
                elif plus_rect.collidepoint(event.pos):
                    selected = min(50, selected + 1)
                elif diff_left.collidepoint(event.pos):
                    diff_index = (diff_index - 1) % len(difficulties)
                elif diff_right.collidepoint(event.pos):
                    diff_index = (diff_index + 1) % len(difficulties)
                elif choice_left.collidepoint(event.pos):
                    num_choices = max(4, num_choices - 1)
                elif choice_right.collidepoint(event.pos):
                    num_choices = min(6, num_choices + 1)
                elif start_btn.collidepoint(event.pos):
                    return selected, difficulties[diff_index], num_choices

# ---------------------------------------------------------
# MAIN LOOP WRAPPER
# ---------------------------------------------------------
def main():
    num_q, difficulty, num_choices = start_menu()
    quiz = Quiz(num_questions=num_q, difficulty=difficulty, num_choices=num_choices)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                quiz.handle_click(event.pos)

        quiz.update()
        quiz.draw()
        clock.tick(60)

# ---------------------------------------------------------
# START PROGRAM
# ---------------------------------------------------------
main()
