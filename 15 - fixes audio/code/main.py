import pygame, sys
from settings import *
from level import Level

class Game:
	def __init__(self):
		pygame.init()
		try:
			self.screen = pygame.display.set_mode((WIDTH,HEIGTH), pygame.SCALED | pygame.RESIZABLE)
		except pygame.error:
			self.screen = pygame.display.set_mode((WIDTH,HEIGTH))
		pygame.display.set_caption('Zelda')
		self.clock = pygame.time.Clock()
		self.level = Level()

		self.main_sound = pygame.mixer.Sound('../audio/main.ogg')
		self.main_sound.set_volume(0.4)
		self.main_sound.play(loops = -1)

	def restart(self):
		self.level = Level()
		self.level.state = 'playing'

	def activate_screen_action(self):
		state = self.level.state
		if state in ('menu','paused'):
			self.level.begin_playing()
		elif state in ('game_over','victory'):
			self.restart()

	def handle_keydown(self,key):
		state = self.level.state
		if key == pygame.K_m and state in ('playing','upgrade','paused'):
			if state == 'paused':
				self.level.state = 'upgrade'
			else:
				self.level.toggle_menu()
		elif key in (pygame.K_ESCAPE, pygame.K_p) and state in ('playing','paused'):
			self.level.toggle_pause()
		elif key in (pygame.K_RETURN, pygame.K_KP_ENTER) and state in ('menu','paused'):
			self.level.begin_playing()
		elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_r) and state in ('game_over','victory'):
			self.restart()

	def handle_click(self,pos):
		rect = self.level.ui.action_rect
		if rect and rect.collidepoint(pos):
			self.activate_screen_action()

	def run(self):
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				if event.type == pygame.KEYDOWN:
					self.handle_keydown(event.key)
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					self.handle_click(event.pos)

			self.screen.fill(WATER_COLOR)
			self.level.run()
			pygame.display.update()
			self.clock.tick(FPS)

if __name__ == '__main__':
	game = Game()
	print('Zelda ready', flush=True)
	game.run()
