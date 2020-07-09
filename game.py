# python libraries
import pygame, time, copy
import tables

# global variables
NAME = 0; COLOR = 1; EN_PASSANT = 2; HAS_MOVED = 2

class Game:
	""" A representation of the chess game. 
	
	:param turn: a representation of the player currently playing; 0 for black and 1 for white.
	:type turn: int
	:param board: the set of pieces listed according its position.
	:type board: list[str | None]
	:param pos_kings: the white and black kings position
	:type pos_kings: list[(int, int)]
	"""	
	def __init__(self, turn=None, board=None, pos_kings=None):
		assert turn == board == pos_kings == None or (turn != None and board != None and pos_kings != None)

		self.over = False

		if turn is None:
			self.turn = 1
		else:
			self.turn = turn

		if board is None:
			self.board = [
				["R00", "P00", None, None, None, None, "P10", "R10"],
				["N0" , "P00", None, None, None, None, "P10", "N1" ],
				["B0" , "P00", None, None, None, None, "P10", "B1" ],
				["Q0" , "P00", None, None, None, None, "P10", "Q1" ],
				["K00", "P00", None, None, None, None, "P10", "K10"],
				["B0" , "P00", None, None, None, None, "P10", "B1" ],
				["N0" , "P00", None, None, None, None, "P10", "N1" ],
				["R00", "P00", None, None, None, None, "P10", "R10"],
			]
		else:
			self.board = board

		if pos_kings is None:
			self.pos_kings = [(4, 0), (4, 7)]
		else:
			self.pos_kings = pos_kings

	def make_move(self, x, y, n, m):
		""" Fix pieces' position and attributes after a move. """
		captured = promoted = False

		if self.board[n][m] is not None:
			captured = True

		# Make move	
		piece = self.board[x][y]
		self.board[x][y] = None
		self.board[n][m] = piece

		assert piece is not None

		if piece[NAME] == 'P':
			# Set pawn's ``en_passant`` attribute to True
			if m == 3 + self.turn:
				self.board[n][m] = piece[:EN_PASSANT] + '1'

			# Remove enemy pawns that were captured en passent
			# Acknowledge capture
			other = self.board[n][m - (-1)**self.turn]
			if other is not None and other[NAME] == 'P' and other[EN_PASSANT] == '1':
				self.board[n][m - (-1)**self.turn] = None
				captured = True
			
			# Acknowledge promotion
			if m == 7*(not self.turn):
				promoted = True

		elif piece[NAME] == 'R':
			self.board[n][m] = piece[:HAS_MOVED] + '1'

		elif piece[NAME] == 'K':
			if piece[HAS_MOVED] == '0':
				# Swap rook with king
				if n == 2:
					rook = self.board[0][7*self.turn]
					self.board[0][7*self.turn] = None
					self.board[3][7*self.turn] = rook
				elif n == 6:
					rook = self.board[7][7*self.turn]
					self.board[7][7*self.turn] = None
					self.board[5][7*self.turn] = rook
			self.board[n][m] = piece[:HAS_MOVED] + '1'
			self.pos_kings[self.turn] = (n, m)

		# Rechange enemy pawns' attribute ``en_passant`` to False
		for x in range(8):
			other = self.board[x][3 + (not self.turn)]
			if other is not None and other[NAME] == 'P' and other[COLOR] != piece[COLOR]:
				self.board[x][3 + (not self.turn)] = other[:EN_PASSANT] + '0'

		return captured, promoted

	def get_moves_legal(self, x, y):
		""" Return a list with allowed moves for one piece. """
		# Remove piece from ``board`` and verify if king is being attacked
		moves_legal = set()
		moves = self.get_moves(x, y)

		piece = self.board[x][y]
		self.board[x][y] = None

		assert piece is not None
		
		if piece[NAME] != 'K' and not self.check():
			moves_legal = moves
		else:
			self.board[x][y] = piece

			# Verify moves that stop the check
			for n, m in moves:
				if piece[NAME] == 'K':
					if piece[COLOR] == '0':
						pos_kings = [(n, m), self.pos_kings[1]]				
					else:
						pos_kings = [self.pos_kings[0], (n, m)]
				else:
					pos_kings = list(self.pos_kings)

				game = Game(self.turn, [list(row) for row in self.board], pos_kings)				
				game.make_move(x, y, n, m)

				if not game.check():
					moves_legal.add((n, m))

		self.board[x][y] = piece
		
		return moves_legal

	def get_all_moves_legal(self):
		""" Return a dictionary with allowed moves for each piece.

		:rtype: dict[(int, int), (int, int)]
		"""
		all_moves_legal = {}

		for x in range(8):
			for y in range(8):
				other = self.board[x][y]
				if other is not None and other[COLOR] == str(self.turn):
					all_moves_legal[(x, y)] = self.get_moves_legal(x, y)

		return all_moves_legal

	def under_attack(self, pos_pieces):
		""" Check if any of the positions is being attacked.

		:param pos_pieces: the set of positions.
		:type pos_pieces: set[(int, int)]
		:rtype: bool
		"""
		for x in range(8):
			for y in range(8):
				other = self.board[x][y]
				if other is not None and other[COLOR] != str(self.turn):		
					if len(pos_pieces & self.get_moves_atk(x, y)) != 0:
						return True
		return False	

	def check(self):
		""" Check if king is being attacked. """		
		return self.under_attack({self.pos_kings[self.turn]})

	def checkmate(self):
		""" Return state[1]_ of the game.
		
		[1] {0: no checkmate, 1: checkmate, 2: stalemate}
		"""
		if self.check():
			checkmate = 1
			for moves in self.get_all_moves_legal().values():
				if len(moves) != 0:
					checkmate = 0
					break
		else:
			checkmate = 0
		return checkmate
			
	def evaluate(self):
		""" Return an evaluation[1]_[2]_ for the piece's positions in ``board``.
		
		[1] https://www.chessprogramming.org/Evaluation
		[2] https://www.chessprogramming.org/Simplified_Evaluation_Function
		"""
		val = 0
		no_pieces = 0

		for x in range(8):
			for y in range(8):
				if self.board[x][y] is None: continue
				
				no_pieces += 1
				piece = self.board[x][y]

				if int(piece[COLOR]):
					i, j = y, x
				else:
					i, j = 7 - y, 7 - x
			    
				if piece[NAME] == 'P':
					# Suppose right away it's an isolated, and then check if it actually is
					centipawns = 50 + tables.EVAL_PAWN[i][j]

					# Check if doubled
					for m in range(8):
						if m == y: continue
						other = self.board[x][m]
						if other is not None and other[COLOR] == piece[COLOR] and other[NAME] == 'P':
							centipawns -= 50
							break

					# Check if not isolated
					brk = False
					for n in (y - 1, y + 1):
						if not 0 <= n < 8: continue
						for m in range(8):
							other = self.board[n][m]
							if other is not None and other[COLOR] == piece[COLOR] and other[NAME] == 'P':
								centipawns += 50
								brk = True
								break
						if brk: break
						
					# Check if blocked
					if len( self.get_moves(x, y) ) == 0:
						centipawns -= 50
				if piece[NAME] == 'N':
					centipawns = 320 + tables.EVAL_KNIGHT[i][j]
				elif piece[NAME] == 'B':
					centipawns = 330 + tables.EVAL_BISHOP[i][j]
				elif piece[NAME] == 'R':
					centipawns = 500 + tables.EVAL_ROOK[i][j]
				elif piece[NAME] == 'Q':
					centipawns = 900 + tables.EVAL_QUEEN[i][j]
				elif piece[NAME] == 'K':
					if no_pieces > 8:
						centipawns = tables.EVAL_KING_MIDDLE[i][j]
					else:
						centipawns = tables.EVAL_KING_END[i][j]
				else:
					centipawns = 0

				val += centipawns if piece[COLOR] == str(self.turn) else -centipawns

		for moves_legal in self.get_all_moves_legal().values():
			val += 10*len(moves_legal)

		self.turn = 0 if self.turn else 1
		for moves_legal in self.get_all_moves_legal().values():
			val -= 10*len(moves_legal)

		self.turn = 0 if self.turn else 1
		'''
		if abs(eval) > 1.5:
			return (-1)**(eval < 0)*3
		elif abs(eval) > 0.7:
			return (-1)**(eval < 0)*2
		elif abs(eval) > 0.26:
			return (-1)**(eval < 0)*1
		else:
			return 0
		'''
		return val

	def get_moves_atk(self, x, y):
		""" Return attack moves. """
		piece = self.board[x][y]
		moves_atk = set()

		if piece[NAME] == 'P':
			# diagonal capture
			b = (-1)**int(piece[COLOR])
			for a in (-1, 1):
				if 0 <= x + a < 8 and 0 <= y + b < 8:
					other = self.board[x + a][y + b]
					if other is not None and other[COLOR] != piece[COLOR]:
						moves_atk.add((x + a, y + b))
					elif other is None:
						other = self.board[x + a][y + b - (-1)**int(piece[COLOR])]
						if other is not None and other[NAME] == 'P' and other[EN_PASSANT] == '1':
							moves_atk.add((x + a, y + b))
		elif piece[NAME] == 'N':
			# L-shape movement
			for a in (-2, -1, 1, 2):
				for b in (-2, -1, 1, 2):
					if abs(a) == abs(b): continue
					if 0 <= x + a < 8 and 0 <= y + b < 8:
						other = self.board[x + a][y + b]
						if other is None or other[COLOR] != piece[COLOR]:
							moves_atk.add((x + a, y + b))
		elif piece[NAME] == 'B':
			# diagonal movement
			for a in (-1, 1):
				for b in (-1, 1):			
					k = 1
					while 0 <= x + a*k < 8 and 0 <= y + b*k < 8:
						other = self.board[x + a*k][y + b*k]
						if other is None:
							moves_atk.add((x + a*k, y + b*k))
						elif other[COLOR] != piece[COLOR]:
							moves_atk.add((x + a*k, y + b*k))
							break
						else:
							break
						k += 1
		elif piece[NAME] == 'R':
			# cross movement
			for a in (-1, 0, 1):
				for b in (-1, 0, 1):
					if abs(a) == abs(b): continue
					k = 1
					while 0 <= x + a*k < 8 and 0 <= y + b*k < 8:
						other = self.board[x + a*k][y + b*k]
						if other is None:
							moves_atk.add((x + a*k, y + b*k))
						elif other[COLOR] != piece[COLOR]:
							moves_atk.add((x + a*k, y + b*k))
							break
						else:
							break
						k += 1
		elif piece[NAME] == 'Q':
			# cross-diagonal movement
			for a in (-1, 0, 1):
				for b in (-1, 0, 1):
					if a == b == 0: continue
					k = 1
					while 0 <= x + a*k < 8 and 0 <= y + b*k < 8:
						other = self.board[x + a*k][y + b*k]
						if other is None:
							moves_atk.add((x + a*k, y + b*k))
						elif other[COLOR] != piece[COLOR]:
							moves_atk.add((x + a*k, y + b*k))
							break
						else:
							break
						k += 1
		else:
			# one-square cross-diagonal movement
			for a in (-1, 0, 1):
				for b in (-1, 0, 1):
					if a == b == 0: continue
					if 0 <= x + a < 8 and 0 <= y + b < 8:
						other = self.board[x + a][y + b]
						if other is None or other[COLOR] != piece[COLOR]:
							moves_atk.add((x + a, y + b))

		return moves_atk

	def get_moves_neutral(self, x, y):
		""" Return neutral moves. """
		piece = self.board[x][y]
		moves_neutral = set()

		if piece[NAME] == 'P':
			# one-two-squares advance movement
			for b in (1, 2):
				b *= (-1)**int(piece[COLOR])
				if 0 <= y + b < 8:
					other = self.board[x][y + b]
					if other is None:
						moves_neutral.add((x, y + b))
						if y != 1 + 5*int(piece[COLOR]): 
							break
					else:
						break
		else:
			if piece[HAS_MOVED] == '1':
				return moves_neutral

			# castle
			other = self.board[0][y]
			if other is not None and other[NAME] == 'R' and other[HAS_MOVED] == '0':
				# no piece between this rook and king
				can_move = True
				for i in range(3):
					if self.board[1 + i][y] is not None:
						can_move = False
						break
		
				if can_move:
					# enemy attack range doesn't reach squares between this rook and king
					if not self.under_attack({(n, y) for n in range(1, x + 1)}):
						moves_neutral.add((2, y))

			other = self.board[7][y]
			if other is not None and other[NAME] == 'R' and other[HAS_MOVED] == '0':
				# no piece between this rook and king
				can_move = True
				for i in range(2):
					if self.board[6 - i][y] is not None:
						can_move = False
						break

				if can_move:
					# enemy attack range doesn't reach squares between this rook and king
					if not self.under_attack({(n, y) for n in range(x, 7)}):
						moves_neutral.add((6, y))

		return moves_neutral	

	def get_moves(self, x, y):
		""" Return attack and neutral (if existing) moves considering the chess' movement rules [1]_. 
		
		[1] this moves may not be allowed.
		"""
		piece = self.board[x][y]

		if piece[NAME] in ('P', 'K'):
			return self.get_moves_atk(x, y) | self.get_moves_neutral(x, y)
		return self.get_moves_atk(x, y)	

'''
while True:
	

	if over:
		#timer_thread.cancel() # important !!
		screen.fill((0, 0, 0) if turn else (255, 255, 255))
		text = myfont.render("PRETAS VENCEM" if turn else "BRANCAS VENCEM", False, (255, 255,255) if turn else (0, 0, 0))
		screen.blit(text, ((480 - text.get_rect().width) / 2, (480 - text.get_rect().height) / 2))
		pygame.display.update()
		time.sleep(5)
		quit()

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			quit()
		if event.type == pygame.MOUSEBUTTONDOWN:
			posx, posy = pygame.mouse.get_pos()
			posx = (posx // 60) * 60
			posy = (posy // 60) * 60

			boardDisplay()

			for p in [p for p in All if p.color == turn_color]:
				if (posx, posy) == (p.x, p.y):
					if p.action():

						move_sound.play()

						arrangeGame(not turn)

						print(evaluate(All))

						turn = not turn
					
						# INVERT BOARD
						if inverting:
							time.sleep(0.5)
							for p in All:
								p.x += 2*(210 - p.x)
								p.y += 2*(210 - p.y)
						
						boardDisplay()

						turn_color = "white" if turn else "Black"
						Moves = checkMoves(turn)

						# CHECKS IF GAME IS OVER
						check_mate = True
						for PieceMoves in Moves.values():
							if len(PieceMoves) != 0:
								check_mate = False
								break
						
						# GAME OVER
						if check_mate or over:

							time.sleep(2)
							

							screen.fill((0, 0, 0) if turn else (255, 255, 255))
							
							if check_mate:

								if look4check():
									text = myfont.render("PRETAS VENCEM" if turn else "BRANCAS VENCEM", False, (255, 255,255) if turn else (0, 0, 0))
								else:
									text = myfont.render("EMPATE  POR", False, (255, 255,255) if turn else (0, 0, 0))
									text2 = myfont.render("AFOGAMENTO", False, (255, 255,255) if turn else (0, 0, 0))
									screen.blit(text2, ((480 - text.get_rect().width) / 2, (480 - text.get_rect().height) / 2 + 30))
							else:
								text = myfont.render("BRANCAS VENCEM" if turn else "PRETAS VENCEM", False, (255, 255,255) if turn else (0, 0, 0))	
							screen.blit(text, ((480 - text.get_rect().width) / 2, (480 - text.get_rect().height) / 2))

							pygame.display.update()

							time.sleep(5)
							quit()

	clock.tick(60)
'''