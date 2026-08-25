# 🥋 Ikemen Combo Finder

An automated tool designed to discover possible combo chains for **Ikemen GO** and **MUGEN** characters. It parses raw character source files (`.def`, `.cmd`, `.cns`/`.st`), builds a transition graph of possible moves, optimizes sequences using a **Genetic Algorithm**, and verifies them through a rule-based **Combo Simulator**.

---





## ⚠️ Read This First — An Honest Disclaimer
This is not a good project — and I'd rather be upfront about that.

If you stumbled onto this repository expecting a polished, well-engineered tool that gets regular updates, let me save you the disappointment now: this isn't it. This project is imperfect, messy, and flawed in more ways than I can count. There might be bugs, questionable decisions, and a long list of things that should be improved but haven't been.

Some honest context about why:

I can't code. I'm not a programmer, and I don't write the code in this repository myself. This entire project is built by relying heavily on AI — I describe what I want, it generates the code, and I test until something works (even this readme file is AI generated).
Because of that, everything takes longer. What a real developer could do in an hour might take me days or weeks of trial and error. Some things stay broken for a long time simply because I don't always know how to fix them.
Don't expect frequent updates. There is no roadmap, no release schedule, and no promises. Long silences between commits are normal here, not a sign that something big is coming.
So, with all that in mind:

- Just passing by? Feel free to try it — but keep your expectations low. It may not work correctly with your character, and it may never be fixed.

- An actual developer? You'll probably find this codebase painful to read, and you'd be right. Fork it, rewrite it, or use it as a cautionary tale — it's all good.
I'm still putting this out there publicly because it might be useful or interesting to someone despite everything. Just don't hold your breath for updates.

---

## 🚀 Project Architecture & Workflow

1. **The Parsing Phase (`src/parser/`)**
   - **`def_parser.py`**: Locates character definition files and maps asset paths.
   - **`cmd_parser.py`**: Extracts commands, buttons, and command time windows.
   - **`cns_parser.py`**: Scans state files (`.cns` / `.st`) to map states (`[Statedef]`), base damage, and hitstun parameters.

2. **The Relational Cancel Graph Phase (`src/model/cancel_graph.py`)**
   - Builds a directed graph (`NetworkX`) where nodes represent moves and directed edges represent allowed transitions based on standard fighting game heuristics (Normals ➔ Specials ➔ Supers, Light ➔ Medium ➔ Heavy).

3. **The Search & Validation Phase (`src/search/` & `src/validation/`)**
   - **Genetic Algorithm (`genetic.py` & `fitness.py`)**: Evolves populations of move sequences over multiple generations to maximize length, damage, and graph compliance.
   - **Simulator (`simulator.py`)**: Evaluates step-by-step connectivity, drops invalid links, and applies realistic damage scaling per hit index.
4. **Output Files**
   - **Check these both folders  (`results/combos/` & `results/combos/`) for extracted moves and discovered combos in json format.**
---




## 📂 Project Structure

```text
ikemen-combo-finder/
├── README.md
├── requirements.txt
├── config.yaml                 # Character paths, search settings, outputs
├── data/
│   └── chars/                  # Character folders directory
├── src/
│   ├── parser/                 # Parses .def, .cmd, and .cns files
│   ├── model/                  # Data structures (Move, Character, CancelGraph)
│   ├── search/                 # Genetic algorithm and fitness evaluator
│   ├── validation/             # Rule-checking combo simulator & validator
│   └── utils/                  # Helper functions
├── scripts/                    # Entry-point scripts (Extraction & Search)
└── results/
    ├── moves/                  # Extracted character profiles (.json)
    └── combos/                 # Discovered optimal combos (.json)
```

---

## 🛠️ Requirements & Installation

### Prerequisite
* **Python 3.14.7** or higher.

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/username/ikemen-combo-finder.git
   cd ikemen-combo-finder
   ```

2. **Set Up Virtual Environment (Recommended)** 
The use of a *virtual environment* is highly recommended to keep project dependencies isolated. If you don't want to use a *virtual environment*, you can **skip this step**.

   * **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate
     ```
   * **Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## 📖 How to Use

1. **Add a Character:** Place your character folder inside `data/chars/`.
2. **Configure:** Update `config.yaml` with your character's folder name:
   ```yaml
   character_path: "data/chars/your_character_name"
   ```
3. **Extract Moves:** Run the extraction script:
   ```bash
   python scripts/extract_moves.py
   ```
4. **Find & Simulate Combos:** Run the search algorithm and validator:
   ```bash
   python scripts/find_combos.py
   ```




## ⚠️ Limitations

> ### Rule-Based Assumptions
>
> The **Relational Cancel Graph** currently relies on predefined fighting-game conventions and heuristics to determine whether one move can transition into another.
>
> For example, the system generally assumes relationships such as:
>
> ```text
> Light Normal → Medium Normal → Heavy Normal
> Normal → Special → Super
> ```
>
> These rules are useful as a general approximation, but they **do not represent a universal MUGEN or Ikemen GO standard**.
>
> MUGEN characters are highly customizable. Character developers can implement their own combo systems, cancel rules, state transitions, command requirements, hitstun behavior, and special mechanics. A character may intentionally allow transitions that would normally be considered invalid by traditional fighting-game conventions, or prohibit transitions that would normally be considered standard.
>
> ---
>
> ### Damage and Hitstun Are Approximations
>
> Damage scaling, hitstun, and combo continuation are modeled using extracted values and simplified rules.
>
> Actual in-game behavior can be affected by character-specific implementations, engine behavior, state controllers, hit definitions, scaling systems, and custom mechanics.
>
> Therefore, the simulated damage and combo duration should be treated as **estimates rather than authoritative in-game results**.





## 📜 License

This project is licensed under the **MIT License**. 

See the [LICENSE](LICENSE) file for the full license text. Feel free to use, modify, fork, and share this project with the MUGEN and Ikemen GO communities!
