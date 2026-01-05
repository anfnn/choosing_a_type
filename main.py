"""
Лабораторная работа №4: Реализация моделей принятия коллективных решений
Предметная область: Выбор совместного места отдыха (вариант №3 из ТЗ)
Варианты: "Крым", "Сочи", "Алтай"
"""

import tkinter as tk
from tkinter import ttk, messagebox


# ======================
# МОДЕЛИ ПРИНЯТИЯ РЕШЕНИЙ
# ======================

VARIANTS = ["Крым", "Сочи", "Алтай"]  # Популярные места отдыха в РФ


def plurality_vote(ranks):
    """Модель относительного большинства: считает первые места"""
    first_choices = [rank[0] for rank in ranks]
    counts = {v: first_choices.count(v) for v in VARIANTS}
    winner = max(counts, key=counts.get)
    explanation = f"Победило место «{winner}», так как получило наибольшее число первых мест: {counts[winner]} из {len(ranks)}."
    return winner, explanation, counts


def pairwise_matrix(ranks):
    """Создаёт матрицу попарных побед: matrix[a][b] = сколько раз a > b"""
    n = len(VARIANTS)
    idx = {v: i for i, v in enumerate(VARIANTS)}
    matrix = [[0] * n for _ in range(n)]

    for rank in ranks:
        for i in range(n):
            for j in range(i + 1, n):
                a = rank[i]
                b = rank[j]
                matrix[idx[a]][idx[b]] += 1
    return matrix


def condorcet_winner(ranks):
    """Явный победитель по Кондорсе: выигрывает у всех в попарных сравнениях"""
    matrix = pairwise_matrix(ranks)
    n = len(VARIANTS)
    idx = {v: i for i, v in enumerate(VARIANTS)}

    for v in VARIANTS:
        i = idx[v]
        wins_all = True
        for j in range(n):
            if i == j:
                continue
            if matrix[i][j] <= matrix[j][i]:  # не выигрывает у j
                wins_all = False
                break
        if wins_all:
            explanation = f"«{v}» — явный победитель по Кондорсе: предпочтительнее любого другого места в прямом сравнении."
            return v, explanation
    return None, "Явного победителя по Кондорсе нет: цикл предпочтений или паритет."


def copeland_score(ranks):
    """Правило Копленда: +1 за победу, -1 за поражение в паре"""
    matrix = pairwise_matrix(ranks)
    n = len(VARIANTS)
    scores = {}
    idx = {v: i for i, v in enumerate(VARIANTS)}

    for v in VARIANTS:
        i = idx[v]
        score = 0
        for j in range(n):
            if i == j:
                continue
            if matrix[i][j] > matrix[j][i]:
                score += 1
            elif matrix[i][j] < matrix[j][i]:
                score -= 1
        scores[v] = score

    winner = max(scores, key=scores.get)
    explanation = f"По правилу Копленда победило место «{winner}» с баллом {scores[winner]} (разница побед и поражений в парных сравнениях)."
    return winner, explanation, scores


def simpson_score(ranks):
    """Правило Симпсона: максимизирует минимальное число побед в парах"""
    matrix = pairwise_matrix(ranks)
    n = len(VARIANTS)
    min_wins = {}
    idx = {v: i for i, v in enumerate(VARIANTS)}

    for v in VARIANTS:
        i = idx[v]
        worst = min(matrix[i][j] for j in range(n) if j != i)
        min_wins[v] = worst

    winner = max(min_wins, key=min_wins.get)
    explanation = (
        f"По правилу Симпсона победило место «{winner}», так как его наихудший результат в парных сравнениях — "
        f"{min_wins[winner]} голосов, что выше, чем у других."
    )
    return winner, explanation, min_wins


def borda_count(ranks):
    """Модель Борда: 2 балла за 1-е место, 1 за 2-е, 0 за 3-е (для 3 вариантов)"""
    points = {0: 2, 1: 1, 2: 0}
    scores = {v: 0 for v in VARIANTS}

    for rank in ranks:
        for pos, variant in enumerate(rank):
            scores[variant] += points[pos]

    winner = max(scores, key=scores.get)
    explanation = f"По модели Борда победило место «{winner}» с суммой баллов {scores[winner]}."
    return winner, explanation, scores


# ======================
# ГРАФИЧЕСКИЙ ИНТЕРФЕЙС
# ======================

class TravelVotingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Выбор совместного места отдыха — Коллективное решение")
        self.root.geometry("800x900")

        self.voters = []  # список имён участников
        self.ranks = []   # список ранжировок: [[v1, v2, v3], ...]

        self.setup_ui()

    def setup_ui(self):
        # === Верхняя панель: добавление участников ===
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill="x")

        ttk.Label(top_frame, text="Имя участника:").grid(row=0, column=0, sticky="w")
        self.name_entry = ttk.Entry(top_frame, width=20)
        self.name_entry.grid(row=0, column=1, padx=5)

        ttk.Button(top_frame, text="Добавить участника", command=self.add_voter).grid(row=0, column=2, padx=5)

        # === Область голосования ===
        self.voting_frame = ttk.Frame(self.root, padding="10")
        self.voting_frame.pack(fill="both", expand=True)

        self.voter_widgets = []  # для отслеживания виджетов

        # === Кнопка расчёта ===
        ttk.Button(self.root, text="Рассчитать результаты", command=self.calculate).pack(pady=10)

        # === Область вывода результатов ===
        self.result_frame = ttk.Frame(self.root, padding="10")
        self.result_frame.pack(fill="both", expand=True)

        self.result_text = tk.Text(self.result_frame, height=15, wrap="word")
        scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        self.result_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def add_voter(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Введите имя участника.")
            return
        if name in self.voters:
            messagebox.showwarning("Ошибка", "Участник с таким именем уже добавлен.")
            return

        self.voters.append(name)
        self.name_entry.delete(0, tk.END)

        # Создаём строку для ранжирования
        row_frame = ttk.Frame(self.voting_frame)
        row_frame.pack(fill="x", pady=3)

        ttk.Label(row_frame, text=f"{name}:").pack(side="left")

        # Три выпадающих списка с уникальными значениями
        combo1 = ttk.Combobox(row_frame, values=VARIANTS, state="readonly", width=12)
        combo2 = ttk.Combobox(row_frame, values=VARIANTS, state="readonly", width=12)
        combo3 = ttk.Combobox(row_frame, values=VARIANTS, state="readonly", width=12)

        combo1.pack(side="left", padx=2)
        combo2.pack(side="left", padx=2)
        combo3.pack(side="left", padx=2)

        # Ограничиваем выбор: нельзя дублировать
        def update_choices(*args):
            selected = set()
            c1, c2, c3 = combo1.get(), combo2.get(), combo3.get()
            if c1: selected.add(c1)
            if c2: selected.add(c2)
            if c3: selected.add(c3)

            avail = [v for v in VARIANTS if v not in selected]
            if not c1: combo1.configure(values=[c1] if c1 else VARIANTS)
            if not c2: combo2.configure(values=avail + ([c2] if c2 else []))
            if not c3: combo3.configure(values=avail + ([c3] if c3 else []))

        combo1.bind("<<ComboboxSelected>>", update_choices)
        combo2.bind("<<ComboboxSelected>>", update_choices)
        combo3.bind("<<ComboboxSelected>>", update_choices)

        self.voter_widgets.append((name, combo1, combo2, combo3))

    def calculate(self):
        self.ranks = []
        for name, c1, c2, c3 in self.voter_widgets:
            v1, v2, v3 = c1.get(), c2.get(), c3.get()
            if not all([v1, v2, v3]) or len({v1, v2, v3}) != 3:
                messagebox.showerror("Ошибка", f"Участник {name}: заполните все три позиции без повторов.")
                return
            self.ranks.append([v1, v2, v3])

        if not self.ranks:
            messagebox.showwarning("Ошибка", "Нет данных для голосования.")
            return

        # Очищаем вывод
        self.result_text.delete(1.0, tk.END)

        # 1. Относительное большинство
        w1, e1, c1 = plurality_vote(self.ranks)
        self.result_text.insert(tk.END, "1. Относительное большинство:\n")
        self.result_text.insert(tk.END, f"   {e1}\n")
        self.result_text.insert(tk.END, f"   Подсчёт: {c1}\n\n")

        # 2. Кондорсе — явный победитель
        w2, e2 = condorcet_winner(self.ranks)
        self.result_text.insert(tk.END, "2. Явный победитель по Кондорсе:\n")
        self.result_text.insert(tk.END, f"   {e2}\n\n")

        # 3. Правило Копленда
        w3, e3, s3 = copeland_score(self.ranks)
        self.result_text.insert(tk.END, "3. Правило Копленда:\n")
        self.result_text.insert(tk.END, f"   {e3}\n")
        self.result_text.insert(tk.END, f"   Баллы: {s3}\n\n")

        # 4. Правило Симпсона
        w4, e4, s4 = simpson_score(self.ranks)
        self.result_text.insert(tk.END, "4. Правило Симпсона:\n")
        self.result_text.insert(tk.END, f"   {e4}\n")
        self.result_text.insert(tk.END, f"   Мин. победы: {s4}\n\n")

        # 5. Модель Борда
        w5, e5, s5 = borda_count(self.ranks)
        self.result_text.insert(tk.END, "5. Модель Борда:\n")
        self.result_text.insert(tk.END, f"   {e5}\n")
        self.result_text.insert(tk.END, f"   Баллы: {s5}\n\n")

        # Итог
        self.result_text.insert(tk.END, "— ИТОГ —\n")
        methods = [w1, w2 if w2 else "(нет)", w3, w4, w5]
        from collections import Counter
        freq = Counter([w for w in methods if w != "(нет)"])
        if freq:
            consensus = freq.most_common(1)[0][0]
            self.result_text.insert(tk.END, f"Рекомендуемое место отдыха для группы: «{consensus}»\n")


# ======================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ======================

if __name__ == "__main__":
    root = tk.Tk()
    app = TravelVotingApp(root)
    root.mainloop()