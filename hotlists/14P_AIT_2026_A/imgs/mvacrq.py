#------------------------------
# VACR Quiz script v1.1 (by Marty Mayhem (dmartinez61789@gmail.com)
#------------------------------

import libs/pygame
import random
import sys
import time

pygame.init()

# -----------------------------
# FULLSCREEN & CONFIG
# -----------------------------
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 120, 255)

# helpers for relative positioning
def rel_x(f):
    return int(SCREEN_WIDTH * f)

def rel_y(f):
    return int(SCREEN_HEIGHT * f)

def center_x(width):
    return (SCREEN_WIDTH - width) // 2

def center_y(height):
    return (SCREEN_HEIGHT - height) // 2

# fonts scale with height (base 600)
def scale_font(size):
    return int(size * (SCREEN_HEIGHT / 600))

FONT = pygame.font.SysFont("arial", scale_font(28))
BIG_FONT = pygame.font.SysFont("arial", scale_font(40))

pygame.display.set_caption("VACR Quiz")

# -----------------------------
# AIRCRAFT CATEGORIES
# -----------------------------
aircraft_categories = {
    # Fighters
    "F-14 Tomcat": "Fighter",
    "F-15 Eagle": "Fighter",
    "F-22 Raptor": "Fighter",
    "F-35 Lightning": "Fighter",
    "A/V-8 Harrier": "Fighter",
    "A-10 Thunderbolt": "Fighter",
    "F-16 Fighting Falcon": "Fighter",
    "F/A-18 Hornet": "Fighter",
    "JAS-39 Gripen": "Fighter",
    "MIG-31 Foxhound": "Fighter",
    "Rafale": "Fighter",
    "MIG-29 Fulcrum": "Fighter",
    "SU-27 Flanker": "Fighter",
    "Alpha Jet": "Fighter",
    "F-7P Airguard": "Fighter",
    "J-10 Anihilator": "Fighter",
    "JF-17 Thunder": "Fighter",

    # Transports
    "C-160 Transall": "Transport",
    "C-130 Hercules": "Transport",
    "C-17 Globemaster": "Transport",
    "C-5 Galaxy": "Transport",
    "AN-12 Cub": "Transport",
    "C-23 Sherpa": "Transport",
    "AN-2 Colt": "Transport",

    # Helicopters
    "UH-60 Blackhawk": "Helicopter",
    "MD-500 Defender": "Helicopter",
    "CH-53 Sea Stallion": "Helicopter",
    "CH-47 Chinook": "Helicopter",
    "AH-64 Apache": "Helicopter",
    "AH-1 Cobra": "Helicopter",
    "MV-22 Osprey": "Helicopter",
    "A129 Mangusta": "Helicopter",
    "MI-26 Halo": "Helicopter",
    "NH-90": "Helicopter",
    "SA-330 Puma": "Helicopter",
    "PAH-2 Tiger": "Helicopter",
    "MI-28 Havoc": "Helicopter",
    "MI-24 Hind": "Helicopter",
    "MI-8 Hip": "Helicopter",
    "MI-2 Hoplite": "Helicopter",
    "WG-13 Lynx": "Helicopter",
    "KA-50 Hokum": "Helicopter",
    "Harbin Z-9": "Helicopter",

    # UAVs
    "Mirach 100 Meteor": "UAV",
    "MQ-5B Hunter": "UAV",
    "RQ-2 Pioneer": "UAV",
    "RQ-7B Shadow": "UAV",
    "MQ-9 Reaper": "UAV",
    "MQ-8 Fire Scout": "UAV",
    "Schmel-1 Yak-061": "UAV"
}

# -----------------------------
# QUIZ DATA
# -----------------------------
aircraft_models = list(aircraft_categories.keys())

aircraft_images = {}
for model in aircraft_models:
    safe = model.replace(' ', '_').replace('/', '_').lower()
    aircraft_images[model] = [
        f"{safe}__a.png",
        f"{safe}__b.png",
        f"{safe}__c.png"
    ]

# -----------------------------
# IMAGE HELPERS
# -----------------------------
def scale_preserve_aspect(img, max_width, max_height):
    w, h = img.get_size()
    ratio = min(max_width / w, max_height / h)
    new_size = (int(w * ratio), int(h * ratio))
    return pygame.transform.smoothscale(img, new_size)

def load_image(path):
    try:
        img = pygame.image.load(path)
        max_w = SCREEN_WIDTH * 0.7
        max_h = SCREEN_HEIGHT * 0.6
        return scale_preserve_aspect(img, max_w, max_h)
    except:
        max_w = int(SCREEN_WIDTH * 0.7)
        max_h = int(SCREEN_HEIGHT * 0.6)
        surf = pygame.Surface((max_w, max_h))
        surf.fill(GRAY)
        text = FONT.render("no image, bro", True, BLACK)
        surf.blit(text, (max_w // 2 - text.get_width() // 2,
                         max_h // 2 - text.get_height() // 2))
        return surf

# -----------------------------
# QUIZ CLASS
# -----------------------------
class Quiz:
    def __init__(self, num_questions=50, difficulty="Standard"):
        self.num_questions = min(max(1, num_questions), 50)
        self.difficulty = difficulty
        self.points = 0

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

        self.questions = random.sample(aircraft_models, self.num_questions)
        self.index = 0
        self.score = 0
        self.wrong = 0
        self.state = "show_image"

        self.current_model = None
        self.current_image = None
        self.choices = []
        self.correct_answer = None
        self.result_text = ""
        self.image_start_time = None
        self.choice_start_time = None

        self.next_question()

    def next_question(self):
        if self.index >= self.num_questions:
            self.state = "finished"
            return

        self.current_model = self.questions[self.index]
        self.correct_answer = self.current_model

        img_path = random.choice(aircraft_images[self.current_model])
        self.current_image = load_image(img_path)

        category = aircraft_categories[self.correct_answer]
        same_category = [
            m for m in aircraft_models
            if aircraft_categories[m] == category and m != self.correct_answer
        ]

        if len(same_category) >= 5:
            wrong_choices = random.sample(same_category, 5)
        else:
            wrong_choices = same_category + random.sample(
                [m for m in aircraft_models if aircraft_categories[m] != category],
                5 - len(same_category)
            )

        self.choices = wrong_choices + [self.correct_answer]
        random.shuffle(self.choices)

        self.state = "show_image"
        self.image_start_time = time.time()
        self.choice_start_time = None

    def update(self):
        if self.state == "show_image":
            if time.time() - self.image_start_time >= self.image_time:
                self.state = "show_choices"
                self.choice_start_time = time.time()

        elif self.state == "show_choices":
            if time.time() - self.choice_start_time >= self.choice_time:
                self.check_answer("TIMEOUT")

    def check_answer(self, choice):
        if choice == self.correct_answer:
            self.score += 1
            if self.difficulty == "Easy":
                self.points += 5
            elif self.difficulty == "Standard":
                self.points += 10
            elif self.difficulty == "Warfighter":
                self.points += 12
            elif self.difficulty == "AI":
                self.points += 14
            self.result_text = random.choice(["yup.", "got it.", "nailed it.", "bingo.", "good.", "awesome.", "hell yea.", "sweet.", "dope.", "yeeea booyy."])
        else:
            self.wrong += 1
            if choice == "TIMEOUT":
                self.result_text = f"too slow, bro. {self.correct_answer}"
            elif self.wrong == 3:
                self.result_text = f"bro, lock in. {self.correct_answer}"
            elif self.wrong == 4:
                self.result_text = f"seriously bro? {self.correct_answer}"
            elif self.wrong == 5:
                self.result_text = f"wtf bro. {self.correct_answer}"
            elif self.wrong > 5:
                self.result_text = f"you gunna fail, bro. {self.correct_answer}"
            else:
                self.result_text = f"nope. {self.correct_answer}"

        self.state = "show_result"

    def draw(self):
        screen.fill(WHITE)

        if self.state == "show_image":
            img = self.current_image
            if img:
                x = center_x(img.get_width())
                y = rel_y(0.15)
                screen.blit(img, (x, y))

        elif self.state == "show_choices":
            title_text = BIG_FONT.render("which one was it?", True, BLACK)
            screen.blit(title_text, (center_x(title_text.get_width()), rel_y(0.05)))

            btn_height = rel_y(0.07)
            btn_width = SCREEN_WIDTH * 0.5
            start_y = rel_y(0.2)
            gap = rel_y(0.02)

            for i, choice in enumerate(self.choices):
                y = start_y + i * (btn_height + gap)
                x = center_x(int(btn_width))
                rect = pygame.Rect(x, y, int(btn_width), int(btn_height))
                pygame.draw.rect(screen, GRAY, rect, border_radius=8)
                label = FONT.render(choice, True, BLACK)
                screen.blit(label, (rect.x + (rect.width - label.get_width()) // 2,
                                    rect.y + (rect.height - label.get_height()) // 2))

        elif self.state == "show_result":
            result = BIG_FONT.render(self.result_text, True, BLACK)
            screen.blit(result, (center_x(result.get_width()), rel_y(0.3)))

            btn_width = SCREEN_WIDTH * 0.2
            btn_height = rel_y(0.08)
            next_btn = pygame.Rect(center_x(int(btn_width)), rel_y(0.5),
                                   int(btn_width), int(btn_height))
            pygame.draw.rect(screen, GRAY, next_btn, border_radius=8)
            next_text = FONT.render("Next", True, BLACK)
            screen.blit(next_text, (next_btn.x + (next_btn.width - next_text.get_width()) // 2,
                                    next_btn.y + (next_btn.height - next_text.get_height()) // 2))

        elif self.state == "finished":
            percent = (self.score / self.num_questions) * 100

            # Final message
            if percent < 80.0:
                final = BIG_FONT.render("you suck, bro.", True, BLACK)
            else:
                if percent == 100.0:
                    final = BIG_FONT.render("you crushed it, bro.", True, BLACK)
                elif percent > 90.0:
                    final = BIG_FONT.render("not bad, bro.", True, BLACK)
                else:
                    final = BIG_FONT.render("barely passed, bro.", True, BLACK)

            points_text = FONT.render(f"Points: {self.points}", True, BLACK)
            score_text = FONT.render(f"Score: {self.score} / {self.num_questions}", True, BLACK)
            percent_text = FONT.render(f"Percentage: {percent:.1f}%", True, BLACK)

            screen.blit(final, (center_x(final.get_width()), rel_y(0.25)))
            screen.blit(points_text, (center_x(points_text.get_width()), rel_y(0.10)))
            screen.blit(score_text, (center_x(score_text.get_width()), rel_y(0.35)))
            screen.blit(percent_text, (center_x(percent_text.get_width()), rel_y(0.42)))

            # --- Buttons ---
            btn_w = max(rel_x(0.22), 250)
            btn_h = max(rel_y(0.08), 60)

            play_btn = pygame.Rect(center_x(btn_w), rel_y(0.55), btn_w, btn_h)
            quit_btn = pygame.Rect(center_x(btn_w), rel_y(0.70), btn_w, btn_h)

            pygame.draw.rect(screen, BLUE, play_btn, border_radius=10)
            pygame.draw.rect(screen, RED, quit_btn, border_radius=10)

            play_label = FONT.render("recock, bro", True, WHITE)
            quit_label = FONT.render("no more, bro", True, WHITE)

            screen.blit(play_label, (play_btn.centerx - play_label.get_width() // 2,
                                     play_btn.centery - play_label.get_height() // 2))

            screen.blit(quit_label, (quit_btn.centerx - quit_label.get_width() // 2,
                                     quit_btn.centery - quit_label.get_height() // 2))

            # Save rects for click detection
            self.play_btn = play_btn
            self.quit_btn = quit_btn

        pygame.display.flip()

    def handle_click(self, pos):
        if self.state == "show_choices":
            btn_height = rel_y(0.07)
            btn_width = SCREEN_WIDTH * 0.5
            start_y = rel_y(0.2)
            gap = rel_y(0.02)

            for i, choice in enumerate(self.choices):
                y = start_y + i * (btn_height + gap)
                x = center_x(int(btn_width))
                rect = pygame.Rect(x, y, int(btn_width), int(btn_height))
                if rect.collidepoint(pos):
                    self.check_answer(choice)

        elif self.state == "show_result":
            btn_width = SCREEN_WIDTH * 0.2
            btn_height = rel_y(0.08)
            next_btn = pygame.Rect(center_x(int(btn_width)), rel_y(0.5),
                                   int(btn_width), int(btn_height))
            if next_btn.collidepoint(pos):
                self.index += 1
                self.next_question()
                
        elif self.state == "finished":
            if self.play_btn.collidepoint(pos):
                # Restart the quiz
                self.index = 0
                self.score = 0
                self.wrong = 0
                self.points = 0
                self.questions = random.sample(aircraft_models, self.num_questions)
                self.next_question()

            elif self.quit_btn.collidepoint(pos):
                pygame.quit()
                sys.exit()


# -----------------------------
# START MENU
# -----------------------------
def start_menu():
    selected = 50
    difficulties = ["Easy", "Standard", "Warfighter", "AI"]
    diff_index = 1

    running = True
    while running:
        screen.fill(WHITE)

        # Vertical layout anchor
        y = rel_y(0.12)
        spacing = rel_y(0.06)

        # --- Title ---
        title = BIG_FONT.render("Marty's Visual Aircraft Recognition Quiz", True, BLACK)
        screen.blit(title, (center_x(title.get_width()), y))
        y += title.get_height() + spacing

        # --- Prompt ---
        prompt = FONT.render("how many of these shits you wanna try?", True, BLACK)
        screen.blit(prompt, (center_x(prompt.get_width()), y))
        y += prompt.get_height() + spacing

        # --- Number Selector ---
        num_text = BIG_FONT.render(str(selected), True, BLUE)

        btn_size = max(rel_y(0.06), 40)  # never let buttons get too small
        gap = rel_x(0.015)

        row_width = btn_size + gap + num_text.get_width() + gap + btn_size
        row_x = center_x(row_width)

        minus_rect = pygame.Rect(row_x, y, btn_size, btn_size)
        num_x = row_x + btn_size + gap
        plus_rect = pygame.Rect(num_x + num_text.get_width() + gap, y, btn_size, btn_size)

        pygame.draw.rect(screen, GRAY, minus_rect, border_radius=8)
        pygame.draw.rect(screen, GRAY, plus_rect, border_radius=8)

        screen.blit(num_text, (num_x, y + (btn_size - num_text.get_height()) // 2))

        minus_label = BIG_FONT.render("-", True, BLACK)
        plus_label = BIG_FONT.render("+", True, BLACK)

        screen.blit(minus_label, (minus_rect.centerx - minus_label.get_width() // 2,
                                  minus_rect.centery - minus_label.get_height() // 2))
        screen.blit(plus_label, (plus_rect.centerx - plus_label.get_width() // 2,
                                 plus_rect.centery - plus_label.get_height() // 2))

        y += btn_size + spacing

        # --- Difficulty Selector ---
        diff_text = BIG_FONT.render(difficulties[diff_index], True, BLUE)

        arrow_size = btn_size
        row_width = arrow_size + gap + diff_text.get_width() + gap + arrow_size
        row_x = center_x(row_width)

        diff_left = pygame.Rect(row_x, y, arrow_size, arrow_size)
        diff_label_x = row_x + arrow_size + gap
        diff_right = pygame.Rect(diff_label_x + diff_text.get_width() + gap, y, arrow_size, arrow_size)

        pygame.draw.rect(screen, GRAY, diff_left, border_radius=8)
        pygame.draw.rect(screen, GRAY, diff_right, border_radius=8)

        left_arrow = BIG_FONT.render("<", True, BLACK)
        right_arrow = BIG_FONT.render(">", True, BLACK)

        screen.blit(left_arrow, (diff_left.centerx - left_arrow.get_width() // 2,
                                 diff_left.centery - left_arrow.get_height() // 2))
        screen.blit(right_arrow, (diff_right.centerx - right_arrow.get_width() // 2,
                                  diff_right.centery - right_arrow.get_height() // 2))

        screen.blit(diff_text, (diff_label_x, y + (arrow_size - diff_text.get_height()) // 2))

        y += arrow_size + spacing * 1.5

        # --- Start Button ---
        start_w = max(rel_x(0.22), 250)
        start_h = max(rel_y(0.08), 60)
        start_btn = pygame.Rect(center_x(start_w), y, start_w, start_h)

        pygame.draw.rect(screen, BLUE, start_btn, border_radius=10)
        start_label = FONT.render("send it!", True, WHITE)
        screen.blit(start_label, (start_btn.centerx - start_label.get_width() // 2,
                                  start_btn.centery - start_label.get_height() // 2))

        pygame.display.flip()

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
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
                elif start_btn.collidepoint(event.pos):
                    return selected, difficulties[diff_index]


# -----------------------------
# MAIN LOOP
# -----------------------------
num_q, difficulty = start_menu()
quiz = Quiz(num_questions=num_q, difficulty=difficulty)
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            quiz.handle_click(event.pos)

    quiz.update()
    quiz.draw()
    clock.tick(60)

