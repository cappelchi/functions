# -*- coding: utf-8 -*-
"""vcf_bed_manipul.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/14k3gTpgao9XoKGW8fnRnJCA7xha-qLw6
"""
import csv
from tqdm import tqdm
from pyliftover import LiftOver
import pandas as pd

def find_chrom (fname):
    #Поискк окончания header в vcf file
    with open (fname, 'r') as check:
        reader = csv.reader(check, delimiter = '\t')
        for cnt, row in enumerate(reader):
            if row[0] == '#CHROM':
                return cnt
                break

def snp_recode(sample, ref, alt):
    #для сингапурской базы возвращает пару для VCF файла вида 0|0, декодирует пару REF / ALT из букв в цифру
    if len(sample) == 2:
        snp_recode = str(2 * int(alt == sample[0]) - 1 + \
                         (ref == sample[0])).replace('-1', '.')  + '|' + \
                        str(2 * int(alt == sample[1]) - 1 + \
                            (ref == sample[1])).replace('-1', '.')
    else:
        snp_recode = '.|.'  
    
    return snp_recode

def chip_intersection (vcf_name, chip_names, by_snp_name = True):
    #поиск одинаковых снипов по ID (названию) в чипах для vcf файлов
    #названия фалов (чипов) chip_names передаются списком
    #ищем по названию или координате by_snp_name (True/False)
    if (vcf_name == '') or (chip_names == []):
        print('Filenames not defined')
        return
    if by_snp_name:
        ucols_vcf = [2]
        ucols_chip = [7]
        col_names = ['SNP']
    else:
        ucols_vcf = [0, 1]
        ucols_chip = [5, 6]
        col_names = ['CHROM', 'POS']

    sheet =[]
    start_row = find_chrom(vcf_name)       
    df_vcf = pd.read_csv(
        vcf_name,
        #'/content/ReichLab/V42/short/v42.4.1240K_HO.selected_38.vcf', 
        sep = '\t', 
        usecols = ucols_vcf,
        header = start_row, 
        #nrows = 1000,
        index_col = False
        )
    if by_snp_name:
        set1 = set(df_vcf.ID)
    else:
        df_vcf['crd'] = df_vcf['#CHROM'].apply(str) + ':' +  df_vcf['POS'].apply(str)
        set1 = set(df_vcf.crd)
    print (f'VCF ({vcf_name}) SNP count: ', len(df_vcf))
    sheet.append(len(df_vcf))
    set3 = set([])
    for chip_name in chip_names:           
        df_chip = pd.read_csv(
            chip_name,
            #'/content/ReichLab/V42/short/v42.4.1240K_HO.selected_38.vcf', 
            sep = '\s+', 
            usecols = ucols_chip,
            names = col_names,
            header = None, 
            #nrows = 1000,
            index_col = False
            )
        if by_snp_name: 
            #set1 = set(df_chip.SNP) & set1
            set2 = set(df_chip.SNP) & set1
            set3 = set3 | set2
        else:
            df_chip['crd'] = df_chip['CHROM'].apply(str) + ':' +  df_chip['POS'].apply(str)
            set2 = set(df_chip.crd) & set1
            set3 = set3 | set2
        print(f'Chip ({chip_name}) SNP count: ', len(df_chip))
        print ('VCF vs Chip SNP intersections: ', len(set2))
        sheet.append(len(set2))
        print('')
    print ('Sum of chip intersections: ', len(set3))
    sheet.append(len(set3))
    for cell in sheet:
        print(cell)
    return sheet

def recoord_vcf(input_name = '', output_name = '', snp_only = False):
    #Выравнивание координат на 38 версию генома для vcf файла
    #можно задать альтернативное имя для output file
    #можно выравнивать 18 или 19 версию задавая переменную
    #lo = LiftOver('hg19ToHg38.over.chain.gz')
    #lo = LiftOver('hg18ToHg38.over.chain.gz')
    #другие версии выравниваются через 19 версию
    #snp_only = True отбрасывает мультиаллельные снипы при выравнивании генома
    if (input_name == '') or (output_name == ''):
        return
    with open(input_name, 'r') as input_file:
        reader = csv.reader(input_file, delimiter = '\t')
        trigger = False
        cnt = 0
        cnt_crd = 0
        cnt_mis = 0
        cnt_tri = 0
        with open(output_name, 'w') as output_file:
            for row in tqdm(reader):
                writer = csv.writer(output_file, delimiter = '\t')
                if trigger:
                    cnt += 1
                    if ((len(row[3]) == 1) & (len(row[4]) == 1)) | ((row[3] == '.') & (row[4] == '.')) | (not(snp_only)):
                        rw = lo.convert_coordinate('chr' + str(row[0]), int(row[1]))
                        if rw:                   
                            row[1] = rw[0][1]
                            writer.writerow(row)
                            cnt_crd += 1
                        else:
                            cnt_mis +=1
                    else:
                        cnt_tri +=1
                if row[0] == '#CHROM':
                    writer.writerow(row)
                    trigger = True
    print('')
    print ('Cнипов перемещено = ', cnt_crd)
    print ('Снипов не найдено = ', cnt_mis)
    print ('Мультиаллельных пропущено = ', cnt_tri)

def update2vcf(input_name = '', output_name = '', sep = ' '):
    #Конвертирует txt файл в vcf требуется функция snp_recode выравнивает на 38 геном с hg18.
    if (input_name == '') or (output_name == ''):
        print ('File name missing')
        return
    header_vcf = ['#CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO', 'FORMAT']
    with open(input_name, 'r') as input_file:
        reader = csv.reader(input_file, delimiter = sep)
        cnt_crd = 0
        cnt_mis = 0
 
        with open(output_name, 'w') as output_file:
            for cnt, row in tqdm(enumerate(reader)):
                #if cnt > 10:
                #    break
                writer = csv.writer(output_file, delimiter = '\t')
                #print(row)
                if cnt == 0:
                    for sample in row[11:]:
                        header_vcf.append(sample)
                        
                    writer.writerow(header_vcf)
                
                else:
                    #print(row[3], row[4])
                    pos = lo18_38.convert_coordinate(row[2], int(row[3]))
                    if (pos != []) & (len(row[1]) == 3):
                        ref = row[1][0]
                        alt = row[1][-1]
                        out_row = [row[2][3:], pos[0][1], row[0], ref, alt,  '.', 'PASS', '.', 'GT']
                        for smpl in row[11:]:
                            out_row.append(snp_recode(smpl, ref, alt))
                            
                        cnt_crd += 1
                        writer.writerow(out_row)
                    else:
                        cnt_mis += 1

    print ('Строк включено = ', cnt_crd)
    print ('Снипов не включено = ', cnt_mis)
