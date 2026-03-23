import pygame
import sys

def main():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Flappy Template")

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill((135, 206, 235)) # Sky blue
        # Add basic flappy logic here
        
        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()
