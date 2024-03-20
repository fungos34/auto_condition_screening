
import pandas as pd
import openpyxl
import numpy as np
import time

X7 = [2.5,2.5,2.5,2.7,2.7,2.7,2.9,2.9,2.9,3.1,3.1,3.1,3.3,3.3,3.3,3.5,3.5,3.5,3.7,3.7,3.7,3.9,3.9,3.9,4.2,4.2,4.2,4.5,4.5,4.5,4.8,4.8,4.8,5.2,5.2,5.2,5.6,5.6,5.6,6,6,6]#,'Current (mA)']
Y7 = [2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3,2.5,2.8,3]#,'Charge (F/mol)']
Z7 = [24,22,20,26,23,22,28,25,24,30,27,25,32,29,27,34,31,29,36,32,30,38,34,32,41,37,34,44,39,37,47,42,39,51,46,43,55,49,46,59,53,49]#,'Flow Rate (μL/min)']
C7 = [58.77069570996408, 75.81683734909782, 84.97767335297142, 74.09557354952331, 83.74146263611699, 88.09250270666192, 75.78939380350872, 84.39418537556504, 86.65099406388391, 76.05935860447373, 81.6057221153568, 86.8140332900967, 75.60241520025112, 81.82698114134314, 84.30714873904962, 76.45987532569993, 80.89794914650234, 83.61373685802732, 74.04415147987369, 80.77878173906664, 81.72680284187874, 71.49142231639796, 77.3718835436889, 79.76277381915901, 70.719577949889, 73.48573664835764, 78.16685128472449, 66.45207134360327, 70.78113369639944, 71.70642949459366, 62.58843078478421, 67.09568760357106, 70.46428817419198, 61.23626092520843, 64.07345104185053, 64.20025252300633, 55.57150632553064, 60.06823329893094, 55.60681001019623, 49.982707928864684, 49.83498526960874, 50.36308312719394]#, 'Conversion (%)']

X6 = [26,26,26,30,30,30,34,34,34,38,38,38,42,42,42,46,46,46,50,50,50,54,54,54,58,58,58,62,62,62,66,66,66,70,70,70,74,74,74,78,78,78]#,'Current (mA)']
Y6 = [6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8,6,7,8]#,'Charge (F/mol)']
Z6 = [26,23,20,31,26,23,35,30,26,39,33,29,43,37,32,47,40,35,51,44,38,55,47,41,60,51,45,64,55,48,68,58,51,72,62,54,76,65,57,80,69,60]#,'Flow Rate (μL/min)']
C6 = [71.1233676505315, 76.14140999833413, 78.80120734140161, 71.10283965215368, 75.75090922222766, 78.66830063501952, 70.56487642180204, 74.24186393031252, 75.35848377603956, 67.30731819613428, 71.45228307578427, 73.84791689920539, 67.1457320444, 72.54373905780167, 73.98101839631845, 65.18044492890513, 67.21901708850247, 71.93896370983407, 67.40434580317938, 70.31277840065454, 70.95264374968363, 62.2770672149939, 70.54041988979725, 70.44981233143098, 67.01092365324084, 67.29014809312773, 68.31725288104742, 65.21452370675601, 66.65440877569641, 57.80975655998959, 64.21183644416956, 64.68762516299181, 62.75419407730299, 62.425625235133595, 57.00006029155876, 53.150914764469526, 62.79831980450402, 53.83281094240333, 53.72734912747963, 60.58863648287078, 52.41010851995516, 52.00552283412273]#, 'Conversion (%)']

X5 = [20,20,20,20,20,20,20,30,30,30,30,30,30,30,40,40,40,40,40,40,40,50,50,50,50,50,50,50,60,60,60,60,60,60,60,70,70,70,70,70,70,70]#,'Current (mA)']
Y5 = [3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.1,3.2,3.3,3.4,3.5,3.6,3.7]#,'Charge (F/mol)']
Z5 = [40,38,37,36,35,34,33,60,58,56,54,53,51,50,80,77,75,73,71,69,67,100,97,94,91,88,86,84,120,116,113,109,106,103,100,140,136,131,128,124,120,117]#,'Flow Rate (μL/min)']
C5 = [79.5696361531019, 81.21277271593395, 82.25677286603174, 82.20701167108939, 83.37617715444479, 82.69236098601893, 84.63965728948727, 81.64145891973794, 82.55535204246573, 82.91367866410026, 83.64315195491501, 83.50302650329826, 83.59515726196057, 84.77593786168957, 81.8452026417783, 81.98325607885921, 83.72456980388627, 83.60191612148661, 83.67226562426269, 84.87638993589354, 85.52734759759282, 82.3872763614514, 83.12816275947537, 83.7964019749412, 84.2847312028138, 84.94639793029076, 85.46043319028468, 85.75547385569526, 81.02719575328399, 82.61480391337216, 82.9469908552152, 84.01505041091897, 84.71804513279329, 85.76068101115098, 86.28322890906077, 79.3207577019601, 81.31529067619186, 82.2825085778643, 82.20449471334092, 83.26041456785352, 84.39250612700852, 84.48232543629692]#, 'Conversion (%)']

STY5 = [] # space-time-yield in (g/(F/mol)/h)
for i in range(len(Z5)):
    molmass = 198.27 # g/mol
    concentration = 0.1 # mol/L
    conversion = C5[i] # %
    flow_rate = Z5[i] # μL/min
    charge = Y5[i]
    #STY1.append((((molmass*concentration) * conversion)/charge) * ((flow_rate/1000000)*60)) # space-time-yield in (g/(F/mol)/h)
    STY5.append(((molmass*concentration) * (conversion/100)) * ((flow_rate/1000000)*60)*1000) # productivity in (mg/h)
# STY5.append('Productivity (mg/h)')

STY6 = [] # space-time-yield in (g/(F/mol)/h)
for i in range(len(Z6)):
    molmass = 208.30 # g/mol
    concentration = 0.1 # mol/L
    conversion = C6[i] # %
    flow_rate = Z6[i] # μL/min
    charge = Y6[i]
    #STY1.append((((molmass*concentration) * conversion)/charge) * ((flow_rate/1000000)*60)) # space-time-yield in (g/(F/mol)/h)
    STY6.append(((molmass*concentration) * (conversion/100)) * ((flow_rate/1000000)*60)*1000) # productivity in (mg/h)
# STY6.append('Productivity (mg/h)')

STY7 = [] # space-time-yield in (g/(F/mol)/h)
for i in range(len(Z6)):
    molmass = 120.15 # g/mol
    concentration = 0.025 # mol/L
    conversion = C7[i] # %
    flow_rate = Z7[i] # μL/min
    charge = Y7[i]
    #STY1.append((((molmass*concentration) * conversion)/charge) * ((flow_rate/1000000)*60)) # space-time-yield in (g/(F/mol)/h)
    STY7.append(((molmass*concentration) * (conversion/100)) * ((flow_rate/1000000)*60)*1000) # productivity in (mg/h)
# STY7.append('Productivity (mg/h)')


EFF5 = []
for i in range(len(Y5)):
    molar_charge = 2
    conversion = C5[i] # %
    charge = Y5[i]
    EFF5.append(((molar_charge/charge) * (conversion/100))*100)  # 'Current Efficiency (%)'
# EFF5.append('Current Efficiency (%)')

EFF6 = []
for i in range(len(Y6)):
    molar_charge = 4
    conversion = C6[i] # %
    charge = Y6[i]
    EFF6.append(((molar_charge/charge) * (conversion/100))*100)  # 'Current Efficiency (%)'
# EFF6.append('Current Efficiency (%)')

EFF7 = []
for i in range(len(Y7)):
    molar_charge = 2
    conversion = C7[i] # %
    charge = Y7[i]
    EFF7.append(((molar_charge/charge) * (conversion/100))*100)  # 'Current Efficiency (%)'
# EFF7.append('Current Efficiency (%)')


index1 = ['Current (mA)','Charge (F/mol)','Flow Rate (μL/min)','Conversion (%)','Productivity (mg/h)','Current Efficiency (%)']

df = pd.DataFrame([X5, Y5, Z5, C5, STY5, EFF5],
                  index=index1, columns=np.arange(1,43))

df2 = pd.DataFrame([X6, Y6, Z6, C6, STY6, EFF6],
                  index=index1, columns=np.arange(1,43))

df3 = pd.DataFrame([X7, Y7, Z7, C7, STY7, EFF7],
                  index=index1, columns=np.arange(1,43))

path = 'RialWagner_Longrun_Rawdata.xlsx'

with pd.ExcelWriter(path) as writer:
    # writer.book = openpyxl.load_workbook(path)
    df.to_excel(writer, sheet_name='Methoxydiphenylmethane')
    df2.to_excel(writer, sheet_name='BenzeneDimethoxyTertiarybutyl')
    df3.to_excel(writer, sheet_name='BenzeneEthanol')
# df.to_excel('output.xlsx', sheet_name='DiphenylaceticAcid_Longrun')
# df2.to_excel('output.xlsx', sheet_name='Longrun')
