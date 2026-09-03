from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.button import Button
from kivy.clock import Clock
import random

class GameMasterRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=10, **kwargs)
        
        # 1. CORE STATE DATABASE
        self.gold = 1000
        self.prestige_points = 0
        self.prestige_rank = 1
        self.boss_tokens = 0
        self.zone_level = 1
        self.max_historical_zone = 1
        self.current_stage = 1
        self.stages_per_zone = 10
        self.combat_elapsed = 0.0
        
        # Catalogs & Active Party Setup
        self.hero_catalog = [
            {"id":1, "name":"Gothic Vanguard", "hp":500, "max_hp":500, "dmg":45, "def":20, "acc":90, "dodge":5, "crit_chance":5, "gauge":0.0, "ability":"AOE Cleave"},
            {"id":2, "name":"Blood Cultist", "hp":380, "max_hp":380, "dmg":60, "def":10, "acc":85, "dodge":10, "crit_chance":8, "gauge":0.0, "ability":"Vampiric Siphon"},
            {"id":3, "name":"Grave Knight", "hp":650, "max_hp":650, "dmg":30, "def":35, "acc":80, "dodge":0, "crit_chance":3, "gauge":0.0, "ability":"Bone Armor"}
        ]
        self.active_party = [dict(self.hero_catalog[0])]
        self.active_enemies = []
        self.active_hero_index = 0
        
        # 2. Programmatic Mobile UI Layout Generation
        self.header_label = Label(text="", size_hint_y=None, height=40, font_size='20sp')
        self.gold_label = Label(text="", size_hint_y=None, height=30, font_size='16sp')
        self.hero_stats_label = Label(text="", size_hint_y=None, height=40, font_size='14sp')
        
        self.hero_hp_bar = ProgressBar(max=500, value=500, size_hint_y=None, height=20)
        self.hero_gauge_bar = ProgressBar(max=6, value=0, size_hint_y=None, height=10)
        
        self.add_widget(self.header_label)
        self.add_widget(self.gold_label)
        self.add_widget(self.hero_stats_label)
        self.add_widget(self.hero_hp_bar)
        self.add_widget(self.hero_gauge_bar)
        
        # Enemy View Panels
        self.enemy_labels = [Label(size_hint_y=None, height=30) for _ in range(3)]
        self.enemy_bars = [ProgressBar(max=100, value=100, size_hint_y=None, height=15) for _ in range(3)]
        for i in range(3):
            self.add_widget(self.enemy_labels[i])
            self.add_widget(self.enemy_bars[i])
            
        # Command Buttons
        self.prestige_btn = Button(text="PRESTIGE RESET\n(Rank Up)", size_hint_y=None, height=60)
        self.prestige_btn.bind(on_press=self._on_prestige_reset_pressed)
        self.add_widget(self.prestige_btn)
        
        self._spawn_zone_encounter()
        Clock.schedule_interval(self._execute_combat_tick, 1.0)

    # 3. CORE LOGIC ENGINE INTERPOLATION
    def _spawn_zone_encounter(self):
        self.combat_elapsed = 0.0
        self.active_enemies.clear()
        
        peak_hp = (50 + self.max_historical_zone * 30) * (1.0 + (self.prestige_rank - 1) * 0.3)
        peak_dmg = (10 + self.max_historical_zone * 5) * (1.0 + (self.prestige_rank - 1) * 0.3)
        
        for i in range(3):
            enemy_hp = int(peak_hp * 0.45)
            self.active_enemies.append({
                "name": f"Construct Mk.{random.randint(1, 99)}",
                "hp": enemy_hp, "max_hp": enemy_hp,
                "dmg": int(peak_dmg * 0.40), "def": int(self.zone_level * 2),
                "acc": 85, "dodge": 5, "crit_chance": 5
            })
        for h in self.active_party:
            h["hp"] = h["max_hp"]
        self._update_ui()

    def _execute_combat_tick(self, dt):
        if not self.active_party or not self.active_enemies:
            return
            
        hero = self.active_party[self.active_hero_index]
        if hero["hp"] <= 0:
            self._handle_party_wipe()
            return
            
        target = self._get_first_alive_enemy()
        if target:
            # Hero Phase Execution
            if hero["gauge"] >= 6.0:
                hero["gauge"] = 0.0
                if hero["id"] == 1: # AOE Cleave Simulation
                    for e in self.active_enemies:
                        if e["hp"] > 0:
                            e["hp"] = max(0, e["hp"] - int(hero["dmg"] * 1.5 - e["def"]))
            else:
                hit_chance = clamp(hero["acc"] - target["dodge"], 5, 95)
                if random.randint(1, 100) <= hit_chance:
                    raw_dmg = max(1, int(hero["dmg"] - target["def"]))
                    target["hp"] = max(0, target["hp"] - raw_dmg)
                    hero["gauge"] = min(6.0, hero["gauge"] + 1.0)
                    
        # Enemy Phase Execution
        for e in self.active_enemies:
            if e["hp"] > 0 and hero["hp"] > 0:
                if random.randint(1, 100) <= e["acc"]:
                    hero["hp"] = max(0, hero["hp"] - max(1, int(e["dmg"] - hero["def"])))
                    
        self._check_battle_outcomes()
        self._update_ui()

    def _check_battle_outcomes(self):
        all_dead = all(e["hp"] <= 0 for e in self.active_enemies)
        if all_dead:
            self.current_stage += 1
            self.gold += int(self.zone_level * 5 * (1.0 + (self.prestige_rank - 1) * 0.3))
            
            if self.current_stage > self.stages_per_zone:
                self.zone_level += 1
                self.current_stage = 1
                if self.zone_level > self.max_historical_zone:
                    self.max_historical_zone = self.zone_level
                    if self.max_historical_zone % 5 == 0:
                        self.boss_tokens += 1
            self._spawn_zone_encounter()

    def _handle_party_wipe(self):
        self.zone_level = max(1, self.zone_level - 5)
        self.current_stage = 1
        self._spawn_zone_encounter()

    def _on_prestige_reset_pressed(self, instance):
        self.prestige_points += self.zone_level
        self.zone_level = 1
        self.current_stage = 1
        self.prestige_rank += 1
        self._spawn_zone_encounter()

    def _get_first_alive_enemy(self):
        for e in self.active_enemies:
            if e["hp"] > 0: return e
        return None

    def _update_ui(self):
        self.header_label.text = f"ZONE {self.zone_level} | STAGE {self.current_stage}/10"
        self.gold_label.text = f"GOLD: {self.gold}  |  PRESTIGE: {self.prestige_points}  |  BOSS TOKENS: {self.boss_tokens}"
        
        if self.active_party:
            hero = self.active_party[0]
            self.hero_stats_label.text = f"{hero['name'].upper()} - DMG: {hero['dmg']} | DEF: {hero['def']}"
            self.hero_hp_bar.max = hero["max_hp"]
            self.hero_hp_bar.value = hero["hp"]
            self.hero_gauge_bar.value = hero["gauge"]
            
        for i, e in enumerate(self.active_enemies):
            if e["hp"] > 0:
                self.enemy_labels[i].text = f"{e['name']} ({e['hp']}/{e['max_hp']})"
                self.enemy_bars[i].max = e["max_hp"]
                self.enemy_bars[i].value = e["hp"]
            else:
                self.enemy_labels[i].text = f"{e['name']} [DESTROYED]"
                self.enemy_bars[i].value = 0

def clamp(n, minn, maxn):
    return max(min(n, maxn), minn)

class GrimAutoApp(App):
    def build(self):
        return GameMasterRoot()

if __name__ == '__main__':
    GrimAutoApp().run()

