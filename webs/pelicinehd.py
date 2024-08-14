import requests
from lxml import html
from urllib.parse import urljoin, urlparse, parse_qs, urlunparse
from tqdm import tqdm

visited_urls = set()

def modify_trembed_url(iframe_url, option_index):
    """ Modifica el parámetro trembed en la URL del iframe. """
    parsed_url = urlparse(iframe_url)
    query_params = parse_qs(parsed_url.query)
    query_params['trembed'] = [str(option_index)]
    
    new_query = '&'.join(f"{key}={value[0]}" for key, value in query_params.items())
    modified_url = urlunparse(parsed_url._replace(query=new_query))
    return modified_url

def scrape_page(url, file, depth=0, max_depth=3, pbar=None):
    if depth > max_depth:
        return
    
    if url in visited_urls:
        return
    
    visited_urls.add(url)
    
    try:
        response = requests.get(url)
        tree = html.fromstring(response.content)

        # Busca todos los enlaces con span que contengan "CASTELLANO" o "DUAL-AUD"
        server_links = tree.xpath('//a[contains(@href, "#options") and (.//span[contains(@class,"server") and (contains(text(),"CASTELLANO") or contains(text(),"DUAL-AUD") )])]')
        for server_link in server_links:
            href = server_link.get('href')
            option_index = href.split('-')[-1]  # Obtener el índice de la opción (0, 1, 2, ...)
            language = server_link.xpath('.//span[contains(@class,"server")]/text()')[0].strip()  # Obtener el texto del idioma
            language_link = urljoin(url, href)

            # Accede al enlace con el idioma específico
            language_response = requests.get(language_link)
            language_tree = html.fromstring(language_response.content)

            # Encuentra y modifica el iframe basado en la opción seleccionada
            iframe_elements = language_tree.xpath('//iframe[@src]')
            if iframe_elements:
                h1 = language_tree.xpath('//h1/text()')
                h1_text = h1[0].strip() if h1 else "No se encontró un <h1>"

                image_url = None
                image_element = language_tree.xpath('//div[@class="post-thumbnail alg-ss"]//figure//img')
                if image_element:
                    image_url = urljoin(language_link, image_element[0].get('src'))

                for iframe in iframe_elements:
                    iframe_src = iframe.get('src')
                    modified_iframe_url = modify_trembed_url(iframe_src, option_index)
                    file.write("<tr>\n")
                    file.write(f"<td><h1>{h1_text}</h1></td>\n")
                    file.write(f"<td>{language}</td>\n")
                    if image_url:
                        file.write(f"<td><img src='{image_url}' alt='Thumbnail' style='max-width:120px;'/></td>\n")
                    else:
                        file.write("<td></td>\n")
                    file.write(f"<td><a href='{modified_iframe_url}'>Ir al reproductor</a></td>\n")
                    file.write("</tr>\n")

        if pbar:
            pbar.update(1)
        
        # Busca todos los enlaces y llama recursivamente a scrape_page para cada uno
        link_elements = tree.xpath('//a[@href]')
        for link in link_elements:
            href = link.get('href')
            parsed_url = urlparse(href)
            if parsed_url.scheme in ('javascript', ''):
                continue
            absolute_url = urljoin(url, href)
            scrape_page(absolute_url, file, depth + 1, max_depth, pbar)
    
    except requests.exceptions.RequestException as e:
        file.write(f"<tr><td colspan='4'>Error al acceder a {url}: {str(e)}</td></tr>\n")
        file.write("\n")


# Configuración inicial
start_url = 'https://pelicinehd.com'
output_file = "./webs/pelicinehd.html"
max_depth = 5

with open(output_file, "w") as file:
    # Escribe la estructura básica de la página y el buscador
    file.write("""
<html>
<head>
    <title>Resultados de pelicinehd</title>
    <style>
        #searchInput {
            margin-bottom: 12px;
            padding: 8px;
            width: 100%;
            box-sizing: border-box;
            font-size: 16px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
    </style>
    <script>
        function searchTable() {
            var input, filter, table, tr, td, i, j, txtValue;
            input = document.getElementById("searchInput");
            filter = input.value.toLowerCase();
            table = document.getElementById("resultTable");
            tr = table.getElementsByTagName("tr");

            for (i = 1; i < tr.length; i++) {
                tr[i].style.display = "none";
                td = tr[i].getElementsByTagName("td");
                for (j = 0; j < td.length; j++) {
                    if (td[j]) {
                        txtValue = td[j].textContent || td[j].innerText;
                        if (txtValue.toLowerCase().indexOf(filter) > -1) {
                            tr[i].style.display = "";
                            break;
                        }
                    }
                }
            }
        }
    </script>
</head>
<body>
    <h1>Resultados de pelicinehd</h1>
    <input type="text" id="searchInput" onkeyup="searchTable()" placeholder="Buscar en la tabla...">
    <table id="resultTable" border='1'>
        <tr><th>Título</th><th>Idioma</th><th>Imagen</th><th>Enlace</th></tr>
""")

    total_links_to_scrape = 200
    with tqdm(total=total_links_to_scrape, desc="Scraping en progreso") as pbar:
        scrape_page(start_url, file, max_depth=max_depth, pbar=pbar)
    
    # Cerrar la tabla y el HTML
    file.write("""
    </table>
</body>
</html>
""")

print("Scraping completed.")
