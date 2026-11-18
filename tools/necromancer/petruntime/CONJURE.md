# Universal Conjure: approved design

Available to all classes.
One active conjured pet per character.
Separate from the Necromancer raised army.
300-second cooldown.
Conjured pet XP and level survive logout and safe dismissal.
Combat death permanently destroys that companion.
Conjured pets start at level 1, capped by owner level.

| Unlock | Pet |
| --- | --- |
| 1 | Spectral Wolf |
| 10 | Venom Scorpion |
| 20 | Fire Elemental |
| 30 | Minotaur Guardian |
| 40 | Shadow Wraith |
| 60 | Ancient Dragon |

Scorpion: 10% poison chance on hit.
Fire Elemental: 15% additional fire damage chance.
Minotaur: 10% stun chance.
Shadow Wraith: 20% drain mana chance, three-second internal cooldown.
Drain 10% of enemy maximum MP, limited to available MP.
Split drained mana equally between owner and pet, respecting caps.
Dragon: 15% breath attack chance.

Implementation and native validation pending.
Necromancer rebirth skill remains undecided.

## Round 75B foundation

Dedicated atomic native player-save record.
Independent of the Necromancer roster and class identity.
Cumulative leveling threshold: 100 * (level - 1)^2.
XP can bank at the owner level cap.
One stored companion. Safe dismissal retains its record.
Releasing a dismissed companion removes it permanently.
Cooldown applies to summon and manual recall.
Species stats and growth are initial private balance values.
Native command dispatch and combat integration remain pending.
