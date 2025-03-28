# Antonio Callau
# Version: 1.2

# Librerias requeridas (dotenv opcional para google colab, sustituir las variables de entorno)
# pip install requests beautifulsoup4 python-dotenv

# SITEMAPS
# .xml

# Imports
import requests
from bs4 import BeautifulSoup as bs
import time
import csv
import os
# correo
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
# variables de entorno
from dotenv import load_dotenv
# cargar variables de entorno
load_dotenv()


# Functions
def enviarMail():
    """ Enviar correo con el log del script """

    # datos mail (Se requieren la variables de entorno)
    origen_mail = os.getenv('MAIL_ORIGEN')
    destino_mail = os.getenv('MAIL_DESTINO')
    passwd = os.getenv('MAIL_PASSWD')
    asunto = 'Reporte scrap'
    body = 'El script de hoy se ha ejecutado, ya puedes ver los logs'

    try:
      # config mensaje
      mensaje = MIMEMultipart()
      mensaje['From'] = origen_mail
      mensaje['To'] = destino_mail
      mensaje['Subject'] = asunto
      mensaje.attach(MIMEText(body, 'plain'))  # texto plano

      # adjuntar archivo al mensaje
      archivo = "logs.txt"
      with open(archivo, "rb") as adjunto:
          parte = MIMEBase("application", "octet-stream")
          parte.set_payload(adjunto.read())
      encoders.encode_base64(parte)
      parte.add_header("Content-Disposition", f"attachment; filename={archivo}")
      mensaje.attach(parte)

      # conexion servidor SMTP
      servidor = smtplib.SMTP("smtp.gmail.com", 587)
      servidor.starttls()
      servidor.login(origen_mail, passwd)

      # enviar correo
      servidor.sendmail(origen_mail, destino_mail, mensaje.as_string())
      servidor.quit()

      print('correo enviado')

    except Exception as e:
        print(f"error enviando correo --->\n{e}\n")
        # logs
        tiempo_logs = time.strftime("%Y-%m-%d %H:%M:%S")
        with open('logs.txt', mode='a') as file:
          file.write(f"{tiempo_logs} - Estado: ERROR al enviar mail --->\n{e}")



def scraper_web(url, nombre_categoria):
    """ Scrapea la web de la categoria """

    # request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    respuesta = requests.get(url, headers=headers, timeout=50)

    tiempo_logs = time.strftime("%Y-%m-%d %H:%M:%S")

    if respuesta.status_code == 200:

        # logs
        with open('logs.txt', mode='a') as file:
          file.write(f"{tiempo_logs} - Estado: OK -- Url Scrapeada: {url} de {nombre_categoria}\n")

        hoy = time.strftime("%Y%m%d")
        nombre_tienda = os.getenv('NOMBRE_TIENDA')
        nombre_alumno = os.getenv('NOMBRE_ALUMNO')
        divisa_web = 'euros'
        # requerimientos: fecha{YYYY-MM-DD}-[nombre_tienda | nombre_alumno].csv
        web_productos = f"{hoy}-[{nombre_tienda} | {nombre_alumno}].csv"

        # comprobar si archivo ya existe
        archivo_existe = os.path.isfile(web_productos)

        # editar archivo (a)
        with open(web_productos, mode='a', newline='') as archivo_csv:
            # escritor csv, Nota: el campo descripcion no esta visible asi que lo omito
            escritor_csv = csv.DictWriter(archivo_csv, fieldnames=["ID_Producto", "Nombre", "Precio", "Divisa", "Fecha", "Categoria", "URL_Producto", "URL_Imagen"])

            # escribir cabeceras si el archivo NO existe
            if not archivo_existe:
              escritor_csv.writeheader()

            # formato
            soup = bs(respuesta.text, 'lxml') #otras opciones: lxml, html.parser, html5
            products = soup.find_all('article', class_ = 'product-miniature')

            for product in products:
                id_product = product.get('data-id-product').strip()
                h3_intermedio = product.find('span', class_="h3 product-title")
                name = h3_intermedio.find('a').text.strip()

                price_element = product.find('span', class_="product-price")
                if price_element:
                    price = price_element.text.strip()
                else:
                    price = "no_disponible"  # el producto existe pero todavia no tiene precio (RTX 5070 nuevas)

                price_clean = price.replace('€', '').replace('.', '').replace(',', '.').strip() # quitar puntos y cambiar comas por puntos
                url_product = product.find('a', class_="product-thumbnail").get('href')
                img_url = product.find('img', class_="lazy-product-image").get('data-full-size-image-url')

                escritor_csv.writerow({"ID_Producto":id_product, "Nombre":name, "Precio":price_clean, "Divisa":divisa_web, "Fecha":hoy, "Categoria":nombre_categoria, "URL_Producto":url_product, "URL_Imagen":img_url})


    else:
        #print("Error: ", respuesta.status_code)
        # logs
        with open('logs.txt', mode='a') as file:
          file.write(f"{tiempo_logs} - Estado: ERROR --->\n{respuesta.status_code}\n\n -- Url Scrapeada: {url} de {nombre_categoria}\n")


def categories_scraper_web():
  """ Activa scraper_web pasandole el json con las categorias que debe scrapear """

  lista_urls = [
      {
          'nombre_cat': 'Sobremesa',
          'url_pag': '',
          'num_pags': 3
      },
      {
          'nombre_cat': 'Pc_Gaming',
          'url_pag': '',
          'num_pags': 3
      },
      {
          'nombre_cat': 'Tarj_Graficas',
          'url_pag': '',
          'num_pags': 5
      }
  ]


  for url_element in lista_urls:
    for i in range(1, url_element['num_pags']+1):
      url_aux = "{}?page={}".format(url_element['url_pag'], i) #paginacion
      print(url_aux, url_element['nombre_cat'])
      scraper_web(url_aux, url_element['nombre_cat'])

  enviarMail()
  print('--Terminado--')


# Ejecutar
categories_scraper_web()

