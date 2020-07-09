import board as bd
import player as pr
import game as gm

# python libraries
import ctypes, os, platform, pygame, time, threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import Tk, Button, Label, PhotoImage, messagebox
from PIL import Image, ImageTk

import sys##


class ChessApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.iconbitmap("images/chess-logo.ico")
        self.title("PyChess")

        self.title_font = tkfont.Font(family='Courier New', size=30, weight="bold")
        self.subtitle_font = tkfont.Font(family='Arial', size=10, slant="roman")

        self.button_font = tkfont.Font(family='Courier New', size=12, weight="bold")
        self.button_image = Image.open("images/chess-button.png").resize((int(WIDTH*0.15), int(HEIGHT*0.1)), Image.ANTIALIAS)
        self.button_image = ImageTk.PhotoImage(self.button_image)
        
        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (MenuPage, PlayPage, HumanPage, GamePage):
            page_name = F.__name__
            frame = F(parent=container, root=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location
            # the one on the top of the stacking order
            # will be the one that is visible
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MenuPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()


class MenuPage(tk.Frame):

    def __init__(self, parent, root):
        tk.Frame.__init__(self, parent)
        self.root = root
        self.anstimes = 0

        background_image = Image.open("images/chess-menu-wallpaper.png").resize(SCREENSIZE, Image.ANTIALIAS)
        background_image = ImageTk.PhotoImage(background_image)

        background_label = tk.Label(self, image=background_image)
        background_label.place(x=0, y=0, relwidth=1, relheight=1)
        # keeps an extra reference to the image object, avoiding the garbage-collection
        ''' https://stackoverflow.com/questions/22200003/tkinter-button-not-showing-image '''
        background_label.image = background_image

        button1 = tk.Button(self, text="Play", font=root.button_font, fg="#194455", bg="#194455", activebackground="#194455", bd=0, cursor="plus", 
                            image=root.button_image, compound="center", command=lambda: root.show_frame("PlayPage"))
        button2 = tk.Button(self, text="Settings", font=root.button_font, bd=0, bg="#194455", activebackground="#194455", fg="#194455",
                            image=root.button_image, compound="center", state="disabled")
        self.button3 = tk.Button(self, text="Exit", font=root.button_font, bd=0, bg="#194455", activebackground="#194455", fg="#194455", cursor="spider",
                            image=root.button_image, compound="center", command=lambda: self.exit())  
        # displays the widgets
        button1.pack(pady=(HEIGHT*0.5,4))
        button2.pack(pady=4)
        self.button3.pack(pady=4)
        
    def exit(self):
        if self.anstimes >= 2:
            self.button3.config(state="disabled", cursor="arrow")
            messagebox.showinfo(title="Exit", message="There you go. No need to thank me!")
            return

        answear = messagebox.askyesno(title="Exit", message="But you're having so much fun here!\nAre you sure?")
        if answear == True:
            messagebox.showwarning(title="Exit", message="I noticed you misclicked. No worries, I got you pal! " if self.anstimes == 0 else "You must be blind. You've clicked the wrong button twice!")
            self.anstimes += 1


class PlayPage(tk.Frame):

    def __init__(self, parent, root):
        tk.Frame.__init__(self, parent)
        self.root = root
        self.config(background="#194455")

        label = tk.Label(self, text="Game Mode", font=root.title_font, fg="#ffffff", bg="#194455")
        label.pack(pady=(HEIGHT*0.3,10))

        button1 = tk.Button(self, text="Human", font=root.button_font, fg="#194455", bg="#194455", activebackground="#194455", bd=0, cursor="plus", 
                            image=root.button_image, compound="center", command=lambda: root.show_frame("HumanPage"))
        button2 = tk.Button(self, text="Computer", font=root.button_font, fg="#194455", bg="#194455", activebackground="#194455", bd=0, 
                            image=root.button_image, compound="center", state="disabled")
        button3 = tk.Button(self, text="Back", font=root.button_font, fg="#194455", bg="#194455", activebackground="#194455", bd=0, cursor="plus", 
                            image=root.button_image, compound="center", command=lambda: root.show_frame("MenuPage"))
        button1.pack(pady=4)
        button2.pack(pady=4)
        button3.pack(pady=4)

class HumanPage(tk.Frame):

    def __init__(self, parent, root):
        tk.Frame.__init__(self, parent)
        self.root = root
        self.config(background="#194455")

        label = tk.Label(self, text="Connection", font=root.title_font, fg="#ffffff", bg="#194455")
        label.pack(pady=(HEIGHT*0.3,10))

        button1 = tk.Button(self, text="Own Device", font=root.button_font, fg="#194455", bg="#194455", activebackground="#194455", bd=0, cursor="plus", 
                            image=root.button_image, compound="center", command=lambda: [root.show_frame("GamePage"), root.frames["GamePage"].startGame()])
        button2 = tk.Button(self, text="Local",  font=root.button_font, fg="#194455", bg="#194455", activebackground="#194455", bd=0,
                            image=root.button_image, compound="center", state="disabled")
        button3 = tk.Button(self, text="Back", font=root.button_font, fg="#194455", bg="#194455", activebackground="#194455", bd=0, cursor="plus", 
                            image=root.button_image, compound="center", command=lambda: root.show_frame("PlayPage"))
        button1.pack(pady=4)
        button2.pack(pady=4)
        button3.pack(pady=4)

class GamePage(tk.Frame):

    def __init__(self, parent, root):
        tk.Frame.__init__(self, parent)
        self.root = root
        self.config(background="#194455")

        # menu (left side)
        self.menu = tk.Frame(self, width=150, height=516, highlightbackground='#595959', highlightthickness=2)
        
        button = tk.Button(self.menu, text="Back", font=root.button_font, fg="#194455", bg="#194455", activebackground="#194455", bd=0, cursor="plus", 
                            image=root.button_image, compound="center", command=lambda: root.show_frame("HumanPage"))
        button.pack(pady=4)

        # pygame
        self.pygame_frame = tk.Frame(self, width=482, height=482, highlightbackground='#595959', highlightthickness=2)
        self.embed = tk.Frame(self.pygame_frame, width=480, height=480)

        # Packing
        #self.pack(expand=True)
        #self.pack_propagate(0)

        self.pygame_frame.pack(side="left")
        self.embed.pack()
        self.menu.pack(side="left")
        self.menu.pack_propagate(0)

        # embeds the pygame window
        os.environ['SDL_WINDOWID'] = str(self.embed.winfo_id())
        system = platform.system()
        if system == "Windows":
            os.environ['SDL_VIDEODRIVER'] = 'windib'
        elif system == "Linux":
            os.environ['SDL_VIDEODRIVER'] = 'x11'

        self.root.update_idletasks()
    
    def startGame(self):
        game = gm.Game()    
        board = bd.Board(game, inverting=True, inverted=False)
        player1 = pr.Computer("Leandro", 0, pr.Fischer(3600), game, board, 2)
        #player1 = pr.Human("Leandro", 0, pr.Fischer(3600), game, board)
        player2 = pr.Human("Bruno", 1, pr.Fischer(3600), game, board)


        #player1 = pr.Computer("Leandro", int(sys.argv[1]), pr.Fischer(3600), game, board, 3)
        #player2 = pr.Human("Bruno", int(sys.argv[2]), pr.Fischer(3600), game, board)

        threading.Thread(target=board.startGame(player1, player2), daemon=True).start()


if __name__ == "__main__":
    user32 = ctypes.windll.user32
    SCREENSIZE = WIDTH, HEIGHT = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1) - 50    # -50 is meant to compensate the window bottom bar
    app = ChessApp()
    app.mainloop()



'''
class GamePage(tk.Frame):

    def __init__(self, parent, root):
        tk.Frame.__init__(self, parent)
        self.root = root
        self.config(background="#194455")

        # menu (left side)
        self.menu = tk.Frame(self, width=150, height=516, highlightbackground='#595959', highlightthickness=2)
        
        button = tk.Button(self.menu, text="Back", font=root.button_font, fg="#194455", bg="#194455", activebackground="#194455", bd=0, cursor="plus", 
                            image=root.button_image, compound="center", command=lambda: root.show_frame("HumanPage"))
        button.pack(pady=4)

        # pygame
        self.pygame_frame = tk.Frame(self, width=514, height=514, highlightbackground='#595959', highlightthickness=2)
        self.embed = tk.Frame(self.pygame_frame, width=512, height=512)

        # Packing
        #self.pack(expand=True)
        #self.pack_propagate(0)

        self.menu.pack(side="right")
        self.menu.pack_propagate(0)

        self.pygame_frame.pack(side="right")
        self.embed.pack()

        # embeds the pygame window
        os.environ['SDL_WINDOWID'] = str(self.embed.winfo_id())
        system = platform.system()
        if system == "Windows":
            os.environ['SDL_VIDEODRIVER'] = 'windib'
        elif system == "Linux":
            os.environ['SDL_VIDEODRIVER'] = 'x11'

        self.root.update_idletasks()
    
    def startGame(self):

        'game.main(self.win) #, root)'

        #Start pygame
        pygame.init()
        self.win = pygame.display.set_mode((512, 512))

        self.bg_color = (196, 64, 128)
        self.win.fill(self.bg_color)
        self.pos = 0, 0
        self.direction = 10, 10
        self.size = 40
        self.color = (0, 255, 0)
        self.root.after(30, self.update)

        self.root.mainloop()


    def update(self):

        pygame.draw.rect(self.win, self.bg_color, self.pos + (self.size, self.size))


        self.pos = self.pos[0] + self.direction[0], self.pos[1] + self.direction[1]


        if self.pos[0] < 0 or self.pos[0] > 512 - self.size:
            self.direction = -self.direction[0], self.direction[1]
            self.pos = self.pos[0] + 2 * self.direction[0], self.pos[1] + self.direction[1]
        if self.pos[1] < 0 or self.pos[1] > 512 - self.size:
            self.direction = self.direction[0], -self.direction[1]
            self.pos = self.pos[0] + self.direction[0], self.pos[1] + 2 * self.direction[1]

        pygame.draw.rect(self.win, self.color, self.pos + (self.size, self.size))
        pygame.display.flip()
        self.root.after(30, self.update)
'''

