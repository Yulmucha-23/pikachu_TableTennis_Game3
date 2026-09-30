import pygame
import sys
import math
import os
import asyncio  # ★ pygbag 웹 실행을 위한 asyncio 추가

# 1. 초기화 및 화면 설정 (1500x900)
pygame.init()
WIDTH, HEIGHT = 1500, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pikachu Table Tennis")
clock = pygame.time.Clock()

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (15, 15, 15)
GREEN = (24, 90, 44)
LINE_COLOR = (245, 245, 245)
BALL_COLOR = (255, 130, 0)
SERVE_COLOR = (0, 255, 100)
TOSS_COLOR = (255, 215, 0)
MENU_COLOR = (255, 80, 80)
PIKA_RED = (230, 30, 30)

# 게이지 및 알림 색상
GAUGE_YELLOW = (255, 215, 0)
GAUGE_GREEN = (0, 220, 80)
GAUGE_RED = (255, 50, 50)
SCORE_P1_COLOR = (100, 180, 255)

# 탁구대 규격
TABLE_W, TABLE_H = 700, 320
TABLE_X = (WIDTH - TABLE_W) // 2
TABLE_Y = (HEIGHT - TABLE_H) // 2
NET_X = TABLE_X + TABLE_W // 2

# 캐릭터 크기 및 초기 위치
CHAR_SPEED = 8
p1_x, p1_y = TABLE_X - 120, TABLE_Y + TABLE_H // 2
p2_x, p2_y = TABLE_X + TABLE_W + 120, TABLE_Y + TABLE_H // 2
p1_score = 0
p2_score = 0

# 탁구공 및 잔상 설정
BALL_SIZE = 16
ball_x = 0.0
ball_y = 0.0
ball_z = 0.0
ball_speed_x = 0.0
ball_speed_y = 0.0
ball_speed_z = 0.0
GRAVITY = 0.24
ball_trail = []
is_spike_shot = False

# 텍스트 전광판 연출용 변수
is_out_text_active = False
score_text_display = ""
score_text_sub = ""
score_text_timer = 0

# 경기 규칙 상태 변수
last_bounce_court = 0
p1_bounce_count = 0
p2_bounce_count = 0
last_hit_player = 0

# 서브 시스템 변수
current_server = 1
serve_count = 0
is_waiting_serve = True
is_tossed = False

# 스파이크 게이지 상태 변수
p1_gauge = 0.0
p2_gauge = 0.0
p1_charging = False
p2_charging = False

font = pygame.font.SysFont("malgungothic", 50)
small_font = pygame.font.SysFont("malgungothic", 25)
winner_font = pygame.font.SysFont("malgungothic", 80)
game_over = False
winner = ""

# 입력 감지 플래그
p1_z_pressed = False
p2_enter_pressed = False
p1_shift_released = False
p2_shift_released = False
last_p1_shift_state = False
last_p2_shift_state = False
p2_shift_event_down = False  # ★ 이벤트로 추적하는 오른쪽 Shift 상태 (웹 환경 대응)

# 이미지 로드 (140x140)
IMAGE_NAME = "pikachu.png"
if os.path.exists(IMAGE_NAME):
    pika_base = pygame.image.load(IMAGE_NAME).convert()
    pika_base.set_colorkey((0, 0, 0))
    pika_img = pygame.transform.scale(pika_base, (140, 140))
    p2_sprite = pika_img
    p1_sprite = pygame.transform.flip(pika_img, True, False)
else:
    p1_sprite = pygame.Surface((140, 140))
    p1_sprite.fill((255, 230, 0))
    p2_sprite = pygame.Surface((140, 140))
    p2_sprite.fill((255, 200, 0))

def init_game_fully():
    global p1_score, p2_score, game_over, winner, current_server, serve_count
    p1_score = 0
    p2_score = 0
    game_over = False
    winner = ""
    current_server = 1
    serve_count = -1
    reset_ball()

def trigger_score_event(winner_player, is_out_by_nobounce=False):
    global p1_score, p2_score, game_over, winner, is_out_text_active, score_text_display, score_text_sub, score_text_timer
    if game_over or is_out_text_active:
        return
    is_out_text_active = True
    score_text_timer = 50
    if is_out_by_nobounce:
        score_text_sub = "OUT! Point Lost"
    else:
        score_text_sub = "SCORE!"
    if winner_player == 1:
        p1_score += 1
        score_text_display = "P1 SCORES!"
    else:
        p2_score += 1
        score_text_display = "P2 SCORES!"
    if p1_score >= 15:
        game_over = True
        winner = "Player 1"
        is_out_text_active = False
    elif p2_score >= 15:
        game_over = True
        winner = "Player 2"
        is_out_text_active = False

def draw_gauge_bar(surface, x, y, gauge_val, charging):
    if not charging and gauge_val == 0:
        return
    bar_w, bar_h = 100, 12
    bx, by = x - bar_w // 2, y - 95
    pygame.draw.rect(surface, (60, 60, 60), (bx, by, bar_w, bar_h))
    curr_w = int(bar_w * (gauge_val / 100.0))
    for i in range(curr_w):
        percent = (i / bar_w) * 100.0
        if percent <= 40.0:
            color = GAUGE_YELLOW
        elif percent <= 80.0:
            color = GAUGE_GREEN
        else:
            color = GAUGE_RED
        pygame.draw.line(surface, color, (bx + i, by), (bx + i, by + bar_h - 1))
    pygame.draw.rect(surface, WHITE, (bx, by, bar_w, bar_h), 1)

def reset_ball():
    global ball_x, ball_y, ball_z, ball_speed_x, ball_speed_y, ball_speed_z
    global last_bounce_court, p1_bounce_count, p2_bounce_count, last_hit_player
    global current_server, serve_count, is_waiting_serve, is_tossed, is_spike_shot, ball_trail
    serve_count += 1
    if serve_count >= 2:
        serve_count = 0
        current_server = 2 if current_server == 1 else 1
    if current_server == 1:
        ball_x = float(TABLE_X - 60)
        ball_y = float(p1_y)
    else:
        ball_x = float(TABLE_X + TABLE_W + 60)
        ball_y = float(p2_y)
    ball_z = 30.0
    ball_speed_x = 0.0
    ball_speed_y = 0.0
    ball_speed_z = 0.0
    last_bounce_court = 0
    p1_bounce_count = 0
    p2_bounce_count = 0
    last_hit_player = 0
    is_waiting_serve = True
    is_tossed = False
    is_spike_shot = False
    ball_trail.clear()

# 최초 리셋 실행
reset_ball()

# ★ 비동기 메인 함수 정의
async def main():
    global p1_x, p1_y, p2_x, p2_y
    global p1_shift_released, p2_shift_released, last_p1_shift_state, last_p2_shift_state
    global p2_shift_event_down
    global p1_charging, p2_charging, p1_gauge, p2_gauge
    global p1_z_pressed, p2_enter_pressed
    global ball_x, ball_y, ball_z, ball_speed_x, ball_speed_y, ball_speed_z
    global is_tossed, is_waiting_serve, is_spike_shot, last_hit_player
    global p1_bounce_count, p2_bounce_count, last_bounce_court, is_out_text_active, score_text_timer

    running = True
    while running:
        screen.fill(BLACK)
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # ★ 오른쪽 Shift 키를 이벤트로도 추적 (웹에서 get_pressed가 못 잡는 경우 대비)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RSHIFT:
                p2_shift_event_down = True
            if event.type == pygame.KEYUP and event.key == pygame.K_RSHIFT:
                p2_shift_event_down = False

        if game_over:
            if keys[pygame.K_r]:
                init_game_fully()
            if keys[pygame.K_q]:
                running = False

        if is_out_text_active and not game_over:
            score_text_timer -= 1
            if score_text_timer <= 0:
                is_out_text_active = False
                reset_ball()

        if not game_over and not is_out_text_active:
            # --- 1P 조작키 (E:위, D:아래, S:왼쪽, F:오른쪽) ---
            if keys[pygame.K_e] and p1_y > TABLE_Y - 40:
                p1_y -= CHAR_SPEED
                if is_waiting_serve and current_server == 1 and not is_tossed:
                    ball_y = float(p1_y)
            if keys[pygame.K_d] and p1_y < TABLE_Y + TABLE_H + 40:
                p1_y += CHAR_SPEED
                if is_waiting_serve and current_server == 1 and not is_tossed:
                    ball_y = float(p1_y)
            if keys[pygame.K_s] and p1_x > 40:
                p1_x -= CHAR_SPEED
            if keys[pygame.K_f] and p1_x < TABLE_X - 50:
                p1_x += CHAR_SPEED

            # --- 2P 조작키 (방향키) ---
            if keys[pygame.K_UP] and p2_y > TABLE_Y - 40:
                p2_y -= CHAR_SPEED
                if is_waiting_serve and current_server == 2 and not is_tossed:
                    ball_y = float(p2_y)
            if keys[pygame.K_DOWN] and p2_y < TABLE_Y + TABLE_H + 40:
                p2_y += CHAR_SPEED
                if is_waiting_serve and current_server == 2 and not is_tossed:
                    ball_y = float(p2_y)
            if keys[pygame.K_LEFT] and p2_x > TABLE_X + TABLE_W + 50:
                p2_x -= CHAR_SPEED
            if keys[pygame.K_RIGHT] and p2_x < WIDTH - 40:
                p2_x += CHAR_SPEED

            # ★ 2P 오른쪽 Shift 눌림 여부: get_pressed / get_mods / 이벤트 중 하나라도 감지되면 눌린 것으로 처리
            p2_shift_down = bool(
                keys[pygame.K_RSHIFT]
                or (pygame.key.get_mods() & pygame.KMOD_RSHIFT)
                or p2_shift_event_down
            )

            # 키 릴리즈 감지
            p1_shift_released = (last_p1_shift_state and not keys[pygame.K_LSHIFT])
            p2_shift_released = (last_p2_shift_state and not p2_shift_down)
            last_p1_shift_state = keys[pygame.K_LSHIFT]
            last_p2_shift_state = p2_shift_down

            # 스파이크 게이지 차징
            if keys[pygame.K_LSHIFT] and not is_waiting_serve and not game_over and not is_out_text_active:
                p1_charging = True
                p1_gauge += 4.2
                if p1_gauge >= 100.0:
                    p1_gauge = 0.0
                    p1_charging = False
            elif not keys[pygame.K_LSHIFT]:
                if not p1_shift_released:
                    p1_gauge = 0.0
                    p1_charging = False

            if p2_shift_down and not is_waiting_serve and not game_over and not is_out_text_active:
                p2_charging = True
                p2_gauge += 4.2
                if p2_gauge >= 100.0:
                    p2_gauge = 0.0
                    p2_charging = False
            elif not p2_shift_down:
                if not p2_shift_released:
                    p2_gauge = 0.0
                    p2_charging = False

            # --- 2단계 분할식 수동 토스 및 서브 시스템 ---
            render_ball_y = ball_y - ball_z
            ball_rect = pygame.Rect(ball_x - 10, render_ball_y - 10, BALL_SIZE + 20, BALL_SIZE + 20)

            # 1P 수동 토스 / 서브 처리
            if is_waiting_serve and current_server == 1 and not game_over and not is_out_text_active:
                if keys[pygame.K_z]:
                    if not p1_z_pressed:
                        p1_z_pressed = True
                        if not is_tossed:
                            ball_speed_z = 9.0
                            ball_speed_x = 0.0
                            ball_speed_y = 0.0
                            is_tossed = True
                        else:
                            p1_serve_rect = pygame.Rect(p1_x - 50, p1_y - 120, 220, 240)
                            if ball_rect.colliderect(p1_serve_rect):
                                target_x = TABLE_X + TABLE_W - (TABLE_W * 0.35)
                                frames = 48.0
                                ball_speed_x = (target_x - ball_x) / frames
                                ball_speed_y = (max(min(p1_y, TABLE_Y + TABLE_H - 50), TABLE_Y + 50) - ball_y) / frames
                                ball_speed_z = 5.5
                                last_hit_player = 1
                                is_waiting_serve = False
                else:
                    p1_z_pressed = False

            # 2P 수동 토스 / 서브 처리
            if is_waiting_serve and current_server == 2 and not game_over and not is_out_text_active:
                if keys[pygame.K_RETURN]:
                    if not p2_enter_pressed:
                        p2_enter_pressed = True
                        if not is_tossed:
                            ball_speed_z = 9.0
                            ball_speed_x = 0.0
                            ball_speed_y = 0.0
                            is_tossed = True
                        else:
                            p2_serve_rect = pygame.Rect(p2_x - 140, p2_y - 120, 240, 240)
                            if ball_rect.colliderect(p2_serve_rect):
                                target_x = TABLE_X + (TABLE_W * 0.35)
                                frames = 48.0
                                ball_speed_x = (target_x - ball_x) / frames
                                ball_speed_y = (max(min(p2_y, TABLE_Y + TABLE_H - 50), TABLE_Y + 50) - ball_y) / frames
                                ball_speed_z = 5.5
                                last_hit_player = 2
                                is_waiting_serve = False
                else:
                    p2_enter_pressed = False

        # --- 물리 이동 및 잔상 기록 ---
        if not is_waiting_serve or is_tossed:
            if not game_over and not is_out_text_active:
                ball_x += ball_speed_x
                ball_y += ball_speed_y
                ball_speed_z -= GRAVITY
                ball_z += ball_speed_z
                if is_spike_shot:
                    ball_trail.append((int(ball_x), int(ball_y - ball_z)))
                    if len(ball_trail) > 8:
                        ball_trail.pop(0)
                else:
                    ball_trail.clear()

            if is_waiting_serve and is_tossed and ball_z <= 0 and not game_over and not is_out_text_active:
                if current_server == 1:
                    trigger_score_event(2, True)
                else:
                    trigger_score_event(1, True)

            # --- 탁구대 바운드 판단 ---
            if ball_z <= 0 and not is_waiting_serve and not game_over and not is_out_text_active:
                ball_z = 0
                if TABLE_X <= ball_x <= TABLE_X + TABLE_W and TABLE_Y <= ball_y <= TABLE_Y + TABLE_H:
                    ball_speed_z = 6.2
                    if ball_x < NET_X:
                        last_bounce_court = 1
                        if last_hit_player == 1:
                            trigger_score_event(2, True)
                        else:
                            p1_bounce_count += 1
                            if p1_bounce_count >= 2:
                                trigger_score_event(2, False)
                    else:
                        last_bounce_court = 2
                        if last_hit_player == 2:
                            trigger_score_event(1, True)
                        else:
                            p2_bounce_count += 1
                            if p2_bounce_count >= 2:
                                trigger_score_event(1, False)
                else:
                    if is_spike_shot:
                        if last_hit_player == 1:
                            trigger_score_event(2, True)
                        elif last_hit_player == 2:
                            trigger_score_event(1, True)

            # --- 장외 소멸 처리 ---
            if (ball_x < 0 or ball_x > WIDTH or ball_y < 0 or ball_y > HEIGHT) and not is_waiting_serve and not game_over and not is_out_text_active:
                if last_bounce_court == 2 and last_hit_player == 1:
                    trigger_score_event(1, False)
                elif last_bounce_court == 1 and last_hit_player == 2:
                    trigger_score_event(2, False)
                elif last_hit_player == 1:
                    trigger_score_event(2, True)
                elif last_hit_player == 2:
                    trigger_score_event(1, True)

        # --- 랠리 조작 판정계 ---
        p1_racket_rect = pygame.Rect(p1_x + 8, p1_y - 49, 77, 98)
        p2_racket_rect = pygame.Rect(p2_x - 56, p2_y - 49, 77, 98)
        p1_spike_hitbox = pygame.Rect(p1_x - 30, p1_y - 75, 120, 150)
        p2_spike_hitbox = pygame.Rect(p2_x - 90, p2_y - 75, 120, 150)

        # 1P 일반 랠리 및 스파이크 타격
        if ball_speed_x < 0 and not is_waiting_serve and not game_over and not is_out_text_active:
            if ball_rect.colliderect(p1_racket_rect) and keys[pygame.K_z]:
                target_x = TABLE_X + TABLE_W - (TABLE_W * 0.35)
                frames = 44.0
                ball_speed_x = (target_x - ball_x) / frames
                ball_speed_y = ((TABLE_Y + TABLE_H // 2) - ball_y) / frames + (ball_y - p1_y) * 0.04
                ball_speed_z = 4.5
                is_spike_shot = False
                p2_bounce_count = 0
                p1_bounce_count = 0
                last_bounce_court = 0
                last_hit_player = 1
            elif ball_rect.colliderect(p1_spike_hitbox) and p1_shift_released and p1_gauge > 0:
                is_spike_shot = False
                if p1_gauge <= 40.0:
                    target_x = TABLE_X + TABLE_W - (TABLE_W * 0.30)
                    frames = 48.0
                    ball_speed_x = (target_x - ball_x) / frames
                    ball_speed_y = ((TABLE_Y + TABLE_H // 2) - ball_y) / frames
                    ball_speed_z = 4.8
                    p2_bounce_count = 0
                    p1_bounce_count = 0
                    last_bounce_court = 0
                    last_hit_player = 1
                elif p1_gauge <= 80.0:
                    target_x = TABLE_X + TABLE_W - (TABLE_W * 0.25)
                    frames = 36.0
                    ball_speed_x = (target_x - ball_x) / frames
                    target_y = TABLE_Y + (TABLE_H * 0.30) if (ball_y - p1_y) < 0 else TABLE_Y + (TABLE_H * 0.70)
                    ball_speed_y = (target_y - ball_y) / frames
                    ball_speed_z = 3.8
                    is_spike_shot = True
                    p2_bounce_count = 0
                    p1_bounce_count = 0
                    last_bounce_court = 0
                    last_hit_player = 1
                else:
                    ball_speed_x = 14.5
                    ball_speed_y = (ball_y - p1_y) * 0.12
                    ball_speed_z = 8.5
                    is_spike_shot = True
                    p2_bounce_count = 0
                    p1_bounce_count = 0
                    last_bounce_court = 0
                    last_hit_player = 1
                p1_gauge = 0.0

        # 2P 일반 랠리 및 스파이크 타격
        if ball_speed_x > 0 and not is_waiting_serve and not game_over and not is_out_text_active:
            if ball_rect.colliderect(p2_racket_rect) and keys[pygame.K_RETURN]:
                target_x = TABLE_X + (TABLE_W * 0.35)
                frames = 44.0
                ball_speed_x = (target_x - ball_x) / frames
                ball_speed_y = ((TABLE_Y + TABLE_H // 2) - ball_y) / frames + (ball_y - p2_y) * 0.04
                ball_speed_z = 4.5
                is_spike_shot = False
                p1_bounce_count = 0
                p2_bounce_count = 0
                last_bounce_court = 0
                last_hit_player = 2
            elif ball_rect.colliderect(p2_spike_hitbox) and p2_shift_released and p2_gauge > 0:
                is_spike_shot = False
                if p2_gauge <= 40.0:
                    target_x = TABLE_X + (TABLE_W * 0.30)
                    frames = 48.0
                    ball_speed_x = (target_x - ball_x) / frames
                    ball_speed_y = ((TABLE_Y + TABLE_H // 2) - ball_y) / frames
                    ball_speed_z = 4.8
                    p1_bounce_count = 0
                    p2_bounce_count = 0
                    last_bounce_court = 0
                    last_hit_player = 2
                elif p2_gauge <= 80.0:
                    target_x = TABLE_X + (TABLE_W * 0.25)
                    frames = 36.0
                    ball_speed_x = (target_x - ball_x) / frames
                    target_y = TABLE_Y + (TABLE_H * 0.30) if (ball_y - p2_y) < 0 else TABLE_Y + (TABLE_H * 0.70)
                    ball_speed_y = (target_y - ball_y) / frames
                    ball_speed_z = 3.8
                    is_spike_shot = True
                    p1_bounce_count = 0
                    p2_bounce_count = 0
                    last_bounce_court = 0
                    last_hit_player = 2
                else:
                    ball_speed_x = -14.5
                    ball_speed_y = (ball_y - p2_y) * 0.12
                    ball_speed_z = 8.5
                    is_spike_shot = True
                    p1_bounce_count = 0
                    p2_bounce_count = 0
                    last_bounce_court = 0
                    last_hit_player = 2
                p2_gauge = 0.0

        # 화면 그리기
        pygame.draw.rect(screen, GREEN, (TABLE_X, TABLE_Y, TABLE_W, TABLE_H))
        pygame.draw.rect(screen, LINE_COLOR, (TABLE_X, TABLE_Y, TABLE_W, TABLE_H), 5)
        pygame.draw.line(screen, LINE_COLOR, (TABLE_X, TABLE_Y + TABLE_H // 2), (TABLE_X + TABLE_W, TABLE_Y + TABLE_H // 2), 2)
        pygame.draw.line(screen, WHITE, (NET_X, TABLE_Y - 20), (NET_X, TABLE_Y + TABLE_H + 20), 6)

        # 캐릭터 렌더링
        screen.blit(p1_sprite, (int(p1_x - 55), int(p1_y - 70)))
        pygame.draw.line(screen, (160, 82, 45), (int(p1_x + 30), int(p1_y + 15)), (int(p1_x + 55), int(p1_y - 5)), 7)
        pygame.draw.circle(screen, PIKA_RED, (int(p1_x + 60), int(p1_y - 10)), 20)
        pygame.draw.circle(screen, WHITE, (int(p1_x + 60), int(p1_y - 10)), 20, 2)
        screen.blit(p2_sprite, (int(p2_x - 85), int(p2_y - 70)))
        pygame.draw.line(screen, (160, 82, 45), (int(p2_x - 30), int(p2_y + 15)), (int(p2_x - 45), int(p2_y - 5)), 7)
        pygame.draw.circle(screen, (40, 120, 230), (int(p2_x - 55), int(p2_y - 10)), 20)
        pygame.draw.circle(screen, WHITE, (int(p2_x - 55), int(p2_y - 10)), 20, 2)
        draw_gauge_bar(screen, int(p1_x), int(p1_y), p1_gauge, p1_charging)
        draw_gauge_bar(screen, int(p2_x), int(p2_y), p2_gauge, p2_charging)

        if is_waiting_serve and not game_over and not is_out_text_active:
            if current_server == 1:
                msg = " Wait Toss" if not is_tossed else " Toss! Hit!"
                screen.blit(small_font.render(msg, True, TOSS_COLOR if is_tossed else SERVE_COLOR), (int(p1_x - 40), int(p1_y - 120)))
            else:
                msg = " Wait Toss" if not is_tossed else " Toss! Hit!"
                screen.blit(small_font.render(msg, True, TOSS_COLOR if is_tossed else SERVE_COLOR), (int(p2_x - 40), int(p2_y - 120)))

        # 스파이크 잔상 이펙트
        if is_spike_shot and len(ball_trail) > 1:
            for idx, pos in enumerate(ball_trail):
                target_pos = (int(pos[0] + BALL_SIZE // 2), int(pos[1] + BALL_SIZE // 2))
                target_radius = int((BALL_SIZE // 2) * (idx / len(ball_trail)))
                if target_radius > 0:
                    pygame.draw.circle(screen, (255, 130, 0), target_pos, target_radius)

        # 공 하단 그림자 및 공
        pygame.draw.ellipse(screen, (25, 55, 25), (int(ball_x), int(ball_y + 10), BALL_SIZE, BALL_SIZE // 2))
        pygame.draw.ellipse(screen, BALL_COLOR, (int(ball_x), int(ball_y - ball_z), BALL_SIZE, BALL_SIZE))

        # 전광판 자막
        if is_out_text_active and not game_over:
            out_label = font.render(score_text_sub, True, GAUGE_RED)
            screen.blit(out_label, (WIDTH // 2 - out_label.get_width() // 2, HEIGHT // 2 - 140))
            score_label = small_font.render(score_text_display, True, SCORE_P1_COLOR if "1" in score_text_display else GAUGE_RED)
            screen.blit(score_label, (WIDTH // 2 - score_label.get_width() // 2, 95))

        # 스코어 보드
        screen.blit(font.render(f"1P: {p1_score}", True, WHITE), (TABLE_X, 40))
        screen.blit(font.render(f"2P: {p2_score}", True, WHITE), (TABLE_X + TABLE_W - 130, 40))

        if is_waiting_serve and not game_over and not is_out_text_active:
            guide_p1 = "1P | Move: E(Up) D(Down) S(Left) F(Right) | Hit: Z | Spike: Hold LShift"
            guide_p2 = "2P | Move: Arrow Keys | Hit: Enter | Spike: Hold RShift"
            screen.blit(small_font.render(guide_p1, True, SCORE_P1_COLOR), (WIDTH // 2 - 400, HEIGHT - 70))
            screen.blit(small_font.render(guide_p2, True, GAUGE_RED), (WIDTH // 2 - 340, HEIGHT - 40))

        # 최종 승리 화면
        if game_over:
            win_label = winner_font.render(f"★ {winner} Victory! ★", True, GAUGE_YELLOW)
            retry_label = small_font.render("Press 'R' to Restart / Press 'Q' to Quit Game", True, WHITE)
            screen.blit(win_label, (WIDTH // 2 - win_label.get_width() // 2, HEIGHT // 2 - 80))
            screen.blit(retry_label, (WIDTH // 2 - retry_label.get_width() // 2, HEIGHT // 2 + 50))

        pygame.display.update()
        clock.tick(60)
        
        # ★ 핵심: 웹 브라우저 이벤트 루프에 제어권을 양보하여 화면이 멈추지 않게 함
        await asyncio.sleep(0)

    pygame.quit()

# ★ 비동기 루프 실행
asyncio.run(main())