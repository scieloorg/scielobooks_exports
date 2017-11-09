# coding: utf-8
import os
import configparser
import requests
import datetime

from lxml.etree import Element
from lxml import etree
from iso639 import languages


# Request
def request_book(host, port, sbid):
    jsondocs = {}
    try:
        # open the connection
        print('\nhttp://{0}:{1}/scielobooks_1a/{2}'.format(host, port, sbid))
        r = requests.get('http://%s:%s/scielobooks_1a/%s' % (host, port, sbid))

        # reads the object
        jsondocs = r.json()

        # close the connection
        r.close()
    except requests.ConnectionError as e:
        print('Erro na requisicao - sbid : %s - %s' % (sbid, e))
        jsondocs = {}

    return jsondocs


def json2xml(host, port, sbidlist, website):

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

    sentdate = Element('SentDate')
    sentdate.text = datetime.datetime.today().strftime("%Y%m%d%H%M")
    header.append(sentdate)

    for sbid in sbidlist:
        sbid = sbid.strip()
        book = {}
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

            # ProductIdentifier ISBN
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
                    'http://dx.doi.org/', '')
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
            productformdetail.text = u'E101'
            descriptivedetail.append(productformdetail)
            descriptivedetail.append(etree.Comment(' E101 EPUB, E107 PDF '))

            primarycontenttype = Element('PrimaryContentType')
            primarycontenttype.text = u'10'
            descriptivedetail.append(primarycontenttype)

            # Collection
            if 'collection' in book:
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

                            titleelementlevel = Element('TitleElementLevel')
                            titleelementlevel.text = u'02'
                            titleelement.append(titleelementlevel)

                            lang = None
                            if 'language' in book:
                                lang = languages.get(alpha2=book['language'])
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
                number = 1
                for authors in book['creators']:
                    contributor = Element('Contributor')
                    descriptivedetail.append(contributor)

                    for key in authors:
                        if key[0] == 'full_name':
                            sequencenumber = Element('SequenceNumber')
                            sequencenumber.text = str(number)
                            contributor.append(sequencenumber)

                            contributorrole = Element('ContributorRole')
                            contributorrole.text = u'A01'
                            contributor.append(contributorrole)

                            personname = Element('PersonName')
                            if ',' in key[1]:
                                personname.text = (
                                    key[1].split(', ')[1]) + ' ' + (
                                    key[1].split(', ')[0])
                            else:
                                personname.text = (key[1])
                            contributor.append(personname)

                            personnameinverted = Element('PersonNameInverted')
                            personnameinverted.text = key[1]
                            contributor.append(personnameinverted)

                            number += 1

            # DescriptibeDetail/EditionType
            editiontype = Element('EditionType')
            editiontype.text = u'DGO'
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
                extenttype.text = u'01'
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

                subjectschemeidentifier = Element('SubjectSchemeIdentifier')
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

            # SupportingResource1
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

            resourceversionfeaturetype = Element('ResourceVersionFeatureType')
            resourceversionfeaturetype.text = u'01'
            resourceversionfeature.append(resourceversionfeaturetype)

            featurevalue = Element('FeatureValue')
            featurevalue.text = u'D502'
            resourceversionfeature.append(featurevalue)

            resourcelink = Element('ResourceLink')
            resourcelink.text = (
                'http://books.scielo.org/id/%s/cover/cover.jpeg' % (sbid))
            resourceversion.append(resourcelink)

            # SupportingResource2
            supportingresource = Element('SupportingResource')
            collateraldetail.append(supportingresource)

            resourcecontenttype = Element('ResourceContentType')
            resourcecontenttype.text = u'15'
            supportingresource.append(resourcecontenttype)

            contentaudience = Element('ContentAudience')
            contentaudience.text = u'00'
            supportingresource.append(contentaudience)

            resourcemode = Element('ResourceMode')
            resourcemode.text = u'06'
            supportingresource.append(resourcemode)

            resourceversion = Element('ResourceVersion')
            supportingresource.append(resourceversion)

            resourceform = Element('ResourceForm')
            resourceform.text = u'01'
            resourceversion.append(resourceform)

            resourcelink = Element('ResourceLink')
            resourcelink.text = ('http://books.scielo.org/id/%s' % (sbid))
            resourceversion.append(resourcelink)

            # Block 4
            product.append(etree.Comment('Block 4'))

            publishingdetail = Element('PublishingDetail')
            product.append(publishingdetail)

            if 'publisher' in book:
                imprint = Element('Imprint')
                publishingdetail.append(imprint)

                imprintname = Element('ImprintName')
                imprintname.text = u'SciELO - ' + book['publisher']
                imprint.append(imprintname)

                publisher = Element('Publisher')
                publishingdetail.append(publisher)

                publishingrole = Element('PublishingRole')
                publishingrole.text = u'01'
                publisher.append(publishingrole)

                publishername = Element('PublisherName')
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
                    date.text = book['year']+'0101'
                    publishingdate.append(date)

            salesrights = Element('SalesRights')
            publishingdetail.append(salesrights)

            salesrightstype = Element('SalesRightsType')
            salesrightstype.text = u'01'
            salesrights.append(salesrightstype)

            territory = Element('Territory')
            salesrights.append(territory)

            regionsincluded = Element('RegionsIncluded')
            regionsincluded.text = u'WORLD'
            territory.append(regionsincluded)

            # Block 5
            product.append(etree.Comment('Block 5 - Related material not \
required if book is digital-only'))

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

            productavailability = Element('ProductAvailability')
            productavailability.text = u'20'
            supplydetail.append(productavailability)

            contries = u'AD AE AF AG AI AL AM AN AO AQ AR AS AT AU AW AX AZ BA \
BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH \
CI CK CL CM CN CO CR CS CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES \
ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY \
HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN \
KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM \
MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU SA SB \
SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK \
TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT \
YU ZA ZM ZW'

            # Price Dollar
            price = Element('Price')
            supplydetail.append(price)

            pricetypecode = Element('PriceTypeCode')
            pricetypecode.text = u'01'
            price.append(pricetypecode)

            priceamount = Element('PriceAmount')
            priceamount.text = book['price_dollar']
            price.append(priceamount)

            currencycode = Element('CurrencyCode')
            currencycode.text = u'USD'
            price.append(currencycode)

            territory = Element('Territory')
            price.append(territory)

            countriesinclude = Element('CountriesIncluded')
            countriesinclude.text = contries
            territory.append(countriesinclude)

            # Price Reais
            price = Element('Price')
            supplydetail.append(price)

            pricetypecode = Element('PriceTypeCode')
            pricetypecode.text = u'02'
            price.append(pricetypecode)

            priceamount = Element('PriceAmount')
            priceamount.text = book['price_reais']
            price.append(priceamount)

            currencycode = Element('CurrencyCode')
            currencycode.text = u'BRL'
            price.append(currencycode)

            territory = Element('Territory')
            price.append(territory)

            countriesinclude = Element('CountriesIncluded')
            countriesinclude.text = contries
            territory.append(countriesinclude)

    # Generates the XML
    return etree.tostring(onix,
                          pretty_print=True,
                          xml_declaration=False,
                          encoding='utf-8')


def main():
    config = configparser.ConfigParser()
    config._interpolation = configparser.ExtendedInterpolation()
    config.read('config.ini')

    sbidlistfile = config['paths']['sbidlistname']
    xmlfolder = config['paths']['xmlfoldername']
    xmlfileout = config['paths']['xmlout']

    host = config['couchdb-books']['url']
    port = config['couchdb-books']['port']

    website = config['books.scielo']['url']

    # Receive sbid list file
    f = open(sbidlistfile, 'r')
    sbidlist = []

    print('SBID list: ')
    for i in f:
        sbidlist.append(i)
        print(i.strip())
    f.close()

    xmldocs = json2xml(
        host=host,
        port=int(port),
        sbidlist=sbidlist,
        website=website)

    # Check and create xml folder output
    if os.path.exists(xmlfolder):
        pass
    else:
        os.mkdir(xmlfolder)

    # Write the XML file
    f = open(xmlfileout, 'w')
    f = open(xmlfileout, 'r+')

    # Declaration whith quotation marks
    f.write(u'<?xml version="1.0" encoding="utf-8"?>\n')

    f.write(xmldocs.decode('utf-8'))
    f.close()

if __name__ == "__main__":
    main()