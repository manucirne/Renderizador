# Desenvolvido por: Luciano Soares
# Displina: Computação Gráfica
# Data: 28 de Agosto de 2020

import argparse

# X3D
import x3d

# Interface
import interface

# GPU
import gpu

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
    print(err)
    print(color)
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
                gpu.GPU.set_pixel(x0, y0 - sy, r, g, b)
            elif(err < -6):
                gpu.GPU.set_pixel(x0 - sx, y0, r, g, b)
            elif (err < 0):
                gpu.GPU.set_pixel(x0 + sx, y0 + sy, r, g, b)
            else:
                gpu.GPU.set_pixel(x0 - sx, y0 - sy, r, g, b)
            prevx0 = x0
            prevy0 = y0

def triangleSet2D(vertices, color):
    """ Função usada para renderizar TriangleSet2D. """
    gpu.GPU.set_pixel(24, 8, 255, 255, 0) # altera um pixel da imagem

LARGURA = 30
ALTURA = 20

if __name__ == '__main__':
    
    width = LARGURA
    height = ALTURA
    x3d_file = "exemplo2.x3d"
    image_file = "tela.png"

    # Tratando entrada de parâmetro
    parser = argparse.ArgumentParser(add_help=False)   # parser para linha de comando
    parser.add_argument("-i", "--input", help="arquivo X3D de entrada")
    parser.add_argument("-o", "--output", help="arquivo 2D de saída (imagem)")
    parser.add_argument("-w", "--width", help="resolução horizonta", type=int)
    parser.add_argument("-h", "--height", help="resolução vertical", type=int)
    args = parser.parse_args() # parse the arguments
    if args.input: x3d_file = args.input
    if args.output: image_file = args.output
    if args.width: width = args.width
    if args.height: height = args.height
    
    # Iniciando simulação de GPU
    gpu.GPU(width, height)

    # Abre arquivo X3D
    scene = x3d.X3D(x3d_file)
    scene.set_resolution(width, height)

    # funções que irão fazer o rendering
    x3d.X3D.render["Polypoint2D"] = polypoint2D
    x3d.X3D.render["Polyline2D"] = polyline2D
    x3d.X3D.render["TriangleSet2D"] = triangleSet2D

    scene.parse() # faz o traversal no grafo de cena
    interface.Interface(width, height, image_file).preview(gpu.GPU._frame_buffer)
