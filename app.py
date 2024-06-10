from flask import Flask, render_template, request, make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from pdfrw import PdfReader, PdfWriter, PageMerge
import requests as req
import io
from datetime import datetime
import pandas as pd
import csv

app = Flask(__name__)

def getCompany(organizationNumber):
    url = f"https://data.brreg.no/enhetsregisteret/api/enheter/{organizationNumber}"
    response = req.get(url)
    if response.status_code == 200:
        data = response.json()
        address = data.get("forretningsadresse", {}).get("adresse", "N/A")
        if isinstance(address, list):
            address = ', '.join([addr for addr in address if addr])  # Join non-empty address parts
        return {
            "name": data.get("navn", "N/A"),
            "address": address,
            "postcode": data.get("forretningsadresse", {}).get("postnummer", "N/A"),
            "city": data.get("forretningsadresse", {}).get("poststed", "N/A")
        }
    else:
        return {
            "name": "N/A",
            "address": "N/A",
            "postcode": "N/A",
            "city": "N/A"
        }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    salesman = request.form['selger']
    org_number = request.form['org_number']
    email = request.form['email']
    price = request.form['price']
    service = request.form['service']
    person_name = request.form['person_name']
    
    company_info = getCompany(org_number)
    company_name = company_info["name"]
    company_address = company_info["address"]
    company_postcode = company_info["postcode"]
    company_city = company_info["city"]
    current_date = datetime.now().strftime("%d/%m/%Y")

    if salesman == "Arya Raeesi":
        salesmanMail = "arya@blinkweb.no"
    elif salesman == "Isak Rysst":
        salesmanMail = "isak@blinkweb.no"

    # Oppdater CSV-filen med ny data
    csv_file_path = 'orderid.csv'
    updated = False
    rows = []
    order_id = None
    
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # Les headerne
        for row in reader:
            if row[1:] == ['', '', '', '', ''] and not updated:  # Sjekk om raden er ledig (unntatt orderID)
                order_id = row[0]  # Hent orderID
                row[1] = company_name
                row[2] = f"{company_address}, {company_postcode} {company_city}"
                row[3] = service
                row[4] = person_name
                row[5] = salesman
                updated = True
            rows.append(row)

    if updated:
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)  # Skriv headerne
            writer.writerows(rows)    # Skriv radene

    # Les den eksisterende PDF-malen
    template_path = "/Users/aryaraeesi/Library/CloudStorage/OneDrive-NTNU/BlinkWeb/Koding/Kontraktsignering/python-contract/preview.pdf"
    template_pdf = PdfReader(template_path)

    # Lag et nytt PDF-dokument
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    width, height = letter

    # Registrer Poppins font
    pdfmetrics.registerFont(TTFont('Poppins', 'fonts/Poppins-Regular.ttf'))

    # Skriv inn de nødvendige dataene på ønskede posisjoner med Poppins font
    can.setFont("Poppins", 12)

    # Eksempelposisjoner (må justeres etter din mal)
    can.drawString(30, 650, org_number)
    can.drawString(30, 614, company_name)
    can.drawString(30, 579, f"{company_address}, {company_postcode} {company_city}")
    can.drawString(30, 545, email)
    can.drawString(30, 510, person_name)
    if order_id:
        can.drawString(453, 765, order_id)  # Juster posisjonen for orderID

    can.drawString(453, 750, current_date)  # Juster posisjonen for dato om nødvendig

    can.setFont("Poppins", 9)
    can.drawString(35, 422, service)
    can.drawString(35,405, "Inkluderer:")

    if service == "Digital profilering":
        can.drawString(35,388,"1) Utvikling av Google My Business side")

    if service == "Etableringspakke hjemmeside":
        can.drawString(35,388,"1) Design og utvikling av hjemmeside")
    
    if service == "Komplett nettsidepakke":
        can.drawString(35,388,"1) Design og utvikling av nettside")

    can.drawString(35, 371, "2) Forhandlinger av avtaler vedrørende")
    can.drawString(46, 358, "markedsføring og annonsering")
    can.drawString(35,341,"3) Konsultasjon og strategiutvikling")
    can.drawString(35,324,"4) SEO-vennlig utvikling")
    can.drawString(35,307,"5) En brukervennlig design")
    can.drawString(35,290,"6) Målgruppebasert design og branding")
    can.drawString(35,273,"7) Sikkerhet og personvern")


    can.drawString(235, 422, f"{price} NOK")

    can.drawString(30, 166, salesman)
    can.drawString(30, 155, salesmanMail)


    can.save()

    # Flytt til starten av bufferet
    packet.seek(0)

    # Les den nye PDF-en fra bufferet
    new_pdf = PdfReader(packet)
    template_page = template_pdf.pages[0]
    overlay_page = new_pdf.pages[0]

    # Slå sammen sidene
    PageMerge(template_page).add(overlay_page).render()

    # Skriv ut den resulterende PDF-en
    output_pdf = io.BytesIO()
    PdfWriter(output_pdf, trailer=template_pdf).write()

    response = make_response(output_pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=output.pdf'
    return response

if __name__ == '__main__':
    app.run(debug=True)
