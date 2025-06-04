import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import json
import os
import pyglet

# Константы для тетриса
WIDTH = 10
HEIGHT = 20
TILE_SIZE = 30  # Размер одной клетки
FPS = 3  # Количество кадров в секунду

# Цвета фигур
COLORS = [
    'cyan', 'blue', 'orange', 'yellow', 'green', 'purple', 'red'
]

# Фигуры
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1], [1, 1]],  # O
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]]   # J
]


def play_sound(file_path):
    """Воспроизводит звуковой файл."""
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден!")
        return

    try:
        sound = pyglet.media.load(file_path)
        sound.play()
    except Exception as e:
        print(f"Ошибка при воспроизведении звука: {e}")

class Tetris:
    def __init__(self, root, music_enabled, sound_enabled, return_to_menu_callback):
        """Инициализация игрового окна и состояния игры."""
        self.root = root
        self.root.title("Tetris")
        self.root.geometry("400x750")
        
        # Инициализация игрового состояния
        self.board = [[0] * WIDTH for _ in range(HEIGHT)]
        self.current_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.music_enabled = music_enabled
        self.sound_enabled = sound_enabled
        self.return_to_menu_callback = return_to_menu_callback
        self.paused = False
        self.music_player = None
        
        # Загрузка изображений
        self.load_images()
        
        # Настройка пользовательского интерфейса
        self.setup_ui()
        
        # Настройка управления
        self.root.bind("<Key>", self.on_key_press)
        
        # Запуск игры
        if self.music_enabled:
            self.play_music()
            
        self.update()
    
    def load_images(self):
        """Загружает все необходимые изображения для игры."""
        try:
            # Фоновое изображение
            game_bg_image = Image.open("images/game_background.jpg")
            self.game_bg_photo = ImageTk.PhotoImage(game_bg_image.resize((400, 750)))
            
            # Изображение игрового поля
            game_pole_image = Image.open("images/gamepole.jpg")
            self.game_pole_photo = ImageTk.PhotoImage(game_pole_image.resize((314, 614)))
            
            # Кнопки управления
            self.load_button_images()
            
        except FileNotFoundError as e:
            print(f"Ошибка загрузки изображения: {e}")
            self.game_bg_photo = ImageTk.PhotoImage(Image.new('RGB', (400, 750), 'black'))
            self.game_pole_photo = ImageTk.PhotoImage(Image.new('RGBA', (314, 614), (0, 0, 0, 0)))
    
    def load_button_images(self):
        """Загружает изображения для кнопок."""
        try:
            # Кнопка выхода
            exit_img = Image.open("images/exit.png")
            self.exit_photo = ImageTk.PhotoImage(exit_img.resize((100, 25)))
            
            # Кнопка настроек
            options_img = Image.open("images/optionsgame.png")
            self.options_photo = ImageTk.PhotoImage(options_img.resize((100, 28)))
            
            # Кнопки управления звуком (размер как у кнопки Play - 300x75)
            self.music_on_image = ImageTk.PhotoImage(Image.open("images/music_button_on.jpg").resize((300, 75), Image.LANCZOS))
            self.music_off_image = ImageTk.PhotoImage(Image.open("images/music_button_off.jpg").resize((300, 75), Image.LANCZOS))
            self.volume_on_image = ImageTk.PhotoImage(Image.open("images/volume_button_on.jpg").resize((300, 75), Image.LANCZOS))
            self.volume_off_image = ImageTk.PhotoImage(Image.open("images/volume_button_off.jpg").resize((300, 75), Image.LANCZOS))
            
            # Кнопка перезапуска
            replay_img = Image.open("images/replay_button.png")
            self.replay_photo = ImageTk.PhotoImage(replay_img.resize((300, 75), Image.LANCZOS))
            
        except FileNotFoundError as e:
            print(f"Ошибка загрузки изображения кнопки: {e}")
            self.create_fallback_buttons()
    
    def create_fallback_buttons(self):
        """Создает стандартные кнопки, если не удалось загрузить изображения."""
        self.exit_photo = None
        self.options_photo = None
        # Используем размер как у кнопки Play - 300x75 для заглушек
        self.music_on_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'green'))
        self.music_off_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'red'))
        self.volume_on_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'blue'))
        self.volume_off_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'gray'))
        self.replay_photo = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'purple'))
    
    def setup_ui(self):
        """Настраивает пользовательский интерфейс."""
        # Основной фрейм
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack()
        
        # Холст для отрисовки
        self.setup_canvas()
        
        # Кнопки управления
        self.setup_control_buttons()
        
        # Отображение счета
        self.setup_score_display()
    
    def setup_canvas(self):
        """Настраивает игровой холст."""
        self.canvas = tk.Canvas(self.main_frame, width=400, height=750, bg='black')
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.game_bg_photo)
        
        # Позиционирование игрового поля
        self.game_pole_offset_x = 50
        self.game_pole_offset_y = 43
        self.canvas.create_image(
            self.game_pole_offset_x,
            self.game_pole_offset_y,
            anchor=tk.NW,
            image=self.game_pole_photo
        )
        self.canvas.pack()
        
        # Отступы для игрового поля
        self.padding_x = (400 - WIDTH * TILE_SIZE) // 2 + 7
        self.padding_y = (750 - HEIGHT * TILE_SIZE) // 2 - 26
    
    def setup_control_buttons(self):
        """Настраивает кнопки управления."""
        # Кнопка выхода
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
        
        # Кнопка настроек
        self.options_button = tk.Button(
            self.main_frame,
            image=self.options_photo,
            command=self.show_options,
            borderwidth=0
        )
        self.options_button.place(x=284, y=12)
    
    def setup_score_display(self):
        """Настраивает отображение счета."""
        self.score_text = self.canvas.create_text(
            200, 50,
            text="0",
            font=("Arial", 24),
            fill="blue",
            anchor="center",
            tags="score"
        )

    def play_music(self):
        """Воспроизведение фоновой музыки."""
        if self.music_enabled:
            try:
                if self.music_player is None:  # Проверяем, не играет ли уже музыка
                    self.music_player = pyglet.media.Player()
                    music = pyglet.media.load("sounds/music.wav")
                    self.music_player.queue(music)
                    self.music_player.loop = True  # Зацикливаем музыку
                    self.music_player.play()
            except Exception as e:
                print(f"Ошибка при воспроизведении музыки: {e}")

    def stop_music(self):
        """Остановка фоновой музыки."""
        if self.music_player:
            self.music_player.pause()
            self.music_player = None

    def toggle_music(self, options_window):
        """Переключение состояния музыки."""
        self.music_enabled = not self.music_enabled
        self.music_button.config(image=self.music_on_image if self.music_enabled else self.music_off_image)
        if self.music_enabled:
            self.play_music()  # Запуск музыки, если она включена
        else:
            self.stop_music()  # Остановка музыки, если она выключена
        options_window.focus_set()

    def toggle_sound(self, options_window):
        """Переключение состояния звуков игры."""
        self.sound_enabled = not self.sound_enabled
        self.sound_button.config(image=self.volume_on_image if self.sound_enabled else self.volume_off_image)
        options_window.focus_set()

    def new_piece(self):
        shape = random.choice(SHAPES)
        color = random.choice(COLORS)
        return {
            'shape': shape,
            'color': color,
            'x': WIDTH // 2 - len(shape[0]) // 2,
            'y': 0
        }

    def draw_piece(self, piece, shadow=False):
        for y, row in enumerate(piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    fill_color = piece['color'] if not shadow else "gray"
                    outline_color = "white" if not shadow else "gray"
                    self.canvas.create_rectangle(
                        self.padding_x + (piece['x'] + x) * TILE_SIZE,
                        self.padding_y + (piece['y'] + y) * TILE_SIZE,
                        self.padding_x + (piece['x'] + x + 1) * TILE_SIZE,
                        self.padding_y + (piece['y'] + y + 1) * TILE_SIZE,
                        fill=fill_color, outline=outline_color, stipple="gray50" if shadow else None
                    )

    def draw_board(self):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.game_bg_photo)  # Фоновое изображение
        self.canvas.create_image(
            self.game_pole_offset_x,  # Смещение по X
            self.game_pole_offset_y,  # Смещение по Y
            anchor=tk.NW, image=self.game_pole_photo  # Новое изображение для границ
        )
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
        # Рисуем тень фигуры
        shadow_piece = self.calculate_shadow()
        self.draw_piece(shadow_piece, shadow=True)
        # Рисуем текущую фигуру
        self.draw_piece(self.current_piece)
        # Убедимся, что текст счета отображается поверх других элементов
        self.canvas.tag_raise("score")

    def calculate_shadow(self):
        # Создаем копию текущей фигуры
        shadow_piece = {
            'shape': self.current_piece['shape'],
            'color': self.current_piece['color'],
            'x': self.current_piece['x'],
            'y': self.current_piece['y']
        }
        # Симулируем падение фигуры до столкновения
        while not self.check_collision(shadow_piece, dy=1):
            shadow_piece['y'] += 1
        return shadow_piece

    def check_collision(self, piece, dx=0, dy=0):
        for y, row in enumerate(piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece['x'] + x + dx
                    new_y = piece['y'] + y + dy
                    # Проверяем выход за границы или пересечение с другими фигурами
                    if (new_x < 0 or 
                        new_x >= WIDTH or 
                        new_y >= HEIGHT or 
                        (new_y >= 0 and self.board[new_y][new_x])):
                        return True
        return False

    def merge_piece(self):
        """Объединяет текущую фигуру с игровым полем."""
        # Объединяем фигуру с полем
        for y, row in enumerate(self.current_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    board_y = self.current_piece['y'] + y
                    if 0 <= board_y < HEIGHT:  # Проверяем границы доски
                        self.board[board_y][self.current_piece['x'] + x] = COLORS.index(self.current_piece['color']) + 1
        
        if self.sound_enabled:
            play_sound("sounds/sound.wav")
            
        self.clear_lines()
        self.current_piece = self.new_piece()
        
        # Проверяем, может ли новая фигура быть размещена
        if self.check_collision(self.current_piece):
            # Проверяем, находится ли какая-либо часть фигуры в верхней видимой области
            if any(0 <= self.current_piece['y'] + y < 1  # Проверяем только верхнюю строку
                   for y, row in enumerate(self.current_piece['shape'])
                   for x, cell in enumerate(row) if cell):
                # Если да, и она сталкивается, то это конец игры
                self.game_over = True
                self.show_game_over()

    def clear_lines(self):
        lines_to_clear = [i for i, row in enumerate(self.board) if all(row)]
        for i in lines_to_clear:
            del self.board[i]
            self.board.insert(0, [0] * WIDTH)
        self.score += len(lines_to_clear)
        self.update_score()

    def update_score(self):
        """Обновляет отображение счета на экране."""
        self.canvas.itemconfig(self.score_text, text=f"{self.score}")
        self.canvas.tag_raise("score")

    def on_key_press(self, event):
        if self.game_over or self.paused:
            return
        if event.keysym == 'Left':
            if not self.check_collision(self.current_piece, dx=-1):
                self.current_piece['x'] -= 1
        elif event.keysym == 'Right':
            if not self.check_collision(self.current_piece, dx=1):
                self.current_piece['x'] += 1
        elif event.keysym == 'Down':
            if not self.check_collision(self.current_piece, dy=1):
                self.current_piece['y'] += 1
        elif event.keysym == 'Up':
            self.rotate_piece()
        self.draw_board()

    def rotate_piece(self):
        piece = self.current_piece
        shape = piece['shape']
        new_shape = [list(row) for row in zip(*shape[::-1])]
        if not self.check_collision({'shape': new_shape, 'x': piece['x'], 'y': piece['y']}):
            piece['shape'] = new_shape

    def show_game_over(self):
        # Звук при завершении игры
        if self.sound_enabled:
            play_sound("sounds/gameoversound.wav")

        # Кнопка "Replay"
        self.restart_button = tk.Button(
            self.main_frame,
            text="REPLAY",
            font=("Arial", 24, "bold"),
            width=10,
            height=2,
            bg="#4CAF50",  # Green color
            fg="black",  # Black text
            command=self.restart_game
        )
        # Центрируем кнопку по горизонтали
        button_width = 200  # Ширина кнопки в пикселях
        button_height = 50  # Высота кнопки в пикселях
        x_position = (400 - button_width) // 2  # Центр экрана по горизонтали
        self.restart_button.place(x=x_position, y=250, width=button_width, height=button_height)

        # Кнопка "Exit"
        self.menu_button = tk.Button(
            self.main_frame,
            text="EXIT",
            font=("Arial", 24, "bold"),
            width=10,
            height=2,
            bg="#f44336",  # Red color
            fg="black",  # Black text
            command=self.return_to_menu
        )
        # Располагаем кнопку Exit под кнопкой Replay с отступом 20 пикселей
        self.menu_button.place(x=x_position, y=320, width=button_width, height=button_height)


    def restart_game_from_options(self):
        # Закрываем окно настроек
        if hasattr(self, 'options_window') and self.options_window.winfo_exists():
            self.options_window.destroy()
        # Перезапускаем игру
        self.restart_game()

    def restart_game(self):
        # Останавливаем текущую музыку, если она играет
        self.stop_music()
        
        # Сбрасываем состояние игры
        self.board = [[0] * WIDTH for _ in range(HEIGHT)]
        self.current_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.update_score()
        self.paused = False  # Снимаем паузу

        # Удаляем кнопки, если они существуют
        if hasattr(self, 'restart_button'):
            self.restart_button.destroy()
        if hasattr(self, 'menu_button'):
            self.menu_button.destroy()

        # Закрываем окно настроек, если оно открыто
        if hasattr(self, 'options_window') and self.options_window.winfo_exists():
            self.options_window.destroy()

        # Очищаем холст
        self.canvas.delete("all")
        self.draw_board()  # Перерисовываем игровое поле

        # Запускаем музыку заново, если она включена
        if self.music_enabled:
            self.play_music()

        # Запускаем обновление игры
        self.update()
        
        # Возвращаем фокус в главное окно
        self.root.focus_set()

    def return_to_menu(self):
        # Останавливаем музыку
        self.stop_music()
        # Закрываем окно игры
        self.root.destroy()
        # Возвращаемся в главное меню
        self.return_to_menu_callback()

    def on_close(self):
        # Останавливаем музыку
        self.stop_music()
        # Закрываем окно игры
        self.root.destroy()
        # Завершаем программу
        self.root.quit()

    def show_options(self):
        # Открываем окно настроек
        self.paused = True  # Ставим игру на паузу
        self.options_window = tk.Toplevel(self.root)
        self.options_window.title("Options")
        self.options_window.geometry("400x750")  # Размер окна настроек

        # Загрузка фонового изображения для окна настроек
        try:
            options_bg_image = Image.open("images/options_background.jpg")
            options_bg_image = options_bg_image.resize((400, 750))
            self.options_bg_photo = ImageTk.PhotoImage(options_bg_image)
        except FileNotFoundError:
            self.options_bg_photo = ImageTk.PhotoImage(Image.new('RGB', (400, 750), 'black'))

        # Создаем холст для фона
        self.options_canvas = tk.Canvas(self.options_window, width=400, height=750)
        self.options_canvas.create_image(0, 0, anchor=tk.NW, image=self.options_bg_photo)
        self.options_canvas.pack()

        # Кнопка выхода (в том же стиле, что и в основном игровом окне)
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
        self.exit_button.place(x=10, y=13)  # Такие же координаты, как и в основном окне
        
        # Параметры кнопок (размер как у кнопки Play - 300x75)
        button_width = 300  # Ширина как у кнопки Play
        button_height = 75  # Высота как у кнопки Play
        button_spacing = 25  # Отступ между кнопками
        
        # Вычисляем общую высоту всех кнопок с отступами
        total_buttons_height = 3 * button_height + 2 * button_spacing
        
        # Центрирование по вертикали и горизонтали
        x_position = (400 - button_width) // 2
        start_y = (750 - total_buttons_height) // 2  # Центрируем по вертикали
        
        # Стиль для всех кнопок
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

        # Кнопка музыки
        self.music_button = tk.Button(
            self.options_window,
            image=self.music_on_image if self.music_enabled else self.music_off_image,
            command=lambda: self.toggle_music(self.options_window),
            **button_style
        )
        self.music_button.place(x=x_position, y=start_y, 
                              width=button_width, height=button_height)

        # Кнопка звуков
        self.sound_button = tk.Button(
            self.options_window,
            image=self.volume_on_image if self.sound_enabled else self.volume_off_image,
            command=lambda: self.toggle_sound(self.options_window),
            **button_style
        )
        self.sound_button.place(x=x_position, y=start_y + button_height + button_spacing, 
                              width=button_width, height=button_height)
        
        # Кнопка Replay
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

        # Обработка закрытия окна настроек
        self.options_window.protocol("WM_DELETE_WINDOW", lambda: self.close_options(self.options_window))

    def close_options(self, options_window):
        # Закрытие окна настроек и снятие паузы
        options_window.destroy()
        self.paused = False
        # Продолжаем обновление игры
        self.update()

    def update(self):
        if not self.game_over and not self.paused:
            if not self.check_collision(self.current_piece, dy=1):
                self.current_piece['y'] += 1
            else:
                self.merge_piece()
                # Если игра закончилась после объединения, не продолжаем обновление
                if self.game_over:
                    return
            self.draw_board()
            # Устанавливаем интервал времени в соответствии с FPS
            self.root.after(1000 // FPS, self.update)

class MainMenu:
    def __init__(self, root):
        """Инициализация главного меню."""
        self.root = root
        self.root.title("Tetris Main Menu")
        self.root.geometry("400x750")
        
        # Настройка состояния
        self.music_enabled = True
        self.sound_enabled = True
        
        # Загрузка изображений
        self.load_images()
        
        # Настройка пользовательского интерфейса
        self.setup_ui()
    
    def load_images(self):
        """Загружает все необходимые изображения для меню."""
        try:
            # Фоновое изображение
            menu_bg_image = Image.open("images/menu_background.jpg")
            self.menu_bg_photo = ImageTk.PhotoImage(menu_bg_image.resize((400, 750)))
            
            # Кнопки меню
            play_img = Image.open("images/play_button.png")
            self.play_photo = ImageTk.PhotoImage(play_img.resize((300, 75)))
            
            options_img = Image.open("images/options_button.png")
            self.options_photo = ImageTk.PhotoImage(options_img.resize((300, 75)))
            
            # Кнопки управления звуком (размер как у кнопки Play - 300x75)
            self.music_on_image = ImageTk.PhotoImage(Image.open("images/music_button_on.jpg").resize((300, 75), Image.LANCZOS))
            self.music_off_image = ImageTk.PhotoImage(Image.open("images/music_button_off.jpg").resize((300, 75), Image.LANCZOS))
            self.volume_on_image = ImageTk.PhotoImage(Image.open("images/volume_button_on.jpg").resize((300, 75), Image.LANCZOS))
            self.volume_off_image = ImageTk.PhotoImage(Image.open("images/volume_button_off.jpg").resize((300, 75), Image.LANCZOS))
            
        except FileNotFoundError as e:
            print(f"Ошибка загрузки изображений: {e}")
            self.create_fallback_images()
    
    def create_fallback_images(self):
        """Создает стандартные изображения, если не удалось загрузить файлы."""
        self.menu_bg_photo = ImageTk.PhotoImage(Image.new('RGB', (400, 750), 'black'))
        self.play_photo = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'green'))
        self.options_photo = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'blue'))
        # Кнопки управления звуком (размер как у кнопки Play - 300x75)
        self.music_on_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'green'))
        self.music_off_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'red'))
        self.volume_on_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'blue'))
        self.volume_off_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), 'gray'))
    
    def setup_ui(self):
        """Настраивает пользовательский интерфейс главного меню."""
        # Холст для фона
        self.menu_canvas = tk.Canvas(self.root, width=400, height=750)
        self.menu_canvas.create_image(0, 0, anchor=tk.NW, image=self.menu_bg_photo)
        self.menu_canvas.pack()
        
        # Кнопка Play
        self.play_button = tk.Button(
            self.root,
            image=self.play_photo,
            command=self.start_tetris,
            borderwidth=0,
            bg="black",
            activebackground="black"
        )
        self.play_button.place(x=51, y=540)
        
        # Кнопка Options
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
        # Закрываем меню и запускаем тетрис
        self.root.withdraw()  # Скрываем главное меню
        tetris_root = tk.Toplevel(self.root)
        game = Tetris(tetris_root, self.music_enabled, self.sound_enabled, self.show_main_menu)
        tetris_root.protocol("WM_DELETE_WINDOW", self.on_close_game)  # Обработка закрытия окна игры

    def on_close_game(self):
        # Закрываем окно игры
        self.root.quit()  # Завершаем программу

    def show_options(self):
        # Окно настроек
        self.options_window = tk.Toplevel(self.root)
        self.options_window.title("Options")
        self.options_window.geometry("400x750")  # Размер окна настроек

        # Загрузка фонового изображения для окна настроек
        try:
            options_bg_image = Image.open("images/options_background.jpg")
            options_bg_image = options_bg_image.resize((400, 750))  # Новый размер фона
            self.options_bg_photo = ImageTk.PhotoImage(options_bg_image)
        except FileNotFoundError:
            self.options_bg_photo = ImageTk.PhotoImage(Image.new('RGB', (400, 750), 'black'))

        # Создание холста для фона
        self.options_canvas = tk.Canvas(self.options_window, width=400, height=750)
        self.options_canvas.create_image(0, 0, anchor=tk.NW, image=self.options_bg_photo)
        self.options_canvas.pack()

        # Кнопка выхода (в том же стиле, что и в основном игровом окне)
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
        self.exit_button.place(x=10, y=13)  # Такие же координаты, как и в основном окне

        # Настройки кнопок (размер как у кнопки Play - 300x75)
        button_width = 300
        button_height = 75
        x_position = (400 - button_width) // 2  # Центрируем по горизонтали
        min_spacing = 30  # Расстояние между кнопками
        
        # Рассчитываем отступы для позиционирования блока кнопок
        total_buttons_height = 2 * button_height + min_spacing
        start_y = (750 - total_buttons_height) // 2 + 50  # Сдвигаем кнопки на 50 пикселей ниже центра
        
        # Позиция первой кнопки (музыка)
        music_button_y = start_y
        
        # Кнопка включения/выключения музыки (верхняя кнопка)
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

        # Кнопка включения/выключения звуков игры (нижняя кнопка)
        self.sound_button = tk.Button(
            self.options_window,
            image=self.volume_on_image if self.sound_enabled else self.volume_off_image,
            command=lambda: self.toggle_sound(self.options_window),
            borderwidth=0,
            width=button_width,
            height=button_height,
            bg='black'
        )
        # Позиция второй кнопки (звук) с минимальным отступом
        sound_button_y = music_button_y + button_height + min_spacing
        self.sound_button.place(x=x_position, y=sound_button_y, 
                              width=button_width, height=button_height)

    def toggle_music(self, options_window):
        # Переключение состояния музыки
        self.music_enabled = not self.music_enabled
        self.music_button.config(image=self.music_on_image if self.music_enabled else self.music_off_image)
        options_window.focus_set()

    def toggle_sound(self, options_window):
        # Переключение состояния звуков игры
        self.sound_enabled = not self.sound_enabled
        self.sound_button.config(image=self.volume_on_image if self.sound_enabled else self.volume_off_image)
        options_window.focus_set()

    def show_main_menu(self):
        # Показываем главное меню
        self.root.deiconify()  # Показываем главное меню
        if hasattr(self, 'tetris_root'):
            self.tetris_root.destroy()  # Закрываем окно игры, если оно существует

if __name__ == "__main__":
    root = tk.Tk()
    menu = MainMenu(root)
    root.mainloop()