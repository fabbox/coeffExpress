#!/usr/bin/python

import html5lib
from urllib.request import urlopen
import re
import json

def clean_text(in_str):
    # remove "()" stuff
    in_str = re.sub('\(.*\)', '', in_str)
    in_str = re.sub('\n', '', in_str)
    in_str = in_str.strip()
    return in_str


def build_ecricome_table(ecricome_url):

    with urlopen(ecricome_url) as f:
        transport_encoding = f.info().get_content_charset()
        document = html5lib.parse(f, transport_encoding=transport_encoding)

    # find table (here table contain coeff)
    div_main = document.findall(".//*[@class='main']")
    list_table = div_main[0].findall(".//*{http://www.w3.org/1999/xhtml}table")

    # extract table data
    my_table = {}
    for table in list_table:

        lines = table.findall(".//{http://www.w3.org/1999/xhtml}tr")

        my_lines = []

        cap = table.findall(".//{http://www.w3.org/1999/xhtml}caption")[0]
        mstr = get_text(cap)
        if mstr.lower() == "scientifiques":
            key = 'sci'
        elif mstr.lower() == "économiques":
            key = 'eco'
        elif mstr.lower() == "technologiques":
            key = 'tech'

#        my_lines.append(mstr)

        header = []
        for idx, head in enumerate(lines[0].findall(".//{http://www.w3.org/1999/xhtml}th")):
            mstr = get_text(head)
            if idx != 0:
                mstr = school2id(mstr)
            header.append(mstr)
        my_lines.append(header)

        for line in lines[1:]:
            cols = []
            for idx, col in enumerate(line.findall(".//{http://www.w3.org/1999/xhtml}td")):
                txt = get_text(col)
                if idx == 0:
                    txt = clean_header(txt)
                cols.append(clean_text(txt))

            my_lines.append(cols)

        for i, l in enumerate(my_lines):
            if i == 0:
                continue
            my_lines[i][0] = epreuves2matieres(l[0])

#        my_lines

        my_table[key] = my_lines

    ecoles = {}
    ecoles['id'] = {}
    ecoles['filiere'] = {}

    school_id = my_table[key][0][1:]


    for idx, k in enumerate(my_table):
        table = my_table[k]
        filiere = k
        # build dict for
        coeff = {}
        for i in table[1:-1]:
            coeff[i[0]] = [ int(x) for x in i[1:]]

        sommeCoeff = []
        for i, c in enumerate(coeff):
            if i == 0:
                for v in coeff[c]:
                    sommeCoeff.append(v)
            else:
                for j, v in enumerate(coeff[c]):
                    sommeCoeff[j] += v

#    for idx, filiere in enumerate(filieres):
#        bce_url_key = bce_url + keys[idx]

#        school_id, coeff, sommeCoeff = get_bce_dict(bce_url_key)

        if idx == 0:
            ecoles['id'] = school_id
        else:
            for idx_ecole, school in enumerate(ecoles['id']):
                assert(school == school_id[idx_ecole])

        ecoles['filiere'][filiere] = {}
        ecoles['filiere'][filiere]['matieres'] = list(coeff.keys())
        ecoles['filiere'][filiere]['coeff'] = coeff
        ecoles['filiere'][filiere]['sommeCoeff'] = sommeCoeff

    # add cg for ect with coeff 0
    ecoles['filiere']['tech']['matieres'].append('cg')
    ecoles['filiere']['tech']['coeff']['cg'] = [0, 0]

    return ecoles


def get_text(cell):
    txt = ""
    for stxt in cell.itertext():
        txt += stxt
    return clean_text(txt)


def get_page_as_element(url):
    with urlopen(url) as f:
        transport_encoding = f.info().get_content_charset()
        document = html5lib.parse(f, transport_encoding=transport_encoding)
#    return document
    body = document.find(".//{http://www.w3.org/1999/xhtml}body")
    return body


def clean_header(in_str):
    """ remove part of string to rewrite uniform header
    """
    to_remove = ['EDHEC',  # must be before HEC
                 'HEC',
                 'ESCP Europe',
                 'ESC',
                 'ESSEC',
                 'EMLyon',
                 'emlyon',
                 'SKEMA',
                 'GRENOBLE',
                 'STRASBOURG',
                 'LA ROCHELLE',
                 'SCBS',
                 'ELVi',
                 'IENA',
                 '/']
    for r in to_remove:
        in_str = re.sub(r, '', in_str)
    in_str = re.sub('Mathématiques.*$', 'Mathématiques', in_str)
    in_str = re.sub('Synthèse de textes', 'Contraction de texte', in_str)
    in_str = re.sub('Résumé de texte', 'Contraction de texte', in_str)
    in_str = in_str.strip()
    return in_str


def school2id(sstr):

    possible_sstr = \
        [
         'NEOMA Business School',
         'KEDGE Business School',
         'École de Management de NORMANDIE',
         'LA ROCHELLE business school',
         'Groupe ESC CLERMONT',
         'ISC PARIS Business School',
         'SOUTH CHAMPAGNE BUSINESS SCHOOL',
         'EM Strasbourg Business School',
         'Montpellier Business School',
         'RENNES School of Business',
         'AUDENCIA Business School',
         'BREST Business School',
         'BSB Burgundy School of Business',
         'EDHEC Business School',
         'emlyon business school',
         'ESCP Europe',
         'ESSEC Business School',
         'GRENOBLE Ecole de Management',
         'ESC PAU Business School',
         'HEC Paris',
         'ICN Business School',
         'INSEEC school of business and economics',
         'ISG International Business School',
         'SKEMA Business School',
         'institut mines-télécom business school',
         'TOULOUSE Business School'
         ]

    low_poss_str = [ x.lower() for x in possible_sstr]
    ids = [
        "neoma",
        "kedge",
        "emnormandie",
        "esclarochelle",
        "escclermont",
        "iscparis",
        "esctroyes",
        "emstrasbourg",
        "montpellierbs",
        "escrennes",
        "audencia",
        "brestbs",
        "escdijon",
        "edhec",
        "emlyon",
        "escpeurope",
        "essec",
        "grenoblebs",
        "escpau",
        "hecparis",
        "icnbs",
        "inseec",
        "isg",
        "skemabs",
        "telecommgmt",
        "toulousebs"
        ]

    return ids[low_poss_str.index(sstr.lower())]

def epreuves2matieres(mstr):

    epreuve = {
                'math': ['Mathématiques'],
                'philo': ['Culture Générale', 'Diss. culture générale'],
                'cg': ['Contraction de texte'],
                'lv1': ['LV1', 'Langue vivante I'],
                'lv2': ['LV2', 'Langue vivante II'],
                'esh': ['Eco., socio. et histoire', 'Économie, sociologie et  histoire du monde contemporain'],
                'mgmt': ['Management et gestion', 'Management et sciences de gestion'],
                'eco': ['Économie et Droit', 'Economie, Droit' ],
                'hgg': ['Histoire Géographie et géopolitique du monde contemporain', 'Hist., géo. et géopolitique']
                }

    for matiere in epreuve:
        if mstr in epreuve[matiere]:
            return matiere

    print('Course "' + mstr + '" -> Nothing found')
    return mstr


def get_bce_dict(bce_url_key):
    document = get_page_as_element(bce_url_key) # body
#    document

    table = document.find(".//{http://www.w3.org/1999/xhtml}table")

#    table

    lines = table.findall(".//{http://www.w3.org/1999/xhtml}tr")

    my_lines = []

    header = []
    for head in lines[0].findall(".//{http://www.w3.org/1999/xhtml}th"):
        mstr = get_text(head)
        mstr = clean_header(mstr)
        mstr = epreuves2matieres(mstr)
        header.append(mstr)
    my_lines.append(header)

    for line in lines[1:]:
        cols = []
        for col in line.findall(".//{http://www.w3.org/1999/xhtml}td"):
            cols.append(get_text(col))

        my_lines.append(cols)

    if my_lines[-1][0].find('SAINT-CYR') != -1:
        print('Remove saint SAINT-CYR')
        del my_lines[-1]
    if my_lines[-1][0].find('ENSAE ParisTech') != -1:
        print('Remove ENSAE ParisTech')
        del my_lines[-1]

    # clean string in table
    tab_head = my_lines[0]
    my_set = set(my_lines[0])
    my_set.remove('Ecole')


    idx_set = []
    for i in my_set:
        slist = []
        k = 0
        for j in range(tab_head.count(i)):
            k = tab_head.index(i, k)
            slist.append(k)
            k += 1
        idx_set.append(slist)
#    print(idx_set)

    new_table = []
    my_line = []
    # first line
    my_line.append('Ecole')
    for i in my_set:
        my_line.append(i)

    new_table.append(my_line)

    for i_s in range(1, len(my_lines)):  # loop on school
        my_line = []
        my_line.append(my_lines[i_s][0])
        # loop on "matière"
        for m in range(len(idx_set)):
            midx_set = idx_set[m]
            coeff = 0
            # loop on coeff by matière
            for c in midx_set:
                if my_lines[i_s][c] != '':
                    coeff += int(my_lines[i_s][c])
            my_line.append(coeff)
        new_table.append(my_line)

    table = []
    # transpose table
    for j in range(len(new_table[0])):
        line = []
        for i in range(len(new_table)):
            if i != 0 and j == 0:
                val = school2id(new_table[i][j])
            else:
                val = new_table[i][j]
            line.append(val)

        table.append(line)

    school_id = table[0][1:]

    # build dict for
    coeff = {}
    for i in table[1:]:
        coeff[i[0]] = i[1:]

    sommeCoeff = []
    for i, c in enumerate(coeff):
        if i == 0:
            for v in coeff[c]:
                sommeCoeff.append(v)
        else:
            for j, v in enumerate(coeff[c]):
                sommeCoeff[j] += v

    return school_id, coeff, sommeCoeff

def get_bce(bce_url):
    filieres = ['eco', 'sci', 'tech']

    ecoles = {}
    ecoles['id'] = []
    ecoles['filiere'] = {}

#    bce_url = "http://concours-bce.com/epreuves_ecrites/"
    keys = ['ece', 'ecs', 'ect']


    for idx, filiere in enumerate(filieres):
        bce_url_key = bce_url + keys[idx]

        school_id, coeff, sommeCoeff = get_bce_dict(bce_url_key)

        if idx == 0:
            ecoles['id'] = school_id
        else:
            for idx_ecole, school in enumerate(ecoles['id']):
                assert(school == school_id[idx_ecole])

        ecoles['filiere'][filiere] = {}
        ecoles['filiere'][filiere]['matieres'] = list(coeff.keys())
        ecoles['filiere'][filiere]['coeff'] = coeff
        ecoles['filiere'][filiere]['sommeCoeff'] = sommeCoeff

    return ecoles

def add_dict(dik, dik2):
    for k in dik:
        if isinstance(dik[k], list):
            dik[k] += dik2[k]
            if k == 'matieres':
                dik[k] = list(set(dik[k]))
        else:
#            print(type(dik[k]))
            dik[k] = add_dict(dik[k], dik2[k])
    return dik


def print_list_str(dik, key, offset=0, last=False):
    mstr = offset*' ' + key + ': ' + re.sub("'", '"', repr(dik[key]))
    if last:
        print(mstr)
    else:
        print(mstr + ",")

def print_coeff(coeff, last=False):
    key = "coeff"
    print(15*' ' + key + ': {')
    slast = False
    for idx, k in enumerate(coeff):
        if idx == len(coeff) - 1:
            slast = True
        print_arr(k, coeff[k], offset=17, last=slast)

    print(15*' ' + "     },")  # close coeff

def print_arr(key, arr, offset=0, last=False):
    mstr = offset * ' ' + key + ': ' +  repr(arr)
    if last:
        print(mstr)
    else:
        print(mstr + ",")


def print_sommeCoeff(fil, offset=15, last=True):
    key = "sommeCoeff"
    arr = fil[key]
    print_arr(key, arr, offset=offset, last=last)


def print_spe(idx, spe, fil):
    print(5*' ' + spe + ': {')
    print_list_str(fil, 'matieres', offset=15)
    print_coeff(fil['coeff'])
    print_sommeCoeff(fil)
    if idx < 2:
        print(10*' ' + '},') # close spe
    else:
        print(10*' ' + '}')  # close spe


if __name__ == "__main__":
    ecricome_url = "https://www.ecricome.org/" \
        + "epreuves-et-coefficients-ecricome-prepa"
    ecricome = build_ecricome_table(ecricome_url)
#    print(repr(ecricome))


    bce_url = "http://concours-bce.com/epreuves_ecrites/"
    bce = get_bce(bce_url)
#    print(repr(bce))

    ecoles = add_dict(ecricome, bce)
    ecoles['filiere']['tech']['matieres'].append('droit')
    ecoles['filiere']['tech']['coeff']['eco'] = \
        [ x/2 for x in ecoles['filiere']['tech']['coeff']['eco']]
    ecoles['filiere']['tech']['coeff']['droit'] = \
        ecoles['filiere']['tech']['coeff']['eco']

#    print(ecoles)



    print('')
    print(70 * '-')
    print('')
    # print to export
    print("var ecoles = {")
    key = "id"
    print(key + ': ' + re.sub("'", '"', repr(ecoles[key])) + ",")
    key = "filiere"
    print(key + ': {')
    for idx, spe in enumerate(ecoles[key]):
        print_spe(idx, spe, ecoles[key][spe])
    print("     }")  # close filieres
    print("};")   # close ecole
