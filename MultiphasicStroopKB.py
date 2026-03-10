import tkinter as tk
import random
import time
from tkinter import messagebox

# --- CONFIGURATION ---
CONDITIONS_POOLS = {
    "Congruent": [],
    "Incongruent": [],
    "Violence": ["KILL", "ASSAULT", "STAB", "PUNCH"],
    "Alcohol": ["BEER", "BOOZE", "DRINK", "LIQUOR"],
    "Cannabis": ["WEED", "KUSH", "MARYJANE", "POT"],
    "Opioids": ["FENT", "HEROIN", "PILLS", "SMACK"],
    "Amphetamines": ["METH", "CRACK", "COKE", "SNOW"],
    "Fear": ["SCARED", "TERROR", "PANIC", "FEAR"],
    "Happy": ["SMILE", "JOY", "HAPPY", "HORRAY"],
    "Sad": ["FROWN", "SAD", "GLOOMY", "MISERY"],
    "Angry": ["MAD", "RAGE", "ANGER", "FURY"],
    "Neutral": ["TABLE", "CHAIR", "CLOUD", "BOOK"]
}

TIME_LIMIT = 1500

COLOR_MAP = {
    'r': ("RED", "red"),
    'b': ("BLUE", "blue"),
    'g': ("GREEN", "green"),
    'y': ("YELLOW", "yellow"),
}


class StroopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stroop Research Tool")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#000000")

        self.running = False
        self.waiting_for_input = False  # NEW: Prevents double-triggering
        self.trial_count = 0
        self.results = []
        self.timeout_id = None
        self.total_trials_limit = 0
        self.trial_sequence = []

        self.selected_conditions = {cond: tk.BooleanVar(value=True) for cond in CONDITIONS_POOLS.keys()}
        self.active_list = []

        self.main_frame = tk.Frame(root, bg="#000000")
        self.main_frame.pack(expand=True, fill="both")

        self.show_config_screen()

    def show_config_screen(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="SELECT CONDITIONS", font=("Helvetica", 24, "bold"), fg="white",
                 bg="black").pack(pady=30)

        grid_frame = tk.Frame(self.main_frame, bg="black")
        grid_frame.pack(pady=10)

        for i, (cond, var) in enumerate(self.selected_conditions.items()):
            cb = tk.Checkbutton(grid_frame, text=cond, variable=var, font=("Arial", 14),
                                fg="white", bg="black", selectcolor="#444444",
                                activebackground="black", activeforeground="cyan")
            cb.grid(row=i // 3, column=i % 3, sticky="w", padx=20, pady=5)

        tk.Button(self.main_frame, text="CONFIRM & CONTINUE", font=("Arial", 14, "bold"),
                  command=self.validate_and_start, bg="#0072B2", fg="white").pack(pady=40)

    def validate_and_start(self):
        self.active_list = [cond for cond, var in self.selected_conditions.items() if var.get()]
        if not self.active_list:
            messagebox.showwarning("Selection Required", "Please select at least one condition.")
            return

        calculated_limit = len(self.active_list) * 12
        self.total_trials_limit = min(80, calculated_limit)
        temp_sequence = self.active_list * 12
        random.shuffle(temp_sequence)
        self.trial_sequence = temp_sequence[:self.total_trials_limit]
        self.show_start_screen()

    def show_start_screen(self):
        self.clear_frame()
        instructions = (
            f"Conditions Selected: {len(self.active_list)}\n"
            f"Total Trials: {self.total_trials_limit}\n\n"
            "Identify the INK COLOR of the word.\n\n"
            "Keys: R=Red, B=Blue, G=Green, Y=Yellow\n"
            "Time Limit: 1.5 seconds\n\n"
            "Press SPACE to begin."
        )
        tk.Label(self.main_frame, text=instructions, font=("Helvetica", 18), fg="#f0f0f0", bg="black").pack(pady=20)
        self.root.bind("<space>", lambda e: self.start_task())

    def start_task(self):
        self.root.unbind("<space>")
        self.running = True
        self.results = []
        self.trial_count = 0

        for key in COLOR_MAP.keys():
            self.root.bind(key, self.handle_keypress)
        self.root.bind('q', lambda e: self.end_task())

        self.clear_frame()
        self.display_label = tk.Label(self.main_frame, text="", font=("Helvetica", 70, "bold"), bg="#000000")
        self.display_label.pack(expand=True)
        self.prepare_next_trial()

    def prepare_next_trial(self):
        if not self.running: return
        if self.trial_count >= self.total_trials_limit:
            self.end_task()
            return

        self.waiting_for_input = False  # Input disabled during fixation
        self.display_label.config(text="+", fg="white")
        self.root.after(600, self.next_trial)

    def next_trial(self):
        if not self.running: return

        self.current_cond = self.trial_sequence[self.trial_count]
        if self.current_cond == "Congruent":
            self.target_key = random.choice(list(COLOR_MAP.keys()))
            word = COLOR_MAP[self.target_key][0]
        elif self.current_cond == "Incongruent":
            self.target_key = random.choice(list(COLOR_MAP.keys()))
            other_word_options = [v[0] for k, v in COLOR_MAP.items() if k != self.target_key]
            word = random.choice(other_word_options)
        else:
            word = random.choice(CONDITIONS_POOLS[self.current_cond])
            self.target_key = random.choice(list(COLOR_MAP.keys()))

        self.display_label.config(text=word, fg=COLOR_MAP[self.target_key][1])
        self.waiting_for_input = True  # NEW: Now we accept input
        self.start_time = time.time()

        # Cancel any existing timeout before starting a new one
        if self.timeout_id:
            self.root.after_cancel(self.timeout_id)
        self.timeout_id = self.root.after(TIME_LIMIT, self.handle_timeout)

    def handle_keypress(self, event):
        # Ignore if we aren't in a trial or already answered
        if not self.running or not self.waiting_for_input:
            return

        if self.timeout_id:
            self.root.after_cancel(self.timeout_id)
            self.timeout_id = None

        self.waiting_for_input = False  # Lock input immediately
        rt = time.time() - self.start_time
        is_correct = (event.char.lower() == self.target_key)
        self.record_and_feedback(is_correct, rt)

    def handle_timeout(self):
        if not self.running or not self.waiting_for_input:
            return

        self.timeout_id = None
        self.waiting_for_input = False  # Lock input
        self.record_and_feedback(False, TIME_LIMIT / 1000.0, timed_out=True)

    def record_and_feedback(self, is_correct, rt, timed_out=False):
        self.results.append({
            "condition": self.current_cond,
            "correct": is_correct,
            "rt": rt
        })
        self.trial_count += 1

        if timed_out:
            self.display_label.config(text="TOO SLOW", fg="gray")
        elif is_correct:
            self.display_label.config(text="CORRECT", fg="white")
        else:
            self.display_label.config(text="INCORRECT", fg="white")

        self.root.after(500, self.prepare_next_trial)

    def end_task(self):
        self.running = False
        if self.timeout_id:
            self.root.after_cancel(self.timeout_id)
            self.timeout_id = None
        for key in COLOR_MAP.keys():
            self.root.unbind(key)
        self.show_results_screen()

    def show_results_screen(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Results Summary", font=("Helvetica", 24, "bold"), fg="white", bg="black").pack(
            pady=20)
        container = tk.Frame(self.main_frame, bg="#222222", padx=20, pady=20)
        container.pack(pady=10)

        header = f"{'Condition':<15} | {'Acc %':<8} | {'Avg RT (s)':<10}"
        tk.Label(container, text=header, font=("Courier", 12, "bold"), fg="white", bg="#222222").pack(anchor="w")

        conditions_tested = sorted(list(set(r['condition'] for r in self.results)))
        for cond in conditions_tested:
            cond_data = [r for r in self.results if r['condition'] == cond]
            acc = (sum(1 for r in cond_data if r['correct']) / len(cond_data)) * 100
            correct_rts = [r['rt'] for r in cond_data if r['correct']]
            avg_rt = sum(correct_rts) / len(correct_rts) if correct_rts else 0

            row = f"{cond:<15} | {acc:>7.1f}% | {avg_rt:>9.3f}s"
            tk.Label(container, text=row, font=("Courier", 12), fg="white", bg="#222222").pack(anchor="w")

        tk.Button(self.main_frame, text="NEW CONFIGURATION", command=self.show_config_screen).pack(pady=20)
        tk.Button(self.main_frame, text="EXIT", command=self.root.destroy).pack()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = StroopApp(root)
    root.mainloop()