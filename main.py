import flet as ft
import random

def main(page: ft.Page):
    page.title = "GrimAuto Mobile"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    # 1. CORE STATE DATABASE
    state = {
        "gold": 1000, "prestige_points": 0, "prestige_rank": 1, "boss_tokens": 0,
        "zone_level": 1, "max_historical_zone": 1, "current_stage": 1, "stages_per_zone": 10
    }
    
    hero_catalog = [
        {"id": 1, "name": "Gothic Vanguard", "hp": 500, "max_hp": 500, "dmg": 45, "def": 20, "acc": 90, "dodge": 5, "gauge": 0.0},
        {"id": 2, "name": "Blood Cultist", "hp": 380, "max_hp": 380, "dmg": 60, "def": 10, "acc": 85, "dodge": 10, "gauge": 0.0},
    ]
    active_party = [dict(hero_catalog[0])]
    active_enemies = []
    
    # Interface UI Components Natively Generated
    header_label = ft.Text(value="", size=22, weight=ft.FontWeight.BOLD, color="white")
    gold_label = ft.Text(value="", size=16, color="amber")
    hero_stats_label = ft.Text(value="", size=14, color="green")
    
    hero_hp_bar = ft.ProgressBar(width=400, color="green", bgcolor="grey")
    hero_gauge_bar = ft.ProgressBar(width=400, color="blue", bgcolor="grey")
    
    enemy_list_view = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    def _spawn_zone_encounter():
        active_enemies.clear()
        peak_hp = (50 + state["max_historical_zone"] * 30) * (1.0 + (state["prestige_rank"] - 1) * 0.3)
        peak_dmg = (10 + state["max_historical_zone"] * 5) * (1.0 + (state["prestige_rank"] - 1) * 0.3)
        
        for i in range(3):
            e_hp = int(peak_hp * 0.45)
            active_enemies.append({
                "name": f"Construct Mk.{random.randint(1, 99)}", "hp": e_hp, "max_hp": e_hp,
                "dmg": int(peak_dmg * 0.40), "def": int(state["zone_level"] * 2), "acc": 85, "dodge": 5
            })
        for h in active_party:
            h["hp"] = h["max_hp"]
        _update_ui()

    def _execute_combat_tick():
        if not active_party or not active_enemies: return
        hero = active_party[0]
        if hero["hp"] <= 0:
            state["zone_level"] = max(1, state["zone_level"] - 5)
            state["current_stage"] = 1
            _spawn_zone_encounter()
            return
            
        # Quick Turn Calculations Simulation Loop
        for e in active_enemies:
            if e["hp"] > 0:
                e["hp"] = max(0, e["hp"] - max(1, int(hero["dmg"] - e["def"])))
                break
        
        for e in active_enemies:
            if e["hp"] > 0 and hero["hp"] > 0:
                hero["hp"] = max(0, hero["hp"] - max(1, int(e["dmg"] - hero["def"])))
                
        if all(e["hp"] <= 0 for e in active_enemies):
            state["current_stage"] += 1
            state["gold"] += int(state["zone_level"] * 5 * (1.0 + (state["prestige_rank"] - 1) * 0.3))
            if state["current_stage"] > state["stages_per_zone"]:
                state["zone_level"] += 1
                state["current_stage"] = 1
                state["max_historical_zone"] = max(state["max_historical_zone"], state["zone_level"])
            _spawn_zone_encounter()
        _update_ui()

    def _on_prestige_pressed(e):
        state["prestige_points"] += state["zone_level"]
        state["zone_level"] = 1
        state["current_stage"] = 1
        state["prestige_rank"] += 1
        _spawn_zone_encounter()

    def _update_ui():
        header_label.value = f"ZONE {state['zone_level']} | STAGE {state['current_stage']}/10"
        gold_label.value = f"GOLD: {state['gold']} | PRESTIGE: {state['prestige_points']} | TOKENS: {state['boss_tokens']}"
        
        hero = active_party[0]
        hero_stats_label.value = f"{hero['name'].upper()} - HP: {hero['hp']}/{hero['max_hp']}"
        hero_hp_bar.value = hero["hp"] / hero["max_hp"]
        
        enemy_list_view.controls.clear()
        for e in active_enemies:
            status = f"{e['name']} ({e['hp']}/{e['max_hp']})" if e["hp"] > 0 else f"{e['name']} [DESTROYED]"
            enemy_list_view.controls.append(ft.Text(value=status, color="red" if e["hp"] > 0 else "grey"))
        page.update()

    prestige_btn = ft.ElevatedButton(text="PRESTIGE RESET", on_click=_on_prestige_pressed)
    
    page.add(
        header_label, gold_label, hero_stats_label, hero_hp_bar,
        ft.Container(height=10), enemy_list_view, ft.Container(height=20), prestige_btn
    )
    
    _spawn_zone_encounter()
    
    # Background Clock Trigger
    def loop_ticker():
        while True:
            _execute_combat_tick()
            import time
            time.sleep(1.0)
            
    import threading
    threading.Thread(target=loop_ticker, daemon=True).start()

ft.app(target=main)
