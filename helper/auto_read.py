import regex as re
import locale

locale.setlocale(locale.LC_ALL,'de_DE') # 'en_US.UTF-8')

FILE_NAME = '501.txt'
TABLE_HEADER = '\[Peak Table\(PDA\-Ch1\)\]'
DELIMITER = '!'
COLUMN_NAME = 'Area'
NUMBER_PEAKS_MAX = 3
RETENTION_COLUMN_NAME = 'R.Time'
RETENTION_TIMES_OF_INTEREST = [[9.4,9.6,'Product'],[8.1,8.3]]#[[4.3,4.9],[7.1,7.8,'Product']] # ranges of peak retention times in minutes

def auto_read_hplc_data():
    with open(FILE_NAME,'r') as file:
        lines = file.readlines()
        i=0
        # print(lines)
        for line in lines:
            i+=1
            # print(re.search(TABLE_HEADER,line))
            if re.search(str(TABLE_HEADER),line):
                # print(re.search(TABLE_HEADER,line))
                # print(line)
                # print('line before')
                # print(TABLE_HEADER)
                for j in range(NUMBER_PEAKS_MAX+1):
                    # print(f'line no {i+j+2}: {lines[i+j+1]}',end='')
                    lis = []
                    lis = [*lines[i+j+1].split(DELIMITER)]
                    for k in range(len(lis)):
                        if re.search(f'^{RETENTION_COLUMN_NAME}$', lis[k]):
                            ind2 = k
                        if re.search(f'^{COLUMN_NAME}$', lis[k]):
                            ind = k
                parameters = []
                for m in range(NUMBER_PEAKS_MAX):
                    lis = []
                    lis = [*lines[i+m+2].split(DELIMITER)]  
                    # print(f'ind is: {ind}')
                    # print(f'lis is: {lis}')
                    try:
                        retention_time = lis[ind2]
                        retention_time = float(str(retention_time).replace(",","."))
                        # retention_time = locale.atof(lis[ind2])
                        # print(f'length of retention time of interest: {RETENTION_TIMES_OF_INTEREST}')
                        for o in range(len(RETENTION_TIMES_OF_INTEREST)):
                            # print(f'true or false: {RETENTION_TIMES_OF_INTEREST[o][0] <= retention_time <= RETENTION_TIMES_OF_INTEREST[o][1]}')
                            if RETENTION_TIMES_OF_INTEREST[o][0] <= retention_time <= RETENTION_TIMES_OF_INTEREST[o][1]:
                                if len(RETENTION_TIMES_OF_INTEREST[o]) > 2:
                                    if RETENTION_TIMES_OF_INTEREST[o][2].lower() == 'product':
                                        numerator = float(lis[ind])
                                parameter = float(lis[ind])
                                parameters.append(parameter)
                        # print(f'ret times are: {retention_time}')
                    except IndexError:
                        pass
                    # for o in range(len(RETENTION_TIMES_OF_INTEREST)):
                    #     if RETENTION_TIMES_OF_INTEREST[o][0] <= retention_times <= RETENTION_TIMES_OF_INTEREST[o][1]:
                    #         parameter = float(lis[ind])
                    #         parameters.append(parameter)
                    
                # print(f'len of parameters: {len(parameters)}')
                # print(f'retention time: {(retention_time)}')
                if len(parameters) == 2:
                    conversion = (numerator / (parameters[0] + parameters[1])) * 100 # %  --- parameters[1]
                    return conversion
                else:
                    raise Exception('Cannot auto calculate the area ratio of more than two selected peaks. \nPlease use for RETENTION_TIMES_OF_INTEREST exactly two retention time ranges or adapt the ranges to the actual HPLC data output. ')
    
if __name__ == '__main__':
    conversions = []
    for i in range(42):
        # RiE-E-309-1
        # if i+1 == 24:
        #     conversions.append((1011126/(424117+1011126))*100)
        #     continue
        FILE_NAME = f'RiE-E-383-{i+1}.txt'
        
        print(f'Processing file ... {FILE_NAME}')
        # print(auto_read_hplc_data())
        conversions.append(auto_read_hplc_data())
    # for i in range(4):
    #     FILE_NAME = f'WaJ-E-{173+i}.txt'
    #     print(f'Processing file ... {FILE_NAME}')
    #     # print(auto_read_hplc_data())
    #     conversions.append(auto_read_hplc_data())
    # for i in range(5):
    #     FILE_NAME = f'WaJ-E-{162+i}.txt'
    #     print(f'Processing file ... {FILE_NAME}')
    #     # print(auto_read_hplc_data())
    #     conversions.append(auto_read_hplc_data())
    # for i in range():
    #     RETENTION_TIMES_OF_INTEREST = [[4.7,4.8],[7.2,7.6]]
    #     FILE_NAME = f'{505+i}.txt'
    #     locale.setlocale(locale.LC_ALL, 'de_DE') # 'en_US.UTF-8')
    #     print(f'it proceeds with processing a file called: {FILE_NAME}')
    #     print(auto_read_hplc_data())
    #     conversions.append(auto_read_hplc_data())
    print(f'Conversions in the order of read text files:\n{conversions}')
    for i in range(len(conversions)):
        print(conversions[i])
        