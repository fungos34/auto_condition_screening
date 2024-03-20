import regex as re

name_extracting_logg='extracting_logg.txt'
name_extracting_times='extracting_times.txt'
name_logg_file='copy_gsioc_protocol.log'

def get_relevant_logg():
    with open(name_logg_file) as file:
        number=0
        lines = file.readlines()
        for line in lines:
            number+=1
            if number==1:
                with open(name_extracting_logg,'a') as extract:
                    extract.write(f'linenumber {number}: {line}')
            match=re.search('<<<.+>>>',line,re.IGNORECASE)
            if match:
                # print(f'match as follows: {match.string}')
                with open(name_extracting_logg,'a') as extract:
                    extract.write(f'linenumber {number}: {match.string}')
                    # extract.write('\n'.join(match.string))
            else:
                pass
    print(f'successfully summarized important logg entries in a file called {extract.name}')

def get_time_between():
    with open(name_extracting_logg) as file:
        lines = file.readlines()
        number=0
        timetable={}
        for line in lines:
            match=re.search('(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2}),(\d*)',line) #YYYY-MM-DD HH-MM-SS,SSS
            if match:
                times=[
                    "y",
                    "m",
                    "d",
                    "h",
                    "min",
                    "sec",
                    "msec"
                ]
                

                value=list(match.groups(0))
                print(f'values: {value}')

                for i in range(len(value)):
                    value_list=list().append(value[i])
                    timetable.update({times[i]: (for _ in )})


                # value_list=[]
                # for j in range(len(value)):
                #     value_list.append(value[j])
                # print(f'value_list: {value_list}')
                # for i in range(len(times)):
                #     timetable.update({times[i]:list().extend(value[i])})

                # times_entity=[]

                # for i in range(len(value)):
                #     value[i]=int(value[i])
                #     times_entity.extend(value)
                # timetable.update({times[i]:times_entity})
                # for i in range(len(match)):
                #     year[i]=int(match.group(i)[0])
                number+=1
                with open(name_extracting_times,'a') as extract:
                    extract.write(match.groups()[0])
        print(f'timetable: {timetable}')

    print(f'successfully extracted times from important entries in a file called {extract.name}')
    
get_relevant_logg()
get_time_between()


