import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Файл для хранения избранных
        self.favorites_file = "favorites.json"
        self.favorites = self.load_favorites()
        
        # Переменные
        self.search_var = tk.StringVar()
        self.current_users = []
        
        self.create_widgets()
        self.load_favorites_display()
    
    def create_widgets(self):
        # Верхняя панель поиска
        search_frame = ttk.LabelFrame(self.root, text="Поиск пользователей GitHub", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text="Имя пользователя:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40, font=("Arial", 10))
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)
        self.search_entry.bind("<Return>", lambda event: self.search_users())
        
        self.search_button = ttk.Button(search_frame, text=" Поиск", command=self.search_users)
        self.search_button.grid(row=0, column=2, padx=5)
        
        # Основная область с двумя панелями
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая панель - результаты поиска
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="Результаты поиска:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        
        # Таблица результатов поиска
        self.results_tree = ttk.Treeview(left_frame, columns=("username", "repos", "followers"), show="headings", height=15)
        self.results_tree.heading("username", text="Username")
        self.results_tree.heading("repos", text="Public Repos")
        self.results_tree.heading("followers", text="Followers")
        self.results_tree.column("username", width=150)
        self.results_tree.column("repos", width=100)
        self.results_tree.column("followers", width=100)
        
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Контекстное меню для результатов
        self.results_menu = tk.Menu(self.root, tearoff=0)
        self.results_menu.add_command(label="Добавить в избранное", command=self.add_to_favorites_from_results)
        self.results_menu.add_command(label="Показать детали", command=self.show_user_details)
        self.results_tree.bind("<Button-3>", self.show_results_context_menu)
        
        # Правая панель - избранное
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        ttk.Label(right_frame, text=" Избранные пользователи:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        
        # Таблица избранных
        self.favorites_tree = ttk.Treeview(right_frame, columns=("username", "added"), show="headings", height=15)
        self.favorites_tree.heading("username", text="Username")
        self.favorites_tree.heading("added", text="Дата добавления")
        self.favorites_tree.column("username", width=150)
        self.favorites_tree.column("added", width=150)
        
        fav_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.favorites_tree.yview)
        self.favorites_tree.configure(yscrollcommand=fav_scrollbar.set)
        
        self.favorites_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fav_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Контекстное меню для избранных
        self.favorites_menu = tk.Menu(self.root, tearoff=0)
        self.favorites_menu.add_command(label="Удалить из избранного", command=self.remove_from_favorites)
        self.favorites_menu.add_command(label="Показать детали", command=self.show_favorite_details)
        self.favorites_tree.bind("<Button-3>", self.show_favorites_context_menu)
        
        # Кнопки управления избранным
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text=" Удалить выбранного", command=self.remove_from_favorites).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text=" Экспорт в JSON", command=self.export_favorites).pack(side=tk.LEFT, padx=2)
        
        # Статус бар
        self.status_bar = ttk.Label(self.root, text="Готов к работе", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def search_users(self):
        """Поиск пользователей на GitHub"""
        username = self.search_var.get().strip()
        
        # Проверка корректности ввода
        if not username:
            messagebox.showwarning("Предупреждение", "Поле поиска не может быть пустым!")
            self.status_bar.config(text="Ошибка: Поле поиска пустое")
            return
        
        self.status_bar.config(text=f"Поиск пользователя '{username}'...")
        self.search_button.config(state=tk.DISABLED)
        
        try:
            # API запрос к GitHub
            url = f"https://api.github.com/search/users?q={username}&per_page=20"
            response = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"})
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("items", [])
                
                if not users:
                    messagebox.showinfo("Результат", f"Пользователь '{username}' не найден")
                    self.status_bar.config(text=f"Пользователь '{username}' не найден")
                    return
                
                # Очищаем текущие результаты
                for item in self.results_tree.get_children():
                    self.results_tree.delete(item)
                
                self.current_users = []
                
                # Получаем дополнительные данные для каждого пользователя
                for user in users[:20]:
                    user_detail = self.get_user_details(user["login"])
                    if user_detail:
                        self.current_users.append(user_detail)
                        self.results_tree.insert("", tk.END, values=(
                            user_detail["login"],
                            user_detail.get("public_repos", 0),
                            user_detail.get("followers", 0)
                        ), tags=(user_detail["login"],))
                
                self.status_bar.config(text=f"Найдено {len(self.current_users)} пользователей")
            else:
                messagebox.showerror("Ошибка", f"Ошибка API: {response.status_code}")
                self.status_bar.config(text=f"Ошибка API: {response.status_code}")
                
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", f"Ошибка сети: {str(e)}")
            self.status_bar.config(text=f"Ошибка сети: {str(e)}")
        finally:
            self.search_button.config(state=tk.NORMAL)
    
    def get_user_details(self, username):
        """Получение детальной информации о пользователе"""
        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"})
            
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def add_to_favorites_from_results(self):
        """Добавление выбранного пользователя в избранное"""
        selected = self.results_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите пользователя для добавления в избранное")
            return
        
        item = self.results_tree.item(selected[0])
        username = item["values"][0]
        
        # Находим пользователя в результатах поиска
        user_data = next((u for u in self.current_users if u["login"] == username), None)
        
        if user_data:
            if username in self.favorites:
                messagebox.showinfo("Информация", f"Пользователь '{username}' уже в избранном")
                return
            
            self.favorites[username] = {
                "login": user_data["login"],
                "avatar_url": user_data.get("avatar_url", ""),
                "html_url": user_data.get("html_url", ""),
                "public_repos": user_data.get("public_repos", 0),
                "followers": user_data.get("followers", 0),
                "following": user_data.get("following", 0),
                "created_at": user_data.get("created_at", ""),
                "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.save_favorites()
            self.load_favorites_display()
            self.status_bar.config(text=f"Пользователь '{username}' добавлен в избранное")
    
    def remove_from_favorites(self):
        """Удаление пользователя из избранного"""
        selected = self.favorites_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите пользователя для удаления")
            return
        
        item = self.favorites_tree.item(selected[0])
        username = item["values"][0]
        
        if messagebox.askyesno("Подтверждение", f"Удалить '{username}' из избранного?"):
            del self.favorites[username]
            self.save_favorites()
            self.load_favorites_display()
            self.status_bar.config(text=f"Пользователь '{username}' удален из избранного")
    
    def load_favorites(self):
        """Загрузка избранных из JSON файла"""
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_favorites(self):
        """Сохранение избранных в JSON файл"""
        with open(self.favorites_file, "w", encoding="utf-8") as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=2)
    
    def load_favorites_display(self):
        """Отображение избранных в таблице"""
        for item in self.favorites_tree.get_children():
            self.favorites_tree.delete(item)
        
        for username, data in self.favorites.items():
            self.favorites_tree.insert("", tk.END, values=(
                username,
                data.get("added_date", "Неизвестно")
            ), tags=(username,))
    
    def show_user_details(self):
        """Показ детальной информации о пользователе"""
        selected = self.results_tree.selection()
        if not selected:
            return
        
        item = self.results_tree.item(selected[0])
        username = item["values"][0]
        user_data = next((u for u in self.current_users if u["login"] == username), None)
        
        if user_data:
            self.show_details_dialog(user_data)
    
    def show_favorite_details(self):
        """Показ деталей избранного пользователя"""
        selected = self.favorites_tree.selection()
        if not selected:
            return
        
        item = self.favorites_tree.item(selected[0])
        username = item["values"][0]
        user_data = self.favorites.get(username)
        
        if user_data:
            self.show_details_dialog(user_data)
    
    def show_details_dialog(self, user_data):
        """Диалоговое окно с деталями пользователя"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Детали: {user_data['login']}")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        
        # Создаем фрейм с прокруткой для информации
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        info_text = f"""
ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ
{'=' * 40}

 Username: {user_data.get('login', 'N/A')}

 Публичные репозитории: {user_data.get('public_repos', 0)}
 Подписчики: {user_data.get('followers', 0)}
 Подписки: {user_data.get('following', 0)}

 GitHub: {user_data.get('html_url', 'N/A')}

 Дата регистрации: {user_data.get('created_at', 'N/A')[:10] if user_data.get('created_at') else 'N/A'}

 В избранном с: {user_data.get('added_date', 'N/A')}
        """
        
        text_widget = tk.Text(frame, wrap=tk.WORD, font=("Courier", 10), height=15)
        text_widget.insert("1.0", info_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Кнопка закрытия
        ttk.Button(frame, text="Закрыть", command=dialog.destroy).pack(pady=10)
        
        # Делаем окно модальным
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.focus()
    
    def export_favorites(self):
        """Экспорт избранных в JSON файл"""
        if not self.favorites:
            messagebox.showinfo("Информация", "Нет избранных пользователей для экспорта")
            return
        
        filename = f"github_favorites_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Успех", f"Избранные экспортированы в файл:\n{filename}")
            self.status_bar.config(text=f"Экспорт завершен: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {str(e)}")
    
    def show_results_context_menu(self, event):
        """Показ контекстного меню для результатов поиска"""
        item = self.results_tree.identify_row(event.y)
        if item:
            self.results_tree.selection_set(item)
            self.results_menu.post(event.x_root, event.y_root)
    
    def show_favorites_context_menu(self, event):
        """Показ контекстного меню для избранных"""
        item = self.favorites_tree.identify_row(event.y)
        if item:
            self.favorites_tree.selection_set(item)
            self.favorites_menu.post(event.x_root, event.y_root)

def main():
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()

if __name__ == "__main__":
    main()
