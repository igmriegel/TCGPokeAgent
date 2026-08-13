# Cartas com redução ou prevenção de dano

Inventário extraído do catálogo canônico do CABT (`cg.api`), sem alteração de código de gameplay. A seleção cobre ataques e efeitos que reduzem dano, previnem todo o dano ou impedem a colocação de contadores de dano.

## Legenda dos códigos

| Código | Categoria |
|---|---|
| `P` | Pokémon |
| `A` | Ataque de Pokémon |
| `I` | Item ou Fóssil |
| `S` | Apoiador (Supporter) |
| `ST` | Estádio |

Nos Pokémon, o código é `P / A`: a linha é de um Pokémon e descreve um ataque. Para Item/Fóssil, Apoiador e Estádio, o SDK não fornece `attack_id`; por isso o campo aparece como `—` e o nome do efeito é mantido.

## Pokémon — 46 ataques defensivos

Os ataques estão separados pelo resultado defensivo: invulnerabilidade/prevenção total quando a condição do texto é satisfeita, ou redução quantitativa de dano.

### Invulnerabilidade — prevenção total (22 ataques)

| Código | Carta | Ataque | Texto original | `card_id` | `attack_id` | Classificação |
|---|---|---|---|---:|---:|---|
| `P / A` | Dunsparce | Dig | Flip a coin. If heads, during your opponent’s next turn, prevent all damage from and effects of attacks done to this Pokémon. | 65 | 75 | prevenção total |
| `P / A` | Terapagos ex | Crown Opal | During your opponent’s next turn, prevent all damage done to this Pokémon by attacks from Basic non-{C} Pokémon. | 176 | 233 | prevenção total |
| `P / A` | Flittle | Splashing Dodge | Flip a coin. If heads, during your opponent’s next turn, prevent all damage from and effects of attacks done to this Pokémon. | 185 | 244 | prevenção total |
| `P / A` | Altaria | Cotton Wings | Flip a coin. If heads, during your opponent’s next turn, prevent all damage done to this Pokémon by attacks. | 194 | 261 | prevenção total |
| `P / A` | Metapod | Harden | During your opponent’s next turn, prevent all damage done to this Pokémon by attacks if that damage is 60 or less. | 253 | 349 | prevenção total |
| `P / A` | Cynthia's Feebas | Undulate | Flip a coin. If heads, during your opponent’s next turn, prevent all damage from and effects of attacks done to this Pokémon. | 365 | 505 | prevenção total |
| `P / A` | Barraskewda | Dive | Flip a coin. If heads, during your opponent’s next turn, prevent all damage from and effects of attacks done to this Pokémon. | 422 | 595 | prevenção total |
| `P / A` | Petilil | Hide | Flip a coin. If heads, during your opponent’s next turn, prevent all damage from and effects of attacks done to this Pokémon. | 484 | 684 | prevenção total |
| `P / A` | Tranquill | Fly | Flip a coin. If tails, this attack does nothing. If heads, during your opponent’s next turn, prevent all damage from and effects of attacks done to this Pokémon. | 552 | 788 | prevenção total |
| `P / A` | Unfezant | Swift Flight | Flip a coin. If heads, during your opponent’s next turn, prevent all damage from and effects of attacks done to this Pokémon. | 553 | 790 | prevenção total |
| `P / A` | Roggenrola | Harden | During your opponent’s next turn, prevent all damage done to this Pokémon by attacks if that damage is 40 or less. | 599 | 860 | prevenção total |
| `P / A` | Marshadow | Shadowy Side Kick | If your opponent’s Pokémon is Knocked Out by damage from this attack, during your opponent’s next turn, prevent all damage from and effects of attacks done to this Pokémon. | 681 | 986 | prevenção total |
| `P / A` | Snom | Hide | Flip a coin. If heads, during your opponent’s next turn, prevent all damage from and effects of attacks done to this Pokémon. | 729 | 1054 | prevenção total |
| `P / A` | Mega Manectric ex | Flash Ray | During your opponent’s next turn, prevent all damage done to this Pokémon by attacks from Basic Pokémon. | 737 | 1064 | prevenção total |
| `P / A` | Bronzor | Iron Defense | Flip a coin. If heads, during your opponent’s next turn, prevent all damage done to this Pokémon by attacks. | 836 | 1205 | prevenção total |
| `P / A` | Archaludon | Coated Attack | During your opponent’s next turn, prevent all damage done to this Pokémon by attacks from Basic Pokémon. | 840 | 1212 | prevenção total |
| `P / A` | Hop's Phantump | Splashing Dodge | Flip a coin. If heads, during your opponent’s next turn, prevent all damage from and effects of attacks done to this Pokémon. | 878 | 1266 | prevenção total |
| `P / A` | Noivern | Agility | Flip a coin. If heads, during your opponent’s next turn, prevent all damage from and effects of attacks done to this Pokémon. | 908 | 1309 | prevenção total |
| `P / A` | Dipplin | Coated Attack | During your opponent’s next turn, prevent all damage done to this Pokémon by attacks from Basic Pokémon. | 921 | 1327 | prevenção total |
| `P / A` | Marill | Hide | Flip a coin. If heads, during your opponent’s next turn, prevent all damage from and effects of attacks done to this Pokémon. | 961 | 1382 | prevenção total |
| `P / A` | Koraidon ex | Tera | As long as this Pokémon is on your Bench, prevent all damage done to this Pokémon by attacks (both yours and your opponent’s). | 979 | 1408 | prevenção total |
| `P / A` | Spewpa | Hide | Flip a coin. If heads, during your opponent’s next turn, prevent all damage from and effects of attacks done to this Pokémon. | 1018 | 1470 | prevenção total |

### Redução de dano (24 ataques)

| Código | Carta | Ataque | Texto original | `card_id` | `attack_id` | Classificação |
|---|---|---|---|---:|---:|---|
| `P / A` | Seedot | Rigidify | During your opponent’s next turn, this Pokémon takes 30 less damage from attacks (after applying Weakness and Resistance). | 68 | 78 | redução de dano |
| `P / A` | Scizor ex | Steel Wing | During your opponent’s next turn, this Pokémon takes 50 less damage from attacks (after applying Weakness and Resistance). | 84 | 100 | redução de dano |
| `P / A` | Varoom | Rigidify | During your opponent’s next turn, this Pokémon takes 30 less damage from attacks (after applying Weakness and Resistance). | 143 | 186 | redução de dano |
| `P / A` | Hop’s Corviknight | Steel Wing | During your opponent’s next turn, this Pokémon takes 60 less damage from attacks (after applying Weakness and Resistance). | 298 | 411 | redução de dano |
| `P / A` | Shelgon | Guard Press | During your opponent’s next turn, this Pokémon takes 30 less damage from attacks (after applying Weakness and Resistance). | 301 | 416 | redução de dano |
| `P / A` | Hop’s Rookidee | Intimidating Stare | During your opponent’s next turn, attacks used by the Defending Pokémon do 20 less damage (before applying Weakness and Resistance). | 307 | 427 | redução de dano |
| `P / A` | Sylveon ex | Magical Charm | During your opponent’s next turn, attacks used by the Defending Pokémon do 100 less damage (before applying Weakness and Resistance). | 316 | 440 | redução de dano |
| `P / A` | Team Rocket's Moltres ex | Flame Screen | During your opponent’s next turn, this Pokémon takes 50 less damage from attacks (after applying Weakness and Resistance). | 407 | 570 | redução de dano |
| `P / A` | Clamperl | Shell Press | During your opponent’s next turn, this Pokémon takes 10 less damage from attacks (after applying Weakness and Resistance). | 415 | 584 | redução de dano |
| `P / A` | Genesect ex | Protect Charge | During your opponent’s next turn, this Pokémon takes 30 less damage from attacks (after applying Weakness and Resistance). | 547 | 780 | redução de dano |
| `P / A` | Sigilyph | Reflect | During your opponent’s next turn, this Pokémon takes 40 less damage from attacks (after applying Weakness and Resistance). | 591 | 849 | redução de dano |
| `P / A` | Klink | Hard Gears | During your opponent’s next turn, this Pokémon takes 10 less damage from attacks (after applying Weakness and Resistance). | 621 | 896 | redução de dano |
| `P / A` | Klang | Hard Gears | During your opponent’s next turn, this Pokémon takes 20 less damage from attacks (after applying Weakness and Resistance). | 622 | 897 | redução de dano |
| `P / A` | Exeggutor | Guard Press | During your opponent’s next turn, this Pokémon takes 30 less damage from attacks (after applying Weakness and Resistance). | 654 | 943 | redução de dano |
| `P / A` | Mega Abomasnow ex | Frost Barrier | During your opponent’s next turn, this Pokémon takes 30 less damage from attacks (after applying Weakness and Resistance). | 723 | 1047 | redução de dano |
| `P / A` | Buneary | Charm | During your opponent’s next turn, attacks used by the Defending Pokémon do 20 less damage (before applying Weakness and Resistance). | 758 | 1095 | redução de dano |
| `P / A` | Pawmi | Growl | During your opponent’s next turn, attacks used by the Defending Pokémon do 30 less damage (before applying Weakness and Resistance). | 809 | 1168 | redução de dano |
| `P / A` | Empoleon ex | Iron Feathers | During your opponent’s next turn, this Pokémon takes 60 less damage from attacks (after applying Weakness and Resistance). | 835 | 1204 | redução de dano |
| `P / A` | Carkol | Guard Press | During your opponent’s next turn, this Pokémon takes 20 less damage from attacks (after applying Weakness and Resistance). | 888 | 1279 | redução de dano |
| `P / A` | Chikorita | Growl | During your opponent’s next turn, attacks used by the Defending Pokémon do 20 less damage (before applying Weakness and Resistance). | 917 | 1322 | redução de dano |
| `P / A` | Registeel ex | Protecting Steel | During your opponent’s next turn, this Pokémon takes 50 less damage from attacks (after applying Weakness and Resistance). | 988 | 1426 | redução de dano |
| `P / A` | Mega Zygarde ex | Gaia Wave | During your opponent’s next turn, this Pokémon takes 30 less damage from attacks (after applying Weakness and Resistance). | 1056 | 1525 | redução de dano |

## Itens/Fósseis — 7 efeitos

| Código | Carta | Efeito | Texto original | `card_id` | `attack_id` | Classificação |
|---|---|---|---|---:|---:|---|
| `I` | Antique Jaw Fossil | Intimidating Jaw | As long as this Pokémon is in the Active Spot, attacks used by your opponent’s Active Pokémon do 30 less damage (before applying Weakness and Resistance). | 1150 | — | redução de dano |
| `I` | Iron Defender | Iron Defender | During your opponent’s next turn, all of your {M} Pokémon take 30 less damage from attacks from your opponent’s Pokémon (after applying Weakness and Resistance). (This includes new Pokémon that come into play.) | 1140 | — | redução de dano |
| `I` | Thick Scale | Thick Scale | The {N} Pokémon this card is attached to takes 50 less damage from attacks from your opponent’s {G}, {R}, {W}, or {L} Pokémon (after applying Weakness and Resistance). | 1179 | — | redução de dano |

## Apoiador — 1 efeito

| Código | Carta | Efeito | Texto original | `card_id` | `attack_id` | Classificação |
|---|---|---|---|---:|---:|---|
| `S` | Acerola's Mischief | Acerola's Mischief | You can use this card only if your opponent has 2 or fewer Prize cards remaining.<br><br>Choose 1 of your Pokémon in play. During your opponent’s next turn, prevent all damage from and effects of attacks done to that Pokémon by your opponent’s Pokémon {ex}. | 1228 | — | prevenção total |

## Estádios — 4 efeitos

| Código | Carta | Efeito | Texto original | `card_id` | `attack_id` | Classificação |
|---|---|---|---|---:|---:|---|
| `ST` | Full Metal Lab | Full Metal Lab | {M} Pokémon (both yours and your opponent’s) take 30 less damage from attacks from the opponent’s Pokémon (after applying Weakness and Resistance). | 1244 | — | redução de dano |
| `ST` | Neutralization Zone | Neutralization Zone | Prevent all damage done to Pokémon that don’t have a Rule Box (both yours and your opponent’s) by attacks from the opponent’s Pokémon {ex} and Pokémon {V}. (Pokémon {ex}, Pokémon {V}, etc. have Rule Boxes.)<br><br>This card can’t be put into your hand or deck from the discard pile. | 1247 | — | prevenção total |
| `ST` | Granite Cave | Granite Cave | Steven’s Pokémon (both yours and your opponent’s) take 30 less damage from attacks from the opponent’s Pokémon (after applying Weakness and Resistance). | 1258 | — | redução de dano |

## Observações de classificação

- **Redução de dano:** o texto reduz uma quantidade de dano, antes ou depois de aplicar Fraqueza e Resistência; isso não é prevenção total.
- **Prevenção total:** o texto impede todo o dano, às vezes condicionado a moeda, atacante, tipo, Rule Box ou posição.
- **Prevenção de contadores:** o `Battle Cage` impede a colocação de contadores de dano por efeitos de ataques e Habilidades, mas declara que o dano de ataques ainda é sofrido.
- **Punk Helmet:** foi incluído no bloco Item/Fóssil por ser um efeito defensivo de retaliação, mas apenas coloca contadores no atacante; não reduz dano e não previne contadores.
- Efeitos que apenas previnem efeitos de ataques, sem prevenir dano (por exemplo, `Antique Cover Fossil`), ficaram fora deste inventário.

