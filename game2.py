import pygame
import os
import math
import random

pygame.init()
pygame.mixer.init()

# WINDOW
pygame.display.set_caption("Ali's Transcendental Adventure")
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
clear_color = (30, 150, 30)

WIDTH, HEIGHT = 800, 600
sprite_folder = "/Users/h/projectspy/rpg/sprite"

# ---------------- AUDIO ----------------
SONG_PARTS = [
    pygame.mixer.Sound(os.path.join(sprite_folder, f"song_part_{i}.wav"))
    for i in range(1, 11)
]
FULL_SONG = pygame.mixer.Sound(os.path.join(sprite_folder, "full_song.wav"))

for s in SONG_PARTS:
    s.set_volume(0.7)
FULL_SONG.set_volume(0.85)

# SPRITE LOADER
def load_sprite(name, size):
    for ext in (".png", ".jpg", ".jpeg"):
        path = os.path.join(sprite_folder, name + ext)
        if os.path.exists(path):
            return pygame.transform.scale(
                pygame.image.load(path).convert_alpha(), size
            )
    raise SystemExit(f"Missing sprite: {name}")

# FONTS
font = pygame.font.SysFont(None, 40)
small_font = pygame.font.SysFont(None, 28)

# YOU WIN TEXT (ONLY ADDED)
win_text = pygame.font.SysFont(None, 96).render("YOU WIN", True, (255, 255, 0))
win_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

# PLAYER
right_image = load_sprite("right1", (64, 100))
left_image  = load_sprite("left1", (64, 100))
player_image = right_image
player_rect = player_image.get_rect(center=(400, 300))
speed = 5

# BULLET
base_bullet_image = load_sprite("bullet", (50, 50))
bullets = []
bullet_speed = 12

# COOLDOWN
cooldown_time = 3000
last_shot_time = -cooldown_time

# BOAR
boar_right = load_sprite("bright", (80, 60))
boar_left  = load_sprite("bleft", (80, 60))
boar_image = boar_right
boar_speed = 2
boar_max_hp = 200
boar_hp = 200
boar_alive = True
knockback_strength = 20

# BOAR RESPAWN
boar_death_time = None
BOAR_RESPAWN_DELAY = 5000

# DASH SETTINGS
DASH_COOLDOWN = 2000
DASH_DURATION = 200
DASH_SPEED = 14
last_dash_time = 0
dash_start_time = 0
is_dashing = False
dash_dir = (0, 0)
DASH_DISTANCE = DASH_SPEED * (DASH_DURATION / (1000 / 60))

def spawn_boar():
    side = random.choice(["top", "bottom", "left", "right"])
    if side == "top":
        return pygame.Rect(random.randint(0, WIDTH), -60, 80, 60)
    if side == "bottom":
        return pygame.Rect(random.randint(0, WIDTH), HEIGHT + 60, 80, 60)
    if side == "left":
        return pygame.Rect(-80, random.randint(0, HEIGHT), 80, 60)
    return pygame.Rect(WIDTH + 80, random.randint(0, HEIGHT), 80, 60)

boar_rect = spawn_boar()

# SOULS
soul_image = load_sprite("soul", (50, 50))
soul_rect = None
souls_collected = 0
gui_soul_image = pygame.transform.scale(soul_image, (48, 48))

# TREE (SHOP)
tree_image = load_sprite("tree", (110, 110))
tree_rect = tree_image.get_rect(topright=(WIDTH - 30, 10))
tree_text = small_font.render("Mother Nature", True, (255, 255, 255))
tree_text_rect = tree_text.get_rect(midtop=(tree_rect.centerx, tree_rect.bottom + 4))

# SHOP / MEMORY
lightbulb_image = load_sprite("lightbulb", (52, 52))
memories = 0
MAX_MEMORIES = 10
MEMORY_PRICE = 2

shop_panel = pygame.Rect(220, 170, 360, 260)
buy_button = pygame.Rect(360, 330, 120, 40)

# GAME LOOP
running = True
while running:
    clock.tick(60)
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            # BUY MEMORY (AUDIO ADDED HERE)
            if player_rect.colliderect(tree_rect):
                if (
                    buy_button.collidepoint(event.pos)
                    and souls_collected >= MEMORY_PRICE
                    and memories < MAX_MEMORIES
                ):
                    souls_collected -= MEMORY_PRICE

                    SONG_PARTS[memories].play()
                    memories += 1

                    if memories == MAX_MEMORIES:
                        pygame.mixer.stop()
                        FULL_SONG.play()

            # SHOOT
            else:
                if current_time - last_shot_time >= cooldown_time:
                    mx, my = pygame.mouse.get_pos()
                    px, py = player_rect.center
                    dx, dy = mx - px, my - py
                    dist = math.hypot(dx, dy)
                    if dist != 0:
                        dx /= dist
                        dy /= dist
                        angle = math.degrees(math.atan2(-dy, dx))
                        rotated = pygame.transform.rotate(base_bullet_image, angle)
                        bullets.append(
                            [rotated.get_rect(center=(px, py)), dx, dy, rotated]
                        )
                        last_shot_time = current_time

    # PLAYER MOVE
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]: player_rect.y -= speed
    if keys[pygame.K_s]: player_rect.y += speed
    if keys[pygame.K_a]:
        player_rect.x -= speed
        player_image = left_image
    if keys[pygame.K_d]:
        player_rect.x += speed
        player_image = right_image

    # BULLETS
    for bullet in bullets[:]:
        bullet[0].x += bullet[1] * bullet_speed
        bullet[0].y += bullet[2] * bullet_speed

        if boar_alive and bullet[0].colliderect(boar_rect):
            boar_hp -= 100
            boar_rect.x += bullet[1] * knockback_strength
            boar_rect.y += bullet[2] * knockback_strength
            bullets.remove(bullet)
            if boar_hp <= 0:
                boar_alive = False
                boar_death_time = current_time
                soul_rect = soul_image.get_rect(center=boar_rect.center)
            continue

        if not screen.get_rect().colliderect(bullet[0]):
            bullets.remove(bullet)

    # BOAR AI
    if boar_alive:
        if boar_rect.colliderect(player_rect):
            running = False

        if not is_dashing and current_time - last_dash_time >= DASH_COOLDOWN:
            dx = player_rect.centerx - boar_rect.centerx
            dy = player_rect.centery - boar_rect.centery
            dist = math.hypot(dx, dy)
            if dist != 0:
                dash_dir = (dx / dist, dy / dist)
                is_dashing = True
                dash_start_time = current_time
                last_dash_time = current_time

        if is_dashing:
            boar_rect.x += dash_dir[0] * DASH_SPEED
            boar_rect.y += dash_dir[1] * DASH_SPEED
            if current_time - dash_start_time >= DASH_DURATION:
                is_dashing = False
        else:
            dx = player_rect.centerx - boar_rect.centerx
            dy = player_rect.centery - boar_rect.centery
            dist = math.hypot(dx, dy)
            if dist != 0:
                dx /= dist
                dy /= dist
                boar_rect.x += dx * boar_speed
                boar_rect.y += dy * boar_speed
                boar_image = boar_left if dx < 0 else boar_right

    # RESPAWN
    if not boar_alive and boar_death_time:
        if current_time - boar_death_time >= BOAR_RESPAWN_DELAY:
            boar_rect = spawn_boar()
            boar_hp = boar_max_hp
            boar_alive = True
            boar_death_time = None

    # SOUL PICKUP
    if soul_rect and player_rect.colliderect(soul_rect):
        souls_collected += 1
        soul_rect = None

    # DRAW
    screen.fill(clear_color)

    # DASH WARNING
    if boar_alive and not is_dashing:
        time_until_dash = DASH_COOLDOWN - (current_time - last_dash_time)
        if 0 < time_until_dash <= 400:
            dx = player_rect.centerx - boar_rect.centerx
            dy = player_rect.centery - boar_rect.centery
            dist = math.hypot(dx, dy)
            if dist != 0:
                dx /= dist
                dy /= dist
                end_x = boar_rect.centerx + dx * DASH_DISTANCE
                end_y = boar_rect.centery + dy * DASH_DISTANCE
                pygame.draw.line(screen, (255, 0, 0),
                                 boar_rect.center, (end_x, end_y), 12)

    # DRAW OBJECTS
    screen.blit(tree_image, tree_rect)
    screen.blit(tree_text, tree_text_rect)
    screen.blit(player_image, player_rect)

    for bullet in bullets:
        screen.blit(bullet[3], bullet[0])

    if boar_alive:
        screen.blit(boar_image, boar_rect)
        ratio = boar_hp / boar_max_hp
        pygame.draw.rect(screen, (60,60,60),
                         (boar_rect.centerx - 30, boar_rect.top - 10, 60, 6))
        pygame.draw.rect(screen, (200,50,50),
                         (boar_rect.centerx - 30, boar_rect.top - 10, int(60*ratio), 6))

    if soul_rect:
        screen.blit(soul_image, soul_rect)

    # GUI
    screen.blit(gui_soul_image, (10, 10))
    screen.blit(font.render(str(souls_collected), True, (255,255,255)), (70, 20))

    # SHOP UI
    if player_rect.colliderect(tree_rect):
        pygame.draw.rect(screen, (30,30,30), shop_panel, border_radius=10)
        pygame.draw.rect(screen, (200,200,200), shop_panel, 2, border_radius=10)

        screen.blit(font.render("Mother Nature's Shop", True, (255,255,255)),
                    (shop_panel.centerx - 140, shop_panel.y + 20))

        screen.blit(lightbulb_image, (shop_panel.x + 40, shop_panel.y + 90))
        screen.blit(small_font.render("Memory", True, (255,255,255)),
                    (shop_panel.x + 110, shop_panel.y + 100))

        pygame.draw.rect(
            screen,
            (0,120,80) if souls_collected >= MEMORY_PRICE and memories < MAX_MEMORIES else (120,80,80),
            buy_button,
            border_radius=6
        )

        screen.blit(small_font.render("Buy", True, (255,255,255)),
                    (buy_button.centerx - 20, buy_button.centery - 10))

        screen.blit(
            small_font.render(f"Owned: {memories}/10", True, (255,255,255)),
            (shop_panel.centerx - 60, shop_panel.bottom - 40)
        )

    # COOLDOWN BAR
    elapsed = current_time - last_shot_time
    if elapsed < cooldown_time:
        ratio = elapsed / cooldown_time
        pygame.draw.rect(screen, (60,60,60),
                         (player_rect.centerx - 25, player_rect.top - 12, 50, 6))
        pygame.draw.rect(screen, (0,200,255),
                         (player_rect.centerx - 25, player_rect.top - 12, int(50*ratio), 6))

    # YOU WIN
    if memories == MAX_MEMORIES:
        screen.blit(win_text, win_rect)
        BOAR_RESPAWN_DELAY = 5000000000000000000

    pygame.display.flip()

pygame.quit()
