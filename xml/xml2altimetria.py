# 02040-xml2altimetria.py
# # -*- coding: utf-8 -*-
""""
Genera un archivo SVG con la altimetría de una etapa a partir de un archivo XML
utilizando expresiones XPath.

@version 1.0 
"""

import xml.etree.ElementTree as ET

class Svg(object):
    """
    Genera archivos SVG con rectángulos, círculos, líneas, polilíneas y texto
    """
    def __init__(self):
        """
        Crea el elemento raíz, el espacio de nombres y la versión
        """
        # Se añaden el ancho y alto al elemento raíz para definir el lienzo
        self.raiz = ET.Element('svg', xmlns="http://www.w3.org/2000/svg", version="2.0", width="1000", height="600")

    def addPolyline(self, points, stroke, strokeWidth, fill):
        """
        Añade un elemento polyline
        """
        # Se usa attrib para poder escribir 'stroke-width' con guion (estándar SVG)
        ET.SubElement(self.raiz, 'polyline',
                      points=points,
                      stroke=stroke,
                      fill=fill,
                      attrib={'stroke-width': strokeWidth})
        
    def addText(self, texto, x, y, fontFamily, fontSize, style):
        """
        Añade un elemento text
        """
        ET.SubElement(self.raiz, 'text',
                      x=x,
                      y=y,
                      fontFamily=fontFamily,
                      fontSize=fontSize,
                      style=style).text = texto

    def escribir(self, nombreArchivoSVG):
        """
        Escribe el archivo SVG con declaración y codificación
        """
        arbol = ET.ElementTree(self.raiz)
        
        """
        Introduce indentación y saltos de línea
        para generar XML en modo texto
        """
        ET.indent(arbol)
        
        arbol.write(nombreArchivoSVG, 
                    encoding='utf-8', 
                    xml_declaration=True
                    )
    
    def ver(self):
        """
        Muestra el archivo SVG. Se utiliza para depurar
        """
        print("\nElemento raiz = ", self.raiz.tag)

        if self.raiz.text != None:
            print("Contenido = "    , self.raiz.text.strip('\n'))
        else:
            print("Contenido = "    , self.raiz.text)
        
        print("Atributos = "    , self.raiz.attrib)

        for hijo in self.raiz.findall('.//'):
            print("\nElemento = " , hijo.tag)
            if hijo.text != None:
                print("Contenido = ", hijo.text.strip('\n'))
            else:
                print("Contenido = ", hijo.text)    
            print("Atributos = ", hijo.attrib)


class Altimetria(object):
    """
    Clase que procesa el XML de la etapa y utiliza la clase Svg para generar el perfil
    """
    def __init__(self, archivoXML):
        """
        Inicializa la clase con el nombre del archivo XML y las listas de datos
        """
        self.archivoXML = archivoXML
        self.puntos = []
        # Espacio de nombres del XML necesario para que funcione XPath
        self.ns = {'u': 'http://www.uniovi.es'}

    def extraerDatos(self):
        """
        Extrae la distancia, altitud y nombre de los puntos utilizando expresiones XPath
        """
        arbol = ET.parse(self.archivoXML)
        raiz = arbol.getroot()
        
        # 1. Punto de salida (inicio)
        salida = raiz.find('.//u:lugar_salida', self.ns)
        alt_salida = float(salida.find('.//u:altitud', self.ns).text)
        nom_salida = salida.find('.//u:ciudad', self.ns).text
        self.puntos.append((0.0, alt_salida, nom_salida))
        
        # 2. Hitos (Puertos de montaña)
        for puerto in raiz.findall('.//u:hitos/u:puerto_montana', self.ns):
            dist = float(puerto.find('u:distancia_salida', self.ns).text)
            alt = float(puerto.find('.//u:altitud', self.ns).text)
            self.puntos.append((dist, alt, "Puerto Montaña"))

        # 3. Puntos Anónimos (ciudades, pueblos de paso)
        for punto in raiz.findall('.//u:puntos_anonimos/u:punto_anonimo', self.ns):
            dist = float(punto.find('u:distancia_salida', self.ns).text)
            alt = float(punto.find('.//u:altitud', self.ns).text)
            nom_nodo = punto.find('u:nombre_punto', self.ns)
            nom = nom_nodo.text if nom_nodo is not None else ""
            self.puntos.append((dist, alt, nom))
            
        # 4. Lugar de meta (final)
        meta = raiz.find('.//u:lugar_meta', self.ns)
        alt_meta = float(meta.find('.//u:altitud', self.ns).text)
        nom_meta = meta.find('.//u:ciudad', self.ns).text
        dist_meta = float(raiz.find('.//u:longitud_etapa', self.ns).text)
        self.puntos.append((dist_meta, alt_meta, nom_meta))

        # Se ordenan los puntos según la distancia para trazar bien la línea
        self.puntos.sort(key=lambda p: p[0])

    def generarSVG(self, nombreSVG):
        """
        Realiza los cálculos de escala y dibuja el polígono usando la clase Svg
        """
        nuevoSVG = Svg()
        
        max_distancia = max(p[0] for p in self.puntos)
        max_altitud = max(p[1] for p in self.puntos) * 1.1 # Margen superior del 10%
        
        ancho_dibujo = 800
        alto_dibujo = 300
        margen_izq = 100
        suelo_y = 400 # Altura donde se encuentra la línea recta base

        # Se inicia el string de coordenadas en la esquina inferior izquierda
        coordenadas = f"{margen_izq},{suelo_y} "

        # Se recorren los puntos extraídos del XML
        for dist, alt, nombre in self.puntos:
            x = margen_izq + (dist / max_distancia) * ancho_dibujo
            y = suelo_y - (alt / max_altitud) * alto_dibujo
            
            coordenadas += f"{x},{y} "
            
            if nombre:
                # Se aplica el estilo de texto vertical que viene en la teoría
                estilo_vert = "writing-mode: tb; glyph-orientation-vertical: 0;"
                nuevoSVG.addText(nombre, str(x - 6), str(suelo_y + 10), 'Verdana', '14', estilo_vert)

        # Se cierra el polígono en la esquina inferior derecha y luego vuelve a la izquierda
        ultimo_x = margen_izq + ancho_dibujo
        coordenadas += f"{ultimo_x},{suelo_y} {margen_izq},{suelo_y}"

        # Se dibuja la línea de la montaña sin relleno y en color rojo
        nuevoSVG.addPolyline(coordenadas, 'red', '3', 'none')

        """Creación del archivo en formato SVG"""
        nuevoSVG.escribir(nombreSVG)
        print("Creado el archivo: ", nombreSVG)


def main():
    
    print(Altimetria.__doc__)

    """Prueba de la clase Altimetria"""
    nombreXML = "etapaEsquema.xml"
    nombreSVG = "altimetria.svg"

    perfil = Altimetria(nombreXML)
    perfil.extraerDatos()
    perfil.generarSVG(nombreSVG)
    
if __name__ == "__main__":
    main()