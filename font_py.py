import pygame
pygame.init()

screen = pygame.display.set_mode((2000, 1000))

fonts = sorted(pygame.font.get_fonts())
font_objs = [(pygame.font.SysFont(f, 12), f) for f in fonts]

text_surfs = [font_obj[0].render("FIGHTER | " + font_obj[1][:10], True, (255, 255, 255)) for font_obj in font_objs]
text_rects = [text_surf.get_rect(topleft=(int(i / 40) * 300, i * 25 % 1000)) for i, text_surf in enumerate(text_surfs)]

text = "fighter"

focused = False
selected_font = ""
f_surf = None

saved_fonts = []

run = True
while run:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            run = False

        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                if not focused:
                    for i, r in enumerate(text_rects):
                        if r.collidepoint(e.pos):
                            focused = True
                            selected_font = fonts[i]
                            f_surf = pygame.font.SysFont(selected_font, 96).render("FIGHTER | " + selected_font, True, (255, 255, 255))
                            break
                else:
                    focused = False

            elif e.button == 3:

                if focused:
                    if selected_font not in saved_fonts:
                        saved_fonts.append(selected_font)
                        print("SAVED FONT:", selected_font)


    screen.fill((0, 0, 0))

    if not focused:
        for i, font_obj in enumerate(font_objs):
            screen.blit(text_surfs[i], text_rects[i])
    else:
        screen.blit(f_surf, (screen.get_width()/2-f_surf.get_width()/2,screen.get_height()/2- f_surf.get_height()/2))

    pygame.display.flip()

# Dumped saved fonts into file
with open("bookmarked_fts.txt", "a") as font_file:
    print("SAVING FONTS")
    font_file.write("\n".join(saved_fonts))