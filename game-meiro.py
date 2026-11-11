import pygame
import sys
import random
from collections import deque

# --- 設定 ---
TILE_SIZE = 40
COLS, ROWS = 20, 10
UI_WIDTH = 250
SCREEN_WIDTH, SCREEN_HEIGHT = (COLS * TILE_SIZE) + UI_WIDTH, ROWS * TILE_SIZE

# --- ログ・状態管理 ---
damage_log = []
last_move = (0, 0)

def is_reachable(dungeon, start, goal):
    queue = deque([start])
    visited = {start}
    while queue:
        x, y = queue.popleft()
        if (x, y) == goal: return True
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and dungeon[ny][nx] != 1:
                if dungeon[ny][nx] != 3 and (nx, ny) not in visited:
                    visited.add((nx, ny)); queue.append((nx, ny))
    return False

def generate_map():
    while True:
        dungeon = [[1 for _ in range(COLS)] for _ in range(ROWS)]
        x, y = 1, 1
        dungeon[y][x] = 0
        for _ in range(150):
            dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            nx, ny = x + dx, y + dy
            if 0 < nx < COLS - 1 and 0 < ny < ROWS - 1:
                x, y = nx, ny
                dungeon[y][x] = 0
        empty_tiles = [(tx, ty) for ty in range(ROWS) for tx in range(COLS) if dungeon[ty][tx] == 0]
        empty_tiles.remove((1, 1))
        random.shuffle(empty_tiles)
        for _ in range(5):
            if empty_tiles: tx, ty = empty_tiles.pop(); dungeon[ty][tx] = 3
        goal_pos = empty_tiles.pop(); dungeon[goal_pos[1]][goal_pos[0]] = 2
        moving_traps = []
        for _ in range(2):
            if empty_tiles:
                tx, ty = empty_tiles.pop()
                moving_traps.append([tx, ty, random.choice([1, -1]), 0, 0])
        if is_reachable(dungeon, (1, 1), goal_pos): return dungeon, [1, 1], moving_traps

# --- 初期化 ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)
font_big = pygame.font.SysFont(None, 50)

map_data, player_pos, moving_traps = generate_map()
score, hp = 0, 3
game_state = "PLAY"
hint_message = ""

# --- メインループ ---
while True:
    screen.fill((30, 30, 30))
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        
        if game_state == "PLAY":
            if event.type == pygame.KEYDOWN:
                dx, dy = 0, 0
                if event.key == pygame.K_w: dy = -1
                elif event.key == pygame.K_s: dy = 1
                elif event.key == pygame.K_a: dx = -1
                elif event.key == pygame.K_d: dx = 1
                
                if dx != 0 or dy != 0:
                    nx, ny = player_pos[0] + dx, player_pos[1] + dy
                    if 0 <= nx < COLS and 0 <= ny < ROWS and map_data[ny][nx] != 1:
                        last_move = (dx, dy)
                        if map_data[ny][nx] == 2:
                            score += 100; map_data,player_pos, moving_traps = generate_map()
                            damage_log = []
                        elif map_data[ny][nx] == 3:
                            hp -= 1; damage_log.append((player_pos[0], player_pos[1], dx, dy))
                        else: player_pos = [nx, ny]
        
        elif game_state == "GAMEOVER":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: 
                    hp = 3; score = 0; damage_log = []; map_data, player_pos, moving_traps = generate_map(); game_state = "PLAY"
                elif event.key == pygame.K_q: pygame.quit(); sys.exit()

    if game_state == "PLAY":
        if hp <= 0: game_state = "GAMEOVER"
        hint_message = ""
        for t in moving_traps:
            t[4] += 1
            if t[4] > 20:
                nx, ny = t[0] + t[2], t[1] + t[3]
                if not (0 < nx < COLS - 1 and 0 < ny < ROWS - 1) or map_data[ny][nx] == 1:
                    t[2], t[3] = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                else: t[0], t[1] = nx, ny
                t[4] = 0
            # AIヒント：被弾ログと移動内容の突き合わせ
            if any(log[0] == t[0] and log[1] == t[1] and log[2] == last_move[0] and log[3] == last_move[1] for log in damage_log):
                hint_message = "AI: RISK DETECTED!"
            if player_pos == [t[0], t[1]]: hp -= 1; damage_log.append((t[0], t[1], last_move[0], last_move[1])); t[0], t[1] = 0, 0

    # 描画
    if game_state == "PLAY":
        for y, row in enumerate(map_data):
            for x, tile in enumerate(row):
                c = (50, 50, 50) if tile == 0 else (255, 255, 255)
                if tile == 2: c = (255, 215, 0)
                elif tile == 3: c = (255, 0, 0)
                pygame.draw.rect(screen, c, (x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE-2, TILE_SIZE-2))
        for t in moving_traps: pygame.draw.rect(screen, (255, 165, 0), (t[0]*TILE_SIZE, t[1]*TILE_SIZE, TILE_SIZE-2, TILE_SIZE-2))
        pygame.draw.rect(screen, (0, 255, 0), (player_pos[0]*TILE_SIZE, player_pos[1]*TILE_SIZE, TILE_SIZE-2, TILE_SIZE-2))
    else:
        screen.blit(font_big.render("GAME OVER", True, (255, 0, 0)), (250, 150))
        screen.blit(font.render(f"Final Score: {score}", True, (255, 255, 255)), (250, 200))
        screen.blit(font.render("Press R to Retry / Q to Quit", True, (255, 255, 0)), (150, 260))

    pygame.draw.rect(screen, (60, 60, 60), (COLS * TILE_SIZE, 0, UI_WIDTH, SCREEN_HEIGHT))
    screen.blit(font.render(f"HP: {hp}", True, (255, 0, 0)), (COLS * TILE_SIZE + 20, 20))
    screen.blit(font.render(f"Score: {score}", True, (0, 255, 0)), (COLS * TILE_SIZE + 20, 60))
    if hint_message: screen.blit(font.render(hint_message, True, (255, 100, 100)), (COLS * TILE_SIZE + 20, 120))
    pygame.display.flip(); clock.tick(60)
