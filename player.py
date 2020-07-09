import game as gm
# python libraries
import pygame, time, threading, copy, random

class Player():
	def __init__(self, name, color, timer, game, board):
		self.name = name
		self.color = color
		self.timer = timer
		self.game = game
		self.board = board


class Human(Player):
	def __init__(self, name, color, timer, game, board):
		super().__init__(name, color, timer, game, board)
		self.clock = pygame.time.Clock()

	def play(self):
		self.timer.triggerStop()
		all_moves_legal = self.game.get_all_moves_legal()

		while True:
			for event in pygame.event.get():
				if event.type == pygame.MOUSEBUTTONDOWN:
					n, m = pygame.mouse.get_pos()
					n, m = n//60, m//60
					n, m = self.board.correctPos((n, m))

					self.board.update()

					other = self.game.board[n][m]
					if other is not None and other[gm.COLOR] == str(self.color):
						if self.action(n, m, all_moves_legal):
							self.timer.triggerStop()
							return
						
			self.clock.tick(60)
	
	def action(self, x, y, all_moves_legal):
		self.board.update((x, y), all_moves_legal[(x, y)])

		while True:
			for event in pygame.event.get():
				if event.type == pygame.MOUSEBUTTONDOWN:
					n, m = pygame.mouse.get_pos()
					n, m = n//60, m//60
					n, m = self.board.correctPos((n, m))

					if (n, m) in all_moves_legal[(x, y)]:
						self.board.origin = (x, y)
						self.board.destin = (n, m)

						captured, promoted = self.game.make_move(x, y, n, m)
						if promoted:
							self.board.promote(n, m)
						if captured:
							self.board.sound_capture.play()
						else:
							self.board.sound_move.play()

						self.board.update()
							
						return True
						
					# Change selected piece
					if (n, m) != (x, y):
						other = self.game.board[n][m]
						if other is not None and other[gm.COLOR] == str(self.game.turn):
							return self.action(n, m, all_moves_legal)
								
					self.board.update()
					
					return False

			self.clock.tick(60)


class Computer(Player):
	def __init__(self, name, color, timer, game, board, depth_final):
		super().__init__(name, color, timer, game, board)
		self.depth_final = depth_final

	def play(self):
		self.timer.triggerStop()
		self.no_nodes = [0] * self.depth_final##
		self.quiescence = False
		self.table_killer = [{} for i in range(self.depth_final - 1)]

		''' Tree visualization.

		self.flag = False
		'''

		game = gm.Game(self.game.turn, [list(row) for row in self.game.board], 
					   list(self.game.pos_kings))
		val, moves_best = self.negamax(game)#, depth=0, alpha=32767, beta=-32768)

		assert len(moves_best) > 0

		''' Best variation visualization. '''
		print(self.no_nodes)
		print(self.table_killer)
		print(val, moves_best)
		f = game.turn
		for m in reversed(moves_best):
			if not f: 
				print("...", end="")
			print(m[-1] + chr(97 + m[2]) + str(8 - m[3]), end=" ")
			f = 1 if not f else 0
		print()
		''''''

		try:
			print(moves_best)
			x, y, n, m, _ = moves_best[-1]
		except ValueError:
			x, y, n, m, promotion, _ = moves_best[-1]
			
		self.board.origin = (x, y)
		self.board.destin = (n, m)
		
		captured, promoted = self.game.make_move(x, y, n, m)

		if captured:
			self.board.sound_capture.play()
		else:
			self.board.sound_move.play()
		if promoted:
			self.game.board[n][m] = promotion + str(self.game.turn)

		self.board.update()
		self.timer.triggerStop()
		return 


	def try_move(self, x, y, n, m, other, val_best, moves_best, game, depth, alpha, beta):
		# self.quiescence = False
		game2 = gm.Game(game.turn, [list(row) for row in game.board], 
					    list(game.pos_kings))
		captured, promoted = game2.make_move(x, y, n, m)
		game2.turn = 0 if game2.turn else 1

		# if not captured and depth == 2:
			# self.quiescence = True

		'''	Tree visualization.

		notation = other[gm.NAME]
		if captured:
			if notation == 'P':
				notation = chr(97 + x)
			notation += 'x'
		if notation == 'P':
			notation = ''
		print("{:s}{:4s}  ".format(' '*6*depth if self.flag else '', notation + chr(97 + n) + str(8 - m)), end='')
		self.flag = False
		'''

		if promoted:
			for promotion in ('N', 'B', 'R', 'Q'):
				game2.board[n][m] = promotion + str(self.game.turn)

				# recursiveness
				val, moves = self.negamax(game2, depth + 1, -beta, -alpha)
				val = -val

				''' Tree visualization.

				print(" {:d}".format(val))
				self.flag = True
				'''

				if val_best < val:
					notation = other[gm.NAME]
					if captured:
						if notation == 'P':
							notation = chr(97 + x)
						notation += 'x'
					if notation == 'P':
						notation = ''
					val_best = val
					moves.append((x, y, n, m, promotion, notation))
					moves_best = moves
				alpha = max(alpha, val)
				
		else:
			# recursiveness
			val, moves = self.negamax(game2, depth + 1, -beta, -alpha)
			val = -val

			''' Tree visualization.

			print(" {:d}".format(val))
			self.flag = True
			'''
			
			if val_best < val:
				notation = other[gm.NAME]
				if captured:
					if notation == 'P':
						notation = chr(97 + x)
					notation += 'x'
				if notation == 'P':
					notation = ''
				val_best = val
				moves.append((x, y, n, m, notation))
				moves_best = moves
			alpha = max(alpha, val)

		return val_best, moves_best, alpha, beta

	def negamax(self, game, depth=0, alpha=-32768, beta=32767):
		""" Find best move recursively using the negamax algorithm along side with modest optimizations. """
		checkmate = game.checkmate()
		if checkmate == 1:
			self.no_nodes[depth - 1] += 1
			return game.evaluate() - 20000, []
		if checkmate == 2:
			self.no_nodes[depth - 1] += 1
			return 0, []
		# quiescence search
		# if self.quiescence:
			# self.no_nodes[depth - 1] += 1
			# return game.evaluate(), []
		if depth == self.depth_final:
			self.no_nodes[depth - 1] += 1
			return game.evaluate(), []

		val_best, moves_best = -32768, []
		all_moves_killer = self.table_killer[depth - 1]

		# Calculate killer moves
		if depth != 0:
			moves_killer = sorted(all_moves_killer.keys(), key=lambda x: all_moves_killer[x], reverse=True)[0:2]
			for move_killer in moves_killer:
				x, y, n, m = move_killer
				other = game.board[x][y]
				if other is None or other[gm.COLOR] != str(game.turn): continue

				moves_legal = game.get_moves_legal(x, y)

				if (n, m) in moves_legal:
					val_best, moves_best, alpha, beta = self.try_move(x, y, n, m, other, val_best, moves_best, 
																	  game, depth, alpha, beta)	
					# alpha-beta prune
					if alpha >= beta:
						all_moves_killer[move_killer] += 1
						return val_best, moves_best
					else:
						if all_moves_killer[move_killer] == 0:
							del all_moves_killer[move_killer]
						else:
							all_moves_killer[move_killer] -= 1

		# Calculate all moves
		for x in range(8):
			for y in range(8):
				other = game.board[x][y]
				if other is None or other[gm.COLOR] != str(game.turn): continue

				moves_legal = game.get_moves_legal(x, y)
				
				for n, m in moves_legal:
					val_best, moves_best, alpha, beta = self.try_move(x, y, n, m, other, val_best, moves_best, 
																	  game, depth, alpha, beta)	
					# alpha-beta prune
					if alpha >= beta:
						if (x, y, n, m) in all_moves_killer:
							all_moves_killer[(x, y, n, m)] += 1
						else:
							all_moves_killer[(x, y, n, m)] = 1
						return val_best, moves_best

		return val_best, moves_best


## Bugs: increment is added even after game is over

class Timer:
	def __init__(self, seconds):
		self.seconds = seconds
	
		self.__WARNING_LIMIT = 30	# must be less or equal to.warning_sound's time

		pygame.mixer.init()
		self.warning_sound = pygame.mixer.Sound("sounds/ticking_clock.wav")

	def __repr__(self):
		s = int(self.seconds)
		return "{:02d}:{:02d}".format(s//60, s%60) if s < 3600 else "{:02d}:{:02d}:{:02d}".format(s//3600, s%3600//60, s%60)
	
	def ready(self):
		self.end_thread = False
		self.stop_thread = True	
		threading.Thread(target=self.countDown, daemon=True).start()

	def countDown(self):
		while not self.end_thread:
			flag = True
			while not self.stop_thread:
				init_time = time.time()
				#print(self)##
				time.sleep(0.01)
				if self.seconds <= self.__WARNING_LIMIT and flag:
					self.warning_sound.play()
					flag = False
				if self.seconds <= 0:
					self.warning_sound.stop()
					self.end_thread = True
					break
				self.seconds -= time.time() - init_time
			time.sleep(0.01)
	
	

# Increment is added after the move
class Fischer(Timer):
	def __init__(self, seconds, increment=3):
		super().__init__(seconds)
		self.increment = increment

	def triggerStop(self, stop_thread=None):
		self.stop_thread = not self.stop_thread if stop_thread == None else stop_thread
				
		if self.stop_thread:
			self.seconds += self.increment
			print(self)##
			self.warning_sound.stop()
			

# Same as Fischer's, except:
# the increment doesn't exceed the initial time
class Bronstein(Timer):
	def __init__(self, seconds, increment=3):
		super().__init__(seconds)
		self.increment = increment
		self.init_seconds = self.seconds
		
	def triggerStop(self, stop_thread = None):
		self.stop_thread = not self.stop_thread if stop_thread == None else stop_thread

		if self.stop_thread:
			self.seconds += self.increment if self.increment < self.init_seconds - self.seconds else self.init_seconds - self.seconds
			print(self)##
			self.warning_sound.stop()
		else:
			self.init_seconds = self.seconds


# Increment is added before the move
class Delay(Timer):
	def __init__(self, seconds, increment):
		super().__init__(seconds)
		self.increment = increment

	def triggerStop(self, stop_thread = None):
		self.stop_thread = not self.stop_thread if stop_thread == None else stop_thread
		
		if self.stop_thread:
			self.warning_sound.stop()
		else:
			self.seconds += self.increment
			print(self)##
		

# No increment
# While time is decreasing for one player,
# it's increasing for the other
class HourGlass(Timer):
	def __init__(self, seconds):
		super().__init__(seconds)

	def triggerStop(self, stop_thread = None):          
		self.stop_thread = not self.stop_thread if stop_thread == None else stop_thread 
		self.warning_sound.stop()

	def countDown(self):
		while not self.end_thread:
			flag = True
			while not self.stop_thread:
				init_time = time.time()
				#print(self)##
				time.sleep(0.01)
				if self.seconds <= self.__WARNING_LIMIT and flag:
					self.warning_sound.play()
					flag = False
				if self.seconds <= 0:
					self.warning_sound.stop()
					self.end_thread = True
					break
				self.seconds -= time.time() - init_time 
			while self.stop_thread:
				init_time = time.time()
				#print(self)##
				time.sleep(0.01)
				self.seconds += time.time() - init_time

