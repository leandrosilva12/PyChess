import game as gm
# python libraries
import pygame
import time##

# Variables:
#	inverting	| bool			| keeps inverting board during game
#	inverted	| bool			| registers if board was turned over at the beginning | useful when player1 is black
#	side		| bool			| registers the side of the board that is currently playing: bottom (True) or top (False) | useful to calculate pieces' position

#	  inverting inverted \ turn |  0  |  1
#	                      ------+-----+-----
#					        00  |  0  |  1						
#                           01  |  1  |  0
#					        11  |  0  |  0						
#                           10  |  1  |  1
#     side = (inverting and not inverted) or (turn and not inverting and not inverted) or (not turn and not inverting and inverted)

KEY_WORDS = {'0': "black", '1': "white", 'P': "pawn", 'N': "knight",
			 'B': "bishop", 'R': "rook", 'Q': "queen", 'K': "king"}

class Board:
	def __init__(self, game, inverting, inverted):
		self.game = game
		self.inverting = inverting
		self.inverted = inverted
		
		self.origin = self.destin = (8, 8)	# out of the board, where can't be seen

		pygame.init()
		pygame.mixer.init()##troquei pelo de cima
		pygame.font.init()

		self.screen = pygame.display.set_mode((480, 480))
		
		self.myfont = pygame.font.SysFont('gillsansultra', 30)
		
		self.sound_move		= pygame.mixer.Sound(     "sounds/move.wav")
		self.sound_capture	= pygame.mixer.Sound(  "sounds/capture.wav")
		self.sound_dings	= pygame.mixer.Sound("sounds/ding-ding.wav")##nao está a fazer nada
	
		self.bg_fade		= pygame.image.load(           "images/fade.png")
		self.bg_fade		= pygame.transform.scale(     self.bg_fade, (480, 480))
		self.bg_white		= pygame.image.load(   "images/square-white.png")
		self.bg_white		= pygame.transform.scale(    self.bg_white, (140, 140))
		self.img_board		= pygame.image.load(    "images/board-brown.png")
		self.img_board		= pygame.transform.scale(   self.img_board, (480, 480))
		self.img_circle		= pygame.image.load(   "images/circle-green.png")
		self.img_circle		= pygame.transform.scale(  self.img_circle, ( 60,  60))
		self.img_capture	= pygame.image.load(  "images/capture-green.png")
		self.img_capture	= pygame.transform.scale( self.img_capture, ( 60,  60))
		self.img_danger		= pygame.image.load(  "images/danger-radial.png")
		self.img_danger		= pygame.transform.scale(  self.img_danger, ( 60,  60))
		self.img_current	= pygame.image.load( "images/square-reddish.png")
		self.img_current	= pygame.transform.scale( self.img_current, ( 60,  60))
		self.img_move		= pygame.image.load("images/square-greenish.png")
		self.img_move		= pygame.transform.scale(    self.img_move, ( 60,  60))
	
	# When the input is a real position, returns the apparent position in board and vice versa.
	def correctPos(self, pos, pixels=False):
		x, y = pos
		if self.side != self.game.turn:
			x = 7 - x
			y = 7 - y

		if pixels: return x*60, y*60
		return x, y

	def update(self, current=(8, 8), moves_legal=[]):
		self.side = ((self.inverting and not self.inverted) or (self.game.turn and not self.inverting 
					 and not self.inverted) or (not self.game.turn and not self.inverting and self.inverted))

		self.screen.blit(  self.img_board, (0, 0))
		self.screen.blit(   self.img_move, self.correctPos(self.origin, True))
		self.screen.blit(   self.img_move, self.correctPos(self.destin, True))
		self.screen.blit(self.img_current, self.correctPos(    current, True))

		if self.game.check():
			pos_king = self.game.pos_kings[self.game.turn]
			self.screen.blit(self.img_danger, self.correctPos(pos_king, True))

		for (x, y) in moves_legal:
			image = self.img_circle
			if self.game.board[x][y] is not None:
				image = self.img_capture

			self.screen.blit(image, self.correctPos((x, y), True))

		for x in range(8):
			for y in range(8):
				other = self.game.board[x][y]
				if other is not None:
					img_piece = pygame.image.load("images/" + KEY_WORDS[other[gm.NAME]] 
													+ "-" + KEY_WORDS[other[gm.COLOR]] + ".png")
					self.screen.blit(img_piece, self.correctPos((x, y), True))

		pygame.display.flip()	# updates everything

	def promote(self, x, y):
		pawn = self.game.board[x][y]
		promotion = ('Q', 'R', 'B', 'N')

		self.screen.blit( self.bg_fade, (  0,   0))
		self.screen.blit(self.bg_white, (170, 170))
			
		for i in range(4):
			img_promotion = pygame.image.load("images/" + KEY_WORDS[promotion[i]] + "-" 
												+ KEY_WORDS[pawn[gm.COLOR]] + ".png")
			self.screen.blit(img_promotion, (180 + 60*(i % 2), 180 + 60*(i//2)) )
		
		pygame.display.flip()

		n0, m0 = 0, 0
		while True:
			for event in pygame.event.get():
				n, m = pygame.mouse.get_pos()
				n, m = n//60, m//60

				if event.type == pygame.MOUSEBUTTONDOWN:
					if 3 <= n <= 4 and 3 <= m <= 4:
						for i in range(4):
							if (180 + 60*(i % 2), 180 + 60*(i//2)) == (n*60, m*60):
								self.game.board[x][y] = promotion[i] + pawn[gm.COLOR]
						return

				if event.type == pygame.MOUSEMOTION:
					if (n, m) != (n0, m0):
						self.screen.blit(self.bg_white, (170, 170))
					
						if 3 <= n <= 4 and 3 <= m <= 4:			
							self.screen.blit( pygame.transform.scale(self.bg_fade, (60, 60)), (60*n, 60*m))
					
						for i in range(4):
							img_promotion = pygame.image.load("images/" + KEY_WORDS[promotion[i]] + "-" 
																+ KEY_WORDS[pawn[gm.COLOR]] + ".png")
							self.screen.blit(img_promotion, (180 + 60*(i % 2), 180 + 60*(i//2)) )
		
						pygame.display.flip()

						n0, m0 = n, m
				
	def startGame(self, player1, player2):
		player1.timer.ready()
		player2.timer.ready()
		while not self.game.over:
			print("eval" , self.game.evaluate())
			self.update()
			player = player1 if self.game.turn == player1.color else player2

			start_time = time.time()##

			player.play()

			elapsed_time = time.time() - start_time; print("Elapsed Time:", elapsed_time)##
			
			self.game.turn = 0 if self.game.turn else 1

			checkmate = self.game.checkmate()
			self.game.over = True if checkmate else False

		print("Checkmate!" if checkmate == 1 else "Stalemate!")##
