```awl
FC193 : Titolo:

Segmento 1: Reset Alarme
    A    "M:CLOCK 0.5Hz"
    R    "LLALM".DB202_DBX85_1
    R    "LLXhALM".DB34_DBX85_1

Segmento 2: ----------------------Alarme----------------------
    AN   "Rezerva".EH01.I353_4
    AN   "LLALM".DB202_DBX43_7
    =    "LLALM".DB202_DBX84_6
    =    "LLXhALM".DB34_DBX84_6

Segmento 3: A0661-Disjunctor Frana Lant T10
    AN   "G120_M93_PN".READ2.DI_Inverter.DI_0
    AN   "LLALM".DB202_DBX43_7
    =    "LLALM".DB202_DBX84_5
    =    "LLXhALM".DB34_DBX84_5

Segmento 4: A0657-Probleme Fuzibil Lant T10
    AN   "G120_M93_PN".READ2.DI_Inverter.DI_2
    AN   "LLALM".DB202_DBX43_7
    =    "LLALM".DB202_DBX84_1
    =    "LLXhALM".DB34_DBX84_1

Segmento 5: A0658-Disjunctor Lant T10
    AN   "G120_M93_PN".READ2.DI_Inverter.DI_3
    AN   "LLALM".DB202_DBX43_7
    =    "LLALM".DB202_DBX84_2
    =    "LLXhALM".DB34_DBX84_2

Segmento 6: A0659-Fuzibil Neinserat Lant T10
    AN   "G120_M93_PN".READ2.DI_Inverter.DI_4
    AN   "LLALM".DB202_DBX43_7
    =    "LLALM".DB202_DBX84_3
    =    "LLXhALM".DB34_DBX84_3

Segmento 7: A0660-Convertizor in Fault Lant T10
    A    "M93_Fault"
    AN   "LLALM".DB202_DBX43_7
    =    "LLALM".DB202_DBX84_4
    =    "LLXhALM".DB34_DBX84_4

Segmento 8: A0664-T10-Lant: TimeOut Deplasare Lant
    A    "M:TRUE"
    A(
    O    "M93_Run_FU"
    O    "M93_Run_BU"
    )
    AN   "LLALM".DB202_DBX43_7
    A(
    L    "DB:T10_OPPV".PVR008
    L    0.000000e+000
    <>R
    )
    L    S5T#40S
    SD   T    803
    NOP  0
    NOP  0
    NOP  0
    A    T    803
    =    "LLALM".DB202_DBX85_0
    =    "LLXhALM".DB34_DBX85_0

Segmento 9: A0665-T10-Lant: Comunicatie Intrerupta cu Encoderul
    A    "M:TRUE"
    =    L    30.0
    A    L    30.0
    AN   "LLALM".DB202_DBX43_7
    A(
    L    ID   425
    L    0.000000e+000
    ==R
    )
    L    S5T#100MS
    SD   T    764
    NOP  0
    NOP  0
    NOP  0
    A    T    764
    S    "LLALM".DB202_DBX85_1
    S    "LLXhALM".DB34_DBX85_1
    A    L    30.0
    A    "DB:OPIN".P157
    R    "LLALM".DB202_DBX85_1
    R    "LLXhALM".DB34_DBX85_1

Segmento 10: A0666-T10-Lant:Senzor home nedetectat sau defect
    A    "M:TRUE"
    AN   "LLALM".DB202_DBX43_7
    A(
    L    "DB_Encoder_Baumer_M93".API.ScaledValue
    L    0.000000e+000
    <R
    )
    A(
    L    "DB_Encoder_Baumer_M93".API.ScaledValue
    L    4.500000e+002
    >=R
    )
    =    "LLALM".DB202_DBX85_2
    =    "LLXhALM".DB34_DBX85_2

Segmento 11: A0667-T10-Lant:TimeOut Cuplare/Decuplare Alim.Inv. Lant T10
    A(
    A    "G120_M93_PN".READ2.DI_Inverter.DI_1
    AN   "G120_M93_PN".Write_DQ_Inverter.DQ_0
    O
    AN   "G120_M93_PN".READ2.DI_Inverter.DI_1
    A    "G120_M93_PN".Write_DQ_Inverter.DQ_0
    )
    L    S5T#10S
    SD   T    771
    NOP  0
    NOP  0
    NOP  0
    A    T    771
    =    "LLALM".DB202_DBX85_3
    =    "LLXhALM".DB34_DBX85_3

Segmento 12: A0668-T10-Lant:TimeOut Deplasare Lant T10 in Pozitia Pas
    A    "M93_Run_FU"
    AN   "M93".Step
    L    S5T#40S
    SD   T    772
    NOP  0
    NOP  0
    NOP  0
    A    T    772
    =    "LLALM".DB202_DBX85_4
    =    "LLXhALM".DB34_DBX85_4

Segmento 13: A0669-T10-Lant:Eroare Depozitare Teava pe Opritor dupa Lant
    AN   "M93".PT_END
    A    "M93".MEM_PT_END
    L    S5T#30S
    SD   T    773
    NOP  0
    NOP  0
    NOP  0
    A    T    773
    =    "LLALM".DB202_DBX85_5
    =    "LLXhALM".DB34_DBX85_5

Segmento 14: A0670-T10-Lant:TimeOut Cuplare/Decuplare Frana Lant
    A    "M:TRUE"
    A(
    AN
    O    "M93_Run_FU"
    O    "M93_Run_BU"
    )
    AN   "G120_M93_PN".READ2.DI_Inverter.DI_5
    O
    AN   "M93_Run_FU"
    AN   "M93_Run_BU"
    AN   "G120_M93_PN".READ2.DI_Inverter.DI_5
    L    S5T#30S
    SD   T    774
    NOP  0
    NOP  0
    NOP  0
    A    T    774
    =    "LLALM".DB202_DBX85_6
    =    "LLXhALM".DB34_DBX85_6

Segmento 15: ---------------- Cumulativ Alarme ----------------
    A    "M:TRUE"
    A(
    O    "LLALM".DB202_DBX43_7
    O    "LLALM".DB202_DBX45_0
    O    "LLALM".DB202_DBX45_1
    O    "LLALM".DB202_DBX45_2
    O    "LLALM".DB202_DBX45_3
    O    "LLALM".DB202_DBX45_4
    O    "LLALM".DB202_DBX46_1
    O    "LLALM".DB202_DBX46_2
    O    "LLALM".DB202_DBX46_3
    O    "LLALM".DB202_DBX46_4
    O    "LLALM".DB202_DBX46_5
    O    "LLALM".DB202_DBX46_6
    O    "LLALM".DB202_DBX84_0
    O    "LLALM".DB202_DBX84_1
    O    "LLALM".DB202_DBX84_2
    O    "LLALM".DB202_DBX84_3
    O    "LLALM".DB202_DBX84_4
    O    "LLALM".DB202_DBX84_5
    O    "LLALM".DB202_DBX84_6
    O    "LLALM".DB202_DBX84_7
    O    "LLALM".DB202_DBX85_0
    O    "LLALM".DB202_DBX85_1
    O    "LLALM".DB202_DBX85_2
    O    "LLALM".DB202_DBX85_3
    O    "LLALM".DB202_DBX85_4
    O    "LLALM".DB202_DBX85_5
    O    "LLALM".DB202_DBX85_6
    )
    AN   "M:FORCE"
    =    "M93".EM

Segmento 16: T10-Lant: Prezenta Teava pe Pozitia de Start de pe Bancal Cap
    A    "M:TRUE"
    =    L    30.0
    A    L    30.0
    A(
    O    "Rezerva".EH01.I355_6
    O    "Rezerva".EH01.I355_7
    O    "Rezerva".EH01.I361_2
    O    "Rezerva".EH01.I361_4
    )
    L    S5T#250MS
    SF   "T800"
    NOP  0
    NOP  0
    A    "T800"
    S    "M79.4"
    A    L    30.0
    A    "M79.4"
    A    "M93".PT_Start
    A    L    30.0
    A    "DB:T10_OPIN".P007
    R    "M79.4"

Segmento 17: T10-Lant: Prezenta Teava pe Pozitia de 'Incetinire' de pe Bancal
    A    "M:TRUE"
    =    L    30.0
    A    L    30.0
    A(
    O    "Rezerva".EH01.I356_2
    O    "Rezerva".EH01.I356_3
    O    "Rezerva".EH01.I359_3
    O    "Rezerva".EH01.I359_5
    )
    L    S5T#200MS
    SF   T    754
    NOP  0
    NOP  0
    A    T    754
    =    "M93".PT_RALL
    S    "M79.1"
    A    L    30.0
    A    "DB:T10_OPIN".P007
    R    "M79.1"

Segmento 18: Decelare New
    A(
    O    "Dec_L1"
    O    "Dec_L2"
    O    "Dec_L3"
    O    "Dec_L4"
    O    "Dec_L5"
    )
    A    "M:TRUE"
    L    S5T#100MS
    SF   T    808
    NOP  0
    NOP  0
    A    T    808
    =    "PasDecelLantT10"

Segmento 19: Stop New
    A(
    O    "Stop_L1"
    O    "Stop_L2"
    O    "Stop_L3"
    O    "Stop_L4"
    O    "Stop_L5"
    )
    A    "M:TRUE"
    L    S5T#100MS
    SF   T    804
    NOP  0
    NOP  0
    A    T    804
    =    "PasStopLantT10"

Segmento 20: T10-Lant: Lant in Pozitia 'Pas'
    A(
    AN   "T10_Pas_1_Lant_Err"
    A    "T10_Pas_1_Lant"
    O
    AN   "T10_Pas_2_Lant_Err"
    A    "T10_Pas_2_Lant"
    O
    AN   "T10_Pas_3_Lant_Err"
    A    "T10_Pas_3_Lant"
    O
    AN   "T10_Pas_4_Lant_Err"
    A    "T10_Pas_4_Lant"
    O
    AN   "T10_Pas_5_Lant_Err"
    A    "T10_Pas_5_Lant"
    )
    A    "Test_Stop"
    A    "M:TRUE"
    O
    A    "PasStopLantT10"
    A    "Test_Stop"
    =    L    30.0
    A(
    A    L    30.0
    L    S5T#50MS
    SD   T    805
    NOP  0
    NOP  0
    A    "T805"
    )
    L    S5T#50MS
    SF   T    806
    NOP  0
    NOP  0
    A    T    806
    =    L    30.1
    A    L    30.1
    FP   "M93".OS_Step
    R    "M79.4"
    S    "M112.1"
    A    L    30.1
    BLD  102
    =    "M93".Step
    A    L    30.0
    BLD  102
    L    S5T#950MS
    SF   T    807

Segmento 21: T10-Lant: Lant in pas Okay pentru Incarcare
    A    "M:TRUE"
    A(
    L    "DB_Encoder_Baumer_M93".API.ScaledValue
    L    7.400000e+001
    <=R
    )
    A(
    L    "DB_Encoder_Baumer_M93".API.ScaledValue
    L    6.000000e+001
    >=R
    )
    O
    A(
    L    "DB_Encoder_Baumer_M93".API.ScaledValue
    L    1.460000e+002
    <=R
    )
    A(
    L    "DB_Encoder_Baumer_M93".API.ScaledValue
    L    1.420000e+002
    >=R
    )
    O
    A(
    L    "DB_Encoder_Baumer_M93".API.ScaledValue
    L    2.180000e+002
    <=R
    )
    A(
    L    "DB_Encoder_Baumer_M93".API.ScaledValue
    L    2.140000e+002
    >=R
    )
    O
    A(
    L    "DB_Encoder_Baumer_M93".API.ScaledValue
    L    2.900000e+002
    <=R
    )
    A(
    L    "DB_Encoder_Baumer_M93".API.ScaledValue
    L    2.860000e+002
    >=R
    )
    O
    A(
    L    "DB_Encoder_Baumer_M93".API.ScaledValue
    L    3.620000e+002
    <=R
    )
    A(
    L    "DB_Encoder_Baumer_M93".API.ScaledValue
    L    3.580000e+002
    >=R
    )
    =    M    75.3

Segmento 22: T10-Lant: Prezenta Teava pe Ultima Pozitie de pe Bancal
    A    "M:TRUE"
    A(
    O    "Rezerva".EH01.I358_1
    AN   "M:FORCE"
    A    "Rezerva".EH01.I358_2
    O    "Rezerva".EH01.I359_4
    O    "Rezerva".EH01.I359_6
    )
    L    S5T#500MS
    SD   T    777
    NOP  0
    NOP  0
    A    T    777
    L    S5T#200MS
    SF   T    801
    NOP  0
    NOP  0
    A    T    801
    =    "M93".PT_END
    R    "M79.1"
    S    "M93".MEM_PT_END

Segmento 23: T10-Lant: TRK: Prezenta Teava pe pozitia 'Incetinire' pe Bancal
    A    "M93".PT_RALL
    FP   "M93_AUX_PIPE_IN"
    S    "M93_TRK_PIPE_In"

Segmento 24: T10-Lant: Teava Prezenta pe 'Ultima' Pozitie Bancal
    A(
    O    "M93".S02
    O    "DB:T10_OPOUT".L047
    )
    AN   "M93".PT_END
    O    "DB:T10_OPIN".P007
    R    "M93".MEM_PT_END

Segmento 25: T10-Lant: Teava Prezenta pe 'Ultima' Pozitie Bancal
    A    "M:TRUE"
    =    L    30.0
    A    L    30.0
    A    "M93".PT_END
    R    "M93_TRK_PIPE_LAST"
    A    L    30.0
    A    "M93_TRK_PIPE_In"
    A    "M93_TRK_PIPE_LAST"
    A    L    30.0
    AN   "M93".PT_RALL
    A    "M93".PT_END
    FP   "M93".OS_PT_END
    R    "M93_TRK_PIPE_In"
    A    L    30.0
    A    "DB:T10_OPIN".P007
    R    "M93_TRK_PIPE_In"
    R    "M93_TRK_PIPE_LAST"

Segmento 26: T10-Lant: TRK: Teava in Pozitia 'Descarcare'
    O    "M93".PT_RALL
    O    "M93".MEM_PT_END
    O    "M93".PT_END
    O    "M93_TRK_PIPE_In"
    =    "M93".TRK_PIPE_Incet

Segmento 27: T10-Lant: Teava Pregatita pt. 'Incarcare'
    A(
    O    "Rezerva".EH01.I355_1
    O    "Rezerva".EH01.I355_2
    O    "Rezerva".EH01.I355_4
    )
    A    "M91".S14
    A    "M92".S03
    =    "M93".PIPE_TO_CHARGE

Segmento 28: T10-Lant: TRK: Deplaseaza Lant in 'Pas'
    A    "M93".OS_Chain_Step
    AN   "M93".BENCH_EMPTY
    JNB  _001
    L    "M93".COUNT_STEP
    L    1
    +I
    T    "M93".COUNT_STEP
_001: NOP 0

Segmento 29: T10-Lant: AUX:Bancal Gol
    A(
    O    "M93".PT_Start
    O    "M:T10:Start:Cycle"
    )
    JNB  _002
    L    0
    T    "M93".COUNT_STEP
_002: NOP 0

Segmento 30: T10-Lant: AUX:Bancal Gol
    L    "M93".COUNT_STEP
    L    27
    >=I
    =    "M93".BENCH_EMPTY

Segmento 31: T10-Lant: Ciclu Selectat
    A    "M:TRUE"
    =    L    30.0
    A    L    30.0
    A(
    L    "DB:T10_OPSP".SPI001
    L    0
    ==I
    )
    =    "M93".C_PT
    A    L    30.0
    A(
    L    "DB:T10_OPSP".SPI001
    L    1
    ==I
    )
    =    "M93".C_TO
    A    L    30.0
    A(
    L    "DB:T10_OPSP".SPI001
    L    2
    ==I
    )
    =    "M93".C_E
    A    L    30.0
    A(
    L    "DB:T10_OPSP".SPI001
    L    3
    ==I
    )
    =    "M93".C_F

Segmento 32: Gestiune C4
    A    "M93".Step
    FP   M    73.7
    CD   "C4"
    BLD  101
    A(
    O    "M92".S08
    O    M    75.1
    )
    FP   M    74.0
    L    C#2
    S    "C4"
    A    "M93".S29
    R    "C4"
    NOP  0
    NOP  0
    NOP  0

Segmento 33: T10-Lant: Calcul TimeOut
    L    "DB13:RX-Q".IN1
    L    "LIPRE".AIACT.SP090
    +I
    T    #AUXI

Segmento 34: T10-Lant: TimeOut Bancal
    O(
    L    #AUXI
    L    999
    >I
    )
    O(
    L    #AUXI
    L    1
    <I
    )
    JC   _018
    L    #AUXI
    ITB
_018: NOP 0
    L    W#16#2000
    OW
    T    #AUXT

Segmento 35: T10-Lant: AUX:TimeOut Bancal (IF 1 START CHAIN)
    A(
    A    "M93".S03
    L    S5T#500MS
    SD   T    834
    NOP  0
    NOP  0
    A    T    834
    )
    A    "M93".C_TO
    AN   "M91".HEADING_PIPE_CAP
    AN   "M91".PT
    =    L    30.0
    A    L    30.0
    L    #AUXT
    SD   T    843
    NOP  0
    NOP  0
    A    T    843
    =    "M93".Time_Out_Bench
    JNB  _003
    L    #AUXT
    T    MW   146
_003: NOP 0

Segmento 36: T10-Lant: ----------------------------------------------------

Segmento 37: T10-Lant: Flag di condizione di inizio ciclo
    A    "M:TRUE"
    A    "DB:T10_OPOUT".L075
    A    "DB:T10_OPOUT".L076
    A    "DB:T10_OPOUT".L077
    AN   "M93_Fault"
    =    "M93".IC

Segmento 38: T10-Lant: Flag di condizione di "starting conditions"
    A    "M93".IC
    =    "M93".STC

Segmento 39: T10-Lant: Flag di condizione macchine limitrofe
    A    "M93".STC
    =    "M93".ML

Segmento 40: T10-Lant: START SEQ
    A    "M:TRUE"
    A    "M93".S29
    A(
    O    "M:T10 Semiautomat"
    O    "M:T10:Auto"
    )
    A    "Rezerva".EH01.I350_0
    AN   "M:T10:Man"
    JNB  _004
    L    1
    T    "M93".Trs
_004: NOP 0

Segmento 41: T10-Lant: S01 - Start
    A    "M93".S01
    A(
    O    "M:T10:Auto"
    O    "M:T10 Semiautomat"
    )
    JNB  _005
    L    2
    T    "M93".Trs
_005: NOP 0

Segmento 42: T10-Lant: S02 - Verificare conditii initiale
    A    "M93".S02
    A(
    A    "DB:T10_OPIN".P003
    A    "M93".STC
    O
    A    "M:T10 Semiautomat"
    A    "DB:T10_OPIN".P030
    )
    JNB  _006
    L    3
    T    "M93".Trs
_006: NOP 0

Segmento 43: T10-Lant: S03 - Verificare conditii de start
    A(
    A(
    O    "M93".PT_Start
    O    "M93".Time_Out_Bench
    )
    A(
    O    "M93".C_E
    O    "M93".C_F
    )
    AN   "M93".PIPE_TO_CHARGE
    )
    A(
    ON   "M92_RunFU"
    AN   "M92".S08
    A    "M:FALSE"
    )
    A(
    AN   "M93".PT_END
    ON   "M93".MEM_PT_END
    AN   "M93_TRK_PIPE_In"
    AN   "M93".PT_END
    )
    A    "M94".S03
    O    "DB:T10_OPOUT".L048
    O
    A    "M:T10 Semiautomat"
    A    "DB:T10_OPIN".P030
    )
    A(
    A    "M93".S03
    A(
    A    "FK Ready"
    O    "Rezerva".EH01.I359_1
    )
    A    "M93".PT_END
    )
    =    L    30.0
    A    L    30.0
    JNB  _007
    L    8
    T    "M93".Trs
_007: NOP 0
    A    L    30.0
    AN   "M:TRUE"
    R    "M79.4"

Segmento 44: T10-Lant: S08: Comanda Inainte
    A    "M93".S08
    =    L    30.0
    A    L    30.0
    A(
    AN   "Test_Stop"
    A    "M93".Step
    O
    A    "Test_Stop"
    A    "PasDecelLantT10"
    )
    JNB  _008
    L    10
    T    "M93".Trs
_008: NOP 0
    A    L    30.0
    A(
    O    "M93".MEM_PT_END
    O    "M93".C_E
    AN   "M:FORCE"
    A    "M93".C_F
    )
    A    "PasDecelLantT10"
    AN   "M:T10 Semiautomat"
    A    "M93_TRK_PIPE_In"
    JNB  _009
    L    14
    T    "M93".Trs
_009: NOP 0

Segmento 45: T10-Lant: S10: Comanda Inainte
    A    "M93".S10
    =    L    30.0
    A    L    30.0
    A(
    AN   "Test_Stop"
    AN   "M93".Step
    O
    A    "Test_Stop"
    A    "PasStopLantT10"
    )
    =    L    30.1
    A    L    30.1
    JNB  _00a
    L    12
    T    "M93".Trs
_00a: NOP 0
    A    L    30.1
    ON   "DB:T10_OPOUT".L048
    O    "M93".PT_END
    JNB  _00b
    L    3
    T    "M93".Trs
_00b: NOP 0
    A    L    30.0
    A(
    O    "M93".MEM_PT_END
    O    "M93".C_E
    AN   "M:FORCE"
    A    "M93".C_F
    )
    A    "PasDecelLantT10"
    AN   "M:T10 Semiautomat"
    A    "M93_TRK_PIPE_In"
    JNB  _00c
    L    14
    T    "M93".Trs
_00c: NOP 0

Segmento 46: T10-Lant: S12: Comanda Inainte
    A    "M93".S12
    =    L    30.0
    A    L    30.0
    A(
    AN   "M93".C_TO
    AN   "M93".C_F
    AN   "M93".C_E
    O
    A    "M93".C_TO
    AN   "C4"
    )
    =    L    30.1
    A    L    30.1
    AN   "M93".MEM_PT_END
    JNB  _00d
    L    3
    T    "M93".Trs
_00d: NOP 0
    A    L    30.1
    A(
    O    "M93".PT_END
    O    "M93".MEM_PT_END
    )
    JNB  _00e
    L    16
    T    "M93".Trs
_00e: NOP 0
    A    L    30.0
    A    "M:TRUE"
    =    L    30.1
    A    L    30.1
    A(
    O    "M93".C_F
    O    "M93".C_E
    O
    A    "M93".C_TO
    A    "C4"
    )
    =    L    30.2
    A    L    30.2
    AN   "M93".PIPE_TO_CHARGE
    =    L    30.3
    A    L    30.3
    A(
    A    "M94".S03
    ON   "DB:T10_OPOUT".L048
    )
    JNB  _00f
    L    3
    T    "M93".Trs
_00f: NOP 0
    A    L    30.3
    A(
    A    "M94".S03
    O    "DB:T10_OPOUT".L048
    )
    =    L    30.4
    A    L    30.4
    AN   "M93".PT_END
    AN   "M93".MEM_PT_END
    JNB  _010
    L    8
    T    "M93".Trs
_010: NOP 0
    A    L    30.4
    A(
    O    "M93".PT_END
    O    "M93".MEM_PT_END
    )
    JNB  _011
    L    16
    T    "M93".Trs
_011: NOP 0
    A    L    30.3
    AN   "M93".PT_RALL
    AN   "M93_TRK_PIPE_LAST"
    JNE  _012
    L    8
    T    "M93".Trs
_012: NOP 0
    A    L    30.2
    A    "M93".PIPE_TO_CHARGE
    JNE  _013
    L    3
    T    "M93".Trs
_013: NOP 0
    A    L    30.1
    A(
    O    "M93".MEM_PT_END
    O    "M93".C_E
    AN   "M:FORCE"
    A    "M93".C_F
    )
    A    "PasDecelLantT10"
    AN   "PasStopLantT10"
    AN   "M:T10 Semiautomat"
    A    "M93_TRK_PIPE_In"
    JNE  _014
    L    14
    T    "M93".Trs
_014: NOP 0

Segmento 47: T10-Lant: S14: Viteza Mica
    A    "M93".S14
    A(
    O    "PasStopLantT10"
    O
    AN   "M:FORCE"
    A    "M93".MEM_PT_END
    O
    AN   "M:FORCE"
    A    "M93".PT_END
    )
    JNE  _015
    L    3
    T    "M93".Trs
_015: NOP 0

Segmento 48: T10-Lant: S16: Restart Seq
    A(
    O    "M93".PT_END
    O    "M93".MEM_PT_END
    )
    A    "M93".S16
    JNB  _016
    L    3
    T    "M93".Trs
_016: NOP 0

Segmento 49: T10-Lant: S29 - Manual Mode
    A    "M:T10:Man"
    JNB  _017
    L    29
    T    "M93".Trs
_017: NOP 0

Segmento 50: T10-Lant: S32 - Emergency Mode
    A    "M93".EM
    JNB  _019
    L    32
    T    "M93".Trs
_019: NOP 0

Segmento 51: T10-Lant: Function management sequencer
    A(
    L    93
    T    "M93".Seq
    SET
    SAVE
    CLR
    A    BR
    )
    JNB  _01a
    CALL "Secventiator cu 128 Pasi"
         DBs := "M93"
         TIM := T193
_01a: NOP 0

Segmento 52: T10-Lant: Mec.93 - Lant: Cuplare CT linie convertizor
    A    "Rezerva".EH01.I350_0
    A    "DB:T10_OPOUT".L076
    =    "G120_M93_PN".Write_DQ_Inverter.DQ_0

Segmento 53: M:Aux Oprire Lant In Pas In Mod Manual
    A    "M:TRUE"
    =    L    30.0
    A    L    30.0
    FP   "PasStopLantT10"
    S    "M82.7"
    A    L    30.0
    A    "DB:T10_OPIN".P031
    FP   "p_edge"
    R    "M82.7"

Segmento 54: T10-Lant: Comenzi Inainte
    A    "M93".S29
    A    "DB:T10_OPIN".P031
    AN   "M82.7"
    AN   "M93_Run_BU"
    O    "M93".S08
    O    "M93".S10
    O    "M93".S12
    O    "M93".S14
    =    "M93_Run_FU"

Segmento 55: T10-Lant: Comenzi Inapoi
    A    "M93".S29
    A    "DB:T10_OPIN".P032
    AN   "M93_Run_FU"
    =    "M93_Run_BU"

Segmento 56: T10-Lant: Logica Blocare / Deblocare FRANA
    A    "M:TRUE"
    =    L    30.0
    A    L    30.0
    A    "M93_Frana"
    =    "Aux_CMD_Frana_M93"
    A    L    30.0
    A    "M93".S29
    =    L    30.1
    A    L    30.1
    A    "DB:T10_OPIN".P034
    S    "M93_Frana"
    A    L    30.1
    A    "DB:T10_OPIN".P035
    R    "M93_Frana"
    A    L    30.0
    A    "M:T10:Man"
    FP   M    68.4
    R    "M93_Frana"
    A    L    30.0
    AN   "M:T10:Man"
    FP   M    68.5
    R    "M93_Frana"
    A    L    30.0
    A    "M93".S29
    FP   M    68.6
    R    "M93_Frana"
    A    L    30.0
    AN   "M93".S29
    FP   M    68.7
    R    "M93_Frana"
    A    L    30.0
    A    "M93".S32
    R    "M93_Frana"
Segmento 57: T10-Lant: Comanda Blocare / Deblocare FRANA
    A    "M:TRUE"
    =    L    30.0
    A    L    30.0
    A    "Aux_CMD_Frana_M93"
    =    "G120_M93_PN".Write_DQ_Inverter.CMD_Brake
    A    L    30.0
    A    "G120_M93_PN".READ2.DI_Inverter.DI_5
    L    S5T#300MS
    SD   T    558
    NOP  0
    NOP  0
    NOP  0
    A    T    558
    =    "DB:T10_OPOUT".L080

Segmento 58: T10-Lant: Verificare SP in MAN
    A    "M:TRUE"
    =    L    30.0
    A    L    30.0
    A(
    L    "DB:T10_OPSP".SPR04
    L    0.000000e+000
    <R
    )
    JNB  _01b
    L    0.000000e+000
    T    "DB:T10_OPSP".SPR04
_01b: NOP  0
    A    L    30.0
    A(
    L    "DB:T10_OPSP".SPR04
    L    5.000000e+001
    >R
    )
    JNB  _01c
    L    5.000000e+001
    T    "DB:T10_OPSP".SPR04
_01c: NOP  0

Segmento 59: T4-Lant: Ciclu Rapid: Viteza Referinta Incarcare
    A(
    A(
    O    "M91".S10
    O    "M91".S20
    )
    A    "M91".PT
    O
    A    "M92".S03
    A    "M91".HEADING_PIPE_CAP
    O    "M92".S08
    O    "M92".S10
    )
    A    "M93_Run_FU"
    A    "M93".C_F
    =    "M93".CF_CHARGE_SPEED

Segmento 60: T10-Lant: Ciclu Rapid: Viteza Referinta Descarcare
    A    "M93".TRK_PIPE_Incet
    A    "M93".C_F
    =    "M93".CF_DISCHARGE_SPEED

Segmento 61: T10-Lant: Ciclu Rapid: Viteza Referinta StandBy
    A    "M93".BENCH_EMPTY
    AN   "M93".CF_CHARGE_SPEED
    AN   "M93".CF_DISCHARGE_SPEED
    A    "M93".C_F
    =    "M93".CF_STANDBY_SPEED

Segmento 62: T10-Lant: Ciclu Rapid: Viteza Referinta 'Rapid'
    AN   "M93".CF_STANDBY_SPEED
    AN   "M93".CF_CHARGE_SPEED
    AN   "M93".CF_DISCHARGE_SPEED
    A    "M93".C_F
    =    "M93".CF_FAST_SPEED

Segmento 63: T10-Lant: Viteza Teava 'Inainte' in Mod Automat [%]
    A    "M93".CF_DISCHARGE_SPEED
    L    "L1PRE".AIACT.SP095
    L    1
    /I
    JC   _02
    A    "M93".CF_CHARGE_SPEED
    L    "L1PRE".AIACT.SP094
    L    1
    /I
    JC   _02
    A    "M93".CF_FAST_SPEED
    L    "L1PRE".AIACT.SP092
    L    1
    /I
    JC   _02
    A    "M93".CF_STANDBY_SPEED
    L    "L1PRE".AIACT.SP093
    L    1
    /I
    JC   _02
    L    "L1PRE".AIACT.SP088
    L    1
    /I
_02: NOP  0
    ITD
    DTR
    T    "M93".SPEED_FW_AUTO_Hz
    L    "M93".SPEED_FW_AUTO_Hz
    L    5.000000e+001
    *R
    T    "M93".SPEED_FW_AUTO_Hz
    L    "M93".SPEED_FW_AUTO_Hz
    L    1.000000e+002
    /R
    T    "M93".SPEED_FW_AUTO_Hz
    L    "L1PRE".AIACT.SP089
    L    1
    /I
    ITD
    DTR
    L    5.000000e+001
    *R
    L    1.000000e+002
    /R
    T    #TMP_Viteza_Man

Segmento 64: T10-Lant: Comenzi - Setpoint
    A    "M:TRUE"
    JNB  _01d
    L    0.000000e+000
    T    "DB:T10_OPPV".PVR010
    SET
    SAVE
    CLR
_01d: A    BR
    =    L    30.0
    A    L    30.0
    A    "M93".S29
    =    L    30.1
    A    L    30.1
    A    "M93_Run_FU"
    =    L    30.2
    JNB  _01e
    L    #TMP_Viteza_Man
    T    "DB:T10_OPPV".PVR010
_01e: NOP  0
    A    L    30.2
    A    "PasDecelLantT10"
    JNB  _01f
    L    5.000000e+000
    T    "DB:T10_OPPV".PVR010
_01f: NOP  0
    A    L    30.1
    A    "M93_Run_BU"
    JNB  _020
    L    #TMP_Viteza_Man
    L    -1.000000e+000
    *R
    T    "DB:T10_OPPV".PVR010
_020: NOP  0
    A(
    A    L    30.0
    A    "M93".S08
    A(
    AN   "M79.1"
    AN   "M93".PT_END
    AN   "M93_TRK_PIPE_In"
    A    "M:TRUE"
    )
    JNB  _021
    L    "M93".SPEED_FW_AUTO_Hz
    T    "DB:T10_OPPV".PVR010
    SET
    SAVE
    CLR
_021: A    BR
    )
    JNB  _022
    L    "DB:T10_OPPV".PVR010
    L    1.200000e+000
    *R
    T    "DB:T10_OPPV".PVR010
_022: NOP  0
    A    L    30.0
    A(
    O    "M93".S10
    O    "M93".S12
    )
    =    L    30.1
    A    L    30.1
    A(
    AN   "M93".C_E
    AN   "M93".C_F
    O    "M:T10 Semiautomat"
    )
    JNB  _023
    L    5.000000e+000
    T    "DB:T10_OPPV".PVR010
_023: NOP  0
    A(
    A    L    30.1
    A(
    O    "M93".C_E
    O    "M93".C_F
    )
    AN   "M:T10 Semiautomat"
    )
    JNB  _024
    L    "M93".SPEED_FW_AUTO_Hz
    T    "DB:T10_OPPV".PVR010
    SET
    SAVE
    CLR
_024: A    BR
    )
    JNB  _025
    L    "DB:T10_OPPV".PVR010
    L    1.200000e+000
    *R
    T    "DB:T10_OPPV".PVR010
_025: NOP  0
    A    L    30.0
    A(
    O    "M93".S14
    O    "M93".S16
    )
    JNB  _026
    L    5.000000e+000
    T    "DB:T10_OPPV".PVR010
_026: NOP  0

Segmento 65: T10-Lant: Liniarizare setpoint
    CALL "LiniarizareNumereReale"
         IN      := "DB:T10_OPPV".PVR010
         IN_MIN  := 0.000000e+000
         IN_MAX  := 5.000000e+001
         OUT_MIN := 0.000000e+000
         OUT_MAX := 1.638400e+004
         OUT     := #Temp_Setpoint_R
    NOP  0

Segmento 66: T10-Lant: Functie convertizor
    A(
    O    "M93_Run_FU"
    O    "M93_Run_BU"
    )
    =    L    30.0
    BLD  103
    A    "M:FALSE"
    =    L    30.1
    BLD  103
    A    "Rezerva".EH01.I350_0
    =    L    30.2
    BLD  103
    A    "DB:OPIN".P004
    =    L    30.3
    BLD  103
    CALL "INVERTER_G120_PN_NEW"
         DB_nr            := "G120_M93_PN"
         run              := L30.0
         reverse_rotation := L30.1
         emergency_stop   := L30.2
         reset            := L30.3
         First_PQW        := W#16#41A
         First_PIW        := W#16#41A
         speed_preset     := #Temp_Setpoint_R
         act_frequency    := #Temp_Freq_R
         fault            := "M93_Fault"
    NOP  0

Segmento 67: T10-Lant: Liniarizare actual frequency
    CALL "LiniarizareNumereReale"
         IN      := #Temp_Freq_R
         IN_MIN  := 0.000000e+000
         IN_MAX  := 1.638400e+004
         OUT_MIN := 0.000000e+000
         OUT_MAX := 5.000000e+001
         OUT     := "DB:T10_OPPV".PVR008
    NOP  0

Segmento 68: T10-Lant: Liniarizare Actual Current
    A(
    A(
    L    "G120_M93_PN".READ2.ACT_CURRENT
    ITD
    T    #Temp_DI
    SET
    SAVE
    CLR
    A    BR
    )
    JNB  _027
    L    #Temp_DI
    DTR
    T    #Temp_R
    SET
    SAVE
    CLR
_027: A    BR
    )
    JNB  _028
    CALL "LiniarizareNumereReale"
         IN      := #Temp_R
         IN_MIN  := 0.000000e+000
         IN_MAX  := 1.638400e+004
         OUT_MIN := 0.000000e+000
         OUT_MAX := 2.250000e+001
         OUT     := "DB:T10_OPPV".PVR009
_028: NOP  0

Segmento 69: T10-Lant: Preset Encoder
    A    "M:TRUE"
    =    L    30.0
    A    L    30.0
    A(
    O    "DB:T10_OPIN".P033
    O    "DB:T10_OPOUT".L081
    )
    FP   M    69.0
    JNB  _029
    L    "DB:T10_OPSP".SPR05
    T    "DB_Encoder_Baumer_M93".API.PresetValue
    SET
    SAVE
    CLR
_029: A    BR
    =    "DB:T10_OPOUT".L082
    A    L    30.0
    A    "DB:T10_OPOUT".L082
    FP   M    69.1
    =    "DB_Encoder_Baumer_M93".API.Sincro

Segmento 70: T10-Lant: Encoder
    A    "DB_Encoder_Baumer_M93".API.Sincro
    =    L    30.0
    BLD  103
    A(
    L    ID    425
    T    "DB_Encoder_Baumer_M93".API.EncoderValue
    SET
    SAVE
    CLR
    A    BR
    )
    JNB  _02a
    CALL "ENCODER_Baumer"
         Encoder       := "DB_Encoder_Baumer_M93".API.EncoderValue
         Bit           := 16
         AzzermtEnc    := L30.0
         PresetPosZero := "DB_Encoder_Baumer_M93".API.PresetValue
         KEnc          := -4.394531e-002
         pos_mm_Real   := "DB_Encoder_Baumer_M93".API.ScaledValue
         pos_mm_DINT   := "DB_Encoder_Baumer_M93".API.ScaledValueDINT
         VirtEnc       := "DB_Encoder_Baumer_M93".API.AUX_VirtualEncoder
         Offset        := "DB_Encoder_Baumer_M93".API.AUX_Offset
_02a: NOP  0

Segmento 71: T10-Lant: Encoder 360
    A    "M:TRUE"
    =    L    30.0
    A    "M:TRUE"
    =    L    30.1
    BLD  103
    A    L    30.0
    JNB  _02b
    CALL "ENCVirtualCAM"
         Always_TRUE   := L30.1
         ActPos        := "DB_Encoder_Baumer_M93".API.ScaledValue
         SetPos        := 7.200000e+001
         SetPos_OK     := 5.200000e+001
         TH_Pos_OK     := 5.000000e+000
         Precision     := 1.000000e-002
         Position_OK   := "T10_Pas_1_Lant"
         ActPosVirtual := #Temp_R
         Error         := "T10_Pas_1_Lant_Err"
_02b: NOP  0
    A    "M:TRUE"
    =    L    30.1
    BLD  103
    A    L    30.0
    JNB  _02c
    CALL "ENCVirtualCAM"
         Always_TRUE   := L30.1
         ActPos        := "DB_Encoder_Baumer_M93".API.ScaledValue
         SetPos        := 1.440000e+002
         SetPos_OK     := 1.240000e+002
         TH_Pos_OK     := 5.000000e+000
         Precision     := 1.000000e-002
         Position_OK   := "T10_Pas_2_Lant"
         ActPosVirtual := #Temp_R
         Error         := "T10_Pas_2_Lant_Err"
_02c: NOP  0
    A    "M:TRUE"
    =    L    30.1
    BLD  103
    A    L    30.0
    JNB  _02d
    CALL "ENCVirtualCAM"
         Always_TRUE   := L30.1
         ActPos        := "DB_Encoder_Baumer_M93".API.ScaledValue
         SetPos        := 2.160000e+002
         SetPos_OK     := 1.960000e+002
         TH_Pos_OK     := 5.000000e+000
         Precision     := 1.000000e-002
         Position_OK   := "T10_Pas_3_Lant"
         ActPosVirtual := #Temp_R
         Error         := "T10_Pas_3_Lant_Err"
_02d: NOP  0
    A    "M:TRUE"
    =    L    30.1
    BLD  103
    A    L    30.0
    JNB  _02e
    CALL "ENCVirtualCAM"
         Always_TRUE   := L30.1
         ActPos        := "DB_Encoder_Baumer_M93".API.ScaledValue
         SetPos        := 2.880000e+002
         SetPos_OK     := 2.680000e+002
         TH_Pos_OK     := 5.000000e+000
         Precision     := 1.000000e-002
         Position_OK   := "T10_Pas_4_Lant"
         ActPosVirtual := #Temp_R
         Error         := "T10_Pas_4_Lant_Err"
_02e: NOP  0
    A    "M:TRUE"
    =    L    30.1
    BLD  103
    A    L    30.0
    JNB  _02f
    CALL "ENCVirtualCAM"
         Always_TRUE   := L30.1
         ActPos        := "DB_Encoder_Baumer_M93".API.ScaledValue
         SetPos        := 3.600000e+002
         SetPos_OK     := 3.400000e+002
         TH_Pos_OK     := 5.000000e+000
         Precision     := 1.000000e-002
         Position_OK   := "T10_Pas_5_Lant"
         ActPosVirtual := #Temp_R
         Error         := "T10_Pas_5_Lant_Err"
_02f: NOP  0

Segmento 72: Pas Stop Positionare OK
    A    "M:TRUE"
    =    L    30.0
    A    "M:TRUE"
    =    L    30.1
    BLD  103
    A    L    30.0
    JNB  _030
    CALL "EncoderLant"
         AlTrue          := L30.1
         Actual_Position := "DB_Encoder_Baumer_M93".API.ScaledValue
         Pos_Decelerare  := 5.850000e+001
         Pos_Stop        := 7.200000e+001
         DeadBand        := 8.000000e-001
         PosDecelOK      := "Dec_L1"
         PosStopOK       := "Stop_L1"
_030: NOP  0
    A    "M:TRUE"
    =    L    30.1
    BLD  103
    A    L    30.0
    JNB  _031
    CALL "EncoderLant"
         AlTrue          := L30.1
         Actual_Position := "DB_Encoder_Baumer_M93".API.ScaledValue
         Pos_Decelerare  := 1.350000e+002
         Pos_Stop        := 1.440000e+002
         DeadBand        := 8.000000e-001
         PosDecelOK      := "Dec_L2"
         PosStopOK       := "Stop_L2"
_031: NOP  0
    A    "M:TRUE"
    =    L    30.1
    BLD  103
    A    L    30.0
    JNB  _032
    CALL "EncoderLant"
         AlTrue          := L30.1
         Actual_Position := "DB_Encoder_Baumer_M93".API.ScaledValue
         Pos_Decelerare  := 2.050000e+002
         Pos_Stop        := 2.160000e+002
         DeadBand        := 8.000000e-001
         PosDecelOK      := "Dec_L3"
         PosStopOK       := "Stop_L3"
_032: NOP  0
    A    "M:TRUE"
    =    L    30.1
    BLD  103
    A    L    30.0
    JNB  _033
    CALL "EncoderLant"
         AlTrue          := L30.1
         Actual_Position := "DB_Encoder_Baumer_M93".API.ScaledValue
         Pos_Decelerare  := 2.745000e+002
         Pos_Stop        := 2.880000e+002
         DeadBand        := 8.000000e-001
         PosDecelOK      := "Dec_L4"
         PosStopOK       := "Stop_L4"
_033: NOP  0
    A    "M:TRUE"
    =    L    30.1
    BLD  103
    A    L    30.0
    JNB  _034
    CALL "EncoderLant"
         AlTrue          := L30.1
         Actual_Position := "DB_Encoder_Baumer_M93".API.ScaledValue
         Pos_Decelerare  := 3.465000e+002
         Pos_Stop        := 3.600000e+002
         DeadBand        := 8.000000e-001
         PosDecelOK      := "Dec_L5"
         PosStopOK       := "Stop_L5"
_034: NOP  0
    A    L    30.0
    AN   "Test_Stop"
    S    "Test_Stop"

Segmento 73: T10-Lant: Comanda Racire fortata
    A    "Rezerva".EH01.I350_0
    A(
    A    "M93".S29
    A    "DB:T10_OPIN".P066
    O    "M93".S08
    )
    FP   "M71.3"
    AN   "Rezerva".EH01.Q352_2
    S    M    66.2
    A(
    A    "DB:T10_OPIN".P066
    FP   "M71.5"
    A    "Rezerva".EH01.Q352_2
    O
    A    "M:T10:Auto"
    AN   "M93".S08
    A    M    66.2
    L    S5T#30M
    SD   T    657
    NOP  0
    NOP  0
    NOP  0
    A    T    657
    )
    ON   "Rezerva".EH01.I350_0
    )
    R    M    66.2
    A    M    66.2
    =    "Rezerva".EH01.Q352_2

Segmento 74: T10-Lant: Interfata Panou Operator
    A    "M:TRUE"
    =    L    30.0
    A    L    30.0
    A    "M93_Run_FU"
    A    "G120_M93_PN".READ1.DRIVE_RUNNING
    A(
    L    "DB:T10_OPPV".PVR008
    L    0.000000e+000
    >R
    )
    =    "DB:T10_OPOUT".L083
    A    L    30.0
    AN   "G120_M93_PN".READ1.DRIVE_RUNNING
    =    "DB:T10_OPOUT".L085
    A    L    30.0
    A    "M93_Run_BU"
    A    "G120_M93_PN".READ1.DRIVE_RUNNING
    A(
    L    "DB:T10_OPPV".PVR008
    L    0.000000e+000
    <R
    )
    =    "DB:T10_OPOUT".L084
    A    L    30.0
    A    "DB:T10_OPOUT".L080
    =    "DB:T10_OPOUT".L078
    A    L    30.0
    A    "DB:T10_OPOUT".L080
    AN   "DB:T10_OPOUT".L080
    =    "DB:T10_OPOUT".L079
    A    L    30.0
    A    "DB:T10_OPIN".P030
    A(
    O    "Aux_ModAutomat"
    O    "M:T10 Semiautomat"
    )
    =    "DB:T10_OPOUT".L086
    JNB  _035
    L    "M93".Sta
    T    "DB:T10_OPPV".PVI003
_035: NOP  0

Segmento 75: T10-Lant: Interfata Panou Operator
    A    "M:TRUE"
    =    L    30.0
    A    L    30.0
    A    "G120_M93_PN".READ2.DI_Inverter.DI_4
    =    "DB:T10_OPOUT".L075
    A    L    30.0
    A    "G120_M93_PN".READ2.DI_Inverter.DI_3
    A    "G120_M93_PN".READ2.DI_Inverter.DI_0
    =    "DB:T10_OPOUT".L076
    A    L    30.0
    A    "G120_M93_PN".READ2.DI_Inverter.DI_1
    =    "DB:T10_OPOUT".L077
    A    L    30.0
    A    "Rezerva".EH01.I356_4
    =    "DB:T10_OPOUT".L081
    A    L    30.0
    A    "Rezerva".EH01.I353_5
    =    "DB:T10_OPOUT".L141
    A    L    30.0
    A    "Rezerva".EH01.I361_2
    =    "DB:T10_OPOUT".L171
    A    L    30.0
    A    "Rezerva".EH01.I361_4
    =    "DB:T10_OPOUT".L172
    A    L    30.0
    A    "Rezerva".EH01.I359_3
    =    "DB:T10_OPOUT".L173
    A    L    30.0
    A    "Rezerva".EH01.I359_5
    =    "DB:T10_OPOUT".L174
    A    L    30.0
    A    "Rezerva".EH01.I359_4
    =    "DB:T10_OPOUT".L175
    A    L    30.0
    A    "Rezerva".EH01.I359_6
    =    "DB:T10_OPOUT".L176
    A    L    30.0
    A    "M93_Fault"
    =    "DB:T10_OPOUT".L147

```
