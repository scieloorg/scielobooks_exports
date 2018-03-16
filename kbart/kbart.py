# coding: utf-8
import os
import configparser
import datetime
import csv

import requests

# Config
config = configparser.ConfigParser()
config._interpolation = configparser.ExtendedInterpolation()
config.read('config.ini')


def request_book(host, port, sbid):
    jsondocs = {}
    try:
        # open the connection
        print('\nhttp://%s:%s/scielobooks_1a/%s' % (host, port, sbid))
        r = requests.get('http://%s:%s/scielobooks_1a/%s' % (host, port, sbid))

        # reads the object
        jsondocs = r.json()

        # close the connection
        r.close()
    except requests.ConnectionError as e:
        print('Erro na requisicao - sbid : %s - %s' % (sbid, e))
        jsondocs = {}

    return jsondocs


def json2kbart(sbidlist):
    # Host and port of CouchDB service
    host = config['couchdb-books']['host']
    port = config['couchdb-books']['port']

    # CSV header
    header = [
        'publication_title',  # title
        'print_identifier',  # isnb
        'online_identifier',  # eisbn
        'date_first_issue_online',  # vazio
        'num_first_vol_online',  # vazio
        'num_first_issue_online',  # vazio
        'date_last_issue_online',  # vazio
        'num_last_vol_online',  # vazio
        'num_last_issue_online',  # vazio
        'title_url',  # URL completa do livro
        'first_author',  # Apenas o primeiro autor do campo "creators"
        'title_id',  # SBID
        'embargo_info',  # vazio
        'coverage_depth',  # vazio
        'coverage_notes',  # vazio
        'publisher_name',  # -- # "publisher"
        'publication_type',  # -- Sempre será "Monograph"
        'date_monograph_published_print',  # -- "year" (ano do livro)
        'date_monograph_published_online',  # -- "publication_date"
        'monograph_volume',  # vazio
        'monograph_edition',  # -- "edition"
        'first_editor',  # vazio
        'parent_publication_title_id',  # vazio
        'preceding_publication_title_id',  # vazio
        'access_type'  # F "is_comercial": false. P "is_comercial": true
        ]

    # Create the KBART file
    folder = config['paths']['kbartfoldername']
    if os.path.exists(folder):
        pass
    else:
        os.mkdir(folder)

    name = config['paths']['kbartfilename']

    dateiso = datetime.datetime.now().strftime('%Y%m%d')

    kbartfile = ('%s/%s_%s.txt' % (folder, name, dateiso))

    with open(kbartfile, 'w', encoding='utf-8') as csv_utf:

        spamwriter_utf = csv.writer(csv_utf, delimiter='\t')

        # Write the reader
        spamwriter_utf.writerow(header)

        # SciELO Books
        for sbid in sbidlist:
            sbid = sbid.strip()
            book = {}
            book = request_book(host, port, sbid)

            publication_title = None
            if 'title' in book:
                publication_title = book['title']

            print_identifier = None
            if 'isbn' in book:
                print_identifier = book['isbn']

            online_identifier = None
            if 'eisbn' in book:
                online_identifier = book['eisbn']

            website = config['books.scielo']['host']
            title_url = ('%s/id/%s' % (website, sbid))

            first_author = None
            if 'creators' in book:
                flag = 0
                for authors in book['creators']:
                    for key in authors:
                        if key[0] == 'full_name' and flag == 0:
                            first_author = key[1]
                            flag = 1

            publisher_name = None
            if 'publisher' in book:
                publisher_name = book['publisher']

            date_monograph_published_print = None
            if 'year' in book:
                date_monograph_published_print = book['year']

            date_monograph_published_online = None
            if 'publication_date' in book:
                date_monograph_published_online = book['publication_date']

            monograph_edition = None
            if 'edition' in book:
                monograph_edition = book['edition']

            access_type = None
            if 'is_comercial' in book:
                if book['is_comercial'] is True:
                    access_type = 'P'
                if book['is_comercial'] is False:
                    access_type = 'F'

            # CSV content
            content = [
                publication_title or u'',
                print_identifier or u'',
                online_identifier or u'',
                u'',
                u'',
                u'',
                u'',
                u'',
                u'',
                title_url or u'',
                first_author or u'',
                sbid or u'',
                u'',
                u'',
                u'',
                publisher_name or u'',
                'Monograph',
                date_monograph_published_print or u'',
                date_monograph_published_online or u'',
                u'',
                monograph_edition or u'',
                u'',
                u'',
                u'',
                access_type or u'']

            spamwriter_utf.writerow([l for l in content])


def main():
    # SBID List
    with open(config['paths']['sbidlistname']) as f:
        sbidlist = [line.strip() for line in f]
    f.close()

    # Build KBART
    json2kbart(sbidlist)

if __name__ == "__main__":
    main()
