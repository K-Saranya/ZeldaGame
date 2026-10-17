import pygame
from settings import *
from tile import Tile
from player import Player
from debug import debug
from support import *
from random import choice, randint
from weapon import Weapon
from ui import UI
from enemy import Enemy
from particles import AnimationPlayer
from magic import MagicPlayer
from upgrade import Upgrade

class Level:
	def __init__(self):

		# get the display surface
		self.display_surface = pygame.display.get_surface()
		self.state = 'menu'

		# sprite group setup
		self.visible_sprites = YSortCameraGroup()
		self.obstacle_sprites = pygame.sprite.Group()

		# attack sprites
		self.current_attack = None
		self.attack_sprites = pygame.sprite.Group()
		self.attackable_sprites = pygame.sprite.Group()

		# sprite setup
		self.spawned_enemies = 0
		self.create_map()

		# user interface
		self.ui = UI()
		self.upgrade = Upgrade(self.player)
		self.score = 0
		self.kills = 0
		self.suspended_at = None
		self.feedback = []
		self.feedback_font = pygame.font.Font(UI_FONT,16)
		self.hit_flash = 0
		self.flash_surface = pygame.Surface(self.display_surface.get_size(), pygame.SRCALPHA)

		# particles
		self.animation_player = AnimationPlayer()
		self.magic_player = MagicPlayer(self.animation_player)

		self.hurt_sound = pygame.mixer.Sound('../audio/hit.wav')
		self.hurt_sound.set_volume(0.45)
		self.death_sound = pygame.mixer.Sound('../audio/death.wav')
		self.death_sound.set_volume(0.7)

	def create_map(self):
		layouts = {
			'boundary': import_csv_layout('../map/map_FloorBlocks.csv'),
			'grass': import_csv_layout('../map/map_Grass.csv'),
			'object': import_csv_layout('../map/map_Objects.csv'),
			'entities': import_csv_layout('../map/map_Entities.csv')
		}
		graphics = {
			'grass': import_folder('../graphics/Grass'),
			'objects': import_folder('../graphics/objects')
		}

		for style,layout in layouts.items():
			for row_index,row in enumerate(layout):
				for col_index, col in enumerate(row):
					if col != '-1':
						x = col_index * TILESIZE
						y = row_index * TILESIZE
						if style == 'boundary':
							Tile((x,y),[self.obstacle_sprites],'invisible')
						if style == 'grass':
							random_grass_image = choice(graphics['grass'])
							Tile(
								(x,y),
								[self.visible_sprites,self.obstacle_sprites,self.attackable_sprites],
								'grass',
								random_grass_image)

						if style == 'object':
							surf = graphics['objects'][int(col)]
							Tile((x,y),[self.visible_sprites,self.obstacle_sprites],'object',surf)

						if style == 'entities':
							if col == '394':
								self.player = Player(
									(x,y),
									[self.visible_sprites],
									self.obstacle_sprites,
									self.create_attack,
									self.destroy_attack,
									self.create_magic)
							else:
								if col == '390': monster_name = 'bamboo'
								elif col == '391': monster_name = 'spirit'
								elif col == '392': monster_name ='raccoon'
								else: monster_name = 'squid'
								Enemy(
									monster_name,
									(x,y),
									[self.visible_sprites,self.attackable_sprites],
									self.obstacle_sprites,
									self.damage_player,
									self.trigger_death_particles,
									self.add_exp)
								self.spawned_enemies += 1

	def create_attack(self):
		self.current_attack = Weapon(self.player,[self.visible_sprites,self.attack_sprites])

	def create_magic(self,style,strength,cost):
		if self.state != 'playing' or not self.player.alive:
			return
		if style == 'heal':
			self.magic_player.heal(self.player,strength,cost,[self.visible_sprites])

		if style == 'flame':
			self.magic_player.flame(self.player,cost,[self.visible_sprites,self.attack_sprites])

	def destroy_attack(self):
		if self.current_attack:
			self.current_attack.kill()
		self.current_attack = None

	def clear_attacks(self):
		self.destroy_attack()
		for sprite in list(self.attack_sprites):
			sprite.kill()

	def player_attack_logic(self):
		if self.attack_sprites:
			for attack_sprite in self.attack_sprites:
				collision_sprites = pygame.sprite.spritecollide(attack_sprite,self.attackable_sprites,False)
				if collision_sprites:
					for target_sprite in collision_sprites:
						if target_sprite.sprite_type == 'grass':
							pos = target_sprite.rect.center
							offset = pygame.math.Vector2(0,75)
							for leaf in range(randint(3,6)):
								self.animation_player.create_grass_particles(pos - offset,[self.visible_sprites])
							target_sprite.kill()
						else:
							damage = target_sprite.get_damage(self.player,attack_sprite.sprite_type)
							if damage:
								self.spawn_feedback(target_sprite.rect.midtop,f'-{int(damage)}','#ffe08a')

	def damage_player(self,amount,attack_type,source=None):
		if self.state != 'playing':
			return False

		result = self.player.apply_damage(amount)
		if not result:
			return False

		self.animation_player.create_particles(attack_type,self.player.rect.center,[self.visible_sprites])
		self.hit_flash = 8
		self.visible_sprites.shake = 7
		self.spawn_feedback(self.player.rect.midtop,f'-{int(amount)}','#ff6b6b')
		if source is not None:
			self.knockback_player(source)

		if result == 'dead':
			self.enter_game_over()
		else:
			self.hurt_sound.play()
		return True

	def knockback_player(self,source):
		vector = pygame.math.Vector2(self.player.hitbox.center) - pygame.math.Vector2(source.hitbox.center)
		if vector.magnitude() == 0:
			vector = pygame.math.Vector2(0,-1)
		else:
			vector = vector.normalize()
		vector *= 32
		self.player.hitbox.x += vector.x
		self.player.collision('horizontal')
		self.player.hitbox.y += vector.y
		self.player.collision('vertical')
		self.player.rect.center = self.player.hitbox.center

	def spawn_feedback(self,world_pos,text,color):
		image = self.feedback_font.render(text,False,color)
		self.feedback.append({
			'image': image,
			'pos': pygame.math.Vector2(world_pos),
			'age': 0,
			'life': 48,
		})

	def update_feedback(self):
		for item in self.feedback:
			item['age'] += 1
		self.feedback = [item for item in self.feedback if item['age'] < item['life']]

	def draw_feedback(self):
		for item in self.feedback:
			progress = item['age'] / item['life']
			pos = pygame.math.Vector2(item['pos']) - self.visible_sprites.offset
			pos.y -= item['age'] * 1.15
			item['image'].set_alpha(int(255 * (1 - progress)))
			rect = item['image'].get_rect(center = pos)
			self.display_surface.blit(item['image'],rect)

	def draw_flash(self):
		alpha = min(80, self.hit_flash * 10)
		self.flash_surface.fill((170,28,28,alpha))
		self.display_surface.blit(self.flash_surface,(0,0))

	def trigger_death_particles(self,pos,particle_type):
		self.animation_player.create_particles(particle_type,pos,self.visible_sprites)

	def add_exp(self,amount):
		if self.state != 'playing':
			return
		self.player.exp += amount
		self.score += amount
		self.kills += 1

	def enter_game_over(self):
		if self.state == 'game_over':
			return
		self.state = 'game_over'
		self.player.health = 0
		self.player.alive = False
		self.player.vulnerable = False
		self.player.attacking = False
		self.player.direction.update(0,0)
		self.clear_attacks()
		self.death_sound.play()

	def enter_victory(self):
		if self.state != 'playing':
			return
		self.state = 'victory'
		self.player.attacking = False
		self.player.direction.update(0,0)
		self.clear_attacks()

	def suspend(self):
		if self.suspended_at is None:
			self.suspended_at = pygame.time.get_ticks()

	def resume_timers(self):
		if self.suspended_at is None:
			return
		delta = pygame.time.get_ticks() - self.suspended_at
		self.suspended_at = None
		self.shift_clocks(delta)

	def shift_clocks(self,delta):
		self.shift_fields(self.player,('hurt_time','attack_time','weapon_switch_time','magic_switch_time'),delta)
		for sprite in self.visible_sprites:
			if getattr(sprite,'sprite_type',None) == 'enemy':
				self.shift_fields(sprite,('attack_time','hit_time'),delta)

	def shift_fields(self,obj,names,delta):
		for name in names:
			value = getattr(obj,name,None)
			if value is not None:
				setattr(obj,name,value + delta)

	def begin_playing(self):
		if self.state in ('menu','paused','upgrade'):
			self.resume_timers()
			self.state = 'playing'

	def toggle_menu(self):
		if self.state == 'playing':
			self.suspend()
			self.state = 'upgrade'
		elif self.state == 'upgrade':
			self.begin_playing()

	def toggle_pause(self):
		if self.state == 'playing':
			self.suspend()
			self.state = 'paused'
		elif self.state == 'paused':
			self.begin_playing()

	def living_enemy_count(self):
		return sum(1 for sprite in self.visible_sprites if getattr(sprite,'sprite_type',None) == 'enemy')

	def check_victory(self):
		if self.state != 'playing' or self.spawned_enemies <= 0:
			return
		if self.living_enemy_count() == 0:
			self.enter_victory()

	def run(self):
		self.visible_sprites.custom_draw(self.player)
		self.draw_feedback()
		if self.hit_flash > 0:
			self.draw_flash()
			self.hit_flash -= 1
		self.ui.display(self.player,self.score,self.kills)

		if self.state == 'playing':
			self.visible_sprites.update()
		if self.state == 'playing':
			self.visible_sprites.enemy_update(self.player)
		if self.state == 'playing':
			self.player_attack_logic()
			self.update_feedback()
			self.check_victory()
		elif self.state == 'upgrade':
			self.upgrade.display()
		elif self.state == 'paused':
			self.ui.display_pause()
		elif self.state == 'game_over':
			self.ui.display_game_over(self.score,self.kills)
		elif self.state == 'victory':
			self.ui.display_victory(self.score,self.kills)
		elif self.state == 'menu':
			self.ui.display_menu()


class YSortCameraGroup(pygame.sprite.Group):
	def __init__(self):
		super().__init__()
		self.display_surface = pygame.display.get_surface()
		self.half_width = self.display_surface.get_size()[0] // 2
		self.half_height = self.display_surface.get_size()[1] // 2
		self.offset = pygame.math.Vector2()
		self.shake = 0

		self.floor_surf = pygame.image.load('../graphics/tilemap/ground.png').convert()
		self.floor_rect = self.floor_surf.get_rect(topleft = (0,0))

	def custom_draw(self,player):
		self.offset.x = player.rect.centerx - self.half_width
		self.offset.y = player.rect.centery - self.half_height
		if self.shake > 0:
			self.offset.x += randint(-4,4)
			self.offset.y += randint(-4,4)
			self.shake -= 1

		floor_offset_pos = self.floor_rect.topleft - self.offset
		self.display_surface.blit(self.floor_surf,floor_offset_pos)

		for sprite in sorted(self.sprites(),key = lambda sprite: sprite.rect.centery):
			offset_pos = sprite.rect.topleft - self.offset
			self.display_surface.blit(sprite.image,offset_pos)

	def enemy_update(self,player):
		enemy_sprites = [sprite for sprite in self.sprites() if hasattr(sprite,'sprite_type') and sprite.sprite_type == 'enemy']
		for enemy in enemy_sprites:
			enemy.enemy_update(player)
