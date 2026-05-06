# FC118 : SEQ18: Excentric T5

File Markdown unico ricostruito dai segmenti AWL forniti.

## Segmento 1: T5-Excentric: Resetare Alarme

```awl
A     "M:CLOCK 0.5Hz"                  M3.7        -- FC5:Clock 0.5Hz
R     "LLALM".DB202_DBX126_0            DB202.DBX126.0 -- 4;EXCENTRIC T5;TimeOut Deplasare Inainte Excentric T5;DI;A1;14;M;0;K
R     "LLALM".DB202_DBX126_1            DB202.DBX126.1 -- 4;EXCENTRIC T5;TimeOut Deplasare Inapoi Excentric T5;DI;A1;14;M;0;K
R     "LLALM".DB202_DBX126_2            DB202.DBX126.2 -- 4;EXCENTRIC T5;TimeOut Deplasare Excentric T5 in Pozitie;DI;A1;14;M;0;K
```

## Segmento 2: T5-Excentric: TimeOut Deplasare 'Inainte'

```awl
A(
A     "TF2 T5-K53.4"                   Q172.3      -- T5 Excentric Contactor Deplasare 'Inainte'
AN    "TF2 T5-E102 K6.7no"             I170.3      -- T5 Excentricentric Confirmare Rotire 'Inainte'
O
AN    "TF2 T5-K53.4"                   Q172.3      -- T5 Excentric Contactor Deplasare 'Inainte'
A     "TF2 T5-E102 K6.7no"             I170.3      -- T5 Excentricentric Confirmare Rotire 'Inainte'
AN    "LLALM".DB202_DBX32_4             DB202.DBX32.4 -- 1;Gen;Z5:Sistem Oprire de Urgenta T5-T6 - Declansat;EM;A3;14;M;0;K
)
L     S5T#500MS
SD    T     242
NOP   0
NOP   0
NOP   0
A     T     242
S     "LLALM".DB202_DBX126_0            DB202.DBX126.0 -- 4;EXCENTRIC T5;TimeOut Deplasare Inainte Excentric T5;DI;A1;14;M;0;K
```

## Segmento 3: T5-Excentric: TimeOut Deplasare 'Inapoi'

```awl
A(
A     "TF2 T5-K53.5"                   Q172.4      -- T5 Excentric Contactor Deplasare 'Inapoi'
AN    "TF2 T5-E102 K6.8no"             I170.4      -- T5 Excentricentric Confirmare Rotire 'Inapoi'
O
AN    "TF2 T5-K53.5"                   Q172.4      -- T5 Excentric Contactor Deplasare 'Inapoi'
A     "TF2 T5-E102 K6.8no"             I170.4      -- T5 Excentricentric Confirmare Rotire 'Inapoi'
AN    "LLALM".DB202_DBX32_4             DB202.DBX32.4 -- 1;Gen;Z5:Sistem Oprire de Urgenta T5-T6 - Declansat;EM;A3;14;M;0;K
)
L     S5T#500MS
SD    T     243
NOP   0
NOP   0
NOP   0
A     T     243
S     "LLALM".DB202_DBX126_1            DB202.DBX126.1 -- 4;EXCENTRIC T5;TimeOut Deplasare Inapoi Excentric T5;DI;A1;14;M;0;K
```

## Segmento 4: T5-Excentric: TimeOut Deplasare Excentric in Pozitie

```awl
A(
O     "TF2 T5-K53.4"                   Q172.3      -- T5 Excentric Contactor Deplasare 'Inainte'
O     "TF2 T5-K53.5"                   Q172.4      -- T5 Excentric Contactor Deplasare 'Inapoi'
)
AN    "M18".OS_POSITION                 DB118.DBX22.0 -- T5-Excentric:OS NOTE POSITION
L     S5T#10S
SD    T     244
NOP   0
NOP   0
NOP   0
A     T     244
S     "LLALM".DB202_DBX126_2            DB202.DBX126.2 -- 4;EXCENTRIC T5;TimeOut Deplasare Excentric T5 in Pozitie;DI;A1;14;M;0;K
```

## Segmento 5: T5-Excentric: Disjumctor Termic Motor

```awl
AN    "TF2 T5-E102 F6.1"               I170.2      -- T5 Excentricentric Protectie Termica Motor
AN    "LLALM".DB202_DBX32_4             DB202.DBX32.4 -- 1;Gen;Z5:Sistem Oprire de Urgenta T5-T6 - Declansat;EM;A3;14;M;0;K
=     "LLALM".DB202_DBX126_3            DB202.DBX126.3 -- 4;EXCENTRIC T5;Disjumctor Termic Mot. Excentric T5-Declansat;DI;A1;14;M;K
```

## Segmento 6: T5-Excentric: Alimentare SoftStarter SIKO

```awl
AN    "TF2 T5-E102 Q6.1"               I170.1      -- T5 Excentricentric Disjunctor Alimentare SoftStarter SIKO
AN    "LLALM".DB202_DBX32_4             DB202.DBX32.4 -- 1;Gen;Z5:Sistem Oprire de Urgenta T5-T6 - Declansat;EM;A3;14;M;0;K
=     "LLALM".DB202_DBX126_4            DB202.DBX126.4 -- 4;EXCENTRIC T5;Alim. SoftStarter SIKO Excentric T5-Decuplat;DI;A1;14;M;K
```

## Segmento 7: T5-Excentric: Alimentare Frana Motor

```awl
AN    "TF2 T5-E102 F6.3"               I170.7      -- T5 Excentricentric Prezenta Tensiune Alimentare Frana
AN    "LLALM".DB202_DBX32_4             DB202.DBX32.4 -- 1;Gen;Z5:Sistem Oprire de Urgenta T5-T6 - Declansat;EM;A3;14;M;0;K
=     "LLALM".DB202_DBX126_5            DB202.DBX126.5 -- 4;EXCENTRIC T5;Alim. Frana Mot. Excentric T5 - Decuplat;DI;A1;14;M;K
```

## Segmento 8: T5-Excentric: Lipsa Tensiune Comanda

```awl
AN    "TF2 T5-E102 F6.6"               I170.0      -- T5 Excentricentric Tensiune Comanda
AN    "LLALM".DB202_DBX32_4             DB202.DBX32.4 -- 1;Gen;Z5:Sistem Oprire de Urgenta T5-T6 - Declansat;EM;A3;14;M;0;K
=     "LLALM".DB202_DBX126_6            DB202.DBX126.6 -- 4;EXCENTRIC T5;Lipsa Tensiune de Comanda Excentric T5;DI;A1;14;M;K
```

## Segmento 9: T5-Excentric: Avarie SoftStarter

```awl
AN    "TF2 T5-E102 G6.1'OK'"           I170.5      -- T5 Excentricentric SoftStarter SIKO 'OK'
AN    "LLALM".DB202_DBX32_4             DB202.DBX32.4 -- 1;Gen;Z5:Sistem Oprire de Urgenta T5-T6 - Declansat;EM;A3;14;M;0;K
=     "LLALM".DB202_DBX126_7            DB202.DBX126.7 -- 4;EXCENTRIC T5;SoftStarter SIKO Excentric T5 - Avarie;DI;A1;14;M;0;K
```

## Segmento 10: T5-Excentric: Eroare Depozitare Teava

```awl
A     "M18".S22                        DB118.DBX8.5 -- T5-Excentric:Pas 22
A     "M18".EX_INITIAL                 DB118.DBX22.5 -- T5-Excentric:Pozitia 'Initial'
=     "LLALM".DB202_DBX127_0            DB202.DBX127.0 -- 4;EXCENTRIC T5;Eroare Depozitare Teava pe Pat Racire T5;SQ;A1;14;O
```

## Segmento 11: T5-Excentric: Memorii Generale

```awl
// Segmento vuoto nel sorgente fornito.
```

## Segmento 12: T5-Excentric: AUX_OS_POSITION

```awl
A(
O     "LM5-T5-B48.3"                   I97.2       -- T5 Excentricentric Senzor Pozitie 'Initial'
O     "LM5-T5-B48.4"                   I97.3       -- T5 Excentricentric Senzor Pozitie 'Vertical'
)
FP    "M18".AUX_OS_POSITION             DB118.DBX22.1 -- T5-Excentric:T5-Excentric OS NOTE POSITION
=     "M18".OS_POSITION                 DB118.DBX22.0 -- T5-Excentric:OS NOTE POSITION
```

## Segmento 13: T5-Excentric: In Pozitia 'Vertical'

```awl
A     "LM5-T5-B48.4"                   I97.3       -- T5 Excentricentric Senzor Pozitie 'Vertical'
=     "M18".EX_VERT                    DB118.DBX22.2 -- T5-Excentric:Pozitie 'Vertical'
```

## Segmento 14: T5-Excentric: In Pozitia 'Initial'

```awl
A     "LM5-T5-B48.3"                   I97.2       -- T5 Excentricentric Senzor Pozitie 'Initial'
=     "M18".EX_INITIAL                 DB118.DBX22.5 -- T5-Excentric:Pozitia 'Initial'
```

## Segmento 15: T5-Excentric: S01:Start

```awl
A     "M18".S01                        DB118.DBX6.0 -- T5-Excentric:Pas 01
A     "M:T5:Auto"                      M49.5       -- T5: Auto
JNB   _001
L     2
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_001: NOP   0
```

## Segmento 16: T5-Excentric: Conditii Start

```awl
O     "M18".EX_INITIAL                 DB118.DBX22.5 -- T5-Excentric:Pozitia 'Initial'
O     "M18".EX_VERT                    DB118.DBX22.2 -- T5-Excentric:Pozitie 'Vertical'
=     "M18".STC                        DB118.DBX25.4 -- T5-Excentric:Conditii Start
```

## Segmento 17: T5-Excentric: S02:Conditii Start Ciclu

```awl
A     "M18".S02                        DB118.DBX6.1 -- T5-Excentric:Pas 02:
A     "M:T5:Start:Cycle"               M45.5       -- T5: Start:CICLU
A     "M18".STC                        DB118.DBX25.4 -- T5-Excentric:Conditii Start
JNB   _002
L     3
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_002: NOP   0
```

## Segmento 18: T5-Excentric: Conditii Start

```awl
A(
O     "M19".S03                        DB119.DBX6.2 -- T5-Lant:Pas 03:
O     "M19".S22                        DB119.DBX8.5 -- T5-Lant:Pas 22
)
A     "M19".STEP                       DB119.DBX22.6 -- T5-Lant:Lant in 'Pas'
AN    "M19".PT_Start                   DB119.DBX23.3 -- T5-Lant:Prezenta Teava pe Pozitia Start lant T5
A     "M69".Charge_OK                  DB169.DBX23.1 -- AUX:Consens pt. Incarcare
ON    "M19".C_F                        DB119.DBX25.7 -- T5-Lant:Cycle Fast 1 Pipe
=     #AUXB                            #AUXB
```

## Segmento 19: T5-Excentric: S03:Conditii Prezenta

```awl
A(
A(
A     "M17".TUBE_HEADING               DB117.DBX22.5 -- T5.1-Role:Teava Pozitionata
L     S5T#1S
SD    T     261
NOP   0
NOP   0
NOP   0
A     T     261
)
A     "M18".EX_INITIAL                 DB118.DBX22.5 -- T5-Excentric:Pozitia 'Initial'
A     "M17".PT_OK                      DB117.DBX22.6 -- T5.1-Role:PT OK
A     "M17".S22                        DB117.DBX8.5 -- T5.1-Role:Pas 22
AN    "M17".FW_ON                      DB117.DBX24.6 -- T5.1-Role:Rotire 'Inainte'
A     "M67".Discharge_OK               DB167.DBX23.2 -- AUX:Consens pt. Descarcare
A     #AUXB                            #AUXB
O     "M18".EX_VERT                    DB118.DBX22.2 -- T5-Excentric:Pozitie 'Vertical'
)
A     "M194.6"                         M194.6      -- Lant T5 a facut un pas
A     "M18".S03                        DB118.DBX6.2 -- T5-Excentric:Pas 03:
JNB   _003
L     4
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_003: NOP   0
```

## Segmento 20: T5-Excentric: S04:Conditii Abilitare

```awl
A     "M18".S04                        DB118.DBX6.3 -- T5-Excentric:Pas 04
JNB   _004
L     7
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_004: NOP   0
```

## Segmento 21: T5-Excentric: S07:Conditii Start

```awl
A     "M18".S07                        DB118.DBX6.6 -- T5-Excentric:Pas 07
=     L     1.0
A     L     1.0
A     "M18".EX_INITIAL                 DB118.DBX22.5 -- T5-Excentric:Pozitia 'Initial'
JNB   _005
L     10
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_005: NOP   0
A     L     1.0
A     "M18".EX_VERT                    DB118.DBX22.2 -- T5-Excentric:Pozitie 'Vertical'
JNB   _006
L     18
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_006: NOP   0
```

## Segmento 22: T5-Excentric: S10:Comanda Deplasare 'Inainte'

```awl
A     "M18".S10                        DB118.DBX7.1 -- T5-Excentric:Pas 10
A     "M18".EX_VERT                    DB118.DBX22.2 -- T5-Excentric:Pozitie 'Vertical'
JNB   _007
L     14
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_007: NOP   0
```

## Segmento 23: T5-Excentric: S14:Comanda Deplasare 'Inainte'

```awl
A     "M18".S14                        DB118.DBX7.5 -- T5-Excentric:Pas 14:
=     L     1.0
A     L     1.0
A(
AN    "M19".S03                        DB119.DBX6.2 -- T5-Lant:Pas 03:
AN    "M19".S22                        DB119.DBX8.5 -- T5-Lant:Pas 22
ON    "M19".STEP                       DB119.DBX22.6 -- T5-Lant:Lant in 'Pas'
O     "M19".PT_Start                   DB119.DBX23.3 -- T5-Lant:Prezenta Teava pe Pozitia Start lant T5
ON    "M69".Charge_OK                  DB169.DBX23.1 -- AUX:Consens pt. Incarcare
)
JNB   _008
L     18
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_008: NOP   0
A     L     1.0
BLD   102
R     "M194.6"                         M194.6      -- Lant T5 a facut un pas
```

## Segmento 24: T5-Excentric: S14:Comanda Deplasare 'Inainte'

```awl
A(
O     "M18".S14                        DB118.DBX7.5 -- T5-Excentric:Pas 14:
O(
A     "M18".S18                        DB118.DBX8.1 -- T5-Excentric:Pas 18
AN    "M18".FW_ON                      DB118.DBX22.7 -- T5-Excentric:Comand FW
)
)
A(
O     "M19".S03                        DB119.DBX6.2 -- T5-Lant:Pas 03:
O     "M19".S22                        DB119.DBX8.5 -- T5-Lant:Pas 22
)
A     "M19".STEP                       DB119.DBX22.6 -- T5-Lant:Lant in 'Pas'
AN    "M19".PT_Start                   DB119.DBX23.3 -- T5-Lant:Prezenta Teava pe Pozitia Start lant T5
A     "M69".Charge_OK                  DB169.DBX23.1 -- AUX:Consens pt. Incarcare
AN    "M136.1"                         M136.1      -- Interblocaj excentric lant T5
JNB   _009
L     22
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_009: NOP   0
```

## Segmento 25: T5-Excentric: S22:Comanda Deplasare 'Inainte'

```awl
A     "M18".S22                        DB118.DBX8.5 -- T5-Excentric:Pas 22
A(
O     "M19".PT_Start                   DB119.DBX23.3 -- T5-Lant:Prezenta Teava pe Pozitia Start lant T5
O     "M18".EX_INITIAL                 DB118.DBX22.5 -- T5-Excentric:Pozitia 'Initial'
)
JNB   _00a
L     26
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_00a: NOP   0
```

## Segmento 26: T5-Excentric: S26:Comanda Deplasare 'Inainte'

```awl
A     "M18".S26                        DB118.DBX9.1 -- T5-Excentric:Pas 26
A     "M18".EX_INITIAL                 DB118.DBX22.5 -- T5-Excentric:Pozitia 'Initial'
JNB   _00b
L     30
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_00b: NOP   0
```

## Segmento 27: T5-Excentric: S30:Sfarsit

```awl
A     "M18".S30                        DB118.DBX9.5 -- T5-Excentric:Pas 30
JNB   _00c
L     3
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_00c: NOP   0
```

## Segmento 28: T5-Excentric: S01:Start

```awl
A(
O     "M18".S29                        DB118.DBX9.4 -- T5-Excentric:Pas 29
O     "M18".S32                        DB118.DBX9.7 -- T5-Excentric:Pas 32
)
AN    "M18".EM                         DB118.DBX25.5 -- T5-Excentric:Emergenta
AN    "M:T5:Manual"                    M47.5       -- T5: Manual
JNB   _00d
L     1
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_00d: NOP   0
```

## Segmento 29: T5-Excentric: S29:Mod Manual

```awl
A     "M:AUX Z5 OK"                    M44.4       -- Zona 5:Auxiliar OK
A     "M:T5:Manual"                    M47.5       -- T5: Manual
JNB   _00e
L     29
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_00e: NOP   0
```

## Segmento 30: T5-Excentric: Cumulativ Alarme

```awl
ON    "M:CMD INS 5 OK"                 M40.4       -- Zona Emergenta 5: Comenzi Abilitate
O     "LLALM".DB202_DBX127_0            DB202.DBX127.0 -- 4;EXCENTRIC T5;Eroare Depozitare Teava pe Pat Racire T5;SQ;A1;14;O
O     "LLALM".DB202_DBX126_0            DB202.DBX126.0 -- 4;EXCENTRIC T5;TimeOut Deplasare Inainte Excentric T5;DI;A1;14;M;0;K
O     "LLALM".DB202_DBX126_1            DB202.DBX126.1 -- 4;EXCENTRIC T5;TimeOut Deplasare Inapoi Excentric T5;DI;A1;14;M;0;K
O     "LLALM".DB202_DBX126_2            DB202.DBX126.2 -- 4;EXCENTRIC T5;TimeOut Deplasare Excentric T5 in Pozitie;DI;A1;14;M;0;K
O     "LLALM".DB202_DBX126_3            DB202.DBX126.3 -- 4;EXCENTRIC T5;Disjumctor Termic Mot. Excentric T5-Declansat;DI;A1;14;M;K
O     "LLALM".DB202_DBX126_4            DB202.DBX126.4 -- 4;EXCENTRIC T5;Alim. SoftStarter SIKO Excentric T5-Decuplat;DI;A1;14;M;K
O     "LLALM".DB202_DBX126_5            DB202.DBX126.5 -- 4;EXCENTRIC T5;Alim. Frana Mot. Excentric T5 - Decuplat;DI;A1;14;M;K
O     "LLALM".DB202_DBX126_6            DB202.DBX126.6 -- 4;EXCENTRIC T5;Lipsa Tensiune de Comanda Excentric T5;DI;A1;14;M;K
O     "LLALM".DB202_DBX126_7            DB202.DBX126.7 -- 4;EXCENTRIC T5;SoftStarter SIKO Excentric T5 - Avarie;DI;A1;14;M;0;K
=     "M18".EM                         DB118.DBX25.5 -- T5-Excentric:Emergenta
```

## Segmento 31: T5-Excentric: S32:Emergenta

```awl
A     "M18".EM                         DB118.DBX25.5 -- T5-Excentric:Emergenta
JNB   _00f
L     32
T     "M18".Trs                        DB118.DBW2  -- T5-Excentric:Numar Pas Cerut
_00f: NOP   0
```

## Segmento 32: T5-Excentric: Gestiune Secventiator

```awl
A(
L     18
T     "M18".Seq                        DB118.DBW0  -- T5-Excentric:Secventa
SET
SAVE
CLR
A     BR
)
JNB   _010
CALL  "Secventiator cu 128 Pasi"        FC32        -- Secventiator cu 128 Pasi
      DBs := "M18"                     DB118       -- T5-Excentric
      TIM := T118
_010: NOP   0
```

## Segmento 33: T5-Excentric: Gestiune Iesiri

```awl
// Segmento vuoto nel sorgente fornito.
```

## Segmento 34: T5-Excentric: Comanda Rotire 'Inainte' in Mod Automat

```awl
O     "M18".S10                        DB118.DBX7.1 -- T5-Excentric:Pas 10
O     "M18".S14                        DB118.DBX7.5 -- T5-Excentric:Pas 14:
O     "M18".S22                        DB118.DBX8.5 -- T5-Excentric:Pas 22
O     "M18".S26                        DB118.DBX9.1 -- T5-Excentric:Pas 26
=     "M18".EXC_AUTO_FW                DB118.DBX22.4 -- T5-Excentric:Excentric Rotire 'Inainte' in Mod Automat
```

## Segmento 35: T5-Excentric: Comanda Rotire 'Inainte' in Mod Manual

```awl
A(
A     "DB:OPIN".P071                   DB81.DBX8.6 -- P071-T5 - Excentric - Cmd. Pas
FP    "M:AUXOS25"                      M278.0
AN    "DB:OPIN".P072                   DB81.DBX8.7 -- P072-T5 - Excentric - Cmd. Inapoi
A     "M:CMD 6-MAIN:LM5"               M43.5       -- Comenzi 6 - Pupitru Principal Activat:LM5: T5-T6
O(
A     "LM5 T5-S44.5"                   I93.4       -- T5 Excentricentric Comanda 'Inainte'
FP    "M:AUXOS26"                      M278.1
AN    "LM5 T5-S44.6"                   I93.5       -- T5 Excentricentric Comanda 'Inapoi'
A     "M:CMD 6-LOCAL:LM5"              M42.5       -- Comenzi 6 - Pupitru Local Activat:LM5: T5-T6
)
O
A     "M18".FW_MANUAL                  DB118.DBX23.1 -- T5-Excentric:Rotire 'Inainte' in Mod Automat (DISABLE OS STEP)
A     "TF2 T5-K53.4"                   Q172.3      -- T5 Excentric Contactor Deplasare 'Inainte'
)
A(
O     "LM5 T5-S44.5"                   I93.4       -- T5 Excentricentric Comanda 'Inainte'
ON    "M:CMD 6-LOCAL:LM5"              M42.5       -- Comenzi 6 - Pupitru Local Activat:LM5: T5-T6
)
A     "M18".S29                        DB118.DBX9.4 -- T5-Excentric:Pas 29
AN    "M18".OS_POSITION                DB118.DBX22.0 -- T5-Excentric:OS NOTE POSITION
=     "M18".FW_MANUAL                  DB118.DBX23.1 -- T5-Excentric:Rotire 'Inainte' in Mod Automat (DISABLE OS STEP)
```

## Segmento 36: T5-Excentric: Comanda Rotire 'Inainte'

```awl
A(
O     "M18".EXC_AUTO_FW                DB118.DBX22.4 -- T5-Excentric:Excentric Rotire 'Inainte' in Mod Automat
O(
A     "DB:OPIN".P069                   DB81.DBX8.4 -- P069-T5 - Excentric - Cmd. Inainte
AN    "DB:OPIN".P072                   DB81.DBX8.7 -- P072-T5 - Excentric - Cmd. Inapoi
A     "M:CMD 6-MAIN:LM5"               M43.5       -- Comenzi 6 - Pupitru Principal Activat:LM5: T5-T6
O     "M18".FW_MANUAL                  DB118.DBX23.1 -- T5-Excentric:Rotire 'Inainte' in Mod Automat (DISABLE OS STEP)
)
A(
OM    "M14".PT_OUT                     DB114.DBX23.4 -- T4 Z-Role:PT OUT
OM    "M18".EX_INITIAL                 DB118.DBX22.5 -- T5-Excentric:Pozitia 'Initial'
)
A     "M18".S29                        DB118.DBX9.4 -- T5-Excentric:Pas 29
)
AN    "M18".BW_ON                      DB118.DBX23.0 -- T5-Excentric:Comand BW
=     L     1.0
A     L     1.0
BLD   102
=     "TF2 T5-K53.4"                   Q172.3      -- T5 Excentric Contactor Deplasare 'Inainte'
A     L     1.0
BLD   102
=     "DB:OPOUT".L103                  DB82.DBX12.6 -- L103-T5 - Excentric - Rotire Inainte
A     L     1.0
L     S5T#1S
SF    T     66
NOP   0
NOP   0
NOP   0
A     T     66
=     "M18".FW_ON                      DB118.DBX22.7 -- T5-Excentric:Comand FW
```

## Segmento 37: T5-Excentric: Comanda Rotire 'Inapoi'

```awl
A(
A     "DB:OPIN".P072                   DB81.DBX8.7 -- P072-T5 - Excentric - Cmd. Inapoi
AN    "DB:OPIN".P069                   DB81.DBX8.4 -- P069-T5 - Excentric - Cmd. Inainte
A     "M:CMD 6-MAIN:LM5"               M43.5       -- Comenzi 6 - Pupitru Principal Activat:LM5: T5-T6
O
A     "LM5 T5-S44.6"                   I93.5       -- T5 Excentricentric Comanda 'Inapoi'
AN    "LM5 T5-S44.5"                   I93.4       -- T5 Excentricentric Comanda 'Inainte'
A     "M:CMD 6-LOCAL:LM5"              M42.5       -- Comenzi 6 - Pupitru Local Activat:LM5: T5-T6
)
A     "M18".S29                        DB118.DBX9.4 -- T5-Excentric:Pas 29
AN    "M17".PT                         DB117.DBX23.3 -- T5.1-Role:Prezenta Teava
AN    "M18".FW_ON                      DB118.DBX22.7 -- T5-Excentric:Comand FW
=     L     1.0
A     L     1.0
BLD   102
=     "TF2 T5-K53.5"                   Q172.4      -- T5 Excentric Contactor Deplasare 'Inapoi'
A     L     1.0
BLD   102
=     "DB:OPOUT".L123                  DB82.DBX15.2 -- L123-T5 - Excentric - Rotire Inapoi
A     L     1.0
L     S5T#1S
SF    T     69
NOP   0
NOP   0
NOP   0
A     T     69
=     "M18".BW_ON                      DB118.DBX23.0 -- T5-Excentric:Comand BW
```

## Segmento 38: T5-Excentric: Comanda 'Start' SoftStarter SIKO

```awl
A(
O     "TF2 T5-K53.4"                   Q172.3      -- T5 Excentric Contactor Deplasare 'Inainte'
O     "TF2 T5-K53.5"                   Q172.4      -- T5 Excentric Contactor Deplasare 'Inapoi'
)
L     S5T#1S
SF    T     735
NOP   0
NOP   0
NOP   0
A     T     735
=     "TF2 T5-K53.6"                   Q172.5      -- T5 Excentric Contactor SoftStarter SIKO 'Start'
```
