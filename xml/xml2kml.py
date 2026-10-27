# -*- coding: utf-8 -*-
"""
Generación de archivos KML a partir de XML mediante expresiones XPath

@version 1.1 19/Octubre/2024
@author: Juan Manuel Cueva Lovelle. Universidad de Oviedo
"""

import os
import sys
import xml.etree.ElementTree as ET


class Kml(object):
    """
    Genera archivo KML con puntos y líneas
    """

    def __init__(self):
        """
        Crea el elemento raíz y el espacio de nombres
        """
        self.raiz = ET.Element('kml', xmlns="http://www.opengis.net/kml/2.2")
        self.doc = ET.SubElement(self.raiz, 'Document')

    def addPlacemark(self, nombre, descripcion, long, lat, alt, modoAltitud, color=None):
        """
        Añade un elemento <Placemark> con puntos <Point> y color opcional
        """
        pm = ET.SubElement(self.doc, 'Placemark')
        ET.SubElement(pm, 'name').text = nombre
        ET.SubElement(pm, 'description').text = descripcion

        if color:
            estilo = ET.SubElement(pm, 'Style')
            icon_style = ET.SubElement(estilo, 'IconStyle')
            ET.SubElement(icon_style, 'color').text = color

            iconos = {
                'ff0000ff': 'red-pushpin.png',  # Rojo
                'ff00ff00': 'grn-pushpin.png',  # Verde
                'ffff0000': 'blue-pushpin.png', # Azul
                'ff00ffff': 'ylw-pushpin.png'   # Amarillo
            }
            if color in iconos:
                icon = ET.SubElement(icon_style, 'Icon')
                ET.SubElement(icon, 'href').text = f'http://maps.google.com/mapfiles/kml/pushpin/{iconos[color]}'

        punto = ET.SubElement(pm, 'Point')
        ET.SubElement(punto, 'coordinates').text = '{},{},{}'.format(long, lat, alt)
        ET.SubElement(punto, 'altitudeMode').text = modoAltitud

    def addLineString(self, nombre, extrude, tesela, listaCoordenadas, modoAltitud, color, ancho):
        """
        Añade un elemento <Placemark> con líneas <LineString>
        """
        ET.SubElement(self.doc, 'name').text = nombre
        pm = ET.SubElement(self.doc, 'Placemark')
        ls = ET.SubElement(pm, 'LineString')
        ET.SubElement(ls, 'extrude').text = extrude
        ET.SubElement(ls, 'tessellation').text = tesela
        ET.SubElement(ls, 'coordinates').text = listaCoordenadas
        ET.SubElement(ls, 'altitudeMode').text = modoAltitud

        estilo = ET.SubElement(pm, 'Style')
        linea = ET.SubElement(estilo, 'LineStyle')
        ET.SubElement(linea, 'color').text = color
        ET.SubElement(linea, 'width').text = ancho

    def escribir(self, nombreArchivoKML):
        """
        Escribe el archivo KML con declaración y codificación
        """
        arbol = ET.ElementTree(self.raiz)
        ET.indent(arbol)
        arbol.write(nombreArchivoKML, encoding='utf-8', xml_declaration=True)

    def ver(self):
        """
        Muestra la estructura del KML para depurar
        """
        print("\nElemento raiz = ", self.raiz.tag)
        for hijo in self.raiz.findall('.//'):
            print("\nElemento = ", hijo.tag)
            if hijo.text:
                print("Contenido = ", hijo.text.strip('\n'))
            print("Atributos = ", hijo.attrib)


class Xml2Kml(object):
    """
    Clase para procesar el XML de la etapa y generar el KML mediante XPath
    """

    def __init__(self, archivoXML="etapaEsquema.xml"):
        self.archivoXML = archivoXML
        self.arbol = None
        self.raiz = None
        self.ns = {'ns': 'http://www.uniovi.es'}

    def cargarXML(self):
        """
        Lee el archivo XML y genera en memoria el árbol DOM
        """
        try:
            self.arbol = ET.parse(self.archivoXML)
            self.raiz = self.arbol.getroot()
        except IOError:
            print('No se encuentra el archivo ', self.archivoXML)
            sys.exit()
        except ET.ParseError:
            print("Error procesando el archivo XML = ", self.archivoXML)
            sys.exit()

    def getCoordenadas(self, elemento):
        """
        Obtiene longitud, latitud y altitud usando XPath
        """
        c = elemento.find('.//ns:coordenadas', self.ns)
        if c is not None:
            longitud = c.find('ns:longitud', self.ns).text
            latitud = c.find('ns:latitud', self.ns).text
            altitud = c.find('ns:altitud', self.ns).text
            return longitud, latitud, altitud
        return "0.0", "0.0", "0.0"

    def crearKML(self, salidaKML="etapa.kml"):
        """
        Recorre el árbol DOM usando XPath y genera el archivo KML
        """
        if self.raiz is None:
            self.cargarXML()

        kml = Kml()

        # Nombre de la etapa
        nodo_nombre = self.raiz.find('ns:nombre', self.ns)
        nombre_etapa = nodo_nombre.text if nodo_nombre is not None else "Etapa"

        coordenadas_ruta = []

        # Lugar de Salida (rojo)
        salida = self.raiz.find('.//ns:lugar_salida', self.ns)
        if salida is not None:
            ciudad = salida.find('ns:ciudad', self.ns).text
            lo, la, al = self.getCoordenadas(salida)
            kml.addPlacemark(f'Salida: {ciudad}', 'Punto de Salida de la etapa',
                              lo, la, al, 'relativeToGround', color='ff0000ff')
            coordenadas_ruta.append(f'{lo},{la},{al}')

        # Puntos anónimos (amarillo) - limitado a 30
        puntos_anonimos = self.raiz.findall('.//ns:punto_anonimo', self.ns)[:30]
        for i, p in enumerate(puntos_anonimos, 1):
            nombre_p = p.find('ns:nombre_punto', self.ns)
            dist_p = p.find('ns:distancia_salida', self.ns)
            dist_txt = f" ({dist_p.text} km)" if dist_p is not None else ""

            if nombre_p is not None and nombre_p.text:
                nombre_str = f"Punto {i}: {nombre_p.text}"
            else:
                nombre_str = f"Punto {i}"

            lo, la, al = self.getCoordenadas(p)
            kml.addPlacemark(nombre_str, f"Punto intermedio{dist_txt}",
                              lo, la, al, 'relativeToGround', color='ff00ffff')
            coordenadas_ruta.append(f'{lo},{la},{al}')

        # Puertos de montaña (verde)
        puertos = self.raiz.findall('.//ns:puerto_montana', self.ns)
        for puerto in puertos:
            cat = puerto.attrib.get('categoria', '')
            dist_p = puerto.find('ns:distancia_salida', self.ns)
            dist_txt = f" - {dist_p.text} km" if dist_p is not None else ""
            lo, la, al = self.getCoordenadas(puerto)

            kml.addPlacemark(f'Puerto de Montaña ({cat})', f'Puerto categoría {cat}{dist_txt}',
                              lo, la, al, 'relativeToGround', color='ff00ff00')

        # Sprints intermedios (azul)
        sprints = self.raiz.findall('.//ns:sprint', self.ns)
        for sprint in sprints:
            tipo = sprint.attrib.get('tipo', 'intermedio')
            dist_p = sprint.find('ns:distancia_salida', self.ns)
            dist_txt = f" - {dist_p.text} km" if dist_txt is not None else ""
            lo, la, al = self.getCoordenadas(sprint)

            kml.addPlacemark(f'Sprint ({tipo})', f'Sprint {tipo}{dist_txt}',
                              lo, la, al, 'relativeToGround', color='ffff0000')

        # Lugar de Meta (rojo)
        meta = self.raiz.find('.//ns:lugar_meta', self.ns)
        if meta is not None:
            ciudad = meta.find('ns:ciudad', self.ns).text
            lo, la, al = self.getCoordenadas(meta)
            kml.addPlacemark(f'Meta: {ciudad}', 'Punto de Llegada/Meta de la etapa',
                              lo, la, al, 'relativeToGround', color='ff0000ff')
            coordenadas_ruta.append(f'{lo},{la},{al}')

        # Trazado de la línea del recorrido
        coords_string = '\n'.join(coordenadas_ruta)
        kml.addLineString(f'Ruta - {nombre_etapa}', "1", "1", coords_string, 'relativeToGround', 'ff0000ff', "5")

        # Guardar archivo KML
        kml.escribir(salidaKML)
        print("Creado el archivo KML: ", salidaKML)

    def main(self):
        xml_file = "etapaEsquema.xml"
        if not os.path.exists(xml_file) and os.path.exists("xml/etapaEsquema.xml"):
            xml_file = "xml/etapaEsquema.xml"

        kml_file = "etapa.kml"

        if len(sys.argv) > 1:
            xml_file = sys.argv[1]
        if len(sys.argv) > 2:
            kml_file = sys.argv[2]

        self.archivoXML = xml_file
        self.cargarXML()
        self.crearKML(kml_file)


if __name__ == "__main__":
    app = Xml2Kml()
    app.main()
