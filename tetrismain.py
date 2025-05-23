import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import random
import json
import os
import pyglet  # Используем pyglet для воспроизведения звука

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

# Файл для сохранения рекорда
HIGH_SCORE_FILE = "high_score.json"

# Функция для воспроизведения звука
def play_sound(file_path):
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден!")
        return

    print(f"Воспроизведение звука: {file_path}")  # Отладочное сообщение
    try:
        sound = pyglet.media.load(file_path)
        sound.play()
    except Exception as e:
        print(f"Ошибка при воспроизведении звука: {e}")

def round_corners(image_path, output_path, corner_radius):
    """
    Создает изображение с закругленными краями.
    
    :param image_path: Путь к исходному изображению.
    :param output_path: Путь для сохранения обработанного изображения.
    :param corner_radius: Радиус закругления углов.
    """
    # Загружаем изображение
    image = Image.open(image_path).convert("RGBA")
    width, height = image.size

    # Создаем маску с закругленными углами
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, width, height), corner_radius, fill=255)

    # Применяем маску к изображению
    result = Image.new("RGBA", (width, height))
    result.paste(image, (0, 0), mask)

    # Сохраняем результат
    result.save(output_path)

class Tetris:
    def __init__(self, root, music_enabled, sound_enabled, return_to_menu_callback):
        self.root = root
        self.root.title("Tetris")
        self.root.geometry("400x750")  # Размер игрового окна

        # Загрузка фонового изображения для игрового поля
        try:
            game_bg_image = Image.open("game_background.jpg")
            game_bg_image = game_bg_image.resize((400, 750))  # Новый размер фона
            self.game_bg_photo = ImageTk.PhotoImage(game_bg_image)
        except FileNotFoundError:
            self.game_bg_photo = ImageTk.PhotoImage(Image.new('RGB', (400, 750), color='black'))

        # Загрузка нового изображения для границ игрового поля
        try:
            game_pole_image = Image.open("gamepole.jpg")  # Новое изображение для границ
            game_pole_image = game_pole_image.resize((314, 614))  # Новый размер
            self.game_pole_photo = ImageTk.PhotoImage(game_pole_image)
        except FileNotFoundError:
            self.game_pole_photo = ImageTk.PhotoImage(Image.new('RGBA', (314, 614), color=(0, 0, 0, 0)))  # Прозрачный фон, если изображение не найдено

        # Основной фрейм для игрового поля и счета
        self.main_frame = tk.Frame(root)
        self.main_frame.pack()

        # Холст для игрового поля
        self.canvas = tk.Canvas(self.main_frame, width=400, height=750, bg='black')
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.game_bg_photo)  # Фоновое изображение

        # Отступы для изображения gamepole.jpg (вправо и вниз)
        self.game_pole_offset_x = 50  # Смещение вправо
        self.game_pole_offset_y = 43  # Смещение вниз
        self.canvas.create_image(
            self.game_pole_offset_x,  # Смещение по X
            self.game_pole_offset_y,  # Смещение по Y
            anchor=tk.NW, image=self.game_pole_photo  # Новое изображение для границ
        )
        self.canvas.pack()

        # Отступы для игрового поля
        self.padding_x = (400 - WIDTH * TILE_SIZE) // 2 + 7 # Отступ по горизонтали
        self.padding_y = (750 - HEIGHT * TILE_SIZE) // 2 - 26 # Отступ по вертикали

        # Загрузка изображения для кнопки Exit
        try:
            exit_image = Image.open("exit.png")  # Убедитесь, что файл exit.png существует
            exit_image = exit_image.resize((100, 25))  # Измените размер изображения, если нужно
            self.exit_photo = ImageTk.PhotoImage(exit_image)
        except FileNotFoundError:
            print("Файл exit.png не найден! Используется стандартная кнопка.")
            self.exit_photo = None

        # Кнопка Exit с изображением
        self.exit_button = tk.Button(
            self.main_frame,
            image=self.exit_photo if self.exit_photo else None,  # Используем изображение, если оно загружено
            text="Exit" if not self.exit_photo else "",  # Текст, если изображение не загружено
            font=("Arial", 12),
            command=self.return_to_menu,
            bg="red" if not self.exit_photo else "black",  # Цвет фона, если нет изображения
            fg="white",  # Цвет текста, если нет изображения
            borderwidth=0  # Убираем границу кнопки
        )
        self.exit_button.place(x=10, y=13)  # Позиция в левом верхнем углу

        # Загрузка изображения для кнопки Options
        try:
            options_image = Image.open("optionsgame.png")
            options_image = options_image.resize((100, 28))
            self.options_photo = ImageTk.PhotoImage(options_image)
        except FileNotFoundError:
            self.options_photo = ImageTk.PhotoImage(Image.new('RGB', (100, 28), color='gray'))

        # Кнопка Options
        self.options_button = tk.Button(
            self.main_frame,
            image=self.options_photo,
            command=self.show_options,
            borderwidth=0
        )
        self.options_button.place(x=493 - 209, y=12)  # Позиция в правом верхнем углу

        # Текст для отображения счета на холсте
        self.score_text = self.canvas.create_text(
            200,  # Позиция по X (центр)
            50,   # Позиция по Y (подняли выше)
            text="0",  # Начальное значение счета
            font=("Arial", 24),  # Шрифт и размер
            fill="blue",  # Цвет текста (синий)
            anchor="center",  # Выравнивание по центру
            tags="score"  # Добавляем тег для текста счета
        )

        # Инициализация игры
        self.board = [[0] * WIDTH for _ in range(HEIGHT)]
        self.current_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.music_enabled = music_enabled
        self.sound_enabled = sound_enabled
        self.return_to_menu_callback = return_to_menu_callback
        self.paused = False
        self.root.bind("<Key>", self.on_key_press)

        # Переменная для управления музыкой
        self.music_player = None

        # Загрузка изображений для кнопок музыки и звука
        try:
            # Загружаем оригинальные изображения кнопок
            self.music_on_image = ImageTk.PhotoImage(Image.open("music_button_on.jpg").resize((300, 75)))
            self.music_off_image = ImageTk.PhotoImage(Image.open("music_button_off.jpg").resize((300, 75)))
            self.volume_on_image = ImageTk.PhotoImage(Image.open("volume_button_on.jpg").resize((300, 75)))
            self.volume_off_image = ImageTk.PhotoImage(Image.open("volume_button_off.jpg").resize((300, 75)))
        except FileNotFoundError:
            print("Один или несколько файлов изображений для кнопок не найдены!")
            # Используем стандартные изображения, если файлы не найдены
            self.music_on_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), color='green'))
            self.music_off_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), color='red'))
            self.volume_on_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), color='blue'))
            self.volume_off_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), color='gray'))

        # Загрузка изображения для кнопки Replay
        try:
            replay_image = Image.open("replay_button.png")
            replay_image = replay_image.resize((300, 75))  # Измените размер изображения, если нужно
            self.replay_photo = ImageTk.PhotoImage(replay_image)
        except FileNotFoundError:
            print("Файл replay_button.png не найден! Используется стандартная кнопка.")
            self.replay_photo = None

        # Запуск музыки, если она включена
        if self.music_enabled:
            self.play_music()

        # Обработка закрытия окна игры через крестик
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.update()

    def play_music(self):
        """Воспроизведение фоновой музыки."""
        if self.music_enabled:
            try:
                if self.music_player is None:  # Проверяем, не играет ли уже музыка
                    self.music_player = pyglet.media.Player()
                    music = pyglet.media.load("music.wav")
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
                    if new_x < 0 or new_x >= WIDTH or new_y >= HEIGHT or (new_y >= 0 and self.board[new_y][new_x]):
                        return True
        return False

    def merge_piece(self):
        for y, row in enumerate(self.current_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    self.board[self.current_piece['y'] + y][self.current_piece['x'] + x] = COLORS.index(self.current_piece['color']) + 1
        if self.sound_enabled:
            play_sound("sound.wav")  # Звук, когда фигура упала и достигла края
        self.clear_lines()
        self.current_piece = self.new_piece()
        if self.check_collision(self.current_piece):
            self.game_over = True
            self.show_game_over()
        # Не вызываем self.update() здесь, чтобы избежать дублирования

    def clear_lines(self):
        lines_to_clear = [i for i, row in enumerate(self.board) if all(row)]
        for i in lines_to_clear:
            del self.board[i]
            self.board.insert(0, [0] * WIDTH)
        self.score += len(lines_to_clear)
        self.update_score()

    def update_score(self):
        # Обновляем текст счета на холсте
        self.canvas.itemconfig(self.score_text, text=f"{self.score}")
        self.canvas.tag_raise("score")  # Поднимаем текст счета на верхний план
        print(f"Счет обновлен: {self.score}")  # Отладочное сообщение

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
            play_sound("gameoversound.wav")  # Воспроизводим ваш звук при окончании игры

        # Отображаем текст "Game Over" и кнопки
        self.game_over_text = self.canvas.create_text(
            493 // 2,
            892 // 2 - 50,
            text="Game Over",
            fill="white",
            font=("Arial", 24)
        )

        # Анимация мигания текста
        self.blink_game_over_text()

        # Кнопка "Играть снова"
        self.restart_button = tk.Button(
            self.main_frame,
            text="Играть снова",
            font=("Arial", 16),
            command=self.restart_game
        )
        self.restart_button.place(x=493 // 2 - 70, y=892 // 2 + 10)  # Позиция кнопки

        # Кнопка "Выйти в меню"
        self.menu_button = tk.Button(
            self.main_frame,
            text="Выйти в меню",
            font=("Arial", 16),
            command=self.return_to_menu
        )
        self.menu_button.place(x=493 // 2 - 70, y=892 // 2 + 60)  # Позиция кнопки

        # Сохраняем рекорд
        self.save_high_score()

    def blink_game_over_text(self):
        # Анимация мигания текста "Game Over"
        if self.game_over:
            current_color = self.canvas.itemcget(self.game_over_text, "fill")
            new_color = "red" if current_color == "white" else "white"
            self.canvas.itemconfig(self.game_over_text, fill=new_color)
            self.root.after(500, self.blink_game_over_text)

    def save_high_score(self):
        # Сохраняем рекорд в файл
        high_score = self.load_high_score()
        if self.score > high_score:
            high_score = self.score
            with open(HIGH_SCORE_FILE, "w") as file:
                json.dump({"high_score": high_score}, file)
        # Отображаем рекорд
        self.canvas.create_text(
            493 // 2,
            892 // 2,
            text=f"Рекорд: {high_score}",
            fill="white",
            font=("Arial", 16)
        )

    def load_high_score(self):
        # Загружаем рекорд из файла
        if os.path.exists(HIGH_SCORE_FILE):
            with open(HIGH_SCORE_FILE, "r") as file:
                data = json.load(file)
                return data.get("high_score", 0)
        return 0

    def restart_game(self):
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

        # Очищаем холст
        self.canvas.delete("all")
        self.draw_board()  # Перерисовываем игровое поле

        # Запускаем обновление игры
        self.update()

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
        options_window = tk.Toplevel(self.root)
        options_window.title("Options")
        options_window.geometry("400x750")  # Размер окна настроек

        # Загрузка фонового изображения для окна настроек
        try:
            options_bg_image = Image.open("options_background.jpg")
            options_bg_image = options_bg_image.resize((400, 750))  # Новый размер фона
            self.options_bg_photo = ImageTk.PhotoImage(options_bg_image)
        except FileNotFoundError:
            self.options_bg_photo = ImageTk.PhotoImage(Image.new('RGB', (400, 750), color='gray'))

        # Создание холста для фона
        options_canvas = tk.Canvas(options_window, width=400, height=750)
        options_canvas.create_image(0, 0, anchor=tk.NW, image=self.options_bg_photo)
        options_canvas.pack()

        # Настройки кнопок
        button_width = 300
        button_height = 75
        x_position = (400 - button_width) // 2  # Центрируем по горизонтали
        min_spacing = 20  # Расстояние между кнопками
        
        # Рассчитываем отступы для позиционирования блока кнопок
        total_buttons_height = 2 * button_height + min_spacing
        start_y = (750 - total_buttons_height) // 2 + 50  # Сдвигаем кнопки на 50 пикселей ниже центра
        
        # Позиция первой кнопки (музыка)
        music_button_y = start_y
        
        # Кнопка включения/выключения музыки (верхняя кнопка)
        self.music_button = tk.Button(
            options_window,
            image=self.music_on_image if self.music_enabled else self.music_off_image,
            command=lambda: self.toggle_music(options_window),
            borderwidth=0,
            width=button_width,
            height=button_height
        )
        self.music_button.place(x=x_position, y=music_button_y, 
                              width=button_width, height=button_height)

        # Кнопка включения/выключения звуков игры (нижняя кнопка)
        self.sound_button = tk.Button(
            options_window,
            image=self.volume_on_image if self.sound_enabled else self.volume_off_image,
            command=lambda: self.toggle_sound(options_window),
            borderwidth=0,
            width=button_width,
            height=button_height
        )
        # Позиция второй кнопки (звук) с минимальным отступом
        sound_button_y = music_button_y + button_height + min_spacing
        self.sound_button.place(x=x_position, y=sound_button_y, 
                              width=button_width, height=button_height)

        # Кнопка "Replay" с изображением (нижняя кнопка)
        replay_button_y = sound_button_y + button_height + min_spacing
        self.replay_button = tk.Button(
            options_window,
            image=self.replay_photo if self.replay_photo else None,
            text="Replay" if not self.replay_photo else "",
            font=("Arial", 14),
            command=lambda: self.restart_game_from_options(options_window),
            bg="black",
            fg="white",
            borderwidth=0,
            width=button_width,
            height=button_height
        )
        self.replay_button.place(x=x_position, y=replay_button_y, 
                               width=button_width, height=button_height)

        # Обработка закрытия окна настроек
        options_window.protocol("WM_DELETE_WINDOW", lambda: self.close_options(options_window))

    def restart_game_from_options(self, options_window):
        # Закрываем окно настроек
        options_window.destroy()
        # Сбрасываем состояние игры
        self.restart_game()

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
            self.draw_board()
            # Устанавливаем интервал времени в соответствии с FPS
            self.root.after(1000 // FPS, self.update)

class MainMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("Tetris Main Menu")
        self.root.geometry("400x750")  # Размер главного меню

        # Загрузка фонового изображения для главного меню
        try:
            menu_bg_image = Image.open("menu_background.jpg")
            menu_bg_image = menu_bg_image.resize((400, 750))  # Новый размер фона
            self.menu_bg_photo = ImageTk.PhotoImage(menu_bg_image)
        except FileNotFoundError:
            self.menu_bg_photo = ImageTk.PhotoImage(Image.new('RGB', (400, 750), color='black'))

        # Создание холста для фона
        self.menu_canvas = tk.Canvas(root, width=400, height=750)
        self.menu_canvas.create_image(0, 0, anchor=tk.NW, image=self.menu_bg_photo)
        self.menu_canvas.pack()

        # Загрузка изображений для кнопок
        try:
            play_image = Image.open("play_button.png")
            play_image = play_image.resize((300, 75))  # Увеличиваем размер кнопки
            self.play_photo = ImageTk.PhotoImage(play_image)
        except FileNotFoundError:
            self.play_photo = ImageTk.PhotoImage(Image.new('RGB', (300, 75), color='green'))

        try:
            options_image = Image.open("options_button.png")
            options_image = options_image.resize((300, 75))  # Увеличиваем размер кнопки
            self.options_photo = ImageTk.PhotoImage(options_image)
        except FileNotFoundError:
            self.options_photo = ImageTk.PhotoImage(Image.new('RGB', (300, 75), color='blue'))

        # Кнопка Play
        self.play_button = tk.Button(
            root,
            image=self.play_photo,
            command=self.start_tetris,
            borderwidth=0,
            bg="black",  # Цвет фона кнопки
            activebackground="black"  # Цвет фона при нажатии
        )
        self.play_button.place(x=51, y=540)  # Позиция кнопки Play

        # Кнопка Options
        self.options_button = tk.Button(
            root,
            image=self.options_photo,
            command=self.show_options,
            borderwidth=0,
            bg="black",  # Цвет фона кнопки
            activebackground="black"  # Цвет фона при нажатии
        )
        self.options_button.place(x=51, y=640)  # Позиция кнопки Options

        # Переменные для управления звуком
        self.music_enabled = True
        self.sound_enabled = True

        # Загрузка изображений для кнопок музыки и звука
        try:
            # Загружаем оригинальные изображения кнопок
            self.music_on_image = ImageTk.PhotoImage(Image.open("music_button_on.jpg").resize((300, 75)))
            self.music_off_image = ImageTk.PhotoImage(Image.open("music_button_off.jpg").resize((300, 75)))
            self.volume_on_image = ImageTk.PhotoImage(Image.open("volume_button_on.jpg").resize((300, 75)))
            self.volume_off_image = ImageTk.PhotoImage(Image.open("volume_button_off.jpg").resize((300, 75)))
        except FileNotFoundError:
            print("Один или несколько файлов изображений для кнопок не найдены!")
            # Используем стандартные изображения, если файлы не найдены
            self.music_on_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), color='green'))
            self.music_off_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), color='red'))
            self.volume_on_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), color='blue'))
            self.volume_off_image = ImageTk.PhotoImage(Image.new('RGB', (300, 75), color='gray'))

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
        options_window = tk.Toplevel(self.root)
        options_window.title("Options")
        options_window.geometry("400x750")  # Размер окна настроек

        # Загрузка фонового изображения для окна настроек
        try:
            options_bg_image = Image.open("options_background.jpg")
            options_bg_image = options_bg_image.resize((400, 750))  # Новый размер фона
            self.options_bg_photo = ImageTk.PhotoImage(options_bg_image)
        except FileNotFoundError:
            self.options_bg_photo = ImageTk.PhotoImage(Image.new('RGB', (400, 750), color='gray'))

        # Создание холста для фона
        options_canvas = tk.Canvas(options_window, width=400, height=750)
        options_canvas.create_image(0, 0, anchor=tk.NW, image=self.options_bg_photo)
        options_canvas.pack()

        # Настройки кнопок
        button_width = 300
        button_height = 75
        x_position = (400 - button_width) // 2  # Центрируем по горизонтали
        min_spacing = 10  # Минимальное расстояние между кнопками
        
        # Рассчитываем отступы для позиционирования блока кнопок
        total_buttons_height = 2 * button_height + min_spacing
        start_y = (750 - total_buttons_height) // 2 + 50  # Сдвигаем кнопки на 50 пикселей ниже центра
        
        # Позиция первой кнопки (музыка)
        music_button_y = start_y
        
        # Кнопка включения/выключения музыки (верхняя кнопка)
        self.music_button = tk.Button(
            options_window,
            image=self.music_on_image if self.music_enabled else self.music_off_image,
            command=lambda: self.toggle_music(options_window),
            borderwidth=0,
            width=button_width,
            height=button_height
        )
        self.music_button.place(x=x_position, y=music_button_y, 
                              width=button_width, height=button_height)

        # Кнопка включения/выключения звуков игры (нижняя кнопка)
        self.sound_button = tk.Button(
            options_window,
            image=self.volume_on_image if self.sound_enabled else self.volume_off_image,
            command=lambda: self.toggle_sound(options_window),
            borderwidth=0,
            width=button_width,
            height=button_height
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