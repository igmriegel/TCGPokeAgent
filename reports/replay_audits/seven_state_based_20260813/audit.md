# Seven replay state-based audit

Runtime replay-ID dependency: `false`.

| Replay | Decisions | Divergences | Categories |
|---:|---:|---:|---|
| 92410349 | 61 | 13 | estado_incorreto: 5, prioridade: 8 |
| 92351382 | 55 | 8 | prioridade: 7, estado_incorreto: 1 |
| 92344156 | 66 | 14 | prioridade: 8, linha_incompleta: 2, estado_incorreto: 4 |
| 92301028 | 76 | 14 | estado_incorreto: 5, prioridade: 7, linha_incompleta: 2 |
| 92280407 | 12 | 6 | estado_incorreto: 4, linha_incompleta: 2 |
| 92269436 | 35 | 10 | prioridade: 4, estado_incorreto: 2, linha_incompleta: 4 |
| 92201785 | 46 | 16 | estado_incorreto: 7, prioridade: 7, linha_incompleta: 2 |

## Divergences

### Replay 92410349

#### Step 13 (turn 2) — `estado_incorreto`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[4]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; canonical_ariana_resource_engine
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [677], "bench": [675, 676], "deck_count": 44, "discard": [1142, 1152], "hand": null, "hand_count": 5, "prize": [null, null, null, null, null, null]}, "own": {"active": [473], "bench": [], "deck_count": 45, "discard": [], "hand": [1217, 1216, 1220, 1220, 1219, 1134, 1218], "hand_count": 7, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 2, "turn_action_count": 2, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1216, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 1134, "index": 4, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 5, "type": "END"}]`
- Ranking: `[[[0], 1400.0, ["ariana_before_factory_hand_refresh", "ariana_hand_refresh_and_energy_access"]]]`

#### Step 14 (turn 2) — `prioridade`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[2]`
- Final action: `[5]`
- Corrected line: Execute final action [5]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [677], "bench": [675, 676], "deck_count": 44, "discard": [1142, 1152], "hand": null, "hand_count": 5, "prize": [null, null, null, null, null, null]}, "own": {"active": [473], "bench": [], "deck_count": 45, "discard": [], "hand": [1217, 1216, 1220, 1220, 1219, 1218], "hand_count": 6, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 2, "turn_action_count": 3, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1217, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 8, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 9, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 10, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 11, "type": "CARD"}]`
- Ranking: `[[[5], 120.0, ["search_useful_card"]], [[10], 120.0, ["search_useful_card"]], [[11], 120.0, ["search_useful_card"]], [[0], 80.0, ["search_useful_card"]], [[1], 80.0, ["search_useful_card"]], [[2], 80.0, ["search_useful_card"]], [[3], 80.0, ["search_useful_card"]], [[4], 80.0, ["search_useful_card"]], [[6], 80.0, ["search_useful_card"]], [[7], 80.0, ["search_useful_card"]], [[8], 80.0, ["search_useful_card"]], [[9], 80.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 15 (turn 2) — `estado_incorreto`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[1]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; canonical_ariana_resource_engine
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [677], "bench": [675, 676], "deck_count": 44, "discard": [1142, 1152], "hand": null, "hand_count": 5, "prize": [null, null, null, null, null, null]}, "own": {"active": [473], "bench": [], "deck_count": 44, "discard": [1134], "hand": [1217, 1216, 1220, 1220, 1219, 1218, 1216], "hand_count": 7, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 2, "turn_action_count": 4, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1216, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 1216, "index": 4, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 5, "type": "END"}]`
- Ranking: `[[[0], 1400.0, ["ariana_before_factory_hand_refresh", "ariana_hand_refresh_and_energy_access"]], [[4], 1400.0, ["ariana_before_factory_hand_refresh", "ariana_hand_refresh_and_energy_access"]]]`

#### Step 16 (turn 2) — `estado_incorreto`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[2, 3, 5]`
- Final action: `[1, 2, 3]`
- Corrected line: Execute final action [1,2,3]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [677], "bench": [675, 676], "deck_count": 44, "discard": [1142, 1152], "hand": null, "hand_count": 5, "prize": [null, null, null, null, null, null]}, "own": {"active": [473], "bench": [], "deck_count": 44, "discard": [1134], "hand": [1217, 1216, 1220, 1219, 1218, 1216], "hand_count": 6, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 2, "turn_action_count": 5, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 473, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 414, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 5, "type": "CARD"}]`
- Ranking: `[[[1, 2, 3], 330.0, ["search_useful_card"]], [[1, 2, 5], 330.0, ["search_useful_card"]], [[1, 3, 5], 330.0, ["search_useful_card"]], [[2, 3, 5], 330.0, ["search_useful_card"]], [[1, 2], 220.0, ["search_useful_card"]], [[1, 3], 220.0, ["search_useful_card"]], [[1, 5], 220.0, ["search_useful_card"]], [[2, 3], 220.0, ["search_useful_card"]], [[2, 5], 220.0, ["search_useful_card"]], [[3, 5], 220.0, ["search_useful_card"]], [[1], 110.0, ["search_useful_card"]], [[2], 110.0, ["search_useful_card"]], [[3], 110.0, ["search_useful_card"]], [[5], 110.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 39 (turn 4) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[0]`
- Final action: `[4]`
- Corrected line: Execute final action [4]; canonical_develop_board
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [678], "bench": [675, 676, 677, 677, 673], "deck_count": 35, "discard": [1142, 1152, 1227, 1152, 1152], "hand": null, "hand_count": 6, "prize": [null, null, null, null, null]}, "own": {"active": [463], "bench": [463, 463], "deck_count": 38, "discard": [1134, 1220, 473], "hand": [1217, 1216, 1220, 1219, 1218, 1216, 1216, 891, 1134], "hand_count": 9, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 4, "turn_action_count": 1, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1217, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 891, "index": 4, "type": "EVOLVE"}, {"attack_id": null, "card_id": 891, "index": 5, "type": "EVOLVE"}, {"attack_id": null, "card_id": 891, "index": 6, "type": "EVOLVE"}, {"attack_id": null, "card_id": 1134, "index": 7, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 8, "type": "END"}]`
- Ranking: `[[[4], 500.0, ["evolve_attacker"]], [[5], 500.0, ["evolve_attacker"]], [[6], 500.0, ["evolve_attacker"]]]`

#### Step 50 (turn 6) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[2]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; canonical_develop_board
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [678], "bench": [675, 676, 677, 677, 673], "deck_count": 37, "discard": [1142, 1152, 1227, 1152, 1152, 1102], "hand": null, "hand_count": 4, "prize": [null, null, null, null]}, "own": {"active": [463], "bench": [463, 473], "deck_count": 36, "discard": [1134, 1220, 1217, 1097, 463, 1216], "hand": [1077, 1220, 1217, 414, 1097, 1219, 891, 1216], "hand_count": 8, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 6, "turn_action_count": 2, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 414, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1097, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 891, "index": 3, "type": "EVOLVE"}, {"attack_id": null, "card_id": 891, "index": 4, "type": "EVOLVE"}, {"attack_id": null, "card_id": 1257, "index": 5, "type": "ABILITY"}, {"attack_id": null, "card_id": null, "index": 6, "type": "END"}]`
- Ranking: `[[[3], 500.0, ["evolve_attacker"]], [[4], 500.0, ["evolve_attacker"]]]`

#### Step 81 (turn 10) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[5]`
- Final action: `[4]`
- Corrected line: Execute final action [4]; canonical_develop_board
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [678], "bench": [675, 676, 678, 673, 673], "deck_count": 31, "discard": [1142, 1152, 1227, 1152, 1152, 1102, 1102, 678, 677], "hand": null, "hand_count": 6, "prize": [null, null, null]}, "own": {"active": [463], "bench": [474, 463], "deck_count": 27, "discard": [1134, 1220, 1217, 1097, 1216, 1097, 1216, 1077, 1220, 1217, 1219, 1219, 1220, 1218, 891, 463, 15], "hand": [414, 1077, 1134, 1077, 1257, 463, 1217, 1218], "hand_count": 8, "prize": [null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 10, "turn_action_count": 1, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1077, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1134, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1077, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 463, "index": 4, "type": "PLAY"}, {"attack_id": null, "card_id": 1217, "index": 5, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 6, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 7, "type": "END"}]`
- Ranking: `[[[4], 430.0, ["develop_attacker_line"]]]`

#### Step 110 (turn 14) — `prioridade`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[0]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; canonical_execute_ignition_attack
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [678], "bench": [675, 676, 678, 673, 673], "deck_count": 24, "discard": [1142, 1152, 1227, 1152, 1152, 1102, 1102, 678, 677, 1141, 1102, 1152], "hand": null, "hand_count": 9, "prize": [null]}, "own": {"active": [474], "bench": [], "deck_count": 25, "discard": [1134, 1220, 1217, 1097, 1216, 1097, 1216, 1077, 1220, 1217, 1219, 1219, 1220, 1218, 891, 463, 15, 1217, 463, 15, 463, 15], "hand": [1218, 1077, 1077, 17, 1152, 1218], "hand_count": 6, "prize": [null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 14, "turn_action_count": 2, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1077, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1152, "index": 2, "type": "PLAY"}, {"attack_id": 670, "card_id": 474, "index": 3, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 4, "type": "END"}]`
- Ranking: `[[[3], 720.0, ["porygon2_r_command", "rocket_discard_damage", "honchkrow_attack_for_prize_progress"]]]`

#### Step 112 (turn 14) — `prioridade`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[2]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; canonical_roto_after_factory
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [678], "bench": [675, 676, 678, 673, 673], "deck_count": 24, "discard": [1142, 1152, 1227, 1152, 1152, 1102, 1102, 678, 677, 1141, 1102, 1152], "hand": null, "hand_count": 9, "prize": [null]}, "own": {"active": [474], "bench": [], "deck_count": 24, "discard": [1134, 1220, 1217, 1097, 1216, 1097, 1216, 1077, 1220, 1217, 1219, 1219, 1220, 1218, 891, 463, 15, 1217, 463, 15, 463, 15, 1077], "hand": [1218, 1077, 17, 1152, 1218, 1216], "hand_count": 6, "prize": [null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 14, "turn_action_count": 4, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1152, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1216, "index": 2, "type": "PLAY"}, {"attack_id": 670, "card_id": 474, "index": 3, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 4, "type": "END"}]`
- Ranking: `[[[0], 980.0, ["roto_stick_required_before_partial_damage"]]]`

#### Step 115 (turn 14) — `prioridade`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[1]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; card
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [678], "bench": [675, 676, 678, 673, 673], "deck_count": 24, "discard": [1142, 1152, 1227, 1152, 1152, 1102, 1102, 678, 677, 1141, 1102, 1152], "hand": null, "hand_count": 9, "prize": [null]}, "own": {"active": [474], "bench": [], "deck_count": 19, "discard": [1134, 1220, 1217, 1097, 1216, 1097, 1216, 1077, 1220, 1217, 1219, 1219, 1220, 1218, 891, 463, 15, 1217, 463, 15, 463, 15, 1077, 1216], "hand": [1218, 1077, 17, 1152, 1218, 891, 1219, 414, 1152], "hand_count": 9, "prize": [null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 14, "turn_action_count": 7, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1218, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 3, "type": "CARD"}]`
- Ranking: `[[[3], 120.0, ["search_useful_card"]], [[0], 80.0, ["search_useful_card"]], [[1], 80.0, ["search_useful_card"]], [[2], 80.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 116 (turn 14) — `prioridade`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[0]`
- Final action: `[1]`
- Corrected line: Execute final action [1]; play_item
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [678], "bench": [675, 676, 678, 673, 673], "deck_count": 24, "discard": [1142, 1152, 1227, 1152, 1152, 1102, 1102, 678, 677, 1141, 1102, 1152], "hand": null, "hand_count": 9, "prize": [null]}, "own": {"active": [474], "bench": [], "deck_count": 18, "discard": [1134, 1220, 1217, 1097, 1216, 1097, 1216, 1077, 1220, 1217, 1219, 1219, 1220, 1218, 891, 463, 15, 1217, 463, 15, 463, 15, 1077, 1216, 1134], "hand": [1218, 1077, 17, 1152, 1218, 891, 1219, 414, 1152, 1220], "hand_count": 10, "prize": [null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 14, "turn_action_count": 8, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1152, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 414, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1152, "index": 3, "type": "PLAY"}, {"attack_id": 670, "card_id": 474, "index": 4, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 5, "type": "END"}]`
- Ranking: `[[[1], 620.0, ["poke_pad_murkrow_search"]], [[3], 620.0, ["poke_pad_murkrow_search"]]]`

#### Step 118 (turn 14) — `estado_incorreto`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[3]`
- Final action: `[1]`
- Corrected line: Execute final action [1]; card
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [678], "bench": [675, 676, 678, 673, 673], "deck_count": 24, "discard": [1142, 1152, 1227, 1152, 1152, 1102, 1102, 678, 677, 1141, 1102, 1152], "hand": null, "hand_count": 9, "prize": [null]}, "own": {"active": [474], "bench": [], "deck_count": 18, "discard": [1134, 1220, 1217, 1097, 1216, 1097, 1216, 1077, 1220, 1217, 1219, 1219, 1220, 1218, 891, 463, 15, 1217, 463, 15, 463, 15, 1077, 1216, 1134, 1077], "hand": [1218, 17, 1218, 891, 1219, 414, 1152, 1220], "hand_count": 8, "prize": [null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 14, "turn_action_count": 11, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 473, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 891, "index": 3, "type": "CARD"}]`
- Ranking: `[[[1], 110.0, ["search_useful_card"]], [[2], 110.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 122 (turn 14) — `estado_incorreto`

- Objective: `attack_or_control`
- Historical action: `[1]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; end
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [678], "bench": [675, 676, 678, 673, 673], "deck_count": 24, "discard": [1142, 1152, 1227, 1152, 1152, 1102, 1102, 678, 677, 1141, 1102, 1152], "hand": null, "hand_count": 9, "prize": [null]}, "own": {"active": [474], "bench": [463], "deck_count": 16, "discard": [1134, 1220, 1217, 1097, 1216, 1097, 1216, 1077, 1220, 1217, 1219, 1219, 1220, 1218, 891, 463, 15, 1217, 463, 15, 463, 15, 1077, 1216, 1134, 1077, 1152, 1152], "hand": [1218, 17, 1218, 891, 1219, 414, 1220, 891], "hand_count": 8, "prize": [null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 14, "turn_action_count": 15, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "PLAY"}, {"attack_id": 670, "card_id": 474, "index": 1, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 2, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 3, "type": "END"}]`
- Ranking: `[[[3], -998.0, ["end_only_after_productive_actions", "safe_end_turn"]]]`

### Replay 92351382

#### Step 13 (turn 2) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[0]`
- Final action: `[4]`
- Corrected line: Execute final action [4]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [791], "bench": [119, 119, 235, 119], "deck_count": 43, "discard": [1086, 1086], "hand": null, "hand_count": 4, "prize": [null, null, null, null, null, null]}, "own": {"active": [463], "bench": [463], "deck_count": 43, "discard": [1216], "hand": [1097, 1218, 1097, 474, 15, 1219, 1220], "hand_count": 7, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": true, "turn": 2, "turn_action_count": 3, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1216, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 8, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 9, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 10, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 11, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 12, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 13, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 14, "type": "CARD"}]`
- Ranking: `[[[4], 120.0, ["search_useful_card"]], [[7], 120.0, ["search_useful_card"]], [[12], 120.0, ["search_useful_card"]]]`

#### Step 89 (turn 8) — `estado_incorreto`

- Objective: `attack_or_control`
- Historical action: `[2]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [121], "bench": [235, 119, 121, 791], "deck_count": 30, "discard": [1086, 1086, 1152, 1213, 1086, 1198, 1198, 1097, 2], "hand": null, "hand_count": 4, "prize": [null, null, null, null]}, "own": {"active": [463], "bench": [414, 473], "deck_count": 36, "discard": [1216, 1134, 1216, 1152, 1220, 1216, 891, 463, 15, 463, 15], "hand": [1077, 17, 1077], "hand_count": 3, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 8, "turn_action_count": 2, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 474, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 891, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 3, "type": "CARD"}]`
- Ranking: `[[[0], 700.0, ["select_articuno_matchup_tech"]], [[1], 110.0, ["search_useful_card"]], [[3], 110.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 103 (turn 10) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[4]`
- Final action: `[5]`
- Corrected line: Execute final action [5]; end
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [121], "bench": [235, 119, 121, 791], "deck_count": 26, "discard": [1086, 1086, 1152, 1213, 1086, 1198, 1198, 1097, 2, 1227], "hand": null, "hand_count": 7, "prize": [null, null, null]}, "own": {"active": [473], "bench": [414], "deck_count": 34, "discard": [1216, 1134, 1216, 1152, 1220, 1216, 891, 463, 15, 463, 15, 1152, 891, 463], "hand": [1077, 17, 1077, 1217], "hand_count": 4, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 10, "turn_action_count": 1, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 1077, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 1217, "index": 4, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 5, "type": "END"}]`
- Ranking: `[[[5], -998.0, ["end_only_after_productive_actions", "safe_end_turn"]]]`

#### Step 110 (turn 10) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[5]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [121], "bench": [235, 119, 121, 791], "deck_count": 30, "discard": [1086, 1086, 1152, 1213, 1086, 1198, 1198, 1097, 2, 1227], "hand": null, "hand_count": 3, "prize": [null, null, null]}, "own": {"active": [473], "bench": [414, 463, 463], "deck_count": 30, "discard": [1216, 1134, 1216, 1152, 1220, 1216, 891, 15, 463, 15, 1152, 891, 463, 1217, 1097], "hand": [1220, 17, 1134, 1219], "hand_count": 4, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 10, "turn_action_count": 8, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1219, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 8, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 9, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 10, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 11, "type": "CARD"}]`
- Ranking: `[[[0], 120.0, ["search_useful_card"]], [[1], 120.0, ["search_useful_card"]], [[11], 120.0, ["search_useful_card"]]]`

#### Step 126 (turn 12) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[5]`
- Final action: `[7]`
- Corrected line: Execute final action [7]; canonical_factory_rescue_giovanni
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [121], "bench": [235, 119, 121, 791, 119], "deck_count": 25, "discard": [1086, 1086, 1152, 1213, 1086, 1198, 1198, 1097, 2, 1227, 1227], "hand": null, "hand_count": 6, "prize": [null, null]}, "own": {"active": [463], "bench": [414, 463], "deck_count": 27, "discard": [1216, 1134, 1216, 1152, 1220, 1216, 891, 15, 463, 15, 1152, 891, 463, 1217, 1097, 1134, 1134, 473], "hand": [1220, 17, 1219, 1216, 1219, 1218], "hand_count": 6, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 12, "turn_action_count": 1, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1220, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 3, "type": "ATTACH"}, {"attack_id": null, "card_id": 1219, "index": 4, "type": "PLAY"}, {"attack_id": null, "card_id": 1216, "index": 5, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 6, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 7, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 8, "type": "END"}]`
- Ranking: `[[[7], -2600.0, ["giovanni_without_immediate_ko_or_control", "giovanni_preserves_supporters_until_ko"]]]`

#### Step 151 (turn 14) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[8]`
- Final action: `[5]`
- Corrected line: Execute final action [5]; canonical_factory_rescue_giovanni
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [121], "bench": [235, 119, 121, 791, 120], "deck_count": 22, "discard": [1086, 1086, 1152, 1213, 1086, 1198, 1198, 1097, 2, 1227, 1227, 1198, 1121, 1256, 1121, 2], "hand": null, "hand_count": 5, "prize": [null]}, "own": {"active": [463], "bench": [414], "deck_count": 21, "discard": [1216, 1134, 1216, 1152, 1220, 1216, 891, 15, 463, 15, 1152, 891, 463, 1217, 1097, 1134, 1134, 473, 1216, 463, 15], "hand": [1220, 17, 1219, 1219, 1218, 474, 1219, 1152, 1217, 1217], "hand_count": 10, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 14, "turn_action_count": 1, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1220, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 1219, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 4, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 5, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 6, "type": "PLAY"}, {"attack_id": null, "card_id": 1152, "index": 7, "type": "PLAY"}, {"attack_id": null, "card_id": 1217, "index": 8, "type": "PLAY"}, {"attack_id": null, "card_id": 1217, "index": 9, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 10, "type": "END"}]`
- Ranking: `[[[5], -2600.0, ["giovanni_without_immediate_ko_or_control", "giovanni_preserves_supporters_until_ko"]]]`

#### Step 156 (turn 14) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[2]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; canonical_execute_ignition_attack
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [121], "bench": [235, 119, 121, 791, 120], "deck_count": 24, "discard": [1086, 1086, 1152, 1213, 1086, 1198, 1198, 1097, 2, 1227, 1227, 1198, 1121, 1256, 1121, 2], "hand": null, "hand_count": 3, "prize": [null]}, "own": {"active": [891], "bench": [414], "deck_count": 25, "discard": [1216, 1134, 1216, 1152, 1220, 1216, 15, 463, 15, 1152, 891, 463, 1217, 1097, 1134, 1134, 473, 1216, 463, 15, 1217, 1097], "hand": [1077, 1219, 1134], "hand_count": 3, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 14, "turn_action_count": 6, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1134, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1257, "index": 2, "type": "ABILITY"}, {"attack_id": 1285, "card_id": 891, "index": 3, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 4, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 5, "type": "END"}]`
- Ranking: `[[[3], 610.0, ["honchkrow_rocket_feathers", "rocket_hand_damage", "rocket_feathers_below_ko_threshold"]]]`

#### Step 157 (turn 14) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[2]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; play_item
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [121], "bench": [235, 119, 121, 791, 120], "deck_count": 24, "discard": [1086, 1086, 1152, 1213, 1086, 1198, 1198, 1097, 2, 1227, 1227, 1198, 1121, 1256, 1121, 2], "hand": null, "hand_count": 3, "prize": [null]}, "own": {"active": [891], "bench": [414], "deck_count": 23, "discard": [1216, 1134, 1216, 1152, 1220, 1216, 15, 463, 15, 1152, 891, 463, 1217, 1097, 1134, 1134, 473, 1216, 463, 15, 1217, 1097], "hand": [1077, 1219, 1134, 1219, 17], "hand_count": 5, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 14, "turn_action_count": 7, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1134, "index": 1, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 2, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 3, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 4, "type": "END"}]`
- Ranking: `[[[0], 980.0, ["roto_stick_required_before_partial_damage"]], [[1], 720.0, ["transceiver_proton_early_game"]]]`

### Replay 92344156

#### Step 8 (turn 1) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[0]`
- Final action: `[2]`
- Corrected line: Execute final action [2]; end
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [676], "bench": [675], "deck_count": 47, "discard": [], "hand": null, "hand_count": 5, "prize": [null, null, null, null, null, null]}, "own": {"active": [473], "bench": [463], "deck_count": 45, "discard": [1134], "hand": [1219, 1217, 1220, 1077, 891, 1216], "hand_count": 6, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": false, "turn": 1, "turn_action_count": 4, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1220, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1077, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 2, "type": "END"}]`
- Ranking: `[[[2], -998.0, ["end_only_after_productive_actions", "safe_end_turn"]]]`

#### Step 26 (turn 3) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[7]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; canonical_develop_board
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [676], "bench": [675, 677, 677, 673, 673], "deck_count": 40, "discard": [1227, 6], "hand": null, "hand_count": 6, "prize": [null, null, null, null, null]}, "own": {"active": [463], "bench": [463, 463, 463], "deck_count": 41, "discard": [1134, 1220, 473], "hand": [1219, 1217, 1077, 891, 1216], "hand_count": 5, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 3, "turn_action_count": 2, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1219, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1217, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1077, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 891, "index": 3, "type": "EVOLVE"}, {"attack_id": null, "card_id": 891, "index": 4, "type": "EVOLVE"}, {"attack_id": null, "card_id": 891, "index": 5, "type": "EVOLVE"}, {"attack_id": null, "card_id": 891, "index": 6, "type": "EVOLVE"}, {"attack_id": null, "card_id": 1216, "index": 7, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 8, "type": "END"}]`
- Ranking: `[[[3], 500.0, ["evolve_attacker"]], [[4], 500.0, ["evolve_attacker"]], [[5], 500.0, ["evolve_attacker"]], [[6], 500.0, ["evolve_attacker"]]]`

#### Step 55 (turn 5) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[6]`
- Final action: `[4]`
- Corrected line: Execute final action [4]; canonical_archer_preserves_nonlethal_rocket_supporters
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [678], "bench": [675, 678, 674, 673, 676], "deck_count": 32, "discard": [1227, 676, 1142, 1152, 1227], "hand": null, "hand_count": 6, "prize": [null, null, null, null]}, "own": {"active": [891], "bench": [463, 463], "deck_count": 34, "discard": [1134, 1220, 473, 1216, 1219, 1217, 17, 463], "hand": [1077, 414, 1077, 1152, 1217, 1217, 1219, 1219], "hand_count": 8, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 5, "turn_action_count": 1, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 414, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1077, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1152, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 1217, "index": 4, "type": "PLAY"}, {"attack_id": null, "card_id": 1217, "index": 5, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 6, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 7, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 8, "type": "END"}]`
- Ranking: `[[[4], -2400.0, ["archer_without_safe_disruption"]], [[5], -2400.0, ["archer_without_safe_disruption"]]]`

#### Step 61 (turn 5) — `linha_incompleta`

- Objective: `attack_or_control`
- Historical action: `[3]`
- Final action: `[4]`
- Corrected line: Execute final action [4]; end
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [678], "bench": [675, 678, 674, 673, 676], "deck_count": 32, "discard": [1227, 676, 1142, 1152, 1227], "hand": null, "hand_count": 6, "prize": [null, null, null, null]}, "own": {"active": [891], "bench": [891, 463], "deck_count": 30, "discard": [1134, 1220, 473, 1216, 1219, 1217, 17, 463, 1219, 1152], "hand": [1077, 414, 1077, 1217, 1217, 1219, 1121, 1220, 1217], "hand_count": 9, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 5, "turn_action_count": 7, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 414, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1077, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1121, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 4, "type": "END"}]`
- Ranking: `[[[4], -998.0, ["end_only_after_productive_actions", "safe_end_turn"]]]`

#### Step 62 (turn 5) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[3, 4]`
- Final action: `[1, 3]`
- Corrected line: Execute final action [1,3]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [678], "bench": [675, 678, 674, 673, 676], "deck_count": 32, "discard": [1227, 676, 1142, 1152, 1227], "hand": null, "hand_count": 6, "prize": [null, null, null, null]}, "own": {"active": [891], "bench": [891, 463], "deck_count": 30, "discard": [1134, 1220, 473, 1216, 1219, 1217, 17, 463, 1219, 1152], "hand": [1077, 414, 1077, 1217, 1217, 1219, 1220, 1217], "hand_count": 8, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 5, "turn_action_count": 8, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 414, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 7, "type": "CARD"}]`
- Ranking: `[[[1, 3], 70.0, ["preserve_pokemon_line", "discard_redundant_rocket_supporter"]], [[1, 4], 70.0, ["preserve_pokemon_line", "discard_redundant_rocket_supporter"]], [[1, 5], 70.0, ["preserve_pokemon_line", "discard_redundant_rocket_supporter"]], [[1, 6], 70.0, ["preserve_pokemon_line", "discard_redundant_rocket_supporter"]], [[1, 7], 70.0, ["preserve_pokemon_line", "discard_redundant_rocket_supporter"]], [[0, 1], -130.0, ["discard_replaceable_card", "preserve_pokemon_line"]], [[1, 2], -130.0, ["preserve_pokemon_line", "discard_replaceable_card"]]]`

#### Step 63 (turn 5) — `estado_incorreto`

- Objective: `attack_or_control`
- Historical action: `[1]`
- Final action: `[2]`
- Corrected line: Execute final action [2]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [678], "bench": [675, 678, 674, 673, 676], "deck_count": 32, "discard": [1227, 676, 1142, 1152, 1227], "hand": null, "hand_count": 6, "prize": [null, null, null, null]}, "own": {"active": [891], "bench": [891, 463], "deck_count": 30, "discard": [1134, 1220, 473, 1216, 1219, 1217, 17, 463, 1219, 1152, 1217, 1217], "hand": [1077, 414, 1077, 1219, 1220, 1217], "hand_count": 6, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 5, "turn_action_count": 9, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 474, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 891, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 473, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 414, "index": 3, "type": "CARD"}]`
- Ranking: `[[[2], 110.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 76 (turn 7) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[3]`
- Final action: `[5]`
- Corrected line: Execute final action [5]; canonical_archer_preserves_nonlethal_rocket_supporters
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [678], "bench": [675, 678, 674, 673, 676], "deck_count": 22, "discard": [1227, 676, 1142, 1152, 1227, 6, 1141, 673, 674, 677, 6, 6, 6, 1192, 1102], "hand": null, "hand_count": 6, "prize": [null, null, null]}, "own": {"active": [891], "bench": [891], "deck_count": 28, "discard": [1134, 1220, 473, 1216, 1219, 1217, 17, 463, 1219, 1152, 1217, 1217, 1121, 891, 463], "hand": [1077, 414, 1077, 1219, 1220, 1217, 1218], "hand_count": 7, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 7, "turn_action_count": 1, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 414, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1077, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 4, "type": "PLAY"}, {"attack_id": null, "card_id": 1217, "index": 5, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 6, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 7, "type": "END"}]`
- Ranking: `[[[5], -2400.0, ["archer_without_safe_disruption"]]]`

#### Step 77 (turn 7) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[3]`
- Final action: `[13]`
- Corrected line: Execute final action [13]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [678], "bench": [675, 678, 674, 673, 676], "deck_count": 22, "discard": [1227, 676, 1142, 1152, 1227, 6, 1141, 673, 674, 677, 6, 6, 6, 1192, 1102], "hand": null, "hand_count": 6, "prize": [null, null, null]}, "own": {"active": [891], "bench": [891], "deck_count": 28, "discard": [1134, 1220, 473, 1216, 1219, 1217, 17, 463, 1219, 1152, 1217, 1217, 1121, 891, 463], "hand": [1077, 414, 1077, 1220, 1217, 1218], "hand_count": 6, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 7, "turn_action_count": 2, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1218, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1109, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 8, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 9, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 10, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 11, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 12, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 13, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 14, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 15, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 16, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 17, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 18, "type": "CARD"}]`
- Ranking: `[[[13], 120.0, ["search_useful_card"]], [[0], 80.0, ["search_useful_card"]], [[1], 80.0, ["search_useful_card"]], [[2], 80.0, ["search_useful_card"]], [[3], 80.0, ["search_useful_card"]], [[4], 80.0, ["search_useful_card"]], [[5], 80.0, ["search_useful_card"]], [[6], 80.0, ["search_useful_card"]], [[7], 80.0, ["search_useful_card"]], [[8], 80.0, ["search_useful_card"]], [[9], 80.0, ["search_useful_card"]], [[10], 80.0, ["search_useful_card"]], [[11], 80.0, ["search_useful_card"]], [[12], 80.0, ["search_useful_card"]], [[14], 80.0, ["search_useful_card"]], [[15], 80.0, ["search_useful_card"]], [[16], 80.0, ["search_useful_card"]], [[17], 80.0, ["search_useful_card"]], [[18], 80.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 82 (turn 7) — `estado_incorreto`

- Objective: `attack_or_control`
- Historical action: `[0]`
- Final action: `[]`
- Corrected line: Execute final action []; end
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [678], "bench": [675, 678, 674, 673, 676], "deck_count": 22, "discard": [1227, 676, 1142, 1152, 1227, 6, 1141, 673, 674, 677, 6, 6, 6, 1192, 1102], "hand": null, "hand_count": 6, "prize": [null, null, null]}, "own": {"active": [891], "bench": [891, 473], "deck_count": 21, "discard": [1134, 1220, 473, 1216, 1219, 1217, 17, 463, 1219, 1152, 1217, 1217, 1121, 891, 463, 1219], "hand": [414, 1077, 1220, 1217, 1218, 1216], "hand_count": 6, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 7, "turn_action_count": 7, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1220, "index": 0, "type": "CARD"}]`
- Ranking: `[[[], 0.0, ["no_signal"]]]`

#### Step 106 (turn 9) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[1]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; canonical_recover_playable_pokemon
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [678], "bench": [675, 674, 673, 676, 677], "deck_count": 13, "discard": [1227, 676, 1142, 1152, 1227, 6, 1141, 673, 674, 677, 6, 6, 6, 1192, 1102, 678, 677, 6, 6, 1227, 1142, 6, 1142, 1152], "hand": null, "hand_count": 7, "prize": [null, null]}, "own": {"active": [891], "bench": [473], "deck_count": 21, "discard": [1134, 1220, 473, 1216, 1219, 1217, 17, 463, 1219, 1152, 1217, 1217, 1121, 891, 463, 1219, 1077, 1077, 1220, 1217, 1218, 1220, 1219, 1218, 1257, 891, 463, 15], "hand": [414, 1216, 1218, 1097, 1097], "hand_count": 5, "prize": [null, null]}, "retreated": false, "stadium": [1252], "supporter_played": false, "turn": 9, "turn_action_count": 2, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1216, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1097, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 1097, "index": 4, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 5, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 6, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 7, "type": "END"}]`
- Ranking: `[[[3], 1300.0, ["night_stretcher_hand_reduction_before_ariana"]], [[4], 1300.0, ["night_stretcher_hand_reduction_before_ariana"]]]`

#### Step 111 (turn 9) — `estado_incorreto`

- Objective: `attack_or_control`
- Historical action: `[1]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; card
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [678], "bench": [675, 674, 673, 676, 677], "deck_count": 13, "discard": [1227, 676, 1142, 1152, 1227, 6, 1141, 673, 674, 677, 6, 6, 6, 1192, 1102, 678, 677, 6, 6, 1227, 1142, 6, 1142, 1152, 1252], "hand": null, "hand_count": 7, "prize": [null, null]}, "own": {"active": [891], "bench": [473], "deck_count": 17, "discard": [1134, 1220, 473, 1216, 1219, 1217, 17, 463, 1219, 1152, 1217, 1217, 1121, 463, 1219, 1077, 1077, 1220, 1217, 1218, 1220, 1219, 1218, 1257, 891, 463, 15, 1216, 1097], "hand": [414, 1218, 1152, 1220, 1077, 891], "hand_count": 6, "prize": [null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 9, "turn_action_count": 7, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 473, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 891, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 4, "type": "CARD"}]`
- Ranking: `[[[0], 110.0, ["search_useful_card"]], [[1], 110.0, ["search_useful_card"]], [[2], 110.0, ["search_useful_card"]], [[4], 110.0, ["search_useful_card"]]]`

#### Step 114 (turn 9) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[2]`
- Final action: `[1]`
- Corrected line: Execute final action [1]; play_item
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [678], "bench": [675, 674, 673, 676, 677], "deck_count": 13, "discard": [1227, 676, 1142, 1152, 1227, 6, 1141, 673, 674, 677, 6, 6, 6, 1192, 1102, 678, 677, 6, 6, 1227, 1142, 6, 1142, 1152, 1252], "hand": null, "hand_count": 7, "prize": [null, null]}, "own": {"active": [891], "bench": [473, 463], "deck_count": 15, "discard": [1134, 1220, 473, 1216, 1219, 1217, 17, 1219, 1152, 1217, 1217, 1121, 463, 1219, 1077, 1077, 1220, 1217, 1218, 1220, 1219, 1218, 1257, 891, 463, 15, 1216, 1097, 1097], "hand": [414, 1218, 1152, 1220, 1077, 891, 15, 1152], "hand_count": 8, "prize": [null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 9, "turn_action_count": 10, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1152, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1077, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1152, "index": 3, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 4, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 5, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 6, "type": "END"}]`
- Ranking: `[[[1], 620.0, ["poke_pad_murkrow_search"]], [[3], 620.0, ["poke_pad_murkrow_search"]]]`

#### Step 120 (turn 9) — `estado_incorreto`

- Objective: `attack_or_control`
- Historical action: `[1]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; end
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [678], "bench": [675, 674, 673, 676, 677], "deck_count": 13, "discard": [1227, 676, 1142, 1152, 1227, 6, 1141, 673, 674, 677, 6, 6, 6, 1192, 1102, 678, 677, 6, 6, 1227, 1142, 6, 1142, 1152, 1252], "hand": null, "hand_count": 7, "prize": [null, null]}, "own": {"active": [891], "bench": [474, 463], "deck_count": 14, "discard": [1134, 1220, 473, 1216, 1219, 1217, 17, 1219, 1152, 1217, 1217, 1121, 463, 1219, 1077, 1077, 1220, 1217, 1218, 1220, 1219, 1218, 1257, 891, 463, 15, 1216, 1097, 1097, 1077, 1152, 1152], "hand": [414, 1218, 1220, 891, 15], "hand_count": 5, "prize": [null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 9, "turn_action_count": 17, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 1, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 2, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 3, "type": "END"}]`
- Ranking: `[[[3], -998.0, ["end_only_after_productive_actions", "safe_end_turn"]]]`

#### Step 136 (turn 11) — `linha_incompleta`

- Objective: `attack_or_control`
- Historical action: `[4]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; canonical_emergency_headset_before_factory
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [678], "bench": [675, 674, 673, 676, 678], "deck_count": 8, "discard": [1227, 676, 1142, 1152, 1227, 1141, 673, 674, 677, 6, 1192, 1102, 678, 677, 6, 6, 1227, 1142, 6, 1142, 1152, 1252, 6, 1141, 1152], "hand": null, "hand_count": 9, "prize": [null]}, "own": {"active": [891], "bench": [474], "deck_count": 13, "discard": [1134, 1220, 473, 1216, 1219, 1217, 17, 1219, 1152, 1217, 1217, 1121, 463, 1219, 1077, 1077, 1220, 1217, 1218, 1220, 1219, 1218, 1257, 891, 463, 15, 1216, 1097, 1097, 1077, 1152, 1152, 1218, 1220, 891, 463, 15], "hand": [414, 15, 1109], "hand_count": 3, "prize": [null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 11, "turn_action_count": 2, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 15, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 15, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 1109, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 4, "type": "END"}]`
- Ranking: `[[[3], 700.0, ["miracle_headset_ko_or_emergency_line"]]]`

### Replay 92301028

#### Step 17 (turn 2) — `estado_incorreto`

- Objective: `improve_resources`
- Historical action: `[1]`
- Final action: `[2]`
- Corrected line: Execute final action [2]; end
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [192], "bench": [169, 169, 57, 169], "deck_count": 38, "discard": [1206, 1225, 190, 190, 8, 1206, 1192, 1152, 1152], "hand": null, "hand_count": 1, "prize": [null, null, null, null, null, null]}, "own": {"active": [473], "bench": [463], "deck_count": 46, "discard": [], "hand": [1097, 1216, 891, 1220, 1217, 474], "hand_count": 6, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": false, "turn": 2, "turn_action_count": 2, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1216, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 2, "type": "END"}]`
- Ranking: `[[[2], -998.0, ["end_only_after_productive_actions", "safe_end_turn"]]]`

#### Step 27 (turn 4) — `estado_incorreto`

- Objective: `improve_resources`
- Historical action: `[1]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; canonical_recover_playable_pokemon
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [192], "bench": [169, 169, 57, 169], "deck_count": 37, "discard": [1206, 1225, 190, 190, 8, 1206, 1192, 1152, 1152], "hand": null, "hand_count": 2, "prize": [null, null, null, null, null]}, "own": {"active": [463], "bench": [463, 463, 463], "deck_count": 42, "discard": [1220, 473], "hand": [1097, 1216, 891, 1217, 474, 1220], "hand_count": 6, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": false, "turn": 4, "turn_action_count": 1, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1097, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1216, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 891, "index": 2, "type": "EVOLVE"}, {"attack_id": null, "card_id": 891, "index": 3, "type": "EVOLVE"}, {"attack_id": null, "card_id": 891, "index": 4, "type": "EVOLVE"}, {"attack_id": null, "card_id": 891, "index": 5, "type": "EVOLVE"}, {"attack_id": null, "card_id": 1217, "index": 6, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 7, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 8, "type": "END"}]`
- Ranking: `[[[0], 1300.0, ["night_stretcher_hand_reduction_before_ariana"]]]`

#### Step 47 (turn 8) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[2]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; canonical_roto_after_factory
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [169], "bench": [169, 57, 169, 192], "deck_count": 35, "discard": [1206, 1225, 190, 190, 8, 1206, 1192, 1152, 1152, 192, 8, 8], "hand": null, "hand_count": 2, "prize": [null, null, null, null, null]}, "own": {"active": [891], "bench": [463, 463, 463, 474], "deck_count": 30, "discard": [1220, 1216, 1097, 1217, 1220, 1216, 17, 1216], "hand": [1097, 1077, 414, 1217, 1134, 17, 1109, 1216], "hand_count": 8, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 8, "turn_action_count": 6, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 414, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1134, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1109, "index": 3, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 4, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 5, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 6, "type": "END"}]`
- Ranking: `[[[0], 980.0, ["roto_stick_required_before_partial_damage"]]]`

#### Step 49 (turn 8) — `prioridade`

- Objective: `highest_prize_ko`
- Historical action: `[3]`
- Final action: `[2]`
- Corrected line: Execute final action [2]; canonical_headset_contextual
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [169], "bench": [169, 57, 169, 192], "deck_count": 35, "discard": [1206, 1225, 190, 190, 8, 1206, 1192, 1152, 1152, 192, 8, 8], "hand": null, "hand_count": 2, "prize": [null, null, null, null, null]}, "own": {"active": [891], "bench": [463, 463, 463, 474], "deck_count": 29, "discard": [1220, 1216, 1097, 1217, 1220, 1216, 17, 1216, 1134], "hand": [1097, 1077, 414, 1217, 17, 1109, 1216, 1219], "hand_count": 8, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 8, "turn_action_count": 8, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 414, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1109, "index": 2, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 3, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 4, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 5, "type": "END"}]`
- Ranking: `[[[2], -2200.0, ["reserve_miracle_headset"]]]`

#### Step 62 (turn 10) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[0]`
- Final action: `[8]`
- Corrected line: Execute final action [8]; canonical_factory_rescue_giovanni
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [190], "bench": [57, 169, 192], "deck_count": 33, "discard": [1206, 1225, 190, 190, 1206, 1192, 1152, 1152, 192, 8, 169, 8, 1122, 169, 1121], "hand": null, "hand_count": 0, "prize": [null, null, null, null, null]}, "own": {"active": [891], "bench": [463, 463, 463, 474], "deck_count": 28, "discard": [1220, 1216, 1097, 1217, 1220, 1216, 17, 1216, 1134, 1217, 1216, 1219], "hand": [1097, 1077, 414, 17, 1109, 1218, 1220], "hand_count": 7, "prize": [null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 10, "turn_action_count": 1, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 414, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 17, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 3, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 4, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 5, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 6, "type": "ATTACH"}, {"attack_id": null, "card_id": 1109, "index": 7, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 8, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 9, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 10, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 11, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 12, "type": "END"}]`
- Ranking: `[[[8], -2600.0, ["giovanni_without_immediate_ko_or_control", "giovanni_preserves_supporters_until_ko"]]]`

#### Step 64 (turn 10) — `linha_incompleta`

- Objective: `attack_or_control`
- Historical action: `[6]`
- Final action: `[7]`
- Corrected line: Execute final action [7]; canonical_factory_rescue_giovanni
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [190], "bench": [57, 169, 192], "deck_count": 33, "discard": [1206, 1225, 190, 190, 1206, 1192, 1152, 1152, 192, 8, 169, 8, 1122, 169, 1121], "hand": null, "hand_count": 0, "prize": [null, null, null, null, null]}, "own": {"active": [891], "bench": [463, 463, 463, 474], "deck_count": 27, "discard": [1220, 1216, 1097, 1217, 1220, 1216, 17, 1216, 1134, 1217, 1216, 1219, 1077], "hand": [1097, 414, 17, 1109, 1218, 1220, 1217], "hand_count": 7, "prize": [null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 10, "turn_action_count": 3, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 3, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 4, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 5, "type": "ATTACH"}, {"attack_id": null, "card_id": 1109, "index": 6, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 7, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 8, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 9, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 10, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 11, "type": "END"}]`
- Ranking: `[[[7], -2600.0, ["giovanni_without_immediate_ko_or_control", "giovanni_preserves_supporters_until_ko"]]]`

#### Step 65 (turn 10) — `estado_incorreto`

- Objective: `attack_or_control`
- Historical action: `[1, 2]`
- Final action: `[2, 8]`
- Corrected line: Execute final action [2,8]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [190], "bench": [57, 169, 192], "deck_count": 33, "discard": [1206, 1225, 190, 190, 1206, 1192, 1152, 1152, 192, 8, 169, 8, 1122, 169, 1121], "hand": null, "hand_count": 0, "prize": [null, null, null, null, null]}, "own": {"active": [891], "bench": [463, 463, 463, 474], "deck_count": 27, "discard": [1220, 1216, 1097, 1217, 1220, 1216, 17, 1216, 1134, 1217, 1216, 1219, 1077], "hand": [1097, 414, 17, 1218, 1220, 1217], "hand_count": 6, "prize": [null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 10, "turn_action_count": 4, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1220, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 8, "type": "CARD"}]`
- Ranking: `[[[2, 8], 200.0, ["search_useful_card"]], [[6, 8], 200.0, ["search_useful_card"]], [[2, 6], 160.0, ["search_useful_card"]], [[8], 120.0, ["search_useful_card"]], [[2], 80.0, ["search_useful_card"]], [[6], 80.0, ["search_useful_card"]], [[0, 8], -880.0, ["confirmed_prized_unsearchable", "search_useful_card"]], [[1, 8], -880.0, ["confirmed_prized_unsearchable", "search_useful_card"]], [[3, 8], -880.0, ["confirmed_prized_unsearchable", "search_useful_card"]], [[4, 8], -880.0, ["confirmed_prized_unsearchable", "search_useful_card"]], [[5, 8], -880.0, ["confirmed_prized_unsearchable", "search_useful_card"]], [[7, 8], -880.0, ["confirmed_prized_unsearchable", "search_useful_card"]], [[0, 2], -920.0, ["confirmed_prized_unsearchable", "search_useful_card"]], [[0, 6], -920.0, ["confirmed_prized_unsearchable", "search_useful_card"]], [[1, 2], -920.0, ["confirmed_prized_unsearchable", "search_useful_card"]], [[1, 6], -920.0, ["confirmed_prized_unsearchable", "search_useful_card"]], [[2, 3], -920.0, ["search_useful_card", "confirmed_prized_unsearchable"]], [[2, 4], -920.0, ["search_useful_card", "confirmed_prized_unsearchable"]], [[2, 5], -920.0, ["search_useful_card", "confirmed_prized_unsearchable"]], [[2, 7], -920.0, ["search_useful_card", "confirmed_prized_unsearchable"]], [[3, 6], -920.0, ["confirmed_prized_unsearchable", "search_useful_card"]], [[4, 6], -920.0, ["confirmed_prized_unsearchable", "search_useful_card"]], [[5, 6], -920.0, ["confirmed_prized_unsearchable", "search_useful_card"]], [[6, 7], -920.0, ["search_useful_card", "confirmed_prized_unsearchable"]], [[0], -1000.0, ["confirmed_prized_unsearchable"]], [[1], -1000.0, ["confirmed_prized_unsearchable"]], [[3], -1000.0, ["confirmed_prized_unsearchable"]], [[4], -1000.0, ["confirmed_prized_unsearchable"]], [[5], -1000.0, ["confirmed_prized_unsearchable"]], [[7], -1000.0, ["confirmed_prized_unsearchable"]], [[0, 1], -2000.0, ["confirmed_prized_unsearchable"]], [[0, 3], -2000.0, ["confirmed_prized_unsearchable"]], [[0, 4], -2000.0, ["confirmed_prized_unsearchable"]], [[0, 5], -2000.0, ["confirmed_prized_unsearchable"]], [[0, 7], -2000.0, ["confirmed_prized_unsearchable"]], [[1, 3], -2000.0, ["confirmed_prized_unsearchable"]], [[1, 4], -2000.0, ["confirmed_prized_unsearchable"]], [[1, 5], -2000.0, ["confirmed_prized_unsearchable"]], [[1, 7], -2000.0, ["confirmed_prized_unsearchable"]], [[3, 4], -2000.0, ["confirmed_prized_unsearchable"]], [[3, 5], -2000.0, ["confirmed_prized_unsearchable"]], [[3, 7], -2000.0, ["confirmed_prized_unsearchable"]], [[4, 5], -2000.0, ["confirmed_prized_unsearchable"]], [[4, 7], -2000.0, ["confirmed_prized_unsearchable"]], [[5, 7], -2000.0, ["confirmed_prized_unsearchable"]]]`

#### Step 66 (turn 10) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[8]`
- Final action: `[6]`
- Corrected line: Execute final action [6]; canonical_factory_rescue_giovanni
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [190], "bench": [57, 169, 192], "deck_count": 33, "discard": [1206, 1225, 190, 190, 1206, 1192, 1152, 1152, 192, 8, 169, 8, 1122, 169, 1121], "hand": null, "hand_count": 0, "prize": [null, null, null, null, null]}, "own": {"active": [891], "bench": [463, 463, 463, 474], "deck_count": 27, "discard": [1220, 1097, 1220, 1216, 17, 1216, 1134, 1217, 1216, 1219, 1077, 1109], "hand": [1097, 414, 17, 1218, 1220, 1217, 1216, 1217], "hand_count": 8, "prize": [null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 10, "turn_action_count": 5, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 3, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 4, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 5, "type": "ATTACH"}, {"attack_id": null, "card_id": 1218, "index": 6, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 7, "type": "PLAY"}, {"attack_id": null, "card_id": 1216, "index": 8, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 9, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 10, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 11, "type": "END"}]`
- Ranking: `[[[6], -2600.0, ["giovanni_without_immediate_ko_or_control", "giovanni_preserves_supporters_until_ko"]]]`

#### Step 76 (turn 12) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[6]`
- Final action: `[8]`
- Corrected line: Execute final action [8]; canonical_factory_rescue_giovanni
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [169], "bench": [57, 192], "deck_count": 32, "discard": [1206, 1225, 190, 190, 1206, 1192, 1152, 1152, 192, 8, 169, 8, 1122, 169, 1121, 190, 169, 8, 8], "hand": null, "hand_count": 0, "prize": [null, null, null, null, null]}, "own": {"active": [891], "bench": [463, 463, 463, 474], "deck_count": 22, "discard": [1220, 1097, 1220, 1216, 17, 1216, 1134, 1217, 1216, 1219, 1077, 1109, 1216, 1077, 1218, 1220, 1217, 1217, 1218], "hand": [1097, 414, 17, 1257, 1077, 1219, 1218, 1257], "hand_count": 8, "prize": [null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 12, "turn_action_count": 1, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 3, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 4, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 5, "type": "ATTACH"}, {"attack_id": null, "card_id": 1077, "index": 6, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 7, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 8, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 9, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 10, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 11, "type": "END"}]`
- Ranking: `[[[8], -2600.0, ["giovanni_without_immediate_ko_or_control", "giovanni_preserves_supporters_until_ko"]]]`

#### Step 77 (turn 12) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[8]`
- Final action: `[7]`
- Corrected line: Execute final action [7]; canonical_factory_rescue_giovanni
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [169], "bench": [57, 192], "deck_count": 32, "discard": [1206, 1225, 190, 190, 1206, 1192, 1152, 1152, 192, 8, 169, 8, 1122, 169, 1121, 190, 169, 8, 8], "hand": null, "hand_count": 0, "prize": [null, null, null, null, null]}, "own": {"active": [891], "bench": [463, 463, 463, 474], "deck_count": 22, "discard": [1220, 1097, 1220, 1216, 17, 1216, 1134, 1217, 1216, 1219, 1077, 1109, 1216, 1077, 1218, 1220, 1217, 1217, 1218, 1077], "hand": [1097, 414, 17, 1257, 1219, 1218, 1257], "hand_count": 7, "prize": [null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 12, "turn_action_count": 3, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 3, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 4, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 5, "type": "ATTACH"}, {"attack_id": null, "card_id": 1219, "index": 6, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 7, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 8, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 9, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 10, "type": "END"}]`
- Ranking: `[[[7], -2600.0, ["giovanni_without_immediate_ko_or_control", "giovanni_preserves_supporters_until_ko"]]]`

#### Step 103 (turn 16) — `estado_incorreto`

- Objective: `attack_or_control`
- Historical action: `[1]`
- Final action: `[]`
- Corrected line: Execute final action []; end
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [190], "bench": [57, 192], "deck_count": 30, "discard": [1206, 1225, 190, 190, 1206, 1192, 1152, 1152, 192, 169, 1122, 169, 1121, 190, 169, 8, 8], "hand": null, "hand_count": 2, "prize": [null, null, null]}, "own": {"active": [463], "bench": [463, 474, 473], "deck_count": 16, "discard": [1220, 1097, 1220, 1216, 17, 1216, 1134, 1217, 1216, 1219, 1077, 1109, 1216, 1077, 1218, 1220, 1217, 1217, 1218, 1077, 1219, 1218, 463, 15, 1097, 17, 891, 463, 1134, 1219], "hand": [414, 1257, 1257, 17, 1121], "hand_count": 5, "prize": [null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 16, "turn_action_count": 8, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 891, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 891, "index": 2, "type": "CARD"}]`
- Ranking: `[[[], 0.0, ["no_signal"]]]`

#### Step 105 (turn 16) — `linha_incompleta`

- Objective: `attack_or_control`
- Historical action: `[5]`
- Final action: `[6]`
- Corrected line: Execute final action [6]; end
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [190], "bench": [57, 192], "deck_count": 30, "discard": [1206, 1225, 190, 190, 1206, 1192, 1152, 1152, 192, 169, 1122, 169, 1121, 190, 169, 8, 8], "hand": null, "hand_count": 2, "prize": [null, null, null]}, "own": {"active": [891], "bench": [463, 474, 473], "deck_count": 15, "discard": [1220, 1097, 1220, 1216, 17, 1216, 1134, 1217, 1216, 1219, 1077, 1109, 1216, 1077, 1218, 1220, 1217, 1217, 1218, 1077, 1219, 1218, 463, 15, 1097, 17, 891, 463, 1134, 1219, 1152], "hand": [414, 1257, 1257, 17, 1121], "hand_count": 5, "prize": [null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 16, "turn_action_count": 10, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 414, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 3, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 4, "type": "ATTACH"}, {"attack_id": null, "card_id": 1121, "index": 5, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 6, "type": "END"}]`
- Ranking: `[[[6], -998.0, ["end_only_after_productive_actions", "safe_end_turn"]]]`

#### Step 107 (turn 16) — `estado_incorreto`

- Objective: `attack_or_control`
- Historical action: `[0]`
- Final action: `[]`
- Corrected line: Execute final action []; end
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [190], "bench": [57, 192], "deck_count": 30, "discard": [1206, 1225, 190, 190, 1206, 1192, 1152, 1152, 192, 169, 1122, 169, 1121, 190, 169, 8, 8], "hand": null, "hand_count": 2, "prize": [null, null, null]}, "own": {"active": [891], "bench": [463, 474, 473], "deck_count": 15, "discard": [1220, 1097, 1220, 1216, 17, 1216, 1134, 1217, 1216, 1219, 1077, 1109, 1216, 1077, 1218, 1220, 1217, 1217, 1218, 1077, 1219, 1218, 463, 15, 1097, 17, 891, 463, 1134, 1219, 1152, 1257, 1257], "hand": [414, 17], "hand_count": 2, "prize": [null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 16, "turn_action_count": 12, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 891, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 414, "index": 1, "type": "CARD"}]`
- Ranking: `[[[], 0.0, ["no_signal"]]]`

#### Step 123 (turn 20) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[6]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [190], "bench": [57, 192], "deck_count": 28, "discard": [1206, 1225, 190, 190, 1206, 1192, 1152, 1152, 192, 169, 1122, 169, 1121, 190, 169, 8, 8], "hand": null, "hand_count": 4, "prize": [null]}, "own": {"active": [463], "bench": [474, 473], "deck_count": 12, "discard": [1220, 1097, 1220, 1216, 17, 1216, 1134, 1217, 1216, 1219, 1077, 1109, 1216, 1077, 1218, 1220, 1217, 1217, 1218, 1077, 1219, 1218, 15, 1097, 17, 891, 463, 1134, 1219, 1152, 1257, 1257, 1121, 891, 463, 1097, 891, 463], "hand": [414, 17], "hand_count": 2, "prize": [null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 20, "turn_action_count": 2, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1217, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 7, "type": "CARD"}]`
- Ranking: `[[[0], 80.0, ["search_useful_card"]], [[1], 80.0, ["search_useful_card"]], [[2], 80.0, ["search_useful_card"]], [[3], 80.0, ["search_useful_card"]], [[4], 80.0, ["search_useful_card"]], [[5], 80.0, ["search_useful_card"]], [[6], 80.0, ["search_useful_card"]], [[7], 80.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

### Replay 92280407

#### Step 14 (turn 2) — `estado_incorreto`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[5]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; play_item
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [235], "bench": [140, 119], "deck_count": 45, "discard": [1246, 1121, 1097], "hand": null, "hand_count": 2, "prize": [null, null, null, null, null, null]}, "own": {"active": [463], "bench": [], "deck_count": 45, "discard": [], "hand": [1216, 1152, 1217, 1220, 1134, 1216, 1219, 891], "hand_count": 8, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": false, "turn": 2, "turn_action_count": 1, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1216, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1152, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1134, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 1216, "index": 4, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 5, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 6, "type": "END"}]`
- Ranking: `[[[3], 1550.0, ["transceiver_ariana_preserves_petrel"]], [[1], 860.0, ["poke_pad_honchkrow_search"]]]`

#### Step 15 (turn 2) — `linha_incompleta`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[12]`
- Final action: `[14]`
- Corrected line: Execute final action [14]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [235], "bench": [140, 119], "deck_count": 45, "discard": [1246, 1121, 1097], "hand": null, "hand_count": 2, "prize": [null, null, null, null, null, null]}, "own": {"active": [463], "bench": [], "deck_count": 45, "discard": [], "hand": [1216, 1152, 1217, 1220, 1134, 1216, 891], "hand_count": 7, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": true, "turn": 2, "turn_action_count": 2, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1257, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 1121, "index": 8, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 9, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 10, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 11, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 12, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 13, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 14, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 15, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 16, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 17, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 18, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 19, "type": "CARD"}, {"attack_id": null, "card_id": 1109, "index": 20, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 21, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 22, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 23, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 24, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 25, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 26, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 27, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 28, "type": "CARD"}]`
- Ranking: `[[[14], 120.0, ["search_useful_card"]], [[28], 120.0, ["search_useful_card"]]]`

#### Step 16 (turn 2) — `estado_incorreto`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[1]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; play_item
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [235], "bench": [140, 119], "deck_count": 45, "discard": [1246, 1121, 1097], "hand": null, "hand_count": 2, "prize": [null, null, null, null, null, null]}, "own": {"active": [463], "bench": [], "deck_count": 44, "discard": [1219], "hand": [1216, 1152, 1217, 1220, 1134, 1216, 891, 1220], "hand_count": 8, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": true, "turn": 2, "turn_action_count": 3, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1152, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1134, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 2, "type": "END"}]`
- Ranking: `[[[0], 860.0, ["poke_pad_honchkrow_search"]], [[1], 720.0, ["transceiver_proton_early_game"]]]`

#### Step 31 (turn 4) — `estado_incorreto`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[3]`
- Final action: `[1]`
- Corrected line: Execute final action [1]; canonical_develop_empty_bench
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [235], "bench": [140, 120, 119, 112], "deck_count": 36, "discard": [1246, 1121, 1097, 1227, 1152], "hand": null, "hand_count": 5, "prize": [null, null, null, null, null, null]}, "own": {"active": [463], "bench": [], "deck_count": 41, "discard": [1219, 1134, 1152], "hand": [1216, 1217, 1220, 1216, 891, 1220, 1219, 891, 1077], "hand_count": 9, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": false, "turn": 4, "turn_action_count": 1, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1220, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 891, "index": 1, "type": "EVOLVE"}, {"attack_id": null, "card_id": 1220, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 891, "index": 4, "type": "EVOLVE"}, {"attack_id": null, "card_id": null, "index": 5, "type": "END"}]`
- Ranking: `[[[1], 500.0, ["evolve_attacker"]], [[4], 500.0, ["evolve_attacker"]]]`

#### Step 32 (turn 4) — `linha_incompleta`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[9]`
- Final action: `[1]`
- Corrected line: Execute final action [1]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [235], "bench": [140, 120, 119, 112], "deck_count": 36, "discard": [1246, 1121, 1097, 1227, 1152], "hand": null, "hand_count": 5, "prize": [null, null, null, null, null, null]}, "own": {"active": [463], "bench": [], "deck_count": 41, "discard": [1219, 1134, 1152], "hand": [1216, 1217, 1220, 1216, 891, 1220, 891, 1077], "hand_count": 8, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": true, "turn": 4, "turn_action_count": 2, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 1134, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1121, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 8, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 9, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 10, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 11, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 12, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 13, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 14, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 15, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 16, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 17, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 18, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 19, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 20, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 21, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 22, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 23, "type": "CARD"}, {"attack_id": null, "card_id": 1109, "index": 24, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 25, "type": "CARD"}]`
- Ranking: `[[[1], 150.0, ["search_useful_card"]], [[3], 120.0, ["search_useful_card"]], [[0], 80.0, ["search_useful_card"]], [[2], 80.0, ["search_useful_card"]], [[4], 80.0, ["search_useful_card"]], [[5], 80.0, ["search_useful_card"]], [[6], 80.0, ["search_useful_card"]], [[7], 80.0, ["search_useful_card"]], [[8], 80.0, ["search_useful_card"]], [[9], 80.0, ["search_useful_card"]], [[10], 80.0, ["search_useful_card"]], [[11], 80.0, ["search_useful_card"]], [[12], 80.0, ["search_useful_card"]], [[13], 80.0, ["search_useful_card"]], [[14], 80.0, ["search_useful_card"]], [[15], 80.0, ["search_useful_card"]], [[16], 80.0, ["search_useful_card"]], [[17], 80.0, ["search_useful_card"]], [[18], 80.0, ["search_useful_card"]], [[19], 80.0, ["search_useful_card"]], [[20], 80.0, ["search_useful_card"]], [[21], 80.0, ["search_useful_card"]], [[22], 80.0, ["search_useful_card"]], [[23], 80.0, ["search_useful_card"]], [[24], 80.0, ["search_useful_card"]], [[25], 80.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 33 (turn 4) — `estado_incorreto`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[2]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; canonical_develop_empty_bench
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [235], "bench": [140, 120, 119, 112], "deck_count": 36, "discard": [1246, 1121, 1097, 1227, 1152], "hand": null, "hand_count": 5, "prize": [null, null, null, null, null, null]}, "own": {"active": [463], "bench": [], "deck_count": 40, "discard": [1219, 1134, 1152, 1219], "hand": [1216, 1217, 1220, 1216, 891, 1220, 891, 1077, 1220], "hand_count": 9, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": true, "turn": 4, "turn_action_count": 3, "your_index": 1}`
- Legal candidates: `[{"attack_id": null, "card_id": 891, "index": 0, "type": "EVOLVE"}, {"attack_id": null, "card_id": 891, "index": 1, "type": "EVOLVE"}, {"attack_id": null, "card_id": null, "index": 2, "type": "END"}]`
- Ranking: `[[[0], 500.0, ["evolve_attacker"]], [[1], 500.0, ["evolve_attacker"]]]`

### Replay 92269436

#### Step 6 (turn 1) — `prioridade`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[5]`
- Final action: `[8]`
- Corrected line: Execute final action [8]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [860], "bench": [], "deck_count": 45, "discard": [], "hand": null, "hand_count": 8, "prize": [null, null, null, null, null, null]}, "own": {"active": [414], "bench": [], "deck_count": 46, "discard": [], "hand": [17, 15, 1220, 1217, 1216, 1152], "hand_count": 6, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": false, "turn": 1, "turn_action_count": 2, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1220, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 8, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 9, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 10, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 11, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 12, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 13, "type": "CARD"}]`
- Ranking: `[[[8], 120.0, ["search_useful_card"]], [[9], 120.0, ["search_useful_card"]], [[11], 120.0, ["search_useful_card"]]]`

#### Step 7 (turn 1) — `estado_incorreto`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[2]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; canonical_poke_pad_before_ariana
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [860], "bench": [], "deck_count": 45, "discard": [], "hand": null, "hand_count": 8, "prize": [null, null, null, null, null, null]}, "own": {"active": [414], "bench": [], "deck_count": 45, "discard": [1134], "hand": [17, 15, 1220, 1217, 1216, 1152, 1216], "hand_count": 7, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": false, "turn": 1, "turn_action_count": 3, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 17, "index": 0, "type": "ATTACH"}, {"attack_id": null, "card_id": 15, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 1220, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1152, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 4, "type": "END"}]`
- Ranking: `[[[3], 620.0, ["poke_pad_murkrow_search"]]]`

#### Step 8 (turn 1) — `estado_incorreto`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[1, 2, 3]`
- Final action: `[0, 1, 2]`
- Corrected line: Execute final action [0,1,2]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [860], "bench": [], "deck_count": 45, "discard": [], "hand": null, "hand_count": 8, "prize": [null, null, null, null, null, null]}, "own": {"active": [414], "bench": [], "deck_count": 45, "discard": [1134], "hand": [17, 15, 1217, 1216, 1152, 1216], "hand_count": 6, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": true, "turn": 1, "turn_action_count": 4, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 473, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 473, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 414, "index": 5, "type": "CARD"}]`
- Ranking: `[[[0, 1, 2], 330.0, ["search_useful_card"]], [[0, 1, 3], 330.0, ["search_useful_card"]], [[0, 1, 4], 330.0, ["search_useful_card"]], [[0, 2, 3], 330.0, ["search_useful_card"]], [[0, 2, 4], 330.0, ["search_useful_card"]], [[0, 3, 4], 330.0, ["search_useful_card"]], [[1, 2, 3], 330.0, ["search_useful_card"]], [[1, 2, 4], 330.0, ["search_useful_card"]], [[1, 3, 4], 330.0, ["search_useful_card"]], [[2, 3, 4], 330.0, ["search_useful_card"]], [[0, 1], 220.0, ["search_useful_card"]], [[0, 2], 220.0, ["search_useful_card"]], [[0, 3], 220.0, ["search_useful_card"]], [[0, 4], 220.0, ["search_useful_card"]], [[1, 2], 220.0, ["search_useful_card"]], [[1, 3], 220.0, ["search_useful_card"]], [[1, 4], 220.0, ["search_useful_card"]], [[2, 3], 220.0, ["search_useful_card"]], [[2, 4], 220.0, ["search_useful_card"]], [[3, 4], 220.0, ["search_useful_card"]], [[0], 110.0, ["search_useful_card"]], [[1], 110.0, ["search_useful_card"]], [[2], 110.0, ["search_useful_card"]], [[3], 110.0, ["search_useful_card"]], [[4], 110.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 44 (turn 5) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[6]`
- Final action: `[7]`
- Corrected line: Execute final action [7]; canonical_giovanni_prize_target
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [647], "bench": [104, 647, 112, 646], "deck_count": 31, "discard": [1086, 1152, 1231, 1227, 7], "hand": null, "hand_count": 8, "prize": [null, null, null, null, null, null]}, "own": {"active": [414], "bench": [891, 463, 463], "deck_count": 35, "discard": [1134, 1220, 1152, 1216], "hand": [17, 1217, 1216, 1077, 1219, 1097, 1218, 1220], "hand_count": 8, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1259], "supporter_played": false, "turn": 5, "turn_action_count": 1, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 17, "index": 0, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 3, "type": "ATTACH"}, {"attack_id": null, "card_id": 1216, "index": 4, "type": "PLAY"}, {"attack_id": null, "card_id": 1077, "index": 5, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 6, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 7, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 8, "type": "PLAY"}, {"attack_id": null, "card_id": 1259, "index": 9, "type": "ABILITY"}, {"attack_id": null, "card_id": null, "index": 10, "type": "END"}]`
- Ranking: `[[[7], 1600.0, ["giovanni_immediate_ko_line"]]]`

#### Step 45 (turn 5) — `linha_incompleta`

- Objective: `attack_or_control`
- Historical action: `[2]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [647], "bench": [104, 647, 112, 646], "deck_count": 31, "discard": [1086, 1152, 1231, 1227, 7], "hand": null, "hand_count": 8, "prize": [null, null, null, null, null, null]}, "own": {"active": [414], "bench": [891, 463, 463], "deck_count": 35, "discard": [1134, 1220, 1152, 1216], "hand": [17, 1217, 1216, 1077, 1097, 1218, 1220], "hand_count": 7, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1259], "supporter_played": true, "turn": 5, "turn_action_count": 2, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1219, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 8, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 9, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 10, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 11, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 12, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 13, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 14, "type": "CARD"}, {"attack_id": null, "card_id": 1121, "index": 15, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 16, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 17, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 18, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 19, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 20, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 21, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 22, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 23, "type": "CARD"}, {"attack_id": null, "card_id": 1109, "index": 24, "type": "CARD"}]`
- Ranking: `[[[0], 120.0, ["search_useful_card"]], [[3], 120.0, ["search_useful_card"]], [[1], 80.0, ["search_useful_card"]], [[2], 80.0, ["search_useful_card"]], [[4], 80.0, ["search_useful_card"]], [[5], 80.0, ["search_useful_card"]], [[6], 80.0, ["search_useful_card"]], [[7], 80.0, ["search_useful_card"]], [[8], 80.0, ["search_useful_card"]], [[9], 80.0, ["search_useful_card"]], [[10], 80.0, ["search_useful_card"]], [[11], 80.0, ["search_useful_card"]], [[12], 80.0, ["search_useful_card"]], [[13], 80.0, ["search_useful_card"]], [[14], 80.0, ["search_useful_card"]], [[16], 80.0, ["search_useful_card"]], [[17], 80.0, ["search_useful_card"]], [[18], 80.0, ["search_useful_card"]], [[19], 80.0, ["search_useful_card"]], [[20], 80.0, ["search_useful_card"]], [[21], 80.0, ["search_useful_card"]], [[22], 80.0, ["search_useful_card"]], [[23], 80.0, ["search_useful_card"]], [[24], 80.0, ["search_useful_card"]], [[15], 70.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 74 (turn 7) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[0]`
- Final action: `[]`
- Corrected line: Execute final action []; end
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [648], "bench": [104, 647, 112, 646], "deck_count": 29, "discard": [1086, 1152, 1231, 1227, 7, 1122, 1219, 1259], "hand": null, "hand_count": 3, "prize": [null, null, null, null, null]}, "own": {"active": [891], "bench": [463, 463], "deck_count": 30, "discard": [1134, 1220, 1152, 1216, 1219, 414, 1217], "hand": [1219, 17, 1109, 1121, 1217], "hand_count": 5, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 7, "turn_action_count": 5, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1218, "index": 0, "type": "CARD"}]`
- Ranking: `[[[], 0.0, ["no_signal"]]]`

#### Step 75 (turn 7) — `linha_incompleta`

- Objective: `attack_or_control`
- Historical action: `[4]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; canonical_headset_contextual
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [648], "bench": [104, 647, 112, 646], "deck_count": 29, "discard": [1086, 1152, 1231, 1227, 7, 1122, 1219, 1259], "hand": null, "hand_count": 3, "prize": [null, null, null, null, null]}, "own": {"active": [891], "bench": [463, 463], "deck_count": 33, "discard": [1134, 1220, 1152, 1216, 1219, 414, 1217, 1077], "hand": [1219, 17, 1109, 1121, 1217, 1218], "hand_count": 6, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 7, "turn_action_count": 6, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 17, "index": 0, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 1109, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 1121, "index": 4, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 5, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 6, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 7, "type": "END"}]`
- Ranking: `[[[3], -2200.0, ["reserve_miracle_headset"]]]`

#### Step 79 (turn 7) — `linha_incompleta`

- Objective: `attack_or_control`
- Historical action: `[6]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; canonical_emergency_headset_before_factory
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [648], "bench": [104, 647, 112, 646], "deck_count": 29, "discard": [1086, 1152, 1231, 1227, 7, 1122, 1219, 1259], "hand": null, "hand_count": 3, "prize": [null, null, null, null, null]}, "own": {"active": [891], "bench": [891, 463], "deck_count": 32, "discard": [1134, 1220, 1152, 1216, 1219, 414, 1217, 1077, 1219, 1217, 1121], "hand": [17, 1109, 1218], "hand_count": 3, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 7, "turn_action_count": 10, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 17, "index": 0, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 1109, "index": 3, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 4, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 5, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 6, "type": "END"}]`
- Ranking: `[[[3], 700.0, ["miracle_headset_ko_or_emergency_line"]]]`

#### Step 106 (turn 9) — `linha_incompleta`

- Objective: `attack_or_control`
- Historical action: `[4]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; canonical_post_ko_best_supporter
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [648], "bench": [104, 647, 112, 648, 112], "deck_count": 23, "discard": [1086, 1152, 1231, 1227, 1122, 1219, 1259, 1152, 1097, 1219, 1079], "hand": null, "hand_count": 3, "prize": [null, null, null, null]}, "own": {"active": [891], "bench": [463], "deck_count": 31, "discard": [1134, 1220, 1152, 1216, 1219, 414, 1217, 1077, 1219, 1217, 1121, 891, 463, 15], "hand": [17, 1109, 1218, 1257], "hand_count": 4, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 9, "turn_action_count": 1, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 17, "index": 0, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 1109, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 3, "type": "PLAY"}, {"attack_id": 1285, "card_id": 891, "index": 4, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 5, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 6, "type": "END"}]`
- Ranking: `[[[3], -2600.0, ["giovanni_without_immediate_ko_or_control", "giovanni_preserves_supporters_until_ko"]]]`

#### Step 107 (turn 9) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[0]`
- Final action: `[]`
- Corrected line: Execute final action []; end
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [648], "bench": [104, 647, 112, 648, 112], "deck_count": 23, "discard": [1086, 1152, 1231, 1227, 1122, 1219, 1259, 1152, 1097, 1219, 1079], "hand": null, "hand_count": 3, "prize": [null, null, null, null]}, "own": {"active": [891], "bench": [463], "deck_count": 31, "discard": [1134, 1220, 1152, 1216, 1219, 414, 1217, 1077, 1219, 1217, 1121, 891, 463, 15], "hand": [17, 1109, 1218, 1257], "hand_count": 4, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 9, "turn_action_count": 2, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1218, "index": 0, "type": "CARD"}]`
- Ranking: `[[[], 0.0, ["no_signal"]]]`

### Replay 92201785

#### Step 7 (turn 1) — `estado_incorreto`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[5]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [722], "bench": [], "deck_count": 47, "discard": [], "hand": null, "hand_count": 6, "prize": [null, null, null, null, null, null]}, "own": {"active": [473], "bench": [], "deck_count": 45, "discard": [1220, 1134], "hand": [1216, 17, 17, 1152, 1077], "hand_count": 5, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": false, "turn": 1, "turn_action_count": 3, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 463, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 414, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 891, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 474, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 473, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 414, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 891, "index": 8, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 9, "type": "CARD"}]`
- Ranking: `[[[0], 110.0, ["search_useful_card"]], [[2], 110.0, ["search_useful_card"]], [[4], 110.0, ["search_useful_card"]], [[5], 110.0, ["search_useful_card"]], [[6], 110.0, ["search_useful_card"]], [[9], 110.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 9 (turn 1) — `estado_incorreto`

- Objective: `prevent_no_pokemon_loss`
- Historical action: `[2]`
- Final action: `[1]`
- Corrected line: Execute final action [1]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [722], "bench": [], "deck_count": 47, "discard": [], "hand": null, "hand_count": 6, "prize": [null, null, null, null, null, null]}, "own": {"active": [473], "bench": [], "deck_count": 44, "discard": [1220, 1134, 1121], "hand": [1216, 17, 17, 1077, 474], "hand_count": 5, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": false, "turn": 1, "turn_action_count": 5, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 891, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 473, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 414, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 891, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 414, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 463, "index": 8, "type": "CARD"}]`
- Ranking: `[[[1], 110.0, ["search_useful_card"]], [[2], 110.0, ["search_useful_card"]], [[3], 110.0, ["search_useful_card"]], [[4], 110.0, ["search_useful_card"]], [[8], 110.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 17 (turn 3) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[1]`
- Final action: `[6]`
- Corrected line: Execute final action [6]; canonical_transceiver_for_proton
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [722], "bench": [721], "deck_count": 46, "discard": [], "hand": null, "hand_count": 4, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [463], "deck_count": 42, "discard": [1220, 1134, 1121, 1152], "hand": [1216, 17, 17, 1077, 1134], "hand_count": 5, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": false, "turn": 3, "turn_action_count": 2, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1216, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 2, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 3, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 4, "type": "ATTACH"}, {"attack_id": null, "card_id": 1077, "index": 5, "type": "PLAY"}, {"attack_id": null, "card_id": 1134, "index": 6, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 7, "type": "END"}]`
- Ranking: `[[[6], 980.0, ["transceiver_ariana_resource_engine"]]]`

#### Step 19 (turn 3) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[1]`
- Final action: `[2]`
- Corrected line: Execute final action [2]; card
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [722], "bench": [721], "deck_count": 46, "discard": [], "hand": null, "hand_count": 4, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [463], "deck_count": 42, "discard": [1220, 1134, 1121, 1152], "hand": [1216, 17, 1077], "hand_count": 3, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": false, "turn": 3, "turn_action_count": 4, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1217, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 8, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 9, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 10, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 11, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 12, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 13, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 14, "type": "CARD"}]`
- Ranking: `[[[2], 120.0, ["search_useful_card"]], [[6], 120.0, ["search_useful_card"]], [[10], 120.0, ["search_useful_card"]], [[11], 120.0, ["search_useful_card"]]]`

#### Step 21 (turn 3) — `prioridade`

- Objective: `improve_resources`
- Historical action: `[0]`
- Final action: `[2]`
- Corrected line: Execute final action [2]; play_item
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [722], "bench": [721], "deck_count": 46, "discard": [], "hand": null, "hand_count": 4, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [463], "deck_count": 36, "discard": [1220, 1134, 1121, 1152, 1134, 1216], "hand": [17, 1077, 1216, 1219, 1097, 1077, 1217, 1134], "hand_count": 8, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": true, "turn": 3, "turn_action_count": 6, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1077, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1134, "index": 2, "type": "PLAY"}, {"attack_id": 670, "card_id": 474, "index": 3, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 4, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 5, "type": "END"}]`
- Ranking: `[[[2], 720.0, ["transceiver_proton_early_game"]]]`

#### Step 22 (turn 3) — `estado_incorreto`

- Objective: `attack_or_control`
- Historical action: `[0]`
- Final action: `[]`
- Corrected line: Execute final action []; end
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [722], "bench": [721], "deck_count": 46, "discard": [], "hand": null, "hand_count": 4, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [463], "deck_count": 32, "discard": [1220, 1134, 1121, 1152, 1134, 1216], "hand": [17, 1216, 1219, 1097, 1077, 1217, 1134], "hand_count": 7, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": true, "turn": 3, "turn_action_count": 7, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1220, "index": 0, "type": "CARD"}]`
- Ranking: `[[[], 0.0, ["no_signal"]]]`

#### Step 23 (turn 3) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[0]`
- Final action: `[1]`
- Corrected line: Execute final action [1]; play_item
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [722], "bench": [721], "deck_count": 46, "discard": [], "hand": null, "hand_count": 4, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [463], "deck_count": 35, "discard": [1220, 1134, 1121, 1152, 1134, 1216, 1077], "hand": [17, 1216, 1219, 1097, 1077, 1217, 1134, 1220], "hand_count": 8, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": true, "turn": 3, "turn_action_count": 8, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1077, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1134, "index": 1, "type": "PLAY"}, {"attack_id": 670, "card_id": 474, "index": 2, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 3, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 4, "type": "END"}]`
- Ranking: `[[[1], 720.0, ["transceiver_proton_early_game"]]]`

#### Step 24 (turn 3) — `estado_incorreto`

- Objective: `attack_or_control`
- Historical action: `[0, 1, 2]`
- Final action: `[0, 1]`
- Corrected line: Execute final action [0,1]; card
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [722], "bench": [721], "deck_count": 46, "discard": [], "hand": null, "hand_count": 4, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [463], "deck_count": 31, "discard": [1220, 1134, 1121, 1152, 1134, 1216, 1077], "hand": [17, 1216, 1219, 1097, 1217, 1134, 1220], "hand_count": 7, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": true, "turn": 3, "turn_action_count": 9, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1219, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1220, "index": 2, "type": "CARD"}]`
- Ranking: `[[[0, 1], 200.0, ["search_useful_card"]], [[0], 120.0, ["search_useful_card"]], [[0, 1, 2], -800.0, ["search_useful_card", "confirmed_prized_unsearchable"]], [[0, 2], -880.0, ["search_useful_card", "confirmed_prized_unsearchable"]]]`

#### Step 27 (turn 3) — `estado_incorreto`

- Objective: `attack_or_control`
- Historical action: `[0]`
- Final action: `[2]`
- Corrected line: Execute final action [2]; end
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [722], "bench": [721], "deck_count": 46, "discard": [], "hand": null, "hand_count": 4, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [463], "deck_count": 31, "discard": [1220, 1134, 1121, 1152, 1134, 1216, 1077, 1077, 1134], "hand": [17, 1216, 1219, 1097, 1217, 1220, 1219, 1216, 1220, 1219], "hand_count": 10, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": true, "turn": 3, "turn_action_count": 12, "your_index": 0}`
- Legal candidates: `[{"attack_id": 670, "card_id": 474, "index": 0, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 1, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 2, "type": "END"}]`
- Ranking: `[[[2], -998.0, ["end_only_after_productive_actions", "safe_end_turn"]]]`

#### Step 29 (turn 5) — `estado_incorreto`

- Objective: `improve_resources`
- Historical action: `[0]`
- Final action: `[7]`
- Corrected line: Execute final action [7]; canonical_develop_board
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [722], "bench": [721], "deck_count": 45, "discard": [], "hand": null, "hand_count": 5, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [463], "deck_count": 30, "discard": [1220, 1134, 1121, 1152, 1134, 1216, 1077, 1077, 1134, 17], "hand": [17, 1216, 1219, 1097, 1217, 1220, 1219, 1216, 1220, 1219, 463], "hand_count": 11, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": false, "turn": 5, "turn_action_count": 1, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 17, "index": 0, "type": "ATTACH"}, {"attack_id": null, "card_id": 17, "index": 1, "type": "ATTACH"}, {"attack_id": null, "card_id": 1219, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 4, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 5, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 6, "type": "PLAY"}, {"attack_id": null, "card_id": 463, "index": 7, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 8, "type": "END"}]`
- Ranking: `[[[7], 430.0, ["develop_attacker_line"]]]`

#### Step 32 (turn 5) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[5]`
- Final action: `[3]`
- Corrected line: Execute final action [3]; card
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [722], "bench": [721], "deck_count": 45, "discard": [], "hand": null, "hand_count": 5, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [463, 463], "deck_count": 30, "discard": [1220, 1134, 1121, 1152, 1134, 1216, 1077, 1077, 1134, 17], "hand": [1216, 1097, 1217, 1220, 1219, 1216, 1220, 1219], "hand_count": 8, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [], "supporter_played": true, "turn": 5, "turn_action_count": 4, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1152, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1109, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 8, "type": "CARD"}, {"attack_id": null, "card_id": 1134, "index": 9, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 10, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 11, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 12, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 13, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 14, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 15, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 16, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 17, "type": "CARD"}]`
- Ranking: `[[[3], 120.0, ["search_useful_card"]], [[0], 80.0, ["search_useful_card"]], [[1], 80.0, ["search_useful_card"]], [[2], 80.0, ["search_useful_card"]], [[4], 80.0, ["search_useful_card"]], [[5], 80.0, ["search_useful_card"]], [[6], 80.0, ["search_useful_card"]], [[7], 80.0, ["search_useful_card"]], [[8], 80.0, ["search_useful_card"]], [[9], 80.0, ["search_useful_card"]], [[10], 80.0, ["search_useful_card"]], [[11], 80.0, ["search_useful_card"]], [[12], 80.0, ["search_useful_card"]], [[13], 80.0, ["search_useful_card"]], [[14], 80.0, ["search_useful_card"]], [[15], 80.0, ["search_useful_card"]], [[16], 80.0, ["search_useful_card"]], [[17], 80.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 34 (turn 5) — `estado_incorreto`

- Objective: `highest_prize_ko`
- Historical action: `[1]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; canonical_factory_after_supporter
- Public state: `{"energy_attached": true, "first_player": 0, "opponent": {"active": [722], "bench": [721], "deck_count": 45, "discard": [], "hand": null, "hand_count": 5, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [463, 463], "deck_count": 29, "discard": [1220, 1134, 1121, 1152, 1134, 1216, 1077, 1077, 1134, 17, 1219], "hand": [1216, 1097, 1217, 1220, 1219, 1216, 1220, 1219], "hand_count": 8, "prize": [null, null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 5, "turn_action_count": 6, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1257, "index": 0, "type": "ABILITY"}, {"attack_id": 670, "card_id": 474, "index": 1, "type": "ATTACK"}, {"attack_id": null, "card_id": null, "index": 2, "type": "RETREAT"}, {"attack_id": null, "card_id": null, "index": 3, "type": "END"}]`
- Ranking: `[[[0], 450.0, ["use_available_ability"]]]`

#### Step 43 (turn 7) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[3]`
- Final action: `[1]`
- Corrected line: Execute final action [1]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [721], "bench": [], "deck_count": 45, "discard": [722, 1158], "hand": null, "hand_count": 5, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [891, 463], "deck_count": 27, "discard": [1220, 1134, 1121, 1152, 1134, 1216, 1077, 1077, 1134, 17, 1219, 17, 1152], "hand": [1216, 1097, 1217, 1220, 1216, 1220, 1219, 1217], "hand_count": 8, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 7, "turn_action_count": 5, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1134, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1216, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1109, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 8, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 9, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 10, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 11, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 12, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 13, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 14, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 15, "type": "CARD"}]`
- Ranking: `[[[1], 120.0, ["search_useful_card"]], [[0], 80.0, ["search_useful_card"]], [[2], 80.0, ["search_useful_card"]], [[3], 80.0, ["search_useful_card"]], [[4], 80.0, ["search_useful_card"]], [[5], 80.0, ["search_useful_card"]], [[6], 80.0, ["search_useful_card"]], [[7], 80.0, ["search_useful_card"]], [[8], 80.0, ["search_useful_card"]], [[9], 80.0, ["search_useful_card"]], [[10], 80.0, ["search_useful_card"]], [[11], 80.0, ["search_useful_card"]], [[12], 80.0, ["search_useful_card"]], [[13], 80.0, ["search_useful_card"]], [[14], 80.0, ["search_useful_card"]], [[15], 80.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

#### Step 45 (turn 7) — `linha_incompleta`

- Objective: `attack_or_control`
- Historical action: `[1]`
- Final action: `[0]`
- Corrected line: Execute final action [0]; canonical_headset_contextual
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [721], "bench": [], "deck_count": 45, "discard": [722, 1158], "hand": null, "hand_count": 5, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [891, 463], "deck_count": 24, "discard": [1220, 1134, 1121, 1152, 1134, 1216, 1077, 1077, 1134, 17, 1219, 17, 1152, 1219], "hand": [1216, 1097, 1217, 1220, 1216, 1220, 1219, 1217, 1216, 1218, 1109], "hand_count": 11, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 7, "turn_action_count": 7, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1109, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 1, "type": "END"}]`
- Ranking: `[[[0], -2200.0, ["reserve_miracle_headset"]]]`

#### Step 47 (turn 9) — `linha_incompleta`

- Objective: `improve_resources`
- Historical action: `[2]`
- Final action: `[4]`
- Corrected line: Execute final action [4]; canonical_headset_contextual
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [721], "bench": [], "deck_count": 44, "discard": [722, 1158], "hand": null, "hand_count": 6, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [891, 463], "deck_count": 23, "discard": [1220, 1134, 1121, 1152, 1134, 1216, 1077, 1077, 1134, 17, 1219, 17, 1152, 1219], "hand": [1216, 1097, 1217, 1220, 1216, 1220, 1219, 1217, 1216, 1218, 1109, 1218], "hand_count": 12, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": false, "turn": 9, "turn_action_count": 1, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1220, "index": 0, "type": "PLAY"}, {"attack_id": null, "card_id": 1220, "index": 1, "type": "PLAY"}, {"attack_id": null, "card_id": 1219, "index": 2, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 3, "type": "PLAY"}, {"attack_id": null, "card_id": 1109, "index": 4, "type": "PLAY"}, {"attack_id": null, "card_id": 1218, "index": 5, "type": "PLAY"}, {"attack_id": null, "card_id": null, "index": 6, "type": "END"}]`
- Ranking: `[[[4], -2200.0, ["reserve_miracle_headset"]]]`

#### Step 48 (turn 9) — `prioridade`

- Objective: `attack_or_control`
- Historical action: `[5]`
- Final action: `[6]`
- Corrected line: Execute final action [6]; card
- Public state: `{"energy_attached": false, "first_player": 0, "opponent": {"active": [721], "bench": [], "deck_count": 44, "discard": [722, 1158], "hand": null, "hand_count": 6, "prize": [null, null, null, null, null, null]}, "own": {"active": [474], "bench": [891, 463], "deck_count": 23, "discard": [1220, 1134, 1121, 1152, 1134, 1216, 1077, 1077, 1134, 17, 1219, 17, 1152, 1219], "hand": [1216, 1097, 1217, 1220, 1216, 1220, 1217, 1216, 1218, 1109, 1218], "hand_count": 11, "prize": [null, null, null, null, null]}, "retreated": false, "stadium": [1257], "supporter_played": true, "turn": 9, "turn_action_count": 2, "your_index": 0}`
- Legal candidates: `[{"attack_id": null, "card_id": 1134, "index": 0, "type": "CARD"}, {"attack_id": null, "card_id": 1217, "index": 1, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 2, "type": "CARD"}, {"attack_id": null, "card_id": 1152, "index": 3, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 4, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 5, "type": "CARD"}, {"attack_id": null, "card_id": 1219, "index": 6, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 7, "type": "CARD"}, {"attack_id": null, "card_id": 1218, "index": 8, "type": "CARD"}, {"attack_id": null, "card_id": 1097, "index": 9, "type": "CARD"}, {"attack_id": null, "card_id": 1077, "index": 10, "type": "CARD"}, {"attack_id": null, "card_id": 1257, "index": 11, "type": "CARD"}]`
- Ranking: `[[[6], 120.0, ["search_useful_card"]], [[0], 80.0, ["search_useful_card"]], [[1], 80.0, ["search_useful_card"]], [[2], 80.0, ["search_useful_card"]], [[3], 80.0, ["search_useful_card"]], [[4], 80.0, ["search_useful_card"]], [[5], 80.0, ["search_useful_card"]], [[7], 80.0, ["search_useful_card"]], [[8], 80.0, ["search_useful_card"]], [[9], 80.0, ["search_useful_card"]], [[10], 80.0, ["search_useful_card"]], [[11], 80.0, ["search_useful_card"]], [[], 0.0, ["no_signal"]]]`

