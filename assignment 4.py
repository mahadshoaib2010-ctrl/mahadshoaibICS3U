import pygame

pygame.init()

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Spritesheets')

run = True
while run:


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quitS