import pygame
from settings import *

class UI:
	def __init__(self):
		self.display_surface = pygame.display.get_surface()
		self.font = pygame.font.Font(UI_FONT,UI_FONT_SIZE)
		self.small_font = pygame.font.Font(UI_FONT,14)
		self.title_font = pygame.font.Font(UI_FONT,48)

		self.health_bar_rect = pygame.Rect(86,30,210,22)
		self.energy_bar_rect = pygame.Rect(86,62,210,22)

		self.weapon_graphics = []
		for weapon in weapon_data.values():
			path = weapon['graphic']
			weapon = pygame.image.load(path).convert_alpha()
			self.weapon_graphics.append(weapon)

		self.magic_graphics = []
		for magic in magic_data.values():
			magic = pygame.image.load(magic['graphic']).convert_alpha()
			self.magic_graphics.append(magic)

		self.action_rect = None

	def show_bar(self,current,max_amount,bg_rect,color,track_color):
		pygame.draw.rect(self.display_surface,UI_BG_COLOR,bg_rect)
		inner = bg_rect.inflate(-4,-4)
		pygame.draw.rect(self.display_surface,track_color,inner)

		ratio = 0
		if max_amount:
			ratio = max(0, min(1, current / max_amount))
		fill_width = int(inner.width * ratio)
		if fill_width > 0:
			fill_rect = pygame.Rect(inner.left,inner.top,fill_width,inner.height)
			pygame.draw.rect(self.display_surface,color,fill_rect)
		pygame.draw.rect(self.display_surface,UI_BORDER_COLOR,bg_rect,2)

	def selection_box(self,left,top, has_switched):
		bg_rect = pygame.Rect(left,top,ITEM_BOX_SIZE,ITEM_BOX_SIZE)
		pygame.draw.rect(self.display_surface,UI_BG_COLOR,bg_rect)
		if has_switched:
			pygame.draw.rect(self.display_surface,UI_BORDER_COLOR_ACTIVE,bg_rect,3)
		else:
			pygame.draw.rect(self.display_surface,UI_BORDER_COLOR,bg_rect,3)
		return bg_rect

	def weapon_overlay(self,weapon_index,has_switched):
		top = self.display_surface.get_height() - ITEM_BOX_SIZE - 20
		bg_rect = self.selection_box(16,top,has_switched)
		weapon_surf = self.weapon_graphics[weapon_index]
		weapon_rect = weapon_surf.get_rect(center = bg_rect.center)
		self.display_surface.blit(weapon_surf,weapon_rect)

	def magic_overlay(self,magic_index,has_switched):
		top = self.display_surface.get_height() - ITEM_BOX_SIZE - 20
		bg_rect = self.selection_box(16 + ITEM_BOX_SIZE + 12,top,has_switched)
		magic_surf = self.magic_graphics[magic_index]
		magic_rect = magic_surf.get_rect(center = bg_rect.center)
		self.display_surface.blit(magic_surf,magic_rect)

	def draw_panel(self,rect,border=UI_BORDER_COLOR):
		pygame.draw.rect(self.display_surface,UI_BG_COLOR,rect)
		pygame.draw.rect(self.display_surface,border,rect,3)

	def display(self,player,score,kills):
		self.action_rect = None
		surface = self.display_surface
		sw,sh = surface.get_size()

		hurt = player.alive and not player.vulnerable
		hud_border = '#ffffff' if hurt else UI_BORDER_COLOR
		hud = pygame.Rect(16,16,400,96)
		self.draw_panel(hud,hud_border)

		hp_label = self.font.render('HP',False,TEXT_COLOR)
		mp_label = self.font.render('MP',False,TEXT_COLOR)
		surface.blit(hp_label,(30,30))
		surface.blit(mp_label,(30,62))

		health_ratio = 0
		if player.stats['health']:
			health_ratio = max(0, player.health / player.stats['health'])
		health_color = HEALTH_COLOR
		if player.alive and health_ratio <= 0.3 and (pygame.time.get_ticks() // 220) % 2 == 0:
			health_color = '#ffb4b4'
		self.health_bar_rect.topleft = (86,28)
		self.energy_bar_rect.topleft = (86,60)
		self.show_bar(player.health,player.stats['health'],self.health_bar_rect,health_color,HEALTH_TRACK_COLOR)
		self.show_bar(player.energy,player.stats['energy'],self.energy_bar_rect,ENERGY_COLOR,ENERGY_TRACK_COLOR)

		hp_text = self.small_font.render(f'{int(player.health)}/{int(player.stats["health"])}',False,TEXT_COLOR)
		mp_text = self.small_font.render(f'{int(player.energy)}/{int(player.stats["energy"])}',False,TEXT_COLOR)
		surface.blit(hp_text,(304,30))
		surface.blit(mp_text,(304,62))

		score_panel = pygame.Rect(sw - 226,16,210,112)
		self.draw_panel(score_panel)
		rows = (
			('SCORE', int(score)),
			('EXP', int(player.exp)),
			('KILLS', int(kills)),
		)
		for index,(label,value) in enumerate(rows):
			y = 28 + index * 26
			label_surf = self.small_font.render(label,False,UI_TEXT_DIM)
			value_surf = self.font.render(str(value),False,TEXT_COLOR)
			surface.blit(label_surf,(score_panel.left + 14,y))
			value_rect = value_surf.get_rect(right = score_panel.right - 14, centery = y + 8)
			surface.blit(value_surf,value_rect)

		self.weapon_overlay(player.weapon_index,not player.can_switch_weapon)
		self.magic_overlay(player.magic_index,not player.can_switch_magic)
		self.draw_controls_hint(sh,sw)

	def draw_controls_hint(self,sh,sw):
		hint = 'WASD move    SPACE attack    CTRL magic    Q/E swap    M upgrade    ESC pause'
		text = self.small_font.render(hint,False,TEXT_COLOR)
		rect = text.get_rect()
		panel = rect.inflate(24,14)
		panel.midbottom = (sw // 2 + 70, sh - 18)
		if panel.left < 200:
			panel.left = 200
		rect.center = panel.center
		self.draw_panel(panel)
		self.display_surface.blit(text,rect)

	def show_overlay(self,title,message,detail_lines,button_text,accent):
		surface = self.display_surface
		sw,sh = surface.get_size()
		dim = pygame.Surface((sw,sh), pygame.SRCALPHA)
		dim.fill((6,8,14,155))
		surface.blit(dim,(0,0))

		line_height = 30
		title_h = self.title_font.get_height()
		message_h = self.font.get_height() + 18 if message else 0
		panel_h = 28 + title_h + 28 + message_h + len(detail_lines) * line_height + 18 + 52 + 28
		panel_h = min(panel_h, sh - 32)
		panel = pygame.Rect(0,0,700,panel_h)
		panel.center = (sw // 2, sh // 2)
		pygame.draw.rect(surface,UI_BG_COLOR,panel)
		pygame.draw.rect(surface,accent,panel,4)

		y = panel.top + 28
		title_surf = self.title_font.render(title,False,accent)
		title_rect = title_surf.get_rect(midtop = (panel.centerx,y))
		surface.blit(title_surf,title_rect)
		y = title_rect.bottom + 8
		pygame.draw.line(surface,accent,(panel.left + 40,y),(panel.right - 40,y),2)
		y += 18

		if message:
			msg = self.font.render(message,False,TEXT_COLOR)
			msg_rect = msg.get_rect(midtop = (panel.centerx,y))
			surface.blit(msg,msg_rect)
			y = msg_rect.bottom + 18

		for line in detail_lines:
			line_surf = self.font.render(line,False,TEXT_COLOR)
			line_rect = line_surf.get_rect(midtop = (panel.centerx,y))
			surface.blit(line_surf,line_rect)
			y += line_height

		button = pygame.Rect(0,0,320,52)
		button.midtop = (panel.centerx, y + 6)
		pygame.draw.rect(surface,'#2a2416',button)
		pygame.draw.rect(surface,accent,button,3)
		label = self.font.render(button_text,False,accent)
		surface.blit(label,label.get_rect(center = button.center))
		self.action_rect = button

	def display_menu(self):
		self.show_overlay(
			'ZELDA',
			'Clear the island of every monster.',
			[
				'WASD or arrows to move',
				'Space attack     Ctrl magic',
				'Q / E swap gear     M upgrade',
				'Esc pause',
			],
			'ENTER  -  START',
			ACCENT_COLOR)

	def display_pause(self):
		self.show_overlay(
			'PAUSED',
			'The island waits.',
			['M opens upgrades'],
			'ENTER  -  RESUME',
			ACCENT_COLOR)

	def display_game_over(self,score,kills):
		self.show_overlay(
			'DEFEAT',
			'Your health reached zero.',
			[
				f'Score   {int(score)}',
				f'Kills   {int(kills)}',
			],
			'ENTER  -  RESTART',
			DEFEAT_COLOR)

	def display_victory(self,score,kills):
		self.show_overlay(
			'VICTORY',
			'The island is clear.',
			[
				f'Score   {int(score)}',
				f'Kills   {int(kills)}',
			],
			'ENTER  -  PLAY AGAIN',
			VICTORY_COLOR)
