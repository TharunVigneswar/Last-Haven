import pygame
import random
import json
import math
import pathlib as Path

pygame.init()

W, H = 1280, 800
MIN_W, MIN_H = 1000, 650
window = pygame.display.set_mode((W, H), pygame.RESIZABLE)


screen = pygame.Surface((W, H)).convert()
pygame.display.set_caption("LAST HAVEN | Colony Survival")
clock = pygame.time.Clock()

SAVE_FILE = Path.home() / ".last_haven_save.json"

BG = (15, 22, 17)
PANEL = (24, 34, 40)
PANEL_LIGHT = (32, 45, 51)
BORDER = (54, 71, 76)
WHITE = (237, 243, 239)
MUTED = (153, 172, 174)
GREEN = (117, 203, 135)
DARK_GREEN = (40, 82, 57)
CYAN = (94, 208, 204)
YELLOW = (240, 193, 100)
RED = (235, 103, 99)
BLUE = (111, 181, 226)
ORANGE = (235, 150, 93)
PURPLE = (187, 151, 231)

FONT = pygame.font.SysFont("segoeui", 17)
SMALL = pygame.font.SysFont("segoeui", 14)
MEDIUM = pygame.font.SysFont("segoeui", 21, bold=True)
LARGE = pygame.font.SysFont("segoeui", 32, bold=True)
TITLE = pygame.font.SysFont("segoeui", 56, bold=True)

COLS, ROWS = 15, 10
TILE = 42
MAP_X, MAP_Y = 238, 170

BUILDINGS = {
    "Shelter": {
        "cost": {"Wood": 12, "Scrap": 3},
        "color": (177, 130, 88)
    },
    "Farm": {
        "cost": {"Wood": 8, "Scrap": 2},
        "color": (115, 176, 98)
    },
    "Water": {
        "cost": {"Wood": 8, "Scrap": 4},
        "color": (88, 169, 208)
    },
    "Campfire": {
        "cost": {"Wood": 6},
        "color": (232, 139, 75)
    },
    "Defences": {
        "cost": {"Wood": 10, "Scrap": 7},
        "color": (177, 130, 88)
    }
}

resources = {}
day = 1
population = 5
health = 100
morale = 75
buildings = {}
trees = set()
rocks = set()
paths = set()
log = []
log_scroll = 0

page = "menu"
selected_building = None
alert = None
alert_title = ""
alert_color = RED
buttons = []
mouse_logical_pos = (0, 0)

def get_viewport(window_size):
    
    window_w, window_h = max(1, window_size[0]), max(1, window_size[1])
    scale = min(window_w / W, window_h / H)
    view_w = max(1, int(W * scale))
    view_h = max(1, int(H * scale))
    view_x = (window_w - view_w) // 2
    view_y = (window_h - view_h) // 2
    return pygame.Rect(view_x, view_y, view_w, view_h)

def window_to_game_pos(pos, window_size):

    viewport = get_viewport(window_size)
    if not viewport.collidepoint(pos):
        return (-1, -1)
    x = int((pos[0] - viewport.x) * W / viewport.width)
    y = int((pos[1] - viewport.y) * H / viewport.height)
    return (max(0, min(W - 1, x)), max(0, min(H - 1, y)))
won = False
game_over = False
message = ""

def text(surface, value, x, y, font=FONT, color=WHITE):
    image = font.render(str(value), True, color)
    surface.blit(image, (int(x), int(y)))
    return image.get_rect(topleft=(int(x), int(y)))

def centered(surface, value, rect, font=FONT, color=WHITE):
    image = font.render(str(value), True, color)
    surface.blit(image, image.get_rect(center=rect.center))

def panel(rect, color=PANEL, radius=12, outline=BORDER):
    pygame.draw.rect(screen, color, rect, border_radius=radius)
    pygame.draw.rect(screen, outline, rect, 1, border_radius=radius)

def draw_button(rect, label, action, color=PANEL_LIGHT, accent=None):
    hovered = rect.collidepont(mouse_logical_pos)
    fill = tuple(min(255, c + 9) for c in color) if hovered else color
    pygame.draw.rect(screen, fill, rect, border_radius=8)
    pygame.draw.rect(screen, accent or BORDER, rect, 1, border_radius=8)
    centered(screen, label, rect, FONT, WHITE)
    buttons.append((rect, action))

def add_log(value, category="normal"):
    log.append({
        "day": day,
        "text": value,
        "category": category
    })
    if len(log) > 300:
        del log[:-300]

def set_alert(title, value, color=RED):
    global alert, alert_title, alert_color
    alert_title = title
    alert = value
    alert_color = color

def notify(value, category="normal"):
    add_log(value, category)
    if category in {"danger", "warning", "success"}:
        colors = {
            "danger": RED,
            "warning": YELLOW,
            "success": GREEN
        }
        titles = {
            "danger": "COLONY DANGER",
            "warning": "COLONY WARNING",
            "success": "DISCOVERY"
        }
        set_alert(titles[category], value, colors[category])

def new_world():
    global resources, day, population, health, morale
    global buildings, trees, rocks, paths, log, log_scroll
    global selected_building, alert, won, game_over, page

    resources = {
        "Food": 45,
        "Water": 45,
        "Wood": 30,
        "Scrap": 15
    }

    day = 1
    population = 5
    health = 100
    morale = 75

    buildings = {
        (7, 5): "Shelter",
        (6, 5): "Campfire"
    }

    trees = set()
    rocks = set()
    paths = set()

    random.seed()

    for x in range(COLS):
        for y in range(ROWS):
            if abs(2 - 7) <= 2 and abs(y - 5) <= 2:
                continue

        roll = random.random()
        if roll < 0.12:
            trees.add((x, y))
        elif roll < 0.16:
            rocks.add((x, y))

    for x in range(4, 11):
        paths.add((x, 6))

    log = []
    log_scroll = 0
    selected_building = None
    alert = None
    won = False
    game_over = False
    page = "game"

    add_log("Your colony has established a settlement.")
    add_log("Gather supplies and prepare for the unknown.")
    add_log("Survive untill Day 30 to secure the future.")

def can_afford(cost):
    return all(resources.get(item, 0) >= amount
               for item, amount in cost.items())

def spend(cost):
    if not can_afford(cost):
        return False
    for item, amount in cost.items():
        resources[item] -= amount
    return True

def save_game():
    data = {
        "resources": resources,
        "day": day,
        "population": population,
        "health": health,
        "morale": morale,
        "buildings": [
            [x, y, name] for (x, y), name in buildings.items()
        ],
        "trees": [list(p) for p in trees],
        "rocks": [list(p) for p in rocks],
        "paths": [list(p) for p in paths],
        "log": log,
        "won": won,
        "game_over": game_over
    }

    try:
        SAVE_FILE.write_text(json.dumps(data, indent=2))
        add_log("Colony progress saved.")
        return True
    except (OSError, TypeError):
        set_alert("SAVE FAILED", "Could not save the colony.", RED)
        return False

def load_game():
    global resources, day, population, health, morale
    global buildings, trees, rocks, paths, log, won, game_over
    global page, selected_building, alert

    try:
        data = json.loads(SAVE_FILE.read_text())

        resources = data["resources"]
        day = data["day"]
        population = data["population"]
        health = data["health"]
        morale = data["morale"]

        buildings = {
            (int(x), int(y)): name
            for x, y, name in data["buildings"]
        }

        trees = {tuple(p) for p in data.get("trees", [])}
        rocks = {tuple(p) for p in data.get("rocks", [])}
        paths = {tuple(p) for p in data.get("paths", [])}

        log = data.get("log", [])
        log = [
            item if isinstance(item, dict)
            else {"day": day, "text": str(item), "category": "normal"}
            for item in log
        ]

        won = data.get("won", False)
        game_over = data.get("game_over", False)
        selected_building = None
        alert = None
        page = "end" if won or game_over else "game"
        add_log("Save colony loaded.")
        return True

    except (OSError, ValueError, KeyError, TypeError):
        set_alert("NO SAVE FOUND", "Start a new colony to begin.", YELLOW)
        return False

def gather():
    choices = ["Wood", "Scrap", "Food", "Water"]
    item = random.choices(choices, weights=[35, 25, 20, 20])[0]
    amount = random.randint(4, 9)
    resources[item] += amount
    add_log(f"Scavengers collected {amount {item.lower()}}.")
    return 

def hunt():
    global health
    amount = random.randint(6, 13)
    resources["Food"] += amount

    if random.random() < 0.15:
        health = max(0, health - 5)
        notify(f"A hunting accident cost 5 health. Food +{amount}.", "warning")
    else:
        add_log(f"The hunting party returned with {amount} food.")
    check_game_over()

def explore():
    global health, morale, population

    outcome = random.random()

    if outcome < 0.40:
        item = random.choice(["Food", "Water", "Wood", "Scrap"])
        amount = random.randint(7, 15)
        resources[item] += amount
        notify(f"Explorers found {amount} {item.lower()}!!", "success")

    elif outcome < 0.62:
        health = max(0, health - 8)
        notify("Explorers encountered danger. Health -8", "danger")

    elif outcome < 0.78:
        morale = min(100, morale + 10)
        notify("The team returned with hopeful news. Morale +10", "success")

    elif outcome < 0.88 and population < 12:
        population += 1
        notify(f"A survivor joined your colony!!", "success")

    else:
        add_log("The expedition found nothing useful.")

    check_game_over()

def rest_colony():
    global health, morale

    health = min(100, health + 8)
    morale = min(100, morale + 10)
    add_log("The colony rested. Health and morale imporved.")

def build_at(x, y):
    global selected_building

    name = selected_building
    if not name:
        return
    
    if not (0 <= x < COLS and 0 <= y < ROWS):
        return

    if (x, y) in buildings:
        add_log("That tile is already occupied.", "warning")
        return

    if (x, y) in trees or (x, y) in rocks:
        add_log("Clear the obstacle before building there", "warning")
        return

    cost = BUILDINGS[name]["cost"]

    if not can_afford(cost):
        missing = [
            f"{item} {amount - resources[item]}"
            for item, amount in cost.items()
            if resources[item] < amount
        ]
        add_log("Not enough supplies: " + ", ".join(missing), "warning")
        return

    if not spend(cost):
        return

    buildings[(x, y)] = name
    selected_building = None
    add_log(f"{name} constructed at tile {x + 1}, {y + 1}.", "success")
    set_alert("BUILDING COMPLETE", f"{name} has been added to your colony.", GREEN)

def check_game_over():
    global game_over, page

    if health <= 0 or morale <= 0:
        game_over = True
        page = "end"
        set_alert("COLONY LOST", "Your colony could not survive. Start a new settlement to try again.", RED)

def random_event():
    global health, morale, population

    event = random.random()

    if event < 0.16:
        damage = max(2, 12 - len([b for b in buildings.values() if b == "Defences"]) * 3)
        health = max(0, health - damage)
        notify(f"A severe storm struck the colony. Health -{damage}.", "danger")

    elif event < 0.30:
        defences = sum(1 for b  in buildings.values() if b == "Defences")
        damage = max(0, 12 - defences * 4)
        lost = min(resources["Food"], random.randint(2, 8))
        resources["Food"] -= lost
        health = max(0, health - damage)

        if damage == 0:
            notify("Raiders ere driven away by your defenced!!", "success")
        else:
            notify(f"Raiders stole {lost} food. Health -{damage}.", "danger")

    elif event < 0.42:
        health = max(0, health - 7)
        notify("Sickness spread through the colony. Health -7.", "danger")

    elif event < 0.53:
        item = random.choice(["Food", "Water", "Wood", "Scrap"])
        amount = random.randint(5, 12)
        resources[item] += amount
        notify(f"A passing trader left {amount} {item.lower()} in exchange for supplies.", "success")

    elif event < 0.63:
        resources["Scrap"] += 6
        notify("Scouts discovered an abandoned suply cache. Scrap +6", "success")

    elif event < 0.71:
        if resources["Wood"] >= 3:
            resources["Wood"] -= 3
            notify("A small fire damaged stored wood. Wood -3.", "warning")
        else:
            health = max(0, health - 5)
            notify("A fire broke out near the shelter. Health -5.", "danger")

    elif event < 0.80:
        morale = min(100, morale + 8)
        notify("The colony celebrated a small victory. Morale +8.", "success")

    else:
        add_log("The day has passed without a major incident.")

def end_day():
    global day, health, morale, page, won, alert

    if page != "game" or alert is not None:
        return

    farms = sum(1 for b in buildings.values() if b == "Farm")
    collectors = sum(1 for b in buildings.values() if b == "Water")
    fires = sum(1 for b in buildings.values() if b == "Campfire")

    food_produced = farms * 5
    water_produced = collectors * 5

    resources["Food"] += food_produced
    resources["Water"] += water_produced

    if food_produced:
        add_log(f"Farms produced {food_produced} food.")

    if water_produced:
        add_log(f"Collectors produced {water_produced} water.")

    food_needed = population * 2
    water_needed = population * 2

    if resources["Food"] >= food_produced:
        resources["Food"] -= food_produced
    else:
        shortage = food_needed - resources["Food"]
        resources["Food"] = 0
        health = max(0, health - 8)
        morale = max(0, morale - 8)
        add_log(f"Food shortage! Missing {shortage} food.", "danger")

    if resources["Water"] >= water_produced:
        resources["Water"] -= water_produced
    else:
        shortage = water_needed - resources["Water"]
        resources["Water"] = 0
        health = max(0, health - 10)
        add_log(f"Water shortage! Missing {shortage} water.", "danger")

    if fires:
        health = min(100, health + min(3, fires))

    if len(buildings) > 3:
        morale = min(100, morale + 1)

    day += 1
    random_event()
    check_game_over()

    if not game_over and day > 30:
        won = True
        page = "end"
        set_alert("SURVIVAL ACHIEVED", "You colony survived 30 days. You built a new future!!", GREEN)

def draw_background():
    screen.fill(BG)

    for y in range(0, H, 4):
        shade = 2 if (y //4) % 2 == 0 else 0
        pygame.drae.line(
            screen,
            (BG[0] + shade, BG[1] + shade, BG[2] + shade),
            (0, y), (W, y)
        )

def draw_header():
    text(screen, "LAST HAVEN", 22, 17, LARGE)
    text(screen, "COLONY SURVIVAL", 25, 52, SMALL, MUTED)

    pygame.draw.line(screen, BORDER, (22, 76), (W - 22, 76), 1)

    text(screen, f"DAY {day:02}", 250, 25, MEDIUM, CYAN)
    text(screen, f"{population} SURVIVORS", 350, 29, SMALL, MUTED)

    resource_info = {
        ("Food", "●", YELLOW)
        ("Water", "●", BLUE)
        ("Wood", "▰", ORANGE)
        ("Scrap", "◆", MUTED)
    }

    start_x = 500
    for index, (name, symbol, color) in enumerate(resource_info):
        x = start_x + index * 130
        pygame.draw.rect(screen, PANEL, (x, 14, 120, 47), border_radius=9)
        text(screen, symbol, x + 10, 23, MEDIUM, color)
        text(screen, name.upper(), x + 30, 18, SMALL, MUTED)
        text(screen, resources[name], x + 30, 35, MEDIUM, WHITE)

    draw_button(pygame.Rect(1050, 18, 88, 38), "SAVE", "save", accent=GREEN)
    draw_button(pygame.Rect(1145, 18, 112, 38), "MENU", "menu")

def draw_meter(x, y, width, label, value, color):
    text(screen, label, x, y, SMALL, MUTED)
    pygame.draw.rect(screen, (48, 62, 66), (x, y + 21, width, 8), border_radius=4)
    fill = int(width * max(0, min(100, value)) / 100)
    if fill:
        pygame.draw.rect(screen, color, (x, y + 21, fill, 8), border_radius=4)
    text(screen, f"{value}%", x + width + 8, y + 13, SMALL, WHITE)

def draw_left_panel():
    rect = pygame.Rect(20, 95, 200, 600)
    panel(rect)

    text(screen, "COLONY STATUS", 35, 110, MEDIUM)
    draw_meter(35, 147, 130, "HEALTH", health, GREEN if health > 40 else RED)
    draw_meter(35, 147, 130, "MORALE", morale, CYAN if morale > 40 else RED)

    pygame.draw.lin(screen, BORDER, (35, 250), (205, 250))

    text(screen, "ACTIONS", 35, 265, MEDIUM)

    action = [
        ("Gather supplies", "gather", GREEN),
        ("Hunt for food", "hunt", YELLOW),
        ("Explore ruins", "explore", BLUE),
        ("Rest colony", "rest", PURPLE)
    ]

    for i, (label, action, color) in enumerate(actions):
        r = pygame.Rect(34, 300 + i * 45, 170, 36)
        draw_button(r, label, action, accent=color)

    pygame.draw.line(screen, BORDER, (35, 492), (205, 492))
    text(screen, "BUILD MENU", 35, 505, MEDIUM)

    build_names = [
        ("Shelter", "SHELTER"),
        ("Farm", "FARM"),
        ("Water", "WATER"),
        ("Campfire", "FIRE"),
        ("Defences", "DEFENCES")
    ]

    for i, (name, label) in enumerate(build_names):
        y = 539 + i * 39
        r = pygame.Rect(34, y, 170, 32)
        chosen = selected_building == name
        fill = (48, 80, 65) if chosen else PANEL_LIGHT
        draw_button(r, ("✓ " if chosen else "+ ") + label,
                    "select:" + name, fill,
                    BUILDINGS[name]["color"])

def terrain_color(x, y):
    value = (x * 13 + y *7 + x * y * 3) % 5
    greens = [
        (70, 111, 72),
        (74, 116, 75),
        (78, 119, 78),
        (68, 108, 71),
        (82, 121, 78)
    ]
    return greens[value]

def draw_tree(rect):
    cx, cy = rect.centerx, rect.centery

    pygame.draw.ellipse(
        screen, (39, 71, 49),
        (cx - 17, cy + 5, 35, 17)
    )

    pygame.draw.ellipse(
        screen, (1-5, 82, 55),
        (cx - 3, cy - 2, 7, 19),
        border_radius=2
    )

    pygame.draw.circle(screen, (39, 91, 52), (cx, cy - 5), 15)
    pygame.draw.circle(screen, (51, 111, 61), (cx - 5, cy - 10), 10)
    pygame.draw.circle(screen, (65, 125, 68), (cx + 5, cy - 9), 9)
    pygame.draw.circle(screen, (90, 144, 76), (cx - 3, cy - 14), 5)

def draw_rock(rect):
    cx, cy = rect.center

    pygame.draw.ellipse(
        screen, (45, 65, 61),
        (cx - 15, cy + 5, 31, 12)
    )

    points = [
        (cx - 12, cy + 5),
        (cx - 10, cy - 5),
        (cx - 2, cy - 12),
        (cx + 10, cy - 8),
        (cx + 15, cy + 4),
        (cx + 8, cy + 10),
        (cx - 8, cy + 10)
    ]

    pygame.draw.polygon(screen, (117, 128, 119), points)
    pygame.draw.line(screen, (158, 169, 154),
                     (cx - 7, cy - 4), (cx - 1, cy - 9), 2)

def draw_building(rect, name):
    x, y, w, h = rect
    cx, cy =  x + w //2, y + h //2

    if name == "Shelter":
        pygame.dra.ellipse(screen, (46, 68, 52),
                           (x + 4, y + h - 11, w - 8, 13))

        body = pygame.Rect(x + 6, y + 14, w - 12, h - 21)
        pygame.draw.rect(screen, (151, 111, 75), body, border_radius=3)
        pygame.draw.rect(screen, (95, 69, 51), body, 2, border_radius=3)

        roof = [
            (x + 3, y + 17),
            (cx, y + 2),
            (x + w - 3, y + 17)
        ]
        pygame.draw.polygon(screen, (116, 79, 58), roof)
        pygame.draw.line(screen, (184, 138, 94),
                         (x + 8, y + 16), (cx, y + 5), 2)

        door = pygame.Rect(cx - 5, y + h - 20, 10, 15)
        pygame.draw.rect(screen, (71, 51, 39), door, border_radius=2)

        pygame.draw.rect(screen, (220, 184, 125),
                         (x + 9, y + 20, 7, 6), border_radius=1)

    elif name == "Farm":
        pygame.draw.rect(screen, (103, 76, 49),
                         (x + 4, y + 5, w - 8, h - 10),
                         border_radius=4)

        for i in range(4):
            yy = y + 10 + i * 7
            pygame.dra.line(screen, (164, 119, 69),
                            (x + 7, yy), (x + w - 7, yy), 2)

            for j in range(3):
                xx = x + 12 + j * 10
                pygame.draw.ellipse(screen, (87, 161, 83),
                                    (xx, yy - 4, 6, 8))
                pygame.draw.ellipse(screen, (143, 197, 101),
                                    (xx, yy - 4, 3, 5))

    elif name == "Water":
        pygame.draw.ellipse(screen, (53, 75, 76),
                            (x + 5, y + 7, w - 10, h - 10))

        pygame.draw.rect(screen, (128, 119, 94),
                        (cx - 12, cy - 8, 24, 24),
                        border_radius=4)

        pygame.draw.rect(screen, (81, 156, 190),
                        (cx - 9, cy - 5, 18, 18),
                        border_radius=3)

        pygame.draw.ellipse(screen, (137, 218, 228),
                            (cx - 7, cy - 5, 14, 5))

        pygame.draw.line(screen, (182, 178, 145),
                         (cx, cy - 10), (cx, cy - 16), 3)

    elif name == "Campfire":
        pygame.draw.ellipse(screen, (65, 65, 49),
                            (x + 4, y + 7, w - 8, h - 10))

        for angle in (0, 45, 90, 135):
            length = 19
            dx = math.cos(math.radians(angle)) * length / 2
            dy = math.sin(math.radians(angle)) * length / 2
            pygame.draw.line(screen, (115, 78, 47),
                             (cx - dx, cy - dy + 4),
                             (cx + dx, cy + dy + 4), 4)

        pygame.draw.circle(screen, (243, 119, 54), (cx, cy), 8)
        pygame.draw.circle(screen, (255, 197, 85), (cx, cy + 2), 5)
        pygame.draw.circle(screen, (255, 229, 145), (cx, cy + 3), 2)

    elif name == "Defences":
        pygame.draw.ellipse(screen, (45, 67, 51),
                            (x + 4, y + h - 10, w - 8, 12))
    
        pygame.draw.rect(screen, (117, 125, 116),
                         (x + 4, y + 10, w - 8, 14),
                         border_radius=3)

        for i in range(3):
            xx = x + 7 + i * 12
            pygame.draw.rect(screen, (161, 167, 152),
                             (xx, y + 8, 7, 8),
                             border_radius=1)

        pygame.draw.line(screen, (87, 98, 92),
                         (x + 7, cy), (x + w - 7, cy), 2)

def draw_colony_map():
    map_rect = pygame.Rect(
        MAP_X - 5, MAP_Y - 5,
        COLS * TILE + 10, ROWS * TILE + 10
    )
    panel(map_rect, (25, 40, 38), 10)

    mouse_x, mouse_y = mouse_logical_pos
    hovered_tile = None

    for y in range(ROWS):
        for x in range(COLS):
            rect = pygame.Rect(
                MAP_X + x * TILE,
                MAP_Y + y * TILE,
                TILE - 1, TILE - 1
            )

            pygame.draw.rect(screen, terrain_color(x, y), rect)
            
            if (x, y) in paths:
                pygame.draw.rect(screen, (139, 120, 87),
                                 rect.inflate(-4, -4), border_radius=3)
                pygame.draw.circle(screen, (157, 138, 101),
                                   (rect.centerx, rect.centery), 2)

            if (x, y) in trees:
                draw_tree(rect)

            elif (x, y) in rocks:
                draw_rock(rect)

            elif (x, y) in buildings:
                draw_building(rect, buildings[(x, y)])

            if rect.collidepoint(mouse_x, mouse_y):
                hovered_tile = (x, y)
                overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                overlay.fill((235, 246, 223, 45))
                screen.blit(overlay, rect.topleft)

                if selected_building:
                    pygame.draw.rect(screen, CYAN, rect, 2, border_radius=3)

    if hovered_tile:
        x, y = hovered_tile
        label = buildings.get((x, y), "Empty ground")
        if (x, y) in trees:
            label = "Tree"
        elif (x, y) in rocks:
            label = "Rock"

        text(screen, f"Tile {x + 1}, {y + 1}  ·  {label}",
                MAP_X, MAP_Y + ROWS * TILE + 12, SMALL, CYAN)
            
    if selected_building:
        text(screen, f"PLACEMENT MODE: {selected_building}",
             MAP_X + 220, MAP_Y + ROWS * TILE + 12, SMALL, CYAN)

def draw_building_info():
    x, y = MAP_X, 115
    text(screen, "YOUR SETTLEMENT", x, y, MEDIUM)
    text(screen, "Select a building, then click an empty tile.",
         x + 200, y + 4, SMALL, MUTED)

    if selected_building:
        info = BUILDINGS[selected_building]["cost"]
        parts = [f"{k}: {v}" for k, v in info.items()]
        text(screen, "Cost: " + "  ·  ". join(parts),
             x, y + 25, SMALL, MUTED)
    else:
        text(screen, "Build, gather supplies amd protect your survivors.",
             x, y + 25, SMALL, MUTED)

def wrap_text(value, font, max_width):
    words = value.split()
    lines = []
    current = ""

    for word in words:
        trial = word if not current else current + " " + word
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
                current = ""
            if font.size(word)[0] <= max_width:
                current = word
            else:
                piece = ""
                for char in word:
                    trial_piece = piece + char
                    if piece and font.size(trial_piece)[0] > max_width:
                        lines.append(piece)
                        piece = char
                    else:
                        piece = trial_piece
                current = piece

    if current:
        lines.append(current)

    return lines

def draw_log_panel():
    rect = pygame.Rect(900, 170, 357, 420)
    panel(rect)

    text(screen, "COLONY LOG", rect.x + 15, rect.y + 13, MEDIUM)
    text(screen, f"{len(log)} EVENTS", rect.right - 92,
         rect.y + 18, SMALL, MUTED)

    pygame.draw.line(screen, BORDER,
                     (rect.x + 14, rect.y + 43),
                     (rect.right - 14, rect.y + 43))

    content = pygame.Rect(rect.x + 14, rect.y + 52,
                          rect.width - 36, rect.height - 65)

    old_clip = screen.get_clip()
    screen.set_clip(content)

    entries = []
    for item in log:
        prefix = f"D{item.get("day", day):02}  "
        value = prefix + item.get("text", "")
        lines = wrap_text(value, SMALL, content.width - 6)
        color = {
            "danger": RED,
            "warning": YELLOW,
            "success": GREEN
        }.get(item.get("category", "normal"), MUTED)

        entries.append((lines, color))

    total_height = sum(len(lines) * 18 + 9 for lines, _ in entries)
    max_scroll = max(0, total_height - content.height)
    log_scroll = max(0, min(draw_log_panel.scroll, max_scroll))
    draw_log_panel.scroll = log_scroll

    yy = content.y - log_scroll

    for lines, colo in entries:
        for line in lines:
            text(screen, line, content.x, yy, SMALL, color)
            yy += 18
        yy +=9

    screen.set_clip(old_clip)

    if max_scroll > 0:
        bar = pygame.Rect(rect.right - 10, content.y, 4, content.height)
        pygame.draw.rect(screen, (45, 60, 63), bar, border_radius=2)

        thumb_h = max(24, int(content.height * content.height / total_height))
        thumb_y = content.y + int(
            (content.height - thumb_h) * log_scroll / max_scroll
        )
        pygame.draw.rect(screen, CYAN
                         (bar.x, thumb_y, bar.width, thumb_h),
                         border_radius=2)

draw_log_panel.scroll = 0

def draw_colony_summary():
    rect = pygame.Rect(900, 605, 357, 150)
    panel(rect)

    text(screen, "SETTLEMENT REPORT"), rect.x + 15