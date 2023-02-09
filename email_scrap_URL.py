

from bs4 import BeautifulSoup
import requests
import requests.exceptions
import urllib.parse
from collections import deque
import re
from spiderfoot import SpiderFootPlugin, SpiderFootHelpers, SpiderFootEvent


# Descrizione: breve script python Spiderfoot's compatible per effettuare lo scraping delle email
# Il numero di link a partire dai quali le email saranno ricercate è 100,per evitare che la ricerca sia onerosa
# Per verificare se il formato della mail sia corretto,faremo un regex check
# Per effettuare lo scraping dei documenti web da cui ricavare il link relativo alle mail,useremo BeautifulSoup
# Una volta inserito l'URL del target,verranno processati 100 links e sarà possibile vedere tutte le email con lo stesso
# dominio che il programma è riuscito a trovare facendo una scanning dei primi 100 links. Dunque avremo un certo numero
# di emails associate a tali links relativi al dato URL inserito.


class sfp_Email_scraper(SpiderFootPlugin):
    meta = {
        # Module name: A very short but human-readable name for the module.
        'name': "EmailScraper",
        # Description: A sentence briefly describing the module.
        'summary': "search all possible email-addresses linked to a single URL .",
        'flags': ["error prone", "slow"],
        'useCases': ["FootPrint", "Investigate", "Passive"],
        'categories': ["Search Engines", "DNS"],
            # The repo where the code of the tool lives.
            'repository': 'https://github.com/dariopinto99/email_finder'
        }
    results = None
    def setup(self, sfc, userOpts=None):
        if userOpts is None:
            userOpts = dict()
        self.sf = sfc
        self.results = self.tempStorage()
        self.__dataSource__ = "Some Data Source"
        for opt in list(userOpts.keys()):
            self.opts[opt] = userOpts[opt]
    @staticmethod
    def watchedEvents():
        return ["DOMAIN_NAME"]
    @staticmethod
    def producedEvents():
        return ["EMAILADDR", "EMAILADDR_GENERIC"]
    def handleEvent(self, event, link=None, new_email=None, soup=None):
        # The three most used fields in SpiderFootEvent are:
        # event.eventType - the event type, e.g. INTERNET_NAME, IP_ADDRESS, etc.
        # event.module - the name of the module that generated the event, e.g. sfp_dnsresolve
        # event.data - the actual data,in this case the email's link

        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data
        if self.errorState:
            return
        if eventData in self.results:
            self.debug(f"Skipping {eventData}, already checked.")
            return

        self.results[eventData] = True

        self.debug(f"Received event, {eventName}, from {srcModuleName}")
        # Converto in stringa L'URL del quale si vuole effettuare lo scan e lo passo alla deque
        user_url = str(input('[+] Enter target URL to Scan: '))
        urls = deque([user_url])
        # Si effettua uno scraping degli URLS dalla pagina principale cercando così di ricavare il pattern della
        # mail usando regex,le email saranno poi stampate
        scraped_urls = set()
        emails = set()

        # Ricerca delle mail,ci fermiamo a 100 links e non di più per evitare che la ricerca sia troppo onerosa
        # Aggiunta alla deque dei link trovati relativi all'url inserito.
        count = 0
        try:
            while len(urls):
                count += 1
                if count == 100:
                    break
                url = urls.popleft()
                scraped_urls.add(url)
        except:
            print('nothing')
            # Analisi dell'URL tramite l'uso di urlsplit
        parts = urllib.parse.urlsplit(url)
        base_url = '{0.scheme}://{0.netloc}'.format(parts)
        path = url[:url.rfind('/')+1] if '/' in parts.path else url
        print('[%d] Processing %s' % (count , url))
        try:
           response = requests.get(url)
        except(requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
            # Codice per vedere se il format della mail inserita  sia valido(regex check)
            new_email = set(re.findall(r"[a-zA-Z0-9\-+]+@[a-z0-9\-+]+\.[a-z]+", response.text , re.I))
            emails.update(new_email)

            # Creo un oggetto di tipo beautifulSoup per istanziare il link relativo alle mail
            soup = BeautifulSoup(response.text, features="lxml")
            # Istanziamo il link che noi useremo per effettuare il prossimo scan
            # relativo alle nostre emails
            for anchor in soup.find_all("a"):
                link = anchor.attrs['href'] if 'href' in anchor.attrs else ''
                if not link.startswith('/') :
                    link = base_url+link
                elif not link.startswith('http'):
                    link = path+link
                if not link in urls and not link in scraped_urls:
                    urls.append(link)
        except KeyboardInterrupt:
            print('-closing all')

            if new_email['content'] is None:
                return

            tbody = soup.find('tbody')
            if tbody:
                data = str(tbody.contents)
            else:
                # ritorna al contenuto della pagina relativa al link
                data = new_email["content"]
            emails = SpiderFootHelpers.extractEmailsFromText(data)
            for email in emails:
                # Skip unrelated emails
                mailDom = email.lower().split('@')[1]
                if not self.getTarget().matches(mailDom):
                    self.debug(f"Skipped address: {email}")
                    continue
            evt = SpiderFootEvent(email, self.__name__, event)
            self.notifyListeners(evt)


