import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import os
import pyglet
import threading
import time

WIDTH = 10
HEIGHT = 20
TILE_SIZE = 30
FPS = 3

COLORS = ['cyan', 'blue', 'orange', 'yellow', 'green', 'purple', 'red']

SHAPES = [
    [[1, 1, 1, 1]],
    [[1, 1, 1], [0, 1, 0]],
    [[1, 1], [1, 1]],
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1, 1], [1, 1, 0]],
    [[1, 1, 1], [1, 0, 0]],
    [[1, 1, 1], [0, 0, 1]]
]

def play_sound(file_path):
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден!")
        return
    try:
        sound = pyglet.media.load(file_path)
        sound.play()
    except Exception as e:
        print(f"Ошибка при воспроизведении звука: {e}")

class MusicPlayer:
    def __init__(self):
        self.player = pyglet.media.Player()
        self.source = None
        self.playing = False
        self.loop = True
        
    def load(self, file_path):
        if os.path.exists(file_path):
            self.source = pyglet.media.load(file_path)
            self.player.queue(self.source)
            
            @self.player.event
            def on_eos():
                if self.loop and self.playing:
                    self.player.seek(0)
                    self.player.play()
        else:
            print(f"Музыкальный файл {file_path} не найден!")
            
    def play(self):
        if self.source and not self.playing:
            self.player.play()
            self.playing = True
            
    def pause(self):
        if self.playing:
            self.player.pause()
            self.playing = False
            
    def stop(self):
        self.player.pause()
        self.player.seek(0)
        self.playing = False
        
    def set_loop(self, loop):
        self.loop = loop

class Tetris:
    def __init__(self, root, music_enabled, sound_enabled, return_to_menu_callback):
        self.root = root
        self.root.title("Tetris")
        self.root.geometry("400x750")
        
        self.board = [[0] * WIDTH for _ in range(HEIGHT)]
        self.current_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.music_enabled = music_enabled
        self.sound_enabled = sound_enabled
        self.return_to_menu_callback = return_to_menu_callback
        self.paused = False
        
        self.music_player = MusicPlayer()
        self.music_player.load("sounds/music.wav")
        self.music_player.set_loop(True)
        if self.music_enabled:
            self.music_player.play()
        
        self.keys_pressed = set()
        self.fast_fall = False
        
        self.load_images()
        
        self.setup_ui()
        
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        
        self.update()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_images(self):
        try:
            game_bg_image = Image.open("images/game_background.jpg")
            self.game_bg_photo = ImageTk.PhotoImage(game_bg_image.resize((400, 750)))
            
            game_pole_image = Image.open("images/gamepole.jpg")
            self.game_pole_photo = ImageTk.PhotoImage(game_pole_image.resize((314, 614)))
            
            exit_img = Image.open("images/exit.png")
            self.exit_photo = ImageTk.PhotoImage(exit_img.resize((100, 25)))
            
            options_img = Image.open("images/optionsgame.png")
            self.options_photo = ImageTk.PhotoImage(options_img.resize((100, 28)))
            
            self.music_on_image = ImageTk.PhotoImage(Image.open("images/music_button_on.jpg").resize((300, 75), Image.LANCZOS))
            self.music_off_image = ImageTk.PhotoImage(Image.open("images/music_button_off.jpg").resize((300, 75), Image.LANCZOS))
            self.volume_on_image = ImageTk.PhotoImage(Image.open("images/volume_button_on.jpg").resize((300, 75), Image.LANCZOS))
            self.volume_off_image = ImageTk.PhotoImage(Image.open("images/volume_button_off.jpg").resize((300, 75), Image.LANCZOS))
            
            replay_img = Image.open("images/replay_button.png")
            self.replay_photo = ImageTk.PhotoImage(replay_img.resize((300, 75), Image.LANCZOS))
            
        except FileNotFoundError as e:
            print(f"Ошибка загрузки изображения: {e}")
            self.game_bg_photo = ImageTk.PhotoImage(Image.new('RGB', (400, 750), 'black'))
            self.game_pole_photo = ImageTk.PhotoImage(Image.new('RGBA', (314, 614), (0, 0, 0, 0)))
            self.exit_photo = None
            self.options_photo = None
            self.music_on_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'green'))
            self.music_off_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'red'))
            self.volume_on_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'blue'))
            self.volume_off_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'gray'))
            self.replay_photo = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'purple'))

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack()
        
        self.canvas = tk.Canvas(self.main_frame, width=400, height=750, bg='black')
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.game_bg_photo)
        
        self.game_pole_offset_x = 50
        self.game_pole_offset_y = 43
        self.canvas.create_image(
            self.game_pole_offset_x,
            self.game_pole_offset_y,
            anchor=tk.NW,
            image=self.game_pole_photo
        )
        self.canvas.pack()
        
        self.padding_x = self.game_pole_offset_x + 7
        self.padding_y = self.game_pole_offset_y + 7
        
        self.exit_button = tk.Button(
            self.main_frame,
            image=self.exit_photo if self.exit_photo else None,
            text="Exit" if not self.exit_photo else "",
            font=("Arial", 12),
            command=self.return_to_menu,
            bg="red" if not self.exit_photo else "black",
            fg="white",
            borderwidth=0
        )
        self.exit_button.place(x=10, y=13)
        
        self.options_button = tk.Button(
            self.main_frame,
            image=self.options_photo,
            command=self.show_options,
            borderwidth=0
        )
        self.options_button.place(x=284, y=12)
        
        self.score_text = self.canvas.create_text(
            210, 722,
            text="0",
            font=("Arial", 36, "bold"),
            fill="#FFFFFF",
            width=400,
            anchor="center",
            tags=("score", "score_text")
        )
        
        self.canvas.tag_raise("score")

    def new_piece(self):
        shape = random.choice(SHAPES)
        color = random.choice(COLORS)
        return {
            'shape': shape,
            'color': color,
            'x': WIDTH // 2 - len(shape[0]) // 2,
            'y': -1
        }

    def draw_piece(self, piece, shadow=False):
        for y, row in enumerate(piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    if piece['y'] + y < 0:
                        continue
                        
                    fill_color = piece['color'] if not shadow else "gray"
                    outline_color = "white" if not shadow else "gray"
                    self.canvas.create_rectangle(
                        self.padding_x + (piece['x'] + x) * TILE_SIZE,
                        self.padding_y + (piece['y'] + y) * TILE_SIZE,
                        self.padding_x + (piece['x'] + x + 1) * TILE_SIZE,
                        self.padding_y + (piece['y'] + y + 1) * TILE_SIZE,
                        fill=fill_color, outline=outline_color, 
                        stipple="gray50" if shadow else None
                    )

    def draw_board(self):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.game_bg_photo)
        self.canvas.create_image(
            self.game_pole_offset_x,
            self.game_pole_offset_y,
            anchor=tk.NW, 
            image=self.game_pole_photo,
            tags="game"
        )
        
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if self.board[y][x]:
                    self.canvas.create_rectangle(
                        self.padding_x + x * TILE_SIZE,
                        self.padding_y + y * TILE_SIZE,
                        self.padding_x + (x + 1) * TILE_SIZE,
                        self.padding_y + (y + 1) * TILE_SIZE,
                        fill=COLORS[self.board[y][x] - 1], 
                        outline='white',
                        tags="blocks"
                    )
        
        shadow_piece = self.calculate_shadow()
        self.draw_piece(shadow_piece, shadow=True)
        
        self.draw_piece(self.current_piece)
        
        self.update_score()
        
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if self.board[y][x]:
                    self.canvas.create_rectangle(
                        self.padding_x + x * TILE_SIZE,
                        self.padding_y + y * TILE_SIZE,
                        self.padding_x + (x + 1) * TILE_SIZE,
                        self.padding_y + (y + 1) * TILE_SIZE,
                        fill=COLORS[self.board[y][x] - 1], outline='white'
                    )
        
        shadow_piece = self.calculate_shadow()
        self.draw_piece(shadow_piece, shadow=True)
        
        self.draw_piece(self.current_piece)
        
        self.update_score()

    def calculate_shadow(self):
        shadow_piece = {
            'shape': self.current_piece['shape'],
            'color': self.current_piece['color'],
            'x': self.current_piece['x'],
            'y': self.current_piece['y']
        }
        while not self.check_collision(shadow_piece, dy=1):
            shadow_piece['y'] += 1
        return shadow_piece

    def check_collision(self, piece, dx=0, dy=0):
        for y, row in enumerate(piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece['x'] + x + dx
                    new_y = piece['y'] + y + dy
                    if (new_x < 0 or 
                        new_x >= WIDTH or 
                        new_y >= HEIGHT or 
                        (new_y >= 0 and self.board[new_y][new_x])):
                        return True
        return False

    def merge_piece(self):
        for y, row in enumerate(self.current_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    board_y = self.current_piece['y'] + y
                    if 0 <= board_y < HEIGHT:
                        self.board[board_y][self.current_piece['x'] + x] = COLORS.index(self.current_piece['color']) + 1
        
        if self.sound_enabled:
            play_sound("sounds/sound.wav")
            
        self.clear_lines()
        self.current_piece = self.new_piece()
        
        if self.check_collision(self.current_piece, dy=0):
            self.game_over = True
            self.music_player.stop()
            self.show_game_over()

    def clear_lines(self):
        lines_to_clear = [i for i, row in enumerate(self.board) if all(row)]
        for i in lines_to_clear:
            del self.board[i]
            self.board.insert(0, [0] * WIDTH)
        self.score += len(lines_to_clear) * 100
        self.update_score()

    def update_score(self):
        self.canvas.delete("score_text")
        
        self.score_text = self.canvas.create_text(
            210, 722,
            text=f"{self.score}",
            font=("Arial", 36, "bold"),
            fill="#FFFFFF",
            width=400,
            anchor="center",
            tags=("score", "score_text")
        )
        
        self.canvas.tag_raise("score")

    def on_key_press(self, event):
        if self.game_over or self.paused:
            return
            
        if event.keysym == 'Left':
            if not self.check_collision(self.current_piece, dx=-1):
                self.current_piece['x'] -= 1
                self.draw_board()
        elif event.keysym == 'Right':
            if not self.check_collision(self.current_piece, dx=1):
                self.current_piece['x'] += 1
                self.draw_board()
        elif event.keysym == 'Down':
            self.fast_fall = True
            if not self.check_collision(self.current_piece, dy=1):
                self.current_piece['y'] += 1
                self.draw_board()
        elif event.keysym == 'Up':
            self.rotate_piece()
            self.draw_board()
    
    def on_key_release(self, event):
        if event.keysym == 'Down':
            self.fast_fall = False

    def rotate_piece(self):
        piece = self.current_piece
        shape = piece['shape']
        new_shape = [list(row) for row in zip(*shape[::-1])]
        if not self.check_collision({'shape': new_shape, 'x': piece['x'], 'y': piece['y']}):
            piece['shape'] = new_shape

    def show_game_over(self):
        if self.sound_enabled:
            play_sound("sounds/gameoversound.wav")

        self.restart_button = tk.Button(
            self.main_frame,
            text="REPLAY",
            font=("Arial", 24, "bold"),
            width=10,
            height=2,
            bg="#4CAF50",
            fg="black",
            command=self.restart_game
        )
        button_width = 200
        button_height = 50
        x_position = (400 - button_width) // 2
        self.restart_button.place(x=x_position, y=250, width=button_width, height=button_height)

        self.menu_button = tk.Button(
            self.main_frame,
            text="EXIT",
            font=("Arial", 24, "bold"),
            width=10,
            height=2,
            bg="#f44336",
            fg="black",
            command=self.return_to_menu
        )
        self.menu_button.place(x=x_position, y=320, width=button_width, height=button_height)

    def show_options(self):
        self.paused = True
        self.music_player.pause()
        self.options_window = tk.Toplevel(self.root)
        self.options_window.title("Options")
        self.options_window.geometry("400x750")

        try:
            options_bg_image = Image.open("images/options_background.jpg")
            options_bg_image = options_bg_image.resize((400, 750))
            self.options_bg_photo = ImageTk.PhotoImage(options_bg_image)
        except FileNotFoundError:
            self.options_bg_photo = ImageTk.PhotoImage(Image.new('RGB', (400, 750), 'black'))

        self.options_canvas = tk.Canvas(self.options_window, width=400, height=750)
        self.options_canvas.create_image(0, 0, anchor=tk.NW, image=self.options_bg_photo)
        self.options_canvas.pack()

        try:
            exit_img = Image.open("images/exit.png")
            exit_img = exit_img.resize((100, 25))
            self.exit_photo_options = ImageTk.PhotoImage(exit_img)
        except FileNotFoundError:
            self.exit_photo_options = None
            
        self.exit_button = tk.Button(
            self.options_window,
            image=self.exit_photo_options if self.exit_photo_options else None,
            text="Exit" if not self.exit_photo_options else "",
            font=("Arial", 12),
            command=lambda: self.close_options(self.options_window),
            bg="red" if not self.exit_photo_options else "black",
            fg="white",
            borderwidth=0
        )
        self.exit_button.place(x=10, y=13)
        
        button_width = 300
        button_height = 75
        button_spacing = 25
        total_buttons_height = 3 * button_height + 2 * button_spacing
        x_position = (400 - button_width) // 2
        start_y = (750 - total_buttons_height) // 2
        
        button_style = {
            'borderwidth': 0,
            'highlightthickness': 0,
            'width': button_width,
            'height': button_height,
            'bg': 'black',
            'activebackground': '#333333',
            'compound': 'center',
            'relief': 'flat'
        }

        self.music_button = tk.Button(
            self.options_window,
            image=self.music_on_image if self.music_enabled else self.music_off_image,
            command=lambda: self.toggle_music(self.options_window),
            **button_style
        )
        self.music_button.place(x=x_position, y=start_y, 
                              width=button_width, height=button_height)

        self.sound_button = tk.Button(
            self.options_window,
            image=self.volume_on_image if self.sound_enabled else self.volume_off_image,
            command=lambda: self.toggle_sound(self.options_window),
            **button_style
        )
        self.sound_button.place(x=x_position, y=start_y + button_height + button_spacing, 
                              width=button_width, height=button_height)
        
        try:
            replay_img = Image.open("images/replay_button.png")
            replay_img = replay_img.resize((button_width, button_height), Image.LANCZOS)
            self.replay_photo_options = ImageTk.PhotoImage(replay_img)
            has_replay_image = True
        except FileNotFoundError:
            print("Replay button image not found, using text button")
            self.replay_photo_options = None
            has_replay_image = False
            
        self.replay_button = tk.Button(
            self.options_window,
            image=self.replay_photo_options if has_replay_image else None,
            text="Replay" if not has_replay_image else "",
            font=("Arial", 14, "bold") if not has_replay_image else None,
            fg='white' if not has_replay_image else None,
            command=self.restart_game_from_options,
            **button_style
        )
        self.replay_button.place(x=x_position, 
                               y=start_y + 2 * (button_height + button_spacing),
                               width=button_width, 
                               height=button_height)

        self.options_window.protocol("WM_DELETE_WINDOW", lambda: self.close_options(self.options_window))

    def close_options(self, options_window):
        options_window.destroy()
        self.paused = False
        if self.music_enabled and not self.game_over:
            self.music_player.play()
        self.update()

    def toggle_music(self, options_window):
        self.music_enabled = not self.music_enabled
        self.music_button.config(image=self.music_on_image if self.music_enabled else self.music_off_image)
        
        if self.music_enabled:
            self.music_player.play()
        else:
            self.music_player.pause()
            
        options_window.focus_set()

    def toggle_sound(self, options_window):
        self.sound_enabled = not self.sound_enabled
        self.sound_button.config(image=self.volume_on_image if self.sound_enabled else self.volume_off_image)
        options_window.focus_set()

    def restart_game_from_options(self):
        if hasattr(self, 'options_window') and self.options_window.winfo_exists():
            self.options_window.destroy()
        self.restart_game()

    def restart_game(self):
        self.music_player.stop()
            
        self.board = [[0] * WIDTH for _ in range(HEIGHT)]
        self.current_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.update_score()
        self.paused = False

        if hasattr(self, 'restart_button'):
            self.restart_button.destroy()
        if hasattr(self, 'menu_button'):
            self.menu_button.destroy()

        if self.music_enabled:
            self.music_player.play()

        self.canvas.delete("all")
        self.draw_board()
        self.update()

    def return_to_menu(self):
        self.music_player.stop()
        self.root.destroy()
        self.return_to_menu_callback()

    def on_close(self):
        self.music_player.stop()
        self.root.destroy()

    def update(self):
        if not self.game_over and not self.paused:
            if self.fast_fall:
                if not self.check_collision(self.current_piece, dy=1):
                    self.current_piece['y'] += 1
                    self.draw_board()
                    self.root.after(50, self.update)
                    return
                else:
                    self.merge_piece()
                    if self.game_over:
                        return
            else:
                if not self.check_collision(self.current_piece, dy=1):
                    self.current_piece['y'] += 1
                    self.draw_board()
                else:
                    self.merge_piece()
                    if self.game_over:
                        return
            
            self.root.after(1000 // FPS, self.update)

class MainMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("Tetris Main Menu")
        self.root.geometry("400x750")
        
        self.music_enabled = True
        self.sound_enabled = True
        
        self.music_player = MusicPlayer()
        self.music_player.load("sounds/menu_music.wav")
        self.music_player.set_loop(True)
        if self.music_enabled:
            self.music_player.play()
        
        self.load_images()
        self.setup_ui()

    def load_images(self):
        try:
            menu_bg_image = Image.open("images/menu_background.jpg")
            self.menu_bg_photo = ImageTk.PhotoImage(menu_bg_image.resize((400, 750)))
            
            play_img = Image.open("images/play_button.png")
            self.play_photo = ImageTk.PhotoImage(play_img.resize((300, 75)))
            
            options_img = Image.open("images/options_button.png")
            self.options_photo = ImageTk.PhotoImage(options_img.resize((300, 75)))
            
            self.music_on_image = ImageTk.PhotoImage(Image.open("images/music_button_on.jpg").resize((300, 75), Image.LANCZOS))
            self.music_off_image = ImageTk.PhotoImage(Image.open("images/music_button_off.jpg").resize((300, 75), Image.LANCZOS))
            self.volume_on_image = ImageTk.PhotoImage(Image.open("images/volume_button_on.jpg").resize((300, 75), Image.LANCZOS))
            self.volume_off_image = ImageTk.PhotoImage(Image.open("images/volume_button_off.jpg").resize((300, 75), Image.LANCZOS))
            
        except FileNotFoundError as e:
            print(f"Ошибка загрузки изображений: {e}")
            self.create_fallback_images()

    def create_fallback_images(self):
        self.menu_bg_photo = ImageTk.PhotoImage(Image.new('RGB', (400, 750), 'black'))
        self.play_photo = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'green'))
        self.options_photo = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'blue'))
        self.music_on_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'green'))
        self.music_off_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'red'))
        self.volume_on_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'blue'))
        self.volume_off_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'gray'))

    def setup_ui(self):
        self.menu_canvas = tk.Canvas(self.root, width=400, height=750)
        self.menu_canvas.create_image(0, 0, anchor=tk.NW, image=self.menu_bg_photo)
        self.menu_canvas.pack()
        
        self.play_button = tk.Button(
            self.root,
            image=self.play_photo,
            command=self.start_tetris,
            borderwidth=0,
            bg="black",
            activebackground="black"
        )
        self.play_button.place(x=51, y=540)
        
        self.options_button = tk.Button(
            self.root,
            image=self.options_photo,
            command=self.show_options,
            borderwidth=0,
            bg="black",
            activebackground="black"
        )
        self.options_button.place(x=51, y=640)

    def start_tetris(self):
        self.music_player.stop()
        
        tetris_root = tk.Toplevel(self.root)
        game = Tetris(tetris_root, self.music_enabled, self.sound_enabled, self.show_main_menu)
        
        self.root.withdraw()
        
        tetris_root.protocol("WM_DELETE_WINDOW", self.on_close_game)

    def on_close_game(self):
        if self.music_enabled:
            self.music_player.play()
        self.root.deiconify()

    def show_options(self):
        self.options_window = tk.Toplevel(self.root)
        self.options_window.title("Options")
        self.options_window.geometry("400x750")

        try:
            options_bg_image = Image.open("images/options_background.jpg")
            options_bg_image = options_bg_image.resize((400, 750))
            self.options_bg_photo = ImageTk.PhotoImage(options_bg_image)
        except FileNotFoundError:
            self.options_bg_photo = ImageTk.PhotoImage(Image.new('RGB', (400, 750), 'black'))

        self.options_canvas = tk.Canvas(self.options_window, width=400, height=750)
        self.options_canvas.create_image(0, 0, anchor=tk.NW, image=self.options_bg_photo)
        self.options_canvas.pack()

        try:
            exit_img = Image.open("images/exit.png")
            exit_img = exit_img.resize((100, 25))
            self.exit_photo_options = ImageTk.PhotoImage(exit_img)
        except FileNotFoundError:
            self.exit_photo_options = None
            
        self.exit_button = tk.Button(
            self.options_window,
            image=self.exit_photo_options if self.exit_photo_options else None,
            text="Exit" if not self.exit_photo_options else "",
            font=("Arial", 12),
            command=self.options_window.destroy,
            bg="red" if not self.exit_photo_options else "black",
            fg="white",
            borderwidth=0
        )
        self.exit_button.place(x=10, y=13)

        button_width = 300
        button_height = 75
        x_position = (400 - button_width) // 2
        min_spacing = 30
        
        total_buttons_height = 2 * button_height + min_spacing
        start_y = (750 - total_buttons_height) // 2 + 50
        
        music_button_y = start_y
        
        self.music_button = tk.Button(
            self.options_window,
            image=self.music_on_image if self.music_enabled else self.music_off_image,
            command=lambda: self.toggle_music(self.options_window),
            borderwidth=0,
            width=button_width,
            height=button_height,
            bg='black'
        )
        self.music_button.place(x=x_position, y=music_button_y, 
                              width=button_width, height=button_height)

        self.sound_button = tk.Button(
            self.options_window,
            image=self.volume_on_image if self.sound_enabled else self.volume_off_image,
            command=lambda: self.toggle_sound(self.options_window),
            borderwidth=0,
            width=button_width,
            height=button_height,
            bg='black'
        )
        sound_button_y = music_button_y + button_height + min_spacing
        self.sound_button.place(x=x_position, y=sound_button_y, 
                              width=button_width, height=button_height)

    def toggle_music(self, options_window):
        self.music_enabled = not self.music_enabled
        self.music_button.config(image=self.music_on_image if self.music_enabled else self.music_off_image)
        
        if self.music_enabled:
            self.music_player.play()
        else:
            self.music_player.pause()
            
        options_window.focus_set()

    def toggle_sound(self, options_window):
        self.sound_enabled = not self.sound_enabled
        self.sound_button.config(image=self.volume_on_image if self.sound_enabled else self.volume_off_image)
        options_window.focus_set()

    def show_main_menu(self):
        self.root.deiconify()
        if hasattr(self, 'tetris_root'):
            self.tetris_root.destroy()
        if self.music_enabled:
            self.music_player.play()

def update_file_paths():
    try:
        with open('tetris.py', 'r', encoding='utf-8') as file:
            content = file.read()
        
        updated_content = re.sub(
            r'Image\.open\("((?!images/)(?!sounds/))([^"]+\.(?:png|jpg|jpeg))"\)',
            r'Image.open("images/\2")',
            content
        )
        
        updated_content = re.sub(
            r'play_sound\("([^"]+\.wav)"\)',
            r'play_sound("sounds/\1")',
            updated_content
        )
        
        updated_content = re.sub(
            r'pyglet\.media\.load\("([^"]+\.wav)"\)',
            r'pyglet.media.load("sounds/\1")',
            updated_content
        )
        
        if updated_content != content:
            with open('tetris.py', 'w', encoding='utf-8') as file:
                file.write(updated_content)
            print("Пути к файлам успешно обновлены!")
            return True
        return False
    except Exception as e:
        print(f"Ошибка при обновлении путей: {e}")
        return False

if __name__ == "__main__":
    import sys
    import re
    
    if len(sys.argv) > 1 and sys.argv[1] == "--update-paths":
        if update_file_paths():
            print("Файл tetris.py успешно обновлен с новыми путями.")
        else:
            print("Обновление путей не потребовалось или произошла ошибка.")
        sys.exit(0)
    
    root = tk.Tk()
    menu = MainMenu(root)
    root.mainloop()