# coding: utf-8
import configparser
import csv
import datetime
import json
import os
import requests

from iso639 import languages
import logging
from lxml import etree
from lxml.etree import Element

# Check and create logs directory
if os.path.exists('logs'):
    pass
else:
    os.mkdir('logs')

logging.basicConfig(
    filename='logs/scielobooks_onix_xml.info.txt', level=logging.INFO)
logger = logging.getLogger(__name__)


# Request
def request_book(host, port, sbid):
    jsondocs = {}
    try:
        # open the connection
        print('\n')
        msg = ('http://%s:%s/scielobooks_1a/%s' % (host, port, sbid))
        logger.info(msg)
        print(msg)

        r = requests.get('http://%s:%s/scielobooks_1a/%s' % (host, port, sbid))

        # reads the object
        jsondocs = r.json()

        # close the connection
        r.close()
    except requests.ConnectionError as e:
        msg = ('Erro na requisicao - sbid : %s - %s' % (sbid, e))
        logger.info(msg)
        print(msg)
        jsondocs = {}
    return jsondocs


def json2xml(config, sbidlist, demap):
    # Host and port of CouchDB service
    host = config['couchdb-books']['host']
    port = config['couchdb-books']['port']

    # Onix Elements
    onix = Element(
        'ONIXMessage',
        release="3.0",
        xmlns="http://ns.editeur.org/onix/3.0/reference")

    # Header Elements
    header = Element('Header')
    onix.append(header)

    sender = Element('Sender')
    header.append(sender)

    sendername = Element('SenderName')
    sendername.text = u'SciELO Books'
    sender.append(sendername)

    contactname = Element('ContactName')
    contactname.text = u'SciELO Team, tel. +55 11 5083 3639'
    sender.append(contactname)

    emailaddress = Element('EmailAddress')
    emailaddress.text = u'scielo.books@scielo.org'
    sender.append(emailaddress)

    addresses = Element('Addressee')
    header.append(addresses)

    addressesname = Element('AddresseeName')
    addressesname.text = u'SciELO Books'
    addresses.append(addressesname)

    sentdatetime = Element('SentDateTime')
    sentdatetime.text = datetime.datetime.today().strftime(
        "%Y%m%d" + "T" + "%H%M")
    header.append(sentdatetime)

    for sbid in sbidlist:
        sbid = sbid.strip()
        book = {}
        try:
            book = request_book(host, port, sbid)
            if '_id' in book:
                # Product Elements
                product = Element('Product')
                onix.append(product)
                if 'eisbn' in book:
                    recordreference = Element('RecordReference')
                    recordreference.text = book['eisbn']
                    product.append(recordreference)

                notificationtype = Element('NotificationType')
                notificationtype.text = u'03'
                product.append(notificationtype)

                recordsourcename = Element('RecordSourceName')
                recordsourcename.text = u'SciELO Books'
                product.append(recordsourcename)

                # ProductIdentifier ISBN
                productidentifier = Element('ProductIdentifier')
                product.append(productidentifier)

                productidtype = Element('ProductIDType')
                productidtype.text = u'03'
                productidentifier.append(productidtype)
                productidentifier.append(etree.Comment(' 03 is for GTIN-13 '))

                if 'eisbn' in book:
                    idvalue = Element('IDValue')
                    idvalue.text = book['eisbn']
                    productidentifier.append(idvalue)

                productidentifier = Element('ProductIdentifier')
                product.append(productidentifier)

                productidtype = Element('ProductIDType')
                productidtype.text = u'15'
                productidentifier.append(productidtype)
                productidentifier.append(etree.Comment(' 15 is for ISBN-13 '))

                if 'eisbn' in book:
                    idvalue = Element('IDValue')
                    idvalue.text = book['eisbn']
                    productidentifier.append(idvalue)

                # ProductIdentifier DOI
                productidentifier = Element('ProductIdentifier')
                product.append(productidentifier)

                productidtype = Element('ProductIDType')
                productidtype.text = u'06'
                productidentifier.append(productidtype)
                productidentifier.append(etree.Comment(' 06 is for DOI '))

                if 'doi_number' in book:
                    idvalue = Element('IDValue')
                    idvalue.text = book['doi_number'].replace(
                        'http://dx.doi.org/', '').replace(
                        'http://doi.org/', '').replace(
                        'https://doi.org/', '').replace(
                        'https://dx.doi.org/', '')

                    productidentifier.append(idvalue)

                product.append(etree.Comment('Block 1'))

                # DescriptiveDetail
                descriptivedetail = Element('DescriptiveDetail')
                product.append(descriptivedetail)

                productcomposition = Element('ProductComposition')
                productcomposition.text = '00'
                descriptivedetail.append(productcomposition)

                productform = Element('ProductForm')
                productform.text = u'ED'
                descriptivedetail.append(productform)

                productformdetail = Element('ProductFormDetail')
                productformdetail.text = config[
                    'books.scielo']['productformdetail']
                descriptivedetail.append(productformdetail)
                descriptivedetail.append(
                    etree.Comment(' E101 EPUB, E107 PDF '))

                primarycontenttype = Element('PrimaryContentType')
                primarycontenttype.text = u'10'
                descriptivedetail.append(primarycontenttype)

                if 'is_comercial' in book:
                    if book['is_comercial'] is False:
                        epublicense = Element('EpubLicense')
                        descriptivedetail.append(epublicense)

                        epublicensename = Element('EpubLicenseName')
                        epublicensename.text = u'cc by'
                        epublicense.append(epublicensename)

                        epublicenseexpression = Element(
                            'EpubLicenseExpression')
                        epublicense.append(epublicenseexpression)

                        epublicenseexpressiontype = Element(
                            'EpubLicenseExpressionType')
                        epublicenseexpressiontype.text = u'02'
                        epublicenseexpression.append(epublicenseexpressiontype)

                        epublicenseexpressionlink = Element(
                            'EpubLicenseExpressionLink')
                        epublicenseexpressionlink.text = book['use_licence']
                        epublicenseexpression.append(epublicenseexpressionlink)

                # Collection
                if ('collection' in book):
                    for k in book['collection']:
                        if k[0] == 'title':
                            if k[1] is not None:

                                collection = Element('Collection')
                                descriptivedetail.append(collection)

                                collectiontype = Element('CollectionType')
                                collectiontype.text = u'10'
                                collection.append(collectiontype)

                                titledetail_col = Element('TitleDetail')
                                collection.append(titledetail_col)

                                titletype = Element('TitleType')
                                titletype.text = u'01'
                                titledetail_col.append(titletype)

                                titleelement = Element('TitleElement')
                                titledetail_col.append(titleelement)

                                sequencenumber = Element('SequenceNumber')
                                sequencenumber.text = u'1'
                                titleelement.append(sequencenumber)

                                titleelementlevel = Element(
                                    'TitleElementLevel')
                                titleelementlevel.text = u'02'
                                titleelement.append(titleelementlevel)

                                lang = None
                                if 'language' in book:
                                    lang = languages.get(
                                        alpha2=book['language'])
                                    titletext = Element(
                                        'TitleText',
                                        language=lang.bibliographic)
                                    titletext.text = k[1]
                                    titleelement.append(titletext)
                            else:
                                nocollection = Element('NoCollection')
                                descriptivedetail.append(nocollection)
                                break

                # DescriptiveDetail/TitleDetail
                titledetail = Element('TitleDetail')
                descriptivedetail.append(titledetail)

                titletype = Element('TitleType')
                titletype.text = u'01'
                titledetail.append(titletype)

                titleelement = Element('TitleElement')
                titledetail.append(titleelement)

                titleelementlevel = Element('TitleElementLevel')
                titleelementlevel.text = u'01'
                titleelement.append(titleelementlevel)

                if 'title' in book:
                    titletext = Element('TitleText')
                    titletext.text = book['title'].split(':')[0].strip(' ')
                    titleelement.append(titletext)

                    if ':' in book['title']:
                        subtitle = Element('Subtitle')
                        subtitle.text = book['title'].split(':')[1].strip(' ')
                        titleelement.append(subtitle)

                # DescriptiveDetail/Creators
                if 'creators' in book:

                    contribrole_code = {
                        'individual_author': u'A01',
                        'corporate_author': u'A01',
                        'translator': u'B06',
                        'organizer': u'B01',
                        'coordinator': u'B15',
                        'editor': u'B21',
                        'collaborator': u'Z99',
                        'other': u'Z99'}

                    number = 1

                    for authors in book['creators']:

                        contributor = Element('Contributor')
                        descriptivedetail.append(contributor)

                        sequencenumber = Element('SequenceNumber')
                        contributorrole = Element('ContributorRole')
                        personname = Element('PersonName')
                        personnameinverted = Element('PersonNameInverted')

                        for key in authors:

                            if key[0] == 'full_name':
                                sequencenumber.text = str(number)
                                number += 1

                            if key[0] == 'role':
                                contributorrole.text = contribrole_code[
                                    key[1].lower()]

                            if key[0] == 'full_name' and ',' in key[1]:
                                personname.text = (
                                    key[1].split(', ')[1]) + ' ' + (
                                    key[1].split(', ')[0])
                            elif key[0] == 'full_name' and ',' not in key[1]:
                                personname.text = key[1]

                            if key[0] == 'full_name' and ',' in key[1]:
                                personnameinverted.text = key[1]

                        # append in XML
                        if sequencenumber.text:
                            contributor.append(sequencenumber)
                        if contributorrole.text:
                            contributor.append(contributorrole)
                        if personname.text:
                            contributor.append(personname)
                        if personnameinverted.text:
                            contributor.append(personnameinverted)

                # DescriptibeDetail/EditionType
                editiontype = Element('EditionType')
                editiontype.text = u'NED'
                descriptivedetail.append(editiontype)

                # DescriptibeDetail/EditionNumber
                edition = None
                if 'edition' in book:
                    for n in book['edition']:
                        try:
                            edition = int(n)
                        except:
                            pass
                if edition:
                    editionnumber = Element('EditionNumber')
                    editionnumber.text = str(edition)
                    descriptivedetail.append(editionnumber)

                if 'language' in book:
                    language = Element('Language')
                    descriptivedetail.append(language)

                    languagerole = Element('LanguageRole')
                    languagerole.text = u'01'
                    language.append(languagerole)

                    languagecode = Element('LanguageCode')
                    lang = languages.get(alpha2=book['language'])
                    languagecode.text = lang.bibliographic
                    language.append(languagecode)

                if 'pages' in book:
                    extent = Element('Extent')
                    descriptivedetail.append(extent)

                    extenttype = Element('ExtentType')
                    extenttype.text = u'11'
                    extent.append(extenttype)

                    extentvalue = Element('ExtentValue')
                    extentvalue.text = book['pages']
                    extent.append(extentvalue)

                    extentunit = Element('ExtentUnit')
                    extentunit.text = u'03'
                    extent.append(extentunit)

                if 'bisac_code' in book:

                    subject = Element('Subject')
                    descriptivedetail.append(subject)

                    mainsubject = Element('MainSubject')
                    subject.append(mainsubject)

                    subject.append(etree.Comment(' BISAC classification '))

                    subjectschemeidentifier = Element(
                        'SubjectSchemeIdentifier')
                    subjectschemeidentifier.text = u'10'
                    subject.append(subjectschemeidentifier)

                    for code in book['bisac_code']:
                        for key in code:
                            subjectcode = Element('SubjectCode')
                            subjectcode.text = key[1]
                            subject.append(subjectcode)
                # Block 2
                product.append(etree.Comment('Block 2'))

                collateraldetail = Element('CollateralDetail')
                product.append(collateraldetail)

                textcontent = Element('TextContent')
                collateraldetail.append(textcontent)

                texttype = Element('TextType')
                texttype.text = u'03'
                textcontent.append(texttype)

                contentaudience = Element('ContentAudience')
                contentaudience.text = u'00'
                textcontent.append(contentaudience)

                if 'synopsis' in book:
                    text = Element('Text')
                    text.text = book['synopsis']
                    textcontent.append(text)

                # SupportingResource
                supportingresource = Element('SupportingResource')
                collateraldetail.append(supportingresource)

                resourcecontenttype = Element('ResourceContentType')
                resourcecontenttype.text = u'01'
                supportingresource.append(resourcecontenttype)

                contentaudience = Element('ContentAudience')
                contentaudience.text = u'00'
                supportingresource.append(contentaudience)

                resourcemode = Element('ResourceMode')
                resourcemode.text = u'03'
                supportingresource.append(resourcemode)

                resourceversion = Element('ResourceVersion')
                supportingresource.append(resourceversion)

                resourceform = Element('ResourceForm')
                resourceform.text = u'01'
                resourceversion.append(resourceform)

                resourceversionfeature = Element('ResourceVersionFeature')
                resourceversion.append(resourceversionfeature)

                resourceversionfeaturetype = Element(
                    'ResourceVersionFeatureType')
                resourceversionfeaturetype.text = u'01'
                resourceversionfeature.append(resourceversionfeaturetype)

                featurevalue = Element('FeatureValue')
                featurevalue.text = u'D502'
                resourceversionfeature.append(featurevalue)

                resourcelink = Element('ResourceLink')
                website = config['books.scielo']['host']
                resourcelink.text = (
                    '%s/id/%s/cover/cover.jpeg' % (website, sbid))
                resourceversion.append(resourcelink)

                # Block 4
                product.append(etree.Comment('Block 4'))

                publishingdetail = Element('PublishingDetail')
                product.append(publishingdetail)

                if 'publisher' in book:
                    imprint = Element('Imprint')
                    publishingdetail.append(imprint)

                    imprintname = Element('ImprintName')
                    imprintname.text = book['publisher']
                    imprint.append(imprintname)

                    publisher = Element('Publisher')
                    publishingdetail.append(publisher)

                    publishingrole = Element('PublishingRole')
                    publishingrole.text = u'01'
                    publisher.append(publishingrole)

                    publishername = Element('PublisherName')
                    pub = json.load(open('publishers.json'))
                    if pub[book['publisher']]:
                        publishername.text = pub[book['publisher']]
                    else:
                        publishername.text = book['publisher']

                    publisher.append(publishername)

                    publishingstatus = Element('PublishingStatus')
                    publishingstatus.text = u'04'
                    publishingdetail.append(publishingstatus)

                    publishingdate = Element('PublishingDate')
                    publishingdetail.append(publishingdate)

                    publishingdaterole = Element('PublishingDateRole')
                    publishingdaterole.text = u'01'
                    publishingdate.append(publishingdaterole)

                    dateformat = Element('DateFormat')
                    dateformat.text = u'00'
                    publishingdate.append(dateformat)

                    if 'year' in book:
                        date = Element('Date')
                        date.text = book['year'] + '0101'
                        publishingdate.append(date)

                salesrights = Element('SalesRights')
                publishingdetail.append(salesrights)

                salesrightstype = Element('SalesRightsType')
                salesrightstype.text = u'01'
                salesrights.append(salesrightstype)

                territory = Element('Territory')
                salesrights.append(territory)

                # Check if has rules for this SBID
                if sbid in demap.keys():

                    if 'countriesincluded' in demap[sbid][0]:
                        countriesincluded = Element('CountriesIncluded')
                        countriesincluded.text = demap[sbid][0]['countriesincluded']
                        territory.append(countriesincluded)

                    if 'countriesexcluded' in demap[sbid][0]:
                        regionsincluded = Element('RegionsIncluded')
                        regionsincluded.text = u'WORLD'
                        territory.append(regionsincluded)

                        countriesexcluded = Element('CountriesExcluded')
                        countriesexcluded.text = demap[sbid][0]['countriesexcluded']
                        territory.append(countriesexcluded)

                else:
                    regionsincluded = Element('RegionsIncluded')
                    regionsincluded.text = u'WORLD'
                    territory.append(regionsincluded)

                # Block 5
                product.append(etree.Comment(
                    'Block 5 - Related material not required if book is digital-only'))

                # Se ISBN existir
                if 'isbn' in book:
                    relatedmaterial = Element('RelatedMaterial')
                    product.append(relatedmaterial)

                    relatedproduct = Element('RelatedProduct')
                    relatedmaterial.append(relatedproduct)

                    productrelationcode = Element('ProductRelationCode')
                    productrelationcode.text = u'13'
                    relatedproduct.append(productrelationcode)

                    productidentifier = Element('ProductIdentifier')
                    relatedproduct.append(productidentifier)

                    productidtype = Element('ProductIDType')
                    if len(book['isbn']) == 10:
                        productidtype.text = u'02'
                    if len(book['isbn']) == 13:
                        productidtype.text = u'15'
                    productidentifier.append(productidtype)

                    idvalue = Element('IDValue')
                    idvalue.text = book['isbn']
                    productidentifier.append(idvalue)

                # Block 6
                product.append(etree.Comment('Block 6'))

                productsupply = Element('ProductSupply')
                product.append(productsupply)

                supplydetail = Element('SupplyDetail')
                productsupply.append(supplydetail)

                supplier = Element('Supplier')
                supplydetail.append(supplier)

                supplierrole = Element('SupplierRole')
                supplierrole.text = u'03'
                supplier.append(supplierrole)

                suppliername = Element('SupplierName')
                suppliername.text = u'SciELO Books'
                supplier.append(suppliername)

                websitetag = Element('Website')
                supplier.append(websitetag)

                websiterole = Element('WebsiteRole')
                websiterole.text = u'29'
                websitetag.append(websiterole)

                websitedescription = Element('WebsiteDescription')
                websitedescription.text = u"Metadata and book's page in SciELO Books"
                websitetag.append(websitedescription)

                websitelink = Element('WebsiteLink')
                website = config['books.scielo']['host']
                websitelink.text = ('%s/id/%s' % (website, sbid))
                websitetag.append(websitelink)

                productavailability = Element('ProductAvailability')
                productavailability.text = u'20'
                supplydetail.append(productavailability)

                # # UnpricedItemType
                # if book['price_dollar'] == '0.00' and book['price_reais'] == '0.00':
                #     unpriceditemtype = Element('UnpricedItemType')
                #     unpriceditemtype.text = u'01'
                #     supplydetail.append(unpriceditemtype)

                # Price Dollar
                # if book['price_dollar'] != '0.00':
                price = Element('Price')
                supplydetail.append(price)

                pricetype = Element('PriceType')
                pricetype.text = u'01'
                price.append(pricetype)

                priceamount = Element('PriceAmount')
                priceamount.text = book['price_dollar']
                price.append(priceamount)

                currencycode = Element('CurrencyCode')
                currencycode.text = u'USD'
                price.append(currencycode)

                territory = Element('Territory')
                price.append(territory)

                regionsincluded = Element('RegionsIncluded')
                regionsincluded.text = u'WORLD'
                territory.append(regionsincluded)

                if book['price_reais'] != '0.00':
                    countriesexcluded = Element('CountriesExcluded')
                    countriesexcluded.text = u'BR'
                    territory.append(countriesexcluded)

                # Price Reais
                # if book['price_reais'] != '0.00':
                price = Element('Price')
                supplydetail.append(price)

                pricetype = Element('PriceType')
                pricetype.text = u'01'
                price.append(pricetype)

                priceamount = Element('PriceAmount')
                priceamount.text = book['price_reais']
                price.append(priceamount)

                currencycode = Element('CurrencyCode')
                currencycode.text = u'BRL'
                price.append(currencycode)

                territory = Element('Territory')
                price.append(territory)

                if book['price_dollar'] == '0.00':
                    regionsincluded = Element('RegionsIncluded')
                    regionsincluded.text = u'WORLD'
                    territory.append(regionsincluded)

                if book['price_dollar'] != '0.00':
                    countriesinclude = Element('CountriesIncluded')
                    countriesinclude.text = u'BR'
                    territory.append(countriesinclude)
            else:
                msg = ("%s SBID Not found." % sbid)
                logger.info(msg)
                print(msg)
        except Exception as e:
            print(e)
            logger.info(e)
            continue

    # Generates the XML
    return etree.tostring(onix,
                          pretty_print=True,
                          xml_declaration=False,
                          encoding='utf-8')


def main():
    # Format ISO date
    dateiso = datetime.datetime.now().strftime('%Y%m%d')

    # Config
    config = configparser.ConfigParser()
    config._interpolation = configparser.ExtendedInterpolation()
    config.read('config.ini')

    # Folder and file names
    if config['paths']['sbidlistname'] == '':
        print('sbidlistname=empty.\nEnter the sbid list name in config.ini.')
        exit()

    xmlfilename = config['paths']['xmlfilename']

    xmlfolder = config['paths']['xmlfoldername']

    if config['paths']['prefix'] == 'yes':
        if config['paths']['xmlfilename'] == '':
            xmlfilename = dateiso
        else:
            xmlfilename = ('%s_%s' % (dateiso, xmlfilename))

    if config['paths']['prefix'] == 'no':
        if config['paths']['xmlfilename'] == '':
            print('xmlfilename = empty.\nEnter a name in config.ini.')
            exit()

    if config['paths']['prefix'] == '':
        if config['paths']['xmlfilename'] == '':
            print('xmlfilename = empty.\nEnter a name in config.ini.')
            exit()

    if config['books.scielo']['productformdetail'] == '':
        print('productformdetail = empty.\n\
Enter a code in config.ini.\n\
Use E101 for EPUB or E107 for PDF')
        exit()

    xmlout = ('%s/%s.xml' % (xmlfolder, xmlfilename))

    print('\nfolder/xmlfile: %s\n' % xmlout)

    # CSV Data Entry Map
    demap = {}
    csvdelimiter = config['paths']['csvdelimiter']
    with open(config['paths']['sourcepath']) as f:
        csvReader = csv.DictReader(f, delimiter=csvdelimiter)
        for rows in csvReader:
            rows = {k: v for k, v in rows.items() if v}
            sbid = rows['sbid']
            if sbid not in demap.keys():
                demap.update({sbid:[]})
            rows.pop('sbid')
            demap[sbid].append(rows)
    f.close()

    # SBID List
    with open(config['paths']['sbidlistname']) as f:
        sbidlist = [line.strip() for line in f]
    f.close()

    print('SBID list: ')

    for i in sbidlist:
        print(i)

    # Build XML object
    xmldocs = json2xml(config=config, sbidlist=sbidlist, demap=demap)

    # Check and create xml folder output
    if xmldocs:
        if os.path.exists(xmlfolder):
            pass
        else:
            os.mkdir(xmlfolder)

    # Write the XML file
    with open(xmlout, encoding='utf-8-sig', mode='w') as f:

        # Declaration with quotation marks
        f.write(u'<?xml version="1.0" encoding="utf-8"?>\n')

        f.write(xmldocs.decode('utf-8'))

    f.close()


if __name__ == "__main__":
    main()
