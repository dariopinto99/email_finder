# email_scraper
#breve script python Spiderfoot's compatible per effettuare lo scraping delle email
# Il numero di link a partire dai quali le email saranno ricercate è 100,per evitare che la ricerca sia onerosa
# Per verificare se il formato della mail sia corretto,faremo un regex check
# Per effettuare lo scraping dei documenti web da cui ricavare il link relativo alle mail,useremo BeautifulSoup
# Una volta inserito l'URL del target,verranno processati 100 links e sarà possibile vedere tutte le email con lo stesso
# dominio che il programma è riuscito a trovare facendo una scanning dei primi 100 links. Dunque avremo un certo numero
# di emails associate a tali links relativi al dato URL inserito.
