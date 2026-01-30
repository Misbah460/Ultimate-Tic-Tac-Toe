import pygame
import sys
import math
import copy
import random

#CONFIGURATION
WIDTH, HEIGHT = 600, 640
BOARD_SIZE = 540
CELL_SIZE = BOARD_SIZE // 9
SMALL_BOARD_SIZE = BOARD_SIZE // 3
OFFSET_X = (WIDTH - BOARD_SIZE) // 2
OFFSET_Y = (HEIGHT - BOARD_SIZE) // 2 + 20

# COLORS 
COLOR_BG = (10, 15, 25)
COLOR_GRID_OFF = (30, 35, 50)
COLOR_GRID_ON = (0, 255, 200)
COLOR_X = (0, 200, 255)
COLOR_O = (255, 50, 100)
COLOR_TEXT = (240, 240, 255)
COLOR_BTN_IDLE = (20, 30, 40)
COLOR_BTN_HOVER = (0, 255, 200)
COLOR_BTN_TEXT_IDLE = (0, 255, 200)
COLOR_BTN_TEXT_HOVER = (10, 15, 25)
COLOR_QUIT_IDLE = (40, 20, 20)
COLOR_QUIT_HOVER = (255, 50, 50)

# SOUND MANAGER
class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        
        def load(name, path, vol=1.0):
            try:
                s = pygame.mixer.Sound(path)
                s.set_volume(vol)
                self.sounds[name] = s
            except:
                pass 

        load('move', 'move.wav', 0.4)
        load('win', 'win.wav', 0.6)
        load('lose', 'lose.wav', 1.0)
        load('start', 'start.wav', 0.7)

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

# PARTICLE SYSTEM
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = (random.randint(100, 255), random.randint(100, 255), random.randint(0, 100))
        self.size = random.randint(4, 8)
        self.vx = random.uniform(-6, 6)
        self.vy = random.uniform(-6, 6)
        self.life = 100

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 2
        self.size = max(0, self.size - 0.1)

    def draw(self, screen):
        if self.life > 0:
            s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, int(self.life * 2.5)), (int(self.size), int(self.size)), int(self.size))
            screen.blit(s, (int(self.x), int(self.y)))

# BUTTON CLASS
class Button:
    def __init__(self, x, y, w, h, text, font, is_quit=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.is_quit = is_quit
        self.hovered = False

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, screen):
        if self.is_quit:
            bg = COLOR_QUIT_HOVER if self.hovered else COLOR_QUIT_IDLE
            txt_c = (255, 255, 255)
            border = COLOR_QUIT_HOVER
        else:
            bg = COLOR_BTN_HOVER if self.hovered else COLOR_BTN_IDLE
            txt_c = COLOR_BTN_TEXT_HOVER if self.hovered else COLOR_BTN_TEXT_IDLE
            border = COLOR_BTN_HOVER
        
        pygame.draw.rect(screen, bg, self.rect, border_radius=10)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=10)
        
        txt_surf = self.font.render(self.text, True, txt_c)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, txt_rect)

    def is_clicked(self):
        return self.hovered

# --- GAME LOGIC ---
class UltimateTTT:
    def __init__(self):
        self.board = [[' ']*9 for _ in range(9)]#self.macro_board[8] = '-'
        self.macro_board = [' ']*9
        self.active_board = -1 
        self.winner = None
        self.game_over = False

    def get_valid_moves(self):
        if self.winner: return []
        if self.active_board == -1 or self.macro_board[self.active_board] != ' ':
            target_boards = [i for i, x in enumerate(self.macro_board) if x == ' ']
        else:
            target_boards = [self.active_board]

        moves = []
        for b_idx in target_boards:
            for c_idx in range(9):
                if self.board[b_idx][c_idx] == ' ':
                    moves.append((b_idx, c_idx))
        return moves

    def check_small_win(self, b_idx):
        b = self.board[b_idx]
        wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for x,y,z in wins:
            if b[x]==b[y]==b[z]!=' ': return b[x]
        if ' ' not in b: return 'D'
        return ' '

    def check_macro_win(self):
        b = self.macro_board
        wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for x,y,z in wins:
            if b[x]==b[y]==b[z] and b[x] not in [' ','D']: return b[x]
        if ' ' not in b: return 'D'
        return None

    def make_move(self, move, player):
        b_idx, c_idx = move
        self.board[b_idx][c_idx] = player
        
        if self.macro_board[b_idx] == ' ':
            res = self.check_small_win(b_idx)
            if res != ' ': self.macro_board[b_idx] = res
        
        self.winner = self.check_macro_win()
        self.active_board = c_idx
        if self.macro_board[self.active_board] != ' ':
            self.active_board = -1
        
        if self.winner: self.game_over = True

# STRONG AI AGENT ---
class AI:
    def __init__(self, level):
        self.level = level 
        self.player = 'O'
        self.opponent = 'X'

    def evaluate_small(self, small_board):
        score = 0
        wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        
        if small_board[4] == self.player: score += 2
        elif small_board[4] == self.opponent: score -= 2

        for x, y, z in wins:
            line = [small_board[x], small_board[y], small_board[z]]
            ai_count = line.count(self.player)
            opp_count = line.count(self.opponent)
            empty_count = line.count(' ')

            if ai_count == 2 and empty_count == 1: score += 10
            if opp_count == 2 and empty_count == 1: score -= 10
            if ai_count == 1 and empty_count == 2: score += 1
            if opp_count == 1 and empty_count == 2: score -= 1
        return score

    def evaluate(self, game):
        score = 0
        for i in range(9):
            if game.macro_board[i] == self.player:
                score += 100
                if i == 4: score += 50
                elif i % 2 == 0: score += 20
            elif game.macro_board[i] == self.opponent:
                score -= 100
                if i == 4: score -= 50
                elif i % 2 == 0: score -= 20
            elif game.macro_board[i] == ' ':
                score += self.evaluate_small(game.board[i])
        return score

    def minimax(self, game, depth, alpha, beta, is_maximizing):
        if game.winner == self.player: return 10000 + depth
        if game.winner == self.opponent: return -10000 - depth
        if game.winner == 'D': return 0
        if depth == 0: return self.evaluate(game)

        moves = game.get_valid_moves()
        if not moves: return 0
        
        if is_maximizing:
            max_eval = -math.inf
            for move in moves:
                new_game = copy.deepcopy(game)
                new_game.make_move(move, self.player)
                eval = self.minimax(new_game, depth-1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = math.inf
            for move in moves:
                new_game = copy.deepcopy(game)
                new_game.make_move(move, self.opponent)
                eval = self.minimax(new_game, depth-1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    def get_move(self, game):
        moves = game.get_valid_moves()
        if not moves: return None

        if self.level == 'EASY':
            return random.choice(moves)
        elif self.level == 'MEDIUM':
            if random.random() < 0.2: return random.choice(moves)
            depth = 3
        else: 
            depth = 4
        
        best_score = -math.inf
        best_move = None
        alpha = -math.inf
        beta = math.inf
        
        moves.sort(key=lambda m: 5 if m[1]==4 else 1, reverse=True)

        for move in moves:
            new_game = copy.deepcopy(game)
            new_game.make_move(move, self.player)
            score = self.minimax(new_game, depth, alpha, beta, False)
            if score > best_score:
                best_score = score
                best_move = move
        
        if best_move is None and moves:
            best_move = random.choice(moves)
        return best_move

# DRAWING
def draw_board(screen, game):
    for i in range(1, 3):
        pygame.draw.line(screen, COLOR_GRID_OFF, 
                         (OFFSET_X + i*SMALL_BOARD_SIZE, OFFSET_Y), 
                         (OFFSET_X + i*SMALL_BOARD_SIZE, OFFSET_Y + BOARD_SIZE), 6)
        pygame.draw.line(screen, COLOR_GRID_OFF, 
                         (OFFSET_X, OFFSET_Y + i*SMALL_BOARD_SIZE), 
                         (OFFSET_X + BOARD_SIZE, OFFSET_Y + i*SMALL_BOARD_SIZE), 6)
    
    for i in range(9):
        if i % 3 != 0:
            pygame.draw.line(screen, (20, 25, 35), (OFFSET_X + i*CELL_SIZE, OFFSET_Y), (OFFSET_X + i*CELL_SIZE, OFFSET_Y + BOARD_SIZE), 2)
            pygame.draw.line(screen, (20, 25, 35), (OFFSET_X, OFFSET_Y + i*CELL_SIZE), (OFFSET_X + BOARD_SIZE, OFFSET_Y + i*CELL_SIZE), 2)

    if not game.winner:
        targets = [game.active_board] if game.active_board != -1 else [i for i,x in enumerate(game.macro_board) if x==' ']
        for t in targets:
            r, c = t%3, t//3
            rect = pygame.Rect(OFFSET_X + r*SMALL_BOARD_SIZE, OFFSET_Y + c*SMALL_BOARD_SIZE, SMALL_BOARD_SIZE, SMALL_BOARD_SIZE)
            pygame.draw.rect(screen, COLOR_GRID_ON, rect, 3)

    font = pygame.font.SysFont("arial", 28, bold=True)
    for b in range(9):
        for c in range(9):
            p = game.board[b][c]
            if p != ' ':
                bx, by = b%3, b//3
                cx, cy = c%3, c//3
                x = OFFSET_X + bx*SMALL_BOARD_SIZE + cx*CELL_SIZE + CELL_SIZE//2
                y = OFFSET_Y + by*SMALL_BOARD_SIZE + cy*CELL_SIZE + CELL_SIZE//2
                color = COLOR_X if p=='X' else COLOR_O
                screen.blit(font.render(p, True, color), font.render(p, True, color).get_rect(center=(x,y)))

    font_big = pygame.font.SysFont("arial", 90, bold=True)
    for i in range(9):
        p = game.macro_board[i]
        if p != ' ':
            bx, by = i%3, i//3
            cx = OFFSET_X + bx*SMALL_BOARD_SIZE + SMALL_BOARD_SIZE//2
            cy = OFFSET_Y + by*SMALL_BOARD_SIZE + SMALL_BOARD_SIZE//2
            
            s = pygame.Surface((SMALL_BOARD_SIZE-6, SMALL_BOARD_SIZE-6))
            s.set_alpha(200)
            s.fill(COLOR_BG)
            screen.blit(s, (OFFSET_X+bx*SMALL_BOARD_SIZE+3, OFFSET_Y+by*SMALL_BOARD_SIZE+3))
            
            color = COLOR_X if p=='X' else (COLOR_O if p=='O' else (200,200,200))
            screen.blit(font_big.render(p, True, color), font_big.render(p, True, color).get_rect(center=(cx,cy)))

# --- MAIN ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ultimate Tic-Tac-Toe")
    clock = pygame.time.Clock()
    
    sounds = SoundManager()
    font_menu = pygame.font.SysFont("comicsansms", 40, bold=True)
    font_btn = pygame.font.SysFont("arial", 24, bold=True)
    font_status = pygame.font.SysFont("arial", 20)
    
    STATE_MENU = 0
    STATE_GAME = 1
    STATE_GAMEOVER = 2
    current_state = STATE_MENU
    
    # Buttons
    btn_easy = Button(WIDTH//2 - 100, 250, 200, 50, "EASY", font_btn)
    btn_med = Button(WIDTH//2 - 100, 320, 200, 50, "MEDIUM", font_btn)
    btn_hard = Button(WIDTH//2 - 100, 390, 200, 50, "HARD", font_btn)
    
    # Game Over Buttons
    btn_menu = Button(WIDTH//2 - 155, HEIGHT//2 + 60, 150, 50, "Main Menu", font_btn)
    btn_quit = Button(WIDTH//2 + 5, HEIGHT//2 + 60, 150, 50, "Quit", font_btn, is_quit=True)

    game = None
    ai = None
    player_turn = True
    particles = []
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(COLOR_BG)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if current_state == STATE_MENU:
                    if btn_easy.is_clicked():
                        game = UltimateTTT()
                        ai = AI('EASY')
                        current_state = STATE_GAME
                        sounds.play('start')
                    elif btn_med.is_clicked():
                        game = UltimateTTT()
                        ai = AI('MEDIUM')
                        current_state = STATE_GAME
                        sounds.play('start')
                    elif btn_hard.is_clicked():
                        game = UltimateTTT()
                        ai = AI('HARD')
                        current_state = STATE_GAME
                        sounds.play('start')
                
                elif current_state == STATE_GAME and player_turn:
                    mx, my = event.pos
                    if OFFSET_X <= mx <= OFFSET_X+BOARD_SIZE and OFFSET_Y <= my <= OFFSET_Y+BOARD_SIZE:
                        col = (mx - OFFSET_X) // CELL_SIZE
                        row = (my - OFFSET_Y) // CELL_SIZE
                        b_idx = (row // 3) * 3 + (col // 3)
                        c_idx = (row % 3) * 3 + (col % 3)
                        
                        if (b_idx, c_idx) in game.get_valid_moves():
                            game.make_move((b_idx, c_idx), 'X')
                            sounds.play('move')
                            player_turn = False
                            
                            # Check Win Immediately
                            if game.winner:
                                current_state = STATE_GAMEOVER
                                if game.winner == 'X': sounds.play('win')
                                elif game.winner == 'O': sounds.play('lose')

                elif current_state == STATE_GAMEOVER:
                    if btn_menu.is_clicked():
                        current_state = STATE_MENU
                        particles = []
                        player_turn = True
                        sounds.play('move')
                    elif btn_quit.is_clicked():
                        running = False

        # --- DRAWING & AI ---
        if current_state == STATE_MENU:
            title = font_menu.render("ULTIMATE TIC-TAC-TOE", True, COLOR_GRID_ON)
            sub = font_status.render("Select AI Difficulty", True, (150, 150, 150))
            screen.blit(title, title.get_rect(center=(WIDTH//2, 120)))
            screen.blit(sub, sub.get_rect(center=(WIDTH//2, 170)))
            for btn in [btn_easy, btn_med, btn_hard]:
                btn.update(mouse_pos)
                btn.draw(screen)

        elif current_state == STATE_GAME:
            draw_board(screen, game)
            header = f"Level: {ai.level}  |  You (X) vs AI (O)"
            h_surf = font_status.render(header, True, COLOR_TEXT)
            screen.blit(h_surf, (20, 20))
            
            if not player_turn and not game.game_over:
                pygame.display.flip()
                move = ai.get_move(game)
                if move:
                    game.make_move(move, 'O')
                    sounds.play('move')
                    player_turn = True
                else:
                    game.game_over = True
                
                if game.winner: 
                    current_state = STATE_GAMEOVER
                    if game.winner == 'X': sounds.play('win')
                    elif game.winner == 'O': sounds.play('lose')

        elif current_state == STATE_GAMEOVER:
            draw_board(screen, game)
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(230)
            overlay.fill((0,0,0))
            screen.blit(overlay, (0,0))
            
            if game.winner == 'X':
                # Split Congratulations
                line1 = font_menu.render("CONGRATULATIONS!", True, (0, 255, 0))
                line2 = font_menu.render("You WIN!", True, (0, 255, 0))
                screen.blit(line1, line1.get_rect(center=(WIDTH//2, HEIGHT//2 - 90)))
                screen.blit(line2, line2.get_rect(center=(WIDTH//2, HEIGHT//2 - 40)))
                
                if not particles:
                    particles = [Particle(WIDTH//2, HEIGHT//2) for _ in range(100)]
                    
            elif game.winner == 'O':
                # Split Bad Luck Message
                line1 = font_menu.render("BAD LUCK!", True, (255, 50, 50))
                line2 = font_menu.render("You Can't Defeat AI", True, (255, 100, 100))
                screen.blit(line1, line1.get_rect(center=(WIDTH//2, HEIGHT//2 - 90)))
                screen.blit(line2, line2.get_rect(center=(WIDTH//2, HEIGHT//2 - 40)))
                
            else:
                msg = "DRAW! BETTER LUCK NEXT TIME!"
                t_surf = font_menu.render(msg, True, (200, 200, 200))
                screen.blit(t_surf, t_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 50)))
            
            for p in particles:
                p.update()
                p.draw(screen)
            
            btn_menu.update(mouse_pos)
            btn_menu.draw(screen)
            btn_quit.update(mouse_pos)
            btn_quit.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()