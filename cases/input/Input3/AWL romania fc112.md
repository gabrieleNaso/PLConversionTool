# FC112 : SEQ12: Lant T4

## Segmento 1: T4-Lant: Citire Date Interfata Convertizor

```awl
//      L     "T4-Lant-Drv-IW1"
//      T     "T4 Lant".RX_STW01
//      L     "T4-Lant-Drv-IW2"
//      T     "T4 Lant".RX_STW02
//      L     "T4-Lant-Drv-IW3"
//      T     "T4 Lant".RX_STW03
//      L     "T4-Lant-Drv-IW4"
//      T     "T4 Lant".RX_STW04
//      L     "T4-Lant-Drv-IW5"
//      T     "T4 Lant".RX_STW05
//      L     "T4-Lant-Drv-IW6"
//      T     "T4 Lant".RX_STW06

L     MW    754
T     "T4 Lant ROST".RX_STW01      DB56.DBW0     -- RX Cuvant Stare 1: Frecventa [Hz x10]

//      L     "T4-Lant_R-Drv-IW2"
//      T     "T4 Lant ROST".RX_STW02
//      L     "T4-Lant_R-Drv-IW3"
//      T     "T4 Lant ROST".RX_STW03
//      L     "T4-Lant_R-Drv-IW4"
//      T     "T4 Lant ROST".RX_STW04
//      L     "T4-Lant_R-Drv-IW5"
//      T     "T4 Lant ROST".RX_STW05
//      L     "T4-Lant_R-Drv-IW6"
//      T     "T4 Lant ROST".RX_STW06
```

## Segmento 2: T4-Lant: Alarme

```awl
```

## Segmento 3: T4-Lant: Resetare Alarme

```awl
A     "M:CLOCK 0.5Hz"             M3.7          -- FC5:Clock 0.5Hz
R     "LLALM".DB202_DBX102_1      DB202.DBX102.1 -- 4;CHAIN T4;TimeOut Cuplare/Decuplare Alim.Inv. Lant T4;DI;A1;10;M;O;K
R     "LLALM".DB202_DBX103_1      DB202.DBX103.1 -- 4;CHAIN T4;TimeOut Deplasare Lant T4 in pozitia Pas;DI;A1;10;M;O;K
R     "LLALM".DB202_DBX102_6      DB202.DBX102.6 -- 4;CHAIN T4 SPIN;TimeOut Cuplare/Decupl. Alim.Inv.LantRost. T4;DI;A1;10;M;O;K
R     "LLALM".DB202_DBX103_4      DB202.DBX103.4 -- 4;CHAIN T4;TimeOut Deplasare Lant T4;DI;A1;10;M;O;K
R     "LLALM".DB202_DBX103_5      DB202.DBX103.5 -- 4;CHAIN T4;TimeOut Cuplare/Decuplare Frana Lant T4;DI;A1;10;M;O;K
```

## Segmento 4: T4-Lant: Stop Permisie Cuplare Lant

```awl
AN    "TF4 T10-E103 S33.7"        I215.6        -- T4 Lant Permisie Cuplare Contactor
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
=     "LLALM".DB202_DBX102_0      DB202.DBX102.0 -- 4;CHAIN T4;Stop Permisie Cuplare Lant T4 - Actionat;DI;A1;10;M;O;K
```

## Segmento 5: T4-Lant: TimeOut Cuplare/Decuplare Alimentare Convertizor

```awl
A(
A     "TF3 T10-K55.5-K22.2"       Q200.4        -- T4 Lant Contactor Alimentare Convertizor
AN    "TF4 T10-E103 K22.2no"      I215.2        -- T4 Lant Confirmare Cuplare Contactor Convertizor
O
AN    "TF3 T10-K55.5-K22.2"       Q200.4        -- T4 Lant Contactor Alimentare Convertizor
A     "TF4 T10-E103 K22.2no"      I215.2        -- T4 Lant Confirmare Cuplare Contactor Convertizor
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
)
L     S5T#500MS
SD    T     76
NOP   0
NOP   0
NOP   0
A     T     76
S     "LLALM".DB202_DBX102_1      DB202.DBX102.1 -- 4;CHAIN T4;TimeOut Cuplare/Decuplare Alim.Inv. Lant T4;DI;A1;10;M;O;K
```

## Segmento 6: T4-Lant: TimeOut Deplasare in Pozitia 'Pas'

```awl
A(
O     "T4 Lant".TX_CW01_FW        DB69.DBX39.0 -- TX Cuvant Control 1: Inainte
O     "T4 Lant".TX_CW01_BW        DB69.DBX39.1 -- TX Cuvant Control 1: Inapoi
)
AN    "M12".OS_CHAIN_STEP         DB112.DBX23.6 -- T4-Lant:Lant in 'Pas'
L     S5T#1M40S
SD    T     290
NOP   0
NOP   0
NOP   0
A     T     290
S     "LLALM".DB202_DBX103_1      DB202.DBX103.1 -- 4;CHAIN T4;TimeOut Deplasare Lant T4 in pozitia Pas;DI;A1;10;M;O;K
```

## Segmento 7: T4-Lant: TimeOut Deplasare

```awl
A(
AN(
A(
O     "T4 Lant".TX_CW01_FW        DB69.DBX39.0 -- TX Cuvant Control 1: Inainte
O     "T4 Lant".TX_CW01_BW        DB69.DBX39.1 -- TX Cuvant Control 1: Inapoi
)
AN    "TF4 T10-E103 K24.5.2"      I215.5        -- T4 Lant Convertizor 'RUN'
)
AN(
AN    "T4 Lant".TX_CW01_FW        DB69.DBX39.0 -- TX Cuvant Control 1: Inainte
AN    "T4 Lant".TX_CW01_BW        DB69.DBX39.1 -- TX Cuvant Control 1: Inapoi
A     "TF4 T10-E103 K24.5.2"      I215.5        -- T4 Lant Convertizor 'RUN'
)
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
L     S5T#5S
SD    T     405
NOP   0
NOP   0
NOP   0
A     T     405
A     "M:FALSE"                   M0.1          -- Intotdeauna Inactiv
S     "LLALM".DB202_DBX103_4      DB202.DBX103.4 -- 4;CHAIN T4;TimeOut Deplasare Lant T4;DI;A1;10;M;O;K
```

## Segmento 8: T4-Lant: Lipsa Tensiune Comanda

```awl
AN    "TF4 T10-E103 Q21.2/K21.2"  I214.0        -- T4 Lant Tensiune Comanda
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
=     "LLALM".DB202_DBX102_2      DB202.DBX102.2 -- 4;CHAIN T4;Lipsa Tensiune de Comanda Lant T4;DI;A1;10;M;K
```

## Segmento 9: T4-Lant: Sectionator Alimentare Convertizor

```awl
AN    "TF4 T10-E103 Q17.3"        I217.1        -- T4 Lant Disjunctor Alimentare Convertizor
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
=     "LLALM".DB202_DBX102_3      DB202.DBX102.3 -- 4;CHAIN T4;Sectionator Alim.Inv. Mot. Lant T4 - Decuplat;DI;A1;10;M;K
```

## Segmento 10: T4-Lant: Disjunctor Alimentare Frana

```awl
AN    "TF4 T10-E103 Q11.8"        I215.7        -- T4 Lant Disjunctor Alimentare Frana
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
=     "LLALM".DB202_DBX102_4      DB202.DBX102.4 -- 4;CHAIN T4;Alim. Frana Mot. Lant T4 - Decuplat;DI;A1;10;M;K
```

## Segmento 11: T4-Lant: TimeOut Cuplare/Decuplare Frana

```awl
A(
A     "TF3 T10-K52.7-K22.6"       Q190.6        -- T4 Lant Contactor Frana
AN    "TF4 T10-E103 K22.6no"      I215.3        -- T4 Lant Confirmare Cuplare Contactor Frana
O
AN    "TF3 T10-K52.7-K22.6"       Q190.6        -- T4 Lant Contactor Frana
A     "TF4 T10-E103 K22.6no"      I215.3        -- T4 Lant Confirmare Cuplare Contactor Frana
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
)
L     S5T#500MS
SD    T     406
NOP   0
NOP   0
NOP   0
A     T     406
S     "LLALM".DB202_DBX103_5      DB202.DBX103.5 -- 4;CHAIN T4;TimeOut Cuplare/Decuplare Frana Lant T4;DI;A1;10;M;O;K
```

## Segmento 12: T4-Lant: Avarie Convertizor

```awl
A(
ON    "TF4 T10-E103 K24.5.1"      I215.4        -- T4 Lant Convertizor 'OK'
O     "Lant-T4-Flt"               M300.0        -- Lant T4 Avarie
)
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
=     "LLALM".DB202_DBX102_5      DB202.DBX102.5 -- 4;CHAIN T4;Inverter Mot. Lant T4 - Avarie;DI;A1;10;M;O;K
```

## Segmento 13: T4-Lant: Disjunctor Alimentare Ventilator Motor

```awl
AN    "TF4 T10-E103 Q11.7"        I215.0        -- T4 Lant Disjunctor Alimentare Ventilatoare Motoare
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
=     "LLALM".DB202_DBX103_7      DB202.DBX103.7 -- 4;CHAIN T4;Disjunctor Termic Alim. Vent.Mot. Lant T4-Declansat;DI;A1;10;M
```

## Segmento 14: T4-LantRost: TimeOut Cuplare/Decuplare Alimentare Convertizor

```awl
A(
A(
A     "TF3 T10-K54.5"             Q191.4        -- T4 Lant Rostogolire Contactor Alimentare Convertizor
AN    "TF4 T10-E102 K26.2no"      I217.2        -- T4 Lant Rostogolire Confirmare Cuplare Contactor Convertizor
O
AN    "TF3 T10-K54.5"             Q191.4        -- T4 Lant Rostogolire Contactor Alimentare Convertizor
A     "TF4 T10-E102 K26.2no"      I217.2        -- T4 Lant Rostogolire Confirmare Cuplare Contactor Convertizor
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
)
L     S5T#500MS
SD    T     77
NOP   0
NOP   0
NOP   0
A     T     77
S     "LLALM".DB202_DBX102_6      DB202.DBX102.6 -- 4;CHAIN T4 SPIN;TimeOut Cuplare/Decupl. Alim.Inv.LantRost. T4;DI;A1;10;M;O;K
```

## Segmento 15: T4-LantRost: Sectionator Alimentare Convertizor

```awl
AN    "TF4 T10-E102 Q17.3"        I217.1        -- T4 Lant Rostogolire Disjunctor Alimentare Convertizor
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
=     "LLALM".DB202_DBX102_7      DB202.DBX102.7 -- 4;CHAIN T4 SPIN;Sectionator Alim.Inv Mot.LantRost T4-Decuplat;DI;A1;10;M;K
```

## Segmento 16: T4-LantRost: Disjunctor Termic Motor

```awl
AN    "TF4 T10-E102 Q17.3"        I217.7        -- T4 Lant Rostogolire Protectie Termica Motor
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
=     "LLALM".DB202_DBX103_0      DB202.DBX103.0 -- 4;CHAIN T4 SPIN;Disjunctor Termic Mot. LantRost. T4-Declansat;DI;A1;10;M;K
```

## Segmento 17: T4-LantRost: Avarie Convertizor

```awl
AN    "TF4 T10-E102 U17.3'OK"     I217.4        -- T4 Lant Rostogolire Convertizor 'OK'
A     "TF4 T10-E102 U17.3'OK"     I217.4        -- T4 Lant Rostogolire Convertizor 'OK'
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
O     "M729.3"                    M729.3        -- Faulte inverter rostogolire lant T4
=     "LLALM".DB202_DBX103_2      DB202.DBX103.2 -- 4;CHAIN T4 SPIN;Inverter Mot. LantRost. T4 - Avarie;DI;A1;10;M;O;K
```

## Segmento 18: T4-LantRost: TimeOut Deplasare

```awl
A(
A(
A(
O     "T4 Lant ROST".TX_CW01_FW   DB56.DBX39.0 -- TX Cuvant Control 1: Inainte
O     "T4 Lant ROST".TX_CW01_BW   DB56.DBX39.1 -- TX Cuvant Control 1: Inapoi
)
AN    "TF4 T10-E102 U17.3(RUN)"   I217.5        -- T4 Lant Rostogolire Convertizor 'RUN'
O
AN    "T4 Lant ROST".TX_CW01_FW   DB56.DBX39.0 -- TX Cuvant Control 1: Inainte
AN    "T4 Lant ROST".TX_CW01_BW   DB56.DBX39.1 -- TX Cuvant Control 1: Inapoi
A     "TF4 T10-E102 U17.3(RUN)"   I217.5        -- T4 Lant Rostogolire Convertizor 'RUN'
)
AN    "M:CMD INS 4 OK"            M40.3         -- Zona Emergenta 4: Comenzi Abilitate
L     S5T#5S
SD    T     407
NOP   0
NOP   0
NOP   0
A     T     407
)
S     "LLALM".DB202_DBX103_6      DB202.DBX103.6 -- 4;CHAIN T4 SPIN;TimeOut Deplasare LantRost. T4;DI;A1;10;M;O;K
A     "DB:OPIN".P004              DB81.DBX0.3  -- P004-Invertere Auxiliare - Reset
A     "T4 Lant ROST".TX_CW01_FW   DB56.DBX39.0 -- TX Cuvant Control 1: Inainte
AN    "T4 Lant ROST".TX_CW01_BW   DB56.DBX39.1 -- TX Cuvant Control 1: Inapoi
O     "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
R     "LLALM".DB202_DBX103_6      DB202.DBX103.6 -- 4;CHAIN T4 SPIN;TimeOut Deplasare LantRost. T4;DI;A1;10;M;O;K
NOP   0
```

## Segmento 19: T4-LantRost: Stop Permisie Cuplare Contactor

```awl
AN    "TF4 T10-E102 S35.7"        I217.7        -- T4 Lant Rostogolire Permisie Cuplare Contactor
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
=     "LLALM".DB202_DBX103_3      DB202.DBX103.3 -- 4;CHAIN T4 SPIN;Stop Permisie Cuplare LantRost. T4 - Actionat;DI;A1;10;M;K
```

## Segmento 20: T4-Lant: Eroare Depozitare Teava

```awl
AN    "M12".PT_END                DB112.DBX23.4 -- T4-Lant:Prezenta Teava pe Ultima Pozitie Bancal
A     "M12".MEM_PT_END            DB112.DBX23.7 -- T4-Lant:Memorie Teava pe Ultima Pozitie Bancal
L     S5T#1S
SD    T     269
NOP   0
NOP   0
NOP   0
A     T     269
=     "LLALM".DB202_DBX104_3      DB202.DBX104.3 -- 4;CHAIN T4;Eroare Depozitare Teava pe Opritor dupa Lant T4;DI;A1;10;O
=     "DB:OPOUT".L198             DB82.DBX24.5  -- L198-T4 - Lant - Alarma Tracking
```

## Segmento 21: T4-Lant: Prezenta Teava Pozitia 'Incetinire'

```awl
AN    "M12".PT_RALL               DB112.DBX22.7 -- T4-Lant:Prezenta Teava Incet Pozitie Bancal
S     "M12".AUX_PTRALL_ON         DB112.DBX123.4
```

## Segmento 22: T4-Lant: Senzor 'Incetinire' Blocat

```awl
A     "M12".OS_CHAIN_STEP         DB112.DBX23.6 -- T4-Lant:Lant in 'Pas'
=     L     32.0
A     L     32.0
AN    "M12".AUX_PTRALL_ON         DB112.DBX123.4
AN    "LLALM".DB202_DBX32_3       DB202.DBX32.3 -- 1;Gen;Z4:Sistem Oprire de Urgenta T3,T4 - Declansat;EM;A3;10;M;O;K
=     "LLALM".DB202_DBX104_4      DB202.DBX104.4 -- 4;CHAIN T4;Senzor Incetinire T4 - Avarie(blocat pe "activat");DI;A1;10;M;O;K
A     L     32.0
BLD   102
R     "M12".AUX_PTRALL_ON         DB112.DBX123.4
```

## Segmento 23: T4-Lant: Memorii Generale

```awl
```

## Segmento 24: T4-Lant: Prezenta Teava pe Pozitie de Start de pe Bancal

```awl
A(
A(
O     "LM4 T4-B48.6"              I81.5         -- T4 Lant Senzor 2 Prezenta Teava pe Lant (intrare)
O     "LM4 T4-B48.5"              I81.4         -- T4 Lant Senzor 1 Prezenta Teava pe Lant (intrare)
)
L     S5T#200MS
SD    T     351
NOP   0
NOP   0
NOP   0
A     T     351
)
L     S5T#200MS
SF    T     439
NOP   0
NOP   0
NOP   0
A     T     439
S     "M12".PT_Start              DB112.DBX23.3 -- T4-Lant:Prezenta Teava pe Pozitia Start Bancal
```

## Segmento 25: T4-Lant: Prezenta Teava pe Pozitia de 'Incetinire' de pe Bancal

```awl
A(
O     "PLC-E102-T4-B49.X1"        I0.3          -- T4-Senzor Proximitate Pozitia 'Incetinire' 1
O     "PLC-E102-T4-B49.X2"        I0.4          -- T4-Senzor Proximitate Pozitia 'Incetinire' 2
)
L     S5T#700MS
SF    T     542
NOP   0
NOP   0
NOP   0
A     T     542
=     "M12".PT_RALL               DB112.DBX22.7 -- T4-Lant:Prezenta Teava Incet Pozitie Bancal
```

## Segmento 26: T4-Lant: Prezenta Teava pe Ultima Pozitie de pe Bancal

```awl
A(
O     "LM4 T4-B49.1"              I82.0         -- T4 Lant Senzor 1 Prezenta Teava pe Lant (pendula opritor iesire)
O     "LM4 T4-B49.2"              I82.1         -- T4 Lant Senzor 2 Prezenta Teava pe Lant (pendula opritor iesire)
)
L     S5T#500MS
SF    T     541
NOP   0
NOP   0
NOP   0
A     T     541
=     "M12".PT_END                DB112.DBX23.4 -- T4-Lant:Prezenta Teava pe Ultima Pozitie Bancal
```

## Segmento 27: T4-Lant: Lant in Pozitia 'Pas'

```awl
A     "LM4 T4-B48.7"              I81.6         -- T4 Lant Senzor 'Pas'
=     L     32.0
A(
A     L     32.0
L     S5T#50MS
SD    "T544"                      T544          -- Pas lant T4
NOP   0
NOP   0
NOP   0
A     "T544"                      T544          -- Pas lant T4
)
L     S5T#10MS
SF    T     545
NOP   0
NOP   0
NOP   0
A     T     545
=     L     32.1
A     L     32.1
FP    "M12".OS_STEP               DB112.DBX23.5 -- T4-Lant:OS Pas Lant
=     "M12".OS_CHAIN_STEP         DB112.DBX23.6 -- T4-Lant:Lant in 'Pas'
A     L     32.1
BLD   102
=     "M12".STEP                  DB112.DBX22.6 -- T4-Lant:Lant in 'Pas'
A     L     32.1
BLD   102
=     "DB:OPOUT".L071             DB82.DBX8.6   -- L071-T4 - Lant (transport) - Pas Efectuat
A     L     32.0
BLD   102
L     S5T#950MS
SF    "T680"                      T680          -- Time pas Lant T4
```

## Segmento 28: T4-Lant: TRK: Prezenta Teava pe Pozitia 'Incetinire' pe Bancal

```awl
A     "M12".PT_RALL               DB112.DBX22.7 -- T4-Lant:Prezenta Teava Incet Pozitie Bancal
FP    "M12".AUX_PIPE_IN           DB112.DBX122.5
A     "T4 Lant".TX_CW01_FW        DB69.DBX39.0 -- TX Cuvant Control 1: Inainte
S     "M12".TRK_PIPE_IN           DB112.DBX122.2 -- PIPE IN CHAIN RALL POSITION
```

## Segmento 29: T4-Lant: Teava Prezenta pe 'Ultima' Pozitie Bancal

```awl
A(
O     "M12".S02                  DB112.DBX6.1  -- T4-Lant:Pas 02:
ON    "M13".UP                   DB113.DBX25.0 -- T4-OPRITOR:FLIPPER UP
)
AN    "M12".PT_END               DB112.DBX23.4 -- T4-Lant:Prezenta Teava pe Ultima Pozitie Bancal
O     "DB:OPIN".P302             DB81.DBX37.5  -- P302-T4 - Reset Tracking
R     "M12".MEM_PT_END           DB112.DBX23.7 -- T4-Lant:Memorie Teava pe Ultima Pozitie Bancal
```

## Segmento 30: T4-Lant: Teava Prezenta pe 'Ultima' Pozitie Bancal

```awl
A     "M12".OS_CHAIN_STEP         DB112.DBX23.6 -- T4-Lant:Lant in 'Pas'
=     L     32.0
A     L     32.0
A     "M12".TRK_PIPE_LAST         DB112.DBX122.1 -- PIPE IN CHAIN LAST POSITION
S     "M12".MEM_PT_END            DB112.DBX23.7 -- T4-Lant:Memorie Teava pe Ultima Pozitie Bancal
A     L     32.0
BLD   102
R     "M12".TRK_PIPE_LAST         DB112.DBX122.1 -- PIPE IN CHAIN LAST POSITION
A     L     32.0
A     "M12".TRK_PIPE_IN           DB112.DBX122.2 -- PIPE IN CHAIN RALL POSITION
S     "M12".TRK_PIPE_LAST         DB112.DBX122.1 -- PIPE IN CHAIN LAST POSITION
R     "M12".TRK_PIPE_IN           DB112.DBX122.2 -- PIPE IN CHAIN RALL POSITION
```

## Segmento 31: T4-Lant: TRK: Teava in Pozitia 'Descarcare'

```awl
O     "M12".PT_RALL               DB112.DBX22.7 -- T4-Lant:Prezenta Teava Incet Pozitie Bancal
O     "M12".TRK_PIPE_IN           DB112.DBX122.2 -- PIPE IN CHAIN RALL POSITION
O     "M12".TRK_PIPE_LAST         DB112.DBX122.1 -- PIPE IN CHAIN LAST POSITION
O     "M12".MEM_PT_END            DB112.DBX23.7 -- T4-Lant:Memorie Teava pe Ultima Pozitie Bancal
O     "M12".PT_END                DB112.DBX23.4 -- T4-Lant:Prezenta Teava pe Ultima Pozitie Bancal
=     "M12".TRK_PIPE_INcet        DB112.DBX122.0 -- ONE PIPE IN Incet POSITION
```

## Segmento 32: T4-Lant: Teava Pregatita pt. 'Incarcare'

```awl
A(
A(
A(
A     "LM4 T3-B49.3"              I80.2         -- T4 Role-1 Senzor 1 Prezenta Teava pe Role
A     "M:FALSE"                   M0.1          -- Intotdeauna Inactiv
O     "E81.7"                     I81.7         -- T4 senzori suplimentar la tevi scurte
O     "LM4 T4-B48.1"              I81.0         -- T4 Role-1 Senzor 2 Prezenta Teava pe Role
O     "LM4 T4-B48.2"              I81.1         -- T4 Role-1 Senzor 3 Prezenta Teava pe Role
)
)
A     "M10".S14                   DB110.DBX7.5  -- T4.1-Role:Pas 14:
O     "M10".S18                   DB110.DBX8.1  -- T4.1-Role:Pas 18
O     "M10".S19                   DB110.DBX8.2  -- T4.1-Role:Pas 19
O     "M10".S22                   DB110.DBX8.5  -- T4.1-Role:Pas 22
)
A(
O     "M11".S03                   DB111.DBX6.2  -- T4-Excentric:Pas 03
O     "M11".S04                   DB111.DBX6.3  -- T4-Excentric:Pas 04
O     "M11".S07                   DB111.DBX6.6  -- T4-Excentric:Pas 07
O     "M11".S10                   DB111.DBX7.1  -- T4-Excentric:Pas 10
O     "M11".S14                   DB111.DBX7.5  -- T4-Excentric:Pas 14
O     "M11".S18                   DB111.DBX8.1  -- T4-Excentric:Pas 18
O     "M11".S22                   DB111.DBX8.5  -- T4-Excentric:Pas 22
)
AN    "M11".STOP                  DB111.DBX25.3 -- T4-Excentric:Cerere 'Stop' in Mod Automat
=     "M12".PIPE_TO_CHARGE        DB112.DBX123.5 -- 1 pipe to charge
```

## Segmento 33: T4-Lant: TRK: Deplaseaza Lant in 'Pas'

```awl
A(
O     "M12".OS_CHAIN_STEP         DB112.DBX23.6 -- T4-Lant:Lant in 'Pas'
AN    "M12".BENCH_EMPTY           DB112.DBX23.0 -- T4-Lant:Bancal Gol
JNB   _001
L     "M12".COUNT_STEP            DB112.DBW94   -- T4-Lant:Numar Pas Lant
L     1
+I
T     "M12".COUNT_STEP            DB112.DBW94   -- T4-Lant:Numar Pas Lant
_001: NOP 0
```

## Segmento 34: T4-Lant: AUX:Bancal Gol

```awl
A(
O     "M12".PT_Start              DB112.DBX23.3 -- T4-Lant:Prezenta Teava pe Pozitia Start Bancal
O     "M:T4 Start:Cycle"          M45.4         -- T4: Start:CICLU
)
JNB   _002
L     0
T     "M12".COUNT_STEP            DB112.DBW94   -- T4-Lant:Numar Pas Lant
_002: NOP 0
```

## Segmento 35: T4-Lant: AUX:Bancal Gol

```awl
L     "M12".COUNT_STEP            DB112.DBW94   -- T4-Lant:Numar Pas Lant
L     27
>=I
=     "M12".BENCH_EMPTY           DB112.DBX23.0 -- T4-Lant:Bancal Gol
```

## Segmento 36: T4-Lant: Ciclu Selectat

```awl
A     "M:TRUE"                    M0.0          -- Intotdeauna Activ
=     L     32.0
A     L     32.0
A(
L     "DB:OPSP".SPI010            DB83.DBW18    -- SPI010-Lant T4 Mod Functie (0:Umplere,1:TimeOut,2:Golire)
L     0
==I
)
=     "M12".C_PT                  DB112.DBX25.0 -- T4-Lant:Cycle Filling
A     L     32.0
A(
L     "DB:OPSP".SPI010            DB83.DBW18    -- SPI010-Lant T4 Mod Functie (0:Umplere,1:TimeOut,2:Golire)
L     1
==I
)
=     "M12".C_TO                  DB112.DBX25.1 -- T4-Lant:Cycle Time out
A     L     32.0
A(
L     "DB:OPSP".SPI010            DB83.DBW18    -- SPI010-Lant T4 Mod Functie (0:Umplere,1:TimeOut,2:Golire)
L     2
==I
)
=     "M12".C_E                   DB112.DBX25.2 -- T4-Lant:Cycle Empty
A     L     32.0
A(
L     "DB:OPSP".SPI010            DB83.DBW18    -- SPI010-Lant T4 Mod Functie (0:Umplere,1:TimeOut,2:Golire)
L     3
>=I
)
=     "M12".C_F                   DB112.DBX25.7 -- T4-Lant:Cycle Fast One pipe
```

## Segmento 37: T4-Lant: Calcul TimeOut

```awl
L     "DB13:RX-Q".INI1            DB13.DBW20    -- Cadenta Desire [sec]
L     "LIPRE".A1ACT.SPU33         DB246.DBD264  -- A1:SPU33: T4: Lant: Depasire Timp la Pornirea Unui Pas [sec]
+I
T     #AUXI                                       -- #AUXI
```

## Segmento 38: T4-Lant: TimeOut Bancal

```awl
O(
L     #AUXI                       #AUXI
L     999
>I
)
O(
L     #AUXI                       #AUXI
L     1
<I
)
JC    M002
L     #AUXI                       #AUXI
ITB
M002: NOP 0
L     W#16#2000
OW
T     #AUXI                       #AUXI
```

## Segmento 39: T4-Lant: AUX:TimeOut Bancal (IF 1 START CHAIN)

```awl
A     "M12".S03                   DB112.DBX6.2  -- T4-Lant:Pas 03:
A     "M12".C_TO                  DB112.DBX25.1 -- T4-Lant:Cycle Time out
AN    "M10".PT                    DB110.DBX23.3 -- T4.1-Role:Prezenta Teava
AN    "M09".PT                    DB109.DBX23.3 -- T3-Role:Prezenta Teava
L     #AUXI                       #AUXI
SD    T     97
NOP   0
NOP   0
LC    T     97
T     "M:T4:TIMEOUT_BENCH"        MW100
A     T     97
=     "M12".TIME_OUT_BENCH        DB112.DBX22.5 -- T4-Lant:TimeOut Bancal
```

## Segmento 40: T4-Lant: S01:Start

```awl
A     "M12".S01                   DB112.DBX6.0  -- T4-Lant:Pas 01
A     "M:T4:Auto"                 M49.4         -- T4: Auto
JNB   _003
L     2
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_003: NOP 0
```

## Segmento 41: T4-Lant: Conditii Start

```awl
A     "M12".STEP                  DB112.DBX22.6 -- T4-Lant:Lant in 'Pas'
=     "M12".STC                   DB112.DBX25.4 -- T4-Lant:Conditii Start
```

## Segmento 42: T4-Lant: S02:Conditii Start Ciclu

```awl
A     "M12".S02                   DB112.DBX6.1  -- T4-Lant:Pas 02:
A     "M:T4:Start:Cycle"          M45.4         -- T4: Start:CICLU
A     "M12".STC                   DB112.DBX25.4 -- T4-Lant:Conditii Start
JNB   _004
L     3
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_004: NOP 0
```

## Segmento 43: T4-Lant: S03:Conditii Prezenta

```awl
A(
A(
O     "M12".PT_Start              DB112.DBX23.3 -- T4-Lant:Prezenta Teava pe Pozitia Start Bancal
O     "M12".TIME_OUT_BENCH        DB112.DBX22.5 -- T4-Lant:TimeOut Bancal
ON    "M12".STEP                  DB112.DBX22.6 -- T4-Lant:Lant in 'Pas'
O
A(
A     "M12".C_E                   DB112.DBX25.2 -- T4-Lant:Cycle Empty
AN    "M11".S10                   DB111.DBX7.1  -- T4-Excentric:Pas 10
AN    "M11".S14                   DB111.DBX7.5  -- T4-Excentric:Pas 14
AN    "M11".S22                   DB111.DBX8.5  -- T4-Excentric:Pas 22
O     "M12".C_F                   DB112.DBX25.7 -- T4-Lant:Cycle Fast One pipe
)
AN    "M12".PIPE_TO_CHARGE        DB112.DBX123.5 -- 1 pipe to charge
)
A(
A(
O     "M11".S03                   DB111.DBX6.2  -- T4-Excentric:Pas 03
O     "M11".S18                   DB111.DBX8.1  -- T4-Excentric:Pas 18
)
AN    "M11".FW_ON                 DB111.DBX22.7 -- T4-Excentric:Rotire 'Inainte'
O     "M11".S26                   DB111.DBX9.1  -- T4-Excentric:Pas 26
)
A(
AN    "M12".PT_END                DB112.DBX23.4 -- T4-Lant:Prezenta Teava pe Ultima Pozitie Bancal
AN    "M12".MEM_PT_END            DB112.DBX23.7 -- T4-Lant:Memorie Teava pe Ultima Pozitie Bancal
ON    "M12".TRK_PIPE_LAST         DB112.DBX122.1 -- PIPE IN CHAIN LAST POSITION
O
A(
A     "M13".S03                   DB113.DBX6.2  -- T4-OPRITOR:Pas 03:
A     "M13".UP                    DB113.DBX25.0 -- T4-OPRITOR:FLIPPER UP
A     "M12".S03                   DB112.DBX6.2  -- T4-Lant:Pas 03:
L     S5T#300MS
SD    T     760
NOP   0
NOP   0
NOP   0
A     T     760
)
)
JNB   _005
L     4
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_005: NOP 0
```

## Segmento 44: T4-Lant: S04:Conditii Abilitare

```awl
A     "M12".S04                   DB112.DBX6.3  -- T4-Lant:Pas 04
JNB   _006
L     7
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_006: NOP 0
```

## Segmento 45: T4-Lant: S07:Conditii Start

```awl
A     "M12".S07                   DB112.DBX6.6  -- T4-Lant:Pas 07
JNB   _007
L     10
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_007: NOP 0
```

## Segmento 46: T4-Lant: S10:Comanda Deplasare 'Inainte'

```awl
A     "M12".S10                   DB112.DBX7.1  -- T4-Lant:Pas 10
AN    "M12".STEP                  DB112.DBX22.6 -- T4-Lant:Lant in 'Pas'
JNB   _008
L     14
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_008: NOP 0
```

## Segmento 47: T4-Lant: S14:Comanda Deplasare 'Inainte'

```awl
A     "M12".S14                   DB112.DBX7.5  -- T4-Lant:Pas 14:
JNB   _009
L     18
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_009: NOP 0
```

## Segmento 48: T4-Lant: S18:Comanda Deplasare 'Inainte'

```awl
A     "M12".S18                   DB112.DBX8.1  -- T4-Lant:Pas 18
A     "M12".STEP                  DB112.DBX22.6 -- T4-Lant:Lant in 'Pas'
=     L     32.0
A     L     32.0
JNB   _00a
L     20
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_00a: NOP 0
A     L     32.0
A(
ON    "M13".UP                    DB113.DBX25.0 -- T4-OPRITOR:FLIPPER UP
O     "M12".PT_END                DB112.DBX23.4 -- T4-Lant:Prezenta Teava pe Ultima Pozitie Bancal
)
JNB   _00b
L     3
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_00b: NOP 0
```

## Segmento 49: T4-Lant: S20:Selectie

```awl
A     "M12".S20                   DB112.DBX8.3  -- T4-Lant:Pas 20
A(
AN    "M12".C_TO                  DB112.DBX25.1 -- T4-Lant:Cycle Time out
AN    "M12".C_F                   DB112.DBX25.7 -- T4-Lant:Cycle Fast One pipe
AN    "M12".C_E                   DB112.DBX25.2 -- T4-Lant:Cycle Empty
O
A     "M12".C_TO                  DB112.DBX25.1 -- T4-Lant:Cycle Time out
AN    "C2"                        C2            -- Lant T4 doi pasi
)
=     L     32.0
A     L     32.0
AN    "M12".MEM_PT_END            DB112.DBX23.7 -- T4-Lant:Memorie Teava pe Ultima Pozitie Bancal
AN    "M12".PT_END                DB112.DBX23.4 -- T4-Lant:Prezenta Teava pe Ultima Pozitie Bancal
JNB   _00c
L     3
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_00c: NOP 0
A     L     32.0
A(
O     "M12".MEM_PT_END            DB112.DBX23.7 -- T4-Lant:Memorie Teava pe Ultima Pozitie Bancal
O     "M12".PT_END                DB112.DBX23.4 -- T4-Lant:Prezenta Teava pe Ultima Pozitie Bancal
)
JNB   _00d
L     22
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_00d: NOP 0
```

## Segmento 50: T4-Lant: S20:Comanda Deplasare 'Inainte'

```awl
A     "M12".S20                   DB112.DBX8.3  -- T4-Lant:Pas 20
A(
O     "M12".C_F                   DB112.DBX25.7 -- T4-Lant:Cycle Fast One pipe
O     "M12".C_E                   DB112.DBX25.2 -- T4-Lant:Cycle Empty
A(
A     "M12".C_TO                  DB112.DBX25.1 -- T4-Lant:Cycle Time out
A     "C2"                        C2            -- Lant T4 doi pasi
)
)
=     L     32.0
A     L     32.0
AN    "M12".PIPE_TO_CHARGE        DB112.DBX123.5 -- 1 pipe to charge
JNB   _00e
L     3
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_00e: NOP 0
A     L     32.0
A     "M12".TRK_PIPE_LAST         DB112.DBX122.1 -- PIPE IN CHAIN LAST POSITION
=     L     32.1
A     L     32.1
A     "M13".S03                   DB113.DBX6.2  -- T4-OPRITOR:Pas 03:
AN    "M13".UP                    DB113.DBX25.0 -- T4-OPRITOR:FLIPPER UP
JNB   _00f
L     10
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_00f: NOP 0
A     L     32.3
AN    "M12".PT_END                DB112.DBX23.4 -- T4-Lant:Prezenta Teava pe Ultima Pozitie Bancal
AN    "M12".MEM_PT_END            DB112.DBX23.7 -- T4-Lant:Memorie Teava pe Ultima Pozitie Bancal
JNB   _010
L     22
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_010: NOP 0
A     L     32.3
A(
O     "M12".MEM_PT_END            DB112.DBX23.7 -- T4-Lant:Memorie Teava pe Ultima Pozitie Bancal
O     "M12".PT_END                DB112.DBX23.4 -- T4-Lant:Prezenta Teava pe Ultima Pozitie Bancal
)
JNB   _011
L     10
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_011: NOP 0
A     L     32.1
AN    "M12".TRK_PIPE_LAST         DB112.DBX122.1 -- PIPE IN CHAIN LAST POSITION
JNB   _012
L     10
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_012: NOP 0
A     L     32.0
A     "M12".PIPE_TO_CHARGE        DB112.DBX123.5 -- 1 pipe to charge
JNB   _013
L     3
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_013: NOP 0
```

## Segmento 51: T4-Lant: S22:Sfarsit Secventa

```awl
A(
O     "M12".PT_END                DB112.DBX23.4 -- T4-Lant:Prezenta Teava pe Ultima Pozitie Bancal
ON    "M12".MEM_PT_END            DB112.DBX23.7 -- T4-Lant:Memorie Teava pe Ultima Pozitie Bancal
)
A     "M12".S22                   DB112.DBX8.5  -- T4-Lant:Pas 22
JNB   _013
L     1
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_013: NOP 0
```

## Segmento 52: T4-Lant: S01:Start

```awl
A(
O     "M12".S29                   DB112.DBX9.4  -- T4-Lant:Pas 29
O     "M12".S32                   DB112.DBX9.7  -- T4-Lant:Pas 32
)
AN    "M12".EM                    DB112.DBX25.5 -- T4-Lant:Emergenta
AN    "M:T4:Manual"               M47.4         -- T4: Manual
JNB   _014
L     1
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_014: NOP 0
```

## Segmento 53: T4-Lant: S29:Mod Manual

```awl
A     "M:AUX Z4 OK"               M44.3         -- Zona 4:Auxiliar OK
A     "M:T4:Manual"               M47.4         -- T4: Manual
JNB   _015
L     29
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_015: NOP 0
```

## Segmento 54: T4-Lant: Cumulativ Alarme

```awl
ON    "M:CMD INS 4 OK"            M40.3         -- Zona Emergenta 4: Comenzi Abilitate
O     "LLALM".DB202_DBX102_1      DB202.DBX102.1 -- 4;CHAIN T4;TimeOut Cuplare/Decuplare Alim.Inv. Lant T4;DI;A1;10;M;O;K
O     "LLALM".DB202_DBX102_2      DB202.DBX102.2 -- 4;CHAIN T4;Lipsa Tensiune de Comanda Lant T4;DI;A1;10;M;K
O     "LLALM".DB202_DBX102_3      DB202.DBX102.3 -- 4;CHAIN T4;Sectionator Alim.Inv. Mot. Lant T4 - Decuplat;DI;A1;10;M;K
O     "LLALM".DB202_DBX102_4      DB202.DBX102.4 -- 4;CHAIN T4;Alim. Frana Mot. Lant T4 - Decuplat;DI;A1;10;M;K
O     "LLALM".DB202_DBX102_5      DB202.DBX102.5 -- 4;CHAIN T4;Inverter Mot. Lant T4 - Avarie;DI;A1;10;M;O;K
O     "LLALM".DB202_DBX103_1      DB202.DBX103.1 -- 4;CHAIN T4;TimeOut Deplasare Lant T4 in pozitia Pas;DI;A1;10;M;O;K
O     "LLALM".DB202_DBX103_4      DB202.DBX103.4 -- 4;CHAIN T4;TimeOut Deplasare Lant T4;DI;A1;10;M;O;K
O     "LLALM".DB202_DBX103_5      DB202.DBX103.5 -- 4;CHAIN T4;TimeOut Cuplare/Decuplare Frana Lant T4;DI;A1;10;M;O;K
O     "LLALM".DB202_DBX104_4      DB202.DBX104.4 -- 4;CHAIN T4;Senzor Incetinire T4 - Avarie(blocat pe "activat");DI;A1;10;M;O;K
=     "M12".EM                    DB112.DBX25.5 -- T4-Lant:Emergenta
```

## Segmento 55: T4-Lant: S32:Emergenta

```awl
A     "M12".EM                    DB112.DBX25.5 -- T4-Lant:Emergenta
JNB   _016
L     32
T     "M12".Trs                  DB112.DBW2    -- T4-Lant:Numar Pas Cerut
_016: NOP 0
```

## Segmento 56: T4-Lant: Gestiune Secventiator

```awl
A(
L     12
T     "M12".Seq                   DB112.DBW0    -- T4-Lant:Secventa
SET
SAVE
CLR
A     BR
)
JNB   _017
CALL  "Secventiator cu 128 Pasi"  FC32          -- Secventiator cu 128 Pasi
      DBs:="M12"                  DB112         -- T4-Lant
      TIM:=T112
_017: NOP 0
```

## Segmento 57: T4-Lant: Gestiune Iesiri

```awl
A     "T544"                      T544          -- Pas lant T4
FP    M     143.2
CD    "C2"                        C2            -- Lant T4 doi pasi
BLD   101
A     "M11".S07                   DB111.DBX6.6  -- T4-Excentric:Pas 07
FP    M     143.1
L     C#2
S     "C2"                        C2            -- Lant T4 doi pasi
A     "M12".S29                   DB112.DBX9.4  -- T4-Lant:Pas 29
R     "C2"                        C2            -- Lant T4 doi pasi
NOP   0
NOP   0
NOP   0
```

## Segmento 58: T4-Lant: Mod Manual Continuu

```awl
A(
O     "DB:OPIN".P278              DB81.DBX34.5 -- P278-T4 - Lant - Mod Operare Continuu (local)
O     "M12".M_MODE                DB112.DBX25.6 -- T4-Lant:Mod Manual Continuu
)
A(
ON    "DB:OPIN".P277              DB81.DBX34.4 -- P277-T4 - Lant - Mod Operare Pas (local)
ON    "M:CMD 5-MAIN:LM4"          M43.4        -- Comenzi 5 - Pupitru Principal Activat:LM4: T3-T4
)
A     "M:CMD 5-MAIN:LM4"          M43.4        -- Comenzi 5 - Pupitru Principal Activat:LM4: T3-T4
O
A     "LM4 T10[T4]=S45.3"         I79.2        -- T4 Lant Selectie 'Pas/Continuu'
A     "M:CMD 5-LOCAL:LM4"         M42.4        -- Comenzi 5 - Pupitru Local Activat:LM4: T3-T4
=     L     32.0
A     L     32.0
BLD   102
=     "M12".M_MODE                DB112.DBX25.6 -- T4-Lant:Mod Manual Continuu
A     L     32.0
BLD   102
=     "DB:OPOUT".L054             DB82.DBX6.5  -- L054-T4 - Lant - Mod Operare Continuu
A     L     32.0
NOT
=     "DB:OPOUT".L053             DB82.DBX6.4  -- L053-T4 - Lant - Mod Operare Pas
```

## Segmento 59: T4-Lant: AUX:Deplasare 'Inainte' in Mod Automat

```awl
O     "M12".S10                   DB112.DBX7.1  -- T4-Lant:Pas 10
O     "M12".S14                   DB112.DBX7.5  -- T4-Lant:Pas 14:
O     "M12".S18                   DB112.DBX8.1  -- T4-Lant:Pas 18
O     "M12".S20                   DB112.DBX8.3  -- T4-Lant:Pas 20
=     "M12".CHAIN_AUTO_FW         DB112.DBX22.4 -- T4-Lant:Deplasare 'Inainte'
```

## Segmento 60: T4-Lant: Deplasare 'Inainte'

```awl
A(
O     "M12".CHAIN_AUTO_FW         DB112.DBX22.4 -- T4-Lant:Deplasare 'Inainte'
O(
A(
A(
A     "DB:OPIN".P039              DB81.DBX4.6  -- P039-T4 - Lant (transport) - Cmd. Inainte
FP    "M:AUXOSO23"                M277.6
O
A     "DB:OPIN".P039              DB81.DBX4.6  -- P039-T4 - Lant (transport) - Cmd. Inainte
A     "M12".M_MODE                DB112.DBX25.6 -- T4-Lant:Mod Manual Continuu
)
A     "M:CMD 5-MAIN:LM4"          M43.4        -- Comenzi 5 - Pupitru Principal Activat:LM4: T3-T4
O
A(
A     "LM4 T10[T4]=S45.1"         I79.0        -- T4 Lant Comanda 'Inainte'
FP    "M:AUXOSO24"                M277.7
O
A     "LM4 T10[T4]=S45.1"         I79.0        -- T4 Lant Comanda 'Inainte'
A     "M12".M_MODE                DB112.DBX25.6 -- T4-Lant:Mod Manual Continuu
)
A     "M:CMD 5-LOCAL:LM4"         M42.4        -- Comenzi 5 - Pupitru Local Activat:LM4: T3-T4
)
AN    "M12".PT_END                DB112.DBX23.4 -- T4-Lant:Prezenta Teava pe Ultima Pozitie Bancal
O
A     "T4 Lant".TX_CW01_FW        DB69.DBX39.0 -- TX Cuvant Control 1: Inainte
AN    "M12".M_MODE                DB112.DBX25.6 -- T4-Lant:Mod Manual Continuu
AN    "M12".OS_CHAIN_STEP         DB112.DBX23.6 -- T4-Lant:Lant in 'Pas'
)
A(
ON    "DB:OPIN".P040              DB81.DBX4.7  -- P040-T4 - Lant (transport) - Cmd. Inapoi
ON    "M:CMD 5-MAIN:LM4"          M43.4        -- Comenzi 5 - Pupitru Principal Activat:LM4: T3-T4
)
A(
ON    "LM4 T10[T4]=S45.2"         I79.1        -- T4 Lant Comanda 'Inapoi'
ON    "M:CMD 5-LOCAL:LM4"         M42.4        -- Comenzi 5 - Pupitru Local Activat:LM4: T3-T4
)
AN    "M12".BW_ON                 DB112.DBX24.7 -- T4-Lant:BACKWARD ON
=     L     32.0
A     L     32.0
A     "M:FALSE"                   M0.1          -- Intotdeauna Inactiv
=     "TF3 T10-K55.7"             Q200.6        -- T4 Lant Contactor Deplasare 'Inainte'
A     L     32.0
BLD   102
=     "T4 Lant".TX_CW01_FW        DB69.DBX39.0 -- TX Cuvant Control 1: Inainte
A     L     32.0
BLD   102
=     "DB:OPOUT".L067             DB82.DBX8.2  -- L067-T4 - Lant (transport) - Deplasare Inainte
A     L     32.0
L     S5T#1S
SF    T     351
NOP   0
NOP   0
NOP   0
A     T     351
=     "M12".FW_ON                 DB112.DBX24.6 -- T4-Lant:FORWARD ON
```

## Segmento 61: T4-Lant: Deplasare 'Inapoi'

```awl
A(
A     "DB:OPIN".P040              DB81.DBX4.7  -- P040-T4 - Lant (transport) - Cmd. Inapoi
A     "DB:OPIN".P039              DB81.DBX4.6  -- P039-T4 - Lant (transport) - Cmd. Inainte
A     "M:CMD 5-MAIN:LM4"          M43.4        -- Comenzi 5 - Pupitru Principal Activat:LM4: T3-T4
O
A     "LM4 T10[T4]=S45.2"         I79.1        -- T4 Lant Comanda 'Inapoi'
AN    "LM4 T10[T4]=S45.1"         I79.0        -- T4 Lant Comanda 'Inainte'
A     "M:CMD 5-LOCAL:LM4"         M42.4        -- Comenzi 5 - Pupitru Local Activat:LM4: T3-T4
)
AN    "M12".PT_Start              DB112.DBX23.3 -- T4-Lant:Prezenta Teava pe Pozitia Start Bancal
A     "M12".S29                   DB112.DBX9.4  -- T4-Lant:Pas 29
AN    "T4 Lant".TX_CW01_FW        DB69.DBX39.0 -- TX Cuvant Control 1: Inainte
=     L     32.0
A     L     32.0
A     "M:FALSE"                   M0.1          -- Intotdeauna Inactiv
=     "TF3 T10-K55.8"             Q200.7        -- T4 Lant Contactor Deplasare 'Inapoi'
A     L     32.0
BLD   102
=     "T4 Lant".TX_CW01_BW        DB69.DBX39.1 -- TX Cuvant Control 1: Inapoi
A     L     32.0
BLD   102
=     "DB:OPOUT".L068             DB82.DBX8.3  -- L068-T4 - Lant (transport) - Deplasare Inapoi
A     L     32.0
L     S5T#1S
SF    T     352
NOP   0
NOP   0
NOP   0
A     T     352
=     "M12".BW_ON                 DB112.DBX24.7 -- T4-Lant:BACKWARD ON
```

## Segmento 62: T4-Lant: Contactor Alimentare Convertizor

```awl
A     "TF4 T10-E103 S33.7"        I215.6        -- T4 Lant Permisie Cuplare Contactor
A     "M:CMD INS 4 OK"            M40.3         -- Zona Emergenta 4: Comenzi Abilitate
AN    "LLALM".DB202_DBX102_2      DB202.DBX102.2 -- 4;CHAIN T4;Lipsa Tensiune de Comanda Lant T4;DI;A1;10;M;K
=     "TF3 T10-K55.5-K22.2"       Q200.4        -- T4 Lant Contactor Alimentare Convertizor
```

## Segmento 63: T4-LantRost: Comanda Deplasare 'Inainte'

```awl
A(
A(
O     "DB:OPIN".P037              DB81.DBX4.4  -- P037-T4 - Lant (rostogolire) - Cmd. Inainte
O     "T4 Lant ROST".TX_CW01_FW   DB56.DBX39.0 -- TX Cuvant Control 1: Inainte
)
A     "M:CMD 5-MAIN:LM4"          M43.4        -- Comenzi 5 - Pupitru Principal Activat:LM4: T3-T4
O
A     "LM4 T10[T4]=S45.4"         I79.3        -- T4 Lant Rostogolire Comanda Inainte
A     "M:CMD 5-LOCAL:LM4"         M42.4        -- Comenzi 5 - Pupitru Local Activat:LM4: T3-T4
)
A(
AN    "DB:OPIN".P038              DB81.DBX4.5  -- P038-T4 - Lant (rostogolire) - Cmd. Inapoi
AN    "DB:OPIN".P057              DB81.DBX7.0  -- P057-T4 - Lant (rostogolire) - Cmd. Stop
O
AN    "M:CMD 5-MAIN:LM4"          M43.4        -- Comenzi 5 - Pupitru Principal Activat:LM4: T3-T4
AN    "M:T4 Auto"                 M49.4        -- T4: Auto
)
A(
ON    "LM4 T10[T4]=S45.5"         I79.4        -- T4 Lant Rostogolire Comanda Inapoi
ON    "M:CMD 5-LOCAL:LM4"         M42.4        -- Comenzi 5 - Pupitru Local Activat:LM4: T3-T4
)
AN    "LLALM".DB202_DBX102_6      DB202.DBX102.6 -- 4;CHAIN T4 SPIN;TimeOut Cuplare/Decupl. Alim.Inv.LantRost. T4;DI;A1;10;M;O;K
AN    "LLALM".DB202_DBX102_7      DB202.DBX102.7 -- 4;CHAIN T4 SPIN;Sectionator Alim.Inv Mot.LantRost T4-Decuplat;DI;A1;10;M;K
AN    "LLALM".DB202_DBX103_0      DB202.DBX103.0 -- 4;CHAIN T4 SPIN;Disjunctor Termic Mot.LantRost. T4-Declansat;DI;A1;10;M;K
AN    "LLALM".DB202_DBX103_2      DB202.DBX103.2 -- 4;CHAIN T4 SPIN;Inverter Mot. LantRost. T4 - Avarie;DI;A1;10;M;O;K
AN    "LLALM".DB202_DBX103_6      DB202.DBX103.6 -- 4;CHAIN T4 SPIN;TimeOut Deplasare LantRost. T4;DI;A1;10;M;O
A     "M:CMD INS 4 OK"            M40.3        -- Zona Emergenta 4: Comenzi Abilitate
AN    "T4 Lant ROST".TX_CW01_BW   DB56.DBX39.1 -- TX Cuvant Control 1: Inapoi
=     "T4 Lant ROST".TX_CW01_FW   DB56.DBX39.0 -- TX Cuvant Control 1: Inainte
=     "DB:OPOUT".L069             DB82.DBX8.4  -- L069-T4 - Lant (rostogolire) - Deplasare Inainte
```

## Segmento 64: T4-LantRost: Comanda Deplasare 'Inapoi'

```awl
A(
A     "DB:OPIN".P038              DB81.DBX4.5  -- P038-T4 - Lant (rostogolire) - Cmd. Inapoi
AN    "DB:OPIN".P037              DB81.DBX4.4  -- P037-T4 - Lant (rostogolire) - Cmd. Inainte
A     "M:CMD 5-MAIN:LM4"          M43.4        -- Comenzi 5 - Pupitru Principal Activat:LM4: T3-T4
O
A     "LM4 T10[T4]=S45.5"         I79.4        -- T4 Lant Rostogolire Comanda Inapoi
AN    "LM4 T10[T4]=S45.4"         I79.3        -- T4 Lant Rostogolire Comanda Inainte
A     "M:CMD 5-LOCAL:LM4"         M42.4        -- Comenzi 5 - Pupitru Local Activat:LM4: T3-T4
)
AN    "LLALM".DB202_DBX102_6      DB202.DBX102.6 -- 4;CHAIN T4 SPIN;TimeOut Cuplare/Decupl. Alim.Inv.LantRost. T4;DI;A1;10;M;O;K
AN    "LLALM".DB202_DBX102_7      DB202.DBX102.7 -- 4;CHAIN T4 SPIN;Sectionator Alim.Inv Mot.LantRost T4-Decuplat;DI;A1;10;M;K
AN    "LLALM".DB202_DBX103_0      DB202.DBX103.0 -- 4;CHAIN T4 SPIN;Disjunctor Termic Mot.LantRost. T4-Declansat;DI;A1;10;M;K
AN    "LLALM".DB202_DBX103_2      DB202.DBX103.2 -- 4;CHAIN T4 SPIN;Inverter Mot. LantRost. T4 - Avarie;DI;A1;10;M;O;K
AN    "LLALM".DB202_DBX103_6      DB202.DBX103.6 -- 4;CHAIN T4 SPIN;TimeOut Deplasare LantRost. T4;DI;A1;10;M;O
A     "M12".S29                   DB112.DBX9.4 -- T4-Lant:Pas 29
AN    "T4 Lant ROST".TX_CW01_FW   DB56.DBX39.0 -- TX Cuvant Control 1: Inainte
=     "T4 Lant ROST".TX_CW01_BW   DB56.DBX39.1 -- TX Cuvant Control 1: Inapoi
=     "DB:OPOUT".L070             DB82.DBX8.5  -- L070-T4 - Lant (rostogolire) - Deplasare Inapoi
```

## Segmento 65: T4-LantRost: Contactor Alimentare Convertizor

```awl
A     "TF4 T10-E102 S35.7"        I217.6        -- T4 Lant Rostogolire Permisie Cuplare Contactor
A     "M:CMD INS 4 OK"            M40.3         -- Zona Emergenta 4: Comenzi Abilitate
AN    "LLALM".DB202_DBX102_2      DB202.DBX102.2 -- 4;CHAIN T4;Lipsa Tensiune de Comanda Lant T4;DI;A1;10;M;K
=     "TF3 T10-K54.5"             Q191.4        -- T4 Lant Rostogolire Contactor Alimentare Convertizor
```

## Segmento 66: T4 ventilator racire motor lant rotogolire

```awl
AN    "M12".S32                   DB112.DBX9.7  -- T4-Lant:Pas 32
A     "M12".PT_Start              DB112.DBX23.3 -- T4-Lant:Prezenta Teava pe Pozitia Start Bancal
L     S5T#30M
SF    T     140
NOP   0
NOP   0
NOP   0
A     T     140
=     "A191.6"                    Q191.6        -- Ventilator racire motor rostogolire
```

## Segmento 67: T4-Lant: Ciclu Rapid: Viteza Referinta Incarcare

```awl
A(
A(
O     "M10".S18                   DB110.DBX8.1  -- T4.1-Role:Pas 18
O     "M10".S19                   DB110.DBX8.2  -- T4.1-Role:Pas 19
O     "M10".S22                   DB110.DBX8.5  -- T4.1-Role:Pas 22
)
A     "M10".PT                    DB110.DBX23.3 -- T4.1-Role:Prezenta Teava
O
A     "M11".S03                   DB111.DBX6.2  -- T4-Excentric:Pas 03
A     "M10".HEADING_PIPE          DB110.DBX23.5 -- T4.1-Role:Teava Pozitionata
O     "M11".S04                   DB111.DBX6.3  -- T4-Excentric:Pas 04
O     "M11".S07                   DB111.DBX6.6  -- T4-Excentric:Pas 07
O     "M11".S10                   DB111.DBX7.1  -- T4-Excentric:Pas 10
O     "M11".S14                   DB111.DBX7.5  -- T4-Excentric:Pas 14
O     "M11".S18                   DB111.DBX8.1  -- T4-Excentric:Pas 18
O     "M11".S22                   DB111.DBX8.5  -- T4-Excentric:Pas 22
)
A     "M12".CHAIN_AUTO_FW         DB112.DBX22.4 -- T4-Lant:Deplasare 'Inainte'
A     "M12".C_F                   DB112.DBX25.7 -- T4-Lant:Cycle Fast One pipe
=     "M12".CF_CHARGE_SPEED       DB112.DBX123.1 -- FAST CYCLE :CHARGE SPEED REF.
```

## Segmento 68: T4-Lant: Ciclu Rapid: Viteza Referinta Descarcare

```awl
A     "M12".TRK_PIPE_Incet        DB112.DBX122.0 -- ONE PIPE IN Incet POSITION
A     "M12".C_F                   DB112.DBX25.7  -- T4-Lant:Cycle Fast One pipe
=     "M12".CF_DISCHARGE_SPEED    DB112.DBX123.2 -- FAST CYCLE :DISCHARGE SPEED REF.
```

## Segmento 69: T4-Lant: Ciclu Rapid: Viteza Referinta 'StandBy'

```awl
A     "M12".BENCH_EMPTY           DB112.DBX23.0 -- T4-Lant:Bancal Gol
AN    "M12".CF_CHARGE_SPEED       DB112.DBX123.1 -- FAST CYCLE :CHARGE SPEED REF.
AN    "M12".CF_DISCHARGE_SPEED    DB112.DBX123.2 -- FAST CYCLE :DISCHARGE SPEED REF.
A     "M12".C_F                   DB112.DBX25.7 -- T4-Lant:Cycle Fast One pipe
=     "M12".CF_STANDBY_SPEED      DB112.DBX123.0 -- FAST CYCLE :STAND-BY SPEED REF.
```

## Segmento 70: T4-Lant: Ciclu Rapid: Viteza Referinta 'Rapid'

```awl
AN    "M12".CF_STANDBY_SPEED      DB112.DBX123.0 -- FAST CYCLE :STAND-BY SPEED REF.
AN    "M12".CF_CHARGE_SPEED       DB112.DBX123.1 -- FAST CYCLE :CHARGE SPEED REF.
AN    "M12".CF_DISCHARGE_SPEED    DB112.DBX123.2 -- FAST CYCLE :DISCHARGE SPEED REF.
A     "M12".C_F                   DB112.DBX25.7 -- T4-Lant:Cycle Fast One pipe
=     "M12".CF_FAST_SPEED         DB112.DBX123.3 -- FAST CYCLE :FAST SPEED REF.
```

## Segmento 71: T4-Lant: Viteza Teava 'Inainte' in Mod Automat [m/min *10]

```awl
A     "M12".CF_DISCHARGE_SPEED    DB112.DBX123.2 -- FAST CYCLE :DISCHARGE SPEED REF.
L     "LIPRE".AIACT.SP028         DB246.DBW254   -- A1:SP028: T4-Lant:Viteza de 'Incarcare' Inainte [m/min]
JC    M005
A     "M12".CF_CHARGE_SPEED       DB112.DBX123.1 -- FAST CYCLE :CHARGE SPEED REF.
L     "LIPRE".AIACT.SP027         DB246.DBW252   -- A1:SP027: T4-Lant:Viteza de 'Incarcare' Inainte [m/min]
JC    M005
A     "M12".CF_FAST_SPEED         DB112.DBX123.3 -- FAST CYCLE :FAST SPEED REF.
L     "LIPRE".AIACT.SP025         DB246.DBW248   -- A1:SP025: T4-Lant:Rapid Inainte [m/min]
JC    M005
A     "M12".CF_STANDBY_SPEED      DB112.DBX123.0 -- FAST CYCLE :STAND-BY SPEED REF.
L     "LIPRE".AIACT.SP026         DB246.DBW250   -- A1:SP026: T4-Lant:Viteza de 'StandBy' Inainte [m/min]
JC    M005
L     "LIPRE".AIACT.SP030         DB246.DBW258   -- A1:SP030: T4: Lant: Viteza Inainte in Mod Automat [rpm]
M005: NOP   0
ITD
DTR
L     1.000000e+001
/R
T     "M12".SPEED_FW_AUTO_MT_MIN  DB112.DBD96   -- T4-Lant:Viteza Teava 'Inainte' AUTO [METER\MINUTE]
```

## Segmento 72: T4-Lant: Viteza Teava 'Inainte' in Mod Automat [rpm]

```awl
L     "M12".SPEED_FW_AUTO_MT_MIN  DB112.DBD96  -- T4-Lant:Viteza Teava 'Inainte' AUTO [METER\MINUTE]
L     1.700000e+000
/R
T     "M12".SPEED_FW_AUTO_ROLL_MIN DB112.DBD100 -- T4-Lant:Viteza Teava 'Inainte' AUTO [ROLL\MINUTE]
```

## Segmento 73: T4-Lant: Viteza Teava 'Inainte' in Mod Automat [rpm] Motor

```awl
L     "M12".SPEED_FW_AUTO_ROLL_MIN DB112.DBD100 -- T4-Lant:Viteza Teava 'Inainte' AUTO [ROLL\MINUTE]
L     3.653400e+002
*R
T     "M12".SPEED_FW_AUTO_RPM     DB112.DBD104 -- T4-Lant:Viteza Teava 'Inainte' AUTO [RPM]
```

## Segmento 74: T4-Lant: Viteza Teava 'Inainte' in Mod Automat [HZ *10]

```awl
L     "M12".SPEED_FW_AUTO_RPM     DB112.DBD104 -- T4-Lant:Viteza Teava 'Inainte' AUTO [RPM]
L     5.000000e+001
*R
L     1.470000e+003
/R
L     1.000000e+001
*R
T     "M12".SPEED_FW_AUTO_HZ      DB112.DBD108 -- T4-Lant:Viteza Teava 'Inainte' AUTO [HZ *10]
```

## Segmento 75: T4-Lant: Viteza Operativa

```awl
AN    "T4 Lant".TX_CW01_FW        DB69.DBX39.0 -- TX Cuvant Control 1: Inainte
AN    "T4 Lant".TX_CW01_BW        DB69.DBX39.1 -- TX Cuvant Control 1: Inapoi
L     0
JC    M003
L     "LIPRE".AIACT.SP031         DB246.DBW260 -- A1:SP031: T4: Lant: Viteza in Mod Manual [rpm]
ITD
DTR
A     "M12".S29                   DB112.DBX9.4 -- T4-Lant:Pas 29
JC    M003
L     "M12".SPEED_FW_AUTO_HZ      DB112.DBD108 -- T4-Lant:Viteza Teava 'Inainte' AUTO [HZ *10]
M003: NOP   0
T     "M12".SPEED_OPERATIVE       DB112.DBD116 -- T4-Lant:Viteza Operativa Teava [HZ *10]
```

## Segmento 76: T4-Lant: Control Viteza Operativa

```awl
L     "M12".SPEED_OPERATIVE       DB112.DBD116 -- T4-Lant:Viteza Operativa Teava [HZ *10]
TRUNC
T     "T4 Lant".TX_CW02_REF       DB69.DBW40   -- TX Cuvant Control 2: Referinta Viteza [HZ x 10]
```

## Segmento 77: T4-Lant: Resetare Convertizor

```awl
A     "DB:OPIN".P004              DB81.DBX0.3  -- P004-Invertere Auxiliare - Reset
=     "T4 Lant".TX_CW01_RESET     DB69.DBX38.4 -- TX Cuvant Control 1: Resetare Avarie Convertizor
```

## Segmento 78: T4-Lant: PLC ON (EVER ONE)

```awl
A     "M:TRUE"                    M0.0         -- Intotdeauna Activ
=     "T4 Lant".TX_CW01_PLC_ON    DB69.DBX38.7 -- TX Cuvant Control 1: PLC ON (EVER 1)
```

## Segmento 79: T4-Lant: Contactor Frana

```awl
A(
O     "M12".FW_ON                 DB112.DBX24.6 -- T4-Lant:FORWARD ON
O     "M12".BW_ON                 DB112.DBX24.7 -- T4-Lant:BACKWARD ON
)
A     "TF3 T10-K52.7-K22.6"       Q190.6        -- T4 Lant Contactor Frana
A(
A     "TF4 T10-E103 K24.5.2"      I215.5        -- T4 Lant Convertizor 'RUN'
A     "M:FALSE"                   M0.1          -- Intotdeauna Inactiv
O(
L     "Lant-T4-RefFbkHz"          MD504         -- FeedBack Referinta Viteza Lant T4 [Hz]
L     1.000000e+000
>R
)
)
L     S5T#1S500MS
SF    T     355
NOP   0
NOP   0
NOP   0
A     T     355
=     "TF3 T10-K52.7-K22.6"       Q190.6        -- T4 Lant Contactor Frana
```

## Segmento 80: T4-Lant: Abilitare Convertizor

```awl
A(
A(
O     "T4 Lant".TX_CW01_FW        DB69.DBX39.0 -- TX Cuvant Control 1: Inainte
O     "T4 Lant".TX_CW01_BW        DB69.DBX39.1 -- TX Cuvant Control 1: Inapoi
)
A(
A     "TF3 T10-K52.7-K22.6"       Q190.6       -- T4 Lant Contactor Frana
O
A     "T4 Lant".TX_CW01_Abilitare DB69.DBX39.7 -- TX Cuvant Control 1: Abilitare
A(
A     "TF4 T10-E103 K24.5.2"      I215.5       -- T4 Lant Convertizor 'RUN'
A     "M:FALSE"                   M0.1         -- Intotdeauna Inactiv
O(
L     "Lant-T4-RefFbkHz"          MD504        -- FeedBack Referinta Viteza Lant T4 [Hz]
L     0.000000e+000
<>R
)
)
)
)
L     S5T#500MS
SD    T     65
NOP   0
NOP   0
NOP   0
A     T     65
=     L     32.0
A     L     32.0
BLD   102
=     "T4 Lant".TX_CW01_Abilitare DB69.DBX39.7 -- TX Cuvant Control 1: Abilitare
A     L     32.0
A     "M:FALSE"                   M0.1          -- Intotdeauna Inactiv
=     "TF3 T10-K55.6"             Q200.5        -- T4 Lant Contactor 'Abilitare'
```

## Segmento 81: Gestiune Semn SetPoint Viteza MicroMaster Lant T4

```awl
L     "M12".SPEED_OPERATIVE       DB112.DBD116 -- T4-Lant:Viteza Operativa Teava [HZ *10]
ABS
L     1.000000e+001
/R
T     "Lant-T4-RefHz"             MD400        -- Referinta Viteza Lant T4 [Hz]
```

## Segmento 82: Gestiune Convertizor MicroMaster Lant T4

```awl
A(
A(
A     "T4 Lant".TX_CW01_Abilitare DB69.DBX39.7 -- TX Cuvant Control 1: Abilitare
L     S5T#3S
SF    T     465
NOP   0
NOP   0
NOP   0
A     T     465
)
=     L     32.0
BLD   103
A     "T4 Lant".TX_CW01_Abilitare DB69.DBX39.7 -- TX Cuvant Control 1: Abilitare
A     "T4 Lant".TX_CW01_BW        DB69.DBX39.1 -- TX Cuvant Control 1: Inapoi
=     L     32.1
BLD   103
A     "PLC-E101-K19.2no"          I12.3         -- Zona 4 Releu Opritoarele Urgenta
=     L     32.2
BLD   103
A     "T4 Lant".TX_CW01_RESET     DB69.DBX38.4 -- TX Cuvant Control 1: Resetare Avarie Convertizor
=     L     32.3
BLD   103
A(
CALL  "LiniarizareNumereReale"    FC38
IN    :="Lant-T4-RefHz"           MD400         -- Referinta Viteza Lant T4 [Hz]
IN_MIN:=0.000000e+000
IN_MAX:=1.000000e+002
OUT_MIN:=0.000000e+000
OUT_MAX:=1.638400e+004
OUT   :="Lant-T4-RefUnit"         MD404         -- Referinta Viteza Lant T4 [Unit]
A     BR
)
JNB   _018
CALL  "MicroMaster PP03"          FC30          -- Inverter management
DB_nr :="Lant T4 (MicroMaster)"    DB40
run   :=L32.0
reverse_rotation:=L32.1
emergency_stop  :=L32.2
reset :=L32.3
First_PQW:=W#16#23C
First_PIW:=W#16#23C
speed_preset    :="Lant-T4-RefUnit" MD404       -- Referinta Viteza Lant T4 [Unit]
act_frequency   :="Lant-T4-RefFbkUnit" MD500    -- FeedBack Referinta Viteza Lant T4 [Unit]
fault :="Lant-T4-Flt"             M300.0        -- Lant T4 Avarie
_018: A     BR
)
JNB   _019
CALL  "LiniarizareNumereReale"    FC38
IN    :="Lant-T4-RefFbkUnit"      MD500         -- FeedBack Referinta Viteza Lant T4 [Unit]
IN_MIN:=0.000000e+000
IN_MAX:=1.638400e+004
OUT_MIN:=0.000000e+000
OUT_MAX:=1.000000e+002
OUT   :="Lant-T4-RefFbkHz"        MD504         -- FeedBack Referinta Viteza Lant T4 [Hz]
_019: NOP   0
```

## Segmento 83: Feedback SetPoint Viteza Lant T4

```awl
L     "Lant-T4-RefFbkHz"          MD504        -- FeedBack Referinta Viteza Lant T4 [Hz]
L     1.000000e+001
*R
TRUNC
T     "T4 Lant".RX_STW01          DB69.DBW0    -- RX Cuvant Stare 1: Frecventa [Hz x10]
```

## Segmento 84: T4-Lant: Scriere Date Interfata Convertizor

```awl
NOP   0
//    L     DB69.DBW0
//    T     "T4-Lant-Drv-CV1"

//    L     "T4 Lant".TX_CW02_REF
//    T     "T4-Lant-Drv-RF"

//    L     0
//    T     "T4-Lant-Drv-003"
//    T     "T4-Lant-Drv-004"
//    T     "T4-Lant-Drv-005"
//    T     "T4-Lant-Drv-006"
```

## Segmento 85: T4-LantRost: Gestiune Convertizor

```awl
```

## Segmento 86: T4-LantRost: Referinta Viteza

```awl
O     "T4 Lant ROST".TX_CW01_FW   DB56.DBX39.0 -- TX Cuvant Control 1: Inainte
O     "T4 Lant ROST".TX_CW01_BW   DB56.DBX39.1 -- TX Cuvant Control 1: Inapoi
L     "LIPRE".AIACT.SP034         DB246.DBW266 -- A1:SP034: T4: Lant Rostogolire: Viteza [rpm]
JC    M001
L     0
M001: NOP   0
T     "T4 Lant ROST".TX_CW02_REF  DB56.DBW40   -- TX Cuvant Control 2: Referinta Viteza [HZ x 10]
```

## Segmento 87: T4-LantRost: Resetare Convertizor

```awl
A     "DB:OPIN".P004              DB81.DBX0.3  -- P004-Invertere Auxiliare - Reset
=     "T4 Lant ROST".TX_CW01_RESET DB56.DBX38.4 -- TX Cuvant Control 1: Resetare Avarie Convertizor
```

## Segmento 88: T4-LantRost: PLC ON (EVER ONE)

```awl
A     "M:TRUE"                    M0.0         -- Intotdeauna Activ
=     "T4 Lant ROST".TX_CW01_PLC_ON DB56.DBX38.7 -- TX Cuvant Control 1: PLC ON (EVER 1)
```

## Segmento 89: T4-LantRost: Lant 'On'

```awl
A(
O     "T4 Lant ROST".TX_CW01_FW   DB56.DBX39.0 -- TX Cuvant Control 1: Inainte
O     "T4 Lant ROST".TX_CW01_BW   DB56.DBX39.1 -- TX Cuvant Control 1: Inapoi
)
L     S5T#500MS
SF    T     350
NOP   0
NOP   0
NOP   0
A     T     350
=     "M12".SPINNING_ON           DB112.DBX22.0 -- T4-Lant:Lant Rostogolire Deplasare 'Inainte'
```

## Segmento 90: T4-LantRost: Abilitare Convertizor

```awl
A(
O     "T4 Lant ROST".TX_CW01_FW   DB56.DBX39.0 -- TX Cuvant Control 1: Inainte
O     "T4 Lant ROST".TX_CW01_BW   DB56.DBX39.1 -- TX Cuvant Control 1: Inapoi
)
A     "TF3 T10-K54.6"             Q191.5       -- T4 Lant Rostogolire Contactor 'Abilitare'
A     "TF4 T10-E102 U17.3(RUN)"   I217.5       -- T4 Lant Rostogolire Convertizor 'RUN'
=     "M12".SPINNING_ON           DB112.DBX22.0 -- T4-Lant:Lant Rostogolire Deplasare 'Inainte'
=     "T4 Lant ROST".TX_CW01_Abilitare DB56.DBX39.7 -- TX Cuvant Control 1: Abilitare
=     "TF3 T10-K54.6"             Q191.5       -- T4 Lant Rostogolire Contactor 'Abilitare'
```

## Segmento 91: T4-LantRost: Scriere Date Interfata Convertizor

```awl
//    L     DB56.DBW    38
//    T     "T4-LantR-Drv-CV1"

//    L     "T4 Lant ROST".TX_CW02_REF
//    T     "T4-LantR-Drv-RF"

//    L     0
//    T     "T4-LantR-Drv-003"
//    T     "T4-LantR-Drv-004"
//    T     "T4-LantR-Drv-005"
//    T     "T4-LantR-Drv-006"
```

## Segmento 92: Trei tev la iesire

```awl
A     "M:TRUE"                    M0.0         -- Intotdeauna Activ
=     L     32.0
A     L     32.0
A(
L     MW    612
L     0
<I
)
JNB   _01a
L     0
T     MW    612
_01a: NOP   0
A     L     32.0
A(
L     MW    612
L     2
>I
)
JNB   _01b
L     2
T     MW    612
_01b: NOP   0
A     L     32.0
A(
L     MW    612
L     2
==I
)
=     "M609.2"                    M609.2       -- Doua tevi la iesire
```

## Segmento 93: Inverter G120 Lant rostogolire T4

```awl
A(
A(
AN(
O     "T4 Lant ROST".TX_CW01_FW   DB56.DBX39.0 -- TX Cuvant Control 1: Inainte
O     "T4 Lant ROST".TX_CW01_BW   DB56.DBX39.1 -- TX Cuvant Control 1: Inapoi
)
=     L     32.0
BLD   103
A     "T4 Lant ROST".TX_CW01_BW   DB56.DBX39.1 -- TX Cuvant Control 1: Inapoi
=     L     32.1
BLD   103
A     "M:CMD INS 4 OK"            M40.3        -- Zona Emergenta 4: Comenzi Abilitate
=     L     32.2
BLD   103
A     "DB:OPIN".P004              DB81.DBX0.3  -- P004-Invertere Auxiliare - Reset
=     L     32.3
BLD   103
A     "M:CMD INS 4 OK"            M40.3        -- Zona Emergenta 4: Comenzi Abilitate
=     L     32.4
BLD   103
CALL  "INVERTER G120"             FC31
DB_nr :="Lant Rost T4"            DB506
run   :=L32.0
reverse_rotation:=L32.1
emergency_stop  :=L32.2
reset :=L32.3
First_PQW:=W#16#48C
First_PIW:=W#16#48C
speed_preset    :="MD750"         MD750         -- Setpoint rostogolire lant T4
EN_ContLinie    :=L32.4
act_frequency   :=#frecv          #frecv
fault :="M729.3"                  M729.3        -- Fault inverter rostogolire lant t4
A     BR
)
JNB   _01c
L     #frecv                       #frecv
L     3.036000e-002
*R
T     #frecvr                      #frecvr
AN    OV
SAVE
CLR
_01c: A     BR
)
JNB   _01d
L     #frecvr                      #frecvr
TRUNC
T     MW    754
_01d: NOP   0
```

## Segmento 94: Titolo:

```awl
A(
A(
L     "T4 Lant ROST".TX_CW02_REF  DB56.DBW40   -- TX Cuvant Control 2: Referinta Viteza [HZ x 10]
ITD
T     #setpoint2                   #setpoint2
SET
SAVE
CLR
A     BR
)
JNB   _01e
L     #setpoint2                   #setpoint2
DTR
T     #setpoint1                   #setpoint1
SET
SAVE
CLR
_01e: A     BR
)
JNB   _01f
L     #setpoint1                   #setpoint1
L     2.000000e+001
*R
T     "MD750"                     MD750         -- Setpoint rostogolire lant T4
_01f: NOP   0
```

## Segmento 95: Titolo:

```awl
A     "T4 Lant".TX_CW01_Abilitare DB69.DBX39.7 -- TX Cuvant Control 1: Abilitare
R     "M12".PT_Start              DB112.DBX23.3 -- T4-Lant:Prezenta Teava pe Pozitia Start Bancal
```
