# FC106 : SEQ06: Aruncator T1-C

## Segmento 1: T1C-Aruncator: Alarme

```stl
A(
    O     "E46.6"                 I46.6           -- Sel Comanda Scuturator T1C (Local)
    O     "DB:OPIN".P436         DB81.DBX54.3    -- Comanda Scuturator T1C
)
A     "DB:OPOUT".L026           DB82.DBX3.1     -- L026-T1C - Mod Operare Automat Selectat
=     "Q40.3"                   Q40.3           -- Comanda - Scuturator T1C
=     "DB:OPOUT".L047           DB82.DBX5.6     -- L047-T1C - Scuturator comandat
```

## Segmento 2: T1C-Aruncator: Lipsa Tensiune Alimentare

```stl
AN    "LM2-T1C-F8.1"            I47.6           -- T1C Prezenta Tensiune Alimentare ElectroValva Aruncator
AN    "LIALM".DB202_DBX32_1     DB202.DBX32.1   -- 1;Gen;22:Sistem Oprire de Urgenta T1-C - Declansat;EM;A3;1;M;0;K
=     "LIALM".DB202_DBX74_0     DB202.DBX74.0   -- 1;FLIPPER T1C;Lipsa Tensiune Alimentare Aruncator T1-C;DI;A1;2;M;K
```

## Segmento 3: T1C-Aruncator: TimeOut Deplasare in Pozitia 'Sus'

```stl
A(
    A     "A:LM2-T1C-K56.1"      Q40.2           -- T1C Aruncator ElectroValva 'Ridicare'
    AN    "LM2-T1C-B48.2"        I49.1           -- T1C Aruncator Senzor Proximitete Pozitia 'Sus'
    L     S5T#10S
    SD    T 209
    NOP   0
    NOP   0
    NOP   0
    A     T 209
)
=     "LIALM".DB202_DBX74_1     DB202.DBX74.1   -- 1;FLIPPER T1C;TimeOut Deplasare Aruncator T1-C in pozitia Sus;DI;A1;2;M;0
```

## Segmento 4: T1C-Aruncator: TimeOut Deplasare in Pozitia 'Jos'

```stl
A(
    AN    "A:LM2-T1C-K56.1"      Q40.2           -- T1C Aruncator ElectroValva 'Ridicare'
    AN    "LM2-T1C-B48.1"        I49.0           -- T1C Aruncator Senzor Proximitete Pozitia 'Jos'
    L     S5T#10S
    SD    T 210
    NOP   0
    NOP   0
    NOP   0
    A     T 210
)
AN    "LIALM".DB202_DBX32_1     DB202.DBX32.1   -- 1;Gen;22:Sistem Oprire de Urgenta T1-C - Declansat;EM;A3;1;M;0;K
=     "LIALM".DB202_DBX74_2     DB202.DBX74.2   -- 1;FLIPPER T1C;TimeOut Deplasare Aruncator T1-C in pozitia Jos;DI;A1;2;M;0
```

## Segmento 5: T1C-Aruncator: Memorii Generale

```stl
-- Nessun contenuto visibile nell'immagine sorgente
```

## Segmento 6: T1C-Aruncator: in Pozitia 'Sus'

```stl
A     "LM2-T1C-B48.2"           I49.1           -- T1C Aruncator Senzor Proximitete Pozitia 'Sus'
L     S5T#1S
SD    T 426
NOP   0
NOP   0
NOP   0
A     T 426
=     "M06".UP                  DB106.DBX25.0   -- T1C-Aruncator:Pozitia 'Sus'
```

## Segmento 7: T1C-Aruncator: in Pozitia 'Jos'

```stl
A     "LM2-T1C-B48.1"           I49.0           -- T1C Aruncator Senzor Proximitete Pozitia 'Jos'
L     S5T#1S
SD    T 427
NOP   0
NOP   0
NOP   0
A     T 427
=     "M06".DOWN                DB106.DBX25.1   -- T1C-Aruncator:Pozitia 'Jos'
```

## Segmento 8: T1C-Aruncator: Preset Timeout

```stl
A     "M06".S29                 DB106.DBX9.4    -- T1C-Aruncator:Pas 29
L     S5T#20MS
JC    _000
A     "M06".S18                 DB106.DBX8.1    -- T1C-Aruncator:Pas 18
L     S5T#1S
JC    _000
L     S5T#0MS
_000: NOP   0
T     "M06".Preset              DB106.DBW26     -- Preset Temporizator Secventa
```

## Segmento 9: T1C-Aruncator: S01:Start

```stl
A     "M06".S01                 DB106.DBX6.0    -- T1C-Aruncator:Pas 01
A     "M:T1-C:Auto"             M49.1           -- T1-C: Auto
JNB   _001
L     2
T     "M06".Trs                 DB106.DBW2      -- T1C-Aruncator:Numar Pas Cerut
_001: NOP   0
```

## Segmento 10: T1C-Aruncator: Conditii Start

```stl
A     "M06".DOWN                DB106.DBX25.1   -- T1C-Aruncator:Pozitia 'Jos'
=     "M06".STC                 DB106.DBX25.4   -- T1C-Aruncator:Conditii Start
```

## Segmento 11: T1C-Aruncator: Conditii Start Ciclu

```stl
A     "M06".S02                 DB106.DBX6.1    -- T1C-Aruncator:Pas 02:
A     "M:T1-C:Start:Cycle"      M45.1           -- T1-C: Start:CICLU
A     "M06".STC                 DB106.DBX25.4   -- T1C-Aruncator:Conditii Start
JNB   _002
L     3
T     "M06".Trs                 DB106.DBW2      -- T1C-Aruncator:Numar Pas Cerut
_002: NOP   0
```

## Segmento 12: T1C-Aruncator: S03:Conditii Prezenta

```stl
A     "M06".S03                 DB106.DBX6.2    -- T1C-Aruncator:Pas 03:
A     "M05".PT_END              DB105.DBX23.4   -- T1C-Lant:Prezenta Teava pe Ultima Pozitie Bancal
A     "M06".DOWN                DB106.DBX25.1   -- T1C-Aruncator:Pozitia 'Jos'
A     "M:QUENCH:LOAD T1-C"      M30.1           -- Incarca Cuptor Calitor din T1-C
AN    "M06".STOP                DB106.DBX25.3   -- T1C-Aruncator:Cerere 'Stop' in Mod Automat
A     "M62".Charge_OK           DB162.DBX23.1   -- AUX:Consens pt. Incarcare
A     "M07".S03                 DB107.DBX6.2    -- T1C-Role:Pas 03:
AN    "M07".PT                  DB107.DBX23.3   -- T1C-Role:Prezenta Teava
JNB   _003
L     4
T     "M06".Trs                 DB106.DBW2      -- T1C-Aruncator:Numar Pas Cerut
_003: NOP   0
```

## Segmento 13: T1C-Aruncator: S04:Conditii Abilitare

```stl
A     "M06".S04                 DB106.DBX6.3    -- T1C-Aruncator:Pas 04
JNB   _004
L     7
T     "M06".Trs                 DB106.DBW2      -- T1C-Aruncator:Numar Pas Cerut
_004: NOP   0
```

## Segmento 14: T1C-Aruncator: S07

```stl
A     "M06".S07                 DB106.DBX6.6    -- T1C-Aruncator:Pas 07
JNB   _005
L     10
T     "M06".Trs                 DB106.DBW2      -- T1C-Aruncator:Numar Pas Cerut
_005: NOP   0
```

## Segmento 15: T1C-Aruncator: S10:Comanda 'Ridicare'

```stl
A     "M06".S10                 DB106.DBX7.1    -- T1C-Aruncator:Pas 10
JNB   _006
L     14
T     "M06".Trs                 DB106.DBW2      -- T1C-Aruncator:Numar Pas Cerut
_006: NOP   0
```

## Segmento 16: T1C-Aruncator: S14:Comanda 'Ridicare'

```stl
A     "M06".S14                 DB106.DBX7.5    -- T1C-Aruncator:Pas 14:
A(
    O     "M06".UP               DB106.DBX25.0   -- T1C-Aruncator:Pozitia 'Sus'
    O     "LIALM".DB202_DBX74_1  DB202.DBX74.1   -- 1;FLIPPER T1C;TimeOut Deplasare Aruncator T1-C in pozitia Sus;DI;A1;2;M;0
)
JNB   _007
L     18
T     "M06".Trs                 DB106.DBW2      -- T1C-Aruncator:Numar Pas Cerut
_007: NOP   0
```

## Segmento 17: T1C-Aruncator: S18:Comanda 'Ridicare'

```stl
A     "M06".S18                 DB106.DBX8.1    -- T1C-Aruncator:Pas 18
A     "M07".PT                  DB107.DBX23.3   -- T1C-Role:Prezenta Teava
JNB   _008
L     22
T     "M06".Trs                 DB106.DBW2      -- T1C-Aruncator:Numar Pas Cerut
_008: NOP   0
```

## Segmento 18: T1C-Aruncator: S22:in Pozitia 'Jos'

```stl
A     "M06".S22                 DB106.DBX8.5    -- T1C-Aruncator:Pas 22
A     "M06".DOWN                DB106.DBX25.1   -- T1C-Aruncator:Pozitia 'Jos'
JNB   _009
L     26
T     "M06".Trs                 DB106.DBW2      -- T1C-Aruncator:Numar Pas Cerut
_009: NOP   0
```

## Segmento 19: T1C-Aruncator: S26:in Pozitia 'Jos'

```stl
A     "M06".S26                 DB106.DBX9.1    -- T1C-Aruncator:Pas 26
JNB   _00a
L     3
T     "M06".Trs                 DB106.DBW2      -- T1C-Aruncator:Numar Pas Cerut
_00a: NOP   0
```

## Segmento 20: T1C-Aruncator: S01:Start

```stl
A(
    O     "M06".S29             DB106.DBX9.4    -- T1C-Aruncator:Pas 29
    O     "M06".S32             DB106.DBX9.7    -- T1C-Aruncator:Pas 32
)
AN    "M06".EM                  DB106.DBX25.5   -- T1C-Aruncator:Emergenta
AN    "M:T1-C:Manual"           M47.1           -- T1-C: Manual
JNB   _00b
L     1
T     "M06".Trs                 DB106.DBW2      -- T1C-Aruncator:Numar Pas Cerut
_00b: NOP   0
```

## Segmento 21: T1C-Aruncator: S29:Mod Manual

```stl
A     "M:AUX 22 OK"             M44.1           -- Zona 2:Auxiliar OK
A     "M:T1-C:Manual"           M47.1           -- T1-C: Manual
JNB   _00c
L     29
T     "M06".Trs                 DB106.DBW2      -- T1C-Aruncator:Numar Pas Cerut
_00c: NOP   0
```

## Segmento 22: T1C-Aruncator: Cumulativ Alarme

```stl
ON    "M:CMD INS 2 OK"          M40.1           -- Zona Emergenta 2: Comenzi abilitate
O     "LIALM".DB202_DBX35_0     DB202.DBX35.0   -- 1;Gen;Lipsa Tensiune Alimentare pt. Electrovalvole (PLC);DI;A1;6;M;K
O     "LIALM".DB202_DBX34_0     DB202.DBX34.0   -- 1;Gen;Lipsa Tensiune Alimentare pt. modulele ET-LM2;DI;A1;6;M;K
O     "LIALM".DB202_DBX74_0     DB202.DBX74.0   -- 1;FLIPPER T1C;Lipsa Tensiune Alimentare Aruncator T1-C;DI;A1;2;M;K
O     "LIALM".DB202_DBX33_5     DB202.DBX33.5   -- 1;Gen;Lipsa Tensiune Alimentare pt. modulele ET-TF3;DI;A1;6;M;K
O     "LIALM".DB202_DBX34_0     DB202.DBX34.0   -- 1;Gen;Lipsa Tensiune Alimentare pt. modulele ET-LM2;DI;A1;6;M;K
O     "LIALM".DB202_DBX37_3     DB202.DBX37.3   -- 1;LM2;Lipsa Tensiune Alimentare Intrari Digitale (LM2);DI;A1;6;M;K
O     "LIALM".DB202_DBX37_4     DB202.DBX37.4   -- 1;LM2;Lipsa Tensiune Alimentare Iesiri Digitale (LM2);DI;A1;6;M;K
O     "LIALM".DB202_DBX74_2     DB202.DBX74.2   -- 1;FLIPPER T1C;TimeOut Deplasare Aruncator T1-C in pozitia Jos;DI;A1;2;M;0
O     "LIALM".DB202_DBX74_3     DB202.DBX74.3   -- 1;FLIPPER T1C;Eroare Depozitare Teava pe C.Role;SQ;A1;2;0
=     "M06".EM                  DB106.DBX25.5   -- T1C-Aruncator:Emergenta
```

## Segmento 23: T1C-Aruncator: S32:Emergenta

```stl
A     "M06".EM                  DB106.DBX25.5   -- T1C-Aruncator:Emergenta
JNB   _00d
L     32
T     "M06".Trs                 DB106.DBW2      -- T1C-Aruncator:Numar Pas Cerut
_00d: NOP   0
```

## Segmento 24: T1C-Aruncator: Gestiune Secventiator

```stl
A(
    L     6
    T     "M06".Seq             DB106.DBW0      -- T1C-Aruncator:Sequenza
    SET
    SAVE
    CLR
    A     BR
)
JNB   _00e
CALL  "Secventiator cu 128 Pasi" FC32           -- Secventiator cu 128 Pasi
DBs:= "M06"                   DB106            -- T1C-Arunc
TIM:= T106
_00e: NOP   0
```

## Segmento 25: T1C-Aruncator: Teava nu este in pozitia corecta (eroare depozit)

```stl
A     "M06".TOUT                DB106.DBX24.0   -- T1C-Aruncator:TimeOut
A     "M06".S18                 DB106.DBX8.1    -- T1C-Aruncator:Pas 18
=     "LIALM".DB202_DBX74_3     DB202.DBX74.3   -- 1;FLIPPER T1C;Eroare Depozitare Teava pe C.Role;SQ;A1;2;0
```

## Segmento 26: T1C-Aruncator: Comanda 'Ridicare' in Mod Automat

```stl
O     "M06".S10                 DB106.DBX7.1    -- T1C-Aruncator:Pas 10
O     "M06".S14                 DB106.DBX7.5    -- T1C-Aruncator:Pas 14:
O     "M06".S18                 DB106.DBX8.1    -- T1C-Aruncator:Pas 18
=     "M06".FLIPPER_AUTO        DB106.DBX22.4   -- T1C-Aruncator:Comanda 'Ridicare' in Mod Automat
```

## Segmento 27: T1C-Aruncator: Contactor Comanda 'Ridicare'

```stl
O     "M06".FLIPPER_AUTO        DB106.DBX22.4   -- T1C-Aruncator:Comanda 'Ridicare' in Mod Automat
O
A(
    A     "DB:OPIN".P026        DB81.DBX3.1     -- P026-T1C - Aruncator - Cmd. Sus
    A     "M:CMD 4-MAIN:LM2"    M43.3           -- Comenzi 4 - Pupitru Principal Activat:LM2: T1-C
    O
    A     "LM2-T1C-S44.3"       I45.5           -- T1C Aruncator Comanda 'Ridicare'
    A     "M:CMD 4-LOCAL:LM2"   M42.3           -- Comenzi 4 - Pupitru Local Activat:LM2: T1-C
    O
    A     "A:LM2-T1C-K56.1"     Q40.2           -- T1C Aruncator ElectroValva 'Ridicare'
)
A(
    ON    "DB:OPIN".P027        DB81.DBX3.2     -- P027-T1C - Aruncator - Cmd. Jos
    ON    "M:CMD 4-MAIN:LM2"    M43.3           -- Comenzi 4 - Pupitru Principal Activat:LM2: T1-C
)
A(
    ON    "LM2-T1C-S44.4"       I45.6           -- T1C Aruncator Comanda 'Coborare'
    ON    "M:CMD 4-LOCAL:LM2"   M42.3           -- Comenzi 4 - Pupitru Local Activat:LM2: T1-C
)
A     "M06".S29                 DB106.DBX9.4    -- T1C-Aruncator:Pas 29
=     "A:LM2-T1C-K56.1"         Q40.2           -- T1C Aruncator ElectroValva 'Ridicare'
=     "M06".FU_ON               DB106.DBX24.6   -- T1C-Aruncator:Deplasare 'Ridicare'
```
