import pygame, sys, random

from pygame.locals import *
from datetime import datetime
from time import sleep, time
from os import remove
from warnings import filterwarnings


filterwarnings('ignore', category=DeprecationWarning)

pygame.init()
pygame.mixer.init

clock = pygame.time.Clock()

width = 800
height = 600


res = (width, height)

name = 'Sky Dash'

screen = pygame.display.set_mode(res)
pygame.display.set_caption(name)

# Sprite Groups
clouds = pygame.sprite.Group()
platforms = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
danger = pygame.sprite.Group()
players = pygame.sprite.Group()
seagulls = pygame.sprite.Group()

# text and screen background
BG = (52, 164, 235)
BG2 = (100, 100, 255)

# Invisible mouse
pygame.mouse.set_visible(False)

PSD = 7
PlayerSpeed = PSD

CHANCE = 128
# 1/128 = 0.5% chance of lava block

FPS = 110

# Calculating Players position relative to start
vec = pygame.math.Vector2
highscore = vec(0, 0)


class Clouds(pygame.sprite.Sprite):
	def __init__(self, pos):
		super().__init__()

		self.image = pygame.image.load('cloud.png')
		self.rect = self.image.get_rect()

		self.rect.center = pos

	def update(self):
		x, y = self.rect.center

		if x < -self.image.get_width() - 10:
			random.seed(datetime.now())
			x = width + self.image.get_width() + 10
			y = random.randrange(0, height)

		x-=1

		self.rect.center = (x, y)

class Platform(pygame.sprite.Sprite):
	def __init__(self, Landable, image=None):
		super().__init__()

		if image == None:
			if Landable:
				self.image = pygame.image.load('platform_' + str(random.randint(0, 2)) + '.png')
			else:
				self.image = pygame.image.load('death.png')
		else:
			self.image = pygame.image.load(image)

		self.rect = self.image.get_rect()
		self.rect.center = (random.randrange(width * 1.25, width * 1.5), random.randrange(height * 7//12, height * 5//6))
		self.pos = vec((self.rect.center))

class Seagull(pygame.sprite.Sprite):
	def __init__(self):
		super().__init__()

		self.image = pygame.image.load('seagull.png')

		self.rect = self.image.get_rect()
		self.rect.center = (random.randrange(width, width * 2), random.randrange(height * 1//6, height * 5//24))

		self.x, self.y = self.rect.center

	def update(self):
		self.x -= PlayerSpeed * 1.15
		self.rect.center = (self.x, self.y)

		if self.x < 0:
			all_sprites.remove(self)
			danger.remove(self)
			seagulls.remove(self)

			self.kill()

class Player(pygame.sprite.Sprite):
	def __init__(self):
		super().__init__()

		self.image = pygame.Surface((40, 40))
		self.image.fill((120, 255, 120))

		self.rect = self.image.get_rect()

		self.rect.center = (width//2, 0)

		self.acc = 1
		self.relpos = vec(self.rect.center)

		self.sound = pygame.mixer.Sound('jump.ogg')

		pygame.mixer.Sound.set_volume(self.sound, 0.04)


		self.jumpstate = True

	def move(self):

		x, y = self.rect.center

		keys = pygame.key.get_pressed()

		if pygame.sprite.spritecollide(self, platforms, False):
			plat = pygame.sprite.spritecollide(self, platforms, False)
			px, py = plat[0].rect.topleft

			if y <= py:
				x+=PlayerSpeed
				self.relpos.x += PlayerSpeed
		else:
			x+=PlayerSpeed
			self.relpos.x += PlayerSpeed

		self.rect.center = (x, y)

	def jump(self):

		x, y = self.rect.center


		keys = pygame.key.get_pressed()
		mkeys = pygame.mouse.get_pressed()


		if keys[K_SPACE] or mkeys[0]:
			self.sound.stop()
			self.sound.play()
			y -= 20

		self.rect.center = (x, y)

	def gravity(self):

		x, y = self.rect.center

		if not pygame.sprite.spritecollide(self, platforms, False):
			y += self.acc
			self.acc += 0.4

			self.rect.center = (x, y)
		else:
			self.acc = 0
			self.rect.center = (x, y)



	def update(self):

		x, y = self.rect.midtop

		if x > width * 2//3:
			x = width * 2//3

		self.rect.midtop = (x, y)


		if pygame.sprite.spritecollide(self, platforms, False):
			plats = pygame.sprite.spritecollide(self, platforms, False)
			plat = plats[-1]
			platx, platy = plat.rect.midtop

			plat_w = plat.image.get_width()
			plat_h = plat.image.get_height()

			if y > platy and x > (platx + plat_w * 1//3) and x < (platx + plat_w * 2//3):
				self.jumpstate = False
				self.rect.midtop = (platx, y)
			else:
				self.jumpstate = True


		self.relpos.x += PlayerSpeed

		if self.jumpstate:
			self.jump()

		self.gravity()


class HighScoreLine(Player):
	def __init__(self):
		super().__init__()

		self.image = pygame.Surface((20, height))
		self.image.fill((10, 10, 255))

		self.image.set_alpha(50)

		self.rect = self.image.get_rect()
		self.rect.center = (highscore.x, height/2)
		self.x, self.y = self.rect.center

def main():
	pygame.mixer.music.load('song-' + str(random.randint(0, 4)) +'.ogg')

	for i in range(40):
		new_cloud = Clouds((random.randrange(0, width), random.randrange(0, height)))

		if not pygame.sprite.spritecollide(new_cloud, clouds, False):
			clouds.add(new_cloud)
			all_sprites.add(new_cloud)

	global highscore
	global PlayerSpeed
	global CHANCE

	scoreLine = HighScoreLine()
	all_sprites.add(scoreLine)

	# defining player
	p1 = Player()
	all_sprites.add(p1)
	players.add(p1)

	# Defining ground platform
	plat1 = Platform(True, 'platform_0.png')

	plat1.image = pygame.transform.scale(plat1.image, (width, plat1.image.get_height()))
	plat1.rect = plat1.image.get_rect()
	plat1.rect.topleft = (0, height * 5//6 + 3)

	platforms.add(plat1)
	all_sprites.add(plat1)

	platx, platy = plat1.rect.center

	pygame.mixer.music.play(-1, 0)


	sub = pygame.font.Font('pixelart.ttf', 25)

	while True:

		hs1 = sub.render('Current Highscore: ', BG2, (55,55,255))
		hs2 = sub.render(str(highscore.x//100), BG2, (55, 55, 255))

		hs1Rect = hs1.get_rect()
		hs2Rect = hs2.get_rect()

		hs1Rect.center = (width * 6//16, hs1.get_height())
		hs2Rect.center = (width * 11//16, hs2.get_height())




		score1 = sub.render('Player Score', BG2, (55,55,255))
		score2 = sub.render(str(p1.relpos.x//100), BG2, (55,55,255))

		score1Rect = score1.get_rect()
		score2Rect = score2.get_rect()

		score1Rect.center = (width * 6//16, score1.get_height()*2)
		score2Rect.center = (width  * 11//16, score2.get_height()*2)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()


		screen.fill(BG)

		x, y = p1.rect.center

		for plat in platforms:
			px, py = plat.rect.center
			px -= PlayerSpeed
			plat.rect.center = (px, py)

		if x > scoreLine.x:
			scoreLine.x -= PlayerSpeed

		for i in range(1):
			random.seed(datetime.now())

			choice = random.randint(0, CHANCE)

			if choice == 0:
				new_plat = Platform(False)
				danger.add(new_plat)
			else :
				new_plat = Platform(True)


			if not pygame.sprite.spritecollide(new_plat, platforms, False):
				platforms.add(new_plat)
				all_sprites.add(new_plat)
			else:
				new_plat.kill()

		if y > height * 2 or pygame.sprite.spritecollide(p1, danger, False) or x < 0:
			PlayerSpeed = PSD
			CHANCE = 128
			gameOver(p1, highscore)

		i = 0
		for plat in platforms:
			i+=1
			px, py = plat.rect.topright
			if px <= 0 or i > 10:
				plat.kill()

		if p1.relpos.x > 30000 == 0:
			choice = random.randint(0, CHANCE)

			if choice == 0:
				for i in range(random.randrange(0, 10)):
					new_seagull = Seagull()

					if not pygame.sprite.spritecollide(new_seagull, seagulls, False):
						seagulls.add(new_seagull)
						all_sprites.add(new_seagull)
						danger.add(new_seagull)

		if p1.relpos.x >= highscore.x:
			highscore.x = p1.relpos.x
			scoreLine.x = x
		else:
			scoreLine.x = highscore.x

		# When players score divided by 10 gives a remainder of 0.
		# And if player score not zero its self

		if p1.relpos.x % 10000 == 0 and p1.relpos.x != 0:
			PlayerSpeed += 1
			CHANCE //= 4

		scoreLine.rect.center = (scoreLine.x, height//2)

		clouds.update()
		seagulls.update()
		p1.update()

		all_sprites.draw(screen)

		screen.blit(hs1, hs1Rect)
		screen.blit(hs2, hs2Rect)

		screen.blit(score1, score1Rect)
		screen.blit(score2, score2Rect)

		pygame.display.update()
		clock.tick(FPS)

def startScreen():

	header = pygame.font.Font('pixelart.ttf', 50)
	sub = pygame.font.Font('pixelart.ttf', 25)

	title = header.render(name, BG, (255, 255, 255))

	start = sub.render('Start', BG, (255, 255, 255))
	exit = sub.render('Quit', BG, (255, 255, 255))

	cursor = sub.render('->', BG, (100, 255, 100))

	titleRect = title.get_rect()

	startRect = start.get_rect()
	exitRect = exit.get_rect()

	cursorRect = cursor.get_rect()

	titleRect.center = (width/2, height * 1//3)

	startRect.center = (width/2, height * 1//2 - 10)
	exitRect.center = (width/2, height * 1//2 + 10)

	cursorRect.center = (width//2 - 50, height * 1//2 - 10)

	x, y = cursorRect.center

	sx, sy = startRect.center
	ex, ey = exitRect.center

	while True:

		for event in pygame.event.get():
			key = pygame.key.get_pressed()
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == KEYDOWN:

				if key[K_UP]:
					y -= 20
				if key[K_DOWN]:
					y += 20
				if key[K_p]:
					pygame.mixer.quit()
				if key[K_u]:
					pygame.mixer.init()


				if key[K_RETURN]:
					if y == ey:
						pygame.mixer.music.unload()
						pygame.quit()
						sys.exit()
					elif y == sy:
						main()
					break

				if y > ey:
					y = sy
				if y < sy:
					y = ey






		cursorRect.center = (x, y)

		screen.fill(BG)

		screen.blit(title, titleRect)
		screen.blit(start, startRect)
		screen.blit(exit, exitRect)
		screen.blit(cursor, cursorRect)

		pygame.display.update()


def gameOver(p1, highscore):

	if p1.relpos.x >= highscore.x:
		highscore.x = p1.relpos.x


	pygame.mixer.music.stop()

	header = pygame.font.Font('pixelart.ttf', 40)
	sub = pygame.font.Font('pixelart.ttf', 20)

	text = header.render('Game Over: ' + str(p1.relpos.x//100), BG, (255, 255, 255))
	text2 = sub.render('Press anything to continue', BG, (255, 255, 255))
	score = sub.render('Current Highscore: ' + str(highscore.x//100), BG, (255, 255, 255))

	textRect = text.get_rect()
	text2Rect = text2.get_rect()
	scoreRect = score.get_rect()

	textRect.midbottom = (width // 2, height//3)
	text2Rect.midbottom = (width // 2, height * 3//6)
	scoreRect.midbottom = (width // 2, height * 3//12)

	screen.blit(text, textRect)
	screen.blit(score, scoreRect)
	screen.blit(text2, text2Rect)

	pygame.display.flip()
	sleep(0.75)

	while True:
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				sleep(0.25)
				for sprite in all_sprites:
					sprite.kill()
				startScreen()
				break
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()

		pygame.display.flip()

startScreen()
