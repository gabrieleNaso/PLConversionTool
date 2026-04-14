# FC102 : SEQ02: Aruncator T1-A

## Segmento 1: T1A-Aruncator: Scuturator

```awl
A(

O "E26.7" I26.7 -- Buton scuturator T1A

O "DB:OPIN".P437 DB81.DBX54.4 -- Comanda Scuturator T1A

O "T779" T779 -- Comanda scuturator

)

A "M:T1-A:auto" M49.0 -- T1-A: Auto

= "A24.3" Q24.3 -- Comanda scuturator T1A

= "DB:OPOUT".L045 DB82.DBX5.4 -- L045-T1A - Scuturator comandat
```

## Segmento 2: T1A-Aruncator: Lipsa Tensiune Alimentare

```awl
AN "LM1 T1A-F8.1" I25.0 -- T1A Prezenta Tensiune Alimentare ElectroValva Aruncator

AN "LLALM".DB202_DBX32_0 DB202.DBX32.0 -- 1;Gen;Z1:Sistem Oprire de Urgenta T1-A - Declansat;EM;A3;1;M;0;K

= "LLALM".DB202_DBX62_0 DB202.DBX62.0 -- 1;FLIPPER T1A;Lipsa Tensiune Alimentare Aruncator T1-A;DI;A1;1;M;K
```

## Segmento 3: T1A-Aruncator: TimeOut Deplasare in Pozitia 'Sus'

```awl
A "A:LM1 T1A-K56.1" Q24.0 -- T1A Aruncator ElectroValva ''Ridicare''

AN "LM1 T1A-B48.2" I30.1 -- T1A Aruncator Senzor Proximitate Pozitia 'Sus'

L S5T#10S

SD T 50

NOP 0

NOP 0

NOP 0

A T 50

= "LLALM".DB202_DBX62_1 DB202.DBX62.1 -- 1;FLIPPER T1A;TimeOut Deplasare Aruncator T1-A in pozitia Sus;DI;A1;1;M;0
```

## Segmento 4: T1A-Aruncator: TimeOut Deplasare in Pozitia 'Jos'

```awl
A(

AN "A:LM1 T1A-K56.1" Q24.0 -- T1A Aruncator ElectroValva ''Ridicare''

AN "LM1 T1A-B48.1" I30.0 -- T1A Aruncator Senzor Proximitate Pozitia 'Jos'

L S5T#10S

SD T 51

NOP 0

NOP 0

NOP 0

A T 51

)

AN "LLALM".DB202_DBX32_0 DB202.DBX32.0 -- 1;Gen;Z1:Sistem Oprire de Urgenta T1-A - Declansat;EM;A3;1;M;0;K

= "LLALM".DB202_DBX62_2 DB202.DBX62.2 -- 1;FLIPPER T1A;TimeOut Deplasare Aruncator T1-A in pozitia Jos;DI;A1;1;M;0
```

## Segmento 5: T1A-Aruncator: Memorii Generale

```awl
A(

AN "M01".PT_END DB101.DBX23.4 -- T1A-Lant:Prezenta Teava pe Ultima Pozitie Bancal

L S5T#2S

SD T 780

NOP 0

NOP 0

NOP 0

A T 780

)

A "M:AUX CLOCK 0.5Hz" M4.7 -- FC5:Aux Clock 0.5Hz

L S5T#1S300MS

SE "T779" T779 -- Comanda scuturator

NOP 0

NOP 0

NOP 0

NOP 0
```

## Segmento 6: T1A-Aruncator: Aruncator in Pozitia 'Sus'

```awl
A "LM1 T1A-B48.2" I30.1 -- T1A Aruncator Senzor Proximitate Pozitia 'Sus'

L S5T#1S

SD T 418

NOP 0

NOP 0

NOP 0

A T 418

= "M02".UP DB102.DBX25.0 -- T1A-Aruncator:Pozitia 'Sus'
```

## Segmento 7: T1A-Aruncator: Aruncator in Pozitia 'Jos'

```awl
A "LM1 T1A-B48.1" I30.0 -- T1A Aruncator Senzor Proximitate Pozitia 'Jos'

L S5T#1S

SD T 419

NOP 0

NOP 0

NOP 0

A T 419

= "M02".DOWN DB102.DBX25.1 -- T1A-Aruncator:Pozitia 'Jos'
```

## Segmento 8: T1A-Aruncator: Preset Timeout

```awl
A "M02".S29 DB102.DBX9.4 -- T1A-Aruncator:Pas 29

L S5T#0MS

JC _000

A "M02".S18 DB102.DBX8.1 -- T1A-Aruncator:Pas 18

L S5T#10S

JC _000

L S5T#0MS

_000: NOP 0

T "M02".Preset DB102.DBW26 -- Preset Temporizator Secventa
```

## Segmento 9: T1A-Aruncator: S01:Start

```awl
A "M02".S01 DB102.DBX6.0 -- T1A-Aruncator:Pas 01

A "M:T1-A:Auto" M49.0 -- T1-A: Auto

JNB _001

L 2

T "M02".Trs DB102.DBW2 -- T1A-Aruncator:Numar Pas Cerut

_001: NOP 0
```

## Segmento 10: T1A-Aruncator: Conditii Start

```awl
A "M02".DOWN DB102.DBX25.1 -- T1A-Aruncator:Pozitia 'Jos'

= "M02".STC DB102.DBX25.4 -- T1A-Aruncator:Conditii Start
```

## Segmento 11: T1A-Aruncator: S02:Conditii Start Ciclu

```awl
A "M02".S02 DB102.DBX6.1 -- T1A-Aruncator:Pas 02:

A "M:T1-A:Start:Cycle" M45.0 -- T1-A: Start:CICLU

A "M02".STC DB102.DBX25.4 -- T1A-Aruncator:Conditii Start

JNB _002

L 3

T "M02".Trs DB102.DBW2 -- T1A-Aruncator:Numar Pas Cerut

_002: NOP 0
```

## Segmento 12: T1A-Aruncator: S03:Conditii Prezenta

```awl
A "M02".S03 DB102.DBX6.2 -- T1A-Aruncator:Pas 03:

A "M01".PT_END DB101.DBX23.4 -- T1A-Lant:Prezenta Teava pe Ultima Pozitie Bancal

A "M02".DOWN DB102.DBX25.1 -- T1A-Aruncator:Pozitia 'Jos'

A "M:QUENCH:LOAD T1-A" M30.0 -- Incarca Cuptor Calitor din T1-A

AN "M02".STOP DB102.DBX25.3 -- T1A-Aruncator:Cerere 'Stop' in Mod Automat

A "M61".Charge_OK DB161.DBX23.1 -- AUX:Consens pt. Incarcare

A "M03".S03 DB103.DBX6.2 -- T1A-Role:Pas 03:

AN "M03".PT DB103.DBX23.3 -- T1A-Role:Prezenta Teava

JNB _003

L 4

T "M02".Trs DB102.DBW2 -- T1A-Aruncator:Numar Pas Cerut

_003: NOP 0
```

## Segmento 13: T1A-Aruncator: S04:Conditii Abilitare

```awl
A "M02".S04 DB102.DBX6.3 -- T1A-Aruncator:Pas 04

A(

O "DB13:RX-Q".IN01_B03 DB13.DBX0.3 -- Bit recirculare teava intrare - Stop aruncator

ON "DB13:RX-Q".IN01_B04 DB13.DBX0.4 -- Buton OP recirculare teava

O "DB13:RX-Q".IN01_B05 DB13.DBX0.5 -- Bit recirculare teava - Primul ciclu

)

JNB _004

L 7

T "M02".Trs DB102.DBW2 -- T1A-Aruncator:Numar Pas Cerut

_004: NOP 0
```

## Segmento 14: T1A-Aruncator: S07:

```awl
A "M02".S07 DB102.DBX6.6 -- T1A-Aruncator:Pas 07

JNB _005

L 10

T "M02".Trs DB102.DBW2 -- T1A-Aruncator:Numar Pas Cerut

_005: NOP 0
```

## Segmento 15: T1A-Aruncator: S10:Aruncator Comanda 'Ridicare'

```awl
A "M02".S10 DB102.DBX7.1 -- T1A-Aruncator:Pas 10

JNB _006

L 14

T "M02".Trs DB102.DBW2 -- T1A-Aruncator:Numar Pas Cerut

_006: NOP 0
```

## Segmento 16: T1A-Aruncator: S14:Aruncator Comanda 'Ridicare'

```awl
A "M02".S14 DB102.DBX7.5 -- T1A-Aruncator:Pas 14:

A(

O "M02".UP DB102.DBX25.0 -- T1A-Aruncator:Pozitia 'Sus'

O "LLALM".DB202_DBX62_1 DB202.DBX62.1 -- 1;FLIPPER T1A;TimeOut Deplasare Aruncator T1-A in pozitia Sus;DI;A1;1;M;0

)

JNB _007

L 18

T "M02".Trs DB102.DBW2 -- T1A-Aruncator:Numar Pas Cerut

_007: NOP 0
```

## Segmento 17: T1A-Aruncator: S18:Aruncator Comanda 'Ridicare'

```awl
A "M02".S18 DB102.DBX8.1 -- T1A-Aruncator:Pas 18

A "M03".PT DB103.DBX23.3 -- T1A-Role:Prezenta Teava

JNB _008

L 22

T "M02".Trs DB102.DBW2 -- T1A-Aruncator:Numar Pas Cerut

_008: NOP 0
```

## Segmento 18: T1A-Aruncator: S22:Aruncator in Pozitia 'Jos'

```awl
A "M02".S22 DB102.DBX8.5 -- T1A-Aruncator:Pas 22

A "M02".DOWN DB102.DBX25.1 -- T1A-Aruncator:Pozitia 'Jos'

JNB _009

L 26

T "M02".Trs DB102.DBW2 -- T1A-Aruncator:Numar Pas Cerut

_009: NOP 0
```

## Segmento 19: T1A-Aruncator: S26:Aruncator in Pozitia 'Jos'

```awl
A "M02".S26 DB102.DBX9.1 -- T1A-Aruncator:Pas 26

JNB _00a

L 3

T "M02".Trs DB102.DBW2 -- T1A-Aruncator:Numar Pas Cerut

_00a: NOP 0
```

## Segmento 20: T1A-Aruncator: S01:Start

```awl
A(

O "M02".S29 DB102.DBX9.4 -- T1A-Aruncator:Pas 29

O "M02".S32 DB102.DBX9.7 -- T1A-Aruncator:Pas 32

)

AN "M02".EM DB102.DBX25.5 -- T1A-Aruncator:Emergenta

AN "M:T1-A:Manual" M47.0 -- T1-A: Manual

JNB _00b

L 1

T "M02".Trs DB102.DBW2 -- T1A-Aruncator:Numar Pas Cerut

_00b: NOP 0
```

## Segmento 21: T1A-Aruncator: S29:Mod Manual

```awl
A "M:AUX Z1 OK" M44.0 -- Zona 1:Auxiliar OK

A "M:T1-A:Manual" M47.0 -- T1-A: Manual

JNB _00c

L 29

T "M02".Trs DB102.DBW2 -- T1A-Aruncator:Numar Pas Cerut

_00c: NOP 0
```

## Segmento 22: T1A-Aruncator: Cumulativ Alarme

```awl
ON "M:CMD INS 1 OK" M40.0 -- Zona Emergenta 1: Comenzi Abilitate

O "LLALM".DB202_DBX35_0 DB202.DBX35.0 -- 1;Gen;Lipsa Tensiune Alimentare pt. Electrovalvole (PLC);DI;A1;6;M;K

O "LLALM".DB202_DBX35_1 DB202.DBX35.1 -- 1;Gen;Lipsa Tensiune Alimentare pt. Electrovalvole (LM1);DI;A1;6;M;K

O "LLALM".DB202_DBX62_0 DB202.DBX62.0 -- 1;FLIPPER T1A;Lipsa Tensiune Alimentare Aruncator T1-A;DI;A1;1;M;K

O "LLALM".DB202_DBX36_5 DB202.DBX36.5 -- 1;LM1;Lipsa Tensiune Alimentare Intrari Digitale (LM1);DI;A1;13;M;K

O "LLALM".DB202_DBX33_7 DB202.DBX33.7 -- 1;Gen;Lipsa Tensiune Alimentare pt. modulele ET-LM1;DI;A1;6;M;K

O "LLALM".DB202_DBX33_3 DB202.DBX33.3 -- 1;Gen;Lipsa Tensiune Alimentare pt. modulele ET-TF1;DI;A1;6;M;K

O "LLALM".DB202_DBX36_6 DB202.DBX36.6 -- 1;LM1;Lipsa Tensiune Alimentare Iesiri Digitale (LM1);DI;A1;13;M;K

O "LLALM".DB202_DBX62_2 DB202.DBX62.2 -- 1;FLIPPER T1A;TimeOut Deplasare Aruncator T1-A in pozitia Jos;DI;A1;1;M;0

O "LLALM".DB202_DBX62_3 DB202.DBX62.3 -- 1;FLIPPER T1A;Eroare Depozitare Teava pe C.Role T1-A;SQ;A1;1;0

= "M02".EM DB102.DBX25.5 -- T1A-Aruncator:Emergenta
```

## Segmento 23: T1A-Aruncator: S32:Emergenta

```awl
A "M02".EM DB102.DBX25.5 -- T1A-Aruncator:Emergenta

JNB _00d

L 32

T "M02".Trs DB102.DBW2 -- T1A-Aruncator:Numar Pas Cerut

_00d: NOP 0
```

## Segmento 24: T1A-Aruncator: Gestiune Secventiator

```awl
A(

L 2

T "M02".Seq DB102.DBW0 -- T1A-Aruncator:Secventa

SET

SAVE

CLR

A BR

)

JNB _00e

CALL "Secventiator cu 128 Pasi" FC32 -- Secventiator cu 128 Pasi

DBs:="M02" DB102 -- T1A-Arunc

TIM:=T102

_00e: NOP 0
```

## Segmento 25: T1A-Aruncator: Teava nu este in pozitia corecta (eroare depozit)

```awl
A "M02".TOUT DB102.DBX24.0 -- T1A-Aruncator:TimeOut

A "M02".S18 DB102.DBX8.1 -- T1A-Aruncator:Pas 18

= "LLALM".DB202_DBX62_3 DB202.DBX62.3 -- 1;FLIPPER T1A;Eroare Depozitare Teava pe C.Role T1-A;SQ;A1;1;0
```

## Segmento 26: T1A-Aruncator: Comanda 'Ridicare' in Mod Automat

```awl
O "M02".S10 DB102.DBX7.1 -- T1A-Aruncator:Pas 10

O "M02".S14 DB102.DBX7.5 -- T1A-Aruncator:Pas 14:

O "M02".S18 DB102.DBX8.1 -- T1A-Aruncator:Pas 18

= "M02".FLIPPER_AUTO DB102.DBX22.4 -- T1A-Aruncator:Comanda 'Ridicare' in Mod Automat
```

## Segmento 27: T1A-Aruncator: Comanda 'Ridicare'

```awl
O "M02".FLIPPER_AUTO DB102.DBX22.4 -- T1A-Aruncator:Comanda 'Ridicare' in Mod Automat

O

A(

A "DB:OPIN".P013 DB81.DBX1.4 -- P013-T1A - Aruncator - Cmd. Sus

A "M:CMD 3-MAIN:LM1" M43.2 -- Comenzi 3 - Pupitru Principal Activat:LM1: T1-A

O

A "LM1 T1A-S44.6" I25.7 -- T1A Aruncator Comanda ''Ridicare''

A "M:CMD 4-LOCAL:LM2" M42.3 -- Comenzi 4 - Pupitru Local Activat:LM2: T1-C

O "A:LM1 T1A-K56.1" Q24.0 -- T1A Aruncator ElectroValva ''Ridicare''

)

A(

ON "DB:OPIN".P014 DB81.DBX1.5 -- P014-T1A - Aruncator - Cmd. Jos

ON "M:CMD 3-MAIN:LM1" M43.2 -- Comenzi 3 - Pupitru Principal Activat:LM1: T1-A

)

A(

ON "LM1 T1A-S44.7" I26.0 -- T1A Aruncator Comanda 'Coborare'

ON "M:CMD 4-LOCAL:LM2" M42.3 -- Comenzi 4 - Pupitru Local Activat:LM2: T1-C

)

A "M02".S29 DB102.DBX9.4 -- T1A-Aruncator:Pas 29

= L 1.0

A L 1.0

BLD 102

= "A:LM1 T1A-K56.1" Q24.0 -- T1A Aruncator ElectroValva ''Ridicare''

A L 1.0

BLD 102

= "M02".FU_ON DB102.DBX24.6 -- T1A-Aruncator:Deplasare 'Ridicare'

A L 1.0

BLD 102

= "DB:OPOUT".L017 DB82.DBX2.0 -- L017-T1A - Opritor - Deplasare Inainte

A L 1.0

NOT

= "DB:OPOUT".L018 DB82.DBX2.1 -- L018-T1A - Opritor - Deplasare Inapoi
```
