# full imports
import pygame, sys, random, cv2

# import specific methods
from pygame.locals import *
from datetime import datetime
from time import sleep, time
from warnings import filterwarnings
from os import listdir
from os.path import isdir

# filter warning
filterwarnings('ignore', category=DeprecationWarning)

# initiate sound and graphics
pygame.mixer.init()
pygame.init()

# Create FPS handler
clock = pygame.time.Clock()

# Resolution
width = 900
height = 700

# joystick

gameIcon = pygame.image.load("icons/gameIcon.png")
pygame.display.set_icon(gameIcon)

p1Pad = None
p2Pad = None

if pygame.joystick.get_count() > 0:
    p1Pad = pygame.joystick.Joystick(0)
    p1Pad.init()

if pygame.joystick.get_count() > 1:
    p2Pad = pygame.joystick.Joystick(0)
    p2Pad.init()

    p1Pad = pygame.joystick.Joystick(1)
    p1Pad.init()

# resolution tuple
res = (width, height)

firstEntry = True

# Game name
name = 'Sky Dash Battle'

# Setting up window
screen = pygame.display.set_mode(res)
pygame.display.set_caption(name)

# Sprite Groups
clouds = pygame.sprite.Group()
platforms = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
danger = pygame.sprite.Group()
players = pygame.sprite.Group()
seagulls = pygame.sprite.Group()
decorations = pygame.sprite.Group()
scanlineGroup = pygame.sprite.Group()

# text and screen background
BG = (52, 164, 235)
BG2 = (100, 100, 255)

# Invisible mouse
pygame.mouse.set_visible(False)

# Initial Player speed
PSD = 4

# player speed
PlayerSpeed = PSD

CHANCE = 32
# 1/32 = 3.125% chance of lava block

FPS = 45

# Calculating Players position relative to start
vec = pygame.math.Vector2

# extras
debug = True
scanlineBool = True
multiBool = False

# for startscreen
Exit = False


# Clouds Class
class Clouds(pygame.sprite.Sprite):
    # General settings
    def __init__(self, pos, img="backgroundObjects/cloud.png"):
        super().__init__()

        self.image = pygame.image.load(img)
        self.rect = self.image.get_rect()

        self.rect.center = pos

    # Make them move in the air
    def update(self):
        x, y = self.rect.center

        # if out of window then respawn ahead of widthspan
        if x < -self.image.get_width() - 10:
            random.seed(datetime.now())
            x = width + self.image.get_width() + 10
            y = random.randrange(0, height)

        # slowly drift backwards creating virtual effect
        x -= 1

        self.rect.center = (x, y)


# platform mechanism
class Platform(pygame.sprite.Sprite):
    # initial settings
    # asking Program if landable
    def __init__(self, Landable, image=None, dir="ground", surface=screen, sizeFactor=1):
        super().__init__()

        width, height = surface.get_size()

        # if there is no specific image then use random
        # if not landable then use lava block image.
        if image == None:
            plat_dir = listdir('platforms/' + dir)
            bad_dir = listdir('badObjects/' + dir)

            plat_max_len = len(plat_dir) - 1
            bad_max_len = len(bad_dir) - 1

            for item in plat_dir:
                if isdir(item):
                    plat_max_len -= 1

            for item in bad_dir:
                if isdir(item):
                    bad_max_len -= 1

            if Landable:
                self.image = pygame.image.load(
                    'platforms/' + dir + '/platform_' + str(random.randint(0, plat_max_len)) + '.png')
            else:
                self.image = pygame.image.load(
                    'badObjects/' + dir + '/badplat' + str(random.randint(0, bad_max_len - 1)) + '.png')
        else:
            self.image = pygame.image.load(image)

        if sizeFactor != 1:
            self.image = pygame.transform.scale(self.image, (
            self.image.get_width() // sizeFactor, self.image.get_height() // sizeFactor))

        # General settings
        self.rect = self.image.get_rect()
        self.rect.center = (
        random.randrange(width * 1.25, width * 2), random.randrange(height * 8 // 12, height * 5 // 6))
    # self.pos = vec((self.rect.center))


# Seagulls class
class Seagull(pygame.sprite.Sprite):
    # initial settings
    def __init__(self, dir="ground", surface=screen, image=None):
        super().__init__()

        width, height = surface.get_size()

        if image == None:
            self.image = pygame.image.load('badObjects/' + dir + '/air/seagull.png')
        else:
            self.image = pygame.image.load(image)

        self.rect = self.image.get_rect()
        self.rect.center = (random.randint(width, width * 2), random.randint(0, height * 5 // 24))

        self.x, self.y = self.rect.center

    # Update mechanism
    def update(self):
        self.x -= PlayerSpeed * 1.15
        self.rect.center = (self.x, self.y)

        if pygame.sprite.spritecollide(self, players, False):
            self.image = pygame.image.load("misc/explosion.png")
            self.rect = self.image.get_rect()
            self.rect.center = (self.x, self.y)

        # if seagull is out of screen then kill it
        if self.x < 0:
            all_sprites.remove(self)
            danger.remove(self)
            seagulls.remove(self)

            self.kill()


# Player class
class Player(pygame.sprite.Sprite):
    # initial settings
    def __init__(self, AIMode=False, sideLength=40, sizeFactor=1, name="Player1", surf=screen):
        super().__init__()
        self.sideLength = sideLength

        self.image = pygame.image.load("players/player2.png")
        self.image = pygame.transform.scale(self.image, (self.sideLength // sizeFactor, self.sideLength // sizeFactor))

        self.rect = self.image.get_rect()

        self.rect.center = (width // 2, 0)

        self.acc = 0
        self.relpos = vec(self.rect.center)

        self.name = name
        self.jumpstate = True
        self.dead = False
        self.AIMode = AIMode
        self.jumpGame = False

        if self.AIMode:
            self.jumpstate = False

        self.fric = -0.12
        self.vel = 0

        self.screen = surf

    def move(self):
        x, y = self.rect.center

        keys = pygame.key.get_pressed()

        if keys[K_RIGHT]:
            self.vel += PSD
        if keys[K_LEFT]:
            self.vel -= PSD

        x += self.vel

        self.rect.center = (x, y)

    # Jump mechanism
    def jump(self, jumpForce=20):

        x, y = self.rect.center

        # key mapping
        keys = pygame.key.get_pressed()
        mkeys = pygame.mouse.get_pressed()

        # Event handling
        if not self.AIMode:
            if keys[K_SPACE] or mkeys[0]:
                # jumping
                y -= jumpForce
            if p1Pad != None:
                if p1Pad.get_button(0):
                    y -= jumpForce
        else:
            y -= jumpForce

        # Updating position
        self.rect.center = (x, y)

    def AI(self):
        if pygame.sprite.spritecollideany(self, platforms):
            self.jumpstate = False

            collided_platform = pygame.sprite.spritecollide(self, platforms, False)[-1]
            next_platform = None


            # Calculate index number for collided platform
            index = 0
            for plat in platforms.sprites():
                if plat == collided_platform:
                    next_platform = platforms.sprites()[index + 1]
                    break
                index += 1

            distance = (next_platform.rect.midleft[0] - collided_platform.rect.midright[0])

            if distance <= 80 and self.rect.centery <= collided_platform.rect.midtop[0]:
                self.jumpstate = False
            elif distance <= 200 and self.rect.centery <= collided_platform.rect.midtop[0]:
                if self.rect.y <= 10:
                    self.jumpstate = False
            elif self.rect.centerx >= collided_platform.rect.midright[0] or self.rect.centery >= collided_platform.rect.midtop[1]:
                self.jumpstate = True


    # Gravity mechanics
    def gravity(self, gravityDecimal=0.5):

        x, y = self.rect.center

        # checking for collision
        # If not then continue falling and updating position
        if not pygame.sprite.spritecollide(self, platforms, False):
            y += self.acc
            self.acc += gravityDecimal

            self.rect.center = (x, y)
        # else stop and update position
        else:
            self.acc = 0
            self.rect.center = (x, y)

    # The Update mechanism
    def update(self, jumpForce=20, gravity=0.5):

        x, y = self.rect.midtop

        # Creating bounding box
        if x > width * 2//3:
            x = width * 2//3
        # Updating Position
        self.rect.midtop = (x, y)

        # Checking for collision
        if pygame.sprite.spritecollide(self, platforms, False):

            plats = pygame.sprite.spritecollide(self, platforms, False)
            plat = plats[-1]
            platx, platy = plat.rect.midtop

            plat_w = plat.image.get_width()
            # plat_h = plat.image.get_height()

            # If player collides with platform and is deep in the block
            # Then stop all motion except for jumping mechanism
            if y > platy and x > (platx + plat_w * 1 // 3) and x < (platx + plat_w * 2 // 3):
                self.jumpstate = False
                self.rect.midtop = (platx, y)
            else:
                self.jumpstate = True

        if pygame.sprite.spritecollide(self, danger, False):
            self.image = pygame.image.load("misc/explosion.png")
            self.image = pygame.transform.scale(self.image, (100, 100))

            self.rect = self.image.get_rect()
            self.rect.midtop = (x, y)

        # Updating relative position
        self.relpos.x += PlayerSpeed

        if self.jumpGame:
            self.move()

        if self.AIMode:
            self.AI()

        # If not in air allow jump mechanism
        if self.jumpstate:
            self.jump(jumpForce)

        # Running virtual gravity method
        self.gravity(gravity)


class PlatDecorations(pygame.sprite.Sprite):
    def __init__(self, platform, image=None, dir="ground", surface=screen, sizeFactor=1):
        super().__init__()

        if image != None:
            self.image = pygame.image.load(image)
        else:
            decor_max_len = len(listdir('decorations/' + dir)) - 1
            self.image = pygame.image.load(
                'decorations/' + dir + '/decor_' + str(random.randint(0, decor_max_len)) + '.png')

        if sizeFactor != 1:
            self.image = pygame.transform.scale(self.image, (
            self.image.get_width() // sizeFactor, self.image.get_height() // sizeFactor))

        if platform == None:
            print("Cannot summon decoration, specified platform is None")
            sys.exit()

        self.rect = self.image.get_rect()
        self.platform = platform

        self.surface = surface

        self.image.set_alpha(200)

    def update(self):
        self.rect.midbottom = self.platform.rect.midtop
        x, y = self.rect.midbottom

        self.rect.midbottom = (x, y + self.image.get_height() * 1 // 6)


class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()


class SpiderBoss(pygame.sprite.Sprite):
    def __init__(self, surface=screen):
        super().__init__()

        self.alphaVal = 0

        width, height = surface.get_size()

        self.image = pygame.image.load("bosses/spider/SpiderBoss.png")

        self.rect = self.image.get_rect()
        self.rect.center = (width // 2, height * 2)

        self.entry = False

    def opening(self):
        self.image.set_alpha(self.alphaVal)

        if self.alphaVal < 254:
            self.alphaVal += 1


class Player2(Player):
    def __init__(self, surf, sizeFactor=1, name="Player2", AI_Mode=False, sideLength=40):
        super().__init__()

        self.sideLength = sideLength

        self.image = pygame.image.load("players/player.png")
        self.image = pygame.transform.scale(self.image, (self.sideLength // sizeFactor, self.sideLength // sizeFactor))

        self.rect = self.image.get_rect()

        self.rect.center = (width // 2, 0)

        self.name = name
        self.AIMode = AI_Mode
        self.screen = surf

        if self.AIMode:
            self.jumpstate = False

    def jump(self, jumpForce=20):
        x, y = self.rect.center

        # key mapping
        keys = pygame.key.get_pressed()

        # Event handling
        if not self.AIMode:
            if keys[K_w]:

                # jumping
                y -= jumpForce
            elif p2Pad != None:
                if p2Pad.get_button(0):
                    y -= jumpForce
        else:
            y -= jumpForce

        # Updating position
        self.rect.center = (x, y)

    def move(self):
        x, y = self.rect.center

        keys = pygame.key.get_pressed()

        if keys[K_d]:
            x += PSD
        if keys[K_a]:
            x -= PSD

        self.rect.center = (x, y)

    pass


class PlayerTag(pygame.sprite.Sprite):
    def __init__(self, player, number):
        super().__init__()

        font = pygame.font.Font("fonts/pixelart.ttf", 40)

        self.image = font.render(number, BG2, (55, 255, 55))

        self.player = player

        self.rect = self.image.get_rect()
        self.rect.midbottom = self.player.rect.midtop

    def update(self):
        self.rect.midbottom = self.player.rect.midtop


# Levels Class
class Level():
    def __init__(self, bg, spriteDirs, song, startblock, factor=1, playerStartSpeed=PSD, moveBool=False, gravity=0.5, jumpForce=20, name="Unknown Level", diff="easy"):

        self.bg = bg
        self.factor = factor

        self.diff = diff

        self.name = name

        if self.bg != None:
            self.noBG = False
            self.bg = "backgrounds/" + bg
        else:
            self.noBG = True
            self.bg = "backgrounds/Unknown.png"

        self.bgSong = song

        self.platDir, self.cloud = spriteDirs

        self.jumpForce = jumpForce
        self.gravity = gravity

        self.psd = playerStartSpeed
        self.moveBool = moveBool
        self.startblock = startblock

    def loadBG(self, surf=screen):
        self.image = pygame.image.load(self.bg)
        self.image = pygame.transform.scale(self.image, surf.get_size())

        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)


class CoopLevel():
    def __init__(self, backgrounds, spriteDir, startblock, song, factor=1, gravity=0.5, jumpForce=20,
                 PlayerStartSpeed=PSD, moveBool=False, name="Unknown Level", diff="easy"):
        self.bg1, self.bg2 = backgrounds
        self.bgSong = song

        self.name = name

        self.bg1 = "backgrounds/dual-BGs/" + self.bg1
        self.bg2 = "backgrounds/dual-BGs/" + self.bg2

        self.startblock = startblock

        self.diff = diff

        self.factor = factor

        self.platDir = spriteDir
        self.psd = PlayerStartSpeed

        self.moveBool = moveBool

        self.gravity = gravity
        self.jumpForce = jumpForce

    def loadBG(self, size1, size2):
        self.image1 = pygame.image.load(self.bg1)
        self.image1 = pygame.transform.scale(self.image1, size1)

        self.image2 = pygame.image.load(self.bg2)
        self.image2 = pygame.transform.scale(self.image2, size2)

        self.rect1 = self.image1.get_rect()
        self.rect2 = self.image2.get_rect()

        self.rect1.topleft = self.rect2.topleft = (0, 0)


class Line(pygame.sprite.Sprite):
    def __init__(self, thickness, alpha, color, pos):
        super().__init__()

        self.alpha = alpha

        self.image = pygame.Surface((screen.get_width(), thickness))
        self.image.fill(color)
        self.image.set_alpha(self.alpha)

        self.rect = self.image.get_rect()
        self.rect.topleft = pos

class Text(pygame.sprite.Sprite):
    def __init__(self, str, BG_FG_Color, script, pos):
        self.image = script.render(str, BG_FG_Color[0], BG_FG_Color[1])

        self.rect = self.image.get_rect()
        self.rect.center = pos

levels = [
    Level("earth.png", ("space", None), "neon-run.ogg", "platform_5.png", 10, 11, False, 0.15, 10, "Orbital Strike"),
    Level("neon-city.png", ("neon", None), "extsong.ogg", "platform_4.png", 10, 15, False, 1, 30, "Neon City"),
    Level("neon-landscape.png", ("neon", None), "neon-scape.ogg", "platform_4.png", 7, 5, False, 1, 30, "Neon outscape"),
    Level("volcano-dash.png", ("ground", "cloud.png"), "lava-run.ogg", "platform_5.png", 11, 5, False, 1, 30, "Huanuna Island"),
    Level("planet-run.png", ("ground", "cloud.png"), "planet-run.ogg", "platform_5.png", 11, 7, False, 1, 30, "Exo Dash"),
    Level("candyland.png", ("candy", None), "candyland.ogg", "platform_1.png", 11, 5, False, 1, 30, "Candyland"),
    Level("overworld.png", ("ground", None), "overworld.ogg", "platform_5.png", 11, 5, False, 1, 30, "Overworld"),
    Level("pyramids.png", ("sand", "cloud.png"), "pyramid.ogg", "platform_0.png", 11, 5, False, 1, 30, "The Pyramids"),
    Level("jungle.png", ("jungle", None), "jungle.ogg", "platform_5.png", 11, 5, False, 1, 30, "The Amazon Jungle")
]

multiplayerLevels = [
    CoopLevel(("earthdual1.png", "earthdual2.png"), "space", "platform_5.png", "dual-BGMs/dual.ogg", 10, 0.3, 15,
              name="Satellite in Orbit"),
    CoopLevel(("neon-dual1.png", "neon-dual2.png"), "neon", "platform_4.png", "dual-BGMs/neon-dual.ogg", 10, 1, 30,
              name="Neon City"),
    CoopLevel(("mars-dual1.png", "mars-dual2.png"), "space", "platform_5.png", "dual-BGMs/mars-dual.ogg", 10, 0.3, 15,
              name="The red planet"),
    CoopLevel(("super-dual1.png", "super-dual2.png"), "neon", "platform_4.png", "dual-BGMs/super-dual.ogg", 10, 1, 30,
              name="Microchip"),
    CoopLevel(("nebula-dual1.png", "nebula-dual2.png"), "neon", "platform_4.png", "dual-BGMs/nebula-dual.ogg", 10, 1,
              30, name="The Nebula\'s hidden layer"),
    CoopLevel(("exo-dual1.png", "exo-dual2.png"), "ground", "platform_5.png", "dual-BGMs/planet-dual.ogg", 10, 1, 30,
              name="Exo-Planet run"),
    CoopLevel(("candy-dual1.png", "candy-dual2.png"), "candy", "platform_1.png", "dual-BGMs/candy-dual.ogg", 10, 1, 30,
              name="Sugar Rush"),
    CoopLevel(("pyramids1.png", "pyramids2.png"), "sand", "platform_0.png", "dual-BGMs/pyramid-run.ogg", 10, 1, 30,
              name="Pyramid Chase"),
    CoopLevel(("AI-Demo1.png", "AI-Demo2.png"), "space", "platform_5.png", "dual-BGMs/ai-dual.ogg", 10, 0.3, 15,
              name="AI Demo")
]


def scanlines():
    if scanlineBool:
        thickness = 1
        for i in range(screen.get_height()):
            if i % (thickness * 2) == 0:
                scanlineGroup.add(Line(thickness, 100, (0, 0, 0), (0, i)))


scanlines()

def returnFrames(src, size):
    slides = cv2.VideoCapture(src)
    imageList = []

    while True:
        ret, frame = slides.read()
        if not ret:
            break

        shape = frame.shape[1::-1]
        img = pygame.image.frombuffer(frame.tobytes(), shape, "BGR")
        img = pygame.transform.scale(img, size)
        imageList.append(img)

    slides.release()
    return imageList

loading = pygame.image.load("backgrounds/loading.png")
loading = pygame.transform.scale(loading, res)

screen.blit(loading, (0, 0))
pygame.display.update()

lvlSelect_Anim = returnFrames("backgrounds/levelSelect.gif", res)
startup_1 = returnFrames("backgrounds/startup-1.gif", res)
startup_2 = returnFrames("backgrounds/startup-2.gif", res)


def levelSelect(list, func):

    font = pygame.font.Font("fonts/pixelart.ttf", 20)

    fontcolor = (64, 125, 120)

    levelMenu = pygame.Surface((screen.get_width() * 2 // 3, screen.get_height()))

    menuRect = levelMenu.get_rect()
    menuRect.topleft = (screen.get_width() // 3, 0)


    cursor = font.render(">", BG2, (55, 255, 55))
    cursorRect = cursor.get_rect()
    cursorRect.topleft = (0, 0)

    prevWin = pygame.Surface((screen.get_width() // 3 - 20, screen.get_height() // 4))
    prevRect = prevWin.get_rect()
    prevRect.topleft = (10, screen.get_height() // 4)

    lineList = []
    bgList = []
    diffList = []

    p1 = font.render("Player 1:", BG2, fontcolor)
    p2 = font.render("Player 2:", BG2, fontcolor)

    header = font.render("AI On/Off", BG2, (131, 214, 153))

    p1On = font.render("On", BG2, (55, 255, 55))
    p1Off = font.render("Off", BG2, (55, 255, 55))

    p2On = font.render("On", BG2, (55, 255, 55))
    p2Off = font.render("Off", BG2, (55, 255, 55))

    p1_state = [True, False]
    p2_state = [True, False]

    p1Rect = p1.get_rect()
    p2Rect = p2.get_rect()

    headerRect = header.get_rect()

    p1OnRect = p1On.get_rect()
    p1OffRect = p1Off.get_rect()

    p2OnRect = p2On.get_rect()
    p2OffRect = p2Off.get_rect()

    p1Itr = 0
    p2Itr = 0

    i = 0
    for level in list:
        tmp = font.render(level.name, BG2, fontcolor)
        tmpRect = tmp.get_rect()

        tmpRect.topleft = (20, i * tmp.get_height() + 5)

        diff = font.render(level.diff, BG2, (152, 32, 32))
        diffRect = diff.get_rect()

        lineList.append((tmp, tmpRect, level))
        diffList.append((diff, diffRect))

        if not multiBool:
            image = pygame.image.load(level.bg)
            image = pygame.transform.scale(image, prevWin.get_size())

            rect = image.get_rect()
            rect.topleft = (0, 0)

            bgList.append((image, rect))
        else:
            image = pygame.image.load(level.bg1)
            image = pygame.transform.scale(image, prevWin.get_size())

            rect = image.get_rect()
            rect.topleft = (0, 0)

            bgList.append((image, rect))

        i += 1

    # clear rubish from screen
    screen.fill((0, 0, 0))

    itr = 0
    row = 0

    itrRow = [p1Itr, p2Itr]

    run = True

    mainLevel = None

    index = 0

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:

                keys = pygame.key.get_pressed()

                if keys[K_UP]:
                    if itr <= 0:
                        itr = len(lineList) - 1
                    else:
                        itr -= 1
                    break
                if keys[K_DOWN]:
                    if itr >= len(lineList) - 1:
                        itr = 0
                    else:
                        itr += 1
                    break

                if keys[K_RETURN]:

                    if multiBool:
                        mainLevel = level
                        run = False
                        break
                    else:
                        func(level)

                    startScreen()
                    break
                if keys[K_ESCAPE]:
                    startScreen()
                    break



        tmp, lnRect, level = lineList[itr]
        bgImage, bgRect = bgList[itr]
        diff, diffRect = diffList[itr]

        diffRect.topleft = prevRect.bottomleft

        cursorRect.midright = lnRect.midleft

        if index >= len(lvlSelect_Anim) - 1:
           index = 0
           continue
        else:
           index += 1

        bg = lvlSelect_Anim[index]
        screen.blit(bg, (0, 0))

        levelMenu.fill((0, 0, 0))
        levelMenu.set_alpha(150)

        prevWin.blit(bgImage, bgRect)
        screen.blit(diff, diffRect)

        for line in lineList:
            lineIMG, lineRect, tmp = line
            levelMenu.blit(lineIMG, lineRect)

        levelMenu.blit(cursor, cursorRect)
        screen.blit(levelMenu, menuRect)
        screen.blit(prevWin, prevRect)

        scanlineGroup.draw(prevWin)
        scanlineGroup.draw(screen)

        pygame.display.update()
        clock.tick(30)

    run = True
    if multiBool:
        index = 0
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    keys = pygame.key.get_pressed()

                    if keys[K_ESCAPE]:
                        levelSelect(list, func)
                        break
                    if keys[K_RETURN]:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()

                        pygame.mixer.music.load("songs/" + mainLevel.bgSong)
                        pygame.mixer.music.play(-1)

                        func(mainLevel, p1_state[itrRow[0]], p2_state[itrRow[1]])
                        break

                    if keys[K_DOWN]:
                        row += 1
                        break

                    if keys[K_UP]:
                        row -= 1
                        break

                    if keys[K_RIGHT]:
                        itrRow[row] += 1
                        break

                    if keys[K_LEFT]:
                        itrRow[row] -= 1
                        break

            if itrRow[row] < 0:
                itrRow[row] = 1

            if itrRow[row] > 1:
                itrRow[row] = 0

            if row < 0:
                row = 1

            elif row > 1:
                row = 0

            p1Rect.center = (screen.get_width() // 3, screen.get_height() // 2 - 10)
            p2Rect.center = (screen.get_width() // 3, screen.get_height() // 2 + 10)

            headerRect.center = (screen.get_width() // 2, screen.get_height() // 2 - 50)

            p1OnRect.center = (screen.get_width() * 2 // 3, screen.get_height() // 2 - 10)
            p2OnRect.center = (screen.get_width() * 2 // 3, screen.get_height() // 2 + 10)

            p1OffRect.center = p1OnRect.center
            p2OffRect.center = p2OnRect.center



            if index >= len(lvlSelect_Anim) - 1:
                index = 0
                continue
            else:
                index += 1

            bg = lvlSelect_Anim[index]
            screen.blit(bg, (0, 0))

            if p1_state[itrRow[0]]:
                screen.blit(p1On, p1OnRect)
            else:
                screen.blit(p1Off, p1OffRect)

            if p2_state[itrRow[1]]:
                screen.blit(p2On, p2OnRect)
            else:
                screen.blit(p2Off, p2OffRect)

            if row == 0:
                cursorRect.midright = p1OnRect.midleft
            elif row == 1:
                cursorRect.midright = p2OnRect.midleft

            screen.blit(p1, p1Rect)
            screen.blit(p2, p2Rect)

            screen.blit(cursor, cursorRect)
            screen.blit(header, headerRect)

            scanlineGroup.draw(screen)
            pygame.display.update()
            clock.tick(30)
def test_level():
    base_plat = Platform(True, "platforms/ground/platform_5.png", None)
    base_plat.image = pygame.transform.scale(base_plat.image, (base_plat.image.get_width() * 3, base_plat.image.get_height() * 2))

    base_plat.rect = base_plat.image.get_rect()
    base_plat.rect.midleft = (0, screen.get_height())

    testPlayer = Player()
    testPlayer.jumpGame = True

    testPlayer.rect.center = (screen.get_width()//2, 0)

    players.add(testPlayer)

    for sprite in platforms:
        platforms.remove(sprite)
        sprite.kill()

    platforms.add(base_plat)

    bg = pygame.image.load("backgrounds/startup-1.gif")
    bg = pygame.transform.scale(bg, res)

    pygame.mixer.music.load("songs/Extras/south_island.ogg")
    pygame.mixer.music.play(-1)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                key = pygame.key.get_pressed()
                if key[K_ESCAPE]:
                    startScreen()
                    break

        screen.blit(bg, (0, 0))

        players.update()

        players.draw(screen)
        platforms.draw(screen)


        scanlineGroup.draw(screen)

        pygame.display.update()
        clock.tick(FPS)


def main(tmpLvl):
    if tmpLvl.noBG:
        tmpLvl.bg = None

    if tmpLvl.bg != None:
        tmpLvl.loadBG()

    # Creating background clouds
    if tmpLvl.cloud != None:
        for i in range(20):
            new_cloud = Clouds((random.randrange(0, width), random.randrange(0, height)), "backgroundObjects/" + tmpLvl.cloud)

            if not pygame.sprite.spritecollide(new_cloud, clouds, False):
                clouds.add(new_cloud)

    pygame.mixer.music.load("songs/" + tmpLvl.bgSong)

    # Importing global variables
    global PlayerSpeed
    global CHANCE

    PlayerSpeed = tmpLvl.psd

    # defining player
    p1 = Player()
    all_sprites.add(p1)
    players.add(p1)

    # Defining ground platform
    plat1 = Platform(True, "platforms/" + tmpLvl.platDir + '/' + tmpLvl.startblock)

    # Customizing platform
    plat1.image = pygame.transform.scale(plat1.image, (plat1.image.get_width() * 3, plat1.image.get_height() * 3))
    plat1.rect = plat1.image.get_rect()
    plat1.rect.topleft = (50, height * 5 // 6 + 3)

    plat2 = Platform(True, "platforms/" + tmpLvl.platDir + '/platform_0.png')

    plat2.rect.center = (width * 1.25, height * 4 // 6)

    # Add initial platform to groups
    platforms.add(plat1)
    all_sprites.add(plat1)

    platforms.add(plat2)
    all_sprites.add(plat2)

    # loop the background music
    pygame.mixer.music.play(-1, 0)

    platnum = 0
    decor_plat = None

    # Creating font object
    sub = pygame.font.Font('fonts/pixelart.ttf', 25)

    while True:

        # PlayerSpeed Text
        ps1 = sub.render('Player Speed:', BG2, (55, 255, 55))
        ps2 = sub.render(str(PlayerSpeed), BG2, (55, 255, 55))

        # Rectangle
        ps1Rect = ps1.get_rect()
        ps2Rect = ps2.get_rect()

        # Position
        ps1Rect.center = (width * 6 // 16, ps1.get_height() * 3)
        ps2Rect.center = (width * 11 // 16, ps2.get_height() * 3)

        # HUD Player text
        score1 = sub.render('Player Distance', BG2, (55, 255, 55))
        score2 = sub.render(str(p1.relpos.x // FPS), BG2, (55, 255, 55))

        # text rectangle
        score1Rect = score1.get_rect()
        score2Rect = score2.get_rect()

        # Positioning text
        score1Rect.center = (width * 6 // 16, score1.get_height() * 2)
        score2Rect.center = (width * 11 // 16, score2.get_height() * 2)

        # Window event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        x, y = p1.rect.center

        # Making the platforms move to create an illusion
        # That the player is moving
        for plat in platforms:
            px, py = plat.rect.center
            px -= PlayerSpeed
            plat.rect.center = (px, py)

        # Put in for loop for user to increase game intensity
        for i in range(1):
            # randomizing chance
            # same logic as the seagull (l. 399) but with lava blocks
            # but not dependent on distance
            random.seed(datetime.now())

            choice = random.randint(0, CHANCE)

            if choice == 0:
                new_plat = Platform(False, None, tmpLvl.platDir)
                danger.add(new_plat)
            else:
                platnum += 1
                new_plat = Platform(True, None, tmpLvl.platDir)
                decor_plat = new_plat

            # if platforms overlap
            # remove them
            if not pygame.sprite.spritecollide(new_plat, platforms, False):
                platforms.add(new_plat)
                all_sprites.add(new_plat)
            else:
                new_plat.kill()

        # checking if the player died
        # If it happened then reset settings and run gameOver method
        if y > height * 2 or pygame.sprite.spritecollide(p1, danger, False) or x < 0:
            PlayerSpeed = tmpLvl.psd
            CHANCE = 128
            for item in decorations:
                all_sprites.add(item)
            for item in clouds:
                all_sprites.add(item)

            gameOver()

        # if platform is out of screen or if there are more than 10 platforms then destroy
        i = 0
        for plat in platforms:
            i += 1
            px, py = plat.rect.topright
            if px <= -50 or i > 10:
                plat.kill()
                plat = None

        # Seagull spawning after player distance 500
        if p1.relpos.x > 50000:
            # Chance of a seagull spawning
            choice = random.randint(0, CHANCE)

            # If true then spawn
            if choice == 0:
                for i in range(random.randrange(0, 3)):
                    new_seagull = Seagull(tmpLvl.platDir)

                    if not pygame.sprite.spritecollide(new_seagull, seagulls, False):
                        seagulls.add(new_seagull)
                        all_sprites.add(new_seagull)
                        danger.add(new_seagull)

        # When players score divided by 100 gives a remainder of 0.
        # And if player score not zero its self

        if p1.relpos.x % (70 * 100) // tmpLvl.factor == 0 and p1.relpos.x != 0:
            PlayerSpeed += 1

            # 1/chancenumber divided by 105/100
            CHANCE //= 1.05

        if platnum % 20 == 0:
            new_decor = PlatDecorations(decor_plat, None, tmpLvl.platDir)
            if pygame.sprite.spritecollide(new_decor, decorations, False):
                new_decor.kill()
            else:
                decorations.add(new_decor)

        for decor in decorations:
            x, y = decor.rect.center
            if x < 0 - screen.get_width() * 2:
                decor.image.set_alpha(0)
                decorations.remove(decor)
                decor.kill()

        # Updating sprite groups
        clouds.update()
        seagulls.update()
        p1.update(tmpLvl.jumpForce, tmpLvl.gravity)

        # to cover glitchy sprites
        screen.fill((0, 0, 0))

        if tmpLvl.bg != None:
            screen.blit(tmpLvl.image, tmpLvl.rect)
        else:
            screen.fill((55, 55, 155))

        decorations.update()

        # Drawing all sprites to screen
        clouds.draw(screen)
        decorations.draw(screen)

        all_sprites.draw(screen)

        screen.blit(score1, score1Rect)
        screen.blit(score2, score2Rect)

        screen.blit(ps1, ps1Rect)
        screen.blit(ps2, ps2Rect)

        scanlineGroup.draw(screen)

        # Refreshing screen
        pygame.display.update()

        # Fixed Frame rate 110 recommended unless old computer
        clock.tick(FPS)

def multiplayer(tmplvl, p1Mode, p2Mode):

    aliens = pygame.sprite.Group()
    numberGroup = pygame.sprite.Group()

    random.seed(datetime.now())

    # Importing global variables
    global PlayerSpeed
    global CHANCE

    PlayerSpeed = PlayerSpeed + 1

    line = pygame.Surface((width, 20))
    line.fill((0, 0, 0))

    line.set_alpha(200)

    lineRect = line.get_rect()
    lineRect.topleft = (0, height * 1 // 2 - 10)

    # Split-screen
    sc1 = pygame.Surface((width, height / 2))
    sc2 = pygame.Surface((width, height / 2))

    # Splitscreen rect
    sc1Rect = sc1.get_rect()
    sc2Rect = sc2.get_rect()

    # Positioning screens
    sc1Rect.topleft = (0, 0)
    sc2Rect.topleft = (0, height / 2)

    tmplvl.loadBG(screen.get_size(), sc1.get_size())

    # defining players
    p1 = Player(surf=sc1, AIMode=p1Mode, sideLength=35)
    players.add(p1)

    p1Tag = PlayerTag(p1, "1")

    p2 = Player2(sc2, AI_Mode=p2Mode, sideLength=35)
    players.add(p2)

    p2Tag = PlayerTag(p2, "2")

    numberGroup.add(p1Tag)
    numberGroup.add(p2Tag)

    # Defining ground platform
    plat1 = Platform(True, 'platforms/' + tmplvl.platDir + '/' + tmplvl.startblock, None, sc1)

    # Customizing platform
    plat1.rect.topleft = (sc1.get_width() * 0.5, sc1.get_height() * 5 // 6 + 3)

    plat2 = Platform(True, 'platforms/' + tmplvl.platDir + '/platform_0.png', None, sc1)

    plat2.image = pygame.transform.scale(plat2.image, (plat2.image.get_width() * 2 // 3, plat2.image.get_width() * 2 // 3))

    plat2.rect = plat2.image.get_rect()
    plat2.rect.center = (sc1.get_width() * 1.15, sc1.get_height() * 4 // 6)

    # Add initial platform to groups
    platforms.add(plat1)
    all_sprites.add(plat1)

    platforms.add(plat2)
    all_sprites.add(plat2)

    # Creating font object
    header = pygame.font.Font('fonts/segaArt.ttf', 100)
    sub = pygame.font.Font('fonts/pixelart.ttf', 25)

    line1 = Text("Player 1: ", BG_FG_Color=(None, (150, 250, 150)), script=sub, pos=(0, 0))
    line2 = Text("Player 2: ", BG_FG_Color=(None, (150, 250, 150)), script=sub, pos=(0, 0))

    line1.rect.topleft = (0, 0)
    line2.rect.topleft = line1.rect.bottomleft

    ended = False
    winner = None
    counter = 0

    platnum = 0
    decor_plat = None

    while True:

        counter += PlayerSpeed

        # PlayerSpeed And Distance Text
        ps1 = sub.render('Player Speed:', BG2, (55, 255, 55))
        ps2 = sub.render(str(PlayerSpeed), BG2, (55, 55, 255))

        pd1 = sub.render('Player Distance:', BG2, (55, 255, 55))
        pd2 = sub.render(str(counter // FPS), BG2, (55, 55, 255))

        # Win dialog
        win = header.render('You Win', BG2, (55, 55, 255))

        # Rectangle
        ps1Rect = ps1.get_rect()
        ps2Rect = ps2.get_rect()

        pd1Rect = pd1.get_rect()
        pd2Rect = pd1.get_rect()

        winRect = win.get_rect()

        # Position
        ps1Rect.center = (width * 6 // 16, ps1.get_height() * 2)
        ps2Rect.center = (width * 11 // 16, ps2.get_height() * 2)

        pd1Rect.center = (width * 6 // 16, pd1.get_height() * 3)
        pd2Rect.center = (width * 13 // 16, pd2.get_height() * 3)

        winRect.center = (width / 2, height / 2)

        # Window event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        x, y = p1.rect.center

        # Making the platforms move to create an illusion
        # That the player is moving
        for plat in platforms:
            px, py = plat.rect.center
            px -= PlayerSpeed
            plat.rect.center = (px, py)

        # Put in for loop for user to increase game intensity
        for i in range(1):
            new_plat = Platform(True, None, tmplvl.platDir, sc1)

            new_plat.image = pygame.transform.scale(new_plat.image, (
            new_plat.image.get_width() * 2 // 3, new_plat.image.get_height() * 2 // 3))

            new_plat.rect = new_plat.image.get_rect()
            new_plat.rect.center = (random.randrange(sc1.get_width() * 1.05, sc1.get_width() * 1.5), random.randrange(sc1.get_height() * 8 // 12, sc1.get_height() * 5 // 6))

            # if platforms overlap
            # remove them
            if not pygame.sprite.spritecollide(new_plat, platforms, False):
                platforms.add(new_plat)
                all_sprites.add(new_plat)
                platnum += 1
                decor_plat = new_plat
            else:
                new_plat.kill()

        if not ended and counter // FPS > 0:
            for player in players.sprites():
                x, y = player.rect.center
                if y > sc1.get_height() * 2 or pygame.sprite.spritecollide(player, danger, False) or x < 0:
                    delPlayer = player

                    all_sprites.remove(delPlayer)
                    players.remove(delPlayer)

                    delPlayer.rect.bottomright = (0, 0)

                    delPlayer.kill()
                    break

        if len(players.sprites()) < 2:
            winner = players.sprites()[-1]
            PlayerSpeed = 1
            ended = True
        # if platform is out of screen or if there are more than 10 platforms then destroy
        i = 0
        for plat in platforms:
            i += 1
            if plat.rect.topright[0] <= 0 or i > 10:
                plat.kill()

        # When players score divided by 100 gives a remainder of 0.
        # And if player score is not zero its self
        # In this case it's only used to increment the speed since this is a race.

        if counter > 9000 and counter % (20 * 100) // tmplvl.factor == 0 and counter != 0:
            alien = Seagull(tmplvl.platDir, sc1)

            x, y = alien.rect.center
            alien.rect.center = (x, random.randint(sc1.get_height() * 1 // 3, sc1.get_height() * 5 // 6))

            if pygame.sprite.spritecollide(alien, aliens, False):
                alien.kill()
            else:
                danger.add(alien)
                aliens.add(alien)
                all_sprites.add(alien)

        if counter % (1000) // tmplvl.factor == 0 and counter != 0:
            PlayerSpeed += 1

        # 1/chancenumber  = itself / 1.05
        CHANCE //= 1.05

        if platnum % 20 == 0 and platnum != 0:
            new_decor = PlatDecorations(decor_plat, None, tmplvl.platDir)

            if pygame.sprite.spritecollide(decor_plat, decorations, False):
                new_decor.kill()
            else:
                decorations.add(new_decor)

        for decor in decorations:
            if decor.rect.midright[0] < 0 - screen.get_width() * 0.5:
                decorations.remove(decor)
                decor.kill()
                break

        for player in players.sprites():
            player.update(tmplvl.jumpForce, tmplvl.gravity)
        numberGroup.update()
        decorations.update()
        aliens.update()

        sc1.fill((0, 0, 0))
        sc2.fill((0, 0, 0))

        sc1.blit(tmplvl.image1, tmplvl.rect1)
        sc2.blit(tmplvl.image2, tmplvl.rect2)

        decorations.draw(sc1)
        decorations.draw(sc2)

        sc1.blit(p1.image, p1.rect)
        sc1.blit(p1Tag.image, p1Tag.rect)

        sc2.blit(p2.image, p2.rect)
        sc2.blit(p2Tag.image, p2Tag.rect)

        # Drawing all sprites to screen
        all_sprites.draw(sc1)
        all_sprites.draw(sc2)

        sc1.blit(line1.image, line1.rect)
        sc2.blit(line2.image, line2.rect)

        # Showing splitscreen
        screen.blit(sc1, sc1Rect)
        screen.blit(sc2, sc2Rect)

        screen.blit(line, lineRect)

        screen.blit(ps1, ps1Rect)
        screen.blit(ps2, ps2Rect)

        screen.blit(pd1, pd1Rect)
        screen.blit(pd2, pd2Rect)

        keys = pygame.key.get_pressed()

        if keys[K_r]:
            for sprite in decorations:
                all_sprites.add(sprite)

            ended = False
            sleep(0.5)
            for sprite in all_sprites:
                sprite.kill()

            CHANCE = 128
            PlayerSpeed = PSD

            multiplayer(tmplvl, p1Mode, p2Mode)
            startScreen()

        if ended:
            win2 = sub.render(winner.name, BG2, (55, 155, 255))

            win2Rect = win2.get_rect()

            win2Rect.center = (width // 2, height * 2 // 3)

            screen.blit(win2, win2Rect)

            screen.blit(win, winRect)

            for sprite in decorations:
                all_sprites.add(sprite)

            if keys[K_RETURN]:
                ended = False
                sleep(0.5)
                for sprite in all_sprites:
                    sprite.kill()

                CHANCE = 128
                PlayerSpeed = PSD

                winner.kill()
                winner = None

                startScreen()

            if keys[K_r]:
                ended = False
                sleep(0.5)
                for sprite in all_sprites:
                    sprite.kill()

                CHANCE = 128
                PlayerSpeed = PSD

                winner.kill()
                winner = None

                multiplayer(tmplvl, p1Mode, p2Mode)
                startScreen()
            if p1Pad != None or p2Pad != None:
                if p1Pad.get_button(1):
                    ended = False
                    sleep(0.5)
                    for sprite in all_sprites:
                        sprite.kill()

                    CHANCE = 128
                    PlayerSpeed = PSD

                    winner.kill()
                    winner = None
                    startScreen()

                if p1Pad.get_button(9):
                    ended = False
                    sleep(0.5)
                    for sprite in all_sprites:
                        sprite.kill()

                    CHANCE = 128
                    PlayerSpeed = PSD

                    winner.kill()
                    winner = None

                    multiplayer(tmplvl, p1Mode, p2Mode)
                    startScreen()

        scanlineGroup.draw(screen)

        # Refreshing screen
        pygame.display.update()

        # Fixed Frame rate 110 recommended unless old computer
        clock.tick(FPS)

def helpScreen():
    pygame.mixer.music.load('songs/help.ogg')

    header = pygame.font.Font('fonts/pixelart.ttf', 50)
    sub = pygame.font.Font('fonts/pixelart.ttf', 20)

    title = header.render('Instructions and Details', BG, (230, 230, 230))
    l1 = sub.render("Your goal is too avoid the obstacles in your path by skipping them.", BG, (230, 230, 230))
    l2 = sub.render("Spacebar to jump.", BG, (230, 230, 230))
    l3 = sub.render("You can land on the clouds but not the ones with thunder.", BG, (230, 230, 230))
    l4 = sub.render("During your journey you will encounter lavablocks.", BG, (230, 230, 230))
    l5 = sub.render("You can't land on those", BG, (230, 230, 230))
    l6 = sub.render("You will also find seagulls.", BG, (230, 230, 230))
    l7 = sub.render("Just don't hit any of them, they're very angry", BG, (230, 230, 230))

    titleRect = title.get_rect()

    l1Rect = l1.get_rect()
    l2Rect = l2.get_rect()
    l3Rect = l3.get_rect()

    l1Rect = (width * 1 // 64, height * 7 // 32)
    l2Rect = (width * 1 // 64, height * 9 // 32)
    l3Rect = (width * 1 // 64, height * 11 // 32)
    l4Rect = (width * 1 // 64, height * 13 // 32)
    l5Rect = (width * 1 // 64, height * 15 // 32)
    l6Rect = (width * 1 // 64, height * 17 // 32)
    l7Rect = (width * 1 // 64, height * 19 // 32)

    titleRect = (width * 1 // 32, height * 1 // 16)

    bg = pygame.image.load("backgrounds/help.png")
    bg = pygame.transform.scale(bg, res)

    bgRect = bg.get_rect()

    bgRect = (0, 0)

    pygame.mixer.music.play(0, 0)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN or event.type == pygame.JOYBUTTONDOWN:
                pygame.mixer.music.stop()
                startScreen()

        screen.blit(bg, bgRect)

        screen.blit(title, titleRect)

        screen.blit(l1, l1Rect)
        screen.blit(l2, l2Rect)
        screen.blit(l3, l3Rect)
        screen.blit(l4, l4Rect)
        screen.blit(l5, l5Rect)
        screen.blit(l6, l6Rect)
        screen.blit(l7, l7Rect)

        scanlineGroup.draw(screen)
        clock.tick(FPS - 10)
        pygame.display.update()


def introScreen():
    font = pygame.font.Font("fonts/segaArt.ttf", 125)
    font2 = pygame.font.Font("fonts/pixelart.ttf", 125)

    logo = font2.render("A2", None, (218, 235, 33))
    logo2 = font.render(" Games", None, (218, 235, 33))

    logoRect = logo.get_rect()
    logo2Rect = logo2.get_rect()

    logo2Rect.topleft = (width * 5 // 16, height / 2)
    logoRect.topright = logo2Rect.topleft

    i = 0

    for i in range(255):
        screen.fill((0, 0, 0))
        screen.blit(logo, logoRect)
        screen.blit(logo2, logo2Rect)

        logo2.set_alpha(i)
        logo.set_alpha(i)

        scanlineGroup.draw(screen)
        pygame.display.update()
        clock.tick(FPS)

    sleep(0.5)

    while i > 0:
        screen.fill((0, 0, 0))
        screen.blit(logo, logoRect)
        screen.blit(logo2, logo2Rect)

        logo.set_alpha(i)
        logo2.set_alpha(i)

        i -= 1

        scanlineGroup.draw(screen)
        pygame.display.update()
        clock.tick(FPS)


def startScreen():
    COLOR = (245, 245, 245)

    pygame.mixer.music.load('songs/startups/startup-3.ogg')

    header = pygame.font.Font('fonts/pixelart.ttf', 50)
    sub = pygame.font.Font('fonts/pixelart.ttf', 25)

    title = header.render(name, BG2, COLOR)
    stMode = sub.render('Story Mode (Unfinished)', BG2, COLOR)
    start = sub.render('Arcade', BG2, COLOR)
    multi = sub.render('Multiplayer', BG2, COLOR)
    help = sub.render('Help', BG2, COLOR)
    exit = sub.render('Quit', BG2, COLOR)
    extras = sub.render('Extras', BG2, COLOR)

    cursor = sub.render('->', BG2, (100, 255, 100))

    titleRect = title.get_rect()

    startRect = start.get_rect()
    multiRect = multi.get_rect()
    helpRect = help.get_rect()
    exitRect = exit.get_rect()
    stModeRect = stMode.get_rect()
    extrasRect = extras.get_rect()

    cursorRect = cursor.get_rect()

    titleRect.center = (width/2, height * 1 // 2)

    stModeRect.center = (width/2, height * 1 // 2 - 30)
    startRect.center = (width/2, height * 1 // 2 - 10)
    multiRect.center = (width/2, height * 1 // 2 + 10)
    extrasRect.center = (width/2, height * 1//2 + 30)
    helpRect.center = (width/2, height * 1 // 2 + 50)
    exitRect.center = (width/2, height * 1 // 2 + 70)

    cursorRect.center = (width // 2 - 50, height * 1 // 2 - 10)

    x, y = cursorRect.center
    stx, sty = stModeRect.center
    sx, sy = startRect.midleft
    hx, hy = helpRect.midleft
    ex, ey = exitRect.midleft
    mx, my = multiRect.midleft

    global multiBool
    global firstEntry

    pygame.mixer.music.play(-1)

    scanlines()

    global Exit

    index = 0
    while not Exit:

        for event in pygame.event.get():
            key = pygame.key.get_pressed()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.JOYBUTTONDOWN:
                Exit = True

        if index >= len(startup_1) - 1:
            index = 0
            continue
        else:
            index += 1

        bg = startup_1[index]

        screen.fill((255, 255, 255))

        screen.blit(bg, (0, 0))
        screen.blit(title, titleRect)

        scanlineGroup.draw(screen)

        pygame.display.update()
        clock.tick(10)


    titleRect.center = (width / 2, height * 1 // 3)
    index = 0

    while True:
        for event in pygame.event.get():
            key = pygame.key.get_pressed()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN or event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYAXISMOTION:

                if key[K_UP]:
                    y -= 20
                if key[K_DOWN]:
                    y += 20
                if key[K_p]:
                    pygame.mixer.quit()
                if key[K_u]:
                    pygame.mixer.init()

                if key[K_RETURN] or key[K_SPACE]:
                    if y == ey:
                        pygame.mixer.music.stop()
                        pygame.quit()
                        sys.exit()
                    elif y == hy:
                        pygame.mixer.music.stop()
                        firstEntry = False
                        helpScreen()
                        startScreen()
                    elif y == sy or y == sty:

                        firstEntry = False
                        multiBool = False

                        levelSelect(levels, main)
                        break
                    elif y == my:
                        multiBool = True
                        firstEntry = False
                        levelSelect(multiplayerLevels, multiplayer)
                        break
                    elif y == extrasRect.midleft[1]:
                        firstEntry = False
                        multiBool = False

                        test_level()
                        break

                if y == ey:
                    x = ex - 20
                elif y == hy:
                    x = hx - 20
                elif y == sy:
                    x = sx - 20
                elif y == my:
                    x = mx - 20
                elif y == sty:
                    x = stModeRect.midleft[0] - 20
                elif y == extrasRect.midleft[1]:
                    x = extrasRect.midleft[0] - 20

                if y > ey:
                    y = sty
                    x = stModeRect.midleft[0] - 20
                if y < sty:
                    y = ey
                    x = ex - 20

        if index >= len(startup_2) - 1:
            index = 0
            continue
        else:
            index += 1

        bg = startup_2[index]

        cursorRect.center = (x, y)

        screen.fill((255, 255, 255))

        screen.blit(bg, (0, 0))

        screen.blit(title, titleRect)
        screen.blit(stMode, stModeRect)
        screen.blit(start, startRect)
        screen.blit(multi, multiRect)
        screen.blit(extras, extrasRect)
        screen.blit(exit, exitRect)
        screen.blit(help, helpRect)
        screen.blit(cursor, cursorRect)

        scanlineGroup.draw(screen)

        pygame.display.update()
        clock.tick(10)


def gameOver():
    pygame.mixer.music.load('sounds/gameOver.ogg')

    pygame.mixer.music.stop()

    header = pygame.font.Font('fonts/pixelart.ttf', 40)
    sub = pygame.font.Font('fonts/pixelart.ttf', 20)

    text = header.render('Game Over', BG, (255, 255, 255))
    text2 = sub.render('Press anything to continue', BG, (255, 255, 255))

    textRect = text.get_rect()
    text2Rect = text2.get_rect()

    textRect.midbottom = (width // 2, height // 3)
    text2Rect.midbottom = (width // 2, height * 3 // 6)

    screen.blit(text, textRect)
    screen.blit(text2, text2Rect)

    pygame.mixer.music.play(0, 0)
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN or event.type == pygame.JOYBUTTONDOWN:
                sleep(0.25)
                for sprite in all_sprites:
                    sprite.kill()
                startScreen()
                break
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        scanlineGroup.draw(screen)
        pygame.display.flip()


if not debug:
    introScreen()

startScreen()
