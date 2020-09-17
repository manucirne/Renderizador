# Desenvolvido por: Luciano Soares <lpsoares@insper.edu.br>
# Disciplina: Computação Gráfica
# Data: 28 de Agosto de 2020

import argparse     # Para tratar os parâmetros da linha de comando
import x3d          # Faz a leitura do arquivo X3D, gera o grafo de cena e faz traversal
import interface    # Janela de visualização baseada no Matplotlib
import gpu          # Simula os recursos de uma GPU

def line_equation(P1, P2):
    A = P1[1] - P2[1]
    B = P2[0] - P1[0]
    C = P1[0]*P2[1] - P1[1]*P2[0]
    return A, B, C

def calculate_one_L(line, x, y):
    return line[0]*x + line[1]*y + line[2]

def inside(L1, L2, L3):
    return (L1<0 and L2<0 and L3<0)

def calculate_1_2_3(lines, x, y):
    result = []
    for line in lines:
        result.append(calculate_one_L(line, x, y))
    return result

def calculate_all_L(line1, line2, line3, x, y):
    total = 0
    l1, l2, l3 = calculate_1_2_3([line1, line2, line3], x+0.25, y+0.25)
    if (inside(l1, l2, l3)):
        total += 0.25
    
    l1, l2, l3 = calculate_1_2_3([line1, line2, line3], x+0.75, y+0.25)
    if (inside(l1, l2, l3)):
        total += 0.25

    l1, l2, l3 = calculate_1_2_3([line1, line2, line3], x+0.25, y+0.75)
    if (inside(l1, l2, l3)):
        total += 0.25

    l1, l2, l3 = calculate_1_2_3([line1, line2, line3], x+0.75, y+0.75)
    if (inside(l1, l2, l3)):
        total += 0.25
    
    return total


def polypoint2D(point, color):
    r = int(255*color[0])
    g = int(255*color[1])
    b = int(255*color[2])
    for i in range(0,len(point),2):
        diffx = ((point[i] - int(point[i])))
        diffy = ((point[i + 1] - int(point[i + 1])))
        x = int(point[i]) if (((diffx < 0.8) and (diffx > 0.2)) or (int(point[i]) + 1) < 29) else int(point[i]) + 1
        y = int(point[i + 1]) if (((diffy < 0.8) and (diffy > 0.2)) or ((int(point[i + 1]) + 1) < 19)) else int(point[i + 1]) + 1
        gpu.GPU.set_pixel(x, y, r, g, b)
        if (diffx <= 0.3) and ((x - 1) >= 0):
            gpu.GPU.set_pixel(int(point[i]) - 1, y, r*(0.5-diffx), g*(0.5-diffx), b*(0.5-diffx))
        if (diffy <= 0.3) and ((y - 1) >= 0):
            gpu.GPU.set_pixel(x, int(point[i + 1]) - 1, r*(0.5-diffy), g*(0.5-diffy), b*(0.5-diffy))
        if (diffx >= 0.8) and ((x + 1) <= 29):
            gpu.GPU.set_pixel(int(point[i]) + 1, y, r*(0.5-diffx), g*(0.5-diffx), b*(0.5-diffx))
        if (diffy >= 0.8) and ((y + 1) <= 19):
            gpu.GPU.set_pixel(x, int(point[i + 1]) + 1, r*(0.5-diffy), g*(0.5-diffy), b*(0.5-diffy))
        if ((diffx <= 0.3) and ((x - 1) >= 0)) and ((diffy <= 0.3) and ((y - 1) >= 0)):
            gpu.GPU.set_pixel(int(point[i]) - 1, int(point[i + 1]) - 1, r*(0.5-diffx), g*(0.5-diffx), b*(0.5-diffx))
        if ((diffy >= 0.8) and ((y + 1) <= 19)) and ((diffx >= 0.8) and ((x + 1) <= 29)):
            gpu.GPU.set_pixel(int(point[i]) + 1, int(point[i + 1]) + 1, r*(0.5-diffy), g*(0.5-diffy), b*(0.5-diffy))
        
    """ Função usada para renderizar Polypoint2D. """
    # gpu.GPU.set_pixel(3, 1, 255, 0, 0) # altera um pixel da imagem
    # cuidado com as cores, o X3D especifica de (0,1) e o Framebuffer de (0,255)

def polyline2D(lineSegments, color):
    """ Função usada para renderizar Polyline2D. """
    # referência http://floppsie.comp.glam.ac.uk/Southwales/gaius/gametools/6.html
    r = int(255*color[0])
    g = int(255*color[1])
    b = int(255*color[2])
    x0 = int(lineSegments[0])
    y0 = int(lineSegments[1])
    x1 = int(lineSegments[2])
    y1 = int(lineSegments[3])
    dx = abs(x1-x0)
    dy = abs(y1-y0)
    gpu.GPU.set_pixel(x0, y0, r, g, b)
    gpu.GPU.set_pixel(x1, y1, r, g, b)
    
    if x0 < x1:
        sx = 1
    else:
        sx = -1

    if y0 < y1:
        sy = 1
    else:
        sy = -1
    err = dx-dy
    prevx0 = x0
    prevy0 = y0
    while not ((y0 == y1) and (x0 == x1)):
        if (x0*sx <= x1) and (y0*sy <= y1):
            gpu.GPU.set_pixel(x0, y0, r, g, b)
        e2 = 2*err
        if (e2 > -dy):
            err = err - dy
            x0 = x0 + sx
        if e2 < dx:
            err = err + dx
            y0 = y0 + sy
        if (prevx0 != x0) and (prevy0 != y0):
            if(err > 6):
                gpu.GPU.set_pixel(x0, y0 - sy, r*0.5, g*0.5, b*0.5)
            elif(err < -6):
                gpu.GPU.set_pixel(x0 - sx, y0, r*0.5, g*0.5, b*0.5)
            elif (err < 0):
                gpu.GPU.set_pixel(x0 + sx, y0 + sy, r*0.5, g*0.5, b*0.5)
            else:
                gpu.GPU.set_pixel(x0 - sx, y0 - sy, r*0.5, g*0.5, b*0.5)
            prevx0 = x0
            prevy0 = y0

def triangleSet2D(vertices, color):
    """ Função usada para renderizar TriangleSet2D. """
    r = int(255*color[0])
    g = int(255*color[1])
    b = int(255*color[2])
    line1 = line_equation((vertices[0], vertices[1]), (vertices[2], vertices[3]))
    line2 = line_equation((vertices[2], vertices[3]),(vertices[4], vertices[5]))
    line3 = line_equation((vertices[4], vertices[5]), (vertices[0], vertices[1]))
    for i in range(30):
        for j in range(20):
            per_inside = calculate_all_L(line1, line2, line3, i, j)
            r_p = int(r*per_inside)
            g_p = int(g*per_inside)
            b_p = int(b*per_inside)
            if per_inside>0:
                gpu.GPU.set_pixel(i, j, r_p, g_p, b_p) # altera um pixel da imagem
                

def triangleSet(point, color):
    """ Função usada para renderizar TriangleSet. """
    print("TriangleSet : pontos = {0}".format(point)) # imprime no terminal pontos
    r = int(255*color[0])
    g = int(255*color[1])
    b = int(255*color[2])
    # for i in range(0,len(point),3):
    #     gpu.GPU.set_pixel(int(point[i]) + 1, int(point[i + 1]) + 1, r, g, b)

def viewpoint(position, orientation, fieldOfView):
    """ Função usada para renderizar (na verdade coletar os dados) de Viewpoint. """
    print("Viewpoint : position = {0}, orientation = {1}, fieldOfView = {2}".format(position, orientation, fieldOfView)) # imprime no terminal

def transform(translation, scale, rotation):
    """ Função usada para renderizar (na verdade coletar os dados) de Transform. """
    print("Transform : ", end = '')
    if translation:
        print("translation = {0} ".format(translation), end = '') # imprime no terminal
    if scale:
        print("scale = {0} ".format(scale), end = '') # imprime no terminal
    if rotation:
        print("rotation = {0} ".format(rotation), end = '') # imprime no terminal
    print("")

def triangleStripSet(point, stripCount, color):
    """ Função usada para renderizar TriangleStripSet. """
    print("TriangleStripSet : pontos = {0} ".format(point), end = '') # imprime no terminal pontos
    for i, strip in enumerate(stripCount):
        print("strip[{0}] = {1} ".format(i, strip), end = '') # imprime no terminal
    print("")

def indexedTriangleStripSet(point, index, color):
    """ Função usada para renderizar IndexedTriangleStripSet. """
    print("IndexedTriangleStripSet : pontos = {0}, index = {1}".format(point, index)) # imprime no terminal pontos

def box(size, color):
    """ Função usada para renderizar Boxes. """
    print("Box : size = {0}".format(size)) # imprime no terminal pontos


LARGURA = 30
ALTURA = 20

if __name__ == '__main__':

    # Valores padrão da aplicação
    width = LARGURA
    height = ALTURA
    x3d_file = "exemplo4.x3d"
    image_file = "tela.png"

    # Tratando entrada de parâmetro
    parser = argparse.ArgumentParser(add_help=False)   # parser para linha de comando
    parser.add_argument("-i", "--input", help="arquivo X3D de entrada")
    parser.add_argument("-o", "--output", help="arquivo 2D de saída (imagem)")
    parser.add_argument("-w", "--width", help="resolução horizonta", type=int)
    parser.add_argument("-h", "--height", help="resolução vertical", type=int)
    parser.add_argument("-q", "--quiet", help="não exibe janela de visualização", action='store_true')
    args = parser.parse_args() # parse the arguments
    if args.input: x3d_file = args.input
    if args.output: image_file = args.output
    if args.width: width = args.width
    if args.height: height = args.height

    # Iniciando simulação de GPU
    gpu.GPU(width, height, image_file)

    # Abre arquivo X3D
    scene = x3d.X3D(x3d_file)
    scene.set_resolution(width, height)

    # funções que irão fazer o rendering
    x3d.X3D.render["Polypoint2D"] = polypoint2D
    x3d.X3D.render["Polyline2D"] = polyline2D
    x3d.X3D.render["TriangleSet2D"] = triangleSet2D
    x3d.X3D.render["TriangleSet"] = triangleSet
    x3d.X3D.render["Viewpoint"] = viewpoint
    x3d.X3D.render["Transform"] = transform
    x3d.X3D.render["TriangleStripSet"] = triangleStripSet
    x3d.X3D.render["IndexedTriangleStripSet"] = indexedTriangleStripSet
    x3d.X3D.render["Box"] = box

    # Se no modo silencioso não configurar janela de visualização
    if not args.quiet:
        window = interface.Interface(width, height)
        scene.set_preview(window)

    scene.parse() # faz o traversal no grafo de cena

    # Se no modo silencioso salvar imagem e não mostrar janela de visualização
    if args.quiet:
        gpu.GPU.save_image() # Salva imagem em arquivo
    else:
        window.image_saver = gpu.GPU.save_image # pasa a função para salvar imagens
        window.preview(gpu.GPU._frame_buffer) # mostra janela de visualização
