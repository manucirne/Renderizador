# Desenvolvido por: Luciano Soares <lpsoares@insper.edu.br>
# Disciplina: Computação Gráfica
# Data: 28 de Agosto de 2020

import argparse     # Para tratar os parâmetros da linha de comando
import x3d          # Faz a leitura do arquivo X3D, gera o grafo de cena e faz traversal
import interface    # Janela de visualização baseada no Matplotlib
import gpu          # Simula os recursos de uma GPU
from math import *  # para operações geométricas
import numpy as np  # para lidar com as matrizes

# Defina o tamanhã da tela que melhor sirva para perceber a renderização
height = 200
width = 300

class perspectiveAndTransformations:

    def __init__(self, width, height):
        self.stack_transform = [np.identity(4)]
        self.modelView = np.identity(4)
        self.lookAt = np.identity(4)
        self.P = np.identity(4)
        self.screen_view = screen_view(width, height)

    def pushStack(self, matrix):
        self.stack_transform.append(matrix)

    def actualTransformation(self):
        self.stack_transform.pop()

    def definelookAt(self, orientation, position):
        temp = np.identity(4)
        if orientation[0] != 0:
            temp[1, 1] = cos(orientation[3])
            temp[2, 1] = sin(orientation[3])
            temp[1, 2] = -sin(orientation[3])
            temp[2, 2] = cos(orientation[3])
        if orientation[1] != 0:
            temp[0, 0] = cos(orientation[3])
            temp[0, 2] = sin(orientation[3])
            temp[2, 0] = -sin(orientation[3])
            temp[2, 2] = cos(orientation[3])
        if orientation[2] != 0:
            temp[0, 0] = cos(orientation[3])
            temp[1, 0] = sin(orientation[3])
            temp[0, 1] = -sin(orientation[3])
            temp[1, 1] = cos(orientation[3])

        temp2 = np.identity(4)
        temp2[0, 3] = -position[0]
        temp2[1, 3] = -position[1]
        temp2[2, 3] = -position[2]

        self.lookAt = np.matmul(temp, temp2)

    def defineP(self, aspect, near, far, top, bottom, right, left):
        tempP = np.zeros((4, 4))
        tempP[0, 0] = 2*near/(right-left)
        tempP[1, 1] = 2*near/(top-bottom)
        tempP[2, 2] = -(far+near)/(far-near)
        tempP[2, 3] = -2*far*near/(far-near)
        tempP[3, 2] = -1
        tempP[0, 2] = (right+left)/(right-left)
        tempP[1, 2] = (top+bottom)/(top-bottom)
        self.P = tempP
    
    def defineModelView(self):
        self.modelView = np.matmul(self.P, self.lookAt)

    def translTransform(self, bx, by, bz):
        tempT = np.identity(4)
        tempT[0, 3] = bx
        tempT[1, 3] = by
        tempT[2, 3] = bz
        return tempT
    
    def scaleTransform(self, sx, sy, sz):
        tempS = np.identity(4)
        tempS[0, 0] = sx
        tempS[1, 1] = sy
        tempS[2, 2] = sz
        return tempS

    def rotationTransform(self, x, y, z, teta):
        tempR = np.identity(4)
        if x:    
            tempR[1, 1] = cos(teta)
            tempR[1, 2] = -sin(teta)
            tempR[2, 1] = sin(teta)
            tempR[2, 2] = cos(teta)
        if y:    
            tempR[0, 0] = cos(teta)
            tempR[0, 2] = sin(teta)
            tempR[2, 0] = -sin(teta)
            tempR[2, 2] = cos(teta)
        if z:    
            tempR[0, 0] = cos(teta)
            tempR[0, 1] = -sin(teta)
            tempR[1, 0] = sin(teta)
            tempR[1, 1] = cos(teta)
        return tempR

def screen_view(width, height):
    screen = np.zeros((4, 4))
    screen[0, 0] = width/2
    screen[1, 1] = -height/2
    screen[0, 3] = width/2
    screen[1, 3] = height/2
    return screen


pAndT = perspectiveAndTransformations(width, height)

def destructureX(vertices):
    return vertices[0], vertices[2], vertices[4]

def destructureY(vertices):
    return vertices[1], vertices[3], vertices[5]

def calculate_baricenter(x, y, xa, xb, xc, ya, yb, yc):
    alpha = (-(x-xb)*(yc-yb) + (y-yb)*(xc-xb)) / (-(xa-xb)*(yc-yb) + (ya-yb)*(xc-xb))
    beta = (-(x-xc)*(ya-yc) + (y-yc)*(xa-xc)) / (-(xb-xc)*(ya-yc) + (yb-yc)*(xa-xc))
    gamma = 1 - alpha - beta
    return alpha, beta, gamma

def calculate_color(x, y, vertices, color):
    xa, xb, xc = destructureX(vertices)
    ya, yb, yc = destructureY(vertices)
    alpha, beta, gamma = calculate_baricenter(x, y, xa, xb, xc, ya, yb, yc)
    r = alpha*color[0] + beta*color[3] + gamma*color[6]
    g = alpha*color[1] + beta*color[4] + gamma*color[7]
    b = alpha*color[2] + beta*color[5] + gamma*color[8]
    return 255*r, 255*g, 255*b

def calculate_texture(x, y, image, text, vertices):
    size_img_x = len(image)
    size_img_y = len(image[0])
    
    xa, xb, xc = destructureX(vertices)
    ya, yb, yc = destructureY(vertices)
    alpha, beta, gamma = calculate_baricenter(x, y, xa, xb, xc, ya, yb, yc)

    ua, ub, uc = destructureX(text)
    va, vb, vc = destructureY(text)
    u = alpha*ua + beta*ub + gamma*uc
    v = alpha*va + beta*vb + gamma*vc
    
    u = int(u*size_img_x)-1
    v = int(v*size_img_y)-1
    
    return image[-v][u][:3]

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
        x = int(point[i]) if (((diffx < 0.8) and (diffx > 0.2)) or (int(point[i]) + 1) < (width-1)) else int(point[i]) + 1
        y = int(point[i + 1]) if (((diffy < 0.8) and (diffy > 0.2)) or ((int(point[i + 1]) + 1) < (height-1))) else int(point[i + 1]) + 1
        gpu.GPU.set_pixel(x, y, r, g, b)
        # if (diffx <= 0.3) and ((x - 1) >= 0):
        #     gpu.GPU.set_pixel(int(point[i]) - 1, y, r*(0.5-diffx), g*(0.5-diffx), b*(0.5-diffx))
        # if (diffy <= 0.3) and ((y - 1) >= 0):
        #     gpu.GPU.set_pixel(x, int(point[i + 1]) - 1, r*(0.5-diffy), g*(0.5-diffy), b*(0.5-diffy))
        # if (diffx >= 0.8) and ((x + 1) <= (width-1)):
        #     gpu.GPU.set_pixel(int(point[i]) + 1, y, r*(0.5-diffx), g*(0.5-diffx), b*(0.5-diffx))
        # if (diffy >= 0.8) and ((y + 1) <= (height-1)):
        #     gpu.GPU.set_pixel(x, int(point[i + 1]) + 1, r*(0.5-diffy), g*(0.5-diffy), b*(0.5-diffy))
        # if ((diffx <= 0.3) and ((x - 1) >= 0)) and ((diffy <= 0.3) and ((y - 1) >= 0)):
        #     gpu.GPU.set_pixel(int(point[i]) - 1, int(point[i + 1]) - 1, r*(0.5-diffx), g*(0.5-diffx), b*(0.5-diffx))
        # if ((diffy >= 0.8) and ((y + 1) <= (height-1))) and ((diffx >= 0.8) and ((x + 1) <= (width-1))):
        #     gpu.GPU.set_pixel(int(point[i]) + 1, int(point[i + 1]) + 1, r*(0.5-diffy), g*(0.5-diffy), b*(0.5-diffy))


def polyline2D(lineSegments, color):
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

def triangleSet2D(vertices, color, antialiasing = True, colorPerVertex = False, texture = False, image = None, text = None):
    if not colorPerVertex and not texture:
        r = int(255*color[0])
        g = int(255*color[1])
        b = int(255*color[2])
    line1 = line_equation((vertices[0], vertices[1]), (vertices[2], vertices[3]))
    line2 = line_equation((vertices[2], vertices[3]),(vertices[4], vertices[5]))
    line3 = line_equation((vertices[4], vertices[5]), (vertices[0], vertices[1]))
    for i in range(width):
        for j in range(height):
            per_inside = calculate_all_L(line1, line2, line3, i, j)
            if per_inside>0:
                if colorPerVertex:
                    r, g, b = calculate_color(i, j, vertices, color)
                if texture:
                    r, g, b = calculate_texture(i, j, image, text, vertices)

                r_p = int(r*per_inside) if antialiasing else r
                g_p = int(g*per_inside) if antialiasing else g
                b_p = int(b*per_inside) if antialiasing else b
                gpu.GPU.set_pixel(i, j, r_p, g_p, b_p)

def triangleSet(point, color, text, antializasing = True, colorPerVertex = False, texture = False, image = None):
    mat_width = int(len(point)/3)
    points = np.append(np.reshape(point, (mat_width, 3)).transpose(), np.ones((1, mat_width)), axis=0)
    points = np.matmul(pAndT.stack_transform[-1], points)
    points = np.matmul(pAndT.modelView, points)
    for i in range(len(points[0])):
        points[:,i] /= points[-1,i]
    points = np.matmul(pAndT.screen_view, points)
    points = points[:2].transpose().reshape(mat_width*2)
    for i in range(0, len(points), 6):
        triangleSet2D(points[i:i+6], color, antializasing, colorPerVertex, texture, image, text)


def viewpoint(position, orientation, fieldOfView):
    aspect = width/height
    near = 0.5
    far = 100
    top = near * tan(fieldOfView)
    bottom = -top
    right = top * aspect
    left = - right
    pAndT.defineP(aspect, near, far, top, bottom, right, left)
    pAndT.definelookAt(orientation, position)
    pAndT.defineModelView()

def transform(translation, scale, rotation):
    trans = pAndT.stack_transform[-1]

    if translation:
        trans = np.matmul(pAndT.translTransform(translation[0], translation[1], translation[2]), trans)
    if scale:
        trans = np.matmul(pAndT.scaleTransform(scale[0], scale[1], scale[2]), trans)
    if rotation:
        trans = np.matmul(pAndT.rotationTransform(rotation[0], rotation[1], rotation[2], rotation[3]), trans)
    pAndT.pushStack(trans)

def _transform():
    pAndT.actualTransformation()

def triangleStripSet(point, stripCount, color, antialiasing = False, colorPerVertex = False):
    for i in range(int(stripCount[0]) - 2):
        pos = i*3
        if i % 2 == 0:
            triangleSet([point[pos], point[pos + 1], point[pos + 2], point[pos + 3], point[pos + 4], point[pos + 5], point[pos + 6], point[pos + 7], point[pos + 8]], color, antialiasing)
        else:
            triangleSet([point[pos + 3], point[pos + 4], point[pos + 5], point[pos], point[pos + 1], point[pos + 2], point[pos + 6], point[pos + 7], point[pos + 8]], color, antialiasing)

def indexedTriangleStripSet(point, index, color, colorIndex, texCoord, texCoordIndex, antialiasing = False, colorPerVertex = False, texture = False, image = None):
    for i in range(len(index) - 3):
        if((index[i] != -1 and index[i + 1] != -1 and index[i + 2] != -1)):
            pos1 = int(index[i]*3)
            pos2 = int(index[i + 1]*3)
            pos3 = int(index[i + 2]*3)
            if colorPerVertex:
                col_pos1 = int(colorIndex[i]*3)
                col_pos2 = int(colorIndex[i+1]*3)
                col_pos3 = int(colorIndex[i+2]*3)
            if texture:
                text_pos1 = int(texCoordIndex[i]*2)
                text_pos2 = int(texCoordIndex[i + 1]*2)
                text_pos3 = int(texCoordIndex[i + 2]*2)
            if i % 2 == 0:
                temp = [color[col_pos1], color[col_pos1+1], color[col_pos1+2], color[col_pos2], color[col_pos2+1], color[col_pos2+2], color[col_pos3], color[col_pos3+1], color[col_pos3+2]] if colorPerVertex else []
                temp_text = [texCoord[text_pos1], texCoord[text_pos1 + 1], texCoord[text_pos2], texCoord[text_pos2 + 1], texCoord[text_pos3], texCoord[text_pos3 + 1]] if texture else []
                triangleSet([point[pos1], point[pos1 + 1], point[pos1 + 2], point[pos2], point[pos2 + 1], point[pos2 + 2], point[pos3], point[pos3 + 1], point[pos3 + 2]], temp, temp_text, antialiasing, colorPerVertex, texture, image)
            else:
                temp = [color[col_pos2], color[col_pos2+1], color[col_pos2+2], color[col_pos1], color[col_pos1+1], color[col_pos1+1], color[col_pos3], color[col_pos3+1], color[col_pos3+2]] if colorPerVertex else []
                temp_text = [texCoord[text_pos2], texCoord[text_pos2 + 1], texCoord[text_pos1], texCoord[text_pos1 + 1], texCoord[text_pos3], texCoord[text_pos3 + 1]] if texture else []
                triangleSet([point[pos2], point[pos2 + 1], point[pos2 + 2], point[pos1], point[pos1 + 1], point[pos1 + 2], point[pos3], point[pos3 + 1], point[pos3 + 2]], temp, temp_text, antialiasing, colorPerVertex, texture, image)



def box(size, color):
    x = size[0]/2
    y = size[1]/2
    z = size[2]/2

    side = [-x, -y, -z, -x, -y, z, -x, y, -z, -x, y, z, x, y, -z, x, y, z, x, -y, -z, x, -y, z]
    back = [-x, -y, -z, -x, y, -z, x, -y, -z, x, y, -z]
    front = [-x, -y, z, x, -y, z, -x, y, z, x, y, z]
    triangleStripSet(side, [8], color, True)
    triangleStripSet(back, [4], color, True)
    triangleStripSet(front, [4], color, True)


def indexedFaceSet(coord, coordIndex, colorPerVertex, color, colorIndex, texCoord, texCoordIndex, current_color, current_texture):
    """ Função usada para renderizar IndexedFaceSet. """
    # A função indexedFaceSet é usada para desenhar malhas de triângulos. Ela funciona de
    # forma muito simular a IndexedTriangleStripSet porém com mais recursos.
    # Você receberá as coordenadas dos pontos no parâmetro cord, esses
    # pontos são uma lista de pontos x, y, e z sempre na ordem. Assim point[0] é o valor
    # da coordenada x do primeiro ponto, point[1] o valor y do primeiro ponto, point[2]
    # o valor z da coordenada z do primeiro ponto. Já point[3] é a coordenada x do
    # segundo ponto e assim por diante. No IndexedFaceSet uma lista informando
    # como conectar os vértices é informada em coordIndex, o valor -1 indica que a lista
    # acabou. A ordem de conexão será de 3 em 3 pulando um índice. Por exemplo: o
    # primeiro triângulo será com os vértices 0, 1 e 2, depois serão os vértices 1, 2 e 3,
    # depois 2, 3 e 4, e assim por diante.
    # Adicionalmente essa implementação do IndexedFace suport cores por vértices, assim
    # a se a flag colorPerVertex estiver habilidades, os vértices também possuirão cores
    # que servem para definir a cor interna dos poligonos, para isso faça um cálculo
    # baricêntrico de que cor deverá ter aquela posição. Da mesma forma se pode definir uma
    # textura para o poligono, para isso, use as coordenadas de textura e depois aplique a
    # cor da textura conforme a posição do mapeamento. Dentro da classe GPU já está
    # implementadado um método para a leitura de imagens.
    # interpolação baricêntrica
    if not colorPerVertex and not current_texture:
        indexedTriangleStripSet(coord, coordIndex, current_color, colorIndex, texCoord, texCoordIndex, False)
    elif colorPerVertex:
        indexedTriangleStripSet(coord, coordIndex, color, colorIndex, texCoord, texCoordIndex, False, True)
    elif texCoord:
        image = gpu.GPU.load_texture(current_texture[0])
        indexedTriangleStripSet(coord, coordIndex, color, colorIndex, texCoord, texCoordIndex, False, False, True, image)

    
    # O print abaixo é só para vocês verificarem o funcionamento, deve ser removido.
    # print("IndexedFaceSet : ")
    # if coord:
    #     print("\tpontos(x, y, z) = {0}, coordIndex = {1}".format(coord, coordIndex)) # imprime no terminal
    # if colorPerVertex:
    #     print("\tcores(r, g, b) = {0}, colorIndex = {1}".format(color, colorIndex)) # imprime no terminal
    # if texCoord:
    #     print("\tpontos(u, v) = {0}, texCoordIndex = {1}".format(texCoord, texCoordIndex)) # imprime no terminal
    # if(current_texture):
    #     image = gpu.GPU.load_texture(current_texture[0])
    #     print("\t Matriz com image = {0}".format(image))

if __name__ == '__main__':

    # Valores padrão da aplicação
    # width = LARGURA
    # height = ALTURA
    x3d_file = "exemplo9.x3d"
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
    x3d.X3D.render["_Transform"] = _transform
    x3d.X3D.render["TriangleStripSet"] = triangleStripSet
    x3d.X3D.render["IndexedTriangleStripSet"] = indexedTriangleStripSet
    x3d.X3D.render["Box"] = box
    x3d.X3D.render["IndexedFaceSet"] = indexedFaceSet

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