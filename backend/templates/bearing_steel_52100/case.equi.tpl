FILE-00001    09:28    11May26  Wuhu Xinxing Ductile Iron Pipes Co. Ltd    FactSage 8.3
comments
'O' '13'
'TC' 'ATM' 'J' 'NOVPT' 'NOPHYS' 'CUT' '1e-75 1e-75' 'WIN' 'NOTH' '%' 'NOAQUA' 'NOEPH'
'O' '10'
'CXHY' '2' 'NOGIONTK' '2000' 'NODEMO' 'NOVIR' 'DILEX' '1e+7' 'NOG25' 'MINS2'
'O' '7'
'LIM' '250' '10000' '1.000E-35' '1.000E+08' '1.000E-08' '1.000E+35'
'O' '6'
'TRNS' 'TRNUM' '0'  'NOPARA' '' ' 13   1  2  3  4  5  6  7  8  9  10  11  12  13'
'O' '3'
'ISOP' '0' ''
'R' 'NEW'
 {{MASS_Fe}} Fe  +  {{MASS_C}} C  +  {{MASS_Cr}} Cr  +  {{MASS_Si}} Si  +
'I' '   '
 (1000.00,1,s1-FactPS,#1) (1000.00,1,s1-FactPS,#1) (1000.00,1,s-FactPS,#1) (1000.00,1,s-FactPS,#1)
'R' 'NEW'
 {{MASS_Mn}} Mn  +  {{MASS_Al}} Al  +  {{MASS_N}} N  +  {{MASS_O}} O  +
'I' '   '
 (1000.00,1,s1-FactPS,#1) (1000.00,1,s-FactPS,#1) (1000.00,1,g-FactPS,#1) (1000.00,1,g-FactPS,#1)
'R' 'NEW'
 {{MASS_P}} P  +  {{MASS_S}} S  +  {{MASS_Ca}} Ca  +  {{MASS_Mg}} Mg  +
'I' '   '
 (1000.00,1,s1-FactPS,#1) (1000.00,1,s1-FactPS,#1) (1000.00,1,s1-FactPS,#1) (1000.00,1,s-FactPS,#1)
'R' 'NEW'
 {{MASS_Ti}} Ti  =
'I' '   '
 (1000.00,1,s1-FactPS,#1)
'F' 'WIN'
 'T' '{{T_START}} {{T_END}} {{T_STEP}}' 'P' '{{P_ATM}}' 'DH' ''
'DAT1' ' 3'
FT53 ST53 OX53
'DAT2' ' 2'
ST53 OX53
'DAT3' '0'

'GRID'
GRIDOPS   0  0
GRIDEND
'SS' '1035'
 214    +    101  1 N2O4
 216    +    101  1 MgC2
 217    +    101  1 Mg2C3
 222    +    101  1 MgCO3
 223    +    101  1 Mg(NO3)2
 227    +    101  1 Al5C3N
 268    +    101  1 P3N5
 288    +    101  1 SO3
 290    +    101  1 MgSO4
 291    +    102  1 MgSO4
 292    +    101  1 Al2S3
 293    +    101  1 Al2(SO4)3
 294    +    101  1 SiS
 295    +    101  1 SiS2
 296    +    101  1 P2S3
 297    +    101  1 P4S3
 298    +    101  1 P2S5
 299    +    101  1 P4S5
 300    +    101  1 P4S6
 301    +    101  1 P4S7
 306    +    101  1 Ca3N2
 307    +    101  1 CaCN2
 309    +    101  1 CaO2
 310    +    101  1 CaCO3
 311    +    102  1 CaCO3
 312    +    101  1 Ca(NO3)2
 314    +    101  1 CaMg(CO3)2
 315    +    101  1 CaCO3(MgCO3)3
 335    +    101  1 Ca5(SiO4)2CO3
 336    +    101  1 Ca5Si2O7(CO3)2
 346    +    101  1 Ca4Al6Si6O24CO3
 365    +    101  1 CaSO3
 366    +    101  1 CaSO4
 367    +    102  1 CaSO4
 371    +    101  1 Ti2C
 373    +    101  1 TiN3
 376    +    101  1 TiO
 377    +    102  1 TiO
 398    +    101  1 Ti2AlC
 399    +    101  1 Ti3AlC
 400    +    101  1 Ti3AlC2
 405    +    101  1 TiS
 406    +    101  1 TiS2
 407    +    101  1 TiS3
 408    +    101  1 Ti2S
 409    +    101  1 Ti2S3
 419    +    101  1 Cr2C
 420    +    101  1 Cr3C
 427    +    101  1 CrO2
 428    +    101  1 CrO3
 430    +    101  1 Cr(CrO4)
 432    +    101  1 Cr2(CrO4)3
 433    +    101  1 Cr8O21
 434    +    101  1 Cr(CO)6
 435    +    101  1 MgCrO4
 437    +    101  1 Cr2AlC
 450    +    101  1 Cr2(SO4)3
 451    +    101  1 CaCrO4
 462    +    101  1 Mn3C2
 466    +    101  1 MnN
 467    +    101  1 Mn2N
 468    +    101  1 Mn3N
 471    +    101  1 Mn6N4
 479    +    101  1 MnCO3
 480    +    101  1 Mn3AlC
 500    +    101  1 MnSO4
 511    +    101  1 Fe3C2
 512    +    101  1 Fe5C2
 513    +    102  1 Fe5C2
 514    +    101  1 Fe7C3
 516    +    101  1 Fe3N
 527    +    101  1 FeCO3
 569    +    101  1 FeSO4
 570    +    101  1 Fe2(SO4)3
 585    +    101  1 FeCr2S4
 587    +    101  2 C
 588    +    102  2 C
 589    +    101  2 N
 590    +    102  2 N
 591    +    103  2 N
 592    +    104  2 N
 593    +    105  2 N
 594    +    106  2 N
 595    +    107  2 N
 596    +    101  2 Mg
 597    +    102  2 Mg
 598    +    103  2 Mg
 599    +    104  2 Mg
 600    +    105  2 Mg
 601    +    106  2 Mg
 602    +    107  2 Mg
 603    +    101  2 Mg3N2
 604    +    102  2 Mg3N2
 605    +    103  2 Mg3N2
 607    +    101  2 Al
 608    +    102  2 Al
 609    +    103  2 Al
 610    +    104  2 Al
 611    +    105  2 Al
 612    +    106  2 Al
 613    +    107  2 Al
 614    +    108  2 Al
 615    +    109  2 Al
 616    +    101  2 Al4C3
 617    +    101  2 AlN
 622    +    101  2 Al3Mg
 623    +    101  2 Al30Mg23
 624    +    101  2 Si
 625    +    102  2 Si
 626    +    103  2 Si
 627    +    104  2 Si
 628    +    105  2 Si
 629    +    106  2 Si
 630    +    107  2 Si
 631    +    101  2 SiC
 632    +    102  2 SiC
 633    +    101  2 N4Si3
 642    +    101  2 Mg2Si
 643    +    101  2 Al4C4Si
 644    +    101  2 Al8C7Si
 645    +    101  2 P
 646    +    102  2 P
 647    +    103  2 P
 648    +    104  2 P
 649    +    105  2 P
 650    +    106  2 P
 651    +    101  2 Mg3P2
 652    +    101  2 AlP
 653    +    101  2 SiP
 654    +    101  2 SiP2
 655    +    101  2 S
 656    +    102  2 S
 657    +    101  2 MgS
 658    +    101  2 Ca
 659    +    102  2 Ca
 660    +    103  2 Ca
 661    +    101  2 CaC2
 662    +    102  2 CaC2
 663    +    103  2 CaC2
 664    +    104  2 CaC2
 666    +    101  2 Mg2Ca
 667    +    102  2 Mg2Ca
 668    +    101  2 Al2Ca
 669    +    102  2 Al2Ca
 670    +    101  2 Al4Ca
 671    +    101  2 Al3Ca8
 672    +    101  2 Al14Ca13
 673    +    101  2 CaSi
 674    +    101  2 CaSi2
 675    +    101  2 Ca2Si
 676    +    101  2 Ca3Si4
 677    +    101  2 Ca5Si3
 678    +    101  2 Ca14Si19
 679    +    101  2 CaAl2Si2
 680    +    101  2 Ca3P2
 681    +    101  2 CaS
 682    +    101  2 Ti
 683    +    102  2 Ti
 684    +    103  2 Ti
 685    +    104  2 Ti
 686    +    105  2 Ti
 687    +    106  2 Ti
 688    +    107  2 Ti
 689    +    101  2 NTi2
 696    +    101  2 TiSi
 697    +    101  2 TiSi2
 698    +    101  2 Ti3Si
 699    +    101  2 Ti5Si3
 700    +    101  2 Ti5Si4
 701    +    101  2 Cr
 702    +    102  2 Cr
 703    +    103  2 Cr
 704    +    104  2 Cr
 705    +    105  2 Cr
 706    +    101  2 Cr3C2
 707    +    101  2 Cr7C3
 708    +    101  2 Cr20Cr3C6
 710    +    101  2 CrAl7
 711    +    101  2 Cr2Al11
 712    +    101  2 CrSi
 713    +    101  2 Cr5Si3
 714    +    101  2 CrP
 715    +    101  2 CrP2
 716    +    101  2 Cr2P
 717    +    101  2 Cr3P
 718    +    101  2 Cr2S3
 719    +    101  2 Cr8Ti25Al67
 720    +    101  2 Mn
 721    +    102  2 Mn
 722    +    103  2 Mn
 723    +    104  2 Mn
 724    +    105  2 Mn
 725    +    106  2 Mn
 726    +    101  2 Mn3C
 727    +    101  2 Mn5C2
 728    +    101  2 Mn7C3
 729    +    101  2 Mn23C6
 730    +    101  2 Mn3N2
 731    +    101  2 Mn6N5
 733    +    101  2 MnAl4
 734    +    101  2 MnAl6
 735    +    101  2 MnAl12
 736    +    101  2 Mn4Al11
 737    +    101  2 Mn23Al99
 738    +    101  2 MnSi
 739    +    101  2 Mn3Si
 740    +    101  2 Mn5Si3
 741    +    101  2 Mn6Si
 742    +    101  2 Mn9Si2
 743    +    101  2 Mn11Si19
 744    +    101  2 Mn5SiC
 745    +    101  2 Mn8Si2C
 746    +    101  2 MnSiN2
 747    +    101  2 Mn3SiAl2
 748    +    101  2 MnP
 749    +    101  2 MnP3
 750    +    101  2 Mn2P
 751    +    101  2 Mn3P
 752    +    101  2 Mn3P2
 753    +    101  2 MnS
 754    +    101  2 MnS2
 755    +    101  2 MnTi
 756    +    101  2 Ti2Mn
 757    +    101  2 Mn2Ti
 758    +    101  2 Mn2Ti2
 759    +    101  2 Mn3Ti
 760    +    101  2 Mn9Ti2
 761    +    101  2 Cr3Mn5
 762    +    101  2 Fe
 763    +    102  2 Fe
 764    +    101  2 Fe3C
 765    +    102  2 Fe3C
 774    +    101  2 FeAl2
 775    +    101  2 Fe2Al5
 776    +    101  2 FeSi
 777    +    101  2 FeSi2
 778    +    101  2 Fe2Si
 779    +    101  2 Fe3Si7
 780    +    101  2 Fe5Si3
 781    +    101  2 FeSiAl2
 782    +    101  2 Fe2SiAl2
 783    +    101  2 FeP
 784    +    101  2 FeP2
 785    +    101  2 Fe2P
 786    +    101  2 Fe3P
 787    +    102  2 Fe3P
 788    +    101  2 FeSi4P4
 789    +    101  2 FeS
 790    +    101  2 FeS2
 791    +    101  2 Fe7S8
 792    +    101  2 Fe9S10
 793    +    101  2 Fe10S11
 794    +    101  2 Fe11S12
 795    +    101  2 FeTi
 796    +    101  2 FeTi2O5
 797    +    101  2 FeTi3Al8
 799    +    101  3 MgO
 800    +    101  3 Al2O3
 801    +    102  3 Al2O3
 802    +    103  3 Al2O3
 803    +    104  3 Al2O3
 804    +    101  3 SiO2
 805    +    102  3 SiO2
 806    +    103  3 SiO2
 807    +    104  3 SiO2
 808    +    105  3 SiO2
 809    +    106  3 SiO2
 810    +    107  3 SiO2
 811    +    108  3 SiO2
 812    +    101  3 MgSiO3
 813    +    102  3 MgSiO3
 814    +    103  3 MgSiO3
 815    +    104  3 MgSiO3
 816    +    105  3 MgSiO3
 817    +    106  3 MgSiO3
 818    +    107  3 MgSiO3
 819    +    101  3 Mg2SiO4
 820    +    102  3 Mg2SiO4
 821    +    103  3 Mg2SiO4
 822    +    101  3 Al2Si2O7
 823    +    101  3 Mg4Al10Si2O23
 824    +    101  3 Mg3Al2Si3O12
 825    +    101  3 Mg2Al4Si5O18
 826    +    101  3 P2O5
 827    +    102  3 P2O5
 828    +    103  3 P2O5
 829    +    101  3 MgP2O6
 830    +    101  3 Mg2P2O7
 831    +    102  3 Mg2P2O7
 832    +    101  3 Mg3P2O8
 833    +    101  3 MgP4O11
 834    +    101  3 AlPO4
 835    +    102  3 AlPO4
 836    +    103  3 AlPO4
 837    +    104  3 AlPO4
 838    +    101  3 AlP3O9
 839    +    101  3 P2SiO7
 840    +    102  3 P2SiO7
 841    +    103  3 P2SiO7
 842    +    101  3 P4Si3O16
 843    +    101  3 CaO
 844    +    101  3 CaAl2O4
 845    +    101  3 CaAl4O7
 846    +    101  3 CaAl12O19
 847    +    101  3 Ca3Al2O6
 848    +    101  3 CaMg2Al16O27
 849    +    101  3 Ca2Mg2Al28O46
 850    +    101  3 Ca3MgAl4O10
 851    +    101  3 CaSiO3
 852    +    102  3 CaSiO3
 853    +    101  3 Ca2SiO4
 854    +    102  3 Ca2SiO4
 855    +    103  3 Ca2SiO4
 856    +    101  3 Ca3SiO5
 857    +    101  3 Ca3Si2O7
 858    +    101  3 CaMgSi2O6
 859    +    101  3 Ca2MgSi2O7
 860    +    101  3 Ca3MgSi2O8
 861    +    101  3 CaAl2SiO6
 862    +    101  3 CaAl2Si2O8
 863    +    102  3 CaAl2Si2O8
 864    +    101  3 Ca2Al2SiO7
 865    +    101  3 Ca3Al2Si3O12
 866    +    101  3 CaP2O6
 867    +    102  3 CaP2O6
 868    +    103  3 CaP2O6
 869    +    101  3 CaP4O11
 870    +    102  3 CaP4O11
 871    +    101  3 Ca2P2O7
 872    +    102  3 Ca2P2O7
 873    +    103  3 Ca2P2O7
 874    +    101  3 Ca2P6O17
 875    +    101  3 Ca3P2O8
 876    +    102  3 Ca3P2O8
 877    +    103  3 Ca3P2O8
 878    +    101  3 Ca4P2O9
 879    +    102  3 Ca4P2O9
 880    +    101  3 Ca4P6O19
 881    +    101  3 Ca3Mg3(PO4)4
 882    +    101  3 Ca4Mg2P6O21
 883    +    101  3 Ca5P2SiO12
 884    +    101  3 Ca7P2Si2O16
 885    +    101  3 TiO2
 886    +    102  3 TiO2
 887    +    101  3 Ti2O3
 888    +    102  3 Ti2O3
 889    +    101  3 Ti3O5
 890    +    101  3 Ti4O7
 891    +    101  3 Ti5O9
 892    +    101  3 Ti6O11
 893    +    101  3 Ti7O13
 894    +    101  3 Ti8O15
 895    +    101  3 Ti9O17
 896    +    101  3 Ti10O19
 897    +    101  3 Ti20O39
 898    +    101  3 Ti2Al6O13
 899    +    101  3 CaTiO3
 900    +    102  3 CaTiO3
 901    +    103  3 CaTiO3
 902    +    101  3 Ca2Ti2O5
 903    +    102  3 Ca2Ti2O5
 904    +    101  3 Ca3Ti2O6
 905    +    101  3 Ca3Ti2O7
 906    +    101  3 Ca4Ti3O10
 907    +    101  3 Ca3Ti8Al12O37
 908    +    101  3 CaSiTiO5
 909    +    102  3 CaSiTiO5
 910    +    101  3 Ca3Ti2Si3O12
 911    +    101  3 Cr2O3
 912    +    101  3 CaCr2O4
 913    +    102  3 CaCr2O4
 914    +    101  3 (Ca2Cr3)Cr10O20
 915    +    101  3 (CaCr)Si4O10
 916    +    101  3 Ca3Cr2Si3O12
 917    +    101  3 MnO
 918    +    101  3 MnO2
 919    +    101  3 Mn2O3
 920    +    102  3 Mn2O3
 921    +    101  3 Mg6MnO8
 922    +    101  3 MnSiO3
 923    +    101  3 Mn2SiO4
 924    +    101  3 Mn2Al4Si5O18
 925    +    101  3 Mn3Al2Si3O12
 926    +    101  3 MnP2O6
 927    +    101  3 Mn2P2O7
 928    +    101  3 Mn3P2O8
 929    +    101  3 CaMnO3
 930    +    101  3 Ca2MnO4
 931    +    101  3 CaMn2O4
 932    +    101  3 Ca3Mn2O7
 933    +    101  3 CaMn3O6
 934    +    101  3 Ca2Mn3O8
 935    +    101  3 Ca4Mn3O10
 936    +    101  3 CaMn4O8
 937    +    101  3 CaMn7O12
 938    +    101  3 Fe2O3
 939    +    102  3 Fe2O3
 940    +    103  3 Fe2O3
 941    +    101  3 Al2Fe2O6
 942    +    101  3 FeSiO3
 943    +    102  3 FeSiO3
 944    +    103  3 FeSiO3
 945    +    101  3 Fe2SiO4
 946    +    102  3 Fe2SiO4
 947    +    103  3 Fe2SiO4
 948    +    101  3 Fe2Al4Si5O18
 949    +    101  3 Fe3Al2Si3O12
 950    +    101  3 FeP2O6
 951    +    101  3 Fe2P2O7
 952    +    101  3 Fe2P2O8
 953    +    101  3 Fe2P6O18
 954    +    101  3 Fe3P2O8
 955    +    102  3 Fe3P2O8
 956    +    101  3 Fe4P2O10
 957    +    101  3 Fe4P6O21
 958    +    101  3 Fe6P2O14
 959    +    101  3 Fe7P6O24
 960    +    101  3 Fe10P6O26
 961    +    101  3 Fe18P2O24
 962    +    101  3 CaFe2O4
 963    +    101  3 Ca2Fe2O5
 964    +    101  3 CaFe4O7
 965    +    101  3 CaFeSi2O6
 966    +    101  3 Ca2FeSi2O7
 967    +    101  3 Ca3Fe2Si3O12
   0    I      0  1 SOLN-LIQU  // 2 FSstel Liqu     LIQUID
   0    J      0  1 SOLN-FCC   // 3 FSstel FCC      FCC_A1
   0    I      0  1 SOLN-BCC   // 2 FSstel BCC      BCC_A2
   0    I      0  1 SOLN-HCP   // 2 FSstel HCP      HCP_A3
   0    +      0  1 SOLN-CEME  // 1 FSstel CEME     CEMENTITE
   0    +      0  1 SOLN-M23C  // 1 FSstel M23C     M23C6
   0    +      0  1 SOLN-M7C3  // 1 FSstel M7C3     M7C3
   0    +      0  1 SOLN-M3C2  // 1 FSstel M3C2     M3C2
   0    +      0  1 SOLN-SIGM  // 1 FSstel SIGM     SIGMA
   0    +      0  1 SOLN-CBCC  // 1 FSstel CBCC     CBCC_A12
   0    +      0  1 SOLN-CUB   // 1 FSstel CUB      CUB_A13
   0    I      0  1 SOLN-ME3P  // 2 FSstel Me3P     Me3P
   0    I      0  1 SOLN-ME2P  // 2 FSstel Me2P     Me2P
   0    +      0  1 SOLN-M3S1  // 1 FSstel M3S1     Me3Si1
   0    +      0  1 SOLN-M1S1  // 1 FSstel M1S1     Me1Si1
   0    +      0  1 SOLN-M5S3  // 1 FSstel M5S3     M5Si3
   0    I      0  1 SOLN-ME4N  // 2 FSstel Me4N     Me4N
   0    +      0  1 SOLN-HIGH  // 1 FSstel HIGH     HIGH_SIGMA
   0    I      0  1 SOLN-BCC2  // 2 FSstel BCC2     BCC_B2!BCC_A2
   0    +      0  1 SOLN-M5C2  // 1 FSstel M5C2     M5C2
   0    +      0  1 SOLN-C3S   // 1 FSstel C3S      Cr3Si
   0    +      0  1 SOLN-CS2   // 1 FSstel CS2      CrSi2
   0    I      0  1 SOLN-LAV1  // 2 FSstel LAV1     LAVES_C14
   0    I      0  1 SOLN-LAV3  // 2 FSstel LAV3     LAVES_C15
   0    +      0  1 SOLN-DIAM  // 1 FSstel DIAM     Diamond_A4
   0    +      0  1 SOLN-TI2N  // 1 FSstel TI2N     TI2N
   0    +      0  1 SOLN-MONO  // 1 FSstel MONO     Monoxide
   0    +      0  1 SOLN-TAU5  // 1 FSstel TAU5     Tau5_Al8Fe2Si1
   0    +      0  1 SOLN-TAU6  // 1 FSstel TAU6     Tau6_Al5Fe1Si1
   0    +      0  1 SOLN-ACML  // 1 FSstel ACML     L-Al8(Cr,Mn)5
   0    +      0  1 SOLN-ACMH  // 1 FSstel ACMH     H-Al8(Cr,Mn)5
   0    +      0  1 SOLN-TAUA  // 1 FSstel TAUA     alpha_Al16(Fe,Mn)4Si1(Al,Si)2
   0    +      0  1 SOLN-TAUB  // 1 FSstel TAUB     Beta_Al15Si1(Al,Si)4(Fe,Mn)6
   0    I      0  1 SOLN-KAPP  // 2 FSstel KAPP     Kappa-Carbide
   0    +      0  1 SOLN-M8SC  // 1 FSstel M8Si2C1
   0    +      0  1 SOLN-M5SC  // 1 FSstel M5Si1C1
   0    +      0  1 SOLN-D88_  // 1 FSstel D88_M5Si3
   0    +      0  1 SOLN-TAU2  // 1 FSstel Tau2_Al5Fe2Si2
   0    +      0  1 SOLN-TAU4  // 1 FSstel Tau4_Al3Fe1Si2
   0    +      0  1 SOLN-M11S  // 1 FSstel (Mn)11(Si,Al)19
   0    +      0  1 SOLN-AL11  // 1 FSstel HTAl11Mn4-oP156
   0    +      0  1 SOLN-FS2L  // 1 FSstel Fe1Si2
   0    +      0  1 SOLN-FS2H  // 1 FSstel Fe3Si7
   0    I      0  1 SOLN-L10   // 2 FSstel AlTi
   0    I      0  1 SOLN-D019  // 2 FSstel AlTi3_D019
   0    I      0  1 SOLN-ZETA  // 2 FSstel Al5Ti2
   0    I      0  1 SOLN-ETA   // 2 FSstel Al2Ti1
   0    I      0  1 SOLN-EPSH  // 2 FSstel Al3Ti-h
   0    I      0  1 SOLN-EPSL  // 2 FSstel Al3Ti-l
   0    +      0  1 SOLN-TC23  // 1 FSstel C-TiCr2
   0    +      0  1 SOLN-TAO2  // 1 FSstel Tao2
   0    +      0  1 SOLN-MEP   // 1 FSstel MeP
   0    I      0  1 SOLN-ALP   // 2 FSstel AlP
   0    +      0  1 SOLN-A3M2  // 1 FSstel Beta_Al3Mg2
   0    +      0  1 SOLN-GAAM  // 1 FSstel Gamma_Al12Mg17
   0    +      0  1 SOLN-AC2   // 1 FSstel AlCr2
   0    +      0  1 SOLN-A4C   // 1 FSstel Al4Cr
   0    +      0  1 SOLN-A7CR  // 1 FSstel Al7(Cr,Mn)
   0    +      0  1 SOLN-A11C  // 1 FSstel Al11(Cr,Mn)2
   0    +      0  1 SOLN-A5F2  // 1 FSstel Al5Fe2
   0    +      0  1 SOLN-A13F  // 1 FSstel Al13Fe4
   0    I      0  1 SOLN-A8F5  // 2 FSstel Al8Fe5
   0    +      0  1 SOLN-TCF   // 1 FSstel Ti5(Cr,Fe)24
   0    +      0  1 SOLN-PYRR  // 1 FSstel Pyrrhotite
   0    I      0  1 SOLN-MS-C  // 2 FSstel MeS_cubic
   0    J      0  1 SOLN-L12   // 3 FSstel L12!FCC_A1
   0    +      0  1 SOLN-SICN  // 1 FSstel SiC
   0    +      0  1 SOLN-MNTI  // 1 FSstel MnTi
   0    +      0  1 SOLN-NI3M  // 1 FSstel Ni3M
SSEND
ENDF-00001
